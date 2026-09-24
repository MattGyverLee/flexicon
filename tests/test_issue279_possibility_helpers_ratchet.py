#
#   test_issue279_possibility_helpers_ratchet.py
#
#   Offline ratchet for issue #279 gap 2: FLExProject list-field helpers keep
#   live LCM return types; docstrings document cast_to_concrete escape hatch.
#
#   Platform: Python 3.8+
#   Copyright 2026
#

from pathlib import Path
import ast

REPO_ROOT = Path(__file__).resolve().parent.parent
FLEX_PROJECT = REPO_ROOT / "flexicon" / "code" / "FLExProject.py"


def _method_docstring(method_name: str) -> str:
    source = FLEX_PROJECT.read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if not isinstance(node, ast.ClassDef) or node.name != "FLExProject":
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == method_name:
                return ast.get_docstring(item) or ""
    raise AssertionError(f"{method_name} not found on FLExProject")


def _method_body_contains(method_name: str, *needles: str) -> None:
    source = FLEX_PROJECT.read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if not isinstance(node, ast.ClassDef) or node.name != "FLExProject":
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == method_name:
                stmt_lines = []
                for stmt in item.body:
                    if isinstance(stmt, ast.Expr) and isinstance(
                        stmt.value, ast.Constant
                    ) and isinstance(stmt.value.value, str):
                        continue
                    seg = ast.get_source_segment(source, stmt)
                    if seg:
                        stmt_lines.append(seg)
                body_src = "\n".join(stmt_lines)
                flattened = " ".join(body_src.split())
                for needle in needles:
                    assert needle in flattened, (
                        f"{method_name} body must contain {needle!r} (issue #279)"
                    )
                assert "cast_to_concrete" not in body_src, (
                    f"{method_name} must not cast inside the helper (issue #279)"
                )
                return
    raise AssertionError(f"{method_name} not found on FLExProject")


class TestIssue279PossibilityHelpersRatchet:
    def test_list_field_possibilities_docstring_documents_live_os(self):
        doc = _method_docstring("ListFieldPossibilities")
        for phrase in (
            "PossibilitiesOS",
            "load-bearing",
            "cast_to_concrete",
            "ICmPossibility",
        ):
            assert phrase in doc, (
                f"ListFieldPossibilities docstring must mention {phrase!r} (#279)"
            )

    def test_list_field_lookup_docstring_documents_interface_return(self):
        doc = _method_docstring("ListFieldLookup")
        for phrase in ("ICmPossibility", "cast_to_concrete", "FindPossibilityByName"):
            assert phrase in doc, (
                f"ListFieldLookup docstring must mention {phrase!r} (#279)"
            )

    def test_helpers_do_not_materialise_or_cast_returns(self):
        _method_body_contains(
            "ListFieldPossibilities",
            "return pList.PossibilitiesOS",
        )
        _method_body_contains(
            "ListFieldLookup",
            "return pList.FindPossibilityByName",
            "PossibilitiesOS",
        )
