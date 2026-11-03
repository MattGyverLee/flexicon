#
#   test_issue860_phon_getsync_closed_offline.py
#
#   Offline ratchet for issue #860 GetSyncableProperties cast guard.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PHON_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "PhonFeatureOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue860_phon_getsync_closed_live.py"
)


def _get_sync_block(text: str) -> str:
    start = text.index("def GetSyncableProperties(self, item):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue860_get_sync_cast_guard_present():
    block = _get_sync_block(PHON_OPS.read_text(encoding="utf-8"))
    assert "issue #860" in block
    assert "except (AttributeError, System.InvalidCastException):" in block
    assert "GetSyncableProperties requires an IFsClosedFeature" in block
    guard_pos = block.index("issue #860")
    values_pos = block.index("for raw in feat.ValuesOC:")
    assert guard_pos < values_pos


def test_issue860_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #860"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetSyncableProperties" in body
