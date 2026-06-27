"""Tests for Phase 8 metadata-first wiki retrieval."""

from pathlib import Path

from iau_chatbot.retrieval.context import assemble_context
from iau_chatbot.retrieval.metadata import retrieve


def test_metadata_retrieve_boosts_frontmatter_over_body_noise(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "semester-unit-limit.md",
        title="محدودیت تعداد واحد",
        tags=["academic-regulations", "units", "undergraduate"],
        aliases=["سقف واحد", "انتخاب واحد", "ترم"],
        summary="قاعده تعداد واحدهای قابل اخذ.",
        body="دانشجوی کارشناسی در یک نیمسال تحصیلی نمی‌تواند از ۱۲ واحد کمتر و از ۲۰ واحد بیشتر اخذ کند.",
        source="raw/Karshenasi.pdf#page=8",
    )
    _write_page(
        tmp_path / "references" / "course-selection-noise.md",
        title="انتخاب واحد و شهریه",
        tags=["academic-regulations", "fees"],
        aliases=[],
        summary="انتخاب واحد درسی دانشجوی کارشناسی در هر ترم.",
        body="سقف واحد مجاز در هر ترم برای دانشجوی کارشناسی چقدر است؟ این صفحه درباره شهریه است.",
        source="raw/Karshenasi.pdf#page=10",
    )

    results = retrieve(
        "سقف واحد مجاز در هر ترم برای دانشجوی کارشناسی چقدر است؟",
        wiki_dir=tmp_path,
        top_k=1,
    )

    assert results[0].source_path == "references/semester-unit-limit.md"


def test_metadata_retrieve_uses_unit_limit_answer_phrase(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "normal-unit-limit.md",
        title="و گفتگو تعلیم داده می شود",
        tags=["Curriculum", "Course Structure"],
        aliases=[],
        summary="ساختار واحدهای درسی و طول مدت تحصیل.",
        body="تعداد واحدهای انتخابی دانشجوی تمام وقت در یک نیمسال تحصیلی نمی‌تواند از 12 واحد کمتر و از 20 واحد بیشتر باشد.",
        source="raw/Karshenasi.pdf#page=8",
    )
    _write_page(
        tmp_path / "references" / "final-semester.md",
        title="بگذراند",
        tags=["تحصیل", "دروس", "نیمسال"],
        aliases=[],
        summary="انتخاب و گذراندن دروس باقی‌مانده.",
        body="دانشجو در ترم آخر با 24 واحد باقی‌مانده و رعایت شرایط می‌تواند انتخاب واحد کند.",
        source="raw/Karshenasi.pdf#page=9",
    )

    results = retrieve(
        "سقف واحد مجاز در هر ترم برای دانشجوی کارشناسی چقدر است؟",
        wiki_dir=tmp_path,
        top_k=1,
    )

    assert results[0].source_path == "references/normal-unit-limit.md"


def test_metadata_retrieve_normalizes_course_and_term_withdrawal(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "withdrawal.md",
        title="حذف درس و حذف کلیه واحدها",
        tags=["academic-regulations", "course withdrawal", "leave of absence"],
        aliases=["حذف درس", "حذف اضطراری", "حذف ترم", "حذف کلیه دروس"],
        summary="شرایط حذف درس، حذف اضطراری و حذف همه واحدهای نیمسال.",
        body=(
            "دانشجو می‌تواند با موافقت گروه آموزشی درس را حذف کند. "
            "حذف کلیه واحدهای انتخابی فقط با تشخیص شورای آموزشی مجاز است و مرخصی محسوب می‌شود."
        ),
        source="raw/Karshenasi.pdf#page=14",
    )
    _write_page(
        tmp_path / "references" / "grades.md",
        title="نمرات درس",
        tags=["academic-regulations", "grades"],
        aliases=[],
        summary="حذف نمره قبلی در نیمسال جبرانی.",
        body="در صورت تکرار درس، نمره قبلی ممکن است حذف و بلااثر شود.",
        source="raw/Karshenasi.pdf#page=19",
    )

    results = retrieve("حذف درس یا حذف ترم چه شرایطی دارد؟", wiki_dir=tmp_path, top_k=1)

    assert results[0].source_path == "references/withdrawal.md"


