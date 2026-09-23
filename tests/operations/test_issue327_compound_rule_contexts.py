#
#   test_issue327_compound_rule_contexts.py
#
#   Offline coverage for issue #327: CompoundRule must not probe phantom
#   LeftContextOA/RightContextOA on IMoEndoCompound/IMoExoCompound, and
#   must expose the live-confirmed type-specific members instead.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
COMPOUND_RULE_PY = REPO_ROOT / "flexicon" / "code" / "Grammar" / "compound_rule.py"


def _function_property_names(tree: ast.Module) -> set[str]:
    """Return @property method names on CompoundRule."""
    names = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "CompoundRule":
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for dec in item.decorator_list:
                    if isinstance(dec, ast.Name) and dec.id == "property":
                        names.add(item.name)
    return names


class TestIssue327CompoundRuleContexts:
    """Static guards for #327 (no flexicon import -- cloud-safe)."""

    def test_compound_rule_source_has_no_phantom_context_members(self):
        """LeftContextOA/RightContextOA must not appear in compound_rule.py."""
        source = COMPOUND_RULE_PY.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(COMPOUND_RULE_PY))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "ContextOA" in node.value:
                    names.add(node.value)
        forbidden = {"LeftContextOA", "RightContextOA"}
        assert forbidden.isdisjoint(names), (
            f"Phantom context members still referenced: {forbidden & names}"
        )

    def test_removed_context_properties_are_gone(self):
        tree = ast.parse(
            COMPOUND_RULE_PY.read_text(encoding="utf-8"),
            filename=str(COMPOUND_RULE_PY),
        )
        props = _function_property_names(tree)
        assert "left_context" not in props
        assert "right_context" not in props
        assert "contexts" not in props

    def test_live_confirmed_surfaces_are_exposed(self):
        tree = ast.parse(
            COMPOUND_RULE_PY.read_text(encoding="utf-8"),
            filename=str(COMPOUND_RULE_PY),
        )
        props = _function_property_names(tree)
        assert {"head_last", "overriding_msa", "to_msa"}.issubset(props)
