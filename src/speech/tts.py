# src/speech/tts.py
import os
import tempfile
from gtts import gTTS
# Optional: from TTS.api import TTS  (if you want Coqui)
from src.utils.logging import logger

class TextToSpeech:
    def __init__(self, use_coqui: bool = False):
        self.use_coqui = use_coqui
        if use_coqui:
            # Load a lightweight model (you can change to better ones)
            # self.tts = TTS("tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
            logger.info("Coqui TTS loaded (not used in this demo)")
        else:
            self.tts = None
            logger.info("Using gTTS (online, needs internet)")

    def synthesize(self, text: str, lang: str = "en") -> bytes:
        """Convert text to speech and return MP3 bytes."""
        if self.use_coqui:
            # Coqui logic (optional) - for now we fallback to gTTS
            pass
        # Use gTTS (simpler, no GPU needed)
        tts = gTTS(text=text, lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_file:
            tts.save(mp3_file.name)
            mp3_path = mp3_file.name
        with open(mp3_path, "rb") as f:
            audio_bytes = f.read()
        os.unlink(mp3_path)
        return audio_bytes

tts = TextToSpeech(use_coqui=False)