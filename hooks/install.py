#!/usr/bin/env python
#
#   install.py
#
#   Installs git hooks from hooks/ into .git/hooks/.
#   Run once per machine: python hooks/install.py
#
#   Copyright 2025
#

"""
Install local git hooks for flexicon development.

These hooks only run on your machine -- they are never pushed to CI.

Usage::

    python hooks/install.py          # install hooks
    python hooks/install.py --remove # uninstall hooks
"""

import os
import shutil
import stat
import sys
from pathlib import Path


HOOKS_DIR = Path(__file__).parent
REPO_ROOT = HOOKS_DIR.parent
GIT_HOOKS_DIR = REPO_ROOT / ".git" / "hooks"

# Hook files to install (filename must match git hook name)
HOOKS = ["pre-commit"]


def install():
    if not GIT_HOOKS_DIR.exists():
        print(f"[ERROR] Not a git repo: {GIT_HOOKS_DIR} does not exist")
        sys.exit(1)

    for hook_name in HOOKS:
        src = HOOKS_DIR / hook_name
        dst = GIT_HOOKS_DIR / hook_name

        if not src.exists():
            print(f"[WARN] Hook source not found: {src}")
            continue

        # Back up existing hook if it's not ours
        if dst.exists():
            content = dst.read_text(encoding="utf-8", errors="replace")
            if "LCM contract tests" not in content:
                backup = dst.with_suffix(".backup")
                shutil.copy2(dst, backup)
                print(f"[INFO] Backed up existing {hook_name} to {backup.name}")

        shutil.copy2(src, dst)
        # Make executable
        dst.chmod(dst.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"[DONE] Installed {hook_name} -> .git/hooks/{hook_name}")

    print()
    print("Hooks installed. They run automatically on 'git commit'.")
    print("To skip once: SKIP_CONTRACT_TESTS=1 git commit ...")
    print("To uninstall: python hooks/install.py --remove")


def remove():
    for hook_name in HOOKS:
        dst = GIT_HOOKS_DIR / hook_name
        if dst.exists():
            content = dst.read_text(encoding="utf-8", errors="replace")
            if "LCM contract tests" in content:
                dst.unlink()
                print(f"[DONE] Removed {hook_name}")
                # Restore backup if present
                backup = dst.with_suffix(".backup")
                if backup.exists():
                    shutil.move(str(backup), str(dst))
                    print(f"[INFO] Restored {hook_name} from backup")
            else:
                print(f"[WARN] {hook_name} is not ours, skipping")
        else:
            print(f"[INFO] {hook_name} not installed")


if __name__ == "__main__":
    if "--remove" in sys.argv:
        remove()
    else:
        install()
