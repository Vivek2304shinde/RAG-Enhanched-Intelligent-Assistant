# from neo4j import GraphDatabase

# URI = "neo4j+s://e4bb0e99.databases.neo4j.io"

# driver = GraphDatabase.driver(
#     URI,
#     auth=("e4bb0e99", "PASSWORD")
# )

# driver.verify_connectivity()

# print("CONNECTED")
# driver.close()

from src.storage.graph_store import graph_store

print(graph_store.run_cypher(
    "RETURN 1 as x"
))

from src.storage.graph_store import graph_store

graph_store.run_cypher(
    """
    CREATE (n:Test {
        name:'vivek'
    })
    """
)

print("DONE")

print(
    graph_store.run_cypher(
        """
        MATCH (n:Test)
        RETURN n.name as name
        """
    )
)