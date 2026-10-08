"""Deterministic recommendation engine.

Responsibility: given validated `UserPreferences` and the 10 factual bikes from
PostgreSQL, decide which bike fits best. This is plain Python business logic --
NO LLM is involved in scoring. The LLM only produced the preferences; the engine
alone decides, and it can only ever pick from the bikes handed to it.

Pipeline:  bikes -> FILTER (budget) -> SCORE (factual specs x preference weights)
           -> RANK -> best

Scoring approach (transparent + factual):
1. For each relevant spec, compute a per-bike metric normalized to 0..1 across
   the current candidates (min-max). Specs that are "more is better" (power,
   mileage, ground clearance, fuel capacity, displacement) map high->1. Specs
   that are "less is better" for accessibility (weight, seat height) are
   inverted so lighter/lower -> 1.
2. Combine metrics into human-meaningful "fit" factors (city, touring,
   adventure, comfort, mileage, performance).
3. Weight each factor by how much the rider cares (from preferences), sum, and
   scale to 0..100.

Weights live in `DEFAULT_WEIGHTS` / `PRIORITY_WEIGHT` so the logic can be tuned
later without rewrites.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.bike import Bike
from app.recommendation.schemas import (
    Priority,
    RecommendationResult,
    ScoredBike,
    UserPreferences,
)

# How strongly each priority level pulls its factor. Modular: tweak freely.
PRIORITY_WEIGHT: dict[Priority, float] = {
    Priority.low: 0.0,
    Priority.medium: 1.0,
    Priority.high: 2.0,
}

# Baseline weight applied to each factor ONLY when the rider expresses no
# strong (high) priority at all, so a sensible default bike still emerges.
# Once the rider states any high priority, the baseline is dropped so their
# stated intent dominates the result instead of generic averages.
BASE_FACTOR_WEIGHT = 0.5

# A factor counts as a "matching reason" when the rider cares about it and the
# bike scores at least this well on it.
MATCH_THRESHOLD = 0.55

# Factor -> human-readable reason label used in explanations.
FACTOR_LABELS: dict[str, str] = {
    "city": "high_city_suitability",
    "touring": "good_for_highway_and_weekend_trips",
    "adventure": "good_for_adventure_riding",
    "comfort": "comfort_priority_match",
    "mileage": "good_mileage",
    "performance": "strong_performance",
}


@dataclass(frozen=True)
class _Metrics:
    """Normalized 0..1 spec metrics for one bike (relative to the candidates)."""

    mileage: float
    power: float
    displacement: float
    fuel: float
    clearance: float
    weight: float  # normalized weight: heavier -> 1
    lightness: float  # inverted weight: lighter -> 1
    low_seat: float  # inverted seat height: lower -> 1


def _normalize(value: float | None, lo: float, hi: float) -> float:
    """Min-max normalize to 0..1. Missing values -> 0.5 (neutral)."""
    if value is None:
        return 0.5
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def _spec_range(bikes: list[Bike], attr: str) -> tuple[float, float]:
    values = [getattr(b, attr) for b in bikes if getattr(b, attr) is not None]
    if not values:
        return (0.0, 0.0)
    return (min(values), max(values))


def _compute_metrics(bikes: list[Bike]) -> dict[int, _Metrics]:
    """Compute normalized metrics for every candidate bike."""
    ranges = {
        attr: _spec_range(bikes, attr)
        for attr in (
            "mileage",
            "power_ps",
            "engine_cc",
            "fuel_capacity_l",
            "ground_clearance_mm",
            "weight_kg",
            "seat_height_mm",
        )
    }

    metrics: dict[int, _Metrics] = {}
    for b in bikes:
        w_lo, w_hi = ranges["weight_kg"]
        s_lo, s_hi = ranges["seat_height_mm"]
        metrics[b.id] = _Metrics(
            mileage=_normalize(b.mileage, *ranges["mileage"]),
            power=_normalize(b.power_ps, *ranges["power_ps"]),
            displacement=_normalize(b.engine_cc, *ranges["engine_cc"]),
            fuel=_normalize(b.fuel_capacity_l, *ranges["fuel_capacity_l"]),
            clearance=_normalize(b.ground_clearance_mm, *ranges["ground_clearance_mm"]),
            weight=_normalize(b.weight_kg, w_lo, w_hi),
            # Inverted: lighter is better for accessibility/city use.
            lightness=1.0 - _normalize(b.weight_kg, w_lo, w_hi),
            # Inverted: lower seat is easier to reach -> more accessible/comfy.
            low_seat=1.0 - _normalize(b.seat_height_mm, s_lo, s_hi),
        )
    return metrics


def _factor_scores(m: _Metrics) -> dict[str, float]:
    """Combine raw metrics into meaningful 0..1 suitability factors.

    Each factor is designed so the *right kind* of bike wins:
    - city: nimble + efficient (but mileage is only part, so a 97cc commuter
      doesn't automatically dominate every other use case).
    - touring/performance/adventure: reward engine capability, which small
      commuters legitimately lack.
    """
    return {
        # Easy around town: light, low seat, efficient.
        "city": (m.lightness + m.low_seat + m.mileage) / 3.0,
        # Highway/weekend trips: range (fuel) + usable power + bigger engine +
        # some mass for stability. A tiny commuter should NOT win here.
        "touring": (m.fuel + m.power + m.displacement + m.weight) / 4.0,
        # Rough stuff: ground clearance is the dominant factor, plus some
        # engine/suspension capability (displacement). NOT just "lightest bike".
        "adventure": (m.clearance * 2.0 + m.displacement) / 3.0,
        # Comfort proxies: an unstressed (bigger) engine and a planted (heavier)
        # bike feel more composed on longer rides; a reachable seat adds ease.
        # Displacement/weight are weighted more than seat so a tiny commuter
        # doesn't read as "most comfortable".
        "comfort": (m.displacement * 2.0 + m.weight + m.low_seat) / 4.0,
        "mileage": m.mileage,
        # Outright go: power + displacement.
        "performance": (m.power + m.displacement) / 2.0,
    }


def _matching_factors(
    prefs: UserPreferences, best_bike: Bike, candidates: list[Bike]
) -> list[str]:
    """Derive human-readable reasons the winning bike fits, from facts only."""
    metrics = _compute_metrics(candidates)
    factors = _factor_scores(metrics[best_bike.id])

    reasons: list[str] = []
    if (
        prefs.budget is not None
        and best_bike.price is not None
        and best_bike.price <= prefs.budget
    ):
        reasons.append("fits_budget")

    priority_by_factor = {
        "city": prefs.city_usage,
        "touring": prefs.touring_usage,
        "adventure": prefs.adventure_usage,
        "comfort": prefs.comfort_priority,
        "mileage": prefs.mileage_priority,
        "performance": prefs.performance_priority,
    }
    for factor, priority in priority_by_factor.items():
        if priority in (Priority.medium, Priority.high) and factors[factor] >= MATCH_THRESHOLD:
            reasons.append(FACTOR_LABELS[factor])
    return reasons


def _factor_weights(prefs: UserPreferences) -> dict[str, float]:
    """Map rider preferences to a weight per factor.

    When the rider states any strong (high) priority, the per-factor baseline is
    dropped so their intent dominates. When they state nothing strong, a small
    baseline keeps the scoring sensible and produces a reasonable default.
    """
    weights = {
        "city": PRIORITY_WEIGHT[prefs.city_usage],
        "touring": PRIORITY_WEIGHT[prefs.touring_usage],
        "adventure": PRIORITY_WEIGHT[prefs.adventure_usage],
        "comfort": PRIORITY_WEIGHT[prefs.comfort_priority],
        "mileage": PRIORITY_WEIGHT[prefs.mileage_priority],
        "performance": PRIORITY_WEIGHT[prefs.performance_priority],
    }

    # Long daily commutes make mileage + comfort matter more, even if the rider
    # didn't explicitly rank them.
    if prefs.daily_commute_km is not None and prefs.daily_commute_km >= 30:
        weights["mileage"] += 1.0
        weights["comfort"] += 0.5
        weights["city"] += 0.5

    # If the rider expressed a strong priority anywhere, let it lead: no baseline
    # dilution. Otherwise apply a baseline so a default bike still surfaces.
    has_strong_signal = any(v >= PRIORITY_WEIGHT[Priority.high] for v in weights.values())
    base = 0.0 if has_strong_signal else BASE_FACTOR_WEIGHT

    return {factor: base + w for factor, w in weights.items()}


class RecommendationEngine:
    def __init__(self, weights_override: dict[str, float] | None = None) -> None:
        # Allows future tuning/experiments without touching the pipeline.
        self.weights_override = weights_override

    def _filter_by_budget(
        self, bikes: list[Bike], budget: int | None
    ) -> list[Bike]:
        """Keep only bikes within budget. If none qualify, budget is ignored
        (we still return the best overall rather than nothing)."""
        if budget is None:
            return list(bikes)
        within = [b for b in bikes if b.price is not None and b.price <= budget]
        return within if within else list(bikes)

    def recommend(
        self, prefs: UserPreferences, bikes: list[Bike]
    ) -> RecommendationResult:
        if not bikes:
            raise ValueError("No bikes available to recommend from.")

        candidates = self._filter_by_budget(bikes, prefs.budget)
        metrics = _compute_metrics(candidates)
        weights = self.weights_override or _factor_weights(prefs)
        weight_total = sum(weights.values()) or 1.0

        scored: list[ScoredBike] = []
        for b in candidates:
            factors = _factor_scores(metrics[b.id])
            weighted = sum(factors[f] * weights.get(f, 0.0) for f in factors)
            score = round((weighted / weight_total) * 100, 2)
            scored.append(
                ScoredBike(id=b.id, brand=b.brand, model=b.model, score=score)
            )

        # Rank by score desc; tie-break by id for deterministic output.
        scored.sort(key=lambda s: (-s.score, s.id))
        best = scored[0]

        best_bike = next(b for b in candidates if b.id == best.id)
        matching = _matching_factors(prefs, best_bike, candidates)

        return RecommendationResult(
            best=best, ranking=scored, best_matching_factors=matching
        )
