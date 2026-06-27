"""Tests for the Phase 5 LangGraph question-answering agent."""

from pathlib import Path

from iau_chatbot.agent.graph import answer_question


class FakeAnswerLLM:
    """Deterministic answer generator for agent tests."""

    calls = 0

    def complete_text(self, *, system: str, user: str) -> str:
        self.calls += 1
        assert "Only use the supplied wiki context" in system
        assert "do not mention source titles" in system
        assert "detailed, practical, and complete explanation" in system
        assert "سقف واحدهای نیمسال" in user
        return "دانشجو باید سقف واحدهای مجاز نیمسال را رعایت کند."


def test_agent_returns_source_grounded_answer(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "semester-unit-limit.md",
        title="سقف واحدهای نیمسال",
        summary="حداکثر واحدهای قابل اخذ در هر نیمسال.",
        body="دانشجو می‌تواند در هر نیمسال تا سقف مجاز واحد انتخاب کند.",
        source="raw/Karshenasi.pdf#page=8",
    )

    result = answer_question(
        "سقف واحد در ترم چقدر است؟",
        wiki_dir=tmp_path,
        llm=FakeAnswerLLM(),
    )

    assert result.answer == "دانشجو باید سقف واحدهای مجاز نیمسال را رعایت کند."
    assert result.sources[0].wiki_page == "references/semester-unit-limit.md"
    assert result.sources[0].source_ref == "raw/Karshenasi.pdf#page=8"
    assert result.errors == []


def test_agent_rejects_empty_question(tmp_path: Path) -> None:
    result = answer_question("  ", wiki_dir=tmp_path, llm=FakeAnswerLLM())

    assert result.answer == "پرسش نمی‌تواند خالی باشد."
    assert result.sources == []
    assert result.errors == ["empty_question"]


def test_agent_reports_unknown_when_no_pages_match(tmp_path: Path) -> None:
    result = answer_question("شهریه خوابگاه چقدر است؟", wiki_dir=tmp_path, llm=FakeAnswerLLM())

    assert "اطلاعات کافی" in result.answer
    assert result.sources == []
    assert result.errors == ["no_retrieval_results"]


def test_agent_uses_metadata_ranked_evidence(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "semester-unit-limit.md",
        title="محدودیت تعداد واحد",
        summary="قاعده تعداد واحدهای قابل اخذ.",
        body="دانشجوی کارشناسی در یک نیمسال تحصیلی نمی‌تواند از ۱۲ واحد کمتر و از ۲۰ واحد بیشتر اخذ کند.",
        source="raw/Karshenasi.pdf#page=8",
        tags=["academic-regulations", "units", "undergraduate"],
        aliases=["سقف واحد", "انتخاب واحد", "ترم"],
    )
    _write_page(
        tmp_path / "references" / "course-selection-noise.md",
        title="انتخاب واحد و شهریه",
        summary="انتخاب واحد درسی دانشجوی کارشناسی در هر ترم.",
        body="سقف واحد مجاز در هر ترم برای دانشجوی کارشناسی چقدر است؟ این صفحه درباره شهریه است.",
        source="raw/Karshenasi.pdf#page=10",
        tags=["academic-regulations", "fees"],
    )

    llm = RecordingLLM()
    result = answer_question(
        "سقف واحد مجاز در هر ترم برای دانشجوی کارشناسی چقدر است؟",
        wiki_dir=tmp_path,
        llm=llm,
        top_k=1,
    )

    assert result.sources[0].wiki_page == "references/semester-unit-limit.md"
    assert "۲۰ واحد" in llm.last_user


def test_agent_source_excerpt_uses_selected_evidence(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "passing-grade.md",
        title="حداقل نمره قبولی",
        summary="قاعده نمره قبولی.",
        body=(
            "این مقدمه درباره تقویم آموزشی و انتخاب واحد است "
            "ماده ۴۰ حداقل نمره قبولی در هر درس 10 و درس آشنایی با قرآن کریم 12 است"
        ),
        source="raw/Karshenasi.pdf#page=15",
        tags=["نمره قبولی", "ارزیابی"],
        aliases=["آشنایی با قرآن", "حداقل نمره"],
    )

    result = answer_question(
        "حداقل نمره قبولی هر درس چند است و آشنایی با قرآن چند است؟",
        wiki_dir=tmp_path,
        llm=RecordingLLM(),
    )

    assert "آشنایی با قرآن کریم 12" in result.sources[0].excerpt
    assert "این مقدمه" not in result.sources[0].excerpt


