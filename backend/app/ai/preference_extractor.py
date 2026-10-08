"""Turn a natural-language message into validated `UserPreferences`.

Flow:
    message -> AIProvider.generate(JSON) -> parse/clean JSON -> UserPreferences

This is the boundary where unstructured LLM output becomes a strict, typed
object. If the model returns malformed or invalid data, we raise a clear error
rather than letting junk flow into the engine.

Resilience: If the model omits optional fields (defaulting to None), we fill
them with schema defaults before validation. This handles models that output
incomplete JSON due to prompt ambiguity or model limitations.
"""

from __future__ import annotations

import json
from copy import deepcopy

from pydantic import ValidationError

from app.ai.base import AIProvider, AIProviderError
from app.ai.prompts import PREFERENCE_SYSTEM_PROMPT, build_preference_prompt
from app.recommendation.schemas import UserPreferences


class PreferenceExtractionError(RuntimeError):
    """Raised when the LLM output cannot be turned into UserPreferences."""


def _extract_json_object(text: str) -> str:
    """Return the first top-level JSON object found in `text`.

    Handles models that wrap JSON in ```code fences``` or add stray prose,
    even though JSON mode usually prevents that.
    """
    text = text.strip()
    # Strip common markdown code fences.
    if text.startswith("```"):
        text = text.strip("`")
        # After stripping backticks a leading "json" language tag may remain.
        if text[:4].lower() == "json":
            text = text[4:]
        text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise PreferenceExtractionError(
            f"No JSON object found in model output: {text!r}"
        )
    return text[start : end + 1]


def _fill_missing_defaults(data: dict) -> dict:
    """Fill missing optional fields with schema defaults for resilience.

    Some models may omit keys entirely. Pydantic validation requires all
    enum fields, so we fill them with defaults before validation.
    """
    filled = deepcopy(data)

    # Priority fields should never be None. A quality the rider did NOT mention
    # defaults to "low" (neutral) so it does not silently tilt the result.
    priorities = [
        "city_usage",
        "touring_usage",
        "adventure_usage",
        "comfort_priority",
        "mileage_priority",
        "performance_priority",
    ]
    for key in priorities:
        if key not in filled or filled[key] is None:
            filled[key] = "low"

    # numeric fields can be null (optional)
    if "budget" not in filled:
        filled["budget"] = None
    if "daily_commute_km" not in filled:
        filled["daily_commute_km"] = None

    return filled


class PreferenceExtractor:
    """Uses an AIProvider to produce validated UserPreferences."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def extract(self, message: str) -> UserPreferences:
        prompt = build_preference_prompt(message)
        try:
            raw = self.provider.generate(
                prompt,
                system=PREFERENCE_SYSTEM_PROMPT,
                format_json=True,
            )
        except AIProviderError as exc:
            raise PreferenceExtractionError(str(exc)) from exc

        json_text = _extract_json_object(raw)
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise PreferenceExtractionError(
                f"Model did not return valid JSON: {json_text!r}"
            ) from exc

        if not isinstance(data, dict):
            raise PreferenceExtractionError(
                f"Expected a JSON object, got {type(data).__name__}."
            )

        # Fill missing fields with defaults for resilience
        data = _fill_missing_defaults(data)

        try:
            return UserPreferences.model_validate(data)
        except ValidationError as exc:
            raise PreferenceExtractionError(
                f"Model output failed preference validation: {exc}"
            ) from exc
