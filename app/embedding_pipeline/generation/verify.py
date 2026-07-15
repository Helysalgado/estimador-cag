"""Post-generation citation verification against retrieved chunk ids."""

from __future__ import annotations

from app.embedding_pipeline.generation.schemas import CitationReport, Estimate


def verify_citations(
    estimate: Estimate,
    retrieved_chunk_ids: list[str] | set[str],
) -> CitationReport:
    """Return whether every cited chunk_id was present in the retrieval set."""
    allowed = {str(chunk_id) for chunk_id in retrieved_chunk_ids}
    dangling: list[str] = []
    details: list[str] = []
    grounded_lines = 0
    ungrounded_lines = 0

    for index, line in enumerate(estimate.line_items):
        if line.grounded:
            grounded_lines += 1
            for source in line.sources:
                cid = str(source.chunk_id)
                if cid not in allowed:
                    dangling.append(cid)
                    details.append(
                        f"line[{index}] cites unknown chunk_id={cid!r} "
                        f"for description={line.description!r}"
                    )
        else:
            ungrounded_lines += 1

    # Preserve order while unique
    seen: set[str] = set()
    unique_dangling: list[str] = []
    for cid in dangling:
        if cid not in seen:
            seen.add(cid)
            unique_dangling.append(cid)

    return CitationReport(
        ok=len(unique_dangling) == 0,
        dangling_chunk_ids=unique_dangling,
        grounded_lines=grounded_lines,
        ungrounded_lines=ungrounded_lines,
        details=details or None,
    )
