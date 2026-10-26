#
#   test_issue794_environment_delete_hvo_offline.py
#
#   Offline ratchet for issue #794 EnvironmentOperations Delete HVO lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENV_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "EnvironmentOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue794_environment_delete_hvo_live.py"
)


def _block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    if next_def == -1:
        next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue794_delete_uses_hvo_membership():
    block = _block(ENV_OPS.read_text(encoding="utf-8"), "Delete")
    assert "issue #794" in block
    assert "int(slot.Hvo) == target_hvo" in block
    assert "EnvironmentsOS.Remove(env)" not in block


def test_issue794_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #794"
    body = LIVE_GATE.read_text(encoding="utf-8")
    assert "requires_live_project" in body
    assert "Delete" in body
