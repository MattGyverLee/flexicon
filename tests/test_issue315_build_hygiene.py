#
#   test_issue315_build_hygiene.py
#
#   Offline ratchet for issue #315: build/ packaging artifacts must stay
#   gitignored and untracked (stale build/lib/flexicon/ trap).
#
#   Copyright 2026
#

import subprocess
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_issue315_build_directory_gitignored():
    gitignore = (_repo_root() / ".gitignore").read_text(encoding="utf-8")
    lines = {ln.strip() for ln in gitignore.splitlines() if ln.strip()}
    assert "build/" in lines, "build/ must be listed in .gitignore (issue #315)"


def test_issue315_no_tracked_files_under_build():
    root = _repo_root()
    proc = subprocess.run(
        ["git", "ls-files", "build/"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    tracked = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    assert tracked == [], (
        "No paths under build/ may be tracked in git (issue #315); "
        f"found: {tracked[:5]}"
    )


def test_issue315_git_check_ignore_build_path():
    root = _repo_root()
    proc = subprocess.run(
        ["git", "check-ignore", "-v", "build/lib/flexicon/__init__.py"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        "git check-ignore must classify build/lib/flexicon paths as ignored "
        f"(issue #315); stderr={proc.stderr!r}"
    )
    assert ".gitignore" in proc.stdout
