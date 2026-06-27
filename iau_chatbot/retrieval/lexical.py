"""Small Persian-aware lexical retrieval fallback for Obsidian vault pages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from iau_chatbot.ingest.segments import normalize_persian_text


@dataclass(frozen=True)
class RetrievedPage:
    """A wiki page selected for a question."""

    title: str
    source_path: str
    category: str
    tags: list[str]
    aliases: list[str]
    summary: str
    body: str
    sources: list[str]
    score: float
    evidence: str = ""


def retrieve(question: str, *, wiki_dir: Path, top_k: int = 5) -> list[RetrievedPage]:
    """Return the top matching vault pages using lexical overlap."""

    query_terms = _terms(question)
    if not query_terms:
        return []

    ranked: list[RetrievedPage] = []
    for page in _read_pages(wiki_dir):
        text_terms = _terms(f"{page.title} {page.summary} {page.body}")
        overlap = query_terms & text_terms
        if not overlap:
            continue
        score = len(overlap) / len(query_terms)
        ranked.append(
            RetrievedPage(
                title=page.title,
                source_path=page.source_path,
                category=page.category,
                tags=page.tags,
                aliases=page.aliases,
                summary=page.summary,
                body=page.body,
                sources=page.sources,
                score=score,
            )
        )
    return sorted(ranked, key=lambda page: (-page.score, page.title))[:top_k]


@dataclass(frozen=True)
class _VaultPage:
    title: str
    source_path: str
    category: str
    tags: list[str]
    aliases: list[str]
    summary: str
    body: str
    sources: list[str]


def _read_pages(wiki_dir: Path) -> list[_VaultPage]:
    pages: list[_VaultPage] = []
    for path in sorted(wiki_dir.rglob("*.md")):
        if path.name in {"index.md", "log.md", "hot.md"} or any(
            part.startswith("_") for part in path.relative_to(wiki_dir).parts[:-1]
        ):
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter, body = _split_frontmatter(text)
        title = frontmatter.get("title") or path.stem
        pages.append(
            _VaultPage(
                title=title,
                source_path=path.relative_to(wiki_dir).as_posix(),
                category=frontmatter.get("category", ""),
                tags=_inline_list(frontmatter.get("tags", "")),
                aliases=_inline_list(frontmatter.get("aliases", "")),
                summary=frontmatter.get("summary", ""),
                body=body,
                sources=_inline_list(frontmatter.get("sources", "")),
            )
        )
    return pages


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    _, raw_frontmatter, body = text.split("---", 2)
    values: dict[str, str] = {}
    for line in raw_frontmatter.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values, body.strip()


def _inline_list(value: str) -> list[str]:
    if not value.startswith("[") or not value.endswith("]"):
        return []
    return [item.strip() for item in value[1:-1].split(",") if item.strip()]


def _terms(text: str) -> set[str]:
    normalized = normalize_persian_text(text).lower()
    return {
        _stem(match.group(0))
        for match in re.finditer(r"\w+", normalized)
        if len(match.group(0)) > 1
    }


def _stem(term: str) -> str:
    if term == "ترم":
        return "نیمسال"
    for suffix in ("های", "ها", "ان", "ات"):
        if len(term) > len(suffix) + 2 and term.endswith(suffix):
            return term[: -len(suffix)]
    return term
