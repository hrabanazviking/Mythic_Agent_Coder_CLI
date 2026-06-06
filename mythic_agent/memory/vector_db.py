import json
import logging
import math
from pathlib import Path
from typing import Any, Protocol
from openai import OpenAI

from ..core.config_manager import config_manager

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
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
        
        self.base_url = base_url or "https://api.openai.com/v1"
        self.api_key = api_key
        
        # We only init the client if we have a key
        self.client = None
        if self.api_key:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            
        self.records: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load vector memory: {e}")

    def save(self) -> None:
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.records, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save vector memory: {e}")

    def get_embedding(self, text: str) -> list[float]:
        if not self.client:
            logging.warning("No API key for embeddings. Returning zero vector.")
            return [0.0] * 1536  # Default dimension for text-embedding-3-small
            
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Failed to get embedding: {e}")
            return [0.0] * 1536

    def insert(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        vector = self.get_embedding(text)
        record = {
            "text": text,
            "vector": vector,
            "metadata": metadata or {}
        }
        self.records.append(record)
        self.save()

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.records:
            return []
            
        query_vector = self.get_embedding(query)
        scored_records = []
        for record in self.records:
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

# Stubs for the user's custom systems
class OpenVikingProvider:
    def insert(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        logging.warning("OpenVikingProvider insert not implemented.")
    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        logging.warning("OpenVikingProvider search not implemented.")
        return []

class MemPalaceProvider:
    def insert(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        logging.warning("MemPalaceProvider insert not implemented.")
    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        logging.warning("MemPalaceProvider search not implemented.")
        return []

class YggdrasilProvider:
    def insert(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        logging.warning("YggdrasilProvider insert not implemented.")
    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        logging.warning("YggdrasilProvider search not implemented.")
        return []

def get_vector_provider(provider_name: str, agent_name: str, base_url: str | None = None, api_key: str | None = None) -> VectorProvider:
    if provider_name == "open-viking":
        return OpenVikingProvider()
    elif provider_name == "mem-palace":
        return MemPalaceProvider()
    elif provider_name == "yggdrasil":
        return YggdrasilProvider()
    else:
        return LightweightJSONVectorDB(agent_name, base_url, api_key)
