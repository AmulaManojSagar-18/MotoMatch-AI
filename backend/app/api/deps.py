"""FastAPI dependency wiring.

This assembles the per-request object graph:

    get_db -> Session -> BikeRepository -> BikeService

Routes depend on `get_bike_service`, so they never construct repositories or
sessions themselves. This keeps the layers decoupled and easy to test (the
dependency can be overridden).
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.agent.agent import ConversationAgent
from app.agent.store import ConversationStore
from app.ai.base import AIProvider
from app.ai.factory import build_ai_provider
from app.ai.preference_extractor import PreferenceExtractor
from app.db.session import get_db
from app.rag.retriever import BikeKnowledgeRetriever
from app.recommendation.engine import RecommendationEngine
from app.repositories.bike_repository import BikeRepository
from app.services.bike_service import BikeService
from app.services.recommendation_service import RecommendationService


def get_bike_service(db: Session = Depends(get_db)) -> BikeService:
    return BikeService(BikeRepository(db))


def get_ai_provider() -> AIProvider:
    """Return the configured AI provider.

    Declared as its own dependency so tests can override it with a fake,
    keeping the recommendation flow fully deterministic without a live LLM.
    """
    return build_ai_provider()


def get_recommendation_service(
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
) -> RecommendationService:
    return RecommendationService(
        extractor=PreferenceExtractor(provider),
        engine=RecommendationEngine(),
        repository=BikeRepository(db),
    )


# Single process-wide conversation store so multi-turn state survives across
# requests. Simple by design (Phase 3); swap for Redis/durable storage later.
_conversation_store = ConversationStore()


def get_conversation_store() -> ConversationStore:
    return _conversation_store


def get_conversation_agent(
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
) -> ConversationAgent:
    return ConversationAgent(
        provider=provider,
        repository=BikeRepository(db),
        engine=RecommendationEngine(),
        retriever=BikeKnowledgeRetriever(provider),
    )