def test_metadata_retrieve_prefers_withdrawal_rule_over_generic_delete_note(
    tmp_path: Path,
) -> None:
    _write_page(
        tmp_path / "references" / "delete-note.md",
        title="یادآوری",
        tags=["نمرات", "حذف", "نام نویسی مشروط"],
        aliases=[],
        summary="مقررات حذف نمرات و نام نویسی مشروط.",
        body="منظور از حذف در این آیین نامه پاک کردن درس یا نمره نیست بلکه بلااثر نمودن نمره است.",
        source="raw/Karshenasi.pdf#page=17",
    )
    _write_page(
        tmp_path / "references" / "withdrawal.md",
        title="Regulations on Absences and Course Withdrawal",
        tags=["exams", "course withdrawal", "academic policies"],
        aliases=[],
        summary="Course withdrawal procedures and complete withdrawal rules.",
        body="حذف اضطراری و حذف کلیه واحدهای انتخابی در یک نیمسال فقط با شرایط آیین‌نامه مجاز است.",
        source="raw/Karshenasi.pdf#page=14",
    )

    results = retrieve("حذف درس یا حذف ترم چه شرایطی دارد؟", wiki_dir=tmp_path, top_k=1)

    assert results[0].source_path == "references/withdrawal.md"


def test_metadata_retrieve_routes_low_average_to_probation_rule(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "probation.md",
        title="نام نویسی مشروط",
        tags=["academic-regulations", "probation", "units"],
        aliases=["مشروطی", "معدل کمتر از ۱۲", "۱۴ واحد"],
        summary="محدودیت انتخاب واحد دانشجوی مشروط.",
        body="دانشجویی که مشروط ثبت نام می‌کند، جز در آخرین نیمسال حق انتخاب بیش از ۱۴ واحد ندارد.",
        source="raw/Karshenasi.pdf#page=18",
    )
    _write_page(
        tmp_path / "references" / "unit-limit.md",
        title="سقف واحدهای عادی",
        tags=["academic-regulations", "units"],
        aliases=["سقف واحد", "انتخاب واحد"],
        summary="حداکثر واحدهای عادی هر نیمسال.",
        body="دانشجوی عادی می‌تواند تا ۲۰ واحد در یک نیمسال انتخاب کند.",
        source="raw/Karshenasi.pdf#page=8",
    )

    results = retrieve(
        "اگر معدل دانشجو کمتر از ۱۲ شود، ترم بعد چند واحد می‌تواند بگیرد؟",
        wiki_dir=tmp_path,
        top_k=1,
    )

    assert results[0].source_path == "references/probation.md"


def test_metadata_retrieve_routes_passing_grade_question(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "passing-grade.md",
        title="حداقل نمره قبولی",
        tags=["نمره قبولی", "ارزیابی"],
        aliases=["آشنایی با قرآن", "حداقل نمره"],
        summary="حداقل نمره قبولی دروس.",
        body="حداقل نمره قبولی در هر درس 10 و درس آشنایی با قرآن کریم 12 است.",
        source="raw/Karshenasi.pdf#page=15",
    )
    _write_page(
        tmp_path / "references" / "grade-noise.md",
        title="نمرات جبرانی",
        tags=["نمرات"],
        aliases=[],
        summary="تکرار درس و نمره قبلی.",
        body="نمره اخذ شده هر درس در نیمسال جبرانی بررسی می‌شود.",
        source="raw/Karshenasi.pdf#page=19",
    )

    results = retrieve(
        "حداقل نمره قبولی هر درس چند است و آشنایی با قرآن چند است؟",
        wiki_dir=tmp_path,
        top_k=1,
    )

    assert results[0].source_path == "references/passing-grade.md"


