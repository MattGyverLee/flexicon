#
#   test_264_sldr_single_init_path.py
#
#   Class: TestSldrInitializeIsSinglePath
#          Ratchet guard for issue #264: `Sldr.Initialize(...)` must be
#          called from exactly one place in the whole tree --
#          `flexicon/code/FLExInit.py`, behind its `IsInitialized` guard
#          (issue #249). `tests/conftest.py` used to make a second, bare
#          `Sldr.Initialize(True)` call ten lines before calling
#          `FLExInitialize()`, which made the offline suite's pass/fail
#          count order-dependent: whichever module initialized SLDR first
#          decided the outcome for hundreds of tests, and the loser threw
#          `System.InvalidOperationException`.
#
#   Modeled on tests/test_flexlibs2_alias_ratchet.py (issue #240): an
#   AST walk sees only *executable* code, so it is structurally blind to
#   the word "Sldr.Initialize" appearing in a comment or docstring (which
#   tests/test_249_sldr_init_guard.py legitimately does, to document the
#   guarded call it doubles for).
#
#   Known limitation: _has_requires_live_project_marker (below) checks for
#   the marker at FILE level -- a module-level `pytestmark`, or a decorator
#   on any function/class in the file -- not per test function. A file
#   whose siblings carry the marker will pass this ratchet even if one
#   individual live-touching test in it does not. Separately,
#   _calls_live_project_api only recognizes calls named `OpenProject` or
#   `FLExInitialize`, so other live-state entry points (e.g.
#   AllProjectNames, which reads FwDirectoryFinder.ProjectsDirectory) are
#   not detected. Per-function granularity and a wider call-name set are
#   tracked follow-ups, not fixed here.
#
#   Platform: Python (no FieldWorks required)
#
#   Copyright 2026
#

import ast
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# The one file allowed to call Sldr.Initialize -- it does so behind the
# IsInitialized guard from issue #249. Keep this set to exactly one entry;
# a second entry is the same bug this test exists to catch.
_ALLOWED_PATHS = {
    REPO_ROOT / "flexicon" / "code" / "FLExInit.py",
}

# Directories that are not part of the source tree we ratchet on.
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


def _iter_python_files():
    for path in REPO_ROOT.rglob("*.py"):
        if any(part in _SKIP_DIR_NAMES for part in path.relative_to(REPO_ROOT).parts):
            continue
        if path in _ALLOWED_PATHS:
            continue
        yield path


def _executable_sldr_initialize_calls(source: str, filename: str):
    """Return a list of (lineno, snippet) for every executable call whose
    callee is `<something>.Initialize` where `<something>`'s final name
    component is `Sldr` (covers `Sldr.Initialize(...)` and any aliased
    import path ending in `.Sldr.Initialize(...)`).

    Text inside comments and docstrings never becomes a Call node, so it
    is filtered out for free -- exactly like the flexlibs2 ratchet.
    """
    hits = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return hits

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "Initialize"):
            continue
        target = func.value
        name = None
        if isinstance(target, ast.Name):
            name = target.id
        elif isinstance(target, ast.Attribute):
            name = target.attr
        if name == "Sldr":
            hits.append((node.lineno, ast.unparse(node) if hasattr(ast, "unparse") else "Sldr.Initialize(...)"))
    return hits


class TestSldrInitializeIsSinglePath:
    def test_no_executable_sldr_initialize_outside_flexinit(self):
        """
        Every executable `Sldr.Initialize(...)` call outside
        flexicon/code/FLExInit.py recreates the #264 race: a second,
        unguarded init path that throws InvalidOperationException whenever
        it loses the race to be first.
        """
        offenders = []
        for path in _iter_python_files():
            source = path.read_text(encoding="utf-8", errors="replace")
            if "Initialize" not in source:
                continue
            for lineno, snippet in _executable_sldr_initialize_calls(source, str(path)):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {snippet}")

        assert not offenders, (
            "Found Sldr.Initialize(...) calls outside "
            "flexicon/code/FLExInit.py. SLDR init must be owned solely by "
            "FLExInitialize()'s IsInitialized-guarded path:\n  "
            + "\n  ".join(offenders)
        )


# ---------------------------------------------------------------------------
# Marker coverage for ALL test modules that touch a real project
# ---------------------------------------------------------------------------
#
# A module that calls OpenProject()/FLExInitialize() or consumes one of the
# live-project fixtures against a real FLEx project, but is not marked
# requires_live_project, runs during the offline
# `pytest -m "not requires_live_project"` selector, which is exactly the
# oversight #264 found in flexicon/sync/tests/test_base_operations.py.
#
# Originally scoped to flexicon/sync/tests/ and keyed only on "OpenProject(".
# Widened (cycle 2, still #264) after the audit found the same bug class in
# flexicon/tests/test_FLExInit.py (bare FLExInitialize()/FLExCleanup()),
# flexicon/tests/test_FLExProject.py (OpenProject()), and
# tests/test_pattern_writing_systems_enumeration.py (sena3_sandbox fixture) --
# none of which live under flexicon/sync/tests/, so the old scope was
# structurally blind to all three.

_LIVE_FIXTURE_NAMES = {"target_project", "target_sandbox", "sena3_sandbox"}

