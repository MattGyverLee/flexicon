#
#   crystallization_metric.py
#
#   Module: Measure repo crystallization -- stable, consistent, complete LCM
#           wrapper coverage where work converges instead of expanding.
#           Distinct from the live-DB coverage metric (live_coverage_metric.py).
#
#           Three independent axes:
#             1. Coverage   -- how much of the Operations surface is stabilized
#             2. Stability  -- git churn over 30- and 90-day rolling windows
#             3. Regression -- have previously-stabilized classes stayed stable?
#
#           Combined into a single crystallization score (0.00 - 1.00).
#
#   Usage:  python scripts/crystallization_metric.py
#
#   Platform: Python 3 (stdlib only)
#
#   Copyright 2026
#

import datetime
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHASES = ("read", "add", "reorder", "modify", "delete")
STATUS_GLYPH = {"pass": "[PASS]", "fail": "[FAIL]", "skip": "[SKIP]"}
TOTAL_CLASSES_EXPECTED = 60  # canonical denominator; matches live_coverage_metric.py

# Score formula weights
W_COVERAGE = 0.5
W_STABILITY = 0.3
W_REGRESSION = 0.2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pct(n: int, d: int) -> str:
    return f"{(n / d * 100):.1f}%" if d else "n/a"


# ---------------------------------------------------------------------------
# Class inventory (duplicated from live_coverage_metric.py -- intentionally;
# no shared helper until there are more callers)
# ---------------------------------------------------------------------------

def scan_operations_classes(root: Path) -> dict:
    """
    Scan flexicon/code for *Operations.py files (excluding BaseOperations).
    Returns dict: class_name -> {"path": posix_str, "methods": set}

    Raises FileNotFoundError if code_dir is missing, or exists but yields no
    *Operations.py files. Path.rglob() on a missing/wrong directory returns
    no matches WITHOUT raising, which previously let this script (and
    live_coverage_metric.py) silently report zero Operations classes for
    months after the flexlibs2 -> flexicon rename went unnoticed here (see
    the issue #240 audit). Do not let that degrade silently again.
    """
    classes = {}
    code_dir = root / "flexicon" / "code"
    if not code_dir.is_dir():
        raise FileNotFoundError(
            f"scan_operations_classes: {code_dir} does not exist. "
            "Path.rglob() on a missing directory returns no matches without "
            "raising, so this would otherwise silently report zero "
            "Operations classes instead of erroring. Check for a package "
            "rename, or pass the correct repo root."
        )
    for path in code_dir.rglob("*Operations.py"):
        if path.name == "BaseOperations.py":
            continue
        class_name = path.stem
        text = path.read_text(encoding="utf-8")
        methods = set(re.findall(
            r"@OperationsMethod\s*\n\s*def\s+([A-Za-z_][A-Za-z_0-9]*)",
            text,
        ))
        methods = {m for m in methods if not m.startswith("_")}
        classes[class_name] = {
            "path": path.relative_to(root).as_posix(),
            "methods": methods,
        }
    if not classes:
        raise FileNotFoundError(
            f"scan_operations_classes: {code_dir} exists but no "
            "*Operations.py files were found beneath it. This scan should "
            "discover ~80+ Operations classes; zero means the directory is "
            "wrong or empty -- treat this as a hard failure, not an empty "
            "report."
        )
    return classes


# ---------------------------------------------------------------------------
# Coverage axis  (re-derived from live_status.json)
# ---------------------------------------------------------------------------

def load_live_status(root: Path):
    p = root / "tests" / "live_status.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def phase_outcomes(status) -> dict:
    """
    Returns dict: (class_name, phase) -> "pass" | "fail" | "skip"
    Resolves conflicts: fail beats all; pass beats skip.
    """
    if not status:
        return {}
    out = {}
    for info in status.get("by_test", {}).values():
        cls = info.get("operations_class")
        ph = info.get("phase")
        st = info.get("status")
        if not (cls and ph and st):
            continue
        prev = out.get((cls, ph))
        if prev is None:
            out[(cls, ph)] = st
        elif st == "fail":
            out[(cls, ph)] = "fail"
        elif prev == "pass" and st == "skip":
            pass  # pass wins
        elif prev == "skip" and st == "pass":
            out[(cls, ph)] = "pass"
    return out


