"""Tests for the Phase 3 wiki builder CLI."""

import subprocess
import sys
from pathlib import Path

from iau_chatbot.build_wiki import FakeSegmentPageBuilder, page_from_llm_payload
from iau_chatbot.ingest.segments import RegulationSegment
from iau_chatbot.retrieval.metadata import retrieve


def test_build_wiki_fake_mode_writes_vault(tmp_path: Path) -> None:
    pdf_dir = tmp_path / "raw"
    wiki_dir = tmp_path / "wiki"
    pdf_dir.mkdir()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "LLM_API_KEY=test-key",
                f"PDF_DIR={pdf_dir}",
                f"WIKI_DIR={wiki_dir}",
            ]
        ),
        encoding="utf-8",
    )
    segments_file = tmp_path / "segments.jsonl"
    segments_file.write_text(
        '{"source_path":"raw/Karshenasi.pdf","page_start":1,"page_end":1,'
        '"heading":"انتخاب واحد","text":"دانشجو باید سقف مجاز را رعایت کند.",'
        '"source_ref":"raw/Karshenasi.pdf#page=1","content_hash":"sha256:abc"}\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "iau_chatbot.build_wiki",
            "--env-file",
            str(env_file),
            "--segments-jsonl",
            str(segments_file),
            "--fake-llm",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "wiki pages written: 9" in result.stderr
    assert (wiki_dir / "آیین نامه آموزشی" / "انتخاب واحد.md").exists()
    assert (wiki_dir / "مقررات-نمره" / "مشروطی.md").exists()
    assert (
        retrieve("اگر دانشجو مشروط شود ترم بعد چند واحد می‌تواند بردارد؟", wiki_dir=wiki_dir)[
            0
        ].title
        == "مشروطی"
    )


def test_fake_builder_creates_persian_qa_page_with_aliases() -> None:
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="انتخاب همزمان درس پیشنیاز و وابسته",
        text="دانشجو می‌تواند درس پیشنیاز و درس وابسته را با نظر گروه همزمان انتخاب کند.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    page = FakeSegmentPageBuilder().build_page(segment)

    assert page.category == "آیین نامه آموزشی"
    assert page.tags == ["مقررات آموزشی", "دانشگاه آزاد اسلامی"]
    assert "## حکم اصلی" in page.body
    assert "## پرسش‌های قابل پاسخ" in page.body
    assert "درس وابسته" in page.aliases


def test_fake_builder_infers_grade_aliases() -> None:
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="حداقل نمره قبولی",
        text="حداقل نمره قبولی در هر درس 10 است و آشنایی با قرآن کریم 12 می‌باشد.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    page = FakeSegmentPageBuilder().build_page(segment)

    assert "نمره قبولی" in page.aliases
    assert "آشنایی با قرآن" in page.aliases


def test_page_from_llm_payload_ignores_non_object_relationships() -> None:
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="انتخاب واحد",
        text="دانشجو باید سقف مجاز را رعایت کند.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    page = page_from_llm_payload(
        {
            "title": "انتخاب واحد",
            "summary": "سقف مجاز انتخاب واحد.",
            "body": "متن صفحه",
            "relationships": ["[[references/other]]", {"target": "[[x]]", "type": "related_to"}],
        },
        segment,
    )

    assert len(page.relationships) == 1
    assert page.relationships[0].target == "[[x]]"


def test_page_from_llm_payload_normalizes_source_objects() -> None:
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="انتخاب واحد",
        text="دانشجو باید سقف مجاز را رعایت کند.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    page = page_from_llm_payload(
        {
            "title": "انتخاب واحد",
            "summary": "سقف مجاز انتخاب واحد.",
            "body": "متن صفحه",
            "sources": [{"type": "PDF", "title": "آیین نامه", "url": "raw/Karshenasi.pdf#page=31"}],
        },
        segment,
    )

    assert page.sources == ["raw/Karshenasi.pdf#page=31"]


def test_page_from_llm_payload_normalizes_source_without_directory() -> None:
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="انتخاب واحد",
        text="دانشجو باید سقف مجاز را رعایت کند.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    page = page_from_llm_payload(
        {
            "title": "انتخاب واحد",
            "summary": "سقف مجاز انتخاب واحد.",
            "body": "متن صفحه",
            "sources": ["Karshenasi.pdf#page=1"],
        },
        segment,
    )

    assert page.sources == ["raw/Karshenasi.pdf#page=1"]


def test_page_from_llm_payload_keeps_original_segment_text() -> None:
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="انتخاب واحد",
        text="دانشجو باید سقف مجاز را رعایت کند.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    page = page_from_llm_payload(
        {
            "title": "انتخاب واحد",
            "summary": "سقف مجاز انتخاب واحد.",
            "body": "متن صفحه",
        },
        segment,
    )

    assert "## متن منبع" in page.body
    assert "دانشجو باید سقف مجاز را رعایت کند." in page.body


def test_page_from_llm_payload_keeps_and_infers_persian_aliases() -> None:
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="انتخاب همزمان درس پیشنیاز و وابسته",
        text="دانشجو می‌تواند درس پیشنیاز و درس وابسته را با نظر گروه همزمان انتخاب کند.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    page = page_from_llm_payload(
        {
            "title": "انتخاب همزمان درس پیشنیاز و وابسته",
            "summary": "شرایط انتخاب همزمان درس پیشنیاز و وابسته.",
            "body": "متن صفحه",
            "aliases": ["اخذ همزمان پیش‌نیاز", "Prerequisite course"],
        },
        segment,
    )

    assert "اخذ همزمان پیش‌نیاز" in page.aliases
    assert "درس وابسته" in page.aliases
    assert "Prerequisite course" not in page.aliases


def test_page_from_llm_payload_repairs_english_metadata() -> None:
    segment = RegulationSegment(
        source_path="raw/Karshenasi.pdf",
        page_start=1,
        page_end=1,
        heading="حذف اضطراری",
        text="دانشجو می‌تواند تا پنج هفته قبل از پایان نیمسال فقط یک درس را حذف کند.",
        source_ref="raw/Karshenasi.pdf#page=1",
        content_hash="sha256:abc",
    )

    page = page_from_llm_payload(
        {
            "title": "Emergency Withdrawal",
            "category": "Academic Regulations",
            "tags": ["course withdrawal"],
            "summary": "English summary.",
            "body": "English body.",
        },
        segment,
    )

    assert page.title == "حذف اضطراری"
    assert page.category == "آیین نامه آموزشی"
    assert page.tags == ["مقررات آموزشی", "دانشگاه آزاد اسلامی"]
    assert "دانشجو می‌تواند تا پنج هفته" in page.summary
    assert "دانشجو می‌تواند تا پنج هفته" in page.body