# Files that reference OpenProject(/FLExInitialize(/a live fixture name but
# are deliberately excluded, with the reason inline. Every entry here was
# individually inspected in specs/264-conftest-sldr-order/reviews/
# cycle1-audit.md's "False positives eliminated by inspection" list.
_ALLOWLISTED_LIVE_ACCESS_FILES = {
    # target_project / sena3_sandbox here are Mock() attribute names set via
    # `self.target_project = Mock()` in setUp(), not pytest fixture
    # injection -- no real FLEx project is ever opened.
    REPO_ROOT / "flexicon" / "sync" / "tests" / "test_match_strategies.py",
    REPO_ROOT / "flexicon" / "sync" / "tests" / "test_merge_ops.py",
    REPO_ROOT / "flexicon" / "sync" / "tests" / "test_selective_import.py",
    REPO_ROOT / "flexicon" / "sync" / "tests" / "test_sync_engine.py",
    REPO_ROOT / "flexicon" / "sync" / "tests" / "test_validation.py",
    # Calls OpenProject() only with a deliberately nonexistent project name
    # to exercise the failure path; no real FieldWorks project is touched.
    REPO_ROOT / "tests" / "test_headless_lcm_ui.py",
    # Calls the guarded FLExInitialize() only to import types under a
    # live-environment guard; opens no project.
    REPO_ROOT / "tests" / "operations" / "test_issue272_service_locator_seam.py",
    # Calls FLExInit.FLExInitialize()/FLExCleanup() repeatedly, but every
    # CLR touchpoint (Sldr, FwRegistryHelper, etc.) is monkeypatched onto
    # FLExInit's module globals -- no real CLR/FieldWorks call ever happens
    # (see the module docstring). The live counterpart is
    # tests/operations/test_249_sldr_init_live.py.
    REPO_ROOT / "tests" / "test_249_sldr_init_guard.py",
}

_LIVE_ACCESS_SCAN_DIRS = (REPO_ROOT / "tests", REPO_ROOT / "flexicon")


def _iter_live_project_test_files():
    for base in _LIVE_ACCESS_SCAN_DIRS:
        for path in sorted(base.rglob("test_*.py")):
            if any(part in _SKIP_DIR_NAMES for part in path.relative_to(REPO_ROOT).parts):
                continue
            if path in _ALLOWLISTED_LIVE_ACCESS_FILES:
                continue
            yield path


def _calls_live_project_api(tree) -> bool:
    """AST-based: a real Call node invoking OpenProject(...) or
    FLExInitialize(...), regardless of import alias. Immune to the name
    merely appearing in a comment/docstring/string literal."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
        if name in ("OpenProject", "FLExInitialize"):
            return True
    return False


def _uses_live_fixture(tree) -> bool:
    """AST-based: a test function/method declares target_project,
    target_sandbox, or sena3_sandbox as a parameter (pytest fixture
    injection). Does not match `self.target_project = Mock()`, which is an
    attribute assignment, not a parameter -- so Mock-based unit tests are
    not flagged just for reusing these names."""
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        arg_names = {a.arg for a in node.args.args} | {a.arg for a in node.args.kwonlyargs}
        if arg_names & _LIVE_FIXTURE_NAMES:
            return True
    return False


def _sync_test_files_opening_a_project():
    for path in _iter_live_project_test_files():
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        if _calls_live_project_api(tree) or _uses_live_fixture(tree):
            yield path, source


def _has_requires_live_project_marker(source: str, filename: str) -> bool:
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        # Module-level: pytestmark = pytest.mark.requires_live_project
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "pytestmark" in targets and _names_pytest_mark(node.value):
                return True
        # Decorator form: @pytest.mark.requires_live_project
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            for dec in node.decorator_list:
                if _names_pytest_mark(dec):
                    return True
    return False


def _names_pytest_mark(node) -> bool:
    """True if `node` (or, for a Call, its func) resolves to
    pytest.mark.requires_live_project, possibly inside a list/tuple."""
    if isinstance(node, (ast.List, ast.Tuple)):
        return any(_names_pytest_mark(elt) for elt in node.elts)
    if isinstance(node, ast.Call):
        node = node.func
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "requires_live_project"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "pytest"
    )


class TestLiveProjectTestModulesMarkUsage:
    def test_every_live_project_test_carries_the_marker(self):
        """
        Regression pin for #264 item 2, widened in cycle 2: every
        tests/**/test_*.py or flexicon/**/test_*.py module that calls
        OpenProject()/FLExInitialize() or consumes the target_project /
        target_sandbox / sena3_sandbox fixtures must carry
        `requires_live_project` somewhere in the file, so it is excluded
        from the offline `-m "not requires_live_project"` selector.
        Previously scoped to flexicon/sync/tests/ only and keyed solely on
        "OpenProject(", which was structurally blind to
        flexicon/tests/test_FLExInit.py, flexicon/tests/test_FLExProject.py,
        and tests/test_pattern_writing_systems_enumeration.py.
        """
        offenders = []
        for path, source in _sync_test_files_opening_a_project():
            if not _has_requires_live_project_marker(source, str(path)):
                offenders.append(str(path.relative_to(REPO_ROOT)))

        assert not offenders, (
            "These test modules access a real FLEx project (OpenProject()/"
            "FLExInitialize()/a live fixture) but do not carry "
            "`requires_live_project` anywhere in the file:\n  " + "\n  ".join(offenders)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
