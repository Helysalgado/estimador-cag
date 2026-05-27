"""Local text extraction from PDF/DOCX uploads (Camino B, no vision API)."""

from __future__ import annotations

import io
from typing import Literal

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader

from app.config import settings

AttachmentKind = Literal["pdf", "docx"]

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx"})
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)


class AttachmentError(Exception):
    """Raised when an upload fails validation or text extraction."""

    def __init__(self, message: str, *, error: str = "invalid_attachment") -> None:
        self.message = message
        self.error = error
        super().__init__(message)


def detect_attachment_kind(
    filename: str,
    content_type: str | None,
) -> AttachmentKind:
    """Resolve file kind from extension, with MIME as a secondary hint."""
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        return "pdf"
    if lower_name.endswith(".docx"):
        return "docx"
    if content_type in ALLOWED_CONTENT_TYPES:
        if "pdf" in content_type:
            return "pdf"
        return "docx"
    raise AttachmentError(
        f"Unsupported file type for {filename!r}. Allowed: PDF, DOCX.",
        error="unsupported_file_type",
    )


def extract_text_from_pdf(data: bytes) -> str:
    """Extract plain text from PDF bytes using pypdf."""
    try:
        reader = PdfReader(io.BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                parts.append(page_text.strip())
        return "\n".join(parts).strip()
    except Exception as exc:  # noqa: BLE001 — surface as client-facing 400
        raise AttachmentError(
            f"Could not read PDF: {exc}",
            error="pdf_extraction_failed",
        ) from exc


def extract_text_from_docx(data: bytes) -> str:
    """Extract plain text from DOCX bytes using python-docx."""
    try:
        document = Document(io.BytesIO(data))
        parts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(parts).strip()
    except Exception as exc:  # noqa: BLE001
        raise AttachmentError(
            f"Could not read DOCX: {exc}",
            error="docx_extraction_failed",
        ) from exc


def format_attachment_block(filename: str, text: str) -> str:
    """Wrap extracted text with stable delimiters for the LLM prompt."""
    body = text.strip() if text else "(no extractable text)"
    return f"--- attachment: {filename} ---\n{body}"


def truncate_attachment_text(text: str, *, max_chars: int | None = None) -> str:
    """Clamp extracted text to configured char budget."""
    max_chars = max_chars if max_chars is not None else settings.MAX_ATTACHMENT_CHARS
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def build_user_turn(transcript: str, attachments_text: str) -> str:
    """Combine the user transcript with optional attachment blocks."""
    transcript = transcript.strip()
    attachments_text = attachments_text.strip()
    if transcript and attachments_text:
        return f"{transcript}\n\n{attachments_text}"
    return transcript or attachments_text


async def process_attachments(
    uploads: list[UploadFile],
    *,
    max_bytes: int | None = None,
    max_count: int | None = None,
) -> str:
    """Read uploads, validate limits, extract text, and join attachment blocks."""
    max_bytes = max_bytes if max_bytes is not None else settings.MAX_ATTACHMENT_BYTES
    max_count = max_count if max_count is not None else settings.MAX_ATTACHMENTS_PER_REQUEST

    if len(uploads) > max_count:
        raise AttachmentError(
            f"At most {max_count} attachments per request.",
            error="too_many_attachments",
        )

    blocks: list[str] = []
    for upload in uploads:
        filename = (upload.filename or "").strip()
        if not filename:
            raise AttachmentError("Each attachment must have a filename.")

        data = await upload.read()
        if len(data) > max_bytes:
            raise AttachmentError(
                f"File {filename!r} exceeds {max_bytes} bytes.",
                error="attachment_too_large",
            )
        if not data:
            raise AttachmentError(
                f"File {filename!r} is empty.",
                error="empty_attachment",
            )

        kind = detect_attachment_kind(filename, upload.content_type)
        if kind == "pdf":
            text = extract_text_from_pdf(data)
        else:
            text = extract_text_from_docx(data)
        blocks.append(format_attachment_block(filename, truncate_attachment_text(text)))

    return "\n\n".join(blocks)
