#
#   test_issue698_wfimorphbundle_reorder_hvo_offline.py
#
#   Offline ratchet for issue #698 WfiMorphBundle Reorder HVO membership partition.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BUNDLE_OPS = REPO_ROOT / "flexicon" / "code" / "TextsWords" / "WfiMorphBundleOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue698_wfimorphbundle_reorder_hvo_live.py"
)


def _reorder_block(text: str) -> str:
    start = text.index("def Reorder(self, analysis_or_hvo, bundle_list):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue698_reorder_partitions_by_hvo():
    block = _reorder_block(BUNDLE_OPS.read_text(encoding="utf-8"))
    assert "issue #698" in block
    assert "bundle_by_hvo" in block
    assert "current_bundles = set(analysis.MorphBundlesOS)" not in block
    assert "new_bundles = set(bundle_list)" not in block


def test_issue698_reorder_builds_desired_order_from_sequence_members():
    block = _reorder_block(BUNDLE_OPS.read_text(encoding="utf-8"))
    assert "desired_order = [bundle_by_hvo[hvo]" in block


def test_issue698_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #698"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Reorder" in body
