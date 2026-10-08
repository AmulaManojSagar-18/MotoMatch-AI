"""End-to-end tests for POST /chat (Phase 3).

The AI provider is overridden with a scripted fake so the full route + agent +
engine + conversation store run deterministically without Ollama. The DB is the
seeded in-memory SQLite from the `client` fixture.
"""

import json

from app.agent import prompts
from app.api.deps import get_ai_provider
from app.main import app
from tests.conftest import FailingAIProvider, ScriptedAIProvider

VALID_IDS = set(range(1, 11))


def _turn(intent="recommend", prefs=None, **extra) -> str:
    return json.dumps(
        {
            "intent": intent,
            "out_of_catalog_request": extra.get("out_of_catalog_request", False),
            "requested_bike_name": extra.get("requested_bike_name"),
            "knowledge_query": extra.get("knowledge_query"),
            "preferences": prefs or {},
        }
    )


def _use_provider(provider):
    app.dependency_overrides[get_ai_provider] = lambda: provider


def test_chat_multi_turn_recommends(client):
    provider = ScriptedAIProvider(
        structured=[
            _turn(prefs={"budget": 200000, "comfort_priority": "high"}),
            _turn(prefs={"city_usage": "high"}),
        ],
        text="I'd recommend this bike because it fits your budget and city use.",
    )
    _use_provider(provider)

    # Turn 1: no conversation_id -> server creates one, asks a follow-up.
    r1 = client.post("/chat", json={"message": "I need a comfortable bike under 2 lakh"})
    assert r1.status_code == 200
    body1 = r1.json()
    cid = body1["conversation_id"]
    assert cid
    assert body1["recommendation"] is None
    assert body1["message"] == prompts.USAGE_QUESTION

    # Turn 2: reuse the conversation_id -> recommendation produced.
    r2 = client.post("/chat", json={"conversation_id": cid, "message": "Mostly city"})
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["conversation_id"] == cid
    assert body2["recommendation"] is not None
    assert body2["recommendation"]["bike_id"] in VALID_IDS


def test_chat_recommended_bike_exists_in_db(client):
    provider = ScriptedAIProvider(
        structured=[_turn(prefs={"budget": 200000, "city_usage": "high"})],
        text="explanation",
    )
    _use_provider(provider)

    resp = client.post("/chat", json={"message": "city bike under 2 lakh"})
    rec = resp.json()["recommendation"]
    assert rec is not None

    # No-hallucination guard: the id resolves via the Phase 1 bikes API.
    lookup = client.get(f"/bikes/{rec['bike_id']}")
    assert lookup.status_code == 200
    assert lookup.json()["id"] == rec["bike_id"]


def test_chat_out_of_catalog(client):
    provider = ScriptedAIProvider(
        structured=[
            _turn(intent="chitchat", out_of_catalog_request=True,
                  requested_bike_name="Ducati")
        ]
    )
    _use_provider(provider)

    resp = client.post("/chat", json={"message": "Recommend a Ducati"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["recommendation"] is None
    assert "catalog" in body["message"].lower()


def test_chat_ollama_unavailable_returns_502(client):
    _use_provider(FailingAIProvider())
    resp = client.post("/chat", json={"message": "recommend a bike"})
    assert resp.status_code == 502


def test_chat_requires_message(client):
    _use_provider(ScriptedAIProvider())
    resp = client.post("/chat", json={"message": ""})
    assert resp.status_code == 422
