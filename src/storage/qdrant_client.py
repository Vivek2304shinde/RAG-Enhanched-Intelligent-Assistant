# src/storage/qdrant_client.py
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import settings
from src.utils.logging import logger

class QdrantClientWrapper:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        self.collection_name = settings.qdrant_collection_name
        self._ensure_collection()
        logger.info(f"Qdrant client initialized for {self.collection_name}")
    
    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=settings.embedding_dim,
                        distance=models.Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=False,
                        )
                    )
                },
                optimizers_config=models.OptimizersConfigDiff(
                    default_segment_number=2,
                ),
                replication_factor=2,  # adjust if cluster size > 1
            )
            logger.info(f"Created collection {self.collection_name}")
        else:
            logger.info(f"Collection {self.collection_name} already exists")
    
    def upsert_points(self, points: list):
        """points: list of dict with id, vector, payload."""
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        logger.info(f"Upserted {len(points)} points")

qdrant_client = QdrantClientWrapper()