"""Unit tests for PDF/DOCX attachment extraction."""

from __future__ import annotations

import asyncio
import io

import pytest
from docx import Document

from app.services.attachments import (
    AttachmentError,
    build_user_turn,
    detect_attachment_kind,
    extract_text_from_docx,
    format_attachment_block,
    process_attachments,
)
def _docx_bytes(*paragraphs: str) -> bytes:
    buffer = io.BytesIO()
    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)
    document.save(buffer)
    return buffer.getvalue()


def test_detect_attachment_kind_by_extension():
    assert detect_attachment_kind("spec.pdf", None) == "pdf"
    assert detect_attachment_kind("notes.docx", None) == "docx"


def test_detect_attachment_kind_rejects_unknown():
    with pytest.raises(AttachmentError) as exc_info:
        detect_attachment_kind("malware.exe", "application/octet-stream")
    assert exc_info.value.error == "unsupported_file_type"


def test_extract_text_from_docx():
    data = _docx_bytes("Inventory mobile app", "Phase one scope")
    text = extract_text_from_docx(data)
    assert "Inventory mobile app" in text
    assert "Phase one scope" in text


def test_format_attachment_block():
    block = format_attachment_block("brief.docx", "Line one")
    assert block == "--- attachment: brief.docx ---\nLine one"


def test_build_user_turn_joins_transcript_and_attachments():
    joined = build_user_turn(
        "Estimate a SaaS MVP",
        "--- attachment: brief.pdf ---\nScope details",
    )
    assert joined.startswith("Estimate a SaaS MVP")
    assert "--- attachment: brief.pdf ---" in joined


def test_process_attachments_docx():
    class FakeUpload:
        def __init__(self, filename: str, data: bytes, content_type: str) -> None:
            self.filename = filename
            self.content_type = content_type
            self._data = data

        async def read(self) -> bytes:
            return self._data

    uploads = [
        FakeUpload(
            "scope.docx",
            _docx_bytes("SCOPE-ALPHA-123"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    ]
    text = asyncio.run(
        process_attachments(uploads, max_bytes=1_000_000, max_count=5),
    )
    assert "--- attachment: scope.docx ---" in text
    assert "SCOPE-ALPHA-123" in text


def test_process_attachments_rejects_too_many():
    class TinyUpload:
        filename = "a.pdf"
        content_type = "application/pdf"

        async def read(self) -> bytes:
            return b"%PDF-1.4 minimal"

    uploads = [TinyUpload() for _ in range(3)]
    with pytest.raises(AttachmentError) as exc_info:
        asyncio.run(process_attachments(uploads, max_count=2))
    assert exc_info.value.error == "too_many_attachments"
