#
#   test_issue533_wfimorphbundle_duplicate_hvo_offline.py
#
#   Offline ratchet for issue #533 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BUNDLE_OPS = (
    REPO_ROOT
    / "flexicon"
    / "code"
    / "TextsWords"
    / "WfiMorphBundleOperations.py"
)
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue533_wfimorphbundle_duplicate_hvo_live.py"
)


def _duplicate_block(text: str) -> str:
    start = text.index("def Duplicate")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue533_duplicate_insert_after_uses_hvo_index():
    block = _duplicate_block(BUNDLE_OPS.read_text(encoding="utf-8"))
    assert "issue #533" in block
    assert "b.Hvo == target_hvo" in block
    assert "bundle_list.index(source)" not in block
    assert "MorphBundlesOS).index(source)" not in block


def test_issue533_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #533"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Duplicate" in body
