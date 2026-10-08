"""Tests for the RAG bike-knowledge layer (documents, vector store, retriever)."""

from app.rag.documents import build_bike_documents
from app.rag.retriever import BikeKnowledgeRetriever
from app.rag.vector_store import InMemoryVectorStore, cosine_similarity
from tests.conftest import ScriptedAIProvider


def test_build_documents_covers_catalog():
    docs = build_bike_documents()
    assert len(docs) == 10
    names = {d.name for d in docs}
    assert "TVS Ronin 225" in names
    ronin = next(d for d in docs if d.name == "TVS Ronin 225")
    assert "225.9" in ronin.text  # factual engine cc present


def test_cosine_similarity_basic():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_vector_store_search_orders_by_similarity():
    store = InMemoryVectorStore()
    store.add(1, [1.0, 0.0], "a")
    store.add(2, [0.0, 1.0], "b")
    results = store.search([0.9, 0.1], k=2)
    assert results[0][1] == "a"  # closest to the query


def test_retriever_keyword_fallback_finds_right_bike():
    # Embeddings unavailable -> keyword overlap retrieval.
    provider = ScriptedAIProvider(embeddings_fail=True)
    retriever = BikeKnowledgeRetriever(provider)

    docs = retriever.retrieve("What is the engine capacity of the Hunter 350?", k=3)
    assert docs
    assert docs[0].name == "Royal Enfield Hunter 350"


def test_retriever_embedding_path_returns_k():
    # Embeddings available (deterministic fake) -> vector search returns k docs.
    provider = ScriptedAIProvider()
    retriever = BikeKnowledgeRetriever(provider)

    docs = retriever.retrieve("touring motorcycle", k=3)
    assert len(docs) == 3
