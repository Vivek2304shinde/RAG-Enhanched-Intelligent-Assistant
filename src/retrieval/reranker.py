# src/retrieval/reranker.py
from typing import List, Dict
import cohere
from src.config import settings
from src.utils.logging import logger
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        self.use_cohere = bool(settings.cohere_api_key)
        if self.use_cohere:
            self.co = cohere.Client(api_key=settings.cohere_api_key)
        else:
            # Fallback: local cross‑encoder (BGE‑reranker)
            self.model = CrossEncoder('BAAI/bge-reranker-v2-m3', max_length=512)
            logger.info("Loaded local BGE reranker")

    def rerank(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        documents: list of dicts with keys: 'text', 'metadata', 'id', etc.
        Returns re‑ranked list of documents (same dicts).
        """
        if not documents:
            return []

        if self.use_cohere:
            return self._rerank_cohere(query, documents, top_k)
        else:
            return self._rerank_local(query, documents, top_k)

    def _rerank_cohere(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        texts = [doc["text"] for doc in documents]
        try:
            response = self.co.rerank(
                query=query,
                documents=texts,
                top_n=top_k,
                model="rerank-english-v3.0"
            )
            # Map results back to original documents
            reranked = []
            for r in response.results:
                idx = r.index
                reranked.append(documents[idx])
            return reranked
        except Exception as e:
            logger.error(f"Cohere rerank failed: {e}")
            return documents[:top_k]

    def _rerank_local(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        pairs = [[query, doc["text"]] for doc in documents]
        scores = self.model.predict(pairs)
        # Sort by score descending
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        reranked = [documents[i] for i in sorted_indices[:top_k]]
        return reranked

reranker = Reranker()