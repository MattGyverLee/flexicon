#
#   test_issue459_pronunciation_resolver_cast_offline.py
#
#   Offline ratchet for issue #459 PronunciationOperations HVO resolver casts.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PRON_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "PronunciationOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue459_pronunciation_resolver_cast_live.py"
)


def test_issue459_resolvers_use_cast_to_concrete():
    text = PRON_OPS.read_text(encoding="utf-8")
    assert "cast_to_concrete" in text
    assert text.count("cast_to_concrete(self.project.Object") >= 2
    for helper in (
        "__GetPronunciationObject",
        "__GetEntryObject",
    ):
        assert f"def {helper}" in text
    assert "return self.project.Object(pronunciation_or_hvo)" not in text
    assert "return self.project.Object(entry_or_hvo)" not in text


def test_issue459_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #459"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "GetForm" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
