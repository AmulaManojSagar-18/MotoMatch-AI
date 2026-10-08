"""API request/response schemas for the conversational endpoint (Phase 3)."""

from pydantic import BaseModel, Field

from app.agent.schemas import RecommendationPayload


class ChatRequest(BaseModel):
    # Omit on the first message; the server returns a generated id to reuse.
    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation id, or null to start a new conversation.",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="The user's message in natural language.",
    )


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    # Present only once the engine has made a recommendation this turn.
    recommendation: RecommendationPayload | None = None
