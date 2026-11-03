#
#   test_issue876_phon_gloss_sync_offline.py
#
#   Offline ratchet for issue #876 gloss fields in GetSyncableProperties.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PHON_OPS = (
    REPO_ROOT
    / "flexicon"
    / "code"
    / "Grammar"
    / "PhonFeatureOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue876_phon_gloss_sync_live.py"
)


def _get_sync_block(text: str) -> str:
    start = text.index("def GetSyncableProperties(self, item):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue876_gloss_fields_emitted_in_get_syncable_properties():
    block = _get_sync_block(PHON_OPS.read_text(encoding="utf-8"))
    assert "issue #876" in block
    assert "GlossAbbreviation" in block
    assert "RightGlossSep" in block
    assert "ShowInGloss" in block
    assert "__ReadMultiString" in block
    assert 'props["ShowInGloss"]' in block or "props[\"ShowInGloss\"]" in block


def test_issue876_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #876"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GlossAbbreviation" in body
    assert "ShowInGloss" in body
