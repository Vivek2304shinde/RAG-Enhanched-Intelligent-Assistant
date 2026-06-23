# test_phase3.py
from src.retrieval.retrieval_pipeline import retrieval_pipeline

query = "What are the RBI guidelines for MSME lending?"
results = retrieval_pipeline.retrieve(query)
print(f"Retrieved {len(results)} chunks")
for i, r in enumerate(results[:3]):
    print(f"\n--- Result {i+1} ---")
    print(f"Text: {r['text'][:200]}...")
    print(f"Metadata: {r['metadata']}")