#
#   test_issue314_default_ws_properties.py
#
#   Issue #314: FLExProject.DefaultVernacularWs / DefaultAnalysisWs must
#   exist and satisfy core.types.FlexProject.
#
#   Platform: Python.NET / FieldWorks 9+ (live parity in discoverability module)
#
#   Copyright 2026
#

import ast
import importlib.util
from pathlib import Path


def _load_flexproject_protocol():
    """Load core/types.py without importing core (pulls pythonnet via resolvers)."""
    types_path = Path(__file__).resolve().parents[1] / "core" / "types.py"
    spec = importlib.util.spec_from_file_location(
        "flexicon_core_types_issue314", types_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FlexProject


def _flexproject_source_path():
    return (
        Path(__file__).resolve().parents[1]
        / "flexicon"
        / "code"
        / "FLExProject.py"
    )


def _property_return_calls(source_path, property_name):
    """Return the method name invoked by ``return self.<method>()`` in a property."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "FLExProject":
            continue
        for item in node.body:
            if not isinstance(item, ast.FunctionDef) or item.name != property_name:
                continue
            for stmt in item.body:
                if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
                    func = stmt.value.func
                    if isinstance(func, ast.Attribute):
                        return func.attr
    return None


class TestIssue314DefaultWsPropertiesOffline:
    """Structural checks -- no pythonnet import required."""

    def test_flexproject_protocol_declares_default_ws_properties(self):
        types_path = Path(__file__).resolve().parents[1] / "core" / "types.py"
        tree = ast.parse(types_path.read_text(encoding="utf-8"))
        protocol = next(
            n
            for n in tree.body
            if isinstance(n, ast.ClassDef) and n.name == "FlexProject"
        )
        decorator_names = {
            d.id if isinstance(d, ast.Name) else getattr(d, "attr", "")
            for d in protocol.decorator_list
        }
        assert "runtime_checkable" in decorator_names
        prop_names = {
            node.name
            for node in protocol.body
            if isinstance(node, ast.FunctionDef)
            and any(
                isinstance(d, ast.Name) and d.id == "property"
                for d in node.decorator_list
            )
        }
        assert "DefaultVernacularWs" in prop_names
        assert "DefaultAnalysisWs" in prop_names

    def test_flexproject_class_defines_default_ws_properties(self):
        source = _flexproject_source_path().read_text(encoding="utf-8")
        tree = ast.parse(source)
        class_node = next(
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "FLExProject"
        )
        prop_names = {
            node.name
            for node in class_node.body
            if isinstance(node, ast.FunctionDef)
            and any(
                isinstance(d, ast.Name) and d.id == "property"
                for d in node.decorator_list
            )
        }
        assert "DefaultVernacularWs" in prop_names
        assert "DefaultAnalysisWs" in prop_names

    def test_properties_delegate_to_handle_helpers_in_source(self):
        path = _flexproject_source_path()
        assert _property_return_calls(path, "DefaultVernacularWs") == (
            "GetDefaultVernacularWSHandle"
        )
        assert _property_return_calls(path, "DefaultAnalysisWs") == (
            "GetDefaultAnalysisWSHandle"
        )
