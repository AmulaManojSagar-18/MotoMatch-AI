"""Pytest fixtures.

Tests run against an in-memory SQLite database so they are fast and require no
PostgreSQL server. We override the `get_db` dependency so the app uses the test
database, and we seed it from the same catalog the real seed script uses.
"""

import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.base import AIProvider, AIProviderError
from app.data.catalog import BIKE_CATALOG
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.bike import Bike


def _make_seeded_engine():
    """Create an in-memory SQLite engine seeded with the fixed catalog."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    db = SessionLocal()
    try:
        db.add_all([Bike(**data) for data in BIKE_CATALOG])
        db.commit()
    finally:
        db.close()
    return engine, SessionLocal


def _deterministic_vector(text: str, dim: int = 16) -> list[float]:
    """Stable pseudo-embedding derived from text (for RAG tests)."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(dim)]


class FakeAIProvider(AIProvider):
    """Deterministic stand-in for a real LLM.

    Returns a preset response so preference extraction and the /recommend
    endpoint can be tested without a running Ollama server.
    """

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[str] = []

    def generate(
        self, prompt, *, system=None, format_json=False, format_schema=None
    ) -> str:
        self.calls.append(prompt)
        return self.response

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_deterministic_vector(t) for t in texts]


class ScriptedAIProvider(AIProvider):
    """Programmable fake for multi-turn agent tests.

    - `structured` is a queue of JSON strings returned when a structured/JSON
      response is requested (one per turn's TurnAnalysis call).
    - `text` is returned for plain-text calls (explanations / knowledge answers)
      and may be a single string or a queue.
    - `embeddings_fail=True` makes embed() raise, exercising the keyword fallback.
    """

    def __init__(
        self,
        structured: list[str] | None = None,
        text: list[str] | str | None = None,
        embeddings_fail: bool = False,
    ) -> None:
        self.structured = list(structured or [])
        self.text = text
        self.embeddings_fail = embeddings_fail
        self.calls: list[dict] = []
        self.embed_model = "fake-embed"

    def generate(
        self, prompt, *, system=None, format_json=False, format_schema=None
    ) -> str:
        structured_requested = bool(format_json or format_schema)
        self.calls.append({"prompt": prompt, "structured": structured_requested})
        if structured_requested:
            return self.structured.pop(0) if self.structured else "{}"
        if isinstance(self.text, list):
            return self.text.pop(0) if self.text else "OK"
        return self.text if self.text is not None else "OK"

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.embeddings_fail:
            raise AIProviderError("embeddings unavailable")
        return [_deterministic_vector(t) for t in texts]


class FailingAIProvider(AIProvider):
    """Simulates an unavailable provider (e.g. Ollama down)."""

    def generate(
        self, prompt, *, system=None, format_json=False, format_schema=None
    ) -> str:
        raise AIProviderError("Ollama is not reachable")

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise AIProviderError("Ollama is not reachable")


@pytest.fixture()
def db_session():
    """A seeded SQLite session for direct repository/engine tests."""
    engine, SessionLocal = _make_seeded_engine()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def catalog_bikes(db_session):
    """The 10 seeded Bike ORM objects (with ids), ordered by id."""
    from app.repositories.bike_repository import BikeRepository

    return BikeRepository(db_session).get_all()


@pytest.fixture(autouse=True)
def _reset_phase3_state():
    """Keep Phase 3 global state isolated between tests."""
    from app.api.deps import get_conversation_store
    from app.rag.retriever import reset_embedding_cache

    get_conversation_store().reset()
    reset_embedding_cache()
    yield
    get_conversation_store().reset()
    reset_embedding_cache()


@pytest.fixture()
def client():
    # Shared in-memory SQLite DB (StaticPool keeps a single connection so the
    # schema/data persist across the app's requests within a test).
    engine, TestingSessionLocal = _make_seeded_engine()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
