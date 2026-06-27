"""Persian text normalization and regulation segment construction."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

HEADING_RE = re.compile(r"^(ماده|تبصره|فصل|بخش|آیین|آئين|شرایط|شرايط)\s*[۰-۹0-9]*")


@dataclass(frozen=True)
class PageText:
    """Text extracted from one PDF page."""

    page_number: int
    text: str


@dataclass(frozen=True)
class RegulationSegment:
    """Source-backed text segment ready for later Obsidian page generation."""

    source_path: str
    page_start: int
    page_end: int
    heading: str
    text: str
    source_ref: str
    content_hash: str


def normalize_persian_text(text: str) -> str:
    """Normalize common Arabic/Persian variants without changing meaning."""

    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "ي": "ی",
        "ك": "ک",
        "\u200f": "",
        "\u200e": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\u200c(?=\s)|(?<=\s)\u200c", "", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def build_segments(
    source_path: str,
    pages: list[PageText],
    *,
    max_words: int = 1200,
    min_words: int = 40,
) -> list[RegulationSegment]:
    """Build source-cited segments from extracted PDF pages."""

    segments: list[RegulationSegment] = []
    buffer: list[PageText] = []

    for page in pages:
        clean = normalize_persian_text(page.text)
        if not clean:
            continue
        candidate = PageText(page.page_number, clean)
        if buffer and _starts_new_section(clean):
            segments.append(_segment(source_path, buffer))
            buffer = [candidate]
            continue
        if buffer and _word_count(_join(buffer + [candidate])) > max_words:
            segments.append(_segment(source_path, buffer))
            buffer = [candidate]
        else:
            buffer.append(candidate)

        if _word_count(_join(buffer)) >= min_words:
            segments.append(_segment(source_path, buffer))
            buffer = []

    if buffer:
        if (
            segments
            and _word_count(_join(buffer)) < min_words
            and not _starts_new_section(buffer[0].text)
        ):
            previous = segments.pop()
            merged_pages = [
                PageText(previous.page_start, previous.text),
                *buffer,
            ]
            segments.append(_segment(source_path, merged_pages))
        else:
            segments.append(_segment(source_path, buffer))

    return segments


def _segment(source_path: str, pages: list[PageText]) -> RegulationSegment:
    text = _join(pages)
    page_start = pages[0].page_number
    page_end = pages[-1].page_number
    return RegulationSegment(
        source_path=source_path,
        page_start=page_start,
        page_end=page_end,
        heading=_heading(text),
        text=text,
        source_ref=_source_ref(source_path, page_start, page_end),
        content_hash="sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _join(pages: list[PageText]) -> str:
    return "\n\n".join(page.text.strip() for page in pages if page.text.strip())


def _heading(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if _is_page_number(clean) or not any(char.isalpha() for char in clean):
            continue
        if clean and (HEADING_RE.match(clean) or len(clean.split()) <= 8):
            return clean[:120]
    return "بخش بدون عنوان"


def _starts_new_section(text: str) -> bool:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return bool(first_line and HEADING_RE.match(first_line))


def _source_ref(source_path: str, page_start: int, page_end: int) -> str:
    page = str(page_start) if page_start == page_end else f"{page_start}-{page_end}"
    return f"{source_path}#page={page}"


def _word_count(text: str) -> int:
    return len(text.split())


def _is_page_number(text: str) -> bool:
    return bool(text) and all(char.isdigit() for char in text)
