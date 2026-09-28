#
#   test_issue572_boundary_context_ratchet.py
#
#   Class: TestBoundaryContextNameRetired
#          Ratchet guard for issue #572 (C7 / SC-002): the retired
#          boundary-context class name must not reappear in library code,
#          docs or tests. The live class is PhSimpleContextBdry; the old
#          name described a type the LCM does not have.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

"""Ratchet: the retired boundary-context name stays gone (issue #572, SC-002).

The live LCM class is ``PhSimpleContextBdry``. An older name for the same
idea (retired under C7) described a type the LCM does not ship, and the
wrappers, collections, mocks and docs were repaired to stop using it. This
file scans the tree for that retired name and asserts zero offenders, so a
reintroduction fails here instead of shipping a dead discriminator again.

NOTE: this file itself never spells the retired name contiguously. The
needle is built by concatenation, and prose below refers to it only as
"the retired name", so the scanner does not flag its own source and the
``rg`` check in T022 sees only the two allowlisted hits.
"""

import ast
import io
import pathlib
import tokenize

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Built by concatenation so this file's own source never contains the
# retired name as one contiguous token.
_NEEDLE = "PhBoundary" + "Context"

# Files allowed to keep the retired name. Every entry is a hole in the
# ratchet, so each one carries the reason it may keep it. Keep this set
# MINIMAL: exactly the two holes the task list names.
_ALLOWED_PATHS = {
    # 4.x history entry at :3313; rewriting it would falsify the record.
    "CHANGELOG.md": "4.x history entry at :3313",
    # Live surface probe that records the retired class as absent.
    "tests/operations/test_issue572_phonrule_surface_live.py": (
        "probe that records the retired class as absent"
    ),
}

# Directories that are not part of the source tree we ratchet on. Copied
# verbatim from the inbound-alias ratchet test, whose skip set
# already excludes specs/ (historical record trees are out of the ratchet
# entirely rather than allowlisted file-by-file).
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
    "specs",
    "plans",
    "_archive",
}

_RATCHET_SELF = pathlib.Path(__file__).resolve()


def _is_skipped(path: pathlib.Path) -> bool:
    try:
        rel_parts = path.relative_to(REPO_ROOT).parts
    except ValueError:
        return True
    return any(part in _SKIP_DIR_NAMES for part in rel_parts)


def _is_allowlisted(path: pathlib.Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    return rel in _ALLOWED_PATHS


def _iter_python_files():
    for path in REPO_ROOT.rglob("*.py"):
        if _is_skipped(path):
            continue
        if path.resolve() == _RATCHET_SELF:
            continue
        if _is_allowlisted(path):
            continue
        yield path


def _iter_prose_files():
    for suffix in ("*.md", "*.rst"):
        for path in REPO_ROOT.rglob(suffix):
            if _is_skipped(path):
                continue
            if _is_allowlisted(path):
                continue
            yield path


def _ast_name_hits(source: str, filename: str):
    """Names and attribute accesses spelling the retired name (AST pass)."""
    hits = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return hits
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and _NEEDLE in node.id:
            hits.append((node.lineno, node.id))
        elif isinstance(node, ast.Attribute) and _NEEDLE in node.attr:
            hits.append((node.lineno, node.attr))
    return hits


def _string_literal_hits(source: str, filename: str):
    """String literals containing the retired name (literal pass)."""
    hits = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return hits
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _NEEDLE in node.value:
                snippet = node.value.strip().splitlines()[0][:90]
                hits.append((node.lineno, snippet))
    return hits


def _comment_and_docstring_text(source: str, filename: str):
    """Yield (lineno, text) for every comment and docstring in source."""
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


class TestRetiredBoundaryNameIsGone:
    def test_no_ast_references_to_retired_name(self):
        """AST pass: no Name/Attribute node spells the retired name."""
        offenders = []
        for path in _iter_python_files():
            source = path.read_text(encoding="utf-8", errors="replace")
            if _NEEDLE not in source:
                continue
            for lineno, snippet in _ast_name_hits(source, str(path)):
                offenders.append(
                    f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}: {snippet}"
                )
        assert not offenders, (
            "Found AST references to the retired boundary-context name. "
            "Use PhSimpleContextBdry instead:\n  " + "\n  ".join(offenders)
        )

    def test_no_string_literal_references_to_retired_name(self):
        """Literal pass: no string literal names the retired class."""
        offenders = []
        for path in _iter_python_files():
            source = path.read_text(encoding="utf-8", errors="replace")
            if _NEEDLE not in source:
                continue
            for lineno, snippet in _string_literal_hits(source, str(path)):
                offenders.append(
                    f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}: {snippet!r}"
                )
        assert not offenders, (
            "Found string-literal references to the retired boundary-context "
            "name. Use PhSimpleContextBdry instead:\n  " + "\n  ".join(offenders)
        )

    def test_no_retired_name_in_docs_prose(self):
        """Prose pass: no .md/.rst file teaches the retired name."""
        offenders = []
        for path in _iter_prose_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            if _NEEDLE not in text:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if _NEEDLE in line:
                    offenders.append(
                        f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}: "
                        f"{line.strip()[:120]}"
                    )
        assert not offenders, (
            "Documentation names the retired boundary-context class. Use "
            "PhSimpleContextBdry with boundary_marker/boundary_name instead:\n  "
            + "\n  ".join(offenders)
        )

    def test_no_retired_name_in_comments_or_docstrings(self):
        """Comment+docstring pass via tokenize and ast.get_docstring."""
        offenders = []
        for path in _iter_python_files():
            source = path.read_text(encoding="utf-8", errors="replace")
            if _NEEDLE not in source:
                continue
            for lineno, text in _comment_and_docstring_text(source, str(path)):
                if _NEEDLE in text:
                    snippet = text.strip().splitlines()[0][:90]
                    offenders.append(
                        f"{path.relative_to(REPO_ROOT).as_posix()}:{lineno}: {snippet}"
                    )
        assert not offenders, (
            "Found the retired boundary-context name in Python "
            "comments/docstrings. Use PhSimpleContextBdry instead:\n  "
            + "\n  ".join(offenders)
        )


class TestRetiredNameAllowlistStaysHonest:
    def test_every_allowlisted_path_still_earns_its_hole(self):
        """Backward guard: an allowlist entry that no longer needs its hole fails."""
        stale = []
        for rel, reason in _ALLOWED_PATHS.items():
            path = REPO_ROOT / rel
            if not path.exists():
                stale.append(f"{rel}: allowlisted ({reason}) but does not exist")
            elif _NEEDLE not in path.read_text(encoding="utf-8", errors="replace"):
                stale.append(
                    f"{rel}: allowlisted ({reason}) but no longer mentions "
                    "the retired name -- drop the entry"
                )
        assert not stale, (
            "Stale ratchet allowlist entries:\n  " + "\n  ".join(stale)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
