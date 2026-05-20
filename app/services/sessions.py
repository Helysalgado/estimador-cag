"""In-memory conversational session state for multi-turn estimation.

Sessions live in a process-local dict: they are lost on restart and are not
shared across workers. Use a single uvicorn worker for predictable behavior
during local development.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from app.config import settings

MessageRole = Literal["user", "assistant"]


@dataclass(frozen=True)
class Message:
    """One chat message stored in session history (user or assistant only)."""

    role: MessageRole
    content: str


@dataclass
class ProjectMetadata:
    """Stable facts about the project, separate from rolling chat history."""

    project_name: str | None = None
    assumed_team_size: int | None = None
    mentioned_technologies: list[str] = field(default_factory=list)
    agreed_scope: str | None = None
    explicit_constraints: list[str] = field(default_factory=list)
    rejected_options: list[str] = field(default_factory=list)

    def has_content(self) -> bool:
        """True when at least one metadata field is populated."""
        return bool(
            self.project_name
            or self.assumed_team_size is not None
            or self.mentioned_technologies
            or self.agreed_scope
            or self.explicit_constraints
            or self.rejected_options
        )


class ConversationHistory:
    """Rolling user/assistant pairs with a sliding window over completed turns."""

    def __init__(self, *, max_turns: int | None = None) -> None:
        self._max_turns = max_turns if max_turns is not None else settings.SESSION_MAX_TURNS
        self._messages: list[Message] = []

    @property
    def turn_count(self) -> int:
        """Number of completed user/assistant pairs currently stored."""
        return len(self._messages) // 2

    def add_turn(self, user_content: str, assistant_content: str) -> None:
        """Append a completed turn and drop oldest pairs beyond the window."""
        self._messages.append(Message(role="user", content=user_content))
        self._messages.append(Message(role="assistant", content=assistant_content))
        self._trim()

    def build_messages(
        self,
        system_prompt: str,
        *,
        current_user: str | None = None,
    ) -> list[dict[str, str]]:
        """Build an OpenAI-style message list for the LLM call.

        The system prompt is always first. Completed history follows in order.
        An optional ``current_user`` appends the in-flight user turn before the
        assistant reply exists in history.
        """
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        for message in self._messages:
            messages.append({"role": message.role, "content": message.content})
        if current_user is not None:
            messages.append({"role": "user", "content": current_user})
        return messages

    def _trim(self) -> None:
        max_messages = self._max_turns * 2
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]


@dataclass
class Session:
    """One estimation conversation: metadata plus rolling history."""

    session_id: str
    history: ConversationHistory = field(default_factory=ConversationHistory)
    metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


class SessionStore:
    """Volatile, single-process registry of active sessions keyed by UUID."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self) -> str:
        """Create a new session and return its ``session_id``."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = Session(session_id=session_id)
        return session_id

    def get(self, session_id: str) -> Session | None:
        """Return the session if it exists in this process."""
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """Remove a session. Returns True if it existed."""
        return self._sessions.pop(session_id, None) is not None

    def __len__(self) -> int:
        return len(self._sessions)


session_store = SessionStore()
