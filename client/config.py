from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Backend
    BACKEND_URL: str = "http://localhost:8000"
    WEBSOCKET_URL: str = "ws://localhost:8000"  
    
    # Audio
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1
    CHUNK_SIZE: int = 1024
    
    # UI
    WINDOW_WIDTH: int = 1200
    WINDOW_HEIGHT: int = 800
    LANGUAGE: str = "ar"  # ar ou en
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()