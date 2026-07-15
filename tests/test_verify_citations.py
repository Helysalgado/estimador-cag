"""Unit tests for Session 11 citation verification and schema integrity."""

import pytest
from pydantic import ValidationError

from app.embedding_pipeline.generation.schemas import (
    Estimate,
    EstimateLineItem,
    SourceReference,
)
from app.embedding_pipeline.generation.verify import verify_citations


def _grounded_line(*, chunk_id: str = "12") -> EstimateLineItem:
    return EstimateLineItem(
        description="Stripe checkout integration",
        hours=120,
        role="backend",
        grounded=True,
        sources=[
            SourceReference(
                chunk_id=chunk_id,
                document_id="3",
                evidence="Stripe payment intents with webhook reconciliation",
            )
        ],
    )


def test_verify_citations_happy_path() -> None:
    estimate = Estimate(summary="ok", line_items=[_grounded_line(chunk_id="12")])
    report = verify_citations(estimate, ["12", "7", "9"])
    assert report.ok is True
    assert report.dangling_chunk_ids == []
    assert report.grounded_lines == 1
    assert report.ungrounded_lines == 0


def test_verify_citations_detects_dangling() -> None:
    estimate = Estimate(
        line_items=[_grounded_line(chunk_id="99999")],
    )
    report = verify_citations(estimate, ["12", "7"])
    assert report.ok is False
    assert report.dangling_chunk_ids == ["99999"]
    assert report.details is not None
    assert "99999" in report.details[0]


def test_verify_citations_counts_ungrounded() -> None:
    estimate = Estimate(
        line_items=[
            _grounded_line(chunk_id="1"),
            EstimateLineItem(
                description="Loyalty points club",
                hours=None,
                grounded=False,
                sources=[],
                assumption="Not present in retrieved chunks",
            ),
        ]
    )
    report = verify_citations(estimate, {"1"})
    assert report.ok is True
    assert report.grounded_lines == 1
    assert report.ungrounded_lines == 1


def test_schema_rejects_grounded_without_sources() -> None:
    with pytest.raises(ValidationError):
        EstimateLineItem(
            description="x",
            grounded=True,
            sources=[],
            hours=10,
        )


def test_schema_coerces_ungrounded_positive_hours() -> None:
    line = EstimateLineItem(
        description="x",
        grounded=False,
        sources=[],
        hours=40,
        assumption="guess",
    )
    assert line.hours is None
    assert line.assumption == "guess"
