"""Tests for session API endpoints."""

from __future__ import annotations

import io
import uuid

import pytest
from docx import Document

from app.schemas.sessions import ProjectMetadataView, SessionEstimationResponse
from app.services.sessions import session_store


def _create_session_id(client) -> str:
    response = client.post("/api/v1/sessions")
    assert response.status_code == 200
    return response.json()["session_id"]


def _docx_file(name: str, *paragraphs: str) -> tuple[str, tuple[str, bytes, str]]:
    buffer = io.BytesIO()
    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)
    document.save(buffer)
    content_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return ("attachments", (name, buffer.getvalue(), content_type))


@pytest.fixture
def fake_session_estimate(monkeypatch):
    calls: list[dict] = []

    def fake(session, user_turn, *, prompt_version="v1", config=None, **kwargs):  # noqa: ANN001, ARG001
        calls.append(
            {
                "session_id": session.session_id,
                "user_turn": user_turn,
                "prompt_version": prompt_version,
            },
        )
        session.history.add_turn(user_turn, f"Estimation for {user_turn[:20]}")
        session.metadata.project_name = session.metadata.project_name or "StubProject"
        return SessionEstimationResponse(
            text=f"Estimation for {user_turn[:30]}",
            prompt_version=prompt_version,
            turn_count=session.history.turn_count,
            tier="default",
            tier_rule="default_rule",
            project_metadata=ProjectMetadataView.model_validate(session.metadata),
        )

    monkeypatch.setattr(
        "app.routers.sessions.estimate_session_turn",
        fake,
    )
    return calls


def test_create_session_returns_valid_uuid(client):
    session_id = _create_session_id(client)
    uuid.UUID(session_id)
    assert session_store.get(session_id) is not None


def test_session_estimate_returns_estimation_response(client, fake_session_estimate):
    session_id = _create_session_id(client)
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={"transcript": "We need a B2B SaaS for equipment loans."},
    )
    assert response.status_code == 200
    body = response.json()
    assert "text" in body
    assert body["prompt_version"] == "v1"
    assert body["turn_count"] >= 1
    assert body["tier"] == "default"
    assert body["tier_rule"] == "default_rule"
    assert "project_metadata" in body
    assert "equipment loans" in body["text"] or "Estimation" in body["text"]
    assert len(fake_session_estimate) == 1
    assert "equipment loans" in fake_session_estimate[0]["user_turn"]


def test_session_estimate_multipart_with_docx(client, fake_session_estimate):
    session_id = _create_session_id(client)
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={"transcript": "Please review the attached scope."},
        files=[_docx_file("scope.docx", "SCOPE-ALPHA-123", "Extra detail")],
    )
    assert response.status_code == 200
    user_turn = fake_session_estimate[0]["user_turn"]
    assert "SCOPE-ALPHA-123" in user_turn
    assert "--- attachment: scope.docx ---" in user_turn


def test_session_estimate_unknown_session_returns_404(client):
    response = client.post(
        "/api/v1/sessions/00000000-0000-0000-0000-000000000099/estimate",
        data={"transcript": "Hello"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "session_not_found"


def test_session_estimate_unsupported_attachment_returns_400(client):
    session_id = _create_session_id(client)
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={"transcript": "Bad file"},
        files=[("attachments", ("virus.exe", b"MZ", "application/octet-stream"))],
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "unsupported_file_type"


def test_session_estimate_empty_transcript_returns_422(client):
    session_id = _create_session_id(client)
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={"transcript": ""},
    )
    assert response.status_code == 422


def test_session_estimate_invalid_prompt_version_returns_422(client):
    session_id = _create_session_id(client)
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate?prompt_version=v99",
        data={"transcript": "Hello"},
    )
    assert response.status_code == 422


def test_get_session_debug_returns_counts(client, fake_session_estimate):
    session_id = _create_session_id(client)
    client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={"transcript": "A turn with must-have login security."},
    )
    response = client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["message_count"] >= 2
    assert "anchors_count" in body
    assert "summary_chars" in body
    assert "last_resolved_tier" in body
    assert "last_tier_rule" in body


def test_estimate_acb_route_available(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.ENABLE_ACB", True)
    monkeypatch.setattr(
        "app.routers.sessions.estimate_session_turn_acb",
        lambda session, user_turn, **kwargs: {
            "text": "acb response",
            "prompt_version": "v1",
            "turn_count": 1,
            "tier": "default",
            "tier_rule": "default_rule",
            "project_metadata": {
                "project_name": None,
                "assumed_team_size": None,
                "mentioned_technologies": [],
                "agreed_scope": None,
                "explicit_constraints": [],
                "rejected_options": [],
            },
            "trace": [],
        },
    )
    session_id = _create_session_id(client)
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate-acb",
        data={"transcript": "Estimate project called Alpha with discovery and totals."},
    )
    assert response.status_code == 200
    body = response.json()
    assert "trace" in body
