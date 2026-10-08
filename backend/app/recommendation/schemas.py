"""Structured data for the recommendation flow.

`UserPreferences` is the strict contract between the AI layer and the
recommendation engine. The LLM's free-form output is parsed/validated into
this schema; only validated preferences ever reach the engine. The engine
never sees raw LLM text.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Priority(str, Enum):
    """How much the rider cares about a given quality (or how much they use it)."""

    low = "low"
    medium = "medium"
    high = "high"


class UserPreferences(BaseModel):
    """Structured rider requirements derived from natural language.

    Numeric fields are optional (the user may not mention them). Priority fields
    default to `low` (neutral) when unstated, so an unmentioned quality does NOT
    silently tilt the recommendation. Only what the rider actually expresses
    drives the result; this prevents a single lightweight/efficient bike from
    always winning under-specified requests.
    """

    model_config = ConfigDict(extra="ignore")

    # Hard constraint used for filtering (approx ex-showroom INR). Optional.
    budget: int | None = Field(default=None, ge=0)

    # Context signal; higher daily distance nudges mileage/comfort importance.
    daily_commute_km: int | None = Field(default=None, ge=0)

    # Usage intents (default low = not a stated concern).
    city_usage: Priority = Priority.low
    touring_usage: Priority = Priority.low
    adventure_usage: Priority = Priority.low

    # Quality priorities (default low = not a stated concern).
    comfort_priority: Priority = Priority.low
    mileage_priority: Priority = Priority.low
    performance_priority: Priority = Priority.low


class ScoredBike(BaseModel):
    """A single bike with its computed suitability score (0-100)."""

    id: int
    brand: str
    model: str
    score: float


class RecommendationResult(BaseModel):
    """Full engine output: the winner plus the ranked field.

    `best_matching_factors` lists human-readable reasons (derived
    deterministically from facts + preferences) that the LLM can turn into a
    grounded explanation. It defaults to empty so Phase 2 callers are
    unaffected.
    """

    best: ScoredBike
    ranking: list[ScoredBike]
    best_matching_factors: list[str] = []
