"""Tests for the conversational agent (Phase 3), using scripted fake providers.

These are deterministic and need no running Ollama: the ScriptedAIProvider
returns the exact TurnAnalysis JSON per turn and canned explanation text.
"""

import pytest

from app.agent import prompts
from app.agent.agent import ConversationAgent
from app.agent.schemas import ConversationState, PreferenceUpdate
from app.ai.base import AIProviderError
from app.rag.retriever import BikeKnowledgeRetriever
from app.recommendation.engine import RecommendationEngine
from app.recommendation.schemas import Priority
from app.repositories.bike_repository import BikeRepository
from tests.conftest import FailingAIProvider, ScriptedAIProvider

VALID_IDS = set(range(1, 11))


def _make_agent(provider, db_session) -> ConversationAgent:
    return ConversationAgent(
        provider=provider,
        repository=BikeRepository(db_session),
        engine=RecommendationEngine(),
        retriever=BikeKnowledgeRetriever(provider),
    )


def _turn(intent="recommend", prefs=None, **extra) -> str:
    import json

    payload = {
        "intent": intent,
        "out_of_catalog_request": extra.get("out_of_catalog_request", False),
        "requested_bike_name": extra.get("requested_bike_name"),
        "knowledge_query": extra.get("knowledge_query"),
        "preferences": prefs or {},
    }
    return json.dumps(payload)


# --- conversation state unit tests -----------------------------------------

def test_merge_preferences_does_not_lose_previous():
    state = ConversationState("c")
    state.merge_preferences(PreferenceUpdate(budget=200000))
    state.merge_preferences(PreferenceUpdate(city_usage=Priority.high))
    state.merge_preferences(PreferenceUpdate(comfort_priority=Priority.high))

    assert state.accumulated.budget == 200000
    assert state.accumulated.city_usage == Priority.high
    assert state.accumulated.comfort_priority == Priority.high


def test_merge_ignores_none_values():
    state = ConversationState("c")
    state.merge_preferences(PreferenceUpdate(budget=200000))
    # A later turn that mentions nothing new must not wipe the budget.
    state.merge_preferences(PreferenceUpdate())
    assert state.accumulated.budget == 200000


# --- multi-turn flow -------------------------------------------------------

def test_multi_turn_accumulates_then_recommends(db_session):
    provider = ScriptedAIProvider(
        structured=[
            _turn(prefs={"budget": 200000, "comfort_priority": "high"}),
            _turn(prefs={"city_usage": "high"}),
        ],
        text="I recommend this bike because it fits your needs.",
    )
    agent = _make_agent(provider, db_session)
    state = ConversationState("c1")

    # Turn 1: budget + comfort known, usage missing -> ask about usage.
    r1 = agent.handle_turn(state, "I need a comfortable bike under 2 lakh")
    assert r1.recommendation is None
    assert r1.message == prompts.USAGE_QUESTION

    # Turn 2: usage provided -> recommend. Earlier prefs are retained.
    r2 = agent.handle_turn(state, "Mostly city")
    assert r2.recommendation is not None
    assert r2.recommendation.bike_id in VALID_IDS
    assert state.accumulated.budget == 200000
    assert state.accumulated.comfort_priority == Priority.high
    assert state.accumulated.city_usage == Priority.high


def test_follow_up_asks_budget_first_when_missing(db_session):
    provider = ScriptedAIProvider(structured=[_turn(prefs={})])
    agent = _make_agent(provider, db_session)
    state = ConversationState("c2")

    r = agent.handle_turn(state, "Recommend me a bike")
    assert r.recommendation is None
    assert r.message == prompts.BUDGET_QUESTION


def test_recommendation_always_in_catalog_even_below_all_budgets(db_session):
    # Budget below the cheapest bike: engine relaxes budget but still returns a
    # real catalog bike (never fabricated).
    provider = ScriptedAIProvider(
        structured=[_turn(prefs={"budget": 30000, "city_usage": "high"})],
        text="explanation",
    )
    agent = _make_agent(provider, db_session)
    state = ConversationState("c3")

    r = agent.handle_turn(state, "cheap city bike, budget 30k")
    assert r.recommendation is not None
    assert r.recommendation.bike_id in VALID_IDS


