import os
import re
import queue
import threading
import logging
from pathlib import Path
from typing import Dict, Optional

try:
    import requests
    import sounddevice as sd
    import numpy as np
    from piper import PiperVoice
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

try:
    from chatterbox.tts import ChatterboxTTS
    HAS_CHATTERBOX = True
except ImportError:
    HAS_CHATTERBOX = False

from .config_manager import config_manager

class TTSManager:
    def __init__(self):
        self.queue = queue.Queue()
        self.voices: Dict[str, PiperVoice] = {}
        self.voice_dir = Path.home() / ".local" / "share" / "mythic-agent" / "voices"
        self.voice_dir.mkdir(parents=True, exist_ok=True)
        
        self.voice_samples_dir = Path.home() / ".local" / "share" / "mythic-agent" / "voice_samples"
        self.voice_samples_dir.mkdir(parents=True, exist_ok=True)
        
        self.chatterbox_model = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.is_muted = False
        
        # Primary agent (Piper)
        self.primary_voice = "en_US-lessac-high"
        # Subagent pool (Piper)
        self.subagent_voices = [
            "en_GB-jenny_dioco-medium",
            "en_US-ryan-high",
            "en_US-joe-medium",
            "en_US-amy-medium",
            "en_GB-alba-medium"
        ]
        self.agent_voice_map = {"Primary": self.primary_voice}
        self.next_subagent_idx = 0
        
        # NovelAI voices
        self.novelai_primary_voice = "Aina"
        self.novelai_subagent_voices = ["Orea", "Clio", "Ligeia", "Aura", "Eleanor"]
        self.novelai_agent_voice_map = {"Primary": self.novelai_primary_voice}
        self.novelai_next_subagent_idx = 0

    def start(self):
        if not HAS_TTS:
            logging.error("Piper TTS dependencies not installed. TTS disabled.")
            return
            
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.queue.put(None) # Sentinel
            self.thread.join(timeout=2.0)

    def toggle_mute(self) -> bool:
        self.is_muted = not self.is_muted
        if self.is_muted:
            sd.stop() # stop any currently playing audio immediately
        return self.is_muted

    def speak(self, agent_name: str, text: str):
        if not self.is_running or self.is_muted:
            return
        self.queue.put((agent_name, text))

    def _get_voice_for_agent(self, agent_name: str) -> str:
        if agent_name in self.agent_voice_map:
            return self.agent_voice_map[agent_name]
            
        # Assign a new voice from the pool
        voice = self.subagent_voices[self.next_subagent_idx % len(self.subagent_voices)]
        self.next_subagent_idx += 1
        self.agent_voice_map[agent_name] = voice
        return voice

    def _get_novelai_voice_for_agent(self, agent_name: str) -> str:
        if agent_name in self.novelai_agent_voice_map:
            return self.novelai_agent_voice_map[agent_name]
            
        voice = self.novelai_subagent_voices[self.novelai_next_subagent_idx % len(self.novelai_subagent_voices)]
        self.novelai_next_subagent_idx += 1
        self.novelai_agent_voice_map[agent_name] = voice
        return voice

    def _download_voice_if_missing(self, voice_name: str) -> Path:
        model_path = self.voice_dir / f"{voice_name}.onnx"
        json_path = self.voice_dir / f"{voice_name}.onnx.json"
        
        if not model_path.exists() or not json_path.exists():
            logging.info(f"Downloading Piper TTS voice: {voice_name}")
            
            # HuggingFace piper-voices structure
            # e.g., en_US-lessac-high -> en/en_US/lessac/high/en_US-lessac-high.onnx
            parts = voice_name.split("-")
            lang = parts[0].split("_")[0] # en
            locale = parts[0] # en_US
            speaker = parts[1] # lessac
            quality = parts[2] # high
            
            base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/{lang}/{locale}/{speaker}/{quality}/{voice_name}"
            
            for ext in [".onnx", ".onnx.json"]:
                url = base_url + ext
                dest = self.voice_dir / f"{voice_name}{ext}"
                try:
                    resp = requests.get(url, stream=True)
                    resp.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                except Exception as e:
                    logging.error(f"Failed to download voice {voice_name}{ext} from {url}: {e}")
                    raise
                    
        return model_path

    def _get_piper_voice(self, voice_name: str) -> PiperVoice:
        if voice_name in self.voices:
            return self.voices[voice_name]
            
        model_path = self._download_voice_if_missing(voice_name)
        voice = PiperVoice.load(str(model_path))
        self.voices[voice_name] = voice
        return voice

    def _clean_text(self, text: str) -> str:
        # Remove bold/italic markdown formatting and code blocks
        text = re.sub(r"```.*?```", " Code block omitted. ", text, flags=re.DOTALL)
        text = re.sub(r"`.*?`", "", text)
        text = re.sub(r"\*\*|\*|__|_", "", text)
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text) # links
        text = re.sub(r"\[.*?\]", "", text) # removing textual tags like [bold red]
        text = text.replace("#", "").replace(">", "").replace("-", " ")
        return text.strip()

    def _worker_loop(self):
        while self.is_running:
            try:
                item = self.queue.get(timeout=0.5)
                if item is None:
                    continue
                    
                agent_name, raw_text = item
                if self.is_muted:
                    continue
                    
                clean_text = self._clean_text(raw_text)
                if not clean_text:
                    continue
                custom_wav = self.voice_samples_dir / f"{agent_name}.wav"
                fallback_wav = self.voice_samples_dir / "default.wav"
                
                audio_sample_path = None
                if custom_wav.exists():
                    audio_sample_path = custom_wav
                elif fallback_wav.exists():
                    audio_sample_path = fallback_wav
                    
                config = config_manager.load_config()
                backend = config.get("tts_backend", "piper")
                novelai_key = config.get("novelai_api_key", "")
                
                try:
                    if backend == "novelai" and novelai_key:
                        voice_seed = self._get_novelai_voice_for_agent(agent_name)
                        logging.info(f"Generating NovelAI audio using seed {voice_seed}")
                        
                        headers = {"Authorization": f"Bearer {novelai_key}"}
                        payload = {"text": clean_text, "voice": -1, "seed": voice_seed, "opus": "false", "version": "v2"}
                        
                        resp = requests.get("https://api.novelai.net/ai/generate-voice", headers=headers, params=payload)
                        if resp.status_code == 200 and not self.is_muted:
                            from pydub import AudioSegment
                            import io
                            
                            audio_seg = AudioSegment.from_file(io.BytesIO(resp.content))
                            audio_array = np.array(audio_seg.get_array_of_samples(), dtype=np.int16)
                            
                            if audio_seg.channels == 2:
                                audio_array = audio_array.reshape((-1, 2))
                                
                            sd.play(audio_array, samplerate=audio_seg.frame_rate)
                            sd.wait()
                        else:
                            logging.error(f"NovelAI TTS failed: {resp.status_code} {resp.text}")
                    elif audio_sample_path and HAS_CHATTERBOX:
                        if self.chatterbox_model is None:
                            import torch
                            device = "cuda" if torch.cuda.is_available() else "cpu"
                            logging.info(f"Loading Chatterbox model on {device}...")
                            self.chatterbox_model = ChatterboxTTS.from_pretrained(device=device)
                            
                        logging.info(f"Generating Chatterbox audio using reference {audio_sample_path}")
                        wav = self.chatterbox_model.generate(clean_text, audio_prompt_path=str(audio_sample_path))
                        
                        if not self.is_muted:
                            audio_array = wav.squeeze().cpu().numpy()
                            if audio_array.ndim > 1:
                                audio_array = audio_array.T
                            sd.play(audio_array, samplerate=self.chatterbox_model.sr)
                            sd.wait()
                    else:
                        voice_name = self._get_voice_for_agent(agent_name)
                        voice = self._get_piper_voice(voice_name)
                        
                        # Generate audio stream
                        audio_stream = voice.synthesize_stream_raw(clean_text)
                        audio_bytes = b"".join(audio_stream)
                        
                        if audio_bytes and not self.is_muted:
                            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                            sample_rate = voice.config.sample_rate
                            sd.play(audio_array, samplerate=sample_rate)
                            sd.wait()
                            
                except Exception as e:
                    logging.error(f"TTS Synthesis error for agent {agent_name}: {e}")
            except queue.Empty:
                pass
            except Exception as e:
                logging.error(f"TTS Worker Error: {e}")

tts_manager = TTSManager()
