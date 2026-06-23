from src.storage.neo4j_client import neo4j_client
from src.storage.neo4j_http_client import neo4j_http_client

from src.utils.logging import logger


class GraphStore:

    def __init__(self):

        self.mode = None

        try:

            neo4j_client.run_cypher("RETURN 1")

            self.mode = "bolt"

            logger.info("Using Neo4j Bolt")

        except Exception as e:

            logger.warning(f"Bolt failed: {e}")

            self.mode = "http"

            logger.info("Using Neo4j HTTP API")
    
    def merge_node(self, *args, **kwargs):
        if self.mode == "bolt":
            return neo4j_client.merge_node(*args, **kwargs)

        raise NotImplementedError(
            "merge_node not supported in HTTP fallback"
        )
    
    def merge_relationship(self, *args, **kwargs):
        if self.mode == "bolt":
            return neo4j_client.merge_relationship(
                *args,
                **kwargs
        )

        raise NotImplementedError(
            "merge_relationship not supported in HTTP fallback"
        )

    def run_cypher(self, query, params=None):

        if self.mode == "bolt":

            return neo4j_client.run_cypher(
                query,
                params
            )

        return neo4j_http_client.run_cypher(
            query,
            params
        )

    def merge_node(
        self,
        label,
        key_property,
        key_value,
        properties=None
    ):

        query = f"""
        MERGE (n:{label} {{{key_property}: $key_value}})
        SET n += $properties
        RETURN n
        """

        return self.run_cypher(
            query,
            {
                "key_value": key_value,
                "properties": properties or {}
            }
        )

    def merge_relationship(
        self,
        from_label,
        from_key,
        from_value,
        to_label,
        to_key,
        to_value,
        rel_type,
        properties=None
    ):

        query = f"""
        MATCH (a:{from_label} {{{from_key}: $from_value}})
        MATCH (b:{to_label} {{{to_key}: $to_value}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties
        RETURN r
        """

        return self.run_cypher(
            query,
            {
                "from_value": from_value,
                "to_value": to_value,
                "properties": properties or {}
            }
        )

    def create_constraints(self):

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

            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE"

        ]

        for c in constraints:

            try:

                self.run_cypher(c)

            except Exception as e:

                logger.warning(
                    f"Constraint creation failed: {e}"
                )

        logger.info("Constraints ensured")


graph_store = GraphStore()