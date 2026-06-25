# src/agents/runner.py
from src.agents.graph import agent_graph
from src.agents.state import AgentState
from src.utils.logging import logger

def run_agent(query: str) -> dict:
    logger.info(f"Starting agent for query: {query}")
    initial_state: AgentState = {
        "query": query,
        "query_plan": None,
        "rewritten_queries": None,
        "retrieved_chunks": None,
        "graph_data": None,
        "reranked_chunks": None,
        "reflection_feedback": None,
        "needs_re_retrieval": False,
        "calculations": None,
        "draft_answer": None,
        "final_answer": None,
        "citations": None,
        "hallucination_score": None,
        "hallucination_checked": False,
        "is_hallucinated": False,
        "iteration": 1,
        "max_iterations": 3,
        "error": None,
    }
    final_state = agent_graph.invoke(initial_state)
    return {
        "answer": final_state["final_answer"],
        "citations": final_state["citations"],
        "hallucination_score": final_state.get("hallucination_score"),
        "calculations": final_state.get("calculations"),
    }