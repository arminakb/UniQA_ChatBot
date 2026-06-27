"""Metadata-first retrieval for Persian academic regulation wiki pages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from iau_chatbot.ingest.segments import normalize_persian_text

from .lexical import RetrievedPage, _read_pages, _terms


@dataclass(frozen=True)
class QueryMetadata:
    """Deterministic metadata extracted from a Persian student question."""

    topics: set[str]
    actions: set[str]
    constraints: set[str]
    aliases: set[str]


def retrieve(question: str, *, wiki_dir: Path, top_k: int = 5) -> list[RetrievedPage]:
    """Return pages ranked by query metadata first, then lexical overlap."""

    query = extract_query_metadata(question)
    query_terms = _terms(" ".join([question, *query.aliases, *query.topics, *query.actions]))
    if not query_terms and not query.aliases:
        return []

    ranked: list[RetrievedPage] = []
    for page in _read_pages(wiki_dir):
        text = " ".join(
            [page.title, page.category, *page.tags, *page.aliases, page.summary, page.body]
        )
        text_terms = _terms(text)
        overlap = query_terms & text_terms
        metadata_score = _metadata_score(query, page)
        if not overlap and metadata_score <= 0:
            continue
        evidence = _best_evidence(query, question, query_terms, page.summary, page.body)
        score = (
            metadata_score
            + _phrase_hint_score(query, f"{page.title} {page.summary} {page.body}")
            + (len(overlap) / max(len(query_terms), 1))
        )
        ranked.append(
            RetrievedPage(
                title=page.title,
                source_path=page.source_path,
                category=page.category,
                tags=page.tags,
                aliases=page.aliases,
                summary=page.summary,
                body=page.body,
                sources=page.sources,
                score=score,
                evidence=evidence,
            )
        )
    return sorted(ranked, key=lambda page: (-page.score, page.title))[:top_k]


def extract_query_metadata(question: str) -> QueryMetadata:
    """Extract deterministic topic/action aliases from common Persian wording."""

    text = normalize_persian_text(question).lower()
    topics: set[str] = set()
    actions: set[str] = set()
    constraints: set[str] = set()
    aliases: set[str] = set()

    for topic, patterns in _TOPIC_PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            topics.add(topic)
            aliases.update(patterns)

    if "معدل" in text and ("کمتر از 12" in text or "کمتر از ۱۲" in text):
        topics.add("probation")
        aliases.update(_TOPIC_PATTERNS["probation"])

    if "بردار" in text or "اخذ" in text or "انتخاب واحد" in text:
        actions.add("choose-units")
        aliases.add("انتخاب واحد")
    if "حذف درس" in text or "حذف اضطراری" in text:
        actions.add("withdraw-course")
        aliases.update({"حذف درس", "حذف اضطراری"})
    if "حذف ترم" in text or "حذف کلیه" in text or "حذف همه" in text:
        actions.add("withdraw-term")
        aliases.update({"حذف ترم", "حذف کلیه دروس", "حذف کلیه واحدها"})
    if "مرخص" in text:
        actions.add("take-leave")
        aliases.add("مرخصی تحصیلی")
    if "فارغ" in text or "فراغت" in text:
        actions.add("graduate")
        aliases.update({"فارغ التحصیلی", "فراغت از تحصیل"})

    if "ترم" in text or "نیمسال" in text:
        constraints.add("semester")
        aliases.add("نیمسال")
    if "تابستان" in text:
        constraints.add("summer")
        aliases.add("دوره تابستانی")
    if "آخرین" in text:
        constraints.add("final-semester")
        aliases.add("نیمسال آخر")
    if "کارشناسی" in text:
        constraints.add("undergraduate")
        aliases.add("کارشناسی")

    return QueryMetadata(topics, actions, constraints, aliases)


def _metadata_score(query: QueryMetadata, page: object) -> float:
    page_terms = _terms(
        " ".join(
            [
                getattr(page, "title", ""),
                getattr(page, "category", ""),
                *getattr(page, "tags", []),
                *getattr(page, "aliases", []),
                getattr(page, "summary", ""),
            ]
        )
    )
    page_alias_terms = _terms(" ".join(getattr(page, "aliases", [])))
    score = 0.0
    for topic in query.topics:
        topic_terms = _terms(topic + " " + " ".join(_TOPIC_PATTERNS.get(topic, ())))
        if page_terms & topic_terms:
            score += 2.0
        if page_alias_terms & topic_terms:
            score += 1.5
    for action in query.actions:
        action_terms = _terms(action + " " + " ".join(_ACTION_ALIASES.get(action, ())))
        if page_terms & action_terms:
            score += 1.5
    for constraint in query.constraints:
        constraint_terms = _terms(
            constraint + " " + " ".join(_CONSTRAINT_ALIASES.get(constraint, ()))
        )
        if page_terms & constraint_terms:
            score += 0.5
    return score


def _best_evidence(
    query: QueryMetadata, question: str, query_terms: set[str], summary: str, body: str
) -> str:
    candidates = [summary.strip()]
    candidates.extend(line.strip() for line in body.splitlines() if line.strip())
    flat_body = body.replace("\n", " ")
    candidates.extend(part.strip() for part in flat_body.split(".") if part.strip())
    candidates.extend(part.strip() for part in flat_body.split("۔") if part.strip())
    candidates.extend(_rule_chunks(flat_body))
    ranked = sorted(
        (candidate for candidate in candidates if candidate),
        key=lambda candidate: _evidence_key(query, question, query_terms, candidate),
    )
    return ranked[0][:700] if ranked else summary or body[:700]


def _rule_chunks(text: str) -> list[str]:
    chunks = re.split(r"(?=\b(?:ماده|تبصره)\s*[۰-۹0-9]*)", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _evidence_key(
    query: QueryMetadata, question: str, query_terms: set[str], candidate: str
) -> tuple[int, float, int, int, int]:
    phrase_score = _phrase_hint_score(query, candidate)
    numeric_score = _numeric_hint_score(question, candidate)
    overlap = len(query_terms & _terms(candidate))
    if phrase_score:
        return (0, -phrase_score, -numeric_score, len(candidate), -overlap)
    return (1, -overlap, -numeric_score, len(candidate), 0)


def _numeric_hint_score(question: str, candidate: str) -> int:
    question_terms = _terms(question)
    candidate_terms = _terms(candidate)
    return len(question_terms & candidate_terms & {"12", "۱۴", "14", "۲۰", "20", "۳", "3"})


def _phrase_hint_score(query: QueryMetadata, text: str) -> float:
    normalized = normalize_persian_text(text).lower()
    score = 0.0
    for topic in query.topics:
        if topic == "units" and "probation" in query.topics:
            continue
        score += sum(2.0 for phrase in _ANSWER_HINTS.get(topic, ()) if phrase in normalized)
    for action in query.actions:
        score += sum(2.0 for phrase in _ANSWER_HINTS.get(action, ()) if phrase in normalized)
    return score


_TOPIC_PATTERNS: dict[str, tuple[str, ...]] = {
    "units": ("سقف واحد", "واحد مجاز", "واحد", "انتخاب واحد"),
    "probation": ("مشروط", "مشروطی", "معدل کمتر از 12", "معدل کمتر از ۱۲", "کمتر از ۱۲"),
    "course-withdrawal": ("حذف درس", "حذف اضطراری"),
    "term-withdrawal": ("حذف ترم", "حذف کلیه", "حذف همه"),
    "leave-of-absence": ("مرخصی", "مرخصی تحصیلی"),
    "exam-absence": ("غیبت امتحان", "غیبت در امتحان", "امتحان پایان ترم", "نمره صفر"),
    "passing-grade": ("نمره قبولی", "قبولی"),
    "graduation": ("فارغ التحصیلی", "فراغت از تحصیل"),
    "transfer": ("انتقال", "مهمانی", "میهمان"),
}

_ANSWER_HINTS: dict[str, tuple[str, ...]] = {
    "units": ("20 واحد", "۲۰ واحد", "از 20 واحد بیشتر", "از ۲۰ واحد بیشتر"),
    "probation": ("حق انتخاب بیش از 14", "حق انتخاب بیش از ۱۴"),
    "course-withdrawal": ("حذف اضطراری", "course withdrawal", "withdraw from selected courses"),
    "term-withdrawal": ("حذف کلیه واحد", "complete withdrawal", "withdrawal from all"),
    "exam-absence": ("نمره صفر", "score of zero"),
    "withdraw-course": ("حذف اضطراری", "course withdrawal", "withdraw from selected courses"),
    "withdraw-term": ("حذف کلیه واحد", "complete withdrawal", "withdrawal from all"),
}

_ACTION_ALIASES: dict[str, tuple[str, ...]] = {
    "choose-units": ("انتخاب واحد", "اخذ واحد"),
    "withdraw-course": ("حذف درس", "حذف اضطراری"),
    "withdraw-term": ("حذف ترم", "حذف کلیه دروس", "حذف کلیه واحدها"),
    "take-leave": ("مرخصی تحصیلی",),
    "graduate": ("فارغ التحصیلی", "فراغت از تحصیل"),
}

_CONSTRAINT_ALIASES: dict[str, tuple[str, ...]] = {
    "semester": ("نیمسال", "ترم"),
    "summer": ("تابستان", "دوره تابستانی"),
    "final-semester": ("نیمسال آخر", "آخرین نیمسال"),
    "undergraduate": ("کارشناسی",),
}
