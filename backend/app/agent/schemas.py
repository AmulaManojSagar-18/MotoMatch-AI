"""Structured data for the conversational agent (Phase 3).

Everything the LLM produces is validated into these Pydantic models before the
application acts on it, so we never branch on free-form text.

Note on fields: `PreferenceUpdate` mirrors the Phase 2 `UserPreferences` fields,
but every field is Optional. `None` means "the user did not mention this on this
turn", which lets us accumulate preferences across turns without overwriting
known values with defaults. ("highway" riding maps onto `touring_usage`, exactly
as in Phase 2 -- we keep a single touring field for consistency.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.recommendation.schemas import Priority, UserPreferences


class TurnIntent(str, Enum):
    recommend = "recommend"   # user wants / is working toward a recommendation
    knowledge = "knowledge"   # user asks a factual question about a bike
    chitchat = "chitchat"     # greeting / unclear / small talk


class PreferenceUpdate(BaseModel):
    """Preferences mentioned on a single turn (None = not mentioned)."""

    model_config = ConfigDict(extra="ignore")

    budget: int | None = Field(default=None, ge=0)
    daily_commute_km: int | None = Field(default=None, ge=0)
    city_usage: Priority | None = None
    touring_usage: Priority | None = None
    adventure_usage: Priority | None = None
    comfort_priority: Priority | None = None
    mileage_priority: Priority | None = None
    performance_priority: Priority | None = None


class TurnAnalysis(BaseModel):
    """The LLM's structured understanding of one user message."""

    model_config = ConfigDict(extra="ignore")

    intent: TurnIntent = TurnIntent.chitchat
    # True when the user asks about a bike brand/model NOT in our 10-bike catalog.
    out_of_catalog_request: bool = False
    requested_bike_name: str | None = None
    # A factual question to answer via RAG (e.g. "engine cc of the Hunter 350").
    knowledge_query: str | None = None
    preferences: PreferenceUpdate = Field(default_factory=PreferenceUpdate)


class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str


class RecommendationPayload(BaseModel):
    """What the API returns when a recommendation has been made."""

    model_config = ConfigDict(protected_namespaces=())

    bike_id: int
    bike_name: str
    score: float
    matching_factors: list[str] = []


@dataclass
class ConversationState:
    """Server-side memory for one conversation (kept simple, in-memory)."""

    conversation_id: str
    accumulated: PreferenceUpdate = field(default_factory=PreferenceUpdate)
    history: list[ChatMessage] = field(default_factory=list)
    questions_asked: int = 0
    last_recommendation: RecommendationPayload | None = None

    def add_message(self, role: ChatRole, content: str) -> None:
        self.history.append(ChatMessage(role=role, content=content))

    def merge_preferences(self, update: PreferenceUpdate) -> None:
        """Overlay newly mentioned preferences without losing prior ones."""
        new_values = update.model_dump(exclude_none=True)
        if not new_values:
            return
        current = self.accumulated.model_dump()
        current.update(new_values)
        self.accumulated = PreferenceUpdate(**current)

    def to_user_preferences(self) -> UserPreferences:
        """Convert accumulated (partial) prefs into the engine's schema.

        Unmentioned fields fall back to the Phase 2 UserPreferences defaults.
        """
        explicit = self.accumulated.model_dump(exclude_none=True)
        return UserPreferences(**explicit)

    @property
    def budget_known(self) -> bool:
        return self.accumulated.budget is not None

    @property
    def usage_known(self) -> bool:
        return any(
            [
                self.accumulated.city_usage,
                self.accumulated.touring_usage,
                self.accumulated.adventure_usage,
            ]
        )
