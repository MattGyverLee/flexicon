#
#   test_pre_push_gate.py
#
#   Class: TestPrePushGate
#          Coverage for the pre-push offline-gate guard in
#          .githooks/pre_push_gate.py.
#
#   Platform: Python 3 (stdlib only -- this file must never import the
#             flexicon package, so the guard stays verifiable on
#             machines without FieldWorks, including ubuntu CI)
#
#   Copyright 2026
#

"""
Tests for the pre-push offline-gate guard.

The guard exists because the full offline gate
(``python -m pytest -m "not requires_live_project" -q``) cannot run in CI
-- importing the flexicon package executes FLExInit at module scope, which
requires FieldWorks -- so the local gate is the only test execution
between a PR and main. Targeted subset runs kept standing in for the full
gate (caught in the #546 review), and red offline tests have reached main
before (noted in the #545 evidence). The guard makes the full gate
mechanical at push time.

The guard must satisfy two competing requirements, so both are pinned here:

  1. A failing gate must reject the push (exit 1). A guard that goes
     quiet on failure is the fail-open hole it exists to close.
  2. It must not brick pushes for non-gate reasons: an explicit skip
     (env var) passes without invoking pytest at all, and the repo-root
     lookup degrades gracefully outside a git checkout.

No test here runs the real gate (that would recurse into pytest); the
subprocess runner is always stubbed.
"""

import importlib.util
import os
import pathlib

import pytest

GUARD_PATH = (pathlib.Path(__file__).resolve().parents[1]
              / ".githooks" / "pre_push_gate.py")


def _load_guard():
    spec = importlib.util.spec_from_file_location("pre_push_gate", GUARD_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def guard():
    if not GUARD_PATH.exists():
        pytest.skip("pre-push guard not present")
    return _load_guard()


class _Completed:
    def __init__(self, returncode):
        self.returncode = returncode


def _passing_runner(calls):
    def _run(argv, **kwargs):
        calls.append((argv, kwargs))
        return _Completed(0)
    return _run


def _failing_runner(calls, code=1):
    def _run(argv, **kwargs):
        calls.append((argv, kwargs))
        return _Completed(code)
    return _run


class TestGateCommand:
    def test_runs_the_full_offline_gate_not_a_subset(self, guard):
        """The guarded invocation must be exactly the CLAUDE.md gate."""
        assert guard.gate_command("python") == [
            "python", "-m", "pytest",
            "-m", "not requires_live_project", "-q",
        ]

    def test_no_directory_or_file_targets(self, guard):
        """A file/dir target would silently shrink the gate to a subset."""
        argv = guard.gate_command("python")
        assert argv.count("-m") == 2, (
            "gate argv must contain only the two -m flags "
            "(pytest module + marker expression)"
        )
        assert not any(
            a.endswith(".py") or "/" in a or "\\" in a for a in argv[1:]
        ), "gate argv must not name test paths: %r" % (argv,)


class TestMain:
    def test_passing_gate_allows_push(self, guard, monkeypatch):
        calls = []
        monkeypatch.delenv(guard.SKIP_ENV_VAR, raising=False)
        assert guard.main(runner=_passing_runner(calls)) == 0
        assert len(calls) == 1

    def test_failing_gate_rejects_push(self, guard, monkeypatch):
        calls = []
        monkeypatch.delenv(guard.SKIP_ENV_VAR, raising=False)
        assert guard.main(runner=_failing_runner(calls)) == 1
        assert len(calls) == 1

    def test_pytest_exit_code_propagates_to_rejection(self, guard, monkeypatch):
        """Any nonzero pytest exit (failures, errors, misuse) rejects."""
        monkeypatch.delenv(guard.SKIP_ENV_VAR, raising=False)
        for code in (1, 2, 4, 5):
            assert guard.main(
                runner=_failing_runner([], code=code)) == 1, (
                "pytest exit %d must reject the push" % code
            )

    def test_skip_env_var_never_invokes_pytest(self, guard, monkeypatch):
        calls = []
        monkeypatch.setenv(guard.SKIP_ENV_VAR, "1")
        assert guard.main(runner=_failing_runner(calls)) == 0
        assert calls == [], (
            "the skip path must not invoke pytest at all -- otherwise "
            "there is no escape from a spuriously failing gate"
        )

    def test_gate_runs_in_repo_root(self, guard, monkeypatch):
        calls = []
        monkeypatch.delenv(guard.SKIP_ENV_VAR, raising=False)
        guard.main(runner=_passing_runner(calls))
        run_cwd = calls[0][1].get("cwd")
        assert run_cwd and os.path.isdir(run_cwd), (
            "gate must run with cwd set to a real directory"
        )
        assert os.path.isdir(os.path.join(run_cwd, ".githooks")), (
            "gate cwd %r does not look like the repo root" % (run_cwd,)
        )


class TestFindRepoRoot:
    def test_falls_back_to_hook_parent_without_git(self, guard, monkeypatch):
        """Outside a git checkout the hook-dir parent is the root."""

        def _boom(*args, **kwargs):
            raise OSError("no git here")

        monkeypatch.setattr(guard.subprocess, "run", _boom)
        root = guard.find_repo_root(str(GUARD_PATH))
        assert os.path.isdir(os.path.join(root, ".githooks"))
