"""Recommendation service: orchestrates the Phase 2 flow.

    message
      -> PreferenceExtractor (AI understands)  -> UserPreferences
      -> BikeRepository (DB provides facts)    -> list[Bike]
      -> RecommendationEngine (engine decides) -> RecommendationResult

The service wires the pieces together but contains no scoring logic itself and
never asks the LLM to choose a bike.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.preference_extractor import PreferenceExtractor
from app.recommendation.engine import RecommendationEngine
from app.recommendation.schemas import RecommendationResult, UserPreferences
from app.repositories.bike_repository import BikeRepository


@dataclass
class Recommendation:
    """What the service hands back to the route."""

    preferences: UserPreferences
    result: RecommendationResult


class RecommendationService:
    def __init__(
        self,
        extractor: PreferenceExtractor,
        engine: RecommendationEngine,
        repository: BikeRepository,
    ) -> None:
        self.extractor = extractor
        self.engine = engine
        self.repository = repository

    def recommend_from_message(self, message: str) -> Recommendation:
        # 1. AI understands the free-text request -> structured preferences.
        preferences = self.extractor.extract(message)
        # 2. Database provides the factual catalog.
        bikes = self.repository.get_all()
        # 3. Engine decides, choosing only from the catalog bikes.
        result = self.engine.recommend(preferences, bikes)
        return Recommendation(preferences=preferences, result=result)

    def recommend_from_preferences(
        self, preferences: UserPreferences
    ) -> Recommendation:
        """Skip the LLM; score a known preference object (useful for testing
        and for callers that already have structured preferences)."""
        bikes = self.repository.get_all()
        result = self.engine.recommend(preferences, bikes)
        return Recommendation(preferences=preferences, result=result)