def _is_stabilized(glyphs: list) -> bool:
    return all(g in ("[PASS]", "[SKIP]") for g in glyphs) and "[PASS]" in glyphs


def compute_coverage(classes: dict, outcomes: dict) -> dict:
    """
    Returns coverage summary dict.
    Keys: stabilized_classes (list), stabilized (int), total_classes (int),
          phase_pass (int), phase_total (int), methods_exercised (int),
          methods_total (int), class_rows (list of (name, glyphs))
    """
    n_total = len(classes)
    rows = []
    for cls in sorted(classes):
        glyphs = []
        for ph in PHASES:
            st = outcomes.get((cls, ph))
            if st is None:
                glyphs.append("[----]")
            else:
                glyphs.append(STATUS_GLYPH.get(st, "[????]"))
        rows.append((cls, glyphs))

    stabilized_rows = [(c, g) for c, g in rows if _is_stabilized(g)]
    stabilized_classes = [c for c, _ in stabilized_rows]

    phase_total = n_total * len(PHASES)
    phase_pass = sum(1 for _, g in rows for x in g if x == "[PASS]")
    phase_skip = sum(1 for _, g in rows for x in g if x == "[SKIP]")

    methods_total = sum(len(classes[c]["methods"]) for c in classes)
    # For methods_exercised we count methods that appear in at least one live
    # test file for any class (approximation consistent with live_coverage_metric).
    tests_dir = repo_root() / "tests" / "operations"
    all_called: set = set()
    for path in tests_dir.glob("test_*_live.py"):
        text = path.read_text(encoding="utf-8")
        for name in re.findall(r"\.([A-Z][A-Za-z_0-9]*)\s*\(", text):
            all_called.add(name)
    methods_exercised = sum(
        len(classes[c]["methods"] & all_called) for c in classes
    )

    return {
        "stabilized_classes": stabilized_classes,
        "stabilized": len(stabilized_classes),
        "total_classes": n_total,
        "phase_pass": phase_pass,
        "phase_skip": phase_skip,
        "phase_total": phase_total,
        "methods_exercised": methods_exercised,
        "methods_total": methods_total,
        "class_rows": rows,
        "stabilized_rows": stabilized_rows,
    }


# ---------------------------------------------------------------------------
# Stability axis  (git churn)
# ---------------------------------------------------------------------------

def _parse_git_numstat(output: str) -> list:
    """
    Parse output of `git log --numstat --format="COMMIT <hash> <date>" ...`
    Returns list of dicts: {"date": datetime, "path": str, "added": int, "removed": int}
    """
    records = []
    current_date = None
    for line in output.splitlines():
        if line.startswith("COMMIT "):
            parts = line.split()
            # parts: ["COMMIT", hash, date_part, time_part, tz_part]
            if len(parts) >= 3:
                try:
                    # e.g. "2026-05-30 01:09:12 -0500"
                    date_str = parts[2]
                    current_date = datetime.date.fromisoformat(date_str)
                except ValueError:
                    current_date = None
        elif line.strip() == "" or current_date is None:
            continue
        else:
            # numstat line: "<added>\t<removed>\t<path>"
            cols = line.split("\t", 2)
            if len(cols) == 3:
                added_str, removed_str, fpath = cols
                # Renames appear as "old => new" inside braces or as two
                # separate filenames.  We normalise to the destination path.
                # Binary files show "-" for counts; skip them.
                if added_str == "-" or removed_str == "-":
                    continue
                try:
                    added = int(added_str)
                    removed = int(removed_str)
                except ValueError:
                    continue
                records.append({
                    "date": current_date,
                    "path": fpath.strip(),
                    "added": added,
                    "removed": removed,
                })
    return records


