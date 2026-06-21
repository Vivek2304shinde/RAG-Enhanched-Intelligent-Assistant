from supabase import create_client, Client
from src.config import settings
from src.utils.logging import logger

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        logger.info("Supabase client initialized")
    
    def insert_document(self, doc_data: dict) -> str:
        """Insert document record, return doc_id."""
        res = self.client.table("documents").insert(doc_data).execute()
        return res.data[0]["id"]
    
    def insert_chunk(self, chunk_data: dict) -> str:
        res = self.client.table("chunks").insert(chunk_data).execute()
        return res.data[0]["id"]
    
    def insert_table(self, table_data: dict) -> str:
        res = self.client.table("extracted_tables").insert(table_data).execute()
        return res.data[0]["id"]
    
    def insert_chunks_batch(self, chunks: list) -> list:
        """Bulk insert chunks."""
        res = self.client.table("chunks").insert(chunks).execute()
        return [row["id"] for row in res.data]

supabase_client = SupabaseClient()