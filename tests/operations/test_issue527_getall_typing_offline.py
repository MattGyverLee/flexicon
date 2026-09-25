#
#   test_issue527_getall_typing_offline.py
#
#   Offline ratchet for issue #527 GetAll element typing (Overlay + MorphRule).
#
#   Copyright 2026
#

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OVERLAY_OPS = REPO_ROOT / "flexicon" / "code" / "Lists" / "OverlayOperations.py"
OVERLAY_PYI = REPO_ROOT / "flexicon" / "code" / "Lists" / "OverlayOperations.pyi"
MORPH_OPS = REPO_ROOT / "flexicon" / "code" / "Grammar" / "MorphRuleOperations.py"
MORPH_PYI = REPO_ROOT / "flexicon" / "code" / "Grammar" / "MorphRuleOperations.pyi"


def _overlay_getall_doc(text: str) -> str:
    start = text.index("def GetAll(self):")
    end = text.index("\n    @OperationsMethod", start + 1)
    return text[start:end]


def _morph_getall_doc(text: str) -> str:
    start = text.index("def GetAll(self):")
    end = text.index("\n    @OperationsMethod", start + 1)
    return text[start:end]


def test_issue527_overlay_getall_documents_icmoverlay():
    block = _overlay_getall_doc(OVERLAY_OPS.read_text(encoding="utf-8"))
    assert "Returns:" in block
    assert "list[ICmOverlay]" in block
    assert "OverlaysOC" in block


def test_issue527_overlay_pyi_comment_not_possibility_inheritance():
    body = OVERLAY_PYI.read_text(encoding="utf-8")
    assert "ICmPossibility" not in body
    assert "ICmOverlay" in body


def test_issue527_morph_getall_documents_enumerable_wrapper_union():
    block = _morph_getall_doc(MORPH_OPS.read_text(encoding="utf-8"))
    assert "EnumerableWrapper[CompoundRule | AffixTemplate]" in block
    assert "Generator[CompoundRule | AffixTemplate]" not in block


def test_issue527_morph_pyi_getall_typed_union():
    body = MORPH_PYI.read_text(encoding="utf-8")
    assert re.search(
        r"def GetAll\(self\) -> EnumerableWrapper\[Union\[CompoundRule, AffixTemplate\]\]",
        body,
    )