def test_metadata_retrieve_does_not_use_normal_unit_limit_for_probation_question(
    tmp_path: Path,
) -> None:
    _write_page(
        tmp_path / "references" / "normal-unit-limit.md",
        title="واحدهای عادی",
        tags=["Curriculum", "Course Structure"],
        aliases=[],
        summary="تعداد واحدهای عادی.",
        body="تعداد واحدهای انتخابی دانشجوی تمام وقت در یک نیمسال تحصیلی نمی‌تواند از 12 واحد کمتر و از 20 واحد بیشتر باشد.",
        source="raw/Karshenasi.pdf#page=8",
    )
    _write_page(
        tmp_path / "references" / "probation.md",
        title="یادآوری",
        tags=["نمرات", "حذف", "نام نویسی مشروط", "دانشجویان مشروط"],
        aliases=[],
        summary="نام نویسی مشروط.",
        body="دانشجویی که به صورت مشروط نام نویسی می‌کند، جز در آخرین نیمسال تحصیلی حق انتخاب بیش از 14 واحد درسی در آن نیمسال را ندارد.",
        source="raw/Karshenasi.pdf#page=17",
    )

    results = retrieve(
        "اگر معدل دانشجو کمتر از ۱۲ شود، ترم بعد چند واحد می‌تواند بگیرد؟",
        wiki_dir=tmp_path,
        top_k=1,
    )

    assert results[0].source_path == "references/probation.md"


def test_metadata_context_uses_short_evidence_snippet(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "exam-absence.md",
        title="غیبت امتحان",
        tags=["academic-regulations", "exam absence"],
        aliases=["غیبت در امتحان", "امتحان پایان ترم"],
        summary="حکم غیبت غیرموجه در جلسه امتحان.",
        body=(
            "این مقدمه درباره تقویم آموزشی و انتخاب واحد است و شاهد پاسخ نیست.\n\n"
            "غیبت غیرموجه در جلسه امتحان بیش از سه درس به منزله نمره صفر در آن درس‌ها است."
        ),
        source="raw/Karshenasi.pdf#page=14",
    )

    pages = retrieve(
        "اگر دانشجو در امتحان پایان ترم غیبت کند چه می‌شود؟", wiki_dir=tmp_path, top_k=1
    )
    context = assemble_context(pages, max_chars=500)

    assert "نمره صفر" in context
    assert "این مقدمه" not in context


def test_metadata_context_splits_ocr_rule_chunks(tmp_path: Path) -> None:
    _write_page(
        tmp_path / "references" / "passing-grade.md",
        title="حداقل نمره قبولی",
        tags=["نمره قبولی", "ارزیابی"],
        aliases=["آشنایی با قرآن", "حداقل نمره"],
        summary="قاعده نمره قبولی.",
        body=(
            "این مقدمه درباره تقویم آموزشی و انتخاب واحد است "
            "ماده ۴۰ حداقل نمره قبولی در هر درس 10 و درس آشنایی با قرآن کریم 12 است "
            "تبصره این متن درباره کارنامه و امور مالی است"
        ),
        source="raw/Karshenasi.pdf#page=15",
    )

    pages = retrieve(
        "حداقل نمره قبولی هر درس چند است و آشنایی با قرآن چند است؟",
        wiki_dir=tmp_path,
        top_k=1,
    )
    context = assemble_context(pages, max_chars=500)

    assert "حداقل نمره قبولی در هر درس 10" in context
    assert "آشنایی با قرآن کریم 12" in context
    assert "این مقدمه" not in context


def _write_page(
    path: Path,
    *,
    title: str,
    tags: list[str],
    aliases: list[str],
    summary: str,
    body: str,
    source: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"title: {title}",
                "category: references",
                f"tags: [{', '.join(tags)}]",
                f"aliases: [{', '.join(aliases)}]",
                f"sources: [{source}]",
                f"summary: {summary}",
                "lifecycle: reviewed",
                "tier: core",
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
