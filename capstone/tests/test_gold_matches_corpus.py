"""The answer key must describe the corpus that exists.

gold.yml is the eval harness's ground truth AND the index every lesson cites
when it points at a moment in Priya's history. A row that quotes a phrase the
corpus does not contain is a broken citation and a broken eval, and neither
shows up until something reads that specific row.

So: every phrase, surface form, and quoted value in gold.yml must appear
verbatim in the corpus. The corpus is byte-stable on purpose -- dozens of ranks
pinned across the Beginner track depend on it -- so when these disagree, the
answer key is what changes.
"""
from __future__ import annotations

import re

import pytest
from memlab.fixtures import load_agent_writes, load_gold, load_turns

GOLD = load_gold()
CORPUS = " ".join(t["text"] for t in load_turns())
AGENT_TEXT = " ".join(w["text"] for w in load_agent_writes())
SESSIONS = {t["session"] for t in load_turns()}


def session_text(n: int, agent: str | None = None) -> str:
    """Everything written in a session -- by the user, or by a named agent.

    Agent writes live in their own fixture, so a gold row that names one has
    to be checked against that file. Without the `written_by` branch the only
    way to make such a row pass is to point it at a session it is not in.
    """
    if agent:
        return " ".join(
            w["text"] for w in load_agent_writes()
            if w["session"] == n and w["agent"] == agent
        )
    return " ".join(t["text"] for t in load_turns() if t["session"] == n)


@pytest.mark.parametrize("row", GOLD["relative_time"], ids=lambda r: r["phrase"])
def test_relative_time_phrases_are_real(row) -> None:
    where = session_text(row["session"], row.get("written_by"))
    assert row["phrase"] in where, (
        f"{row['phrase']!r} is not in session {row['session']}"
        f"{' (' + row['written_by'] + ')' if row.get('written_by') else ''}"
    )


def appears(needle: str, haystack: str) -> bool:
    """Whole-word, case-insensitive: a surface form at the start of a sentence
    is the same surface form."""
    return re.search(rf"\b{re.escape(needle)}\b", haystack, re.IGNORECASE) is not None


@pytest.mark.parametrize("entity", GOLD["entities"], ids=lambda e: e["canonical"])
def test_entity_surface_forms_are_real(entity) -> None:
    for form in entity["surface_forms"]:
        assert appears(form, CORPUS), f"surface form {form!r} never appears in the corpus"


@pytest.mark.parametrize("entity", GOLD["entities"], ids=lambda e: e["canonical"])
def test_entity_sessions_actually_mention_it(entity) -> None:
    for n in entity["sessions"]:
        text = session_text(n)
        assert any(appears(f, text) for f in entity["surface_forms"]), (
            f"session {n} is listed for {entity['canonical']} but names none of its forms"
        )


@pytest.mark.parametrize("row", GOLD["pii"], ids=lambda r: r["kind"])
def test_pii_values_are_real(row) -> None:
    assert row["value"] in session_text(row["session"]) or row["value"] in CORPUS


def test_supersession_values_are_real() -> None:
    for row in GOLD["supersessions"]:
        for key in ("original", "replacement", "addition"):
            if (side := row.get(key)) and "session" in side:
                assert side["session"] in SESSIONS


def test_procedure_steps_are_real() -> None:
    for proc in GOLD["procedures"]:
        taught = session_text(proc["taught_session"])
        for step in proc["ordered_steps"]:
            head = step.split()[0]
            assert head.lower() in taught.lower(), f"step {step!r} not taught in transcript"
        assert proc["critical_step"] in proc["ordered_steps"]


def test_every_referenced_session_exists() -> None:
    def sessions(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "session" and isinstance(v, int) or k in ("taught_session", "invoked_session"):
                    yield v
                else:
                    yield from sessions(v)
        elif isinstance(node, list):
            for item in node:
                yield from sessions(item)

    for n in sessions(GOLD):
        assert n in SESSIONS, f"gold.yml references session {n}, which does not exist"


def test_shared_memory_rows_match_the_agent_writes() -> None:
    agents = {w["agent"] for w in load_agent_writes()}
    for row in GOLD["shared_memory"]:
        assert row["agent"] in agents
    assert "Berlin" in AGENT_TEXT, "the hearsay case must actually be in the fixture"


def test_the_final_exam_answer_is_supported_by_the_corpus() -> None:
    exam = GOLD["final_question"]
    assert exam["asks"] in session_text(exam["session"])
    assert exam["correct_answer"]["employer"] in CORPUS
    for item in exam["correct_answer"]["permitted"]:
        assert item in CORPUS
