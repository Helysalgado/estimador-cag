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
    APP_ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"

    class Config:
        env_file = ".env"

@lru_cache   # la configuracion se carga 1 sola vez
def get_settings() -> Settings:
    """Return a singleton settings object for the process."""
    return Settings()

settings = get_settings()
