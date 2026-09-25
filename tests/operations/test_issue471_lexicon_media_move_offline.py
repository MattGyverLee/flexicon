#
#   test_issue471_lexicon_media_move_offline.py
#
#   Offline coverage for issue #471: Lexicon MoveMediaFile / MovePicture
#   must re-parent via Add only (never Remove-then-Add).
#
#   Platform: Python 3.8+
#   Copyright 2026
#

import ast
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]

_MOVE_SITES = (
    (
        _REPO_ROOT / "flexicon" / "code" / "Lexicon" / "ExampleOperations.py",
        "ExampleOperations",
        "MoveMediaFile",
        "media",
    ),
    (
        _REPO_ROOT / "flexicon" / "code" / "Lexicon" / "PronunciationOperations.py",
        "PronunciationOperations",
        "MoveMediaFile",
        "media",
    ),
    (
        _REPO_ROOT / "flexicon" / "code" / "Lexicon" / "LexSenseOperations.py",
        "LexSenseOperations",
        "MovePicture",
        "picture",
    ),
)


def _method_source(path: Path, class_name: str, method_name: str) -> str:
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == method_name:
                return ast.get_source_segment(source, item) or ""
    raise AssertionError(f"{class_name}.{method_name} not found in {path}")


class TestIssue471MoveRatchet:
    @pytest.mark.parametrize(
        "path,class_name,method_name,item_name",
        _MOVE_SITES,
        ids=["example-media", "pronunciation-media", "sense-picture"],
    )
    def test_move_method_has_no_remove_on_item(self, path, class_name, method_name, item_name):
        body_src = _method_source(path, class_name, method_name)
        assert f".Remove({item_name})" not in body_src, (
            f"{class_name}.{method_name} must not call Remove({item_name}) (#471)."
        )
        assert ".MediaFilesOS.Add(" in body_src or ".PicturesOS.Add(" in body_src
