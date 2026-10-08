"""Tests for the deterministic recommendation engine (engine 'decides' step)."""

from app.data.catalog import BIKE_CATALOG
from app.recommendation.engine import RecommendationEngine
from app.recommendation.schemas import Priority, UserPreferences

# Seeded ids are 1..10 in catalog order.
PRICE_BY_ID = {i + 1: data["price"] for i, data in enumerate(BIKE_CATALOG)}
VALID_IDS = set(PRICE_BY_ID.keys())


def test_returns_a_bike_from_catalog(catalog_bikes):
    prefs = UserPreferences(city_usage=Priority.high, mileage_priority=Priority.high)
    result = RecommendationEngine().recommend(prefs, catalog_bikes)

    assert result.best.id in VALID_IDS
    assert 0 <= result.best.score <= 100
    # Ranking covers every candidate and is sorted high -> low.
    assert len(result.ranking) == len(catalog_bikes)
    scores = [r.score for r in result.ranking]
    assert scores == sorted(scores, reverse=True)


def test_no_hallucinated_bikes(catalog_bikes):
    prefs = UserPreferences(performance_priority=Priority.high)
    result = RecommendationEngine().recommend(prefs, catalog_bikes)

    for scored in result.ranking:
        assert scored.id in VALID_IDS


def test_budget_filter_excludes_expensive_bikes(catalog_bikes):
    # Only Hero Splendor+ (80,000) is <= 100,000; everything else is >= 150,000.
    prefs = UserPreferences(budget=100000, mileage_priority=Priority.high)
    result = RecommendationEngine().recommend(prefs, catalog_bikes)

    assert PRICE_BY_ID[result.best.id] <= 100000
    # Only the one in-budget bike should be in the ranking.
    assert len(result.ranking) == 1
    assert result.best.id == 1  # Hero Splendor+


def test_budget_filter_keeps_only_affordable(catalog_bikes):
    prefs = UserPreferences(budget=160000)
    result = RecommendationEngine().recommend(prefs, catalog_bikes)

    # Every ranked bike must be within budget.
    for scored in result.ranking:
        assert PRICE_BY_ID[scored.id] <= 160000
    assert PRICE_BY_ID[result.best.id] <= 160000


def test_mileage_priority_prefers_most_efficient(catalog_bikes):
    # Hero Splendor+ has the highest mileage (70) in the catalog.
    prefs = UserPreferences(mileage_priority=Priority.high)
    result = RecommendationEngine().recommend(prefs, catalog_bikes)
    assert result.best.id == 1


def test_performance_priority_prefers_most_powerful(catalog_bikes):
    # Continental GT 650 has the highest power (47) and displacement (648).
    prefs = UserPreferences(performance_priority=Priority.high)
    result = RecommendationEngine().recommend(prefs, catalog_bikes)
    assert result.best.id == 10


def test_over_budget_not_selected_when_affordable_exist(catalog_bikes):
    # The most powerful bikes are expensive; with a tight budget + performance
    # preference, the engine must still stay within budget.
    prefs = UserPreferences(budget=150000, performance_priority=Priority.high)
    result = RecommendationEngine().recommend(prefs, catalog_bikes)
    assert PRICE_BY_ID[result.best.id] <= 150000
