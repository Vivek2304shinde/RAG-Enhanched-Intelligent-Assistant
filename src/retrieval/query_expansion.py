# src/retrieval/query_expansion.py
from typing import List, Dict
from groq import Groq
from src.config import settings
from src.utils.logging import logger

class QueryExpansion:
    def __init__(self):
        self.use_llm = bool(settings.groq_api_key)
        if self.use_llm:
            self.client = Groq(api_key=settings.groq_api_key)

    def generate_hyde_document(self, query: str) -> str:
        """
        Generate a hypothetical document that answers the query.
        This is used as a pseudo‑document for embedding.
        """
        if not self.use_llm:
            return query  # fallback: use original query

        prompt = f"""
You are an expert in Indian government finance and schemes.
Write a concise, factual paragraph (about 100‑150 words) that would answer the following query.
The paragraph should be written as if it were an excerpt from an official document.

Query: {query}

Return only the paragraph, no other text.
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"HyDE generation failed: {e}")
            return query

    def generate_multi_queries(self, query: str, n: int = 3) -> List[str]:
        """
        Generate multiple reformulations of the original query to increase recall.
        """
        if not self.use_llm:
            return [query]

        prompt = f"""
Given the original query, generate {n} alternative ways to ask the same question.
The reformulations should be diverse, using different synonyms and phrasing.
Return only a JSON list of strings.

Query: {query}
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content.strip()
            # Parse JSON list
            import json
            queries = json.loads(content)
            if isinstance(queries, list):
                return queries[:n]
            return [query]
        except Exception as e:
            logger.error(f"Multi‑query generation failed: {e}")
            return [query]

query_expansion = QueryExpansion()