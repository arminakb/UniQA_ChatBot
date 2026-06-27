"""Tests for Phase 3 wiki page schema and Markdown rendering."""

from datetime import UTC, datetime

import pytest

from iau_chatbot.exceptions import WikiBuildError
from iau_chatbot.wiki.markdown import render_page
from iau_chatbot.wiki.schema import WikiPage, WikiRelationship


def test_wiki_page_requires_source() -> None:
    with pytest.raises(WikiBuildError, match="source"):
        WikiPage(
            title="سقف واحدهای نیمسال",
            slug="semester-unit-limit",
            category="references",
            tags=["academic-regulations"],
            summary="حد مجاز اخذ واحد در هر نیمسال.",
            body="متن صفحه",
            sources=[],
        )


def test_render_page_writes_reference_frontmatter() -> None:
    page = WikiPage(
        title="سقف واحدهای نیمسال",
        slug="semester-unit-limit",
        category="references",
        tags=["academic-regulations", "units"],
        summary="حد مجاز اخذ واحد در هر نیمسال.",
        body="## Key Ideas\n\n- دانشجو باید سقف مجاز را رعایت کند.",
        sources=["raw/Karshenasi.pdf#page=1"],
        relationships=[
            WikiRelationship(target="[[references/academic-probation]]", type="related_to")
        ],
        created=datetime(2026, 6, 23, 8, 0, tzinfo=UTC),
        updated=datetime(2026, 6, 23, 8, 0, tzinfo=UTC),
    )

    markdown = render_page(page)

    assert markdown.startswith("---\n")
    assert "title: سقف واحدهای نیمسال\n" in markdown
    assert "category: references\n" in markdown
    assert "tags: [academic-regulations, units]\n" in markdown
    assert 'target: "[[references/academic-probation]]"\n' in markdown
    assert "sources: [raw/Karshenasi.pdf#page=1]\n" in markdown
    assert "summary: حد مجاز اخذ واحد در هر نیمسال.\n" in markdown
    assert "created: 2026-06-23T08:00:00Z\n" in markdown
    assert "# سقف واحدهای نیمسال\n\n## Key Ideas" in markdown
