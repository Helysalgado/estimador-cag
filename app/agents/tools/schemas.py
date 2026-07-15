"""OpenAI Responses API tool definitions (flat schema, strict)."""

from __future__ import annotations

from typing import Any

AGENT_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "search_budgets",
        "description": (
            "Search historical project budgets for items comparable to a single "
            "software component. Call this once per component; do not combine "
            "unrelated components (for example, an ERP integration and a data "
            "migration) into one query."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A focused description of one component to price.",
                },
                "component_type": {
                    "type": "string",
                    "enum": [
                        "integration",
                        "migration",
                        "frontend",
                        "backend",
                        "mobile",
                        "other",
                    ],
                    "description": "Category of the component, used to focus retrieval.",
                },
            },
            "required": ["query", "component_type"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "calculate_estimate",
        "description": (
            "Deterministically compute effort hours from historical reference amounts. "
            "Call after you have collected reference_amounts (estimated_hours) from "
            "search_budgets for each component. Pass one entry per component."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "components": {
                    "type": "array",
                    "description": "Components with historical reference hour amounts.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Component name from the transcript.",
                            },
                            "reference_amounts": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": (
                                    "Historical estimated_hours values from search_budgets."
                                ),
                            },
                        },
                        "required": ["name", "reference_amounts"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["components"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]
