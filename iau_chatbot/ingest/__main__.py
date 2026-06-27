"""Dry-run CLI for PDF ingestion."""

from __future__ import annotations

import argparse
from pathlib import Path

from iau_chatbot.config import Settings
from iau_chatbot.logging import configure_logging

from .pdf import extract_pdf_pages
from .segments import build_segments


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m iau_chatbot.ingest")
    parser.add_argument("--env-file", default=".env", help="Path to the environment file.")
    parser.add_argument("--dry-run", action="store_true", help="Print segment summary only.")
    args = parser.parse_args()

    settings = Settings.from_env(args.env_file)
    logger = configure_logging(settings.log_level)
    pdfs = sorted(settings.pdf_dir.glob("*.pdf"))
    total_segments = 0

    for pdf in pdfs:
        rel_path = _display_path(pdf)
        pages = extract_pdf_pages(pdf)
        segments = build_segments(rel_path, pages)
        total_segments += len(segments)
        logger.info("{}: {} pages, {} segments", rel_path, len(pages), len(segments))
        if args.dry_run:
            for segment in segments:
                logger.info(
                    "segment pages={} ref={} heading={}",
                    f"{segment.page_start}-{segment.page_end}",
                    segment.source_ref,
                    segment.heading,
                )

    logger.info("PDFs processed: {}, total segments: {}", len(pdfs), total_segments)
    return 0


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
