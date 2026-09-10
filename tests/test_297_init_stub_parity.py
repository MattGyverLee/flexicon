#
#   test_297_init_stub_parity.py
#
#   Class: TestInitStubParity
#          Guards `flexicon/__init__.pyi` against drifting out of sync with
#          `flexicon/__init__.py` (issue #297). `__init__.py` re-exports
#          roughly 80 public names -- 43+ Operations classes, exceptions,
#          and helpers -- but defines no `__all__` of its own; the stub is
#          the only place Pyright's public surface is declared. A name
#          missing from the stub's `__all__` makes Pyright report
#          "X is unknown import symbol" for `from flexicon import X`, and a
#          name present in `__all__` but absent from the runtime module (the
#          issue #276-style overstatement) claims an API that does not
#          exist.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

"""
Static (AST-only) parity check between `flexicon/__init__.py` and
`flexicon/__init__.pyi`.

This test deliberately never does `import flexicon`. On a machine without
FieldWorks/pythonnet installed, importing the real package can fail long
before any test body runs, since `flexicon/__init__.py` transitively pulls
in LCM-backed Operations modules. Parsing both files with `ast` gives the
same name lists without ever executing either module, so this test runs
anywhere Python + pytest run.

Both sides of the comparison are derived from the files, not hardcoded --
the whole point of the ratchet is that adding a new public export to
`__init__.py` without updating the stub's `__all__` (or vice versa) fails
loudly here instead of silently shipping a stale stub.
"""

import ast
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
INIT_PY = REPO_ROOT / "flexicon" / "__init__.py"
INIT_PYI = REPO_ROOT / "flexicon" / "__init__.pyi"


def _parse(path: pathlib.Path) -> ast.Module:
    source = path.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(path))


def _runtime_public_names(tree: ast.Module) -> set:
    """
    Every name bound at module level in `flexicon/__init__.py`, filtered to
    the public surface (no leading underscore).

    Covers:
      - `from .code.X import (Y, Z as W)`  -> "Y", "W"
      - module-level assignments, e.g. `version = "4.6.0"`,
        `CAPABILITIES = frozenset({...})`
      - module-level `def` / `class` statements (none exist today, but a
        future one must not silently bypass the ratchet)
    """
    names = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, (ast.Assign,)):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)

    return {name for name in names if not name.startswith("_")}


def _stub_declared_names(tree: ast.Module) -> set:
    """
    Every name actually declared somewhere in `flexicon/__init__.pyi`
    (imports, defs, classes, and plain/annotated assignments), regardless
    of whether it is also listed in `__all__`.
    """
    names = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)

    return names


def _stub_all_entries(tree: ast.Module) -> list:
    """
    The literal list of strings assigned to `__all__` in
    `flexicon/__init__.pyi`.

    Raises AssertionError (via pytest.fail) if no such assignment is found,
    or if it is not a simple list/tuple of string constants -- either
    would itself be a stub authoring bug worth surfacing distinctly from a
    parity mismatch.
    """
    for node in tree.body:
        targets = None
        value = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value

        if not targets or value is None:
            continue

        if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
            continue

        if not isinstance(value, (ast.List, ast.Tuple)):
            pytest.fail(
                "flexicon/__init__.pyi: `__all__` is not a literal list/tuple "
                "of strings; this test cannot statically verify it."
            )

        entries = []
        for elt in value.elts:
            if not (isinstance(elt, ast.Constant) and isinstance(elt.value, str)):
                pytest.fail(
                    "flexicon/__init__.pyi: `__all__` contains a non-string-"
                    "literal element; this test cannot statically verify it."
                )
            entries.append(elt.value)
        return entries

    pytest.fail("flexicon/__init__.pyi: no `__all__` assignment found.")


class TestInitStubParity:
    """
    Ratchet for issue #297: `flexicon/__init__.pyi`'s `__all__` must name
    exactly the public surface that `flexicon/__init__.py` actually
    exports, and every one of those names must be declared somewhere in
    the stub.
    """

    def test_every_runtime_public_name_is_in_stub_all(self):
        """
        Every public name bound at module level in `__init__.py` must
        appear in the stub's `__all__`, or Pyright reports
        "X is unknown import symbol" for `from flexicon import X`.
        """
        runtime_names = _runtime_public_names(_parse(INIT_PY))
        stub_all = set(_stub_all_entries(_parse(INIT_PYI)))

        missing = sorted(runtime_names - stub_all)
        assert not missing, (
            "flexicon/__init__.py exports these public names but "
            "flexicon/__init__.pyi's `__all__` does not list them -- "
            "Pyright will report them as unknown import symbols. Add to "
            "`__all__` (and declare each, e.g. via an ImportFrom or a `def`/"
            "class stub) in flexicon/__init__.pyi:\n  "
            + "\n  ".join(missing)
        )

    def test_stub_all_has_no_name_absent_from_runtime(self):
        """
        The inverse defect (see issue #276): the stub's `__all__` must not
        claim a name that `__init__.py` does not actually export at
        runtime, or callers relying on the stub will type-check against an
        API that does not exist.
        """
        runtime_names = _runtime_public_names(_parse(INIT_PY))
        stub_all = set(_stub_all_entries(_parse(INIT_PYI)))

        overstated = sorted(stub_all - runtime_names)
        assert not overstated, (
            "flexicon/__init__.pyi's `__all__` lists these names but "
            "flexicon/__init__.py does not actually export them at "
            "runtime -- remove them from `__all__` (and their declarations) "
            "in flexicon/__init__.pyi, or add the matching export to "
            "flexicon/__init__.py if the export was simply forgotten:\n  "
            + "\n  ".join(overstated)
        )

    def test_every_stub_all_entry_is_declared_in_stub(self):
        """
        An `__all__` entry with no matching declaration (import/def/class/
        assignment) in the stub is itself a Pyright error, independent of
        whether `__init__.py` exports it.
        """
        stub_tree = _parse(INIT_PYI)
        stub_all = _stub_all_entries(stub_tree)
        declared = _stub_declared_names(stub_tree)

        undeclared = sorted(set(stub_all) - declared)
        assert not undeclared, (
            "flexicon/__init__.pyi's `__all__` lists these names but the "
            "stub never declares them (no matching import/def/class/"
            "assignment) -- add a declaration for each in "
            "flexicon/__init__.pyi:\n  "
            + "\n  ".join(undeclared)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
