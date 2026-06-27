"""Tests for writing Obsidian vault wiki pages."""

import json
from datetime import UTC, datetime
from pathlib import Path

from iau_chatbot.ingest.segments import RegulationSegment
from iau_chatbot.wiki.schema import WikiPage
from iau_chatbot.wiki.store import WikiStore


def test_wiki_store_writes_page_and_vault_bookkeeping(tmp_path: Path) -> None:
    page = WikiPage(
        title="سقف واحدهای نیمسال",
        slug="semester-unit-limit",
        category="references",
        tags=["academic-regulations", "units"],
        summary="حد مجاز اخذ واحد در هر نیمسال.",
        body="## Key Ideas\n\n- دانشجو باید سقف مجاز را رعایت کند.",
        sources=["raw/Karshenasi.pdf#page=1"],
        created=datetime(2026, 6, 23, 8, 0, tzinfo=UTC),
        updated=datetime(2026, 6, 23, 8, 0, tzinfo=UTC),
    )
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="انتخاب واحد",
        text="دانشجو باید سقف مجاز را رعایت کند.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    result = WikiStore(tmp_path).write_pages([page], segments=[segment], llm_calls=1)

    page_path = tmp_path / "references" / "سقف واحدهای نیمسال.md"
    assert result.pages_written == 1
    assert page_path.exists()
    assert "# سقف واحدهای نیمسال" in page_path.read_text(encoding="utf-8")

    manifest = json.loads((tmp_path / ".manifest.json").read_text(encoding="utf-8"))
    assert manifest["stats"]["total_pages"] == 1
    assert manifest["stats"]["llm_calls"] == 1
    assert manifest["sources"]["raw/Karshenasi.pdf"]["content_hash"] == "sha256:abc"
    assert manifest["sources"]["raw/Karshenasi.pdf"]["pages_created"] == [
        "references/سقف واحدهای نیمسال.md"
    ]

    assert "[[references/سقف واحدهای نیمسال]]" in (tmp_path / "index.md").read_text(
        encoding="utf-8"
    )
    assert "WIKI_BUILD" in (tmp_path / "log.md").read_text(encoding="utf-8")
    assert "سقف واحدهای نیمسال" in (tmp_path / "hot.md").read_text(encoding="utf-8")


def test_wiki_store_uses_persian_title_for_page_path(tmp_path: Path) -> None:
    page = WikiPage(
        title="سقف واحدهای نیمسال",
        slug="semester-unit-limit",
        category="references",
        tags=["academic-regulations"],
        summary="حد مجاز اخذ واحد در هر نیمسال.",
        body="متن صفحه.",
        sources=["raw/Karshenasi.pdf#page=1"],
    )
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="انتخاب واحد",
        text="دانشجو باید سقف مجاز را رعایت کند.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    WikiStore(tmp_path).write_pages([page], segments=[segment], llm_calls=1)

    assert (tmp_path / "references" / "سقف واحدهای نیمسال.md").exists()
    assert "[[references/سقف واحدهای نیمسال]]" in (tmp_path / "index.md").read_text(
        encoding="utf-8"
    )


def test_wiki_store_preserves_duplicate_slugs(tmp_path: Path) -> None:
    pages = [
        WikiPage(
            title="تبصره 1",
            slug="tbsrh-1",
            category="references",
            tags=["academic-regulations"],
            summary="صفحه اول.",
            body="## Key Ideas\n\n- صفحه اول.",
            sources=["raw/Karshenasi.pdf#page=1"],
        ),
        WikiPage(
            title="تبصره 1",
            slug="tbsrh-1",
            category="references",
            tags=["academic-regulations"],
            summary="صفحه دوم.",
            body="## Key Ideas\n\n- صفحه دوم.",
            sources=["raw/Karshenasi.pdf#page=2"],
        ),
    ]
    segments = [
        RegulationSegment(
            source_path="raw/Karshenasi.pdf",
            page_start=1,
            page_end=1,
            heading="تبصره 1",
            text="صفحه اول.",
            source_ref="raw/Karshenasi.pdf#page=1",
            content_hash="sha256:one",
        ),
        RegulationSegment(
            source_path="raw/Karshenasi.pdf",
            page_start=2,
            page_end=2,
            heading="تبصره 1",
            text="صفحه دوم.",
            source_ref="raw/Karshenasi.pdf#page=2",
            content_hash="sha256:two",
        ),
    ]

    WikiStore(tmp_path).write_pages(pages, segments=segments, llm_calls=2)

    assert (tmp_path / "references" / "تبصره 1.md").exists()
    assert (tmp_path / "references" / "تبصره 1-2.md").exists()
    index = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "[[references/تبصره 1]]" in index
    assert "[[references/تبصره 1-2]]" in index


def test_wiki_store_records_failed_segments(tmp_path: Path) -> None:
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=3,
        page_end=3,
        heading="ماده 3",
        text="متن",
        source_ref="raw/Karshenasi.pdf#page=3",
        content_hash="sha256:failed",
    )

    WikiStore(tmp_path).write_pages([], segments=[segment], failed_segments=[segment], llm_calls=1)

    manifest = json.loads((tmp_path / ".manifest.json").read_text(encoding="utf-8"))
    assert manifest["stats"]["failed_segments"] == 1
    assert manifest["failed_segments"] == [
        {
            "source_ref": "raw/Karshenasi.pdf#page=3",
            "content_hash": "sha256:failed",
            "heading": "ماده 3",
        }
    ]


def test_wiki_store_rebuild_removes_stale_pages(tmp_path: Path) -> None:
    stale = tmp_path / "references" / "old-page.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("# stale", encoding="utf-8")

    page = WikiPage(
        title="صفحه تازه",
        slug="new-page",
        category="references",
        tags=["academic-regulations"],
        summary="صفحه تازه.",
        body="متن تازه.",
        sources=["raw/Karshenasi.pdf#page=1"],
    )
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="صفحه تازه",
        text="متن تازه.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:new",
    )

    WikiStore(tmp_path).write_pages([page], segments=[segment], llm_calls=1)

    assert not stale.exists()
    assert (tmp_path / "references" / "صفحه تازه.md").exists()
