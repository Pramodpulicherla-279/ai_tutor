"""Application settings. Everything is optional so the service boots with no infra
(mock LLM, in-memory memory, no retrieval) and upgrades as env vars are provided.

Stack: Gemini 2.5 Flash for generation, MongoDB `ai_tutor` for persistence, and
MongoDB Atlas Vector Search for lesson-content retrieval (single database)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "devel-ai-tutor"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    # Auth -------------------------------------------------------------------
    AUTH_OPTIONAL: bool = True
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALG: str = "HS256"
    JWT_AUDIENCE: str = "devel"

    # MongoDB (tutor data + Atlas Vector Search) -----------------------------
    MONGODB_URI: str | None = None         # mongodb+srv://... (same cluster as devora)
    MONGO_DB: str = "ai_tutor"
    VECTOR_COLLECTION: str = "content_chunks"
    VECTOR_INDEX: str = "content_vindex"

    # Other optional services ------------------------------------------------
    REDIS_URL: str | None = None           # redis://localhost:6379/0
    PLATFORM_API_URL: str | None = None    # Node/Express backend base url

    # Generation (Google Gemini via AI Studio) -------------------------------
    # AI Studio / Developer API only. GEMINI_API_KEY comes from
    # https://aistudio.google.com/apikey and spends the AI Studio prepaid credits.
    # Vertex AI is deliberately unsupported so usage can never bill a GCP account.
    GEMINI_API_KEY: str | None = None
    MODEL_SMART: str = "gemini-3.6-flash"
    MODEL_FAST: str = "gemini-3.6-flash"   # use gemini-2.5-flash-lite to cut cost further
    MAX_OUTPUT_TOKENS: int = 1024
    TEMPERATURE: float = 0.6
    RETRIEVAL_K: int = 6

    # CORS -------------------------------------------------------------------
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
