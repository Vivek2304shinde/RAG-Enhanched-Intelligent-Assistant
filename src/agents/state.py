# src/agents/state.py
from typing import List, Dict, Optional, Any
from typing_extensions import TypedDict

class AgentState(TypedDict):
    # User input
    query: str

    # Query understanding
    query_plan: Optional[Dict]          # type, entities, filters, time range
    rewritten_queries: Optional[List[str]]

    # Retrieved data
    retrieved_chunks: Optional[List[Dict]]   # from Qdrant
    graph_data: Optional[List[Dict]]         # from Neo4j
    reranked_chunks: Optional[List[Dict]]    # after reranking

    # Reflection
    reflection_feedback: Optional[str]       # missing info or contradictions
    needs_re_retrieval: bool

    # Reasoning
    calculations: Optional[Dict]             # computed numbers

    # Draft and final answer
    draft_answer: Optional[str]
    final_answer: Optional[str]
    citations: Optional[List[Dict]]          # list of {doc_id, title, page, text snippet}

    # Quality check
    hallucination_score: Optional[float]     # 0–1, higher = worse
    hallucination_checked: bool
    is_hallucinated: bool

    # Control
    iteration: int
    max_iterations: int
    error: Optional[str]