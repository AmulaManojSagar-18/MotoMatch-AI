"""In-memory conversation store (Phase 3).

Deliberately simple: a process-local dict keyed by conversation_id, guarded by
a lock. This is enough to maintain multi-turn state for Phase 3. Redis / durable
sessions are explicitly out of scope and can replace this later behind the same
small interface.
"""

from __future__ import annotations

import threading
import uuid

from app.agent.schemas import ConversationState


class ConversationStore:
    def __init__(self) -> None:
        self._conversations: dict[str, ConversationState] = {}
        self._lock = threading.Lock()

    def get_or_create(self, conversation_id: str | None) -> ConversationState:
        """Return the existing conversation or start a new one.

        If `conversation_id` is None or unknown, a fresh conversation (with a
        new generated id) is created and stored.
        """
        with self._lock:
            if conversation_id and conversation_id in self._conversations:
                return self._conversations[conversation_id]

            new_id = conversation_id or uuid.uuid4().hex
            state = ConversationState(conversation_id=new_id)
            self._conversations[new_id] = state
            return state

    def reset(self) -> None:
        """Clear all conversations (used by tests)."""
        with self._lock:
            self._conversations.clear()
