"""Tests for Phase 4 Obsidian vault retrieval."""

from pathlib import Path

from iau_chatbot.retrieval.context import assemble_context
from iau_chatbot.retrieval.lexical import retrieve
from iau_chatbot.retrieval.vector import retrieve as vector_retrieve


def test_retrieve_returns_relevant_persian_wiki_pages(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "semester-unit-limit.md",
        title="سقف واحدهای نیمسال",
        summary="حداکثر واحدهای قابل اخذ در هر نیمسال.",
        body="دانشجو می‌تواند در هر نیمسال تا سقف مجاز واحد انتخاب کند.",
        source="raw/Karshenasi.pdf#page=8",
    )
    _write_page(
        tmp_path / "references" / "attendance.md",
        title="حضور و غیاب",
        summary="مقررات حضور در کلاس.",
        body="حضور دانشجو در برنامه‌های درسی الزامی است.",
        source="raw/Karshenasi.pdf#page=13",
    )

    results = retrieve("سقف واحد در ترم", wiki_dir=tmp_path, top_k=1)

    assert [page.title for page in results] == ["سقف واحدهای نیمسال"]
    assert results[0].source_path == "references/semester-unit-limit.md"
    assert results[0].sources == ["raw/Karshenasi.pdf#page=8"]
    assert results[0].score > 0


def test_assemble_context_includes_sources_and_limits_pages(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "attendance.md",
        title="حضور و غیاب",
        summary="مقررات حضور در کلاس.",
        body="حضور دانشجو در برنامه‌های درسی الزامی است.",
        source="raw/Karshenasi.pdf#page=13",
    )

    pages = retrieve("حضور کلاس", wiki_dir=tmp_path, top_k=1)
    context = assemble_context(pages, max_chars=180)

    assert "حضور و غیاب" in context
    assert "raw/Karshenasi.pdf#page=13" in context
    assert len(context) <= 180


def test_vector_retrieve_falls_back_to_lexical(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "probation.md",
        title="مشروطی",
        summary="مقررات مشروطی دانشجو.",
        body="دانشجوی مشروط باید شرایط ادامه تحصیل را رعایت کند.",
        source="raw/Karshenasi.pdf#page=18",
    )

    results = vector_retrieve("مقررات مشروطی", wiki_dir=tmp_path, top_k=1)

    assert [page.title for page in results] == ["مشروطی"]


def test_title_and_summary_matches_rank_above_body_noise(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "unit-limit.md",
        title="سقف واحدهای نیمسال",
        summary="حداکثر واحدهای قابل اخذ در هر نیمسال.",
        body="قانون انتخاب واحد.",
        source="raw/Karshenasi.pdf#page=8",
    )
    _write_page(
        tmp_path / "references" / "noise.md",
        title="برنامه آموزشی",
        summary="توضیح عمومی.",
        body="این متن در هر ترم و در هر نیمسال چند بار واژه‌های عمومی را تکرار می‌کند.",
        source="raw/Karshenasi.pdf#page=9",
    )

    results = retrieve("سقف واحد در ترم", wiki_dir=tmp_path, top_k=2)

    assert results[0].title == "سقف واحدهای نیمسال"


def test_phrase_match_ranks_above_generic_overlap(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "unit-limit.md",
        title="تعلیم و برنامه درسی دانشگاهی",
        summary="تعداد واحدهای درسی و طول مدت تحصیل.",
        body="تعداد واحدهای انتخابی دانشجوی تمام وقت در یک نیمسال تحصیلی نمی‌تواند از 12 واحد کمتر و از 20 واحد بیشتر باشد.",
        source="raw/Karshenasi.pdf#page=8",
    )
    _write_page(
        tmp_path / "references" / "course-selection.md",
        title="انتخاب واحد",
        summary="انتخاب واحد درسی و جبران معدل.",
        body="دانشجو باید قوانین انتخاب واحد، امتحان، نمره، ترم و درس را رعایت کند.",
        source="raw/Karshenasi.pdf#page=10",
    )

    results = retrieve(
        "سقف واحد مجاز در هر ترم برای دانشجوی کارشناسی چقدر است؟", wiki_dir=tmp_path, top_k=1
    )

    assert results[0].source_path == "references/unit-limit.md"


def test_retrieve_strips_persian_punctuation_from_terms(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "regulations.md",
        title="مقررات آموزشی",
        summary="مشروطی، مرخصی، شهریه.",
        body="دانشجو باید آیین نامه را رعایت کند.",
        source="raw/Karshenasi.pdf#page=1",
    )

    results = retrieve("شرایط مشروطی چیست؟", wiki_dir=tmp_path, top_k=1)

    assert [page.title for page in results] == ["مقررات آموزشی"]


def _write_page(path: Path, *, title: str, summary: str, body: str, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"title: {title}",
                "category: references",
                "tags: [academic-regulations]",
                f"sources: [{source}]",
                f"summary: {summary}",
                "---",
                "",
                f"# {title}",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )
