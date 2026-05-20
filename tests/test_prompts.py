"""Tests for the Jinja2 prompt loader."""

from __future__ import annotations

import pytest
from jinja2 import Environment, StrictUndefined, UndefinedError

from app.prompts.loader import render_estimation_prompt, render_session_system_prompt
from app.services.sessions import ProjectMetadata
from structlog.testing import capture_logs

from app.schemas.estimation import (
    DetailLevel,
    EstimationRequest,
    OutputFormat,
    ProjectType,
    ReferenceProject,
)


def _make_request(**overrides) -> EstimationRequest:
    base = {
        "description": "A small CRM for a real estate agency: contacts, deals, role-based access.",
        "project_type": ProjectType.WEB_SAAS,
        "detail_level": DetailLevel.MEDIUM,
        "output_format": OutputFormat.PHASES_TABLE,
    }
    base.update(overrides)
    return EstimationRequest(**base)


def test_user_prompt_wraps_description_in_project_description_block() -> None:
    request = _make_request(description="UNIQUE-MARKER-12345 build a tiny scheduling app.")
    _system, user = render_estimation_prompt(request)
    assert "<project_description>" in user
    assert "UNIQUE-MARKER-12345 build a tiny scheduling app." in user
    assert "</project_description>" in user
    start = user.index("<project_description>")
    end = user.index("</project_description>")
    assert "UNIQUE-MARKER-12345" in user[start:end]


def test_phases_table_keyword_appears_only_when_format_requested() -> None:
    table_request = _make_request(output_format=OutputFormat.PHASES_TABLE)
    narrative_request = _make_request(output_format=OutputFormat.NARRATIVE)

    table_system, _ = render_estimation_prompt(table_request)
    narrative_system, _ = render_estimation_prompt(narrative_request)

    assert "phases_table" in table_system
    assert "phases_table" not in narrative_system


def test_detailed_includes_assumptions_per_phase_summary_does_not() -> None:
    detailed_request = _make_request(detail_level=DetailLevel.DETAILED)
    summary_request = _make_request(detail_level=DetailLevel.SUMMARY)

    detailed_system, _ = render_estimation_prompt(detailed_request)
    summary_system, _ = render_estimation_prompt(summary_request)

    assert "list assumptions per phase" in detailed_system.lower()
    assert "list assumptions per phase" not in summary_system.lower()


def test_examples_block_is_included_in_system_prompt() -> None:
    request = _make_request()
    system, _ = render_estimation_prompt(request)
    assert "<examples>" in system
    assert "</examples>" in system


def test_strict_undefined_raises_on_missing_variable() -> None:
    env = Environment(undefined=StrictUndefined)
    template = env.from_string("Hello {{ unknown_variable }}")
    with pytest.raises(UndefinedError):
        template.render()


def test_unknown_version_raises() -> None:
    request = _make_request()
    with pytest.raises(Exception):
        render_estimation_prompt(request, version="v999")


def test_v2_system_differs_from_v1() -> None:
    request = _make_request()
    v1_system, _ = render_estimation_prompt(request, version="v1")
    v2_system, _ = render_estimation_prompt(request, version="v2")
    assert "BONUS_V2_PROFILE" in v2_system
    assert "BONUS_V2_PROFILE" not in v1_system
    assert "V2_CALIBRATION_SET" in v2_system
    assert "V2_CALIBRATION_SET" not in v1_system


def test_reference_projects_rendered_when_present() -> None:
    refs = [
        ReferenceProject(
            name="RefCRM-UniqueMarker",
            description="Internal CRM for pipeline tracking and approvals.",
            estimated_weeks=14,
        )
    ]
    request = _make_request(reference_projects=refs)
    system, _ = render_estimation_prompt(request)
    assert "<reference_projects>" in system
    assert "RefCRM-UniqueMarker" in system
    assert "14" in system


def test_reference_projects_block_absent_when_none() -> None:
    request = _make_request()
    system, _ = render_estimation_prompt(request)
    assert "<reference_projects>" not in system


def test_project_metadata_block_absent_when_empty() -> None:
    request = _make_request()
    empty = ProjectMetadata()
    assert not empty.has_content()

    system, _ = render_estimation_prompt(request, project_metadata=empty)
    assert "<project_metadata>" not in system


def test_project_metadata_block_present_when_populated() -> None:
    request = _make_request()
    metadata = ProjectMetadata(
        project_name="InventoryHub-Unique",
        assumed_team_size=4,
        mentioned_technologies=["React", "PostgreSQL"],
        agreed_scope="MVP for warehouse stock tracking",
        explicit_constraints=["Must launch before Q4"],
        rejected_options=["Native mobile first"],
    )
    system, _ = render_estimation_prompt(request, project_metadata=metadata)
    assert "<project_metadata>" in system
    assert "InventoryHub-Unique" in system
    assert "React, PostgreSQL" in system
    assert "Must launch before Q4" in system
    assert "Native mobile first" in system
    assert "stable facts" in system.lower()


def test_project_metadata_in_v1_and_v2_system() -> None:
    metadata = ProjectMetadata(project_name="CrossVersionMarker")
    request = _make_request()
    v1_system, _ = render_estimation_prompt(request, version="v1", project_metadata=metadata)
    v2_system, _ = render_estimation_prompt(request, version="v2", project_metadata=metadata)
    assert "CrossVersionMarker" in v1_system
    assert "CrossVersionMarker" in v2_system


def test_render_session_system_prompt_includes_metadata() -> None:
    metadata = ProjectMetadata(agreed_scope="Session-only scope marker")
    system = render_session_system_prompt(project_metadata=metadata, version="v1")
    assert "<project_metadata>" in system
    assert "Session-only scope marker" in system


def test_structlog_prompt_rendered_event() -> None:
    with capture_logs() as cap:
        render_estimation_prompt(_make_request())
    events = [log.get("event") for log in cap]
    assert "prompt_rendered" in events
    entry = next(log for log in cap if log.get("event") == "prompt_rendered")
    assert entry.get("prompt_template_version") == "v1"
    assert len(entry.get("content_sha256", "")) == 64
