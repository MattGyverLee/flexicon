#
#   test_flexlibs2_alias_ratchet.py
#
#   Class: TestFlexlibs2AliasIsInboundOnly
#          Ratchet guard for issue #240: `flexlibs2` is a compatibility alias
#          for external callers only. Nothing internal -- shipped library
#          code, example scripts, docstrings, tests -- may walk it. The alias
#          is removed at v5.0.0; every internal reference below would become
#          a hard break at that boundary.
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

# The alias package itself, plus any test that is explicitly ABOUT the
# alias/deprecation, is allowed to reference `flexlibs2`. Everything else is
# not.
_ALLOWED_PATHS = {
    REPO_ROOT / "flexlibs2",
    REPO_ROOT / "tests" / "test_flexlibs2_alias_ratchet.py",
}

# Directories that are not part of the source tree we ratchet on. `.git` and
# in-tree scratch/build outputs must be skipped so a stray file cannot break
# CI without an actual source-tree regression.
_SKIP_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "build",
    "dist",
    "htmlcov",
    "scratchpad",
    ".claude",
}


def _iter_python_files():
    for path in REPO_ROOT.rglob("*.py"):
        if any(part in _SKIP_DIR_NAMES for part in path.relative_to(REPO_ROOT).parts):
            continue
        # Skip anything under an allowed subtree (e.g. the alias package).
        if any(_is_relative_to(path, allowed) for allowed in _ALLOWED_PATHS):
            continue
        yield path


def _is_relative_to(child: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _executable_flexlibs2_imports(source: str, filename: str):
    """Return a list of (lineno, statement) for every executable `flexlibs2`
    import in `source`.

    An "executable" import is one produced by ast.parse -- text inside
    docstrings and comments never becomes an Import/ImportFrom node, so we
    filter those out for free.
    """
    hits = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        # A syntax error is a different regression -- don't mask it here.
        return hits

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "flexlibs2" or module.startswith("flexlibs2."):
                hits.append((node.lineno, f"from {module} import ..."))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "flexlibs2" or alias.name.startswith("flexlibs2."):
                    hits.append((node.lineno, f"import {alias.name}"))
    return hits


_STRING_FLEXLIBS2_RE = re.compile(r"""flexlibs2(?:\.[A-Za-z0-9_]+)+""")


def _string_literal_flexlibs2_references(source: str, filename: str):
    """Return a list of (lineno, snippet) for every string literal that
    names a dotted `flexlibs2.*` path (e.g. `@patch("flexlibs2.sync...")`).

    unittest.mock.patch and other string-based lookups walk the alias at
    runtime the same way an import does, so they belong to the same
    ratchet.
    """
    hits = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return hits

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for match in _STRING_FLEXLIBS2_RE.finditer(node.value):
                hits.append((node.lineno, match.group(0)))
    return hits


class TestFlexlibs2AliasIsInboundOnly:
    def test_no_executable_flexlibs2_imports_outside_alias_package(self):
        """
        Every executable `from flexlibs2...` / `import flexlibs2...` statement
        outside the alias package and its own tests is a v5.0.0 hard break
        waiting to happen. See issue #240.
        """
        offenders = []
        for path in _iter_python_files():
            source = path.read_text(encoding="utf-8")
            for lineno, statement in _executable_flexlibs2_imports(source, str(path)):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {statement}")

        assert not offenders, (
            "Found executable `flexlibs2` imports outside the alias package. "
            "Use `flexicon` instead:\n  "
            + "\n  ".join(offenders)
        )

    def test_no_flexlibs2_dotted_string_references_outside_alias_package(self):
        """
        `@patch("flexlibs2.sync.merge_ops.MergeOperations")` and other
        string-based references walk the alias at runtime just like an
        import does. Same ratchet, different syntax.
        """
        offenders = []
        for path in _iter_python_files():
            source = path.read_text(encoding="utf-8")
            for lineno, snippet in _string_literal_flexlibs2_references(source, str(path)):
                offenders.append(
                    f"{path.relative_to(REPO_ROOT)}:{lineno}: {snippet!r}"
                )

        assert not offenders, (
            "Found `flexlibs2.<...>` dotted references in string literals "
            "outside the alias package. Use `flexicon.<...>` instead:\n  "
            + "\n  ".join(offenders)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
