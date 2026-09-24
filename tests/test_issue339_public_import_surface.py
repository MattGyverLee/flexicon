#
#   test_issue339_public_import_surface.py
#
#   Offline regression for issue #339 / flexicon#257: MSAOperations and
#   PhonFeatureOperations must stay importable via `from flexicon import ...`
#   without executing flexicon (cloud-safe AST ratchet).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
INIT_PY = REPO_ROOT / "flexicon" / "__init__.py"
INIT_PYI = REPO_ROOT / "flexicon" / "__init__.pyi"

# Names called out in issue #339 log-scan triage (MSAOperations x2,
# PhonFeatureOperations x2 across two sessions).
ISSUE_339_EXPORTS = frozenset({"MSAOperations", "PhonFeatureOperations"})


def _parse(path: pathlib.Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _all_literal_names(tree: ast.Module) -> set[str]:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                value = node.value
                if isinstance(value, (ast.List, ast.Tuple)):
                    names = set()
                    for elt in value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(
                            elt.value, str
                        ):
                            names.add(elt.value)
                    return names
    return set()


def _runtime_imports_name(tree: ast.Module, public_name: str) -> bool:
    """True if __init__.py binds public_name from a submodule import."""
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            bound = alias.asname or alias.name
            if bound == public_name:
                return True
    return False


class TestIssue339PublicImportSurface:
    """Pin the #257/#339 export surface without importing flexicon."""

    def test_msa_and_phon_feature_are_runtime_exports(self):
        tree = _parse(INIT_PY)
        all_names = _all_literal_names(tree)
        missing = ISSUE_339_EXPORTS - all_names
        assert not missing, (
            f"flexicon/__init__.py __all__ missing issue #339 exports: {sorted(missing)}"
        )

    def test_msa_and_phon_feature_have_eager_import_bindings(self):
        tree = _parse(INIT_PY)
        for name in ISSUE_339_EXPORTS:
            assert _runtime_imports_name(tree, name), (
                f"flexicon/__init__.py must import {name} at module level "
                f"(from flexicon import {name} is the supported path)"
            )

    def test_stub_all_lists_issue_339_exports(self):
        tree = _parse(INIT_PYI)
        all_names = _all_literal_names(tree)
        missing = ISSUE_339_EXPORTS - all_names
        assert not missing, (
            f"flexicon/__init__.pyi __all__ missing issue #339 exports: {sorted(missing)}"
        )
