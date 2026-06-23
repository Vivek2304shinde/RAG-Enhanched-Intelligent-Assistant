# src/storage/neo4j_client.py
from neo4j import GraphDatabase, AsyncGraphDatabase
from src.config import settings
from src.utils.logging import logger
from typing import List, Dict, Any

class Neo4jClient:
    def __init__(self):
        self.uri = settings.neo4j_uri
        self.user = settings.neo4j_user
        self.password = settings.neo4j_password
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        logger.info("Neo4j driver initialized")
    
    def close(self):
        self.driver.close()
    
    def run_cypher(self, query: str, parameters: dict = None) -> List[Dict]:
        """Execute a Cypher query and return results as list of dicts."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def merge_node(self, label: str, key_property: str, key_value: Any, properties: dict = None):
        """Merge a node with unique constraint on key_property."""
        query = f"""
        MERGE (n:{label} {{{key_property}: $key_value}})
        SET n += $properties
        RETURN n
        """
        params = {"key_value": key_value, "properties": properties or {}}
        return self.run_cypher(query, params)
    
    def merge_relationship(self, from_label: str, from_key: str, from_value: Any,
                           to_label: str, to_key: str, to_value: Any,
                           rel_type: str, properties: dict = None):
        """Merge a relationship between two existing nodes."""
        query = f"""
        MATCH (a:{from_label} {{{from_key}: $from_value}})
        MATCH (b:{to_label} {{{to_key}: $to_value}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties
        RETURN r
        """
        params = {
            "from_value": from_value,
            "to_value": to_value,
            "properties": properties or {}
        }
        return self.run_cypher(query, params)
    
    def create_constraints(self):
        """Create uniqueness constraints for node keys."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Ministry) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Scheme) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Bank) REQUIRE b.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (st:State) REQUIRE st.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (be:Beneficiary) REQUIRE be.category IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (sec:Sector) REQUIRE sec.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Regulation) REQUIRE r.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tender) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:BudgetAllocation) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        ]
        for c in constraints:
            try:
                self.run_cypher(c)
            except Exception as e:
                logger.warning(f"Constraint creation failed (may already exist): {e}")
        logger.info("Constraints ensured")

# Singleton
neo4j_client = Neo4jClient()