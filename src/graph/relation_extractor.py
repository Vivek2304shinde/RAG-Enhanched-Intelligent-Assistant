# src/graph/relation_extractor.py
import json
import re
from typing import List, Dict, Optional
from groq import Groq
from src.utils.logging import logger
from src.config import settings

class RelationExtractor:
    def __init__(self):
        self.use_llm = bool(settings.groq_api_key)
        if self.use_llm:
            self.client = Groq(api_key=settings.groq_api_key)

    def _clean_name(self, name: str) -> str:
        return re.sub(r'\s+', ' ', name).strip()

    def extract_relations(self, text: str, entities: List[Dict]) -> List[Dict]:
        if not entities:
            return []

        if self.use_llm:
            llm_relations = self._extract_relations_llm_function_call(text, entities)
            if llm_relations is not None:
                return llm_relations

        logger.info("Using fallback rule‑based relation extraction")
        return self._extract_relations_rule_based(entities)

    def _extract_relations_llm_function_call(self, text: str, entities: List[Dict]) -> Optional[List[Dict]]:
        """
        Use Groq's function calling to get structured relations.
        """
        # Build list of entity names for context
        entity_names = [e["name"].strip() for e in entities]
        
        # Define the function schema
        functions = [
            {
                "name": "extract_relations",
                "description": "Extract relationships between entities.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "subject": {"type": "string"},
                                    "relation": {
                                        "type": "string",
                                        "enum": ["IMPLEMENTS", "FUNDS", "AFFECTS", "RELATED_TO", "ELIGIBLE_FOR", "ISSUED_BY", "SUPERSEDES", "ALLOCATED_TO", "LOCATED_IN"]
                                    },
                                    "object": {"type": "string"}
                                },
                                "required": ["subject", "relation", "object"]
                            }
                        }
                    },
                    "required": ["relations"]
                }
            }
        ]

        prompt = f"""
You are an expert in Indian government finance and schemes.
Given the following text and a list of entities, extract relationships between these entities.
Use only the allowed relation types.

Entities: {entity_names}
Text: {text[:3000]}
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
                functions=functions,
                function_call="auto"  # ask the model to call the function
            )
            message = response.choices[0].message
            if message.function_call:
                # Parse the function arguments
                args = json.loads(message.function_call.arguments)
                relations = args.get("relations", [])
                # Clean and validate
                valid = []
                for r in relations:
                    if all(k in r for k in ("subject", "relation", "object")):
                        r["subject"] = self._clean_name(r["subject"])
                        r["object"] = self._clean_name(r["object"])
                        if r["subject"] and r["object"] and r["relation"]:
                            valid.append(r)
                return valid
            else:
                logger.warning("Model did not call function, falling back")
                return None
        except Exception as e:
            logger.error(f"LLM function calling failed: {e}")
            return None

    def _extract_relations_rule_based(self, entities: List[Dict]) -> List[Dict]:
        type_to_names = {}
        for e in entities:
            etype = e["entity_type"]
            name = self._clean_name(e["name"])
            type_to_names.setdefault(etype, []).append(name)

        relations = []
        if "SCHEME" in type_to_names and "MINISTRY" in type_to_names:
            for scheme in type_to_names["SCHEME"]:
                for ministry in type_to_names["MINISTRY"]:
                    relations.append({"subject": scheme, "relation": "IMPLEMENTS", "object": ministry})
        if "SCHEME" in type_to_names and "BENEFICIARY" in type_to_names:
            for scheme in type_to_names["SCHEME"]:
                for beneficiary in type_to_names["BENEFICIARY"]:
                    relations.append({"subject": beneficiary, "relation": "ELIGIBLE_FOR", "object": scheme})
        if "SCHEME" in type_to_names and "BANK" in type_to_names:
            for scheme in type_to_names["SCHEME"]:
                for bank in type_to_names["BANK"]:
                    relations.append({"subject": scheme, "relation": "FUNDS", "object": bank})
        if "REGULATION" in type_to_names and "MINISTRY" in type_to_names:
            for reg in type_to_names["REGULATION"]:
                for ministry in type_to_names["MINISTRY"]:
                    relations.append({"subject": reg, "relation": "ISSUED_BY", "object": ministry})
        return relations

relation_extractor = RelationExtractor()