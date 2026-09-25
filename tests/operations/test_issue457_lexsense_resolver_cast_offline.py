#
#   test_issue457_lexsense_resolver_cast_offline.py
#
#   Offline ratchet for issue #457 LexSenseOperations HVO resolver casts.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LEX_SENSE_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexSenseOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue457_lexsense_resolver_cast_live.py"
)


def test_issue457_resolvers_use_cast_to_concrete():
    text = LEX_SENSE_OPS.read_text(encoding="utf-8")
    assert "cast_to_concrete" in text
    assert text.count("cast_to_concrete(self.project.Object") >= 3
    for helper in (
        "__GetSenseObject",
        "__GetEntryObject",
        "__GetSemanticDomainObject",
    ):
        assert f"def {helper}" in text
    assert "return self.project.Object(sense_or_hvo)" not in text
    assert "return self.project.Object(entry_or_hvo)" not in text
    assert "return self.project.Object(domain_or_hvo)" not in text


def test_issue457_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #457"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "Gloss" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
