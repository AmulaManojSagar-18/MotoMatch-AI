"""Ollama implementation of the AIProvider interface.

Talks to a local Ollama server over its HTTP API:
- `POST /api/generate` for text / structured generation.
- `POST /api/embed` for embeddings (used by the RAG layer).

This is the only place in the codebase that knows Ollama exists.
"""

from __future__ import annotations

import httpx

from app.ai.base import AIProvider, AIProviderError


class OllamaProvider(AIProvider):
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float = 60.0,
        embed_model: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.embed_model = embed_model or model

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        format_json: bool = False,
        format_schema: dict | None = None,
    ) -> str:
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            # Low temperature -> more deterministic, reproducible output.
            "options": {"temperature": 0.0},
        }
        if system is not None:
            payload["system"] = system

        if format_schema is not None:
            # Ollama structured outputs: constrain generation to a JSON schema.
            payload["format"] = format_schema
        elif format_json:
            # Ollama's built-in JSON mode: forces syntactically valid JSON.
            payload["format"] = "json"

        data = self._post("/api/generate", payload)
        text = data.get("response")
        if not text:
            raise AIProviderError("Ollama returned an empty response.")
        return text

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = {"model": self.embed_model, "input": texts}
        data = self._post("/api/embed", payload)
        embeddings = data.get("embeddings")
        if not embeddings:
            raise AIProviderError(
                "Ollama returned no embeddings. "
                f"Is the embedding model '{self.embed_model}' pulled "
                "(`ollama pull nomic-embed-text`)?"
            )
        return embeddings

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.post(url, json=payload, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise AIProviderError(
                f"Ollama request failed ({url}): {exc}. "
                "Is the Ollama server running (`ollama serve`) and the model pulled?"
            ) from exc
