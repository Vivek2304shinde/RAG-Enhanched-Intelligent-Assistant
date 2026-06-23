# src/graph/entity_extractor.py
import json
import re
import spacy
from typing import List, Dict
from groq import Groq

from src.utils.logging import logger
from src.config import settings


class EntityExtractor:
    def __init__(self, patterns_path: str = None):
        self.nlp = spacy.load("en_core_web_lg")

        if patterns_path:
            self._add_custom_patterns(patterns_path)

        self.use_llm = bool(settings.groq_api_key)

        if self.use_llm:
            self.client = Groq(api_key=settings.groq_api_key)

    def _add_custom_patterns(self, patterns_path: str):
        with open(patterns_path, "r", encoding="utf-8") as f:
            patterns = json.load(f)

        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        ruler.add_patterns(patterns)

        logger.info(f"Loaded {len(patterns)} custom entity patterns")

    def _clean_name(self, name: str) -> str:
        """
        Clean entity name:
        - Replace newlines, multiple spaces with a single space.
        - Trim leading/trailing whitespace.
        """
        cleaned = re.sub(r'\s+', ' ', name).strip()
        return cleaned

    def extract_entities_spacy(self, text: str) -> List[Dict]:
        doc = self.nlp(text)

        entities = []

        label_map = {
            "ORG": "MINISTRY",
            "GPE": "STATE",
            "PERSON": "BENEFICIARY",
            "PRODUCT": "SCHEME",
        }

        for ent in doc.ents:
            our_label = label_map.get(ent.label_)
            if our_label:
                entities.append(
                    {
                        "entity_type": our_label,
                        "name": self._clean_name(ent.text),
                        "attributes": {},
                    }
                )

        return entities

    def extract_entities_llm(self, text: str) -> List[Dict]:
        if not self.use_llm:
            return []

        prompt = f"""
You are an expert in Indian finance.

Extract entities from the text.

Allowed entity types:

SCHEME
MINISTRY
BANK
STATE
BENEFICIARY
SECTOR
REGULATION
TENDER

Return ONLY valid JSON.

Format:

[
  {{
    "entity_type": "BANK",
    "name": "State Bank of India",
    "attributes": {{}}
  }}
]

Text:

{text[:3000]}
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            content = response.choices[0].message.content.strip()

            # Attempt to parse JSON; if it fails, try to extract JSON from code block
            try:
                entities = json.loads(content)
            except json.JSONDecodeError:
                # Look for a JSON array in the response (markdown code block or plain)
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
                if json_match:
                    content = json_match.group(1).strip()
                else:
                    # Try to find a list pattern
                    list_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                    if list_match:
                        content = list_match.group(0)
                    else:
                        logger.error(f"Could not extract JSON from LLM response: {content[:200]}")
                        return []
                entities = json.loads(content)

            if not isinstance(entities, list):
                return []

            # Clean names and ensure required keys
            cleaned = []
            for e in entities:
                if "entity_type" in e and "name" in e:
                    cleaned.append({
                        "entity_type": e["entity_type"].upper(),
                        "name": self._clean_name(e["name"]),
                        "attributes": e.get("attributes", {})
                    })
            return cleaned

        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")
            return []

    def extract(self, text: str) -> List[Dict]:
        entities = self.extract_entities_spacy(text)

        if self.use_llm:
            entities.extend(self.extract_entities_llm(text))

        # Deduplicate by (entity_type, name)
        seen = set()
        unique = []

        for e in entities:
            key = (
                e["entity_type"],
                e["name"].lower().strip()
            )

            if key not in seen:
                seen.add(key)
                unique.append(e)

        return unique


entity_extractor = EntityExtractor(
    patterns_path="data/knowledge/entity_patterns.json"
)