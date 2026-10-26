#
#   test_issue640_getbeststring_offline.py
#
#   Offline ratchet for issue #640 GetBestString multistring validation.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WS_OPS = REPO_ROOT / "flexicon" / "code" / "System" / "WritingSystemOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue640_getbeststring_live.py"
)


def _get_best_string_block(text: str) -> str:
    start = text.index("def GetBestString")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue640_get_best_string_uses_is_instance_of_type():
    block = _get_best_string_block(WS_OPS.read_text(encoding="utf-8"))
    assert "issue #640" in block
    assert "IMultiUnicode.IsInstanceOfType" in block
    assert "IMultiString.IsInstanceOfType" in block
    assert "isinstance(string_obj" not in block
    assert "best_text(string_obj)" in block


def test_issue640_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #640"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "GetBestString" in body
