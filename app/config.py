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
    DATABASE_URL: str = "postgresql+asyncpg://estimator:estimator@localhost:5432/estimator"

    # Session 10 — hybrid retrieval + cross-encoder reranking
    RERANKING_ENABLED: bool = False
    RERANKER_MODEL_NAME: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    RETRIEVAL_CANDIDATE_POOL_SIZE: int = 50
    RETRIEVAL_TOP_K: int = 5
    RRF_SMOOTHING_K: int = 60

    class Config:
        env_file = ".env"

@lru_cache   # la configuracion se carga 1 sola vez
def get_settings() -> Settings:
    """Return a singleton settings object for the process."""
    return Settings()

settings = get_settings()
