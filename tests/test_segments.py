"""Tests for Persian regulation text segmentation."""

from iau_chatbot.ingest.segments import PageText, build_segments, normalize_persian_text


def test_normalize_persian_text_unifies_arabic_variants() -> None:
    text = "دانشجويان مكلف‌اند\u200c ثبت نام كنند"

    assert normalize_persian_text(text) == "دانشجویان مکلف‌اند ثبت نام کنند"


def test_build_segments_keeps_source_ref_and_hash() -> None:
    pages = [
        PageText(
            page_number=1,
            text="ماده ۱ شرایط عمومی ثبت نام\nدانشجو باید در مهلت تعیین شده ثبت نام کند.",
        ),
        PageText(
            page_number=2,
            text="تبصره ۱ انتخاب واحد\nدانشجو می‌تواند واحدهای مجاز را انتخاب کند.",
        ),
    ]

    segments = build_segments("raw/Karshenasi.pdf", pages, max_words=20)

    assert len(segments) == 2
    assert segments[0].heading == "ماده ۱ شرایط عمومی ثبت نام"
    assert segments[0].source_ref == "raw/Karshenasi.pdf#page=1"
    assert segments[0].content_hash.startswith("sha256:")
    assert segments[1].source_ref == "raw/Karshenasi.pdf#page=2"


def test_build_segments_merges_short_pages() -> None:
    pages = [
        PageText(page_number=1, text="مقدمه کوتاه"),
        PageText(page_number=2, text="ادامه کوتاه"),
    ]

    segments = build_segments("raw/Karshenasi.pdf", pages, max_words=30, min_words=6)

    assert len(segments) == 1
    assert segments[0].page_start == 1
    assert segments[0].page_end == 2
    assert segments[0].source_ref == "raw/Karshenasi.pdf#page=1-2"


def test_heading_skips_page_numbers() -> None:
    pages = [
        PageText(
            page_number=1,
            text="١\nآیین نامه آموزشی\nدانشجو باید مقررات آموزشی را رعایت کند.",
        )
    ]

    segments = build_segments("raw/Karshenasi.pdf", pages)

    assert segments[0].heading == "آیین نامه آموزشی"


def test_heading_skips_punctuation_only_lines() -> None:
    pages = [
        PageText(
            page_number=1,
            text="-\n)\nفصل سوم\nدانشجو باید مقررات آموزشی را رعایت کند.",
        )
    ]

    segments = build_segments("raw/Karshenasi.pdf", pages)

    assert segments[0].heading == "فصل سوم"
