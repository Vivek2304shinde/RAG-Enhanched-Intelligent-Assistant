# test_phase2.py

from src.storage.neo4j_client import neo4j_client
from src.storage.supabase_client import supabase_client
from src.graph.graph_pipeline import graph_pipeline

DOC_ID = "04972721-2bd9-4839-a20b-946cc22ec2fb"


print("\n========================")
print("1. Testing Neo4j Connection")
print("========================")

try:
    result = neo4j_client.run_cypher(
        "RETURN 'Neo4j Connected' AS msg"
    )
    print(result)

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("2. Creating Constraints")
print("========================")

try:
    neo4j_client.create_constraints()
    print("Constraints created successfully")

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("3. Checking Supabase")
print("========================")

try:
    docs = (
        supabase_client.client
        .table("documents")
        .select("*")
        .execute()
    )

    print("Documents found:", len(docs.data))

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("4. Fetching Document")
print("========================")

try:
    doc = (
        supabase_client.client
        .table("documents")
        .select("*")
        .eq("id", DOC_ID)
        .execute()
    )

    print(doc.data)

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("5. Running Graph Pipeline")
print("========================")

try:
    graph_pipeline.process_document(DOC_ID)
    print("Graph pipeline finished")

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("6. Total Nodes")
print("========================")

try:
    result = neo4j_client.run_cypher(
        """
        MATCH (n)
        RETURN count(n) AS total_nodes
        """
    )

    print(result)

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("7. Total Relationships")
print("========================")

try:
    result = neo4j_client.run_cypher(
        """
        MATCH ()-[r]->()
        RETURN count(r) AS total_relationships
        """
    )

    print(result)

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("8. Labels Present")
print("========================")

try:
    result = neo4j_client.run_cypher(
        """
        CALL db.labels()
        """
    )

    for r in result:
        print(r)

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("9. Relationship Types")
print("========================")

try:
    result = neo4j_client.run_cypher(
        """
        CALL db.relationshipTypes()
        """
    )

    for r in result:
        print(r)

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("10. Sample Graph")
print("========================")

try:
    result = neo4j_client.run_cypher(
        """
        MATCH (a)-[r]->(b)
        RETURN a,r,b
        LIMIT 10
        """
    )

    print(result)

except Exception as e:
    print("FAILED:", e)


print("\n========================")
print("TEST COMPLETE")
print("========================")