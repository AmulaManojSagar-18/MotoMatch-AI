"""End-to-end tests for POST /recommend.

The AI provider is overridden with a FakeAIProvider so the whole route runs
deterministically without a live Ollama server. The database is the seeded
in-memory SQLite from the `client` fixture.
"""

import pytest

from app.api.deps import get_ai_provider
from app.data.catalog import BIKE_CATALOG
from app.main import app
from tests.conftest import FakeAIProvider

VALID_IDS = set(range(1, len(BIKE_CATALOG) + 1))

PREFS_JSON = (
    '{"budget": 200000, "daily_commute_km": 40, "city_usage": "high", '
    '"touring_usage": "medium", "adventure_usage": "low", '
    '"comfort_priority": "high", "mileage_priority": "high", '
    '"performance_priority": "low"}'
)


@pytest.fixture()
def fake_provider():
    provider = FakeAIProvider(PREFS_JSON)
    app.dependency_overrides[get_ai_provider] = lambda: provider
    try:
        yield provider
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)


def test_recommend_returns_catalog_bike(client, fake_provider):
    resp = client.post(
        "/recommend",
        json={"message": "Comfortable 40km city commuter, budget 2 lakh, good mileage."},
    )
    assert resp.status_code == 200
    body = resp.json()

    # Shape
    assert "recommended_bike" in body
    assert "score" in body
    assert "preferences" in body
    assert "ranking" in body

    # The recommended bike must be a real catalog bike (no hallucination).
    assert body["recommended_bike"]["id"] in VALID_IDS
    assert 0 <= body["score"] <= 100

    # Extracted preferences flowed through.
    assert body["preferences"]["budget"] == 200000
    assert body["preferences"]["city_usage"] == "high"


def test_recommend_respects_budget(client, fake_provider):
    # Force a tight budget via the fake model output.
    fake_provider.response = '{"budget": 100000, "mileage_priority": "high"}'
    resp = client.post("/recommend", json={"message": "cheap bike under 1 lakh"})
    assert resp.status_code == 200

    price_by_id = {i + 1: d["price"] for i, d in enumerate(BIKE_CATALOG)}
    assert price_by_id[resp.json()["recommended_bike"]["id"]] <= 100000


def test_recommended_id_exists_in_db(client, fake_provider):
    """No-hallucination guard: the recommended id must be fetchable via the
    Phase 1 bikes API, proving it exists in the database."""
    resp = client.post("/recommend", json={"message": "city commuter"})
    bike_id = resp.json()["recommended_bike"]["id"]

    lookup = client.get(f"/bikes/{bike_id}")
    assert lookup.status_code == 200
    assert lookup.json()["id"] == bike_id


def test_recommend_requires_message(client, fake_provider):
    resp = client.post("/recommend", json={"message": ""})
    assert resp.status_code == 422  # fails min_length validation
