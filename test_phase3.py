# test_phase3.py
from src.retrieval.retrieval_pipeline import retrieval_pipeline

query = "Who are the RBI board members"
results = retrieval_pipeline.retrieve(query)
print(f"Retrieved {len(results)} chunks")
for i, r in enumerate(results[:3]):
    print(f"\n--- Result {i+1} ---")
    print(f"Text: {r['text'][:200]}...")
    print(f"Metadata: {r['metadata']}")

print("START")

query = "Who are the RBI board members?"

results = retrieval_pipeline.retrieve(query)

print("RESULTS:", len(results))

for r in results:
    print(r["text"][:200])

print("END")