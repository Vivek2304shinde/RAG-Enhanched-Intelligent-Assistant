# test_redis.py

import redis

r = redis.from_url(
    "redis://default:wgHRKp8ChCMwSraXosdP1MiWP8vt6emb@education-expressive-wideband-98201.db.redis.io:14759",
    decode_responses=True
)

print(r.ping())

r.set("test", "hello")

print(r.get("test"))