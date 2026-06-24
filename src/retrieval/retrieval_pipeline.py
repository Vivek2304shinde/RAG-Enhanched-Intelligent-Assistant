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
        self.top_k_retrieve = 20
        self.top_k_rerank = 5

    def retrieve(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Main entry point: returns list of chunks with text and metadata.
        """
        logger.info("STEP 1 - Retrieval started")

        # 1. Check cache
        cached_result = cache.get(query)
        if cached_result:
            logger.info("STEP 2 - Cache hit")
            return cached_result

        logger.info("STEP 3 - Query understanding")

        # 2. Query understanding (extract filters)
        understood = query_understanding.classify_query(query)
        logger.info(f"STEP 4 - Query understood: {understood}")

        # if filters is None:
        filters = {}

        #TEMPARILY DISABLED: Merge with understood filter
        # Merge with understood filters
        # if understood.get("agencies"):
        #     filters["agency"] = understood["agencies"]

        # if understood.get("time_range"):
        #     filters["year"] = list(
        #         range(
        #             understood["time_range"]["start"],
        #             understood["time_range"]["end"] + 1
        #         )
        #     )

        logger.info("STEP 5 - HyDE generation")

        # 3. Query expansion (HyDE + MultiQuery)
        hyde_doc = query_expansion.generate_hyde_document(query)
        logger.info("STEP 6 - Multi-query generation")
        multi_queries = query_expansion.generate_multi_queries(query, n=3)
        logger.info(f"STEP 7 - Generated {len(multi_queries)} query variants")

        # 4. Perform retrieval for each query variant
        all_chunks = []
        seen_ids = set()

        queries = [query] + multi_queries + [hyde_doc]
        logger.info(f"STEP 8 - Running retrieval on {len(queries)} queries")

        for i, q in enumerate(queries):
            logger.info(f"STEP 9.{i+1} - Searching query variant")
            hits = self._hybrid_search(q, filters, self.top_k_retrieve)
            logger.info(f"STEP 9.{i+1} - Retrieved {len(hits)} hits")

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

        logger.info(f"STEP 10 - Total unique chunks: {len(all_chunks)}")

        # 5. Rerank
        logger.info("STEP 11 - Reranking")
        reranked = reranker.rerank(query, all_chunks, top_k=self.top_k_rerank)
        logger.info(f"STEP 12 - Reranked to {len(reranked)} chunks")

        # 6. Cache the result
        cache.set(query, reranked)
        logger.info("STEP 13 - Cached")
        logger.info("STEP 14 - Retrieval complete")

        return reranked

    def _hybrid_search(self, query: str, filters: Dict, limit: int) -> List:
        """
        Hybrid retrieval using:
        1. Dense search
        2. Sparse search
        3. Late fusion
        """

        logger.info(f"HYBRID SEARCH START: {query[:80]}")

        from src.etl.embedder import embedder

        logger.info("HYBRID SEARCH - Generating embeddings")

        dense_vec, sparse_vec = embedder.embed_batch([query])

        dense_vec = dense_vec[0].tolist()

        sparse_indices = sparse_vec[0]["indices"]
        sparse_values = sparse_vec[0]["values"]
        has_sparse = (
            len(sparse_indices) > 0
        )

        logger.info(
            f"HYBRID SEARCH - Dense dims={len(dense_vec)} "
            f"Sparse terms={len(sparse_indices)}"
        )

        # --------------------------------------------------
        # Build filters
        # --------------------------------------------------

        filter_conditions = []

        if filters:

            if "agency" in filters:

                agencies = (
                    filters["agency"]
                    if isinstance(filters["agency"], list)
                    else [filters["agency"]]
                )

                filter_conditions.append(
                    qdrant_models.FieldCondition(
                        key="agency",
                        match=qdrant_models.MatchAny(any=agencies)
                    )
                )

            if "year" in filters:

                years = (
                    filters["year"]
                    if isinstance(filters["year"], list)
                    else [filters["year"]]
                )

                filter_conditions.append(
                    qdrant_models.FieldCondition(
                        key="year",
                        match=qdrant_models.MatchAny(any=years)
                    )
                )

        filter_condition = (
            qdrant_models.Filter(must=filter_conditions)
            if filter_conditions
            else None
        )

        # --------------------------------------------------
        # DENSE SEARCH
        # --------------------------------------------------

        logger.info("HYBRID SEARCH - Dense retrieval")

        dense_response = qdrant_client.client.query_points(
            collection_name=qdrant_client.collection_name,
            query=dense_vec,
            using="dense",
            query_filter=filter_condition,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )

        dense_hits = dense_response.points

        logger.info(
            f"HYBRID SEARCH - Dense returned {len(dense_hits)} hits"
        )

        # --------------------------------------------------
        # SPARSE SEARCH
        # --------------------------------------------------

        sparse_hits = []

        if has_sparse:

            logger.info(
                "HYBRID SEARCH - Sparse retrieval"
            )

            sparse_response = qdrant_client.client.query_points(
                collection_name=qdrant_client.collection_name,
                query=qdrant_models.SparseVector(
                    indices=sparse_indices,
                    values=sparse_values
                ),
                using="sparse",
                query_filter=filter_condition,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            sparse_hits = sparse_response.points

            logger.info(
                f"HYBRID SEARCH - Sparse returned {len(sparse_hits)} hits"
            )

        else:

            logger.warning(
                "HYBRID SEARCH - Sparse unavailable, using dense retrieval only"
            )

        # --------------------------------------------------
        # LATE FUSION
        # --------------------------------------------------

        fused = {}

        for hit in dense_hits:

            fused[str(hit.id)] = hit

        for hit in sparse_hits:

            if str(hit.id) not in fused:
                fused[str(hit.id)] = hit

            else:
                if hit.score > fused[str(hit.id)].score:
                    fused[str(hit.id)] = hit

        hits = list(fused.values())

        hits.sort(
            key=lambda x: x.score,
            reverse=True
        )

        hits = hits[:limit]

        logger.info(
            f"HYBRID SEARCH - Final fused hits: {len(hits)}"
        )

        return hits
retrieval_pipeline = RetrievalPipeline()