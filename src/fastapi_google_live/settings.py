from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, Any


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash-live-001"
    GEMINI_CONFIG: Dict[str, Any] = Field(
        default_factory=lambda: {"response_modalities": ["TEXT"]}
    )
    SUPPORTED_AUDIO_FORMATS: list[str] = [
        "mp3",
        "wav",
        "m4a",
        "ogg",
    ]
    PCM_SAMPLE_RATE: int = 16000

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    return Settings()
