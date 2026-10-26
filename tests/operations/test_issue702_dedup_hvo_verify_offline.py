#
#   test_issue702_dedup_hvo_verify_offline.py
#
#   Offline ratchet for issue #702 merge dedup post-Remove HVO verification.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRY_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexEntryOperations.py"
SENSE_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexSenseOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue702_dedup_hvo_verify_live.py"
)


def _dedup_pron_block(text: str) -> str:
    start = text.index("def __DeduplicatePronunciationsInEntry(self, entry):")
    next_def = text.find("\n    def __DeduplicateAllomorphsInEntry", start + 1)
    return text[start:next_def]


def _dedup_allo_block(text: str) -> str:
    start = text.index("def __DeduplicateAllomorphsInEntry(self, entry):")
    next_def = text.find("\n    # --- Private Helper Methods ---", start + 1)
    return text[start:next_def]


def _dedup_example_block(text: str) -> str:
    start = text.index("def __DeduplicateExamplesInSense(self, sense):")
    next_def = text.find("\n    # --- Private Helper Methods ---", start + 1)
    return text[start:next_def]


def test_issue702_entry_ops_uses_hvo_membership_helper():
    text = ENTRY_OPS.read_text(encoding="utf-8")
    assert "issue #702" in text
    assert "__OwningSequenceContainsHvo" in text
    pron = _dedup_pron_block(text)
    allo = _dedup_allo_block(text)
    assert "dupe not in entry.PronunciationsOS" not in pron
    assert "dupe not in entry.AlternateFormsOS" not in allo
    assert "__OwningSequenceContainsHvo" in pron
    assert "__OwningSequenceContainsHvo" in allo


def test_issue702_sense_ops_example_dedup_uses_hvo_membership():
    text = SENSE_OPS.read_text(encoding="utf-8")
    block = _dedup_example_block(text)
    assert "issue #702" in block
    assert "__OwningSequenceContainsHvo" in block
    assert "dupe not in sense.ExamplesOS" not in block


def test_issue702_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #702"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "MergeObject" in body
