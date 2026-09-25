#
#   test_issue449_wrapper_unwrap_offline.py
#
#   Offline ratchet for issue #449 (no FieldWorks / libmono required).
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def test_issue449_unwrap_helper_present_on_base_operations():
    src = (REPO_ROOT / "flexicon" / "code" / "BaseOperations.py").read_text(
        encoding="utf-8"
    )
    assert "def _UnwrapLcmObject(obj):" in src
    assert "lcm_object" in src
    assert "issue #449" in src


def test_issue449_shared_resolvers_call_unwrap():
    allo = (
        REPO_ROOT / "flexicon" / "code" / "Lexicon" / "AllomorphOperations.py"
    ).read_text(encoding="utf-8")
    pos = (REPO_ROOT / "flexicon" / "code" / "Grammar" / "POSOperations.py").read_text(
        encoding="utf-8"
    )
    assert "obj = self._UnwrapLcmObject(allomorph_or_hvo)" in allo
    assert "obj = self._UnwrapLcmObject(pos_or_hvo)" in pos


def test_issue449_live_gate_module_exists():
    live = REPO_ROOT / "tests" / "operations" / "test_issue449_getall_roundtrip_live.py"
    assert live.is_file()
    text = live.read_text(encoding="utf-8")
    assert "GetForm(item)" in text
    assert "GetSyncableProperties" in text
    assert "requires_live_project" in text
