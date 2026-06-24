# test_redis.py

# import redis

# r = redis.from_url(
#     "",
#     decode_responses=True
# )

# print(r.ping())

# r.set("test", "hello")

# print(r.get("test"))

# from src.storage.qdrant_client import qdrant_client

# print(dir(qdrant_client.client))

# from src.storage.qdrant_client import qdrant_client

# print(qdrant_client.client.query_points)

# # test_qdrant.py

# from src.storage.qdrant_client import qdrant_client

# info = qdrant_client.client.get_collection(
#     qdrant_client.collection_name
# )

# print(info)

# from src.storage.qdrant_client import qdrant_client

# print(
#     qdrant_client.client.count(
#         collection_name=qdrant_client.collection_name,
#         exact=True
#     )
# )

# # inspect_qdrant.py

# from src.storage.qdrant_client import qdrant_client

# points, _ = qdrant_client.client.scroll(
#     collection_name=qdrant_client.collection_name,
#     limit=5,
#     with_payload=True,
#     with_vectors=False
# )

# for p in points:
#     print("=" * 80)
#     print("ID:", p.id)
#     print("PAYLOAD:")
#     print(p.payload)


# from src.storage.qdrant_client import qdrant_client
# import inspect

# print(inspect.signature(
#     qdrant_client.client.query_points
# ))

# test_qdrant_query.py

# from src.storage.qdrant_client import qdrant_client
# from src.etl.embedder import embedder

# dense, sparse = embedder.embed_batch(
#     ["Who are the RBI board members?"]
# )

# dense = dense[0].tolist()

# result = qdrant_client.client.query_points(
#     collection_name=qdrant_client.collection_name,
#     query=dense,
#     using="dense",
#     limit=5,
#     with_payload=True
# )

# print(result)

# test_vectors.py

# from src.storage.qdrant_client import qdrant_client

# point = qdrant_client.client.retrieve(
#     collection_name=qdrant_client.collection_name,
#     ids=["7e15139f-6234-4ee7-9038-e255c87f7dc4"],
#     with_vectors=True
# )

# print(point)

# test_qdrant_query.py

# from src.storage.qdrant_client import qdrant_client

# print(qdrant_client.client.query_points)

# import inspect
# from src.storage.qdrant_client import qdrant_client

# print(
#     inspect.signature(
#         qdrant_client.client.query_points
#     )
# )

# test_hybrid.py

# from src.storage.qdrant_client import qdrant_client
# from src.etl.embedder import embedder

# dense, sparse = embedder.embed_batch(
#     ["Who are RBI board members?"]
# )

# dense = dense[0].tolist()

# response = qdrant_client.client.query_points(
#     collection_name=qdrant_client.collection_name,
#     query=dense,
#     using="dense",
#     limit=5,
#     with_payload=True
# )

# print(response)

# test_sparse.py

# from src.storage.qdrant_client import qdrant_client
# from src.etl.embedder import embedder
# from qdrant_client.http import models

# dense, sparse = embedder.embed_batch(
#     ["Who are RBI board members?"]
# )

# s = sparse[0]

# response = qdrant_client.client.query_points(
#     collection_name=qdrant_client.collection_name,
#     query=models.SparseVector(
#         indices=s["indices"],
#         values=s["values"]
#     ),
#     using="sparse",
#     limit=5,
#     with_payload=True
# )

# print(response)

from src.config import settings

print(settings.qdrant_url)
print(settings.qdrant_api_key)

# test_qdrant_config.py

from src.config import settings

print(settings.qdrant_url)
print(settings.qdrant_api_key[:20])

from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://3821ed04-21a5-49a5-9a55-fde8fc23208a.eu-central-1-0.aws.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZjJhMDY0NGQtZjdmYy00MTY0LThjMDYtN2NmYmU3ZGVlMjNmIn0.L6-c-iDdBSMSpRyk-tMjAPrTQgDsOIewPnfKXFZnPbM"
)

print(client.get_collections())