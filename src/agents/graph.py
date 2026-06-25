# src/agents/graph.py
from langgraph.graph import StateGraph, END
from src.agents.state import AgentState
from src.agents.nodes import (
    query_planner_node,
    retrieval_node,
    graph_query_node,
    reflection_node,
    re_retrieval_node,
    synthesizer_node,
    reasoner_node,
    hallucination_check_node,
    answer_generator_node,
)

# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("query_planner", query_planner_node)
workflow.add_node("retriever", retrieval_node)
workflow.add_node("graph_query", graph_query_node)
workflow.add_node("reflector", reflection_node)
workflow.add_node("re_retriever", re_retrieval_node)
workflow.add_node("synthesizer", synthesizer_node)
workflow.add_node("reasoner", reasoner_node)
workflow.add_node("hallucination_check", hallucination_check_node)
workflow.add_node("answer_generator", answer_generator_node)

# Define edges
workflow.set_entry_point("query_planner")
workflow.add_edge("query_planner", "retriever")
# After retrieval, we run graph query in parallel (optional)
workflow.add_edge("retriever", "graph_query")
workflow.add_edge("graph_query", "reflector")

# Conditional edge from reflector
def should_re_retrieve(state: AgentState) -> str:
    if state.get("needs_re_retrieval", False) and state["iteration"] < state["max_iterations"]:
        return "re_retriever"
    else:
        return "synthesizer"

workflow.add_conditional_edges(
    "reflector",
    should_re_retrieve,
    {
        "re_retriever": "re_retriever",
        "synthesizer": "synthesizer"
    }
)
workflow.add_edge("re_retriever", "reflector")  # after re‑retrieval, reflect again

# After synthesis, run reasoner and hallucination check (parallel)
workflow.add_edge("synthesizer", "reasoner")
workflow.add_edge("synthesizer", "hallucination_check")
workflow.add_edge("reasoner", "answer_generator")
workflow.add_edge("hallucination_check", "answer_generator")
workflow.add_edge("answer_generator", END)

# Compile
agent_graph = workflow.compile()