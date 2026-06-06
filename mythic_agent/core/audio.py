import os
import queue
import tempfile
import threading
import logging
from typing import Optional

try:
    import sounddevice as sd
    import numpy as np
    from scipy.io.wavfile import write as write_wav
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

from openai import OpenAI
from ..core.config_manager import config_manager

class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.sample_rate = 16000
        self.channels = 1
        self.audio_queue = queue.Queue()
        self.recording_thread: Optional[threading.Thread] = None
        self.stream: Optional[sd.InputStream] = None
        self._frames = []
        
        self.config = config_manager.load_config()
        self.base_url = self.config.get("base_url", config_manager.DEFAULT_BASE_URL)
        # Re-use the existing LLM logic to get the OpenAI API key if available
        self.api_key = self._get_api_key()
        
    def _get_api_key(self) -> str | None:
        """Fetch API key from config or env."""
        if "api_key" in self.config:
            return self.config["api_key"]
        elif "api_keys" in self.config and self.base_url in self.config["api_keys"]:
            return self.config["api_keys"][self.base_url]
        return os.environ.get("OPENAI_API_KEY")

    def _audio_callback(self, indata, frames, time, status):
        """Called for each audio block by sounddevice."""
        if status:
            logging.warning(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())

    def _record_loop(self):
        """The main loop reading from the stream."""
        self._frames = []
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=self._audio_callback):
                while self.is_recording:
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        self._frames.append(data)
                    except queue.Empty:
                        continue
        except Exception as e:
            logging.error(f"Recording error: {e}")
            self.is_recording = False

    def start_recording(self) -> bool:
        """Starts background recording thread."""
        if not HAS_AUDIO:
            logging.error("sounddevice/numpy/scipy not installed. Cannot record audio.")
            return False
            
        if self.is_recording:
            return False
            
        self.is_recording = True
        self.audio_queue = queue.Queue()
        self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.recording_thread.start()
        return True

    def stop_recording(self) -> Optional[str]:
        """Stops recording and returns the path to the saved temporary WAV file."""
        if not self.is_recording:
            return None
            
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=1.0)
            
        if not self._frames:
            return None
            
        # Concatenate all blocks
        audio_data = np.concatenate(self._frames, axis=0)
        
        # Save to temp file
        fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="mythic_voice_")
        os.close(fd)
        
        write_wav(temp_path, self.sample_rate, audio_data)
        self._frames = []
        return temp_path

    def transcribe(self, wav_path: str) -> Optional[str]:
        """Sends the WAV file to the Deepgram or Whisper API and returns the transcribed text."""
        # Reload config in case it changed
        self.config = config_manager.load_config()
        stt_backend = self.config.get("stt_backend", "whisper")
        
        try:
            if stt_backend == "deepgram":
                deepgram_api_key = self.config.get("deepgram_api_key", "")
                if not deepgram_api_key:
                    logging.error("No Deepgram API key found. Cannot transcribe audio.")
                    return None
                    
                import requests
                url = "https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true"
                headers = {
                    "Authorization": f"Token {deepgram_api_key}",
                    "Content-Type": "audio/wav"
                }
                with open(wav_path, "rb") as audio_file:
                    resp = requests.post(url, headers=headers, data=audio_file)
                    
                if resp.status_code == 200:
                    data = resp.json()
                    transcript = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
                    os.remove(wav_path)
                    return transcript
                else:
                    logging.error(f"Deepgram STT failed: {resp.status_code} {resp.text}")
                    return None
                    
            else:
                # Whisper fallback
                api_key = self._get_api_key()
                if not api_key:
                    logging.error("No OpenAI API key found. Cannot transcribe audio.")
                    return None
                    
                # For transcription, we usually want to hit the main OpenAI API directly 
                # unless the user is explicitly pointing to an open-source endpoint that supports Whisper API (e.g. litellm proxy).
                # We'll use the user's base_url, but standard OpenAI requires "whisper-1".
                client = OpenAI(api_key=api_key, base_url=self.base_url)
                
                with open(wav_path, "rb") as audio_file:
                    # whisper-1 is the standard model name for OpenAI transcriptions
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file
                    )
                    
                os.remove(wav_path)
                return transcription.text

        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            try:
                os.remove(wav_path)
            except OSError:
                pass
            return None

# Global singleton
audio_recorder = AudioRecorder()
