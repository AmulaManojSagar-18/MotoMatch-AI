"""Application configuration.

Settings are read from environment variables (and an optional `.env` file).
The only value that matters for Phase 1 is the database connection URL.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "MotoMatch"
    VERSION: str = "2.0.0"

    # Full SQLAlchemy database URL.
    # Default points at a local PostgreSQL instance (source of truth for the catalog).
    # Example: postgresql+psycopg://user:password@host:5432/dbname
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/motomatch"

    # --- AI provider (Phase 2) ---
    # Which AI provider implementation to use. Keeps the app decoupled from a
    # specific vendor; today only "ollama" is implemented.
    AI_PROVIDER: str = "ollama"

    # Local Ollama server + model used to understand the user and manage the
    # conversation. The model only *understands* and *explains*; it never picks
    # a bike (the deterministic engine does that).
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0

    # Embedding model for the RAG bike-knowledge feature (Phase 3). If this
    # model is not pulled, the retriever falls back to keyword matching.
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # --- Frontend integration (Phase 4A) ---
    # Browser origins allowed to call this API (the Vite dev server).
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
