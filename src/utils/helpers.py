# src/utils/helpers.py
import re

def extract_agency_from_text(text: str) -> str:
    """Basic regex to find RBI, SEBI, etc."""
    patterns = {
        "RBI": r"RBI|Reserve Bank of India",
        "SEBI": r"SEBI|Securities and Exchange Board of India",
        "GST": r"GST|Goods and Services Tax",
        "MCA": r"MCA|Ministry of Corporate Affairs",
    }
    for agency, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            return agency
    return "Unknown"