"""Dataclasses for Obsidian-compatible LLM-Wiki pages and manifests."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from iau_chatbot.exceptions import WikiBuildError

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class WikiRelationship:
    """Typed edge to another Obsidian wiki page."""

    target: str
    type: str


@dataclass(frozen=True)
class WikiPage:
    """A source-backed Obsidian Markdown wiki page."""

    title: str
    slug: str
    category: str
    tags: list[str]
    summary: str
    body: str
    sources: list[str]
    relationships: list[WikiRelationship] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    provenance: dict[str, float] = field(
        default_factory=lambda: {"extracted": 1.0, "inferred": 0.0, "ambiguous": 0.0}
    )
    base_confidence: float = 0.75
    lifecycle: str = "draft"
    tier: str = "supporting"
    created: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate required page fields."""

        if not self.title.strip():
            raise WikiBuildError("wiki page title is required")
        if not SLUG_RE.match(self.slug):
            raise WikiBuildError(f"invalid wiki page slug: {self.slug}")
        if not self.category.strip():
            raise WikiBuildError("wiki page category is required")
        if not self.summary.strip():
            raise WikiBuildError("wiki page summary is required")
        if not self.body.strip():
            raise WikiBuildError("wiki page body is required")
        if not self.sources:
            raise WikiBuildError("wiki page must include at least one source")

    @property
    def vault_path(self) -> str:
        """Return the vault-relative Markdown path for this page."""

        return f"{self.category.strip('/')}/{self.slug}.md"

    @property
    def wikilink(self) -> str:
        """Return an Obsidian link to this page without the file extension."""

        return f"[[{self.category.strip('/')}/{self.slug}]]"
