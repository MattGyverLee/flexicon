#
#   test_issue481_lexref_resolver_cast_offline.py
#
#   Offline ratchet for issue #481 LexReferenceOperations HVO resolver casts.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LEX_REF_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexReferenceOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue481_lexref_resolver_cast_live.py"
)


def test_issue481_resolvers_use_cast_to_concrete():
    text = LEX_REF_OPS.read_text(encoding="utf-8")
    assert "from ..lcm_casting import cast_to_concrete" in text
    assert text.count("cast_to_concrete(self.project.Object") >= 4
    for helper in (
        "__ResolveRefType",
        "__ResolveLexRef",
        "__ResolveSenseOrEntry",
        "__ResolveEntry",
    ):
        assert f"def {helper}" in text
    assert "if not hasattr(obj, \"MappingType\")" not in text
    assert "if not hasattr(obj, \"TargetsRS\")" not in text


def test_issue481_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #481"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "GetMappingType" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
