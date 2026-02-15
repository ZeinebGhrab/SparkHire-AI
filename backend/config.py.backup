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

    # ================= Database =================
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "stark_recruitment"

    # ================= Security =================
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ================= ASR (Speech-to-Text) =================
    ASR_ENGINE: str = "vosk"  # vosk | faster-whisper
    VOSK_MODEL_PATH: Path = BASE_DIR / "models" / "vosk-model-ar"
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_LANGUAGE: str = "ar"

    # ================= TTS (Text-to-Speech) =================
    TTS_ENGINE: str = "pyttsx3"  # pyttsx3 | coqui
    TTS_LANGUAGE: str = "ar"
    TTS_CACHE_DIR: Path = BASE_DIR / "uploads" / "tts_cache"

    # ================= Avatar =================
    AVATAR_PROVIDER: str = "simple"  # simple | wav2lip | did

    # ================= File Upload =================
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
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
