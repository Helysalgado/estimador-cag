"""Logfire setup and a local span recorder for offline GRAPH_TRACE.md."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

import logfire

from app.config import settings

_span_log: ContextVar[list[str] | None] = ContextVar("graph_span_log", default=None)


def configure_logfire() -> None:
    """Configure Logfire once at process start (local-only if no token)."""
    token = (settings.LOGFIRE_TOKEN or "").strip()
    if token:
        logfire.configure(token=token, service_name="estimador-cag")
    else:
        logfire.configure(send_to_logfire=False, service_name="estimador-cag")


def begin_span_recording() -> list[str]:
    spans: list[str] = []
    _span_log.set(spans)
    return spans


def get_recorded_spans() -> list[str]:
    return list(_span_log.get() or [])


@contextmanager
def node_span(name: str) -> Iterator[None]:
    """Wrap a node body: Logfire span + local recorder for the delivery file."""
    spans = _span_log.get()
    if spans is not None:
        spans.append(name)
    with logfire.span(f"node: {name}"):
        yield
