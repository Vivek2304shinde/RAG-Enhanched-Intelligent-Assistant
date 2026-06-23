# src/graph/graph_pipeline.py
import re
import uuid
from typing import List, Dict
from src.storage.supabase_client import supabase_client
from src.storage.neo4j_client import neo4j_client
from src.graph.entity_extractor import entity_extractor
from src.graph.relation_extractor import relation_extractor
from src.utils.logging import logger
from src.config import settings


class GraphPipeline:
    def __init__(self):
        # Ensure constraints exist
        neo4j_client.create_constraints()
        logger.info("Graph pipeline initialized")

    def _clean_name(self, name: str) -> str:
        """Clean entity name: remove newlines, multiple spaces."""
        return re.sub(r'\s+', ' ', name).strip()

    def process_chunk(self, chunk: Dict):
        """Process a single chunk: extract entities, relations, write to Neo4j."""
        text = chunk.get("text", "")
        if not text:
            return
        doc_id = chunk.get("doc_id")
        if not doc_id:
            logger.warning("Chunk missing doc_id, skipping")
            return

        # 1. Extract entities
        entities = entity_extractor.extract(text)
        if not entities:
            return

        # Build a mapping from cleaned name -> entity_type (capitalized)
        name_to_type = {}
        for ent in entities:
            cleaned_name = self._clean_name(ent["name"])
            name_to_type[cleaned_name] = ent["entity_type"].capitalize()

        # 2. Extract relations
        relations = relation_extractor.extract_relations(text, entities)

        # 3. Merge entities and create document node if not exists
        for ent in entities:
            label = ent["entity_type"].capitalize()
            name = self._clean_name(ent["name"])
            props = ent.get("attributes", {})
            neo4j_client.merge_node(label, "name", name, props)

        # 4. Ensure Document node exists
        neo4j_client.run_cypher(
            "MERGE (d:Document {id: $doc_id}) RETURN d",
            {"doc_id": doc_id}
        )

        # 5. Link each entity to the document with MENTIONED_IN
        for ent in entities:
            label = ent["entity_type"].capitalize()
            name = self._clean_name(ent["name"])
            neo4j_client.run_cypher(
                f"""
                MATCH (e:{label} {{name: $name}})
                MATCH (d:Document {{id: $doc_id}})
                MERGE (e)-[:MENTIONED_IN]->(d)
                """,
                {"name": name, "doc_id": doc_id}
            )

        # 6. Merge relationships (using the name_to_type mapping for type lookup)
        for rel in relations:
            subj_name = rel.get("subject")
            rel_type = rel.get("relation")
            obj_name = rel.get("object")
            if not all([subj_name, rel_type, obj_name]):
                continue

            subj_name = self._clean_name(subj_name)
            obj_name = self._clean_name(obj_name)
            subj_type = name_to_type.get(subj_name)
            obj_type = name_to_type.get(obj_name)

            if not subj_type or not obj_type:
                logger.warning(f"Could not find types for {subj_name} or {obj_name}, skipping")
                continue

            # Merge relationship
            neo4j_client.merge_relationship(
                from_label=subj_type, from_key="name", from_value=subj_name,
                to_label=obj_type, to_key="name", to_value=obj_name,
                rel_type=rel_type,
                properties={"source_doc": doc_id}
            )

        logger.info(f"Processed chunk with {len(entities)} entities and {len(relations)} relations")

    def process_document(self, doc_id: str):
        """Fetch all chunks for a document and process them."""
        res = supabase_client.client.table("chunks").select("*").eq("doc_id", doc_id).execute()
        chunks = res.data
        logger.info(f"Processing {len(chunks)} chunks for document {doc_id}")
        for chunk in chunks:
            chunk["doc_id"] = doc_id
            self.process_chunk(chunk)

    def process_all_unprocessed(self):
        """Process all documents that haven't been graph‑processed yet."""
        res = supabase_client.client.table("documents").select("id").execute()
        doc_ids = [row["id"] for row in res.data]
        for doc_id in doc_ids:
            result = neo4j_client.run_cypher("MATCH (d:Document {id: $doc_id}) RETURN d", {"doc_id": doc_id})
            if not result:
                logger.info(f"Processing document {doc_id} for graph")
                self.process_document(doc_id)
            else:
                logger.info(f"Document {doc_id} already in graph, skipping")

graph_pipeline = GraphPipeline()