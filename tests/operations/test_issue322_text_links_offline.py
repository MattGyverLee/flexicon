#
#   test_issue322_text_links_offline.py
#
#   Issue #322: phantom TextsRC / RecTypesOA silent no-ops in notebook and
#   anthropology text-link paths.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_DATANB = _REPO / "flexicon/code/Notebook/DataNotebookOperations.py"
_ANTHRO = _REPO / "flexicon/code/Notebook/AnthropologyOperations.py"


class TestIssue322DataNotebookStaticLock:
    def test_get_all_record_types_uses_research_notebook(self):
        source = _DATANB.read_text(encoding="utf-8")
        assert "ResearchNotebookOA" in source
        assert "RecTypesOA" in source
        assert 'hasattr(self.project.lp, "RecTypesOA")' not in source

    def test_text_link_methods_use_text_ra_not_textsrc(self):
        tree = ast.parse(_DATANB.read_text(encoding="utf-8"))
        text_methods = {
            "GetTexts",
            "LinkToText",
            "UnlinkFromText",
        }
        found_textsrc = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name not in text_methods:
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Attribute) and sub.attr == "TextsRC":
                    found_textsrc.append((node.name, sub.lineno))
        assert found_textsrc == [], f"TextsRC still referenced: {found_textsrc}"

        source = _DATANB.read_text(encoding="utf-8")
        for name in text_methods:
            assert f"def {name}" in source
        assert "TextRA" in source


class TestIssue322AnthropologyStaticLock:
    def test_add_remove_text_raise_instead_of_phantom_textsrc(self):
        source = _ANTHRO.read_text(encoding="utf-8")
        assert "supported on anthropology items (issue #322)" in source
        assert source.count("supported on anthropology items (issue #322)") >= 2
        tree = ast.parse(source)
        for method in ("AddText", "RemoveText"):
            fn = next(
                n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == method
            )
            for sub in ast.walk(fn):
                if isinstance(sub, ast.Attribute) and sub.attr == "TextsRC":
                    pytest.fail(f"{method} still references TextsRC at line {sub.lineno}")
