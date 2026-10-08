"""Build the configured AIProvider.

Centralizes the "which provider?" decision so the rest of the app depends only
on the AIProvider interface. Add new providers here as `elif` branches.
"""

from __future__ import annotations

from app.ai.base import AIProvider
from app.ai.ollama_provider import OllamaProvider
from app.core.config import Settings, settings


def build_ai_provider(config: Settings | None = None) -> AIProvider:
    config = config or settings
    provider = config.AI_PROVIDER.lower()

    if provider == "ollama":
        return OllamaProvider(
            base_url=config.OLLAMA_BASE_URL,
            model=config.OLLAMA_MODEL,
            timeout_seconds=config.OLLAMA_TIMEOUT_SECONDS,
            embed_model=config.OLLAMA_EMBED_MODEL,
        )

    raise ValueError(
        f"Unknown AI_PROVIDER '{config.AI_PROVIDER}'. Supported: 'ollama'."
    )
