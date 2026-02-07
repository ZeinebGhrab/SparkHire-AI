import wave
import numpy as np
from pathlib import Path

def save_audio_wav(audio_bytes: bytes, output_path: str, sample_rate: int = 16000):
    """Sauvegarder bytes audio en WAV"""
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)

def load_audio_wav(audio_path: str) -> tuple:
    """Charger fichier WAV"""
    with wave.open(audio_path, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        sample_rate = wf.getframerate()
        channels = wf.getnchannels()
        
        # Convertir en numpy
        audio_np = np.frombuffer(frames, dtype=np.int16)
        
        # Convertir en float32 normalisé
        audio_float = audio_np.astype(np.float32) / 32768.0
        
        return audio_float, sample_rate, channels

def bytes_to_numpy(audio_bytes: bytes) -> np.ndarray:
    """Convertir bytes en numpy array"""
    return np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

def numpy_to_bytes(audio_np: np.ndarray) -> bytes:
    """Convertir numpy array en bytes"""
    return (audio_np * 32768).astype(np.int16).tobytes()