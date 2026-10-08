"""The MotoMatch conversational agent (Phase 3).

One agent, a small set of tools, explicit orchestration (no LangChain). Each
turn:

    user message
      -> ANALYZE (LLM, structured TurnAnalysis)   # understand + route
      -> accumulate preferences into conversation state
      -> route:
           out-of-catalog  -> safety reply
           knowledge        -> get_bike_knowledge tool (RAG) -> grounded answer
           recommend        -> ask follow-up OR recommend_bike tool -> explanation
           chitchat         -> greeting

Responsibility split is strict:
- The LLM understands the user, manages the conversation, and explains.
- The engine (via the recommend_bike tool) DECIDES the bike.
- PostgreSQL is the source of truth; RAG only supports knowledge answers.

We use structured outputs for the agent's decision rather than a specific
model's native tool-call format, which keeps orchestration explicit, reliable
with local models, and easy to test. The deterministic parts (preference
accumulation, readiness, scoring) never depend on the LLM.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import ValidationError

from app.agent import prompts
from app.agent.schemas import (
    ChatRole,
    ConversationState,
    RecommendationPayload,
    TurnAnalysis,
    TurnIntent,
)
from app.agent.tools import ToolError, get_bike_knowledge, recommend_bike
from app.ai.base import AIProvider, AIProviderError
from app.data.catalog import BIKE_CATALOG
from app.rag.retriever import BikeKnowledgeRetriever
from app.recommendation.engine import RecommendationEngine
from app.repositories.bike_repository import BikeRepository

# Cap follow-up questions so we never interrogate the user endlessly.
MAX_FOLLOWUP_QUESTIONS = 2

_QUESTION_STARTERS = (
    "what", "which", "how", "does", "do", "is", "are", "can", "could",
    "tell", "give", "list", "explain", "whats",
)


def _distinctive_tokens(text: str) -> set[str]:
    """Alpha tokens (len>=2) that identify a bike brand/model."""
    return {t for t in re.findall(r"[a-z]+", text.lower()) if len(t) >= 2}


# (display name, identifying keyword set) for each catalog bike.
_CATALOG_KEYWORDS: list[tuple[str, set[str]]] = [
    (
        f"{b['brand']} {b['model']}",
        _distinctive_tokens(b["brand"]) | _distinctive_tokens(b["model"]),
    )
    for b in BIKE_CATALOG
]


def _match_catalog_bike(text: str | None) -> str | None:
    """Return the catalog bike name referenced in `text`, or None.

    Deterministic ground truth for "is this bike in our catalog?", used to
    correct the LLM when it mislabels an in-catalog bike as out-of-catalog.
    """
    if not text:
        return None
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    for name, keywords in _CATALOG_KEYWORDS:
        if keywords & tokens:
            return name
    return None


def _looks_like_question(text: str) -> bool:
    stripped = text.strip().lower()
    if "?" in stripped:
        return True
    words = stripped.split()
    return bool(words) and words[0] in _QUESTION_STARTERS

# Human-readable phrasing for engine match reasons (used in the fallback
# explanation when the LLM is unavailable).
_FACTOR_PHRASES = {
    "fits_budget": "it stays within your budget",
    "high_city_suitability": "it suits city commuting",
    "good_for_highway_and_weekend_trips": "it handles highway and weekend trips",
    "good_for_adventure_riding": "it is capable off-road",
    "comfort_priority_match": "it offers the comfort you want",
    "good_mileage": "it delivers good mileage",
    "strong_performance": "it has strong performance",
}


@dataclass
class ChatTurnResult:
    message: str
    recommendation: RecommendationPayload | None = None


class ConversationAgent:
    def __init__(
        self,
        provider: AIProvider,
        repository: BikeRepository,
        engine: RecommendationEngine,
        retriever: BikeKnowledgeRetriever,
    ) -> None:
        self.provider = provider
        self.repository = repository
        self.engine = engine
        self.retriever = retriever

    # -- public entry point -------------------------------------------------

    def handle_turn(self, state: ConversationState, message: str) -> ChatTurnResult:
        """Process one user message and produce the assistant's reply.

        Raises AIProviderError if the LLM is needed but unavailable for
        understanding the message (surfaced by the route as a 502).
        """
        state.add_message(ChatRole.user, message)

        analysis = self._analyze_turn(state, message)
        if analysis is None:
            # Invalid/unparseable AI output -> ask for clarification gracefully.
            return self._finish(state, prompts.CLARIFY_REPLY, None)

        state.merge_preferences(analysis.preferences)

        # Only honor an out-of-catalog refusal when the model actually named a
        # specific bike that is genuinely NOT in our catalog. Local models tend
        # to over-trigger this flag, so we validate it against the real catalog:
        #   - no specific bike named           -> not a refusal (ignore flag)
        #   - named bike IS in our catalog     -> not a refusal (model error)
        if analysis.out_of_catalog_request:
            requested = analysis.requested_bike_name
            named_out_of_catalog = (
                bool(requested)
                and _match_catalog_bike(requested) is None
                and _match_catalog_bike(message) is None
            )
            if not named_out_of_catalog:
                analysis.out_of_catalog_request = False

        # 1. Genuine out-of-catalog request -> safety reply.
        if analysis.out_of_catalog_request:
            reply = prompts.out_of_catalog_reply(analysis.requested_bike_name)
            return self._finish(state, reply, None)

        # 2. Knowledge question -> RAG-grounded answer. We trust the model's
        #    knowledge intent, and also deterministically catch factual
        #    questions about a catalog bike that the model misrouted.
        knowledge_query = self._resolve_knowledge_query(analysis, message)
        if knowledge_query is not None:
            reply = self._answer_knowledge(knowledge_query)
            return self._finish(state, reply, None)

        # 3. Recommendation path (explicit intent, or we already have signal).
        if (
            analysis.intent == TurnIntent.recommend
            or state.budget_known
            or state.usage_known
        ):
            return self._recommend_or_ask(state)

        # 4. Fallback: greeting / unclear.
        return self._finish(state, prompts.GREETING_REPLY, None)

    def _resolve_knowledge_query(
        self, analysis: TurnAnalysis, message: str
    ) -> str | None:
        """Decide whether this turn is a knowledge question, and what to ask."""
        if analysis.intent == TurnIntent.knowledge:
            return analysis.knowledge_query or message

        # Deterministic assist: a factual question naming a catalog bike, with
        # no new preferences this turn, is a knowledge query even if the model
        # labelled the intent differently.
        no_new_preferences = not analysis.preferences.model_dump(exclude_none=True)
        if (
            _match_catalog_bike(message)
            and _looks_like_question(message)
            and no_new_preferences
        ):
            return message
        return None

    # -- turn analysis (LLM, structured) ------------------------------------

    def _analyze_turn(
        self, state: ConversationState, message: str
    ) -> TurnAnalysis | None:
        history = self._format_history(state)
        known = self._format_known_preferences(state)
        prompt = prompts.build_analyze_prompt(message, history, known)

        raw = self.provider.generate(
            prompt,
            system=prompts.ANALYZE_SYSTEM_PROMPT,
            format_schema=TurnAnalysis.model_json_schema(),
        )

        data = self._loads_json(raw)
        if data is None:
            return None
        try:
            return TurnAnalysis.model_validate(data)
        except ValidationError:
            return None

    # -- recommendation path ------------------------------------------------

    def _recommend_or_ask(self, state: ConversationState) -> ChatTurnResult:
        # Ask for the few things that materially affect quality, but cap it.
        if not state.budget_known and state.questions_asked < MAX_FOLLOWUP_QUESTIONS:
            state.questions_asked += 1
            return self._finish(state, prompts.BUDGET_QUESTION, None)

        if not state.usage_known and state.questions_asked < MAX_FOLLOWUP_QUESTIONS:
            state.questions_asked += 1
            return self._finish(state, prompts.USAGE_QUESTION, None)

        # Enough information (or we've asked enough) -> run the engine via tool.
        preferences = state.to_user_preferences()
        try:
            result = recommend_bike(preferences, self.repository, self.engine)
        except ToolError:
            # Never fabricate a recommendation.
            return self._finish(
                state,
                "I'm sorry, I couldn't produce a recommendation right now. "
                "Please try again shortly.",
                None,
            )

        payload = RecommendationPayload(
            bike_id=result.bike_id,
            bike_name=result.bike_name,
            score=result.score,
            matching_factors=result.matching_factors,
        )
        state.last_recommendation = payload

        explanation = self._explain(result, preferences)
        return self._finish(state, explanation, payload)

    def _explain(self, result, preferences) -> str:
        prompt = prompts.build_explain_prompt(
            bike_name=result.bike_name,
            score=result.score,
            matching_factors=result.matching_factors,
            facts=result.facts,
            preferences=self._preferences_summary(preferences),
        )
        try:
            return self.provider.generate(
                prompt, system=prompts.EXPLAIN_SYSTEM_PROMPT
            ).strip()
        except AIProviderError:
            # Graceful fallback: build a grounded explanation from the facts.
            return self._fallback_explanation(result)

    def _fallback_explanation(self, result) -> str:
        reasons = [
            _FACTOR_PHRASES[f] for f in result.matching_factors if f in _FACTOR_PHRASES
        ]
        reason_text = "; ".join(reasons) if reasons else "it best matches your needs"
        return (
            f"I recommend the {result.bike_name} (match score {result.score}/100) "
            f"because {reason_text}. Key facts: {result.facts}"
        )

    # -- knowledge path (RAG) -----------------------------------------------

    def _answer_knowledge(self, query: str) -> str:
        knowledge = get_bike_knowledge(query, self.retriever)
        prompt = prompts.build_knowledge_prompt(query, knowledge.context)
        try:
            return self.provider.generate(
                prompt, system=prompts.KNOWLEDGE_SYSTEM_PROMPT
            ).strip()
        except AIProviderError:
            # Graceful fallback: return the retrieved facts directly (grounded).
            if knowledge.context:
                return (
                    "Here is what I have on that:\n" + knowledge.context
                )
            return (
                "I don't have that information in my catalog knowledge right now."
            )

    # -- helpers ------------------------------------------------------------

    def _finish(
        self,
        state: ConversationState,
        message: str,
        recommendation: RecommendationPayload | None,
    ) -> ChatTurnResult:
        state.add_message(ChatRole.assistant, message)
        return ChatTurnResult(message=message, recommendation=recommendation)

    def _format_history(self, state: ConversationState, limit: int = 6) -> str:
        # Exclude the just-added current user message (passed separately).
        prior = state.history[:-1][-limit:]
        if not prior:
            return "(no previous messages)"
        return "\n".join(f"{m.role.value}: {m.content}" for m in prior)

    def _format_known_preferences(self, state: ConversationState) -> str:
        known = state.accumulated.model_dump(exclude_none=True, mode="json")
        return json.dumps(known) if known else "(none yet)"

    def _preferences_summary(self, preferences) -> str:
        return json.dumps(preferences.model_dump(mode="json"))

    @staticmethod
    def _loads_json(raw: str) -> dict | None:
        """Best-effort parse of a JSON object from model output."""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text[:4].lower() == "json":
                text = text[4:]
            text = text.strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None
