# src/etl/pipeline.py
import uuid
from typing import List, Dict
from src.config import settings
from src.utils.logging import logger
from src.storage.supabase_client import supabase_client
from src.storage.qdrant_client import qdrant_client
from src.etl.downloader import PDFDownloader
from src.etl.parser import PDFParser
from src.etl.chunker import chunk_elements
from src.etl.embedder import embedder
from qdrant_client.http import models as qdrant_models
import numpy as np
import time

class ETLPipeline:
    def __init__(self):
        self.downloader = PDFDownloader()
        self.batch_size = settings.batch_size
    
    def process_pdf(self, source: str, is_url: bool = True) -> str:
        """Process a single PDF from URL or local path."""
        start_time = time.time()
        
        # 1. Download if URL
        if is_url:
            pdf_path = self.downloader.download_from_url(source)
        else:
            pdf_path = source
        
        logger.info(f"Processing {pdf_path}")
        
        # 2. Parse
        parser = PDFParser(pdf_path)
        raw_chunks, tables = parser.parse()
        doc_metadata = parser.metadata
        
        # 3. Chunk
        final_chunks = chunk_elements(raw_chunks)
        logger.info(f"Generated {len(final_chunks)} chunks from {pdf_path}")
        
        # 4. Insert document record in Supabase
        doc_data = {
            "title": doc_metadata.get("title", "Unknown"),
            "source_url": source if is_url else None,
            "agency": doc_metadata.get("agency", "Unknown"),
            "doc_type": doc_metadata.get("doc_type", "unknown"),
            "year": doc_metadata.get("year"),
            "pdf_path": pdf_path,
            "total_pages": doc_metadata.get("total_pages", 0),
        }
        doc_id = supabase_client.insert_document(doc_data)
        
        # 5. Insert tables (if any)
        for tbl in tables:
            supabase_client.insert_table({
                "doc_id": doc_id,
                "page_number": tbl.get("page", 0),
                "table_data": tbl.get("data", []),
                "caption": "",
            })
        
        # 6. Prepare chunks for embedding & storage
        chunk_texts = [c["text"] for c in final_chunks]
        # Generate embeddings in batches
        all_chunk_ids = []
        total_chunks = len(chunk_texts)
        qdrant_points = []
        
        for i in range(0, total_chunks, self.batch_size):
            batch = chunk_texts[i:i+self.batch_size]
            batch_metadata = final_chunks[i:i+self.batch_size]
            
            dense, sparse = embedder.embed_batch(batch)
            
            # Prepare Supabase chunk records
            supabase_chunks = []
            for j, (text, meta) in enumerate(zip(batch, batch_metadata)):
                chunk_id = str(uuid.uuid4())
                supabase_chunks.append({
                    "id": chunk_id,
                    "doc_id": doc_id,
                    "chunk_index": i + j,
                    "text": text,
                    "page_number": meta["metadata"].get("page", 0),
                    "section_heading": meta["metadata"].get("section", ""),
                    "metadata": meta["metadata"],
                })
                all_chunk_ids.append(chunk_id)
            
            # Insert into Supabase (bulk)
            supabase_client.insert_chunks_batch(supabase_chunks)
            
            # Prepare Qdrant points
            for j, chunk_id in enumerate(all_chunk_ids[i:i+self.batch_size]):
                payload = {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "text": batch[j],
                    "metadata": batch_metadata[j]["metadata"],
                    "agency": doc_metadata.get("agency"),
                    "year": doc_metadata.get("year"),
                    "doc_type": doc_metadata.get("doc_type"),
                }
                # Dense vector
                dense_vec = dense[j].tolist() if isinstance(dense[j], np.ndarray) else dense[j]
                # Sparse vector
                sparse_vec = sparse[j]
                point = qdrant_models.PointStruct(
                    id=chunk_id,
                    vector={
                        "dense": dense_vec,
                        "sparse": qdrant_models.SparseVector(
                            indices=sparse_vec["indices"],
                            values=sparse_vec["values"],
                        )
                    },
                    payload=payload,
                )
                qdrant_points.append(point)
        
        # Upload all points to Qdrant
        qdrant_client.upsert_points(qdrant_points)
        
        elapsed = time.time() - start_time
        logger.info(f"Finished processing {pdf_path} in {elapsed:.2f}s. {total_chunks} chunks inserted.")
        return doc_id
    
    def process_folder(self, folder_path: str = None):
        """Process all PDFs in a folder."""
        if not folder_path:
            folder_path = settings.raw_data_dir
        downloader = PDFDownloader(folder_path)
        pdf_files = downloader.scan_local_folder()
        for pdf in pdf_files:
            self.process_pdf(pdf, is_url=False)