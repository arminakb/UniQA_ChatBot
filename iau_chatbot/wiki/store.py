"""Persistence for Obsidian vault wiki pages and root bookkeeping files."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from iau_chatbot.ingest.segments import RegulationSegment

from .markdown import render_page
from .schema import WikiPage

PagePathMap = dict[int, str]


@dataclass(frozen=True)
class WikiWriteResult:
    """Summary of a vault write operation."""

    pages_written: int
    manifest_path: Path


class WikiStore:
    """Write LLM-Wiki pages into an Obsidian-compatible vault."""

    def __init__(self, vault_dir: Path) -> None:
        self.vault_dir = vault_dir

    def write_pages(
        self,
        pages: list[WikiPage],
        *,
        segments: list[RegulationSegment],
        failed_segments: list[RegulationSegment] | None = None,
        llm_calls: int,
    ) -> WikiWriteResult:
        """Write pages and rebuild vault bookkeeping files."""

        failed_segments = failed_segments or []
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        page_paths = _unique_page_paths(pages)
        self._remove_stale_pages()
        for page in pages:
            page_path = self.vault_dir / page_paths[id(page)]
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(render_page(page), encoding="utf-8")

        now = _timestamp(datetime.now(UTC))
        self._write_manifest(pages, page_paths, segments, failed_segments, llm_calls, now)
        self._write_index(pages, page_paths, now)
        self._write_log(pages, segments, failed_segments, llm_calls, now)
        self._write_hot(pages, page_paths, now)
        return WikiWriteResult(len(pages), self.vault_dir / ".manifest.json")

    def _write_manifest(
        self,
        pages: list[WikiPage],
        page_paths: PagePathMap,
        segments: list[RegulationSegment],
        failed_segments: list[RegulationSegment],
        llm_calls: int,
        now: str,
    ) -> None:
        page_paths_by_source: dict[str, list[str]] = {}
        for page in pages:
            for source in page.sources:
                source_path = source.split("#", 1)[0]
                page_paths_by_source.setdefault(source_path, []).append(page_paths[id(page)])

        manifest = {
            "version": 1,
            "graph_type": "iau_academic_regulations",
            "last_updated": now,
            "sources": {},
            "stats": {
                "total_sources_ingested": len({segment.source_path for segment in segments}),
                "total_pages": len(pages),
                "failed_segments": len(failed_segments),
                "llm_calls": llm_calls,
            },
            "failed_segments": [
                {
                    "source_ref": segment.source_ref,
                    "content_hash": segment.content_hash,
                    "heading": segment.heading,
                }
                for segment in failed_segments
            ],
        }
        for segment in segments:
            entry = manifest["sources"].setdefault(
                segment.source_path,
                {
                    "source_type": "pdf",
                    "content_hash": segment.content_hash,
                    "ingested_at": now,
                    "pages_created": [],
                    "pages_updated": [],
                },
            )
            entry["pages_created"] = sorted(set(page_paths_by_source.get(segment.source_path, [])))

        (self.vault_dir / ".manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _write_index(self, pages: list[WikiPage], page_paths: PagePathMap, now: str) -> None:
        lines = [
            "---",
            "title: IAU Academic Regulations Index",
            "node_type: index",
            f"updated: {now}",
            "---",
            "",
            "# Wiki Index",
            "",
        ]
        by_category: dict[str, list[WikiPage]] = {}
        for page in sorted(pages, key=lambda item: (item.category, item.slug)):
            by_category.setdefault(page.category, []).append(page)
        for category, category_pages in by_category.items():
            lines.append(f"## {category.title()}")
            for page in category_pages:
                tags = " ".join(f"#{tag}" for tag in page.tags)
                lines.append(f"- {_wikilink(page_paths[id(page)])} — {page.summary} ( {tags})")
            lines.append("")
        (self.vault_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")

    def _write_log(
        self,
        pages: list[WikiPage],
        segments: list[RegulationSegment],
        failed_segments: list[RegulationSegment],
        llm_calls: int,
        now: str,
    ) -> None:
        lines = [
            "---",
            "title: IAU Academic Regulations Log",
            "node_type: log",
            f"updated: {now}",
            "---",
            "",
            "# Wiki Log",
            "",
            f"- [{now}] WIKI_BUILD sources={len({s.source_path for s in segments})} "
            f"segments={len(segments)} pages_created={len(pages)} "
            f"failed_segments={len(failed_segments)} llm_calls={llm_calls}",
            "",
        ]
        (self.vault_dir / "log.md").write_text("\n".join(lines), encoding="utf-8")

    def _write_hot(self, pages: list[WikiPage], page_paths: PagePathMap, now: str) -> None:
        lines = [
            "---",
            "title: Hot Cache",
            "node_type: hot_cache",
            f"updated: {now}",
            "---",
            "",
            "# Hot Cache",
            "",
            "## Recent Pages",
        ]
        for page in pages[:10]:
            lines.append(f"- {_wikilink(page_paths[id(page)])} — {page.title}")
        lines.append("")
        (self.vault_dir / "hot.md").write_text("\n".join(lines), encoding="utf-8")

    def _remove_stale_pages(self) -> None:
        for path in self.vault_dir.rglob("*.md"):
            if path.name not in {"index.md", "log.md", "hot.md"}:
                path.unlink()


def _unique_page_paths(pages: list[WikiPage]) -> PagePathMap:
    seen: dict[str, int] = {}
    paths: PagePathMap = {}
    for page in pages:
        title = _safe_filename(page.title) or page.slug
        base = f"{page.category.strip('/')}/{title}"
        count = seen.get(base, 0) + 1
        seen[base] = count
        suffix = "" if count == 1 else f"-{count}"
        paths[id(page)] = f"{base}{suffix}.md"
    return paths


def _safe_filename(value: str) -> str:
    return re.sub(r"[\\/:*?\"<>|]+", " ", value).strip()


def _wikilink(vault_path: str) -> str:
    return f"[[{vault_path.removesuffix('.md')}]]"


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
