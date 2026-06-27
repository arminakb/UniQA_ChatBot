"""Markdown rendering for Obsidian-compatible wiki pages."""

from __future__ import annotations

from datetime import UTC, datetime

from .schema import WikiPage


def render_page(page: WikiPage) -> str:
    """Render a wiki page as Markdown with YAML frontmatter."""

    lines = [
        "---",
        f"title: {page.title}",
        f"category: {page.category}",
        f"tags: {_inline_list(page.tags)}",
    ]
    if page.aliases:
        lines.append(f"aliases: {_inline_list(page.aliases)}")
    if page.relationships:
        lines.append("relationships:")
        for relationship in page.relationships:
            lines.append(f'  - target: "{relationship.target}"')
            lines.append(f"    type: {relationship.type}")
    lines.extend(
        [
            f"sources: {_inline_list(page.sources)}",
            f"summary: {page.summary}",
            "provenance:",
            f"  extracted: {page.provenance.get('extracted', 0.0):g}",
            f"  inferred: {page.provenance.get('inferred', 0.0):g}",
            f"  ambiguous: {page.provenance.get('ambiguous', 0.0):g}",
            f"base_confidence: {page.base_confidence:g}",
            f"lifecycle: {page.lifecycle}",
            f"lifecycle_changed: {_date(page.updated)}",
            f"tier: {page.tier}",
            f"created: {_timestamp(page.created)}",
            f"updated: {_timestamp(page.updated)}",
            "---",
            "",
            f"# {page.title}",
            "",
            page.body.strip(),
            "",
        ]
    )
    return "\n".join(lines)


def _inline_list(values: list[str]) -> str:
    return "[" + ", ".join(values) + "]"


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _date(value: datetime) -> str:
    return _timestamp(value).split("T", 1)[0]
