#
#   fw_restore.py
#
#   Shared helpers for restoring a FieldWorks .fwbackup fixture into the
#   local FieldWorks projects directory.
#
#   Used by scripts/restore_sena3.py (full example project) and
#   scripts/restore_target.py (blank scratch project). Neither script
#   should duplicate this logic.
#
#   Platform: Windows + Python (FieldWorks 9+ installed)
#
#   Copyright 2026
#

import os
import shutil
import zipfile
from pathlib import Path


_REGISTRY_KEY = r"SOFTWARE\SIL\FieldWorks\9"


def find_fw_projects_dir():
    """Return the FieldWorks 9 projects directory as a Path, or None."""
    try:
        import winreg

        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(hive, _REGISTRY_KEY) as key:
                    value, _ = winreg.QueryValueEx(key, "ProjectsDir")
                    if value and os.path.isdir(value):
                        return Path(value)
            except OSError:
                continue
    except ImportError:
        pass

    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidate = Path(local) / "SIL" / "FieldWorks" / "9" / "Projects"
        if candidate.exists():
            return candidate

    return None


def find_fwbackup(fixtures_dir, pattern):
    """Locate the most recent matching .fwbackup in fixtures_dir."""
    fixtures_dir = Path(fixtures_dir)
    if not fixtures_dir.exists():
        return None
    matches = sorted(fixtures_dir.glob(pattern))
    return matches[-1] if matches else None


def restore_project(fwbackup_path, projects_dir, target_name):
    """
    Unzip fwbackup_path and place its contents under projects_dir/target_name.
    Removes any existing target_dir first. Returns the target_dir.
    """
    fwbackup_path = Path(fwbackup_path)
    projects_dir = Path(projects_dir)
    target_dir = projects_dir / target_name

    if not fwbackup_path.exists():
        raise FileNotFoundError(f"Backup not found: {fwbackup_path}")
    if not projects_dir.exists():
        raise FileNotFoundError(f"Projects directory not found: {projects_dir}")

    if target_dir.exists():
        print(f"[INFO] Removing existing {target_dir}")
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True)
    print(f"[INFO] Unzipping {fwbackup_path.name} -> {target_dir}")
    with zipfile.ZipFile(fwbackup_path) as zf:
        zf.extractall(target_dir)

    fwdatas = list(target_dir.glob("*.fwdata"))
    if not fwdatas:
        raise RuntimeError(
            f"No .fwdata found after extraction into {target_dir}; "
            "backup file may be malformed."
        )

    print(f"[OK] Restored {target_name} -> {fwdatas[0]}")
    return target_dir


def check_state(projects_dir, target_name):
    """Report current state of target project. Returns True if present."""
    projects_dir = Path(projects_dir)
    target_dir = projects_dir / target_name
    if not target_dir.exists():
        print(f"[INFO] {target_name} not present in {projects_dir}")
        return False

    fwdatas = list(target_dir.glob("*.fwdata"))
    if not fwdatas:
        print(f"[WARN] {target_dir} exists but contains no .fwdata")
        return False

    print(f"[INFO] {target_name} present: {fwdatas[0]}")
    return True
