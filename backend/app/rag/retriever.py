"""Retriever for bike-knowledge RAG.

Pipeline:  documents -> embeddings -> vector store -> retrieve top-k

Primary path uses `AIProvider.embed` + the in-memory vector store (cosine
similarity). If embeddings are unavailable (e.g. the embedding model isn't
pulled, or Ollama is down), it falls back to a simple keyword-overlap search so
the knowledge feature still works offline. Either way, retrieval is grounded in
the factual catalog documents.
"""

from __future__ import annotations

import re

from app.ai.base import AIProvider, AIProviderError
from app.rag.documents import BikeDocument, build_bike_documents
from app.rag.vector_store import InMemoryVectorStore

# Cache document embeddings per embedding-model so we embed the 10 docs once
# per process rather than on every request.
_EMBED_CACHE: dict[str, InMemoryVectorStore] = {}


def reset_embedding_cache() -> None:
    """Clear the cached document index (used by tests)."""
    _EMBED_CACHE.clear()


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class BikeKnowledgeRetriever:
    def __init__(
        self,
        provider: AIProvider,
        documents: list[BikeDocument] | None = None,
    ) -> None:
        self.provider = provider
        self.documents = documents or build_bike_documents()

    def _model_key(self) -> str:
        return getattr(self.provider, "embed_model", self.provider.__class__.__name__)

    def _get_index(self) -> InMemoryVectorStore | None:
        """Return the embedded vector store, building/caching it on first use.

        Returns None if embeddings are unavailable (caller should fall back).
        """
        key = self._model_key()
        if key in _EMBED_CACHE:
            return _EMBED_CACHE[key]

        try:
            vectors = self.provider.embed([doc.text for doc in self.documents])
        except (AIProviderError, NotImplementedError):
            return None

        store = InMemoryVectorStore()
        for doc, vector in zip(self.documents, vectors):
            store.add(doc.bike_id, vector, doc)
        _EMBED_CACHE[key] = store
        return store

    def retrieve(self, query: str, k: int = 3) -> list[BikeDocument]:
        index = self._get_index()

        if index is not None:
            try:
                query_vector = self.provider.embed([query])[0]
                results = index.search(query_vector, k=k)
                return [payload for _, payload in results]  # type: ignore[misc]
            except (AIProviderError, NotImplementedError):
                pass  # fall through to keyword search

        return self._keyword_retrieve(query, k)

    def _keyword_retrieve(self, query: str, k: int) -> list[BikeDocument]:
        query_tokens = _tokenize(query)
        scored = [
            (len(query_tokens & _tokenize(doc.text)), doc) for doc in self.documents
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        # Only return docs with at least one token overlap; if none overlap,
        # return the top few anyway so the LLM has some context.
        hits = [doc for score, doc in scored if score > 0]
        return (hits or [doc for _, doc in scored])[:k]
