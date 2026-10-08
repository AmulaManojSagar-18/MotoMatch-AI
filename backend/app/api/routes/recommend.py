"""Recommendation route.

POST /recommend: natural-language message in, best-matching catalog bike out.
The route only orchestrates (call service, map to response, translate errors);
all intelligence lives in the AI layer and the engine.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.preference_extractor import PreferenceExtractionError
from app.api.deps import get_recommendation_service
from app.schemas.recommend import (
    RecommendedBike,
    RecommendRequest,
    RecommendResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("", response_model=RecommendResponse, summary="Recommend a bike")
def recommend(
    payload: RecommendRequest,
    service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendResponse:
    try:
        outcome = service.recommend_from_message(payload.message)
    except PreferenceExtractionError as exc:
        # The AI layer failed (model offline, unparseable output, etc.).
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not understand the request via the AI provider: {exc}",
        ) from exc

    best = outcome.result.best
    return RecommendResponse(
        recommended_bike=RecommendedBike(id=best.id, brand=best.brand, model=best.model),
        score=best.score,
        preferences=outcome.preferences,
        ranking=outcome.result.ranking,
    )
