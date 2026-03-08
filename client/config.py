from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ================= API =================
    API_TITLE: str = "Stark Recruitment AI API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # ================= URLs =================
    API_BASE_URL: str = "http://localhost:8000"
    WEBSOCKET_URL: str = "ws://localhost:8000"   

    # ================= Database =================
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "stark_recruitment"

    # ================= Security =================
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ================= ASR (Speech-to-Text) =================
    ASR_ENGINE: str = "faster-whisper"           # faster-whisper | vosk
    VOSK_MODEL_PATH: Path = BASE_DIR / "models" / "vosk-model-ar"
    WHISPER_MODEL_SIZE: str = "medium"
    WHISPER_LANGUAGE: str = "ar"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_DEVICE: str = "cpu"

    # ================= TTS (Text-to-Speech) =================
    TTS_ENGINE: str = "edge-tts"
    TTS_LANGUAGE: str = "ar"
    TTS_CACHE_DIR: Path = BASE_DIR / "uploads" / "tts_cache"
    COQUI_OPTIMIZED_ARABIC: bool = True
    COQUI_MODEL: str = "tts_models/multilingual/multi-dataset/xtts_v2"

    # ================= LLM / Ollama =================
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: float = 60.0

    # ================= Avatar =================
    AVATAR_PROVIDER: str = "simple"

    # ================= File Upload =================
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    ALLOWED_AUDIO_FORMATS: list[str] = [".wav", ".mp3", ".ogg", ".flac"]

    # ================= Audio Processing =================
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1
    CHUNK_SIZE: int = 1024

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()