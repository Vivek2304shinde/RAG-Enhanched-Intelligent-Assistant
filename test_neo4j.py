# from neo4j import GraphDatabase

# driver = GraphDatabase.driver(
#     "neo4j+s://e4bb0e99.databases.neo4j.io",
#     auth=("e4bb0e99",
#           "1fGi9xPBo4NAW0a7BtV31rI_V1k_8JfiBAL_5cmh3kU")
# )

# with driver.session(
#         database="e4bb0e99",
#         default_access_mode="WRITE") as session:

#     print(session.run("RETURN 1").single())

# driver.close()

# import ssl
# import socket

# hostname = "e4bb0e99.databases.neo4j.io"

# ctx = ssl.create_default_context()

# with socket.create_connection((hostname, 7687)) as sock:
#     with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
#         cert = ssock.getpeercert()

# print(cert)

# import ssl
# import socket

# hostname = "e4bb0e99.databases.neo4j.io"

# ctx = ssl._create_unverified_context()

# with socket.create_connection((hostname, 7687)) as sock:
#     with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
#         print(ssock.getpeercert())

# # test_ssl.py

# from neo4j import GraphDatabase

# URI = "neo4j+s://e4bb0e99.databases.neo4j.io"

# driver = GraphDatabase.driver(
#     URI,
#     auth=(
#         "e4bb0e99",
#         "1fGi9xPBo4NAW0a7BtV31rI_V1k_8JfiBAL_5cmh3kU"
#     ),
#     encrypted=True,
#     trust="TRUST_ALL_CERTIFICATES"
# )

# with driver.session() as session:
#     result = session.run("RETURN 1 AS x")
#     print(result.single())

# driver.close()

# from neo4j import GraphDatabase
# import ssl

# ssl_context = ssl._create_unverified_context()

# driver = GraphDatabase.driver(
#     "neo4j+s://e4bb0e99.databases.neo4j.io",
#     auth=(
#         "e4bb0e99",
#         "1fGi9xPBo4NAW0a7BtV31rI_V1k_8JfiBAL_5cmh3kU"
#     ),
#     ssl_context=ssl_context
# )

# with driver.session() as session:
#     print(session.run("RETURN 1").single())


# test_neo4j.py

# from neo4j import GraphDatabase
# import certifi

# driver = GraphDatabase.driver(
#     "neo4j+s://e4bb0e99.databases.neo4j.io",
#     auth=(
#         "e4bb0e99",
#         "1fGi9xPBo4NAW0a7BtV31rI_V1k_8JfiBAL_5cmh3kU"
#     ),
#     trusted_certificates=certifi.where()
# )

# with driver.session(
#         database="e4bb0e99") as session:

#     result = session.run("RETURN 1 AS x")
#     print(result.single())

# driver.close()

# import requests

# url = "https://e4bb0e99.databases.neo4j.io/db/e4bb0e99/query/v2"

# query = {
#     "statement": "RETURN 1 AS x"
# }

# response = requests.post(
#     url,
#     auth=(
#         "e4bb0e99",
#         "1fGi9xPBo4NAW0a7BtV31rI_V1k_8JfiBAL_5cmh3kU"
#     ),
#     json=query
# )

# print(response.status_code)
# print(response.text)

import requests

url = "https://e4bb0e99.databases.neo4j.io/db/e4bb0e99/query/v2"

query = {
    "statement": """
    CREATE (n:TestNode {
        name:'vivek'
    })
    RETURN n
    """
}

r = requests.post(
    url,
    auth=(
        "e4bb0e99",
        "YOUR_PASSWORD"
    ),
    json=query
)

print(r.status_code)
print(r.text)