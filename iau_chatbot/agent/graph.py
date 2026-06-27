"""Question-answering graph over retrieved Obsidian wiki pages."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from iau_chatbot.retrieval.context import assemble_context
from iau_chatbot.retrieval.vector import retrieve

from .prompts import ANSWER_SYSTEM_PROMPT, EMPTY_QUESTION_ANSWER, NO_EVIDENCE_ANSWER
from .prompts import answer_user_prompt
from .state import AgentAnswer, AgentState, AnswerSource


class TextLLM(Protocol):
    """Text completion dependency used by the answer node."""

    def complete_text(self, *, system: str, user: str) -> str:
        """Return answer text for a chat-style prompt."""


_History = deque[tuple[str, str]]
_SESSION_HISTORY: defaultdict[str, _History] = defaultdict(lambda: deque(maxlen=6))


def answer_question(
    question: str,
    *,
    wiki_dir: Path,
    llm: TextLLM,
    session_id: str | None = None,
    top_k: int = 5,
) -> AgentAnswer:
    """Run the Phase 5 QA graph for one question."""

    nodes = _nodes(wiki_dir=wiki_dir, llm=llm, top_k=top_k)
    state: AgentState = {"question": question, "session_id": session_id, "errors": []}
    final = _compile_graph(nodes).invoke(state)
    result = AgentAnswer(
        answer=final.get("answer", NO_EVIDENCE_ANSWER),
        sources=final.get("sources", []),
        session_id=session_id,
        errors=final.get("errors", []),
    )
    if session_id and not result.errors:
        _SESSION_HISTORY[session_id].append((question.strip(), result.answer))
    return result


def _nodes(
    *, wiki_dir: Path, llm: TextLLM, top_k: int
) -> dict[str, Callable[[AgentState], AgentState]]:
    return {
        "validate_question": _validate_question,
        "retrieve_pages": lambda state: _retrieve_pages(state, wiki_dir=wiki_dir, top_k=top_k),
        "assemble_context": _assemble_context,
        "generate_answer": lambda state: _generate_answer(state, llm=llm),
        "attach_sources": _attach_sources,
    }


def _validate_question(state: AgentState) -> AgentState:
    if not state.get("question", "").strip():
        state["answer"] = EMPTY_QUESTION_ANSWER
        state["sources"] = []
        state["errors"] = ["empty_question"]
    return state


def _retrieve_pages(state: AgentState, *, wiki_dir: Path, top_k: int) -> AgentState:
    if state.get("errors"):
        return state
    query = state["question"]
    session_id = state.get("session_id")
    if session_id and _SESSION_HISTORY[session_id]:
        recent_questions = "\n".join(question for question, _ in _SESSION_HISTORY[session_id])
        query = f"{recent_questions}\n{query}"
    pages = retrieve(query, wiki_dir=wiki_dir, top_k=top_k)
    state["retrieved_pages"] = pages
    if not pages:
        state["answer"] = NO_EVIDENCE_ANSWER
        state["sources"] = []
        state["errors"] = ["no_retrieval_results"]
    return state


def _assemble_context(state: AgentState) -> AgentState:
    if state.get("errors"):
        return state
    state["context"] = assemble_context(state.get("retrieved_pages", []))
    return state


def _generate_answer(state: AgentState, *, llm: TextLLM) -> AgentState:
    if state.get("errors"):
        return state
    state["answer"] = llm.complete_text(
        system=ANSWER_SYSTEM_PROMPT,
        user=answer_user_prompt(
            question=state["question"],
            context=state.get("context", ""),
            history=_history_text(state.get("session_id")),
        ),
    ).strip()
    return state


def _attach_sources(state: AgentState) -> AgentState:
    if state.get("errors"):
        return state
    sources: list[AnswerSource] = []
    for page in state.get("retrieved_pages", []):
        for source_ref in page.sources:
            sources.append(
                AnswerSource(
                    wiki_page=page.source_path,
                    title=page.title,
                    source_ref=source_ref,
                    excerpt=(page.evidence or page.summary or page.body[:180])[:180],
                )
            )
    state["sources"] = sources
    return state


def _history_text(session_id: str | None) -> str:
    if not session_id:
        return ""
    turns = _SESSION_HISTORY[session_id]
    if not turns:
        return ""
    lines: list[str] = []
    for index, (question, answer) in enumerate(turns, start=1):
        lines.append(f"Turn {index} Q: {question}")
        lines.append(f"Turn {index} A: {answer}")
    return "\n".join(lines)


def _compile_graph(nodes: dict[str, Callable[[AgentState], AgentState]]):
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:
        return _SequentialGraph(nodes)

    graph = StateGraph(AgentState)
    for name, node in nodes.items():
        graph.add_node(name, node)
    graph.add_edge(START, "validate_question")
    graph.add_edge("validate_question", "retrieve_pages")
    graph.add_edge("retrieve_pages", "assemble_context")
    graph.add_edge("assemble_context", "generate_answer")
    graph.add_edge("generate_answer", "attach_sources")
    graph.add_edge("attach_sources", END)
    return graph.compile()


class _SequentialGraph:
    """Tiny fallback for test/dev environments without the optional LangGraph extra."""

    def __init__(self, nodes: dict[str, Callable[[AgentState], AgentState]]) -> None:
        self.nodes = nodes

    def invoke(self, state: AgentState) -> AgentState:
        for name in (
            "validate_question",
            "retrieve_pages",
            "assemble_context",
            "generate_answer",
            "attach_sources",
        ):
            state = self.nodes[name](state)
        return state
