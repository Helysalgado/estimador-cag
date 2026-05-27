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
from app.sessions.compression.policy import compress_evicted_pairs

MessageRole = Literal["user", "assistant"]


@dataclass(frozen=True)
class Message:
    """One chat message stored in session history (user or assistant only)."""

    role: MessageRole
    content: str


@dataclass
class Anchor:
    """Stable conversational fact promoted from older turns."""

    text: str
    source_turn: int
    confidence: float = 0.5


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
        configured_turns = settings.MAX_CONVERSATION_TURNS or settings.SESSION_MAX_TURNS
        self._max_turns = max_turns if max_turns is not None else configured_turns
        self._messages: list[Message] = []
        self._last_evicted_pairs: list[tuple[Message, Message]] = []

    @property
    def turn_count(self) -> int:
        """Number of completed user/assistant pairs currently stored."""
        return len(self._messages) // 2

    def add_turn(self, user_content: str, assistant_content: str) -> None:
        """Append a completed turn and drop oldest pairs beyond the window."""
        self._messages.append(Message(role="user", content=user_content))
        self._messages.append(Message(role="assistant", content=assistant_content))
        self._trim()

    def consume_evicted_pairs(self) -> list[tuple[Message, Message]]:
        """Return and clear pairs evicted by the latest trim."""
        evicted = self._last_evicted_pairs
        self._last_evicted_pairs = []
        return evicted

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
            overflow = len(self._messages) - max_messages
            evicted = self._messages[:overflow]
            self._messages = self._messages[overflow:]
            self._last_evicted_pairs.extend(
                (evicted[index], evicted[index + 1])
                for index in range(0, len(evicted), 2)
                if index + 1 < len(evicted)
            )


@dataclass
class Session:
    """One estimation conversation: metadata plus rolling history."""

    session_id: str
    history: ConversationHistory = field(default_factory=ConversationHistory)
    metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    anchors: list[Anchor] = field(default_factory=list)
    rolling_summary: str = ""
    last_resolved_tier: str = "default"
    last_tier_rule: str = "default_rule"
    last_turn_observed: dict[str, object] | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def add_turn(self, user_content: str, assistant_content: str) -> None:
        """Append a turn and run compression on evicted history."""
        self.history.add_turn(user_content, assistant_content)
        evicted_pairs = self.history.consume_evicted_pairs()
        if not evicted_pairs:
            return
        summary, new_anchors = compress_evicted_pairs(
            evicted_pairs,
            current_summary=self.rolling_summary,
            max_summary_chars=settings.MAX_SUMMARY_CHARS,
            max_anchors=settings.MAX_ANCHORS,
            current_turn=self.history.turn_count,
        )
        self.rolling_summary = summary
        self.anchors.extend(Anchor(**anchor) for anchor in new_anchors)
        if len(self.anchors) > settings.MAX_ANCHORS:
            self.anchors = self.anchors[-settings.MAX_ANCHORS :]


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
