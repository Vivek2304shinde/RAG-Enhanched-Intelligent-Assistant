# src/etl/chunker.py
from src.config import settings
from src.utils.logging import logger
import re

def recursive_character_splitter(text: str, chunk_size: int, overlap: int):
    """Simple token-based splitting (approx by characters)."""
    # Use a simple recursive split on sentences.
    # We'll use a character-based split with overlap.
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        # try to cut at sentence boundary
        if end < text_len:
            # find last period or newline within the overlap region
            search_end = min(end + overlap, text_len)
            cut_pos = text.rfind('. ', end, search_end)
            if cut_pos == -1:
                cut_pos = text.rfind('\n', end, search_end)
            if cut_pos != -1:
                end = cut_pos + 1
        chunks.append(text[start:end].strip())
        start = end - overlap
    return chunks

def chunk_elements(elements: list) -> list:
    """
    Takes a list of dicts with 'text' and 'metadata' and applies
    additional chunking if text is too long.
    Returns list of chunk dicts with 'text' and 'metadata'.
    """
    final_chunks = []
    for elem in elements:
        text = elem["text"].strip()
        if not text:
            continue
        # If text is short enough, keep as is
        if len(text) < settings.chunk_size * 4:
            final_chunks.append(elem)
        else:
            # Split into smaller chunks
            sub_chunks = recursive_character_splitter(text, settings.chunk_size * 4, settings.chunk_overlap * 2)
            for i, sub in enumerate(sub_chunks):
                meta = elem["metadata"].copy()
                meta["sub_chunk_index"] = i
                final_chunks.append({"text": sub, "metadata": meta})
    return final_chunks