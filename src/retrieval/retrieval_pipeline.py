# src/retrieval/retrieval_pipeline.py
from typing import List, Dict, Optional
from src.storage.qdrant_client import qdrant_client
from src.retrieval.query_understanding import query_understanding
from src.retrieval.query_expansion import query_expansion
from src.retrieval.reranker import reranker
from src.cache.semantic_cache import cache
from src.utils.logging import logger
from qdrant_client.http import models as qdrant_models

class RetrievalPipeline:
    def __init__(self):
        self.top_k_retrieve = 20   # number of candidates from Qdrant
        self.top_k_rerank = 5      # final number after reranking

    def retrieve(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Main entry point: returns list of chunks with text and metadata.
        """
        # 1. Check cache
        cached_result = cache.get(query)
        if cached_result:
            return cached_result

        # 2. Query understanding (extract filters)
        understood = query_understanding.classify_query(query)
        if filters is None:
            filters = {}
        # Merge with understood filters
        if understood.get("agencies"):
            filters["agency"] = understood["agencies"]
        if understood.get("time_range"):
            filters["year"] = list(range(understood["time_range"]["start"], understood["time_range"]["end"] + 1))
        # Additional metadata filters

        # 3. Query expansion (HyDE + MultiQuery)
        # Generate HyDE document and multiple queries
        hyde_doc = query_expansion.generate_hyde_document(query)
        multi_queries = query_expansion.generate_multi_queries(query, n=3)

        # 4. Perform retrieval for each query variant
        all_chunks = []
        seen_ids = set()

        for q in [query] + multi_queries + [hyde_doc]:
            # Search with Qdrant (hybrid)
            hits = self._hybrid_search(q, filters, self.top_k_retrieve)
            for hit in hits:
                chunk_id = hit.payload["chunk_id"]
                if chunk_id not in seen_ids:
                    seen_ids.add(chunk_id)
                    all_chunks.append({
                        "id": chunk_id,
                        "text": hit.payload["text"],
                        "metadata": hit.payload.get("metadata", {}),
                        "score": hit.score,
                        "doc_id": hit.payload.get("doc_id")
                    })

        # 5. Rerank
        reranked = reranker.rerank(query, all_chunks, top_k=self.top_k_rerank)

        # 6. Cache the result
        cache.set(query, reranked)

        return reranked

    def _hybrid_search(self, query: str, filters: Dict, limit: int) -> List:
        """Execute hybrid search on Qdrant."""
        # Generate query embeddings
        from src.etl.embedder import embedder
        dense_vec, sparse_vec = embedder.embed_batch([query])
        dense_vec = dense_vec[0].tolist()
        sparse_indices = sparse_vec[0]["indices"]
        sparse_values = sparse_vec[0]["values"]

        # Build filter if any
        filter_conditions = []
        if filters:
            # Example: if "agency" filter
            if "agency" in filters:
                agencies = filters["agency"] if isinstance(filters["agency"], list) else [filters["agency"]]
                filter_conditions.append(
                    qdrant_models.FieldCondition(
                        key="agency",
                        match=qdrant_models.MatchAny(any=agencies)
                    )
                )
            if "year" in filters:
                years = filters["year"] if isinstance(filters["year"], list) else [filters["year"]]
                filter_conditions.append(
                    qdrant_models.FieldCondition(
                        key="year",
                        match=qdrant_models.MatchAny(any=years)
                    )
                )
        filter_condition = qdrant_models.Filter(must=filter_conditions) if filter_conditions else None

        # Perform search
        search_result = qdrant_client.client.search(
            collection_name=qdrant_client.collection_name,
            query_vector=(
                qdrant_models.NamedVector(
                    name="dense",
                    vector=dense_vec
                ),
                qdrant_models.NamedSparseVector(
                    name="sparse",
                    vector=qdrant_models.SparseVector(
                        indices=sparse_indices,
                        values=sparse_values
                    )
                )
            ),
            query_filter=filter_condition,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        return search_result

retrieval_pipeline = RetrievalPipeline()