#
#   test_issue341_possibility_create_pattern.py
#
#   Offline regression for issue #341: possibility creation must use
#   parameterless ICmPossibilityFactory.Create(), not guessed overloads.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

FACTORY_CREATE_PATHS = (
    REPO_ROOT / "flexicon" / "code" / "Lists" / "PossibilityListOperations.py",
    REPO_ROOT / "flexicon" / "code" / "Lists" / "possibility_item_base.py",
    REPO_ROOT / "flexicon" / "code" / "System" / "CheckOperations.py",
)

POSSIBILITY_LIST_OPS = (
    REPO_ROOT / "flexicon" / "code" / "Lists" / "PossibilityListOperations.py"
)


def _factory_create_calls(tree: ast.AST) -> list[ast.Call]:
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "Create"
            and isinstance(func.value, ast.Name)
            and func.value.id == "factory"
        ):
            calls.append(node)
    return calls


def _function_body(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == name:
                    return item
    return None


class TestIssue341PossibilityFactoryCreatePattern:
    def test_factory_create_is_parameterless_in_helpers(self):
        offenders = []
        for path in FACTORY_CREATE_PATHS:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for call in _factory_create_calls(tree):
                if call.args or call.keywords:
                    offenders.append(f"{path.name}:{call.lineno}")
        assert not offenders, (
            "ICmPossibilityFactory.Create must be called with no arguments "
            f"(issue #341); found: {offenders}"
        )

    def test_create_item_in_list_by_name_delegates_to_find_and_create(self):
        tree = ast.parse(
            POSSIBILITY_LIST_OPS.read_text(encoding="utf-8"),
            filename=str(POSSIBILITY_LIST_OPS),
        )
        func = _function_body(tree, "CreateItemInListByName")
        assert func is not None, "CreateItemInListByName must exist (issue #341)"

        call_names = set()
        for node in ast.walk(func):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

        assert "FindList" in call_names
        assert "CreateItem" in call_names

    def test_class_docstring_warns_against_raw_factory_overload(self):
        tree = ast.parse(
            POSSIBILITY_LIST_OPS.read_text(encoding="utf-8"),
            filename=str(POSSIBILITY_LIST_OPS),
        )
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "PossibilityListOperations":
                doc = ast.get_docstring(node) or ""
                assert "OverloadResolutionError" in doc
                assert "CreateItemInListByName" in doc
                return
        raise AssertionError("PossibilityListOperations class not found")
