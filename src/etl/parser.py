# src/etl/parser.py
import io
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image
from pypdf import PdfReader
import camelot
import pytesseract
from paddleocr import PaddleOCR
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from src.utils.logging import logger
from src.config import settings

# Initialize PaddleOCR (lazy loading)
_ocr = None

def get_ocr():
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    return _ocr

class PDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.reader = PdfReader(self.pdf_path)
        self.total_pages = len(self.reader.pages)
        self.metadata = self._extract_basic_metadata()
    
    def _extract_basic_metadata(self):
        """Extract from filename or PDF metadata."""
        # For now, derive from filename: e.g., RBI_MP_2024.pdf
        name = self.pdf_path.stem
        parts = name.split('_')
        agency = parts[0] if len(parts) > 0 else "Unknown"
        year = None
        for p in parts:
            if p.isdigit() and len(p) == 4:
                year = int(p)
                break
        return {
            "title": name,
            "agency": agency,
            "year": year,
            "doc_type": "unknown",  # can be improved with regex
            "total_pages": self.total_pages,
            "pdf_path": str(self.pdf_path)
        }
    
    def parse(self):
        """Main entry: return list of chunks and list of tables."""
        # Use unstructured to get elements
        elements = partition_pdf(
            filename=str(self.pdf_path),
            strategy="hi_res",
            extract_images_in_pdf=True,
            infer_table_structure=True,
            chunking_strategy="by_title",
            max_characters=settings.chunk_size * 4,  # approx chars
            new_after_n_chars=settings.chunk_size * 4,
            combine_text_under_n_chars=settings.chunk_size * 2,
        )
        
        chunks = []
        tables = []
        for el in elements:
            if el.category == "Table":
                # Extract structured table using camelot or tabula
                table_data = self._extract_table(el.metadata.page_number)
                tables.append({
                    "page": el.metadata.page_number,
                    "data": table_data,
                    "text": el.text  # fallback
                })
                # Also store table as a text chunk (markdown format)
                chunks.append({
                    "text": self._table_to_markdown(table_data),
                    "metadata": {
                        "page": el.metadata.page_number,
                        "category": "table",
                        "section": getattr(el.metadata, "section", None)
                    }
                })
            elif el.category in ["Image", "Picture"]:
                # OCR the image if possible (unstructured may have extracted image)
                # We'll do separate OCR for scanned pages later
                pass
            else:
                # Text element
                chunks.append({
                    "text": el.text,
                    "metadata": {
                        "page": el.metadata.page_number,
                        "category": el.category,
                        "section": getattr(el.metadata, "section", None),
                        "heading": getattr(el.metadata, "heading", None)
                    }
                })
        
        # If no text chunks were found, this is likely a scanned PDF -> use OCR
        # if not chunks or all(len(c["text"].strip()) < 50 for c in chunks):
        #     logger.info(f"PDF {self.pdf_path} appears scanned, using PaddleOCR")
        #     chunks = self._ocr_full_pdf()
        if not chunks:
            logger.warning("No text extracted.")
        
        return chunks, tables
    
    def _extract_table(self, page_num):
        """Extract table from a specific page using camelot."""
        try:
            # try lattice first, then stream
            tables = camelot.read_pdf(str(self.pdf_path), pages=str(page_num), flavor='lattice')
            if len(tables) == 0:
                tables = camelot.read_pdf(str(self.pdf_path), pages=str(page_num), flavor='stream')
            if len(tables) > 0:
                df = tables[0].df
                # Convert to list of dicts
                return df.to_dict(orient='records')
            else:
                return []
        except Exception as e:
            logger.warning(f"Table extraction failed on page {page_num}: {e}")
            return []
    
    def _table_to_markdown(self, table_data):
        if not table_data:
            return ""
        df = pd.DataFrame(table_data)
        return df.to_markdown(index=False)
    
    def _ocr_full_pdf(self):
        """Full PDF OCR using PaddleOCR."""
        ocr = get_ocr()
        chunks = []
        for page_num, page in enumerate(self.reader.pages, start=1):
            from pdf2image import convert_from_path
            images = convert_from_path(str(self.pdf_path), first_page=page_num, last_page=page_num)
            if not images:
                continue
            img = np.array(images[0])
            result = ocr.ocr(img, cls=True)
            if result:
                text = "\n".join([line[1][0] for line in result[0]])
            else:
                text = ""
            chunks.append({
                "text": text,
                "metadata": {"page": page_num, "category": "ocr"}
            })
        return chunks