#
#   test_issue740_allomorph_rc_hvo_offline.py
#
#   Offline ratchet for issue #740 Allomorph RC HVO membership lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ALLO_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "AllomorphOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue740_allomorph_rc_hvo_live.py"
)


def _remove_phone_env_block(text: str) -> str:
    start = text.index("def RemovePhoneEnv(self, allomorph_or_hvo, env_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _add_infl_block(text: str) -> str:
    start = text.index("def AddInflectionClass(self, allo_or_hvo, infl_class_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def _remove_infl_block(text: str) -> str:
    start = text.index("def RemoveInflectionClass(self, allo_or_hvo, infl_class_or_hvo):")
    next_def = text.find("\n    @OperationsMethod", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue740_remove_phoneenv_uses_hvo_membership():
    block = _remove_phone_env_block(ALLO_OPS.read_text(encoding="utf-8"))
    assert "issue #740" in block
    assert "linked.Hvo) == target_hvo" in block
    assert "env in allomorph.PhoneEnvRC" not in block


def test_issue740_inflection_class_mutators_use_hvo_membership():
    text = ALLO_OPS.read_text(encoding="utf-8")
    add_block = _add_infl_block(text)
    remove_block = _remove_infl_block(text)
    assert "issue #740" in add_block
    assert "linked.Hvo) == target_hvo" in add_block
    assert "infl_class not in allomorph.InflectionClassesRC" not in add_block
    assert "issue #740" in remove_block
    assert "infl_class in allomorph.InflectionClassesRC" not in remove_block


def test_issue740_live_gate_module_exists():
    assert LIVE_GATE.is_file()
