#
#   restore_target.py
#
#   Restore the Target fixture from tests/fixtures/Target *.fwbackup
#   into the user's FieldWorks projects directory, overwriting any
#   existing Target project.
#
#   Target is the *scratch* live-test project: a mostly-blank FLEx
#   database used for write-path verification (create / modify / delete
#   against a clean slate). Sena 3 is the *full* example project, used
#   for read-path and modify-pre-existing-data coverage.
#
#   Run before a live-DB write session to guarantee a clean baseline.
#   Re-run after any session to wipe accumulated test mutations.
#
#   Platform: Windows + Python (FieldWorks 9+ installed)
#
#   Copyright 2026
#

import argparse
import sys
from pathlib import Path

# Shared restore helpers live alongside restore_sena3.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fw_restore import (  # noqa: E402
    check_state,
    find_fw_projects_dir,
    find_fwbackup,
    restore_project,
)

_DEFAULT_TARGET = "Target"
_BACKUP_PATTERN = "Target*.fwbackup"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Restore the Target .fwbackup fixture (blank scratch project) "
            "into the FieldWorks projects directory."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report current state without modifying anything.",
    )
    parser.add_argument(
        "--target",
        default=_DEFAULT_TARGET,
        help=f"Project name to restore as (default: {_DEFAULT_TARGET!r}).",
    )
    parser.add_argument(
        "--fixtures",
        default=None,
        help=(
            "Override path to fixtures directory "
            "(default: <repo>/tests/fixtures)."
        ),
    )
    parser.add_argument(
        "--projects-dir",
        default=None,
        help=(
            "Override FieldWorks projects directory "
            "(default: registry or %%LOCALAPPDATA%%\\SIL\\FieldWorks\\9\\Projects)."
        ),
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    fixtures_dir = (
        Path(args.fixtures) if args.fixtures else repo_root / "tests" / "fixtures"
    )
    projects_dir = (
        Path(args.projects_dir) if args.projects_dir else find_fw_projects_dir()
    )

    if projects_dir is None:
        print(
            "[ERROR] Could not locate FieldWorks projects directory. "
            "Pass --projects-dir to override.",
            file=sys.stderr,
        )
        return 2

    if args.check:
        check_state(projects_dir, args.target)
        return 0

    fwbackup = find_fwbackup(fixtures_dir, _BACKUP_PATTERN)
    if fwbackup is None:
        print(
            f"[ERROR] No {_BACKUP_PATTERN!r} found in {fixtures_dir}",
            file=sys.stderr,
        )
        return 2

    try:
        restore_project(fwbackup, projects_dir, args.target)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