def _git_churn(root: Path, since_days: int) -> tuple:
    """
    Run git log --numstat for the past `since_days` days over flexicon/code/.
    Returns (records, error_msg).  error_msg is None on success.
    Tolerates missing git gracefully.

    Only the current path (flexicon/code/) is scanned, not the pre-rename
    flexlibs2/code/ path. `git log --follow` does not work for directory
    pathspecs, and passing both pathspecs would double-count the rename
    commit itself (old-path deletions + new-path additions showing as churn
    on a commit that changed no actual code). Since these are short rolling
    windows (30d/90d) evaluated relative to "now", any gap this introduces
    is transient: it self-heals once 90 days have elapsed since the rename
    (2026-07-04, commit 9b82ffaf), after which every commit in the window
    is naturally under flexicon/code/ anyway.
    """
    since = f"{since_days} days ago"
    cmd = [
        "git", "log",
        "--numstat",
        f"--since={since}",
        "--format=COMMIT %H %ai",
        "--",
        "flexicon/code/",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return [], f"git exited {result.returncode}: {result.stderr.strip()}"
        return _parse_git_numstat(result.stdout), None
    except FileNotFoundError:
        return [], "git not found in PATH"
    except subprocess.TimeoutExpired:
        return [], "git timed out after 30s"


def compute_churn(root: Path, classes: dict) -> dict:
    """
    Returns churn summary:
      churn_30d (int), churn_90d (int), per_class_30d (dict), per_class_90d (dict),
      per_class_last_touched (dict), git_error (str|None)
    """
    records_90, err = _git_churn(root, 90)
    records_30 = [r for r in records_90 if
                  r["date"] >= (datetime.date.today() - datetime.timedelta(days=30))]

    # Build stem -> list of records mappings
    # An Operations file path looks like flexicon/code/.../FooOperations.py
    stem_records_90: dict = defaultdict(list)
    stem_records_30: dict = defaultdict(list)
    for r in records_90:
        stem = Path(r["path"]).stem
        stem_records_90[stem].append(r)
    for r in records_30:
        stem = Path(r["path"]).stem
        stem_records_30[stem].append(r)

    def _sum_churn(recs: list) -> int:
        return sum(r["added"] + r["removed"] for r in recs)

    def _last_touched(recs: list):
        if not recs:
            return None
        return max(r["date"] for r in recs)

    per_class_90 = {c: _sum_churn(stem_records_90.get(c, [])) for c in classes}
    per_class_30 = {c: _sum_churn(stem_records_30.get(c, [])) for c in classes}
    per_class_last = {c: _last_touched(stem_records_90.get(c, [])) for c in classes}

    churn_30 = sum(per_class_30.values())
    churn_90 = sum(per_class_90.values())

    return {
        "churn_30d": churn_30,
        "churn_90d": churn_90,
        "per_class_30d": per_class_30,
        "per_class_90d": per_class_90,
        "per_class_last_touched": per_class_last,
        "git_error": err,
    }


# ---------------------------------------------------------------------------
# Regression axis  (history comparison)
# ---------------------------------------------------------------------------

def load_history(root: Path) -> list:
    p = root / "tests" / "crystallization_history.jsonl"
    if not p.exists():
        return []
    records = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def compute_regression(coverage: dict, history: list) -> dict:
    """
    Compare current stabilized set to last history entry.
    Returns: regressed (list), newly_stabilized (list),
             stabilized_ever (list), still_stabilized (int), regression_factor (float)
    """
    if not history:
        # No prior data -- regression factor neutral (assume 1.0)
        return {
            "regressed": [],
            "newly_stabilized": [],
            "stabilized_ever": list(coverage["stabilized_classes"]),
            "still_stabilized": coverage["stabilized"],
            "regression_factor": 1.0,
        }

    # Collect all classes ever stabilized across full history + current run
    stabilized_ever_set: set = set()
    for entry in history:
        stabilized_ever_set.update(entry.get("stabilized_classes", []))

    # Compare to current
    current_set = set(coverage["stabilized_classes"])
    prev_entry = history[-1]
    prev_set = set(prev_entry.get("stabilized_classes", []))

    # Union with current so newly-stabilized classes count as "ever"
    stabilized_ever_union = stabilized_ever_set | current_set

    regressed = sorted(stabilized_ever_set - current_set)
    newly_stabilized = sorted(current_set - prev_set)

    stabilized_ever = sorted(stabilized_ever_union)
    still_stabilized = len(current_set & stabilized_ever_union)
    n_ever = len(stabilized_ever_union)

    # If nothing has ever been stabilized, regression is not yet applicable.
    # Treat as neutral (1.0) so coverage and stability drive the score.
    if n_ever == 0:
        regression_factor = 1.0
    else:
        regression_factor = still_stabilized / n_ever

    return {
        "regressed": regressed,
        "newly_stabilized": newly_stabilized,
        "stabilized_ever": stabilized_ever,
        "still_stabilized": still_stabilized,
        "regression_factor": regression_factor,
    }


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def compute_score(coverage: dict, churn: dict, regression: dict) -> dict:
    """
    Returns score dict with all components.

    score = 0.5 * (stabilized/total) + 0.3 * stability_factor + 0.2 * regression_factor

    stability_factor = max(0, 1 - churn_30d / max(1, churn_90d_baseline_avg))
    where churn_90d_baseline_avg = churn_90d / 3  (i.e., the 30-day rolling avg
    implied by 90 days; if churn is evenly spread, this equals churn_30d --
    meaning steady-state scores 0.0.  Lower-than-baseline 30d churn scores > 0.)

    regression_factor = still_stabilized / max(1, stabilized_ever)
    """
    total = max(1, TOTAL_CLASSES_EXPECTED)
    coverage_factor = coverage["stabilized"] / total

    churn_30 = churn["churn_30d"]
    churn_90 = churn["churn_90d"]
    # Baseline: expected 30-day churn if pace were constant over 90 days
    churn_90d_baseline_avg = churn_90 / 3
    stability_factor = max(0.0, 1.0 - churn_30 / max(1, churn_90d_baseline_avg))

    regression_factor = regression["regression_factor"]

    score = (
        W_COVERAGE * coverage_factor
        + W_STABILITY * stability_factor
        + W_REGRESSION * regression_factor
    )

    return {
        "score": round(score, 4),
        "coverage_factor": round(coverage_factor, 4),
        "stability_factor": round(stability_factor, 4),
        "regression_factor": round(regression_factor, 4),
        "churn_30d": churn_30,
        "churn_90d": churn_90,
        "churn_90d_baseline_avg": round(churn_90d_baseline_avg, 1),
    }


# ---------------------------------------------------------------------------
# History append
# ---------------------------------------------------------------------------

def append_history(root: Path, coverage: dict, churn: dict, scored: dict, ts: str):
    record = {
        "ts": ts,
        "stabilized": coverage["stabilized"],
        "stabilized_classes": sorted(coverage["stabilized_classes"]),
        "total_classes": coverage["total_classes"],
        "phase_pass": coverage["phase_pass"],
        "phase_total": coverage["phase_total"],
        "methods_exercised": coverage["methods_exercised"],
        "methods_total": coverage["methods_total"],
        "churn_30d": churn["churn_30d"],
        "churn_90d": churn["churn_90d"],
        "score": scored["score"],
    }
    p = root / "tests" / "crystallization_history.jsonl"
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_report(
    ts: str,
    coverage: dict,
    churn: dict,
    regression: dict,
    scored: dict,
) -> str:
    lines = []

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    lines += [
        "# Crystallization Metric",
        "",
        f"Last computed: {ts}",
        "",
        "The project goal is a stable, consistent, complete LCM wrapper that stops "
        "shifting over time. This metric tracks three independent axes.",
        "",
        "Generated by `scripts/crystallization_metric.py`; do not hand-edit.",
        "",
    ]

    # ------------------------------------------------------------------
    # Top-line table
    # ------------------------------------------------------------------
    n = coverage["total_classes"]
    stab = coverage["stabilized"]
    churn_err = churn.get("git_error")
    churn_note = f" [WARN: {churn_err}]" if churn_err else ""

    reg = regression
    still = reg["still_stabilized"]
    ever = len(reg["stabilized_ever"])
    # Display the regression cell meaningfully; first run has no history to compare
    if ever == 0:
        reg_display = "n/a (first run)"
    else:
        reg_display = f"{still}/{ever} stabilized still pass"

    lines += [
        "## Top-line",
        "",
        "| Axis                    | Score                               | Notes |",
        "|-------------------------|-------------------------------------|-------|",
        f"| Coverage                | {stab}/{n} classes ({_pct(stab, n)}) | from tests/live_status.json |",
        f"| Stability (30d churn)   | {scored['churn_30d']} lines changed  | git log --since=30.days{churn_note} |",
        f"| Stability (90d churn)   | {scored['churn_90d']} lines changed  | git log --since=90.days{churn_note} |",
        f"| Regression              | {reg_display} | snapshot diff vs history |",
        f"| Crystallization score   | {scored['score']:.2f} / 1.00              | weighted combo (see below) |",
        "",
    ]

    # ------------------------------------------------------------------
    # Coverage axis
    # ------------------------------------------------------------------
    lines += [
        "## Coverage axis",
        "",
        f"{stab} of {n} classes fully stabilized (all phases PASS or SKIP, at least one PASS).",
        "",
    ]

    stabilized_rows = coverage["stabilized_rows"]
    if stabilized_rows:
        lines += [
            "| Class | Read | Add | Reorder | Modify | Delete |",
            "|-------|------|-----|---------|--------|--------|",
        ]
        for cls, glyphs in stabilized_rows:
            lines.append(f"| {cls} | {' | '.join(glyphs)} |")
    else:
        lines.append("_No classes stabilized yet._")
    lines.append("")

    all_rows = coverage["class_rows"]
    unstabilized = [(c, g) for c, g in all_rows if c not in coverage["stabilized_classes"]]
    if unstabilized:
        lines += [
            "<details><summary>Unstabilized classes ({} of {}) -- click to expand</summary>".format(
                len(unstabilized), n
            ),
            "",
            "| Class | Read | Add | Reorder | Modify | Delete |",
            "|-------|------|-----|---------|--------|--------|",
        ]
        for cls, glyphs in unstabilized:
            lines.append(f"| {cls} | {' | '.join(glyphs)} |")
        lines += ["", "</details>", ""]

    # ------------------------------------------------------------------
    # Stability axis
    # ------------------------------------------------------------------
    lines += [
        "## Stability axis (churn)",
        "",
        "Lines added + removed across `flexicon/code/` per Operations class "
        "over the last 90 days.  Classes that are stabilized AND have non-zero "
        "30-day churn are flagged as **[MOVING]** -- declared crystallized but "
        "still changing.",
        "",
    ]

    if churn_err:
        lines.append(f"[WARN] Git churn data unavailable: {churn_err}")
        lines.append("")
    else:
        # Build per-class churn table, show only classes with any 90d churn
        # plus all stabilized classes (so we never hide a red flag).
        stabilized_set = set(coverage["stabilized_classes"])
        per90 = churn["per_class_90d"]
        per30 = churn["per_class_30d"]
        last_touched = churn["per_class_last_touched"]

        active_classes = sorted(
            {c for c, v in per90.items() if v > 0} | stabilized_set
        )

        if active_classes:
            lines += [
                "| Class | Churn 30d | Churn 90d | Last touched | Flag |",
                "|-------|-----------|-----------|--------------|------|",
            ]
            for cls in active_classes:
                c30 = per30.get(cls, 0)
                c90 = per90.get(cls, 0)
                lt = last_touched.get(cls)
                lt_str = lt.isoformat() if lt else "n/a"
                if cls in stabilized_set and c30 > 0:
                    flag = "**[MOVING]**"
                elif cls in stabilized_set:
                    flag = "[STABLE]"
                else:
                    flag = ""
                lines.append(f"| {cls} | {c30} | {c90} | {lt_str} | {flag} |")
        else:
            lines.append("_No churn in the last 90 days._")
        lines.append("")

    # ------------------------------------------------------------------
    # Regression axis
    # ------------------------------------------------------------------
    lines += [
        "## Regression axis",
        "",
    ]

    if not regression["stabilized_ever"] and not regression["newly_stabilized"]:
        lines.append("_No prior history. This is the first run._")
        lines.append("")
    else:
        if regression["regressed"]:
            lines += [
                "**Classes that were stabilized in a prior run but are now FAIL or missing:**",
                "",
            ]
            for cls in regression["regressed"]:
                lines.append(f"- {cls}")
            lines.append("")
        else:
            lines.append("No regressions detected since prior run.")
            lines.append("")

        if regression["newly_stabilized"]:
            lines += [
                "**Newly stabilized this run (vs. previous run):**",
                "",
            ]
            for cls in regression["newly_stabilized"]:
                lines.append(f"- {cls}")
            lines.append("")

        lines += [
            f"Stabilized ever: {len(regression['stabilized_ever'])} classes  |  "
            f"Still passing: {regression['still_stabilized']}  |  "
            f"Regression factor: {regression['regression_factor']:.3f}",
            "",
        ]

    # ------------------------------------------------------------------
    # Crystallization score breakdown
    # ------------------------------------------------------------------
    lines += [
        "## Crystallization score",
        "",
        "```",
        f"score = {W_COVERAGE} * coverage_factor",
        f"      + {W_STABILITY} * stability_factor",
        f"      + {W_REGRESSION} * regression_factor",
        "",
        f"coverage_factor   = stabilized / {TOTAL_CLASSES_EXPECTED}",
        f"                  = {coverage['stabilized']} / {TOTAL_CLASSES_EXPECTED}",
        f"                  = {scored['coverage_factor']:.4f}",
        "",
        "stability_factor  = max(0, 1 - churn_30d / max(1, churn_90d / 3))",
        f"                  = max(0, 1 - {scored['churn_30d']} / max(1, {scored['churn_90d']} / 3))",
        f"                  = max(0, 1 - {scored['churn_30d']} / {scored['churn_90d_baseline_avg']})",
        f"                  = {scored['stability_factor']:.4f}",
        "",
        "regression_factor = still_stabilized / max(1, stabilized_ever)",
        f"                  = {regression['still_stabilized']} / {max(1, len(regression['stabilized_ever']))}",
        f"                  = {scored['regression_factor']:.4f}",
        "",
        f"score             = {W_COVERAGE} * {scored['coverage_factor']:.4f}",
        f"                  + {W_STABILITY} * {scored['stability_factor']:.4f}",
        f"                  + {W_REGRESSION} * {scored['regression_factor']:.4f}",
        f"                  = {scored['score']:.4f}",
        "```",
        "",
    ]

    # ------------------------------------------------------------------
    # How to regenerate
    # ------------------------------------------------------------------
    lines += [
        "## How to regenerate",
        "",
        "```",
        "python scripts/crystallization_metric.py",
        "```",
        "",
        "Inputs:",
        "- `flexicon/code/**/*Operations.py` -- Operations class inventory",
        "- `tests/live_status.json` -- per-test outcomes from the most recent live pytest run",
        "- `git log --numstat` -- rolling 90-day churn over flexicon/code/",
        "- `tests/crystallization_history.jsonl` -- prior run snapshots",
        "",
        "Outputs:",
        "- `tests/CRYSTALLIZATION.md` -- this file",
        "- `tests/crystallization_history.jsonl` -- one JSON line appended per run",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    root = repo_root()
    ts = _now_iso()

    # 1. Inventory
    classes = scan_operations_classes(root)

    # 2. Coverage axis
    status = load_live_status(root)
    outcomes = phase_outcomes(status)
    coverage = compute_coverage(classes, outcomes)

    # 3. Stability axis
    churn = compute_churn(root, classes)

    # 4. History (before regression, before appending)
    history = load_history(root)

    # 5. Regression axis
    regression = compute_regression(coverage, history)

    # 6. Score
    scored = compute_score(coverage, churn, regression)

    # 7. Write report
    report = render_report(ts, coverage, churn, regression, scored)
    target = root / "tests" / "CRYSTALLIZATION.md"
    target.write_text(report, encoding="utf-8")

    # 8. Append history
    append_history(root, coverage, churn, scored, ts)

    # 9. Summary
    if churn.get("git_error"):
        print(f"[WARN] Git churn unavailable: {churn['git_error']}")
    print(f"[OK] Wrote {target.relative_to(root).as_posix()}")
    print(f"     Operations classes : {len(classes)}")
    print(f"     Stabilized         : {coverage['stabilized']} / {TOTAL_CLASSES_EXPECTED}")
    print(f"     Churn 30d / 90d    : {churn['churn_30d']} / {churn['churn_90d']} lines")
    print(f"     Regression factor  : {scored['regression_factor']:.3f}")
    print(f"     Crystallization    : {scored['score']:.2f} / 1.00")


if __name__ == "__main__":
    main()
