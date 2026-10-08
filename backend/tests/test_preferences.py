"""Tests for LLM preference extraction (AI 'understands' step).

A FakeAIProvider supplies canned model output so these tests are deterministic
and need no running Ollama. They verify that raw model text is correctly parsed
and validated into the strict UserPreferences schema.
"""

import pytest

from app.ai.preference_extractor import PreferenceExtractionError, PreferenceExtractor
from app.recommendation.schemas import Priority
from tests.conftest import FakeAIProvider


def test_extracts_structured_preferences():
    model_json = (
        '{"budget": 200000, "daily_commute_km": 40, "city_usage": "high", '
        '"touring_usage": "medium", "adventure_usage": "low", '
        '"comfort_priority": "high", "mileage_priority": "high", '
        '"performance_priority": "low"}'
    )
    extractor = PreferenceExtractor(FakeAIProvider(model_json))

    prefs = extractor.extract(
        "I need a comfortable bike for 40km daily city commuting. "
        "Budget 2 lakh, mileage important."
    )

    assert prefs.budget == 200000
    assert prefs.daily_commute_km == 40
    assert prefs.city_usage == Priority.high
    assert prefs.comfort_priority == Priority.high
    assert prefs.mileage_priority == Priority.high
    assert prefs.performance_priority == Priority.low


def test_budget_and_mileage_only_message():
    # "under 2 lakh with good mileage" -> budget + mileage emphasized.
    model_json = (
        '{"budget": 200000, "daily_commute_km": null, "city_usage": "medium", '
        '"touring_usage": "low", "adventure_usage": "low", '
        '"comfort_priority": "medium", "mileage_priority": "high", '
        '"performance_priority": "low"}'
    )
    prefs = PreferenceExtractor(FakeAIProvider(model_json)).extract(
        "I want a bike under 2 lakh with good mileage."
    )

    assert prefs.budget == 200000
    assert prefs.mileage_priority == Priority.high
    assert prefs.daily_commute_km is None


def test_handles_code_fenced_json():
    model_json = (
        "```json\n"
        '{"budget": 150000, "city_usage": "high", "mileage_priority": "high"}\n'
        "```"
    )
    prefs = PreferenceExtractor(FakeAIProvider(model_json)).extract("cheap city bike")

    assert prefs.budget == 150000
    assert prefs.city_usage == Priority.high
    # Unspecified priorities fall back to schema defaults.
    assert prefs.performance_priority == Priority.low


def test_defaults_applied_for_missing_fields():
    prefs = PreferenceExtractor(FakeAIProvider("{}")).extract("whatever")
    assert prefs.budget is None
    # Unstated priorities are neutral (low) so they don't bias the engine.
    assert prefs.city_usage == Priority.low  # schema default
    assert prefs.touring_usage == Priority.low


def test_invalid_json_raises():
    with pytest.raises(PreferenceExtractionError):
        PreferenceExtractor(FakeAIProvider("not json at all")).extract("hi")


def test_invalid_enum_value_raises():
    bad = '{"city_usage": "super-high"}'
    with pytest.raises(PreferenceExtractionError):
        PreferenceExtractor(FakeAIProvider(bad)).extract("hi")
