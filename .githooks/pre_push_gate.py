#
#   pre_push_gate.py
#
#   Class: (script)
#          Runs the full offline pytest gate before a push is accepted.
#          Invoked by the pre-push hook.
#
#   Platform: Python 3 (stdlib only -- must run on machines where the
#             flexicon package itself cannot be imported)
#
#   Copyright 2026
#

"""
Enforce the full offline gate before a push.

``CLAUDE.md`` already requires ``python -m pytest -m "not
requires_live_project" -q`` for every change, but evidence files kept
recording targeted subset runs instead (the #546 review caught one), and
red offline tests have reached ``main`` before (the #545 evidence records
4 failures pre-existing on clean ``origin/main``). The ubuntu CI workflow
cannot run this gate at all: importing the ``flexicon`` package executes
``FLExInit`` at module scope, which locates FieldWorks via the Windows
registry, so every test module touching the package fails at collection
without FieldWorks installed. The local gate is therefore the ONLY test
execution standing between a PR and ``main`` -- and it was honor-system.

This guard makes it mechanical: ``git push`` runs the full offline gate
first and the push is rejected when it fails.

Exit codes:
    0  gate passed (or explicitly skipped)
    1  gate failed; the push is rejected

Deliberate bypasses (both leave a trace on the pusher's side):
    git push --no-verify          skips ALL hooks, including this one
    FLEXICON_SKIP_OFFLINE_GATE=1  skips just this gate (e.g. pushing from
                                  a machine without the dev dependencies).

If ``pytest`` itself is missing or broken, that is a failure, not a skip:
a gate that goes quiet when the toolchain is absent is the fail-open hole
this guard exists to close. Install the dev dependencies
(``pip install -r requirements.txt``) and retry.
"""

import os
import subprocess
import sys

#: The exact offline invocation CLAUDE.md requires. Kept as one list so the
#: guard, its tests, and the docs cannot drift apart.
OFFLINE_GATE_ARGS = ["-m", "pytest", "-m", "not requires_live_project", "-q"]

#: Targeted skip for this gate only. `--no-verify` remains the broad hammer.
SKIP_ENV_VAR = "FLEXICON_SKIP_OFFLINE_GATE"


def find_repo_root(hook_file):
    """Return the repository top level for a hook living in .githooks/.

    Prefers ``git rev-parse --show-toplevel`` (correct even when
    core.hooksPath points elsewhere); falls back to the hook directory's
    parent, which is right for the standard in-repo layout.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except OSError:
        pass
    return os.path.dirname(os.path.dirname(os.path.abspath(hook_file)))


def gate_command(python_exe=None):
    """Build the offline-gate argv for the given Python executable."""
    return [(python_exe or sys.executable or "python")] + list(OFFLINE_GATE_ARGS)


def run_gate(repo_root, python_exe=None, runner=None):
    """Execute the offline gate in repo_root; return its exit code.

    Output streams straight through so the pusher watches progress live.
    ``runner`` is a test seam for subprocess.run.
    """
    run = runner or subprocess.run
    completed = run(
        gate_command(python_exe),
        cwd=repo_root,
    )
    return completed.returncode


def main(argv=None, runner=None):
    """Entry point. Returns a process exit code (0 push, 1 reject)."""
    if os.environ.get(SKIP_ENV_VAR) == "1":
        print(
            "[WARN] pre-push: %s=1; offline gate SKIPPED" % SKIP_ENV_VAR
        )
        return 0

    repo_root = find_repo_root(__file__)
    print("[INFO] pre-push: running full offline gate "
          "(%s) ..." % " ".join(gate_command()))
    returncode = run_gate(repo_root, runner=runner)
    if returncode != 0:
        print(
            "[ERROR] pre-push: offline gate FAILED (exit %d); "
            "push rejected." % returncode,
            file=sys.stderr,
        )
        print(
            "[ERROR] Fix the failures and retry. To push anyway: "
            "`git push --no-verify`, or set %s=1 to skip just this "
            "gate." % SKIP_ENV_VAR,
            file=sys.stderr,
        )
        return 1
    print("[OK] pre-push: offline gate passed; pushing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
