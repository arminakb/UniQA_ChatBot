"""CLI for building an Obsidian LLM-Wiki vault from regulation segments."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from loguru import logger

from iau_chatbot.config import Settings
from iau_chatbot.exceptions import WikiBuildError
from iau_chatbot.ingest.pdf import extract_pdf_pages
from iau_chatbot.ingest.segments import RegulationSegment, build_segments
from iau_chatbot.llm import LLMClient
from iau_chatbot.logging import configure_logging
from iau_chatbot.wiki.schema import WikiPage, WikiRelationship
from iau_chatbot.wiki.store import WikiStore


_CURATED_KARSHENASI_RULES: list[dict[str, Any]] = [
    {
        "title": "مشروطی",
        "category": "مقررات-نمره",
        "tags": ["آیین‌نامه", "نمره", "مشروطی"],
        "aliases": ["دانشجوی مشروط", "معدل کمتر از ۱۲", "سقف واحد مشروط"],
        "summary": "اگر میانگین نیمسال دانشجو کمتر از ۱۲ باشد، دانشجو مشروط است و در نیمسال بعد حداکثر ۱۴ واحد می‌تواند اخذ کند.",
        "body": "## حکم اصلی\nاگر میانگین نیمسال دانشجو کمتر از ۱۲ باشد، دانشجو مشروط محسوب می‌شود.\n\n## اعداد و محدودیت‌ها\nدانشجوی مشروط در نیمسال بعد، به جز آخرین نیمسال، حداکثر ۱۴ واحد می‌تواند انتخاب کند.\n\n## پرسش‌های قابل پاسخ\n- اگر دانشجو مشروط شود ترم بعد چند واحد می‌تواند بردارد؟\n- شرط مشروطی چیست؟",
        "sources": ["raw/Karshenasi.pdf#page=1"],
    },
    {
        "title": "اخراج آموزشی",
        "category": "مقررات-نمره",
        "tags": ["آیین‌نامه", "نمره", "اخراج"],
        "aliases": ["اخراج به دلیل مشروطی", "محرومیت آموزشی"],
        "summary": "تکرار وضعیت مشروطی طبق آیین‌نامه می‌تواند به اخراج آموزشی یا بررسی در کمیسیون موارد خاص منجر شود.",
        "body": "## حکم اصلی\nادامه وضعیت نامطلوب آموزشی و تکرار مشروطی مطابق آیین‌نامه قابل پیگیری است.\n\n## شرایط\nپرونده دانشجو در موارد لازم از مسیر آموزشی و کمیسیون مربوط بررسی می‌شود.\n\n## پرسش‌های قابل پاسخ\n- چه زمانی دانشجو اخراج آموزشی می‌شود؟",
        "sources": ["raw/Karshenasi.pdf#page=1"],
    },
    {
        "title": "حداقل نمره قبولی",
        "category": "مقررات-نمره",
        "tags": ["آیین‌نامه", "نمره", "قبولی"],
        "aliases": ["نمره قبولی", "حداقل نمره", "نمره پاس"],
        "summary": "حداقل نمره قبولی درس و اثر آن بر وضعیت آموزشی دانشجو باید طبق آیین‌نامه آموزشی بررسی شود.",
        "body": "## حکم اصلی\nنمره قبولی هر درس طبق مقررات آموزشی همان درس و مقطع ارزیابی می‌شود.\n\n## پرسش‌های قابل پاسخ\n- حداقل نمره قبولی چند است؟\n- اگر درس را پاس نکنم چه می‌شود؟",
        "sources": ["raw/Karshenasi.pdf#page=1"],
    },
    {
        "title": "حذف اضطراری",
        "category": "مقررات-درسی",
        "tags": ["آیین‌نامه", "انتخاب واحد", "حذف"],
        "aliases": ["حذف درس", "حذف اضطراری درس"],
        "summary": "حذف اضطراری درس در بازه و شرایط مشخص آموزشی انجام می‌شود و نباید دانشجو را از حداقل واحد مجاز خارج کند.",
        "body": "## حکم اصلی\nدانشجو فقط در چارچوب تقویم و مقررات آموزشی می‌تواند درس را حذف اضطراری کند.\n\n## شرایط\nرعایت حداقل واحد و تأیید آموزش برای حذف اضطراری لازم است.\n\n## پرسش‌های قابل پاسخ\n- شرایط حذف اضطراری چیست؟",
        "sources": ["raw/Karshenasi.pdf#page=1"],
    },
    {
        "title": "حذف و اضافه",
        "category": "مقررات-درسی",
        "tags": ["آیین‌نامه", "انتخاب واحد", "حذف و اضافه"],
        "aliases": ["تغییر انتخاب واحد", "اضافه کردن درس"],
        "summary": "حذف و اضافه برای اصلاح انتخاب واحد در بازه اعلام‌شده تقویم آموزشی انجام می‌شود.",
        "body": "## حکم اصلی\nدانشجو می‌تواند در مهلت حذف و اضافه، انتخاب واحد خود را طبق ضوابط اصلاح کند.\n\n## پرسش‌های قابل پاسخ\n- حذف و اضافه چه زمانی انجام می‌شود؟",
        "sources": ["raw/Karshenasi.pdf#page=1"],
    },
    {
        "title": "پیشنیاز و همنیاز",
        "category": "مقررات-درسی",
        "tags": ["آیین‌نامه", "درس", "پیشنیاز"],
        "aliases": ["پیش‌نیاز", "همنیاز", "درس وابسته"],
        "summary": "رعایت پیشنیاز، همنیاز و وابستگی دروس هنگام انتخاب واحد الزامی است مگر در موارد مجاز آموزشی.",
        "body": "## حکم اصلی\nدانشجو باید ترتیب پیشنیاز و همنیاز درس‌ها را در انتخاب واحد رعایت کند.\n\n## پرسش‌های قابل پاسخ\n- آیا می‌توان پیشنیاز و درس وابسته را همزمان گرفت؟",
        "sources": ["raw/Karshenasi.pdf#page=1"],
    },
    {
        "title": "مرخصی تحصیلی",
        "category": "مقررات-سنوات",
        "tags": ["آیین‌نامه", "سنوات", "مرخصی"],
        "aliases": ["مرخصی دانشجویی", "درخواست مرخصی"],
        "summary": "مرخصی تحصیلی با درخواست دانشجو و رعایت مقررات سنوات و موافقت واحد دانشگاهی قابل بررسی است.",
        "body": "## حکم اصلی\nمرخصی تحصیلی باید از مسیر رسمی آموزش درخواست و ثبت شود.\n\n## شرایط\nمدت مرخصی و اثر آن بر سنوات تابع آیین‌نامه آموزشی است.\n\n## پرسش‌های قابل پاسخ\n- شرایط مرخصی تحصیلی چیست؟",
        "sources": ["raw/Karshenasi.pdf#page=1"],
    },
    {
        "title": "حداقل و حداکثر واحد در نیمسال",
        "category": "مقررات-ثبت‌نام",
        "tags": ["آیین‌نامه", "ثبت‌نام", "واحد"],
        "aliases": ["سقف واحد", "کف واحد", "انتخاب واحد"],
        "summary": "تعداد واحدهای قابل اخذ در هر نیمسال باید بین حداقل و حداکثر مجاز آموزشی باشد.",
        "body": "## حکم اصلی\nدانشجو هنگام انتخاب واحد باید حداقل و حداکثر واحد مجاز نیمسال را رعایت کند.\n\n## اعداد و محدودیت‌ها\nسقف واحد دانشجوی مشروط با دانشجوی عادی متفاوت است.\n\n## پرسش‌های قابل پاسخ\n- در هر ترم چند واحد می‌توان برداشت؟",
        "sources": ["raw/Karshenasi.pdf#page=1"],
    },
]


class PageBuilder(Protocol):
    """Interface for segment-to-page builders."""

    calls: int

    def build_page(self, segment: RegulationSegment) -> WikiPage:
        """Build one wiki page from a regulation segment."""


class LLMSegmentPageBuilder:
    """Build wiki pages by asking an LLM for the Phase 3 JSON schema."""

    def __init__(self, client: LLMClient) -> None:
        self.client = client
        self.calls = 0

    def build_page(self, segment: RegulationSegment) -> WikiPage:
        """Convert one segment into a source-backed wiki page."""

        self.calls += 1
        payload = self.client.complete_json(system=_SYSTEM_PROMPT, user=_segment_prompt(segment))
        return page_from_llm_payload(payload, segment)


class FakeSegmentPageBuilder:
    """Deterministic local page builder for tests and offline smoke runs."""

    calls = 0

    def build_page(self, segment: RegulationSegment) -> WikiPage:
        self.calls += 1
        title = segment.heading if segment.heading != "بخش بدون عنوان" else "مقررات آموزشی"
        return WikiPage(
            title=title,
            slug=_slug(title),
            category="آیین نامه آموزشی",
            tags=["مقررات آموزشی", "دانشگاه آزاد اسلامی"],
            summary=_summary(segment.text),
            body=_qa_body(segment),
            sources=[segment.source_ref],
            aliases=_aliases([], segment),
        )


def main() -> int:
    """Build the configured Obsidian wiki vault."""

    parser = argparse.ArgumentParser(prog="python -m iau_chatbot.build_wiki")
    parser.add_argument("--env-file", default=".env", help="Path to the environment file.")
    parser.add_argument(
        "--segments-jsonl",
        type=Path,
        help="Optional JSONL segment file. If omitted, PDFs from PDF_DIR are extracted.",
    )
    parser.add_argument(
        "--fake-llm",
        action="store_true",
        help="Use deterministic local page generation instead of calling the LLM.",
    )
    args = parser.parse_args()

    settings = Settings.from_env(args.env_file)
    configure_logging(settings.log_level)
    segments = (
        _load_segments_jsonl(args.segments_jsonl)
        if args.segments_jsonl
        else _segments_from_pdfs(settings.pdf_dir)
    )
    builder: PageBuilder
    if args.fake_llm:
        builder = FakeSegmentPageBuilder()
    else:
        builder = LLMSegmentPageBuilder(
            LLMClient(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            )
        )

    pages: list[WikiPage] = []
    failed_segments: list[RegulationSegment] = []
    for segment in segments:
        try:
            pages.append(builder.build_page(segment))
        except WikiBuildError as exc:
            failed_segments.append(segment)
            logger.warning("wiki page build failed for {}: {}", segment.source_ref, exc)
    pages.extend(_curated_atomic_pages(segments))

    result = WikiStore(settings.wiki_dir).write_pages(
        pages,
        segments=segments,
        failed_segments=failed_segments,
        llm_calls=builder.calls,
    )
    logger.info(
        "wiki pages written: {} manifest={}",
        result.pages_written,
        result.manifest_path,
    )
    return 0


def page_from_llm_payload(payload: dict[str, Any], segment: RegulationSegment) -> WikiPage:
    """Validate an LLM JSON object as a wiki page."""

    relationships = [
        WikiRelationship(target=str(item["target"]), type=str(item["type"]))
        for item in payload.get("relationships", [])
        if isinstance(item, dict) and "target" in item and "type" in item
    ]
    sources = _normalize_sources(payload.get("sources"), segment.source_ref)
    title = _persian_or_fallback(str(payload.get("title", "")), segment.heading)
    summary = _persian_or_fallback(str(payload.get("summary", "")), _summary(segment.text))
    body = _persian_or_fallback(str(payload.get("body", "")), _qa_body(segment))
    return WikiPage(
        title=title,
        slug=_slug(str(payload.get("slug") or title)),
        category=_persian_or_fallback(str(payload.get("category", "")), "آیین نامه آموزشی"),
        tags=_persian_list(payload.get("tags"), ["مقررات آموزشی", "دانشگاه آزاد اسلامی"]),
        summary=summary,
        body=_with_source_text(body, segment.text),
        relationships=relationships,
        sources=sources,
        aliases=_aliases(payload.get("aliases"), segment),
        created=datetime.now(UTC),
        updated=datetime.now(UTC),
    )


def _segments_from_pdfs(pdf_dir: Path) -> list[RegulationSegment]:
    segments: list[RegulationSegment] = []
    for pdf in sorted(pdf_dir.glob("*.pdf")):
        rel_path = _display_path(pdf)
        segments.extend(build_segments(rel_path, extract_pdf_pages(pdf)))
    return segments


def _load_segments_jsonl(path: Path) -> list[RegulationSegment]:
    segments: list[RegulationSegment] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        segments.append(
            RegulationSegment(
                source_path=str(data["source_path"]),
                page_start=int(data["page_start"]),
                page_end=int(data["page_end"]),
                heading=str(data["heading"]),
                text=str(data["text"]),
                source_ref=str(data["source_ref"]),
                content_hash=str(data["content_hash"]),
            )
        )
    return segments


def _curated_atomic_pages(segments: list[RegulationSegment]) -> list[WikiPage]:
    if not any(Path(segment.source_path).name == "Karshenasi.pdf" for segment in segments):
        return []
    now = datetime.now(UTC)
    pages: list[WikiPage] = []
    for item in _CURATED_KARSHENASI_RULES:
        pages.append(
            WikiPage(
                title=item["title"],
                slug=_slug(item["title"]),
                category=item["category"],
                tags=item["tags"],
                aliases=item["aliases"],
                summary=item["summary"],
                body=item["body"],
                sources=item["sources"],
                lifecycle="reviewed",
                tier="core",
                base_confidence=0.95,
                created=now,
                updated=now,
            )
        )
    return pages


def _normalize_sources(raw_sources: Any, fallback: str) -> list[str]:
    sources: list[str] = []
    for source in raw_sources or [fallback]:
        value = (
            source.get("url") or source.get("source_ref") if isinstance(source, dict) else source
        )
        if value:
            sources.append(_normalize_source_ref(str(value), fallback))
    return sources or [fallback]


def _normalize_source_ref(value: str, fallback: str) -> str:
    source_path = fallback.split("#", 1)[0]
    if value == Path(source_path).name or value.startswith(f"{Path(source_path).name}#"):
        return f"{source_path}{value.removeprefix(Path(source_path).name)}"
    return value


def _with_source_text(body: str, source_text: str) -> str:
    if source_text.strip() in body:
        return body
    return f"{body.rstrip()}\n\n## متن منبع\n\n{source_text.strip()}"


def _segment_prompt(segment: RegulationSegment) -> str:
    return "\n".join(
        [
            f"Source: {segment.source_ref}",
            f"Heading: {segment.heading}",
            "",
            segment.text,
        ]
    )


def _summary(text: str) -> str:
    return text.strip().replace("\n", " ")[:180]


def _qa_body(segment: RegulationSegment) -> str:
    text = segment.text.strip()
    return "\n\n".join(
        [
            "## حکم اصلی",
            text,
            "## پرسش‌های قابل پاسخ",
            f"- {segment.heading}",
        ]
    )


def _persian_or_fallback(value: str, fallback: str) -> str:
    value = value.strip()
    return value if _has_persian(value) else fallback.strip()


def _persian_list(raw: Any, fallback: list[str]) -> list[str]:
    values = [str(item).strip() for item in raw or [] if _has_persian(str(item))]
    return values or fallback


def _aliases(raw: Any, segment: RegulationSegment) -> list[str]:
    aliases: list[str] = []
    for value in [*(raw or []), *_inferred_aliases(segment)]:
        text = str(value).strip()
        if text and _has_persian(text) and text not in aliases:
            aliases.append(text)
    return aliases


def _inferred_aliases(segment: RegulationSegment) -> list[str]:
    text = f"{segment.heading}\n{segment.text}"
    aliases: list[str] = []
    for phrase in (
        "پیشنیاز",
        "پیش‌نیاز",
        "درس وابسته",
        "حذف اضطراری",
        "غیبت موجه",
        "غیبت غیرموجه",
        "مرخصی تحصیلی",
        "انصراف از تحصیل",
        "مشروطی",
        "انتخاب واحد",
        "نمره قبولی",
        "حداقل نمره",
        "آشنایی با قرآن",
    ):
        if phrase in text:
            aliases.append(phrase)
    return aliases


def _has_persian(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06ff]", text))


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _slug(text: str) -> str:
    chars: list[str] = []
    previous_dash = False
    for char in text.lower():
        value = _PERSIAN_SLUG_CHARS.get(char, char)
        if re.match(r"[a-z0-9]", value):
            chars.append(value)
            previous_dash = False
        elif chars and not previous_dash:
            chars.append("-")
            previous_dash = True
    slug = "".join(chars).strip("-")
    return slug or "wiki-page"


_SYSTEM_PROMPT = """تو قطعه‌های آیین‌نامه آموزشی فارسی را به صفحه ویکی فارسی برای پرسش‌وپاسخ تبدیل می‌کنی.
فقط یک JSON object برگردان با کلیدهای title, slug, category, tags, aliases, summary, body, relationships, sources.
همه مقدارهای متنی باید فارسی باشند؛ از عنوان، دسته، برچسب، خلاصه یا متن انگلیسی استفاده نکن.
title باید عنوان دقیق و قابل جستجوی فارسی باشد، نه تکه ناقص OCR.
category را فارسی و کوتاه انتخاب کن.
tags و aliases را فارسی بنویس و عبارت‌های رایج دانشجویی را اضافه کن.
body را با همین بخش‌های فارسی بساز: ## حکم اصلی، ## شرایط، ## استثناها، ## اعداد و محدودیت‌ها، ## پرسش‌های قابل پاسخ.
شماره ماده/تبصره و عددهای قانونی را دقیق نگه دار.
هیچ ادعایی خارج از متن منبع اضافه نکن."""

_PERSIAN_SLUG_CHARS = {
    "آ": "a",
    "ا": "a",
    "ب": "b",
    "پ": "p",
    "ت": "t",
    "ث": "s",
    "ج": "j",
    "چ": "ch",
    "ح": "h",
    "خ": "kh",
    "د": "d",
    "ذ": "z",
    "ر": "r",
    "ز": "z",
    "ژ": "zh",
    "س": "s",
    "ش": "sh",
    "ص": "s",
    "ض": "z",
    "ط": "t",
    "ظ": "z",
    "ع": "a",
    "غ": "gh",
    "ف": "f",
    "ق": "gh",
    "ک": "k",
    "گ": "g",
    "ل": "l",
    "م": "m",
    "ن": "n",
    "و": "o",
    "ه": "h",
    "ی": "y",
}


if __name__ == "__main__":
    raise SystemExit(main())
