"""Conversational endpoint (Phase 3).

POST /chat: one user message in, the agent's reply (and a recommendation when
one has been made) out. Conversation state is kept server-side keyed by
`conversation_id`.

The route only orchestrates: load state, call the agent, map the result and
errors to HTTP. All intelligence lives in the agent, engine, and RAG layers.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.agent.agent import ConversationAgent
from app.agent.store import ConversationStore
from app.ai.base import AIProviderError
from app.api.deps import get_conversation_agent, get_conversation_store
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, summary="Chat with MotoMatch")
def chat(
    payload: ChatRequest,
    agent: ConversationAgent = Depends(get_conversation_agent),
    store: ConversationStore = Depends(get_conversation_store),
) -> ChatResponse:
    state = store.get_or_create(payload.conversation_id)

    try:
        result = agent.handle_turn(state, payload.message)
    except AIProviderError as exc:
        # Ollama (or the configured provider) is unavailable: fail clearly
        # rather than crashing or fabricating a reply.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The AI provider is unavailable: {exc}",
        ) from exc

    return ChatResponse(
        conversation_id=state.conversation_id,
        message=result.message,
        recommendation=result.recommendation,
    )
