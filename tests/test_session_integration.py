"""Session 5 integration tests: memory, attachments in prompts, sliding window."""

from __future__ import annotations

import io

import pytest
from pypdf import PdfWriter

from app.config import settings
from app.services.sessions import session_store


def _create_session_id(client) -> str:
    response = client.post("/api/v1/sessions")
    assert response.status_code == 200
    return response.json()["session_id"]


def _pdf_file(name: str) -> tuple[str, tuple[str, bytes, str]]:
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(buffer)
    pdf_bytes = buffer.getvalue()
    return ("attachments", (name, pdf_bytes, "application/pdf"))


@pytest.fixture
def capture_llm_messages(monkeypatch):
    """Record LLM message lists and return deterministic assistant text."""
    captured: list[list[dict[str, str]]] = []

    def fake_generate_sync_messages(*, messages, config):  # noqa: ANN001, ARG001
        captured.append([dict(m) for m in messages])
        last_user = messages[-1]["content"]
        return {"estimation": f"Assistant reply for: {last_user[:60]}"}

    monkeypatch.setattr(
        "app.services.session_estimation.generate_sync_messages",
        fake_generate_sync_messages,
    )
    monkeypatch.setattr(
        "app.services.session_estimation.render_session_system_prompt",
        lambda **kwargs: "SYSTEM-PROMPT-STUB",
    )
    return captured


def test_multi_turn_metadata_evolves_over_two_requests(client, capture_llm_messages):
    session_id = _create_session_id(client)

    first = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={
            "transcript": (
                "We are building project called AlphaApp with React and PostgreSQL."
            ),
        },
    )
    assert first.status_code == 200
    meta1 = first.json()["project_metadata"]
    assert meta1["project_name"] == "AlphaApp"
    assert "React" in meta1["mentioned_technologies"]

    second = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={"transcript": "Revise estimate for team of 6 developers."},
    )
    assert second.status_code == 200
    body2 = second.json()
    meta2 = body2["project_metadata"]
    assert meta2["project_name"] == "AlphaApp"
    assert meta2["assumed_team_size"] == 6
    assert body2["turn_count"] == 2
    assert len(capture_llm_messages) == 2
    assert len(capture_llm_messages[1]) == 4  # system + user + assistant + user


def test_pdf_attachment_text_reaches_llm_messages(
    client,
    capture_llm_messages,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.attachments.extract_text_from_pdf",
        lambda _data: "ATTACHMENT-MARKER-XYZ",
    )
    session_id = _create_session_id(client)
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={"transcript": "Please use the attached scope document."},
        files=[_pdf_file("scope.pdf")],
    )
    assert response.status_code == 200
    assert len(capture_llm_messages) == 1
    last_user = capture_llm_messages[0][-1]["content"]
    assert "--- attachment: scope.pdf ---" in last_user
    assert "ATTACHMENT-MARKER-XYZ" in last_user
    assert "Please use the attached scope document." in last_user


def test_sliding_window_keeps_at_most_max_turns_after_eight_requests(
    client,
    capture_llm_messages,
):
    session_id = _create_session_id(client)
    max_turns = settings.SESSION_MAX_TURNS

    for index in range(8):
        response = client.post(
            f"/api/v1/sessions/{session_id}/estimate",
            data={"transcript": f"turn-{index} user message about scope"},
        )
        assert response.status_code == 200

    session = session_store.get(session_id)
    assert session is not None
    assert session.history.turn_count == max_turns
    assert session.completed_turn_count == 8

    stored_users = [
        message.content
        for message in session.history._messages  # noqa: SLF001 — integration assertion
        if message.role == "user"
    ]
    assert len(stored_users) == max_turns
    assert stored_users[0] == "turn-2 user message about scope"
    assert stored_users[-1] == "turn-7 user message about scope"
    assert "turn-0" not in stored_users
    assert "turn-1" not in stored_users

    # On the 8th request, memory still held turns 1–6 plus the in-flight turn 7.
    last_call = capture_llm_messages[-1]
    history_users = [m["content"] for m in last_call if m["role"] == "user"]
    assert len(history_users) == max_turns + 1
    assert history_users[0] == "turn-1 user message about scope"
    assert history_users[-1] == "turn-7 user message about scope"
    assert "turn-0" not in history_users
