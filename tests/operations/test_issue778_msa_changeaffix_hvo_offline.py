#
#   test_issue778_msa_changeaffix_hvo_offline.py
#
#   Offline ratchet for issue #778 ChangeAffixVariant RC copy HVO lookup.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MSA_OPS = REPO_ROOT / "flexicon" / "code" / "Lexicon" / "MSAOperations.py"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue778_msa_changeaffix_hvo_live.py"
)


def _method_block(text: str, name: str) -> str:
    start = text.index(f"def {name}")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def] if next_def != -1 else text[start:]


def test_issue778_changeaffixvariant_copy_uses_hvo_membership():
    text = MSA_OPS.read_text(encoding="utf-8")
    block = _method_block(text, "ChangeAffixVariant")
    assert "issue #778" in block
    assert "feat not in new_rc" not in block
    assert "int(feat.Hvo)" in block or "int(item.Hvo)" in block


def test_issue778_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "live gate module missing for issue #778"
