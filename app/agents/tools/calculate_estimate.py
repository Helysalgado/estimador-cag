"""Deterministic effort calculation from historical reference hours (Session 12)."""

from __future__ import annotations

from statistics import median
from typing import Any


def calculate_estimate(components: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute per-component and total hours from reference amounts.

    For each component, ``estimated_hours`` is the median of ``reference_amounts``.
    Empty reference lists yield ``estimated_hours=null`` and note ``insufficient_refs``.
    """
    if not components:
        return {
            "components": [],
            "total_hours": 0.0,
            "method": "median_of_reference_amounts",
        }

    breakdown: list[dict[str, Any]] = []
    total = 0.0
    for raw in components:
        name = str(raw.get("name") or "").strip() or "unnamed"
        refs = [float(x) for x in (raw.get("reference_amounts") or []) if x is not None]
        if not refs:
            breakdown.append(
                {
                    "name": name,
                    "estimated_hours": None,
                    "method": "insufficient_refs",
                    "reference_count": 0,
                }
            )
            continue
        hours = float(median(refs))
        total += hours
        breakdown.append(
            {
                "name": name,
                "estimated_hours": round(hours, 2),
                "method": "median",
                "reference_count": len(refs),
            }
        )

    return {
        "components": breakdown,
        "total_hours": round(total, 2),
        "method": "median_of_reference_amounts",
    }
