"""Tests for session turn orchestration and metadata heuristics."""

from __future__ import annotations

from app.services.session_estimation import (
    estimate_session_turn,
    update_metadata_from_turn,
)
from app.services.sessions import ConversationHistory, ProjectMetadata, Session


def test_update_metadata_extracts_technologies_and_project_name():
    metadata = ProjectMetadata()
    update_metadata_from_turn(
        metadata,
        "We are building project called InventoryHub with React and PostgreSQL. Team of 4 developers.",
        "Estimated phases for the stack.",
    )
    assert metadata.project_name == "InventoryHub"
    assert metadata.assumed_team_size == 4
    assert "React" in metadata.mentioned_technologies
    assert "PostgreSQL" in metadata.mentioned_technologies
    assert "InventoryHub" in (metadata.agreed_scope or "")


def test_update_metadata_collects_constraints_and_rejections():
    metadata = ProjectMetadata()
    update_metadata_from_turn(
        metadata,
        "We must launch before Q4. Don't want native mobile first.",
        "Web-first delivery plan.",
    )
    assert any("must launch" in c.lower() for c in metadata.explicit_constraints)
    assert metadata.rejected_options


def test_estimate_session_turn_updates_history_and_metadata(monkeypatch):
    session = Session(session_id="test-session")

    def fake_generate_sync_messages(*, messages, config):  # noqa: ANN001, ARG001
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"].startswith("Turn one about FastAPI")
        return {
            "estimation": "Turn one estimation with React noted.",
            "tokens_in": 120,
            "tokens_out": 80,
            "cost_usd": 0.0025,
            "latency_ms": 340,
        }

    monkeypatch.setattr(
        "app.services.session_estimation.generate_sync_messages",
        fake_generate_sync_messages,
    )
    monkeypatch.setattr(
        "app.services.session_estimation.render_session_system_prompt",
        lambda **kwargs: "SYSTEM",
    )

    response = estimate_session_turn(
        session,
        "Turn one about FastAPI and React. Team of 3 developers.",
        prompt_version="v1",
    )
    assert response.text == "Turn one estimation with React noted."
    assert response.prompt_version == "v1"
    assert response.turn_count == 1
    assert response.observation is not None
    assert response.observation.turn_index == 1
    assert response.observation.session_id == "test-session"
    assert response.observation.tokens_in == 120
    assert session.history.turn_count == 1
    assert "React" in session.metadata.mentioned_technologies
    assert session.metadata.assumed_team_size == 3
    assert session.last_turn_observed is not None
    assert set(session.last_turn_observed.keys()) == {
        "turn_index",
        "session_id",
        "enriched_transcript_chars",
        "attachments_total_chars",
        "messages_in_window",
        "anchors_count",
        "summary_chars",
        "tokens_in",
        "tokens_out",
        "cost_usd",
        "latency_ms",
        "cache_hit_kind",
        "last_resolved_tier",
    }


def test_second_turn_includes_prior_history_in_messages(monkeypatch):
    session = Session(session_id="multi")
    session.history.add_turn("first user", "first assistant")
    captured: list[list[dict[str, str]]] = []

    def fake_generate_sync_messages(*, messages, config):  # noqa: ANN001, ARG001
        captured.append(messages)
        return {"estimation": "second assistant"}

    monkeypatch.setattr(
        "app.services.session_estimation.generate_sync_messages",
        fake_generate_sync_messages,
    )
    monkeypatch.setattr(
        "app.services.session_estimation.render_session_system_prompt",
        lambda **kwargs: "SYSTEM",
    )

    estimate_session_turn(session, "second user question")
    assert len(captured) == 1
    roles = [m["role"] for m in captured[0]]
    assert roles == ["system", "user", "assistant", "user"]
    assert captured[0][1]["content"] == "first user"
    assert captured[0][-1]["content"] == "second user question"


def test_completed_turn_count_exceeds_sliding_window(monkeypatch):
    """Stress CSV uses turn_index = completed turns, not window size."""
    session = Session(session_id="stress-counter", history=ConversationHistory(max_turns=2))

    def fake_generate_sync_messages(*, messages, config):  # noqa: ANN001, ARG001
        return {"estimation": "ok"}

    monkeypatch.setattr(
        "app.services.session_estimation.generate_sync_messages",
        fake_generate_sync_messages,
    )
    monkeypatch.setattr(
        "app.services.session_estimation.render_session_system_prompt",
        lambda **kwargs: "SYSTEM",
    )
    monkeypatch.setattr(
        "app.services.session_estimation.extract_project_metadata_update",
        lambda **kwargs: ProjectMetadata(),
    )

    for index in range(4):
        response = estimate_session_turn(session, f"user turn {index}")
        assert response.observation is not None
        assert response.observation.turn_index == index + 1

    assert session.history.turn_count == 2
    assert session.completed_turn_count == 4
