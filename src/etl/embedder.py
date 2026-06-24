from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from src.config import settings
from src.utils.logging import logger
import numpy as np


class Embedder:

    def __init__(self):
        print("EMBEDDER INITIALIZED")

        self.dense_model = SentenceTransformer(
            settings.embedding_model_name
        )

        self.dim = settings.embedding_dim

        try:

            self.sparse_model = SparseTextEmbedding(
                model_name="prithvida/Splade_PP_en_v1"
            )

            self.hybrid_enabled = True

            logger.info(
                "SPLADE loaded successfully"
            )

        except Exception as e:

            logger.warning(
                f"SPLADE unavailable, falling back to dense retrieval: {e}"
            )

            self.sparse_model = None
            self.hybrid_enabled = False

    def embed_dense(self, texts: list) -> np.ndarray:

        return self.dense_model.encode(
            texts,
            normalize_embeddings=True
        )

    def embed_sparse(self, texts: list) -> list:

        if self.sparse_model is None:

            return [
                {
                    "indices": [],
                    "values": []
                }
                for _ in texts
            ]

        embeddings = list(
            self.sparse_model.embed(texts)
        )

        sparse_list = []

        for emb in embeddings:

            sparse_list.append(
                {
                    "indices": emb.indices.tolist(),
                    "values": emb.values.tolist()
                }
            )

        return sparse_list

    def embed_batch(self, texts: list):

        dense = self.embed_dense(texts)

        sparse = self.embed_sparse(texts)

        return dense, sparse


embedder = Embedder()