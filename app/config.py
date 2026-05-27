from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 86400
    SESSION_MAX_TURNS: int = 6
    MAX_CONVERSATION_TURNS: int = 6
    ENABLE_ACB: bool = True
    ACB_MAX_ITERATIONS: int = 2
    METADATA_EXTRACTOR_MODEL: str = "gpt-4o-mini"
    MAX_SUMMARY_CHARS: int = 4000
    MAX_ANCHORS: int = 20
    MAX_ATTACHMENT_CHARS: int = 60000
    MAX_ATTACHMENT_BYTES: int = 5_000_000
    MAX_ATTACHMENTS_PER_REQUEST: int = 5
    APP_ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"

    class Config:
        env_file = ".env"

@lru_cache   # la configuracion se carga 1 sola vez
def get_settings() -> Settings:
    """Return a singleton settings object for the process."""
    return Settings()

settings = get_settings()
