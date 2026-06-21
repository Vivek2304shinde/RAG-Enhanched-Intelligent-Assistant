# src/run_etl.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.etl.pipeline import ETLPipeline
from src.utils.logging import logger

def main():
    pipeline = ETLPipeline()
    
    # Example 1: Process a single URL
    # pipeline.process_pdf("https://rbidocs.rbi.org.in/rdocs/.../PDFs/...pdf", is_url=True)
    
    # Example 2: Process all PDFs in data/raw
    pipeline.process_folder()
    
    logger.info("ETL pipeline completed.")

if __name__ == "__main__":
    main()