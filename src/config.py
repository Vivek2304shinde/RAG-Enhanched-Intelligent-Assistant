# src/config.py
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Qdrant
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection_name: str = "financial_chunks"
    
    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    
    # Redis
    redis_url: Optional[str] = None
    
    # Neo4j
    # Neo4j
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None
    neo4j_database: Optional[str] = None
    
    # LLM
    openai_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    
    # Embedding model
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_dim: int = 1024  # BGE-M3 dimension
    
    # Paths
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    
    # Pipeline control
    chunk_size: int = 512   # tokens (approx)
    chunk_overlap: int = 50
    batch_size: int = 100   # for Qdrant upload
    enable_graph_extraction: bool = True   # <--- ADD THIS LINE

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()