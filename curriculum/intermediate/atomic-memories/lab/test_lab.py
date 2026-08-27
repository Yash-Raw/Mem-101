"""Atomicity, and the case where the rule is correctly broken. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import get
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

atomise = _solution.atomise
audit_atomicity = _solution.audit_atomicity
is_atomic = _solution.is_atomic


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("atom") / "m.jsonl")
    ingest(store, Scope(user="priya"), get("intermediate"))
    return store.all()


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.atomise("anything", MemoryType.SEMANTIC)


def test_the_transform_actually_fires() -> None:
    """Verified on constructed input, not only on a corpus where it no-ops."""
    parts = atomise("Priya eats fish, and she does not eat meat", MemoryType.SEMANTIC)
    assert parts == ["Priya eats fish", "she does not eat meat"]


def test_a_single_claim_is_left_alone() -> None:
    assert atomise("Priya works at Calico Systems", MemoryType.SEMANTIC) == [
        "Priya works at Calico Systems"
    ]


def test_procedures_are_exempt_by_type() -> None:
    """Same text, different type, opposite outcome.

    Needs a case the conjunction rule would genuinely split -- so the exemption
    is doing the work, not the lookahead.
    """
    text = "Priya pulls the metrics, and she diffs against last week"
    assert len(atomise(text, MemoryType.SEMANTIC)) == 2
    assert len(atomise(text, MemoryType.PROCEDURAL)) == 1


def test_two_independent_guards_protect_a_procedure() -> None:
    """The lookahead and the type exemption overlap on purpose.

    "pull metrics, and diff against last week" is safe even typed SEMANTIC,
    because the clause after `and` has no subject. The type exemption is the
    second line of defence, for procedures phrased with one.
    """
    no_subject = "pull pipeline metrics, and diff against last week"
    assert len(atomise(no_subject, MemoryType.SEMANTIC)) == 1      # lookahead
    with_subject = "Priya pulls metrics, and she diffs the numbers"
    assert len(atomise(with_subject, MemoryType.SEMANTIC)) == 2    # would split
    assert len(atomise(with_subject, MemoryType.PROCEDURAL)) == 1  # type saves it


def test_the_corpus_audits_clean(memories) -> None:
    audit = audit_atomicity(memories)
    assert audit.total == 38
    assert audit.compound == []


def test_the_longest_record_is_the_procedure_and_stays_whole(memories) -> None:
    n, kind, content = audit_atomicity(memories).longest
    assert kind == "procedural"
    assert n > 150
    assert is_atomic(content, MemoryType.PROCEDURAL)
