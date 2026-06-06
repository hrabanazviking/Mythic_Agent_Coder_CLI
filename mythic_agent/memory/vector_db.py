import json
import logging
import math
import os
import threading
import tempfile
import time
from pathlib import Path
from typing import Any, Protocol
from openai import OpenAI

from ..core.config_manager import config_manager

# Try to use numpy for 100x faster cosine similarity, fallback to standard library math
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if HAS_NUMPY:
        a = np.array(v1)
        b = np.array(v2)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    else:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude_v1 = math.sqrt(sum(a * a for a in v1))
        magnitude_v2 = math.sqrt(sum(b * b for b in v2))
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0
        return dot_product / (magnitude_v1 * magnitude_v2)

class VectorProvider(Protocol):
    def insert(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        ...
        
    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        ...

class LightweightJSONVectorDB:
    """A zero-dependency vector DB using OpenAI embeddings and local JSON storage."""
    
    def __init__(self, agent_name: str, base_url: str | None = None, api_key: str | None = None):
        self.agent_name = agent_name
        self.memory_dir = config_manager.MYTHIC_DIR / "memory" / "archival"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / f"{self.agent_name}_vectors.json"
        self._lock = threading.Lock()
        
        self.base_url = base_url or "https://api.openai.com/v1"
        self.api_key = api_key
        
        # We only init the client if we have a key
        self.client = None
        if self.api_key:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=60.0)
            
        self.records: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        with self._lock:
            if self.memory_file.exists():
                try:
                    with open(self.memory_file, "r", encoding="utf-8") as f:
                        self.records = json.load(f)
                except json.JSONDecodeError as e:
                    logging.error(f"Vector memory corrupted for {self.agent_name}. Self-healing... Error: {e}")
                    corrupted_file = self.memory_file.with_suffix('.json.corrupted')
                    try:
                        os.replace(self.memory_file, corrupted_file)
                    except OSError:
                        pass
                except Exception as e:
                    logging.error(f"Failed to load vector memory: {e}")

    def _atomic_save(self) -> None:
        try:
            fd, temp_path = tempfile.mkstemp(dir=self.memory_dir, prefix=f"{self.agent_name}_", suffix=".tmp")
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, indent=4)
            os.replace(temp_path, self.memory_file)
        except Exception as e:
            logging.error(f"Failed to atomic save vector memory: {e}")
            try:
                os.remove(temp_path)
            except OSError:
                pass

    def save(self) -> None:
        with self._lock:
            self._atomic_save()

    def get_embedding(self, text: str) -> list[float]:
        if not self.client:
            logging.warning("No API key for embeddings. Returning zero vector.")
            return [0.0] * 1536  # Default dimension for text-embedding-3-small
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logging.warning(f"Embedding API attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Failed to get embedding after {max_retries} attempts.")
                    return [0.0] * 1536
                time.sleep(2 ** attempt)  # Exponential backoff

    def insert(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        vector = self.get_embedding(text)
        record = {
            "text": text,
            "vector": vector,
            "metadata": metadata or {}
        }
        with self._lock:
            self.records.append(record)
            self._atomic_save()

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        with self._lock:
            if not self.records:
                return []
            records_copy = list(self.records)
            
        query_vector = self.get_embedding(query)
        scored_records = []
        for record in records_copy:
            score = cosine_similarity(query_vector, record["vector"])
            scored_records.append((score, record))
            
        scored_records.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, record in scored_records[:top_k]:
            results.append({
                "score": score,
                "text": record["text"],
                "metadata": record["metadata"]
            })
        return results

import requests

class RemoteRAGProvider:
    def __init__(self, name: str, default_url: str):
        self.name = name
        self.config = config_manager.load_config()
        # Allows user to override the URL in config: e.g. "yggdrasil_url"
        self.base_url = self.config.get(f"{name.lower()}_url", default_url).rstrip("/")
        
    def insert(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        try:
            payload = {"text": text, "metadata": metadata or {}}
            response = requests.post(f"{self.base_url}/insert", json=payload, timeout=10.0)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.warning(f"{self.name} Provider insert failed: {e}")

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        try:
            payload = {"query": query, "top_k": top_k}
            response = requests.post(f"{self.base_url}/search", json=payload, timeout=15.0)
            response.raise_for_status()
            return response.json().get("results", [])
        except requests.exceptions.RequestException as e:
            logging.warning(f"{self.name} Provider search failed: {e}")
            return []

class OpenVikingProvider(RemoteRAGProvider):
    def __init__(self):
        super().__init__("OpenViking", "http://localhost:8081/v1")

class MemPalaceProvider(RemoteRAGProvider):
    def __init__(self):
        super().__init__("MemPalace", "http://localhost:8082/v1")

class YggdrasilProvider(RemoteRAGProvider):
    def __init__(self):
        super().__init__("Yggdrasil", "http://localhost:8083/v1")

def get_vector_provider(provider_name: str, agent_name: str, base_url: str | None = None, api_key: str | None = None) -> VectorProvider:
    if provider_name == "open-viking":
        return OpenVikingProvider()
    elif provider_name == "mem-palace":
        return MemPalaceProvider()
    elif provider_name == "yggdrasil":
        return YggdrasilProvider()
    else:
        return LightweightJSONVectorDB(agent_name, base_url, api_key)
