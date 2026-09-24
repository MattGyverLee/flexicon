#
#   test_issue455_example_resolver_cast_offline.py
#
#   Offline ratchet for issue #455 ExampleOperations HVO resolver casts.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXAMPLE_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "ExampleOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue455_example_resolver_cast_live.py"
)


def test_issue455_resolvers_use_cast_to_concrete():
    text = EXAMPLE_OPS.read_text(encoding="utf-8")
    assert "from ..lcm_casting import cast_to_concrete" in text
    assert text.count("cast_to_concrete(self.project.Object") >= 2
    assert "def __GetExampleObject" in text
    assert "def __GetSenseObject" in text
    assert "return self.project.Object(example_or_hvo)" not in text
    assert "return self.project.Object(sense_or_hvo)" not in text


def test_issue455_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #455"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "DoNotPublishInRC" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
