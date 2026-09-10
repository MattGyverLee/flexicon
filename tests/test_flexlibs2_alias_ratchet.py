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
import io
import pathlib
import re
import tokenize

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# The alias package itself, plus any test that is explicitly ABOUT the
# alias/deprecation, is allowed to reference `flexlibs2`. Everything else is
# not.
#
# Keep this set MINIMAL. Every entry is a hole in the ratchet, so a file
# only belongs here if walking the alias is the thing it tests. A test that
# merely happens to import a library symbol must import it from `flexicon`
# and stay ratcheted.
_ALLOWED_PATHS = {
    REPO_ROOT / "flexlibs2",
    REPO_ROOT / "tests" / "test_flexlibs2_alias_ratchet.py",
    # Behavioral tests for the alias itself -- see that file's scope fence.
    REPO_ROOT / "tests" / "test_flexlibs2_alias_surface.py",
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
    # Historical record trees. These document the rename as it happened;
    # rewriting them would falsify the migration record, so they are out
    # of the ratchet entirely rather than allowlisted file-by-file.
    "specs",
    "plans",
    "_archive",
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


# ---------------------------------------------------------------------------
# Prose ratchet (issue #240)
#
# The AST checks above only see *executable* Python. They are structurally
# blind to Markdown, reStructuredText, docstrings and comments -- which is
# precisely the surface a user copies from. The docstring `Usage::` blocks and
# the ~100 `from flexlibs2 import ...` lines across docs/ stayed invisible to
# this file for the whole life of the rename while it passed green.
#
# Each entry below is a HOLE in the ratchet, so each one carries the reason it
# may keep the old name. The test is always the same: does the text *describe
# the rename or the compatibility shim* (allowed), or does it *teach someone
# how to use the library today* (not allowed)?
# ---------------------------------------------------------------------------

_PROSE_ALLOWED = {
    # Release and project history: these record what actually shipped under
    # the old name, so rewriting them would falsify the record.
    "CHANGELOG.md": "release history, including the rename entries",
    "history.md": "upstream-sync development history",
    "RELEASE_NOTES_v2.4.0.md": "shipped under the old package name",
    "RELEASE_NOTES_v4.6.0.md": "release note discussing the rename itself",
    "docs/internal/RELEASE_v3_0_0.md": "internal notes for a pre-rename cut",
    # Documents whose subject IS the alias or its removal.
    "CLAUDE.md": "documents the deprecated alias and the v5.0.0 removal",
    "README.rst": "user-facing deprecation notice for the legacy name",
    "docs/RELEASING.md": "records that v5.0.0 is reserved for alias removal",
    "docs/FLEXTOOLSMCP_WRITE_CONTRACT.md": "describes the shim's behaviour",
    "docs/_templates/MIGRATION_GUIDE_SECTION.md":
        "worked example quotes a real pre-rename migration entry",
}

# Python files allowed to name the alias in a comment or docstring.
_PY_PROSE_ALLOWED = {
    "flexicon/__init__.py": "module docstring describes the legacy import name",
    "tests/contract/extract_lcm_contract.py":
        "legacy path fallback, with a comment naming the rename commit",
    "tests/operations/test_transaction_rollback.py":
        "notes that the rename split this test in two",
    "tests/write_path_transactions/test_capabilities.py":
        "explains where the alias test moved to",
    "scripts/crystallization_metric.py":
        "guard comment citing the rename as the failure it prevents",
    "scripts/live_coverage_metric.py": "same guard comment",
    "tests/test_264_sldr_single_init_path.py":
        "module docstring names this file as the ratchet pattern it models",
}

# What a *teaching* reference looks like: an import the reader would copy, an
# install command, or a source path that no longer exists. Plain narrative
# prose naming the old package is governed by the whole-file allowlist above.
_TEACHING_RE = re.compile(
    r"(?:from\s+flexlibs2|import\s+flexlibs2"
    r"|pip\s+install\s+flexlibs2|flexlibs2/(?:code|sync|docs)/)"
)


def _iter_prose_files():
    for suffix in ("*.md", "*.rst"):
        for path in REPO_ROOT.rglob(suffix):
            rel = path.relative_to(REPO_ROOT)
            if any(part in _SKIP_DIR_NAMES for part in rel.parts):
                continue
            if rel.as_posix() in _PROSE_ALLOWED:
                continue
            yield path, rel


def _comment_and_docstring_text(source: str, filename: str):
    """Yield (lineno, text) for every comment and docstring in `source`."""
    hits = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                hits.append((tok.start[0], tok.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass

    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return hits

    doc_owners = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if isinstance(node, doc_owners):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                hits.append((getattr(node, "lineno", 1), doc))
    return hits


class TestFlexlibs2IsNotTaughtInProse:
    def test_no_flexlibs2_teaching_references_in_docs(self):
        """
        A doc that says `from flexlibs2 import ...` hands the reader code that
        breaks at v5.0.0. The AST ratchet above cannot see Markdown, so this
        is the guard for the surface users actually copy from. Issue #240.
        """
        offenders = []
        for path, rel in _iter_prose_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            if "flexlibs2" not in text:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if _TEACHING_RE.search(line):
                    offenders.append(f"{rel.as_posix()}:{lineno}: {line.strip()}")

        assert not offenders, (
            "Documentation teaches the deprecated `flexlibs2` path. Use "
            "`flexicon`, or add the file to _PROSE_ALLOWED with a reason if "
            "it is genuinely about the rename:\n  " + "\n  ".join(offenders)
        )

    def test_no_flexlibs2_in_python_comments_or_docstrings(self):
        """
        The `Usage::` blocks in Operations docstrings taught the alias for the
        whole life of the rename while this file passed green, because a
        docstring never becomes an Import node. Comments have the same hole.
        """
        offenders = []
        for path in _iter_python_files():
            rel = path.relative_to(REPO_ROOT)
            if rel.as_posix() in _PY_PROSE_ALLOWED:
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            if "flexlibs2" not in source:
                continue
            for lineno, text in _comment_and_docstring_text(source, str(path)):
                if "flexlibs2" in text:
                    snippet = text.strip().splitlines()[0][:90]
                    offenders.append(f"{rel.as_posix()}:{lineno}: {snippet}")

        assert not offenders, (
            "Found `flexlibs2` in Python comments/docstrings. Use `flexicon`, "
            "or add the file to _PY_PROSE_ALLOWED with a reason:\n  "
            + "\n  ".join(offenders)
        )


class TestProseRatchetAllowlistStaysHonest:
    def test_every_allowlisted_path_still_earns_its_hole(self):
        """
        An allowlist entry for a file that no longer exists, or that no longer
        mentions the alias, is a hole left open for nothing. Fail so the entry
        gets deleted rather than quietly widening the ratchet over time.
        """
        stale = []
        for rel, reason in {**_PROSE_ALLOWED, **_PY_PROSE_ALLOWED}.items():
            path = REPO_ROOT / rel
            if not path.exists():
                stale.append(f"{rel}: allowlisted ({reason}) but does not exist")
            elif "flexlibs2" not in path.read_text(
                encoding="utf-8", errors="replace"
            ):
                stale.append(
                    f"{rel}: allowlisted ({reason}) but no longer mentions the "
                    "alias -- drop the entry"
                )

        assert not stale, (
            "Stale ratchet allowlist entries:\n  " + "\n  ".join(stale)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
