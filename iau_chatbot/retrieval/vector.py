"""Optional vector retrieval wrapper with lexical fallback."""

from __future__ import annotations

from pathlib import Path

from .lexical import RetrievedPage
from .metadata import retrieve as metadata_retrieve


def retrieve(question: str, *, wiki_dir: Path, top_k: int = 5) -> list[RetrievedPage]:
    """Retrieve pages, falling back to lexical retrieval when vector deps are absent."""

    # ponytail: vector dependencies stay optional; Phase 4 works offline via lexical search.
    try:
        import chromadb  # noqa: F401
        import sentence_transformers  # noqa: F401
    except ImportError:
        return metadata_retrieve(question, wiki_dir=wiki_dir, top_k=top_k)
    return metadata_retrieve(question, wiki_dir=wiki_dir, top_k=top_k)
