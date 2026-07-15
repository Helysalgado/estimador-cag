"""Format retrieved chunks into a prompt block with stable string ids."""

from __future__ import annotations

from app.embedding_pipeline.retrieval.pipeline import RetrievedChunk


def assemble_context(chunks: list[RetrievedChunk]) -> str:
    """Build the context section listing each chunk with ids for attribution."""
    if not chunks:
        return (
            "No retrieved chunks were available. "
            "Produce only ungrounded lines with clear assumptions."
        )

    parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        meta = chunk.metadata or {}
        budget_id = meta.get("budget_id", "n/a")
        component_id = meta.get("component_id", "n/a")
        parts.append(
            "\n".join(
                [
                    f"### Chunk {index}",
                    f"chunk_id: {chunk.chunk_id}",
                    f"document_id: {chunk.document_id}",
                    f"budget_id: {budget_id}",
                    f"component_id: {component_id}",
                    "content:",
                    chunk.content.strip(),
                ]
            )
        )
    return "\n\n".join(parts)


def chunk_ids_as_strings(chunks: list[RetrievedChunk]) -> list[str]:
    return [str(chunk.chunk_id) for chunk in chunks]