def test_tool_result_has_score_and_matching_factors(db_session):
    provider = ScriptedAIProvider(
        structured=[_turn(prefs={"budget": 200000, "city_usage": "high",
                                 "mileage_priority": "high"})],
        text="explanation",
    )
    agent = _make_agent(provider, db_session)
    state = ConversationState("c4")

    r = agent.handle_turn(state, "city bike under 2 lakh, great mileage")
    assert r.recommendation is not None
    assert 0 <= r.recommendation.score <= 100
    assert isinstance(r.recommendation.matching_factors, list)
    assert "fits_budget" in r.recommendation.matching_factors


# --- explanation grounding -------------------------------------------------

def test_explanation_prompt_is_grounded_in_results(db_session):
    provider = ScriptedAIProvider(
        structured=[_turn(prefs={"budget": 200000, "city_usage": "high"})],
        text="Here is why.",
    )
    agent = _make_agent(provider, db_session)
    state = ConversationState("c5")

    r = agent.handle_turn(state, "city bike under 2 lakh")

    # The explanation (plain-text) call must include the recommended bike and
    # its score -- proving the explanation is built from the engine's result.
    text_calls = [c["prompt"] for c in provider.calls if not c["structured"]]
    assert text_calls, "expected an explanation LLM call"
    explain_prompt = text_calls[-1]
    assert r.recommendation.bike_name in explain_prompt
    assert str(r.recommendation.score) in explain_prompt


def test_build_explain_prompt_contains_facts_and_factors():
    prompt = prompts.build_explain_prompt(
        bike_name="TVS Ronin 225",
        score=91.0,
        matching_factors=["fits_budget", "high_city_suitability"],
        facts="Price approx INR 150000; mileage 40 kmpl.",
        preferences="{}",
    )
    assert "TVS Ronin 225" in prompt
    assert "fits_budget" in prompt
    assert "91.0" in prompt
    assert "40 kmpl" in prompt


# --- safety / error handling -----------------------------------------------

def test_out_of_catalog_request_is_refused(db_session):
    provider = ScriptedAIProvider(
        structured=[
            _turn(intent="chitchat", out_of_catalog_request=True,
                  requested_bike_name="Ducati Panigale")
        ]
    )
    agent = _make_agent(provider, db_session)
    state = ConversationState("c6")

    r = agent.handle_turn(state, "Recommend a Ducati Panigale")
    assert r.recommendation is None
    assert "catalog" in r.message.lower()


def test_invalid_ai_output_is_handled_gracefully(db_session):
    provider = ScriptedAIProvider(structured=["this is not valid json"])
    agent = _make_agent(provider, db_session)
    state = ConversationState("c7")

    r = agent.handle_turn(state, "something")
    assert r.recommendation is None
    assert r.message == prompts.CLARIFY_REPLY


def test_ollama_unavailable_raises(db_session):
    agent = _make_agent(FailingAIProvider(), db_session)
    state = ConversationState("c8")

    with pytest.raises(AIProviderError):
        agent.handle_turn(state, "recommend a bike")


def test_knowledge_question_uses_rag_answer(db_session):
    provider = ScriptedAIProvider(
        structured=[
            _turn(intent="knowledge",
                  knowledge_query="engine capacity of Royal Enfield Hunter 350")
        ],
        text="The Hunter 350 uses a 349.34 cc engine.",
    )
    agent = _make_agent(provider, db_session)
    state = ConversationState("c9")

    r = agent.handle_turn(state, "What is the engine capacity of the Hunter 350?")
    assert r.recommendation is None
    assert r.message == "The Hunter 350 uses a 349.34 cc engine."


def test_in_catalog_bike_not_refused_when_model_mislabels_it(db_session):
    # The model wrongly flags an in-catalog bike (Hunter 350) as out-of-catalog
    # and labels the turn chitchat. The agent must correct this against the real
    # catalog and answer the knowledge question instead of refusing.
    provider = ScriptedAIProvider(
        structured=[
            _turn(intent="chitchat", out_of_catalog_request=True,
                  requested_bike_name="Royal Enfield Hunter 350")
        ],
        text="The Hunter 350 has a 349.34 cc engine.",
    )
    agent = _make_agent(provider, db_session)
    state = ConversationState("c10")

    r = agent.handle_turn(state, "What is the engine capacity of the Hunter 350?")
    assert r.recommendation is None
    assert "catalog" not in r.message.lower()  # NOT refused
    assert r.message == "The Hunter 350 has a 349.34 cc engine."
