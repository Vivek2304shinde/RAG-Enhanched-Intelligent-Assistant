# scripts/clean_neo4j_nodes.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.neo4j_client import neo4j_client
from src.utils.logging import logger

def clean_all_nodes():
    # Get all nodes with newline in name
    query = """
    MATCH (n)
    WHERE n.name IS NOT NULL AND n.name CONTAINS '\n'
    RETURN elementId(n) AS id, n.name AS bad_name, labels(n) AS labels
    """
    results = neo4j_client.run_cypher(query)
    if not results:
        logger.info("No nodes with newlines found.")
        return

    logger.info(f"Found {len(results)} nodes with newlines.")
    for record in results:
        bad_id = record["id"]
        bad_name = record["bad_name"]
        labels = record["labels"]
        clean_name = " ".join(bad_name.split())
        if clean_name == bad_name:
            continue

        # Check if good node exists
        label_str = ":".join(labels)
        check = neo4j_client.run_cypher(
            f"MATCH (g:{label_str} {{name: $clean}}) RETURN elementId(g) AS id",
            {"clean": clean_name}
        )
        if not check:
            # No duplicate, just rename
            neo4j_client.run_cypher(
                f"MATCH (n) WHERE elementId(n) = $id SET n.name = $clean",
                {"id": bad_id, "clean": clean_name}
            )
            logger.info(f"Renamed: {bad_name} -> {clean_name}")
            continue

        # Duplicate exists: copy relationships
        good_id = check[0]["id"]
        logger.info(f"Merging '{bad_name}' into '{clean_name}'")

        # Copy outgoing relationships
        outgoing = neo4j_client.run_cypher(
            """
            MATCH (bad) WHERE elementId(bad) = $bad_id
            OPTIONAL MATCH (bad)-[r]->(other)
            RETURN type(r) AS rel_type, elementId(other) AS other_id, properties(r) AS props
            """,
            {"bad_id": bad_id}
        )
        for rel in outgoing:
            if rel["other_id"] is None:
                continue
            rel_type = rel["rel_type"]
            other_id = rel["other_id"]
            props = rel["props"] or {}
            # Create relationship from good to other
            create_query = f"""
            MATCH (good) WHERE elementId(good) = $good_id
            MATCH (other) WHERE elementId(other) = $other_id
            CREATE (good)-[r:{rel_type}]->(other)
            SET r = $props
            """
            neo4j_client.run_cypher(create_query, {
                "good_id": good_id,
                "other_id": other_id,
                "props": props
            })

        # Copy incoming relationships
        incoming = neo4j_client.run_cypher(
            """
            MATCH (bad) WHERE elementId(bad) = $bad_id
            OPTIONAL MATCH (other)-[r]->(bad)
            RETURN type(r) AS rel_type, elementId(other) AS other_id, properties(r) AS props
            """,
            {"bad_id": bad_id}
        )
        for rel in incoming:
            if rel["other_id"] is None:
                continue
            rel_type = rel["rel_type"]
            other_id = rel["other_id"]
            props = rel["props"] or {}
            # Create relationship from other to good
            create_query = f"""
            MATCH (good) WHERE elementId(good) = $good_id
            MATCH (other) WHERE elementId(other) = $other_id
            CREATE (other)-[r:{rel_type}]->(good)
            SET r = $props
            """
            neo4j_client.run_cypher(create_query, {
                "good_id": good_id,
                "other_id": other_id,
                "props": props
            })

        # Delete bad node
        neo4j_client.run_cypher(
            "MATCH (n) WHERE elementId(n) = $id DETACH DELETE n",
            {"id": bad_id}
        )
        logger.info(f"Deleted duplicate node: {bad_name}")

if __name__ == "__main__":
    clean_all_nodes()