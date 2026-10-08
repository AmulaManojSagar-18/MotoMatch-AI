"""API request/response schemas for the recommendation endpoint."""

from pydantic import BaseModel, ConfigDict, Field

from app.recommendation.schemas import ScoredBike, UserPreferences


class RecommendRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="The rider's requirements in natural language.",
        examples=[
            "I need a comfortable bike for 40km daily city commuting. "
            "My budget is 2 lakh and mileage is important."
        ],
    )


class RecommendedBike(BaseModel):
    """The chosen bike (a subset of the full Bike record)."""

    model_config = ConfigDict(protected_namespaces=())

    id: int
    brand: str
    model: str


class RecommendResponse(BaseModel):
    recommended_bike: RecommendedBike
    score: float
    preferences: UserPreferences
    # Full ranked list so callers can see runners-up / explain the choice later.
    ranking: list[ScoredBike]
