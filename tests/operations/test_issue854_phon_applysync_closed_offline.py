#
#   test_issue854_phon_applysync_closed_offline.py
#
#   Offline ratchet for issue #854 ApplySyncableProperties cast guard.
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
    / "test_issue854_phon_applysync_closed_live.py"
)


def _apply_sync_block(text: str) -> str:
    start = text.index("def ApplySyncableProperties(self, item, props, ws_map=None")
    next_def = text.find("\n    def __ApplyValues", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue854_apply_sync_cast_guard_is_narrow():
    block = _apply_sync_block(PHON_OPS.read_text(encoding="utf-8"))
    assert "issue #854" in block
    assert "except (AttributeError, System.InvalidCastException):" in block
    assert "except Exception:" not in block
    assert "ApplySyncableProperties requires an IFsClosedFeature" in block


def test_issue854_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #854"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "ApplySyncableProperties" in body
