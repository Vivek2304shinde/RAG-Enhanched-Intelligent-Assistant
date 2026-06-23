# src/retrieval/query_understanding.py
import json
import re
from typing import Dict, List, Optional
from groq import Groq
from src.config import settings
from src.utils.logging import logger

class QueryUnderstanding:
    def __init__(self):
        self.use_llm = bool(settings.groq_api_key)
        if self.use_llm:
            self.client = Groq(api_key=settings.groq_api_key)

    def _clean_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def classify_query(self, query: str) -> Dict:
        """
        Returns a dict with:
        - query_type: factual | comparative | trend | scheme_eligibility | regulation | timeline
        - entities: list of entity names
        - time_range: {start: int, end: int} or None
        - agencies: list of agencies (RBI, SEBI, etc.)
        - filters: dict of other metadata (sector, state, etc.)
        """
        if not self.use_llm:
            # Fallback: basic heuristics
            return self._rule_based_classify(query)

        function_schema = {
            "name": "classify_query",
            "description": "Classify a financial/economic query about Indian government documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["factual", "comparative", "trend", "scheme_eligibility", "regulation", "timeline"]
                    },
                    "entities": {"type": "array", "items": {"type": "string"}},
                    "time_range": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "integer"},
                            "end": {"type": "integer"}
                        },
                        "required": ["start", "end"]
                    },
                    "agencies": {"type": "array", "items": {"type": "string"}},
                    "filters": {"type": "object"}
                },
                "required": ["query_type"]
            }
        }

        prompt = f"""
You are an expert in Indian government finance and schemes.
Analyze the user query and extract structured information.

User query: {query}

Return the classification in JSON format using the provided function.
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
                tools=[{"type": "function", "function": function_schema}],
                tool_choice={"type": "function", "function": {"name": "classify_query"}}
            )
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            return args
        except Exception as e:
            logger.error(f"Query classification LLM failed: {e}")
            return self._rule_based_classify(query)

    def _rule_based_classify(self, query: str) -> Dict:
        q = query.lower()
        if "scheme" in q and ("eligible" in q or "apply" in q):
            qtype = "scheme_eligibility"
        elif "compare" in q or "vs" in q or "difference" in q:
            qtype = "comparative"
        elif "trend" in q or "change" in q or "over time" in q:
            qtype = "trend"
        elif "regulation" in q or "rule" in q or "compliance" in q:
            qtype = "regulation"
        elif "budget" in q or "year" in q or "timeline" in q:
            qtype = "timeline"
        else:
            qtype = "factual"

        # Extract year if present
        import re
        years = re.findall(r'\b(20\d{2})\b', q)
        time_range = None
        if years:
            years = sorted(set(int(y) for y in years))
            if len(years) == 1:
                time_range = {"start": years[0], "end": years[0]}
            elif len(years) >= 2:
                time_range = {"start": min(years), "end": max(years)}

        # Simple agency detection
        agencies = []
        for agency in ["rbi", "sebi", "gst", "mca", "nabard", "sidbi", "ministry of finance"]:
            if agency in q:
                agencies.append(agency.upper())

        return {
            "query_type": qtype,
            "entities": [],
            "time_range": time_range,
            "agencies": agencies,
            "filters": {}
        }

query_understanding = QueryUnderstanding()