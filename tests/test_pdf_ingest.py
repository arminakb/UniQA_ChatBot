"""Tests for PDF ingestion."""

from pathlib import Path

from iau_chatbot.ingest.pdf import extract_pdf_pages
from iau_chatbot.ingest.segments import build_segments


def test_extract_sample_pdf_preserves_persian_text() -> None:
    pages = extract_pdf_pages(Path("raw/Karshenasi.pdf"))

    assert len(pages) == 32
    text = "\n".join(page.text for page in pages)
    assert "کارشناسی" in text


def test_sample_pdf_builds_obsidian_ready_segments() -> None:
    pages = extract_pdf_pages(Path("raw/Karshenasi.pdf"))
    segments = build_segments("raw/Karshenasi.pdf", pages)

    assert segments
    assert all(segment.source_ref.startswith("raw/Karshenasi.pdf#page=") for segment in segments)
    assert all(len(segment.text.split()) <= 1200 for segment in segments)
