"""PDF text extraction using pdfplumber with a PyMuPDF fallback."""

from __future__ import annotations

from pathlib import Path

from iau_chatbot.exceptions import IngestionError

from .segments import PageText, normalize_persian_text


def extract_pdf_pages(path: Path) -> list[PageText]:
    """Extract page text from a PDF path."""

    if not path.exists():
        raise IngestionError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise IngestionError(f"Not a PDF file: {path}")

    pages = _best_pages(_extract_with_pdfplumber(path), _extract_with_pymupdf(path))
    if not any(page.text.strip() for page in pages):
        raise IngestionError(f"No extractable text found in PDF: {path}")
    return pages


def _best_pages(first: list[PageText], second: list[PageText]) -> list[PageText]:
    return max((first, second), key=_quality_score)


def _quality_score(pages: list[PageText]) -> int:
    text = "\n".join(page.text for page in pages[:3])
    return len(text.strip()) - text.count("�") * 100


def _extract_with_pdfplumber(path: Path) -> list[PageText]:
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise IngestionError("Install PDF dependencies with `pip install -e '.[pdf]'`") from exc

    with pdfplumber.open(path) as pdf:
        return [
            PageText(page_number=index, text=normalize_persian_text(page.extract_text() or ""))
            for index, page in enumerate(pdf.pages, start=1)
        ]


def _extract_with_pymupdf(path: Path) -> list[PageText]:
    try:
        import fitz
    except ModuleNotFoundError as exc:
        raise IngestionError("PyMuPDF fallback is unavailable; install `.[pdf]`") from exc

    with fitz.open(path) as doc:
        return [
            PageText(page_number=index, text=normalize_persian_text(page.get_text("text") or ""))
            for index, page in enumerate(doc, start=1)
        ]
