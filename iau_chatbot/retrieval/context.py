"""Context assembly for retrieved Obsidian wiki pages."""

from __future__ import annotations

from .lexical import RetrievedPage


def assemble_context(pages: list[RetrievedPage], *, max_chars: int = 4000) -> str:
    """Build source-cited context text for answer generation."""

    chunks: list[str] = []
    remaining = max_chars
    for page in pages:
        chunk = "\n".join(
            [
                f"## {page.title}",
                f"Path: {page.source_path}",
                f"Sources: {', '.join(page.sources)}",
                page.summary,
                page.evidence or page.body,
            ]
        ).strip()
        if len(chunk) > remaining:
            chunk = chunk[:remaining].rstrip()
        if chunk:
            chunks.append(chunk)
            remaining -= len(chunk)
        if remaining <= 0:
            break
    return "\n\n".join(chunks)
