#
#   test_pyi_return_annotation_ratchet.py
#
#   Class: TestPyiReturnAnnotationRatchet
#          Narrow non-contradiction guard for issue #306: where BOTH
#          `flexicon/code/FLExProject.py` and its `.pyi` stub carry a
#          return annotation on the same public method, the two must
#          agree. This is deliberately NOT a coverage floor -- it never
#          requires an annotation to exist on either side, only that
#          annotations present on both sides don't contradict each
#          other. See MattGyverLee/flexicon#306.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PY_PATH = REPO_ROOT / "flexicon" / "code" / "FLExProject.py"
PYI_PATH = REPO_ROOT / "flexicon" / "code" / "FLExProject.pyi"

# The consumer regex this ratchet pins against (issue #306): a docstring
# `Returns:` section's first content line must match this shape to have
# its type extracted downstream. Whitespace after the colon is required.
_RETURNS_TYPE_RE = re.compile(r"^([A-Za-z_][\w\[\], ]*?):\s+")


def _find_class_public_defs(tree, class_name):
    """Return {method_name: FunctionDef/AsyncFunctionDef} for the public
    (non-underscore-prefixed) methods directly defined on `class_name`.
    """
    defs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_"):
                        defs[item.name] = item
    return defs


def _normalize_annotation(node):
    """Render an annotation AST node to a comparable string, stripping a
    string-literal forward reference down to its inner text (e.g. both
    `"FLExProject"` and `FLExProject` normalize to `FLExProject`).
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.strip()
    return ast.unparse(node).strip().strip("'\"")


class TestPyiReturnAnnotationsDoNotContradict:
    """
    Where a method's return annotation is present on BOTH the runtime
    module and the stub, it must say the same thing. Deliberately does
    NOT assert that any given method has an annotation on either side --
    that would turn this into an unrequested coverage floor (see the
    other 78 public defs on FLExProject that still lack a `Returns:`
    docstring section; sweeping those is explicitly out of scope for
    issue #306).
    """

    def test_shared_return_annotations_agree(self):
        py_tree = ast.parse(
            PY_PATH.read_text(encoding="utf-8"), filename=str(PY_PATH)
        )
        pyi_tree = ast.parse(
            PYI_PATH.read_text(encoding="utf-8"), filename=str(PYI_PATH)
        )

        py_defs = _find_class_public_defs(py_tree, "FLExProject")
        pyi_defs = _find_class_public_defs(pyi_tree, "FLExProject")

        mismatches = []
        for name, py_node in py_defs.items():
            pyi_node = pyi_defs.get(name)
            if pyi_node is None:
                continue
            if py_node.returns is None or pyi_node.returns is None:
                # Non-contradiction check only: an annotation missing on
                # either side is not this test's concern.
                continue
            py_ann = _normalize_annotation(py_node.returns)
            pyi_ann = _normalize_annotation(pyi_node.returns)
            if py_ann != pyi_ann:
                mismatches.append(
                    f"{name}: FLExProject.py returns {py_ann!r}, "
                    f".pyi returns {pyi_ann!r}"
                )

        assert not mismatches, (
            "Return annotations disagree between FLExProject.py and "
            "FLExProject.pyi:\n  " + "\n  ".join(mismatches)
        )


class TestFromOpenProjectReturnTypeRegression:
    """
    Direct regression pin for issue #306: `FromOpenProject` must carry a
    real return annotation, AND its docstring `Returns:` section must be
    parseable by the consumer regex used to extract the documented type.
    """

    def _get_from_open_project(self):
        tree = ast.parse(
            PY_PATH.read_text(encoding="utf-8"), filename=str(PY_PATH)
        )
        defs = _find_class_public_defs(tree, "FLExProject")
        node = defs.get("FromOpenProject")
        assert node is not None, "FromOpenProject not found on FLExProject"
        return node

    def test_from_open_project_has_runtime_return_annotation(self):
        node = self._get_from_open_project()
        assert node.returns is not None, (
            "FromOpenProject has no runtime return annotation (issue #306)"
        )
        assert _normalize_annotation(node.returns) == "FLExProject"

    def test_from_open_project_docstring_returns_section_matches_consumer_regex(
        self,
    ):
        node = self._get_from_open_project()
        doc = ast.get_docstring(node) or ""
        assert "Returns:" in doc, (
            "FromOpenProject docstring has no Returns: section (issue #306)"
        )

        lines = doc.splitlines()
        returns_idx = next(
            i for i, line in enumerate(lines) if line.strip() == "Returns:"
        )
        # First content line after the `Returns:` header.
        content_line = lines[returns_idx + 1].strip()

        match = _RETURNS_TYPE_RE.match(content_line)
        assert match is not None, (
            f"Returns: content line {content_line!r} does not match the "
            "consumer regex r'^([A-Za-z_][\\w\\[\\], ]*?):\\s+'"
        )
        assert match.group(1) == "FLExProject"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
