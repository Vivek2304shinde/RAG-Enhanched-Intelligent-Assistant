# src/agents/nodes.py
import json
import re
from typing import Dict, Any
from groq import Groq
from src.config import settings
from src.utils.logging import logger
from src.retrieval.retrieval_pipeline import retrieval_pipeline
from src.graph.cypher_tool import CypherTool
from src.agents.state import AgentState

# Initialize LLM client
llm_client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

# ---------- Node 1: Query Planner ----------
def query_planner_node(state: AgentState) -> Dict[str, Any]:
    logger.info("AGENT: Query Planner")
    query = state["query"]
    # Use the existing query_understanding module
    from src.retrieval.query_understanding import query_understanding
    plan = query_understanding.classify_query(query)
    return {
        "query_plan": plan,
        "rewritten_queries": [query],  # will be expanded later
        "iteration": 1,
        "max_iterations": 3,
    }

# ---------- Node 2: Retrieval ----------
def retrieval_node(state: AgentState) -> Dict[str, Any]:
    logger.info("AGENT: Retrieval")
    query = state["query"]
    filters = state["query_plan"].get("filters", {})
    # Use the retrieval pipeline
    chunks = retrieval_pipeline.retrieve(query, filters=filters)
    return {"retrieved_chunks": chunks}

# ---------- Node 3: Graph Query ----------
def graph_query_node(state: AgentState) -> Dict[str, Any]:
    logger.info("AGENT: Graph Query")
    query = state["query"]
    plan = state["query_plan"]
    # Determine if graph query is needed: if plan contains entities or relationships
    entities = plan.get("entities", [])
    if not entities:
        return {"graph_data": []}
    # Use a LLM to generate Cypher from the query + entities
    cypher_prompt = f"""
You are a Neo4j expert. Given a user query and a list of entities, generate a Cypher query to find relevant nodes and relationships.
Use the following node labels: Ministry, Scheme, Bank, State, Beneficiary, Sector, Regulation, Tender, BudgetAllocation, Document.
Relationships: IMPLEMENTS, FUNDS, AFFECTS, RELATED_TO, ELIGIBLE_FOR, ISSUED_BY, SUPERSEDES, ALLOCATED_TO, LOCATED_IN.

User query: {query}
Entities: {entities}

Return only the Cypher query, no other text.
"""
    try:
        response = llm_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            messages=[{"role": "user", "content": cypher_prompt}]
        )
        cypher = response.choices[0].message.content.strip()
        # Execute the query safely (read-only)
        results = CypherTool.run_read_query(cypher)
        return {"graph_data": results}
    except Exception as e:
        logger.error(f"Graph query failed: {e}")
        return {"graph_data": []}

# ---------- Node 4: Reranking (optional, but we already have reranking in pipeline) ----------
# We skip separate rerank node because retrieval_pipeline already does reranking.
# Instead, we just use the reranked chunks from retrieval_node.

# ---------- Node 5: Reflection ----------
def reflection_node(state: AgentState) -> Dict[str, Any]:
    logger.info("AGENT: Reflection")
    chunks = state.get("reranked_chunks") or state.get("retrieved_chunks")
    if not chunks:
        return {"reflection_feedback": "No documents retrieved. Need broader search.", "needs_re_retrieval": True}
    # Use LLM to assess if the retrieved chunks are sufficient.
    # Prepare a prompt with the query and the top 3 chunk texts.
    top_texts = [c["text"][:500] for c in chunks[:3]]
    context = "\n\n---\n\n".join(top_texts)
    prompt = f"""
You are a quality assessor. Given a user query and a set of retrieved document excerpts, decide if the excerpts contain enough information to answer the query fully.
If not, specify what is missing (e.g., specific dates, numbers, agency names, contradictions).
Respond in JSON format: {{"sufficient": boolean, "missing": "description of missing info", "needs_re_retrieval": boolean}}.

Query: {state["query"]}
Excerpts:
{context}
"""
    try:
        response = llm_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        # Parse JSON
        result = json.loads(content)
        needs_re = result.get("needs_re_retrieval", False)
        feedback = result.get("missing", "")
        return {"reflection_feedback": feedback, "needs_re_retrieval": needs_re}
    except Exception as e:
        logger.error(f"Reflection failed: {e}")
        return {"reflection_feedback": "Unable to assess; assume sufficient", "needs_re_retrieval": False}

# ---------- Node 6: Re‑retrieval (if reflection says so) ----------
def re_retrieval_node(state: AgentState) -> Dict[str, Any]:
    logger.info("AGENT: Re‑Retrieval")
    # Use the original query, but expand or modify based on feedback
    feedback = state.get("reflection_feedback", "")
    query = state["query"]
    # Rewrite query to include missing info
    new_query = f"{query} (need information about: {feedback})"
    filters = state["query_plan"].get("filters", {})
    chunks = retrieval_pipeline.retrieve(new_query, filters=filters)
    return {"retrieved_chunks": chunks, "needs_re_retrieval": False}

