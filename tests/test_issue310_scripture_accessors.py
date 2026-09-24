#
#   test_issue310_scripture_accessors.py
#
#   Issue #310: FLExProject must expose all six Scripture Operations
#   accessors referenced by docstrings and integration plans.
#
#   Platform: Python.NET / FieldWorks 9+ (offline structural gate)
#
#   Copyright 2026
#

import ast
from pathlib import Path

SCRIPTURE_ACCESSORS = {
    "ScrBooks": "ScrBookOperations",
    "ScrDrafts": "ScrDraftOperations",
    "ScrNotes": "ScrNoteOperations",
    "ScrSections": "ScrSectionOperations",
    "ScrTxtParas": "ScrTxtParaOperations",
    "ScrAnnotations": "ScrAnnotationsOperations",
}


def _flexproject_class_node():
    path = (
        Path(__file__).resolve().parents[1]
        / "flexicon"
        / "code"
        / "FLExProject.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "FLExProject":
            return node
    raise AssertionError("FLExProject class not found")


def _property_names(class_node):
    names = set()
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef):
            if any(
                isinstance(d, ast.Name) and d.id == "property"
                for d in item.decorator_list
            ):
                names.add(item.name)
    return names


def _lazy_import_ops_class(property_name):
    """Return Operations class name from lazy import in a property body."""
    class_node = _flexproject_class_node()
    for item in class_node.body:
        if not isinstance(item, ast.FunctionDef) or item.name != property_name:
            continue
        for stmt in ast.walk(item):
            if isinstance(stmt, ast.ImportFrom) and stmt.module:
                for alias in stmt.names:
                    if alias.name.endswith("Operations"):
                        return alias.name
    return None


class TestIssue310ScriptureAccessorsOffline:
    """Structural checks -- no pythonnet import required."""

    def test_all_scripture_accessors_are_properties_on_flexproject(self):
        props = _property_names(_flexproject_class_node())
        missing = [name for name in SCRIPTURE_ACCESSORS if name not in props]
        assert not missing, f"Missing FLExProject properties: {missing}"

    def test_each_accessor_lazy_imports_matching_operations_class(self):
        for accessor, expected in SCRIPTURE_ACCESSORS.items():
            imported = _lazy_import_ops_class(accessor)
            assert imported == expected, (
                f"{accessor} lazy-imports {imported}, expected {expected}"
            )
