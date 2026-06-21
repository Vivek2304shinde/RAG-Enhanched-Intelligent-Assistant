# src/etl/embedder.py
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
# from fastembed.embedding import SparseTextEmbedding
from src.config import settings
from src.utils.logging import logger
import numpy as np
import asyncio

class Embedder:
    def __init__(self):
        self.dense_model = SentenceTransformer(settings.embedding_model_name)
        # BGE-M3 outputs 1024 dims
        self.dim = settings.embedding_dim
        # Sparse embedder (SPLADE)
        self.sparse_model = SparseTextEmbedding(model_name="prithvida/Splade_PP_en_v1")
        logger.info("Embedding models loaded")
    
    def embed_dense(self, texts: list) -> np.ndarray:
        """Return dense embeddings as numpy array."""
        return self.dense_model.encode(texts, normalize_embeddings=True)
    
    def embed_sparse(self, texts: list) -> list:
        """Return list of sparse vector dicts {indices: values}."""
        embeddings = list(self.sparse_model.embed(texts))
        sparse_list = []
        for emb in embeddings:
            # emb is a SparseEmbedding object with .indices and .values
            sparse_list.append({
                "indices": emb.indices.tolist(),
                "values": emb.values.tolist()
            })
        return sparse_list
    
    def embed_batch(self, texts: list):
        """Return both dense and sparse for a batch."""
        dense = self.embed_dense(texts)
        sparse = self.embed_sparse(texts)
        return dense, sparse

embedder = Embedder()