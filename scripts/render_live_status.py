#!/usr/bin/env python3
"""
Render tests/LIVE_STATUS.md from tests/live_status.json.

Reads the JSON ledger emitted by pytest's session-finish hook (see
tests/flex_plugin.py) and writes a human-readable Markdown table that
summarises which Operations classes have live coverage for each CRUD
phase (read / add / reorder / modify / delete).

Run from the repo root:

    python scripts/render_live_status.py

Optional positional arg overrides the default JSON location:

    python scripts/render_live_status.py path/to/live_status.json

If the JSON is missing or empty, a "no live runs recorded yet" stub is
written so the markdown file still exists and reads cleanly.

ASCII-only output -- no emoji, no Unicode bullets. See CLAUDE.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


PHASES = ("read", "add", "reorder", "modify", "delete")
STATUS_BADGE = {
    "pass": "[PASS]",
    "fail": "[FAIL]",
    "skip": "[SKIP]",
    "untested": "[----]",
}


def _badge(status):
    return STATUS_BADGE.get(status, "[----]")


def _stub_markdown():
    return (
        "# Sena 3 Real-World Status\n"
        "\n"
        "No live test runs have been recorded yet.\n"
        "\n"
        "Run the live suite to populate this ledger:\n"
        "\n"
        "    pytest -m requires_live_project\n"
        "\n"
        "See `tests/LIVE_TESTING.md` for the full workflow.\n"
    )


def _render(payload):
    """Render the ledger payload as Markdown text."""
    by_class = payload.get("by_class") or {}
    if not by_class:
        body = _stub_markdown().rstrip() + "\n"
        timestamp = payload.get("run_timestamp")
        if timestamp:
            body = body.replace(
                "No live test runs have been recorded yet.",
                f"Last run: {timestamp}\n\nNo per-class coverage recorded "
                "(all live tests missing `live_phase` markers).",
            )
        return body

    lines = []
    lines.append("# Sena 3 Real-World Status")
    lines.append("")
    timestamp = payload.get("run_timestamp", "(unknown)")
    lines.append(f"Last run: {timestamp}")
    lines.append("")
    lines.append(
        "Legend: `[PASS]` verified - `[FAIL]` regressed - "
        "`[SKIP]` skipped this run - `[----]` untested"
    )
    lines.append("")

    classes = sorted(by_class.keys())
    name_col_width = max(len("Operations class"), *(len(c) for c in classes))
    phase_col_width = 7  # width of "[PASS] " and the phase header
    header_phases = [p.capitalize().ljust(phase_col_width) for p in PHASES]
    last_verified_width = len("Last verified")

    header = "| {name} | {phases} | {lv} |".format(
        name="Operations class".ljust(name_col_width),
        phases=" | ".join(h.ljust(phase_col_width) for h in header_phases),
        lv="Last verified".ljust(last_verified_width),
    )
    sep = "|{name}|{phases}|{lv}|".format(
        name="-" * (name_col_width + 2),
        phases="|".join("-" * (phase_col_width + 2) for _ in PHASES),
        lv="-" * (last_verified_width + 2),
    )
    lines.append(header)
    lines.append(sep)

    for cls_name in classes:
        cells = by_class[cls_name]
        phase_badges = []
        verifications = []
        for phase in PHASES:
            cell = cells.get(phase) or {"status": "untested", "last_verified": None}
            phase_badges.append(_badge(cell.get("status", "untested")))
            if cell.get("last_verified"):
                verifications.append(cell["last_verified"])
        # Newest last_verified across phases.
        last_verified = max(verifications) if verifications else ""
        row = "| {name} | {phases} | {lv} |".format(
            name=cls_name.ljust(name_col_width),
            phases=" | ".join(b.ljust(phase_col_width) for b in phase_badges),
            lv=last_verified.ljust(last_verified_width),
        )
        lines.append(row)

    lines.append("")

    uncategorized = payload.get("uncategorized_live_tests") or []
    lines.append("## Uncategorized live tests")
    lines.append("")
    if uncategorized:
        lines.append("Tests marked `requires_live_project` but missing `live_phase`:")
        lines.append("")
        for nodeid in uncategorized:
            lines.append(f"- `{nodeid}`")
    else:
        lines.append("None. All recorded live tests carry `live_phase` metadata.")
    lines.append("")

    return "\n".join(lines)


def _resolve_paths(json_arg):
    """Return (json_path, out_path) given an optional CLI override."""
    here = Path(__file__).resolve().parent
    repo_root = here.parent
    tests_dir = repo_root / "tests"
    default_json = tests_dir / "live_status.json"
    json_path = Path(json_arg).resolve() if json_arg else default_json
    out_path = tests_dir / "LIVE_STATUS.md"
    return json_path, out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "json_path",
        nargs="?",
        default=None,
        help="Path to live_status.json (defaults to tests/live_status.json)",
    )
    args = parser.parse_args(argv)

    json_path, out_path = _resolve_paths(args.json_path)

    payload = None
    if json_path.exists():
        try:
            # utf-8-sig tolerates a stray BOM (PowerShell's Set-Content
            # default on older systems) without failing to parse.
            text = json_path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            print(f"[WARN] Could not read {json_path}: {exc}", file=sys.stderr)
            text = ""
        if text.strip():
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                print(
                    f"[WARN] {json_path} is not valid JSON: {exc}. "
                    "Falling back to stub markdown.",
                    file=sys.stderr,
                )

    if not payload:
        markdown = _stub_markdown()
    else:
        markdown = _render(payload)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8", newline="\n")
    print(f"[OK] Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
