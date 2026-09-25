#
#   test_issue493_scripture_resolver_cast_offline.py
#
#   Offline ratchet for issue #493 Scripture HVO resolver casts.
#
#   Copyright 2026
#

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPTURE = REPO_ROOT / "flexicon" / "code" / "Scripture"
LIVE_GATE = (
    REPO_ROOT
    / "tests"
    / "operations"
    / "test_issue493_scripture_resolver_cast_live.py"
)

RESOLVER_FILES = (
    ("ScrSectionOperations.py", "__ResolveBook"),
    ("ScrTxtParaOperations.py", "__ResolveSection"),
    ("ScrNoteOperations.py", "__ResolveBook"),
    ("ScrAnnotationsOperations.py", "__ResolveBook"),
)


def test_issue493_resolvers_use_cast_to_concrete():
    for filename, helper in RESOLVER_FILES:
        text = (SCRIPTURE / filename).read_text(encoding="utf-8")
        assert "from ..lcm_casting import cast_to_concrete" in text
        assert f"def {helper}" in text
        assert "cast_to_concrete(self.project.Object" in text
        assert "return cast_to_concrete(" in text
        # HVO branch must not return bare project.Object
        helper_start = text.index(f"def {helper}")
        next_def = text.find("\n    def ", helper_start + 1)
        block = text[helper_start:next_def] if next_def != -1 else text[helper_start:]
        assert "return self.project.Object(" not in block


def test_issue493_live_gate_module_exists():
    assert LIVE_GATE.is_file(), "missing live gate module for #493"
    text = LIVE_GATE.read_text(encoding="utf-8")
    assert "GetAll" in text
    assert "isinstance(hvo, int)" in text
    assert "requires_live_project" in text