# ---------- Node 7: Cross‑document Synthesis ----------
def synthesizer_node(state: AgentState) -> Dict[str, Any]:
    logger.info("AGENT: Synthesizer")
    chunks = state.get("reranked_chunks") or state.get("retrieved_chunks")
    if not chunks:
        return {"draft_answer": "No information found."}
    # Prepare a synthesis prompt
    context = "\n\n---\n\n".join([c["text"][:1000] for c in chunks[:5]])
    prompt = f"""
You are a financial research assistant. Synthesize the following excerpts to answer the user query.
Provide a concise, well‑structured answer. If the excerpts mention contradictions, note them.
Cite the source by using [1], [2], etc. corresponding to the order of excerpts.

Query: {state["query"]}

Excerpts:
{context}
"""
    try:
        response = llm_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        draft = response.choices[0].message.content.strip()
        return {"draft_answer": draft}
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return {"draft_answer": "Error generating synthesis."}

# ---------- Node 8: Financial Reasoning ----------
def reasoner_node(state: AgentState) -> Dict[str, Any]:
    logger.info("AGENT: Reasoner")
    # Extract numbers from draft or chunks and perform calculations if needed.
    # For MVP, we'll use a simple tool: if the query asks for growth, sum, etc.
    # We'll use a Python sandbox (exec) with limited globals.
    # We'll also use LLM to generate a calculation script.
    draft = state.get("draft_answer", "")
    if not draft:
        return {"calculations": {}}
    # Detect if calculation is needed by keywords
    calc_keywords = ["CAGR", "growth", "sum", "total", "average", "difference"]
    if not any(k in draft.lower() for k in calc_keywords):
        return {"calculations": {}}
    # Prompt LLM to generate Python code to compute the numbers.
    prompt = f"""
You are a financial analyst. Based on the following answer draft, generate Python code to compute any required financial metrics.
Return only the Python code, no other text.

Draft:
{draft}
"""
    try:
        response = llm_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        code = response.choices[0].message.content.strip()
        # Execute safely
        local_vars = {}
        exec(code, {"__builtins__": {}}, local_vars)
        # Assume the last variable holds result
        result = list(local_vars.values())[-1] if local_vars else None
        return {"calculations": {"result": result}}
    except Exception as e:
        logger.error(f"Reasoning failed: {e}")
        return {"calculations": {}}

# ---------- Node 9: Hallucination Judge ----------
def hallucination_check_node(state: AgentState) -> Dict[str, Any]:
    logger.info("AGENT: Hallucination Check")
    draft = state.get("draft_answer", "")
    chunks = state.get("reranked_chunks") or state.get("retrieved_chunks")
    if not draft or not chunks:
        return {"hallucination_checked": True, "is_hallucinated": True}
    context = "\n".join([c["text"] for c in chunks[:3]])
    prompt = f"""
You are a hallucination detector. Given a claim and the context, determine if the claim is supported by the context.
Return a JSON: {{"supported": boolean, "confidence": 0.0-1.0, "unsupported_parts": "..."}}.

Claim: {draft}
Context: {context}
"""
    try:
        response = llm_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        supported = result.get("supported", False)
        confidence = result.get("confidence", 0.5)
        hallucination_score = 1 - confidence if supported else confidence
        return {
            "hallucination_checked": True,
            "is_hallucinated": not supported,
            "hallucination_score": hallucination_score
        }
    except Exception as e:
        logger.error(f"Hallucination check failed: {e}")
        return {"hallucination_checked": True, "is_hallucinated": False, "hallucination_score": 0.0}

# ---------- Node 10: Answer Generator ----------
def answer_generator_node(state: AgentState) -> Dict[str, Any]:
    logger.info("AGENT: Answer Generator")
    draft = state.get("draft_answer", "No answer generated.")
    # If hallucinated, we could add a disclaimer.
    if state.get("is_hallucinated", False):
        draft += "\n\n⚠️ Warning: Some parts of this answer may not be directly supported by the retrieved documents."
    # Add citations from chunks
    chunks = state.get("reranked_chunks") or state.get("retrieved_chunks")
    citations = []
    if chunks:
        for i, c in enumerate(chunks[:5]):
            citations.append({
                "id": c.get("doc_id"),
                "title": c.get("metadata", {}).get("title", "Unknown"),
                "page": c.get("metadata", {}).get("page", ""),
                "snippet": c["text"][:200]
            })
    return {"final_answer": draft, "citations": citations}