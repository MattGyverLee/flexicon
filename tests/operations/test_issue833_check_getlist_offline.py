#
#   test_issue833_check_getlist_offline.py
#
#   Offline ratchet for issue #833 CheckOperations._GetCheckList / GetCheckList.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CHECK_OPS = REPO_ROOT / "flexicon" / "code" / "System" / "CheckOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue833_check_getlist_live.py"
)


def _get_check_list_block(text: str) -> str:
    start = text.index("def _GetCheckList")
    end = text.index("def _GetOrCreateCheckList", start)
    return text[start:end]


def _get_or_create_block(text: str) -> str:
    start = text.index("def _GetOrCreateCheckList")
    next_def = text.find("\n    def _GetDefaultCheckTargets", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue833_get_check_list_uses_langproject_checklistsoc():
    text = CHECK_OPS.read_text(encoding="utf-8")
    block = _get_check_list_block(text)
    assert "# Issue #833" in block
    assert "CheckListsOC" in block
    assert "Implementation would depend on actual FLEx data model" not in block


def test_issue833_get_or_create_registers_list_on_checklistsoc():
    block = _get_or_create_block(CHECK_OPS.read_text(encoding="utf-8"))
    assert "CheckListsOC.Add" in block
    assert "(issue #833)" in block


def test_issue833_public_get_check_list_exists():
    text = CHECK_OPS.read_text(encoding="utf-8")
    assert "def GetCheckList(self):" in text
    assert "@OperationsMethod" in text.split("def GetCheckList")[0][-200:]


def test_issue833_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #833"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetCheckList" in body
    assert "GetAllCheckTypes" in body
