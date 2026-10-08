"""Application tools the agent can call.

These are plain, deterministic Python functions -- the "tools" in the agent
architecture. The LLM decides WHEN to call them (via the structured turn
analysis), but the tools themselves do real application work and never rely on
the LLM for their result:

- recommend_bike  -> runs the Phase 2 recommendation engine over the DB catalog.
- get_bike_knowledge -> retrieves factual bike documents via RAG.

The LLM never touches PostgreSQL or computes scores directly.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.ai.base import AIProvider
from app.rag.documents import BikeDocument
from app.rag.retriever import BikeKnowledgeRetriever
from app.recommendation.engine import RecommendationEngine
from app.recommendation.schemas import UserPreferences
from app.repositories.bike_repository import BikeRepository


class ToolError(RuntimeError):
    """Raised when a tool cannot complete its work."""


class RecommendBikeResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    bike_id: int
    bike_name: str
    score: float
    matching_factors: list[str]
    facts: str  # factual, human-readable specs used to ground the explanation


class KnowledgeResult(BaseModel):
    context: str              # concatenated reference facts for the LLM
    sources: list[str]        # bike names the facts came from


def recommend_bike(
    preferences: UserPreferences,
    repository: BikeRepository,
    engine: RecommendationEngine,
) -> RecommendBikeResult:
    """Tool: pick the best catalog bike for the given preferences.

    Delegates the actual decision to the deterministic engine, over the bikes
    stored in PostgreSQL. The result is always one of the catalog bikes.
    """
    bikes = repository.get_all()
    if not bikes:
        raise ToolError("No bikes available in the catalog to recommend from.")

    result = engine.recommend(preferences, bikes)
    best = result.best
    bike = next(b for b in bikes if b.id == best.id)

    facts = (
        f"Price approx INR {bike.price}; engine {bike.engine_cc} cc; "
        f"power {bike.power_ps} PS; mileage {bike.mileage} kmpl; "
        f"weight {bike.weight_kg} kg; seat height {bike.seat_height_mm} mm; "
        f"category {bike.category}."
    )

    return RecommendBikeResult(
        bike_id=best.id,
        bike_name=f"{bike.brand} {bike.model}",
        score=best.score,
        matching_factors=result.best_matching_factors,
        facts=facts,
    )


def get_bike_knowledge(
    query: str,
    retriever: BikeKnowledgeRetriever,
    k: int = 3,
) -> KnowledgeResult:
    """Tool: retrieve factual reference documents for a knowledge question."""
    documents: list[BikeDocument] = retriever.retrieve(query, k=k)
    context = "\n".join(f"- {doc.text}" for doc in documents)
    sources = [doc.name for doc in documents]
    return KnowledgeResult(context=context, sources=sources)