def test_agent_includes_short_session_history(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "attendance.md",
        title="حضور و غیاب",
        summary="مقررات حضور در کلاس.",
        body="حضور دانشجو در برنامه‌های درسی الزامی است.",
        source="raw/Karshenasi.pdf#page=13",
    )
    llm = RecordingLLM()

    answer_question("حضور در کلاس اجباری است؟", session_id="s1", wiki_dir=tmp_path, llm=llm)
    answer_question("دوباره بگو", session_id="s1", wiki_dir=tmp_path, llm=llm)

    assert "Previous turn:" in llm.last_user
    assert "Turn 1 Q: حضور در کلاس اجباری است؟" in llm.last_user


def test_agent_includes_multiple_recent_turns(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "attendance.md",
        title="حضور و غیاب",
        summary="مقررات حضور در کلاس.",
        body="حضور دانشجو در برنامه‌های درسی الزامی است.",
        source="raw/Karshenasi.pdf#page=13",
    )
    llm = RecordingLLM()

    answer_question("پرسش اول درباره حضور چیست؟", session_id="s2", wiki_dir=tmp_path, llm=llm)
    answer_question("پرسش دوم درباره حضور چیست؟", session_id="s2", wiki_dir=tmp_path, llm=llm)
    answer_question("حالا جمع‌بندی کن", session_id="s2", wiki_dir=tmp_path, llm=llm)

    assert "Turn 1 Q: پرسش اول درباره حضور چیست؟" in llm.last_user
    assert "Turn 2 Q: پرسش دوم درباره حضور چیست؟" in llm.last_user


def test_twenty_representative_questions_return_sources(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "regulations.md",
        title="مقررات آموزشی",
        summary="سقف واحد، مشروطی، حذف و اضافه، مرخصی، مهمانی، انتقال، سنوات، امتحان، نمره، فارغ التحصیلی، کارآموزی، پروژه، دروس عمومی، پیش نیاز، جبران معدل، انصراف، بازگشت، شهریه، حضور و غیاب.",
        body="دانشجو باید مقررات آموزشی مندرج در آیین نامه را رعایت کند.",
        source="raw/Karshenasi.pdf#page=1",
    )
    questions = [
        "سقف واحد در ترم چقدر است؟",
        "مشروطی چه شرایطی دارد؟",
        "حذف و اضافه کی انجام می‌شود؟",
        "مرخصی تحصیلی چطور ثبت می‌شود؟",
        "شرایط مهمانی چیست؟",
        "انتقال به واحد دیگر چگونه است؟",
        "سنوات مجاز تحصیل چقدر است؟",
        "غیبت در امتحان چه حکمی دارد؟",
        "نمره قبولی چند است؟",
        "شرایط فارغ التحصیلی چیست؟",
        "کارآموزی چه ضوابطی دارد؟",
        "پروژه پایانی چه زمانی اخذ می‌شود؟",
        "دروس عمومی اجباری هستند؟",
        "رعایت پیش نیاز لازم است؟",
        "جبران معدل چطور انجام می‌شود؟",
        "انصراف از تحصیل چه شرایطی دارد؟",
        "بازگشت به تحصیل ممکن است؟",
        "شهریه ثابت چگونه محاسبه می‌شود؟",
        "حضور و غیاب کلاس چگونه است؟",
        "آیین نامه آموزشی چه می‌گوید؟",
    ]

    results = [
        answer_question(question, wiki_dir=tmp_path, llm=RecordingLLM()) for question in questions
    ]

    assert len(results) == 20
    assert all(result.sources for result in results)
    assert all(not result.errors for result in results)


class RecordingLLM:
    """LLM stub that records the final prompt."""

    last_user = ""

    def complete_text(self, *, system: str, user: str) -> str:
        self.last_user = user
        return "پاسخ کوتاه."


def _write_page(
    path: Path,
    *,
    title: str,
    summary: str,
    body: str,
    source: str,
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"title: {title}",
                "category: references",
                f"tags: [{', '.join(tags or ['academic-regulations'])}]",
                f"aliases: [{', '.join(aliases or [])}]",
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
