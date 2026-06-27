"""End-to-end smoke test for the local LLM-Wiki QA pipeline."""

from pathlib import Path

from iau_chatbot.agent.graph import answer_question
from iau_chatbot.build_wiki import FakeSegmentPageBuilder
from iau_chatbot.ingest.segments import PageText, build_segments
from iau_chatbot.wiki.store import WikiStore


class _FixtureLLM:
    def complete_text(self, *, system: str, user: str) -> str:
        return "دانشجو در این نمونه مجاز به اخذ حداکثر ۲۰ واحد در هر نیمسال است."


def test_fixture_text_flows_from_segment_to_sourced_answer(tmp_path: Path) -> None:
    pages = [
        PageText(
            page_number=1,
            text=(
                "ماده ۱ انتخاب واحد\n"
                "دانشجو در هر نیمسال تحصیلی مجاز به اخذ حداکثر ۲۰ واحد درسی است. "
                "رعایت سقف واحد برای همه دانشجویان الزامی است."
            ),
        )
    ]
    segments = build_segments("raw/fixture.pdf", pages, min_words=5)
    builder = FakeSegmentPageBuilder()
    wiki_pages = [builder.build_page(segment) for segment in segments]
    wiki_dir = tmp_path / "wiki"
    WikiStore(wiki_dir).write_pages(wiki_pages, segments=segments, llm_calls=builder.calls)

    result = answer_question(
        "سقف واحد در هر ترم چقدر است؟",
        wiki_dir=wiki_dir,
        llm=_FixtureLLM(),
    )

    assert "۲۰ واحد" in result.answer
    assert result.sources
    assert result.sources[0].source_ref == "raw/fixture.pdf#page=1"
