"""AI provider abstraction.

Business logic depends on this interface, NOT on Ollama directly. To add a new
provider later (OpenAI, a hosted model, etc.), implement `AIProvider` and swap
it in via configuration/dependency injection -- nothing else changes.

The interface stays small:
- `generate`: prompt in, text out (optionally forced to JSON / a JSON schema).
- `embed`: text(s) in, embedding vector(s) out (used by the RAG layer).

Turning generated text into structured data is the caller's job (see
app/ai/preference_extractor.py and app/agent/agent.py).
"""

from abc import ABC, abstractmethod


class AIProviderError(RuntimeError):
    """Raised when an AI provider cannot produce a response."""


class AIProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        format_json: bool = False,
        format_schema: dict | None = None,
    ) -> str:
        """Generate a text completion for `prompt`.

        Args:
            prompt: The user-facing instruction/content.
            system: Optional system instruction to steer behaviour.
            format_json: Hint that the response must be valid JSON. Providers
                that support a JSON mode should enable it.
            format_schema: Optional JSON Schema (e.g. a Pydantic model's
                `model_json_schema()`). Providers that support structured
                outputs should constrain generation to this schema. Takes
                precedence over `format_json`.

        Returns:
            The raw generated text.

        Raises:
            AIProviderError: If generation fails (network, model, etc.).
        """
        raise NotImplementedError

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return an embedding vector for each input text.

        Optional capability. Providers that cannot embed should leave this
        raising, and callers (the RAG retriever) will fall back gracefully.

        Raises:
            AIProviderError: If embedding fails or is unavailable.
        """
        raise NotImplementedError("This provider does not support embeddings.")
