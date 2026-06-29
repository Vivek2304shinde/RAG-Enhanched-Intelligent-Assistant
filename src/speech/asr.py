# src/speech/asr.py
import whisper
import tempfile
import os
from src.utils.logging import logger

class SpeechRecognizer:
    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)
        logger.info(f"Whisper {model_size} loaded")

    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes (any format) to text."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            audio_path = f.name
        try:
            result = self.model.transcribe(audio_path)
            return result["text"].strip()
        finally:
            os.unlink(audio_path)

asr = SpeechRecognizer(model_size="base")