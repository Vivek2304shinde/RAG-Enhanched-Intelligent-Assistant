# test_phase4.py
from src.agents.runner import run_agent

query = "What are the RBI guidelines for MSME lending?"
result = run_agent(query)
print("\n=== FINAL ANSWER ===")
print(result["answer"])
print("\n=== CITATIONS ===")
for c in result["citations"]:
    print(f"- {c['title']} (page {c['page']})")
print(f"\nHallucination Score: {result['hallucination_score']}")