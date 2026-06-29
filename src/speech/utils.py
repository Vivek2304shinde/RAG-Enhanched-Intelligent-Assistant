# src/speech/utils.py
import librosa
import soundfile as sf
import io

def load_audio(audio_bytes):
    audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
    return audio, sr

def save_audio(audio, sr, path):
    sf.write(path, audio, sr)

def resample_audio(audio, orig_sr, target_sr=16000):
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)