#
#   test_issue880_infltype_feats_slots_sync_offline.py
#
#   Offline ratchet for issue #880 LexEntryInflType InflFeatsOA/SlotsRC sync.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
VARIANT_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "VariantOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue880_infltype_feats_slots_sync_live.py"
)


def _method_block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue880_get_type_syncable_properties_emits_infl_feats_and_slots():
    text = VARIANT_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "GetTypeSyncableProperties")
    assert "issue #880" in block
    assert "InflFeatsOA" in block
    assert '"InflFeats"' in block and '"InflFeatsGuid"' in block
    assert '"slots_rc"' in block
    assert "SlotsRC" in block


def test_issue880_apply_type_syncable_properties_pops_owned_keys():
    text = VARIANT_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "ApplyTypeSyncableProperties")
    assert "__TYPE_SYNC_INFLTYPE_KEYS" in block
    assert "__ApplyInflTypeInflFeats" in block
    assert "__ApplyInflTypeSlotsRC" in block


def test_issue880_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #880"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "InflFeats" in body or "slots_rc" in body
