# src/etl/downloader.py
import os
import requests
from pathlib import Path
from urllib.parse import urlparse
from src.config import settings
from src.utils.logging import logger
from tqdm import tqdm

class PDFDownloader:
    def __init__(self, raw_dir: str = None):
        self.raw_dir = Path(raw_dir or settings.raw_data_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
    
    def download_from_url(self, url: str, filename: str = None) -> str:
        """Download a PDF and return the local path."""
        if not filename:
            filename = os.path.basename(urlparse(url).path)
            if not filename.endswith(".pdf"):
                filename = f"{hash(url)}.pdf"
        local_path = self.raw_dir / filename
        if local_path.exists():
            logger.info(f"File {local_path} already exists, skipping download")
            return str(local_path)
        
        logger.info(f"Downloading {url} -> {local_path}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(local_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        return str(local_path)
    
    def scan_local_folder(self) -> list:
        """Return list of all PDF paths in raw_dir."""
        return [str(p) for p in self.raw_dir.glob("*.pdf")]