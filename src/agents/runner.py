# src/agents/runner.py
from src.agents.memory import ConversationMemory
from src.agents.graph import agent_graph
from src.agents.state import AgentState
from src.utils.logging import logger

def run_agent(query: str, memory: ConversationMemory = None) -> dict:
    if memory is None:
        memory = ConversationMemory()
    memory.add_user_message(query)
    history = memory.get_history()
    initial_state: AgentState = {
        "query": query,
        "conversation_history": history,  # now used in synthesizer prompt
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
    memory.add_assistant_message(final_state["final_answer"])
    return {
        "answer": final_state["final_answer"],
        "citations": final_state["citations"],
        "hallucination_score": final_state.get("hallucination_score"),
        "calculations": final_state.get("calculations"),
        "conversation_id": id(memory)  # for tracking
    }