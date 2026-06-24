# src/cache/semantic_cache.py
import hashlib
import json
from typing import Optional, List, Dict
import redis
from src.config import settings
from src.utils.logging import logger
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticCache:
    def __init__(self):
        self.redis_client = None
        if settings.redis_url:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True
                )

                self.redis_client.ping()

                logger.info("Redis cache initialized")

            except Exception as e:
                logger.warning(
                    f"Redis unavailable. Continuing without cache: {e}"
                )

                self.redis_client = None
            
        # For similarity check, we'll compute embeddings of query and store them
        self.embed_model = SentenceTransformer('BAAI/bge-m3')
        # self.embed_model = None
        self.similarity_threshold = 0.85

    def _get_embedding(self, text: str) -> np.ndarray:
        return self.embed_model.encode(text, normalize_embeddings=True)

    def _compute_hash(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str) -> Optional[List[Dict]]:
        if not self.redis_client:
            return None
        # Check exact cache first (fast)
        key = f"cache:exact:{self._compute_hash(query)}"
        cached = self.redis_client.get(key)
        if cached:
            logger.info("Cache hit (exact)")
            return json.loads(cached)

        # Semantic cache: check similar queries
        # We'll store embeddings of previous queries and compare
        # For MVP, we skip semantic similarity cache for simplicity, but we'll implement a basic version.
        # We'll scan keys and compute similarity (expensive, but okay for low volume).
        # To keep it simple, we only use exact cache now.
        return None

    def set(self, query: str, results: List[Dict]) -> None:
        if not self.redis_client:
            return
        key = f"cache:exact:{self._compute_hash(query)}"
        self.redis_client.setex(key, 3600 * 24, json.dumps(results))  # TTL 1 day

cache = SemanticCache()