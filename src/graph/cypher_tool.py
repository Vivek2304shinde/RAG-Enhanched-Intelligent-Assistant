# src/graph/cypher_tool.py
from src.storage.graph_store import graph_store
from src.utils.logging import logger
from typing import List, Dict

class CypherTool:
    @staticmethod
    def run_read_query(query: str, params: dict = None) -> List[Dict]:
        """Execute a read‑only Cypher query and return results."""
        # Safety: forbid write queries (MERGE, CREATE, DELETE, SET, etc.)
        forbidden = ["MERGE", "CREATE", "DELETE", "DETACH", "SET", "REMOVE", "DROP"]
        upper_query = query.upper()
        for word in forbidden:
            if word in upper_query:
                raise ValueError(f"Write operation '{word}' not allowed in this tool.")
        return graph_store.run_cypher(query, params)
    
    @staticmethod
    def get_schemes_by_ministry(ministry_name: str) -> List[str]:
        query = """
        MATCH (s:Scheme)-[:IMPLEMENTS]->(m:Ministry {name: $ministry})
        RETURN s.name AS scheme
        """
        results = CypherTool.run_read_query(query, {"ministry": ministry_name})
        return [r["scheme"] for r in results]

    @staticmethod
    def get_beneficiaries_for_scheme(scheme_name: str) -> List[str]:
        query = """
        MATCH (b:Beneficiary)-[:ELIGIBLE_FOR]->(s:Scheme {name: $scheme})
        RETURN b.category AS beneficiary
        """
        results = CypherTool.run_read_query(query, {"scheme": scheme_name})
        return [r["beneficiary"] for r in results]