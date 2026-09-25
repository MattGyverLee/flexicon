#
#   test_issue231_allomorph_remove_orphaned_offline.py
#
#   Offline ratchet for issue #231 live RemoveOrphaned gate (slice 3).
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LIVE_MODULE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue231_allomorph_remove_orphaned_live.py"
)


def test_issue231_live_remove_orphaned_module_exists():
    assert LIVE_MODULE.is_file(), "missing live RemoveOrphaned module for #231"
    text = LIVE_MODULE.read_text(encoding="utf-8")
    assert "RemoveOrphaned" in text
    assert "duplicate_lexeme" in text
    assert "AlternateFormsOS.Add(lexeme)" in text
    assert "isinstance(entry_hvo, int)" in text
    assert "requires_live_project" in text
    assert "target_sandbox" in text
