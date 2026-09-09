#
#   live_coverage_metric.py
#
#   Module: Compute live-DB test coverage across flexicon Operations classes.
#           Reads production code, live test files (live_phase markers), and
#           tests/live_status.json (per-test runtime outcomes); writes
#           tests/LIVE_COVERAGE.md.
#
#   Usage:  python scripts/live_coverage_metric.py
#
#   Platform: Python 3 (stdlib only)
#
#   Copyright 2026
#

import datetime
import json
import re
from collections import defaultdict
from pathlib import Path


PHASES = ("read", "add", "reorder", "modify", "delete")
STATUS_GLYPH = {"pass": "[PASS]", "fail": "[FAIL]", "skip": "[SKIP]"}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def scan_operations_classes(root: Path) -> dict:
    """
    Scan flexicon/code for *Operations.py files (excluding BaseOperations).

    Raises FileNotFoundError if code_dir is missing, or exists but yields no
    *Operations.py files. Path.rglob() on a missing/wrong directory returns
    no matches WITHOUT raising, which previously let this script (and
    crystallization_metric.py) silently report zero Operations classes for
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


def scan_live_test_markers(root: Path) -> dict:
    coverage = defaultdict(lambda: defaultdict(list))
    tests_dir = root / "tests" / "operations"
    for path in tests_dir.glob("test_*_live.py"):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(
            r'@pytest\.mark\.live_phase\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)',
            text,
        ):
            class_name, phase = m.group(1), m.group(2)
            coverage[class_name][phase].append(path.name)
    return coverage


def scan_methods_called_in_tests(root: Path) -> dict:
    called = defaultdict(set)
    tests_dir = root / "tests" / "operations"
    for path in tests_dir.glob("test_*_live.py"):
        text = path.read_text(encoding="utf-8")
        for name in re.findall(r"\.([A-Z][A-Za-z_0-9]*)\s*\(", text):
            called[path.name].add(name)
    return called


def load_live_status(root: Path):
    p = root / "tests" / "live_status.json"
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def phase_outcomes(status) -> dict:
    if not status:
        return {}
    out = {}
    for info in status.get("by_test", {}).values():
        cls, ph, st = info.get("operations_class"), info.get("phase"), info.get("status")
        if not (cls and ph and st):
            continue
        prev = out.get((cls, ph))
        if prev is None:
            out[(cls, ph)] = st
        elif st == "fail":
            out[(cls, ph)] = "fail"
        elif prev == "pass" and st == "skip":
            pass
        elif prev == "skip" and st == "pass":
            out[(cls, ph)] = "pass"
    return out


def render(classes: dict, tests: dict, methods_called: dict, outcomes: dict) -> str:
    n_total = len(classes)
    tested = sorted(c for c in classes if c in tests)
    untested = sorted(c for c in classes if c not in tests)

    def class_row(cls: str) -> tuple:
        glyphs = []
        for ph in PHASES:
            st = outcomes.get((cls, ph))
            if st is None:
                glyphs.append("[----]")
            else:
                glyphs.append(STATUS_GLYPH.get(st, "[????]"))
        return cls, glyphs

    rows = [class_row(c) for c in tested]

    def is_stabilized(glyphs):
        return all(g in ("[PASS]", "[SKIP]") for g in glyphs) and "[PASS]" in glyphs

    def is_partial(glyphs):
        return "[FAIL]" in glyphs or ("[PASS]" in glyphs and "[----]" in glyphs)

    stabilized = [(c, g) for c, g in rows if is_stabilized(g)]
    partial = [(c, g) for c, g in rows if is_partial(g)]

    total_phase_slots = n_total * len(PHASES)
    pass_phases = sum(1 for g_set in rows for g in g_set[1] if g == "[PASS]")
    fail_phases = sum(1 for g_set in rows for g in g_set[1] if g == "[FAIL]")
    skip_phases = sum(1 for g_set in rows for g in g_set[1] if g == "[SKIP]")
    covered_phases = pass_phases + fail_phases + skip_phases

    def method_stats(cls: str) -> tuple:
        n_methods = len(classes[cls]["methods"])
        files = set()
        for fs in tests.get(cls, {}).values():
            files.update(fs)
        called = set()
        for f in files:
            called |= methods_called.get(f, set())
        exercised = classes[cls]["methods"] & called
        return n_methods, len(exercised), exercised

    total_methods = sum(len(classes[c]["methods"]) for c in classes)
    total_exercised = sum(method_stats(c)[1] for c in tested)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pct = lambda n, d: f"{(n / d * 100):.1f}%" if d else "n/a"

    lines = []
    lines.append("# Live-DB Test Coverage Metric")
    lines.append("")
    lines.append(f"Last computed: {now}")
    lines.append("")
    lines.append("Snapshot of how much of the flexicon Operations surface has been exercised against a real FieldWorks project (Sena 3). Generated by `scripts/live_coverage_metric.py`; do not hand-edit.")
    lines.append("")

    lines.append("## Top-line")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Operations classes (total) | {n_total} |")
    lines.append(f"| Classes with any live test | {len(tested)} ({pct(len(tested), n_total)}) |")
    lines.append(f"| Classes fully stabilized (all phases PASS or SKIP, >=1 PASS) | {len(stabilized)} ({pct(len(stabilized), n_total)}) |")
    lines.append(f"| Classes with partial coverage (any FAIL) | {len(partial)} ({pct(len(partial), n_total)}) |")
    lines.append(f"| Phase slots PASS | {pass_phases} / {total_phase_slots} ({pct(pass_phases, total_phase_slots)}) |")
    lines.append(f"| Phase slots FAIL | {fail_phases} / {total_phase_slots} ({pct(fail_phases, total_phase_slots)}) |")
    lines.append(f"| Phase slots SKIP (N/A or no fixture) | {skip_phases} / {total_phase_slots} ({pct(skip_phases, total_phase_slots)}) |")
    lines.append(f"| Phase slots covered (any outcome) | {covered_phases} / {total_phase_slots} ({pct(covered_phases, total_phase_slots)}) |")
    lines.append(f"| @OperationsMethod methods (total) | {total_methods} |")
    lines.append(f"| Methods exercised by a live test | {total_exercised} ({pct(total_exercised, total_methods)}) |")
    lines.append("")

    lines.append("## Stabilized classes")
    lines.append("")
    lines.append("Every phase is PASS or SKIP, with at least one PASS. Treat these as crystallized: do not change behavior without a regression test.")
    lines.append("")
    if stabilized:
        lines.append("| Class | Read | Add | Reorder | Modify | Delete |")
        lines.append("|-------|------|-----|---------|--------|--------|")
        for cls, glyphs in stabilized:
            lines.append(f"| {cls} | {' | '.join(glyphs)} |")
    else:
        lines.append("_None yet._")
    lines.append("")

    lines.append("## Partial coverage (action items)")
    lines.append("")
    lines.append("These classes have a template but at least one phase fails. The failures usually correspond to a filed GitHub issue.")
    lines.append("")
    if partial:
        lines.append("| Class | Read | Add | Reorder | Modify | Delete | Methods exercised |")
        lines.append("|-------|------|-----|---------|--------|--------|-------------------|")
        for cls, glyphs in partial:
            total_m, n_exer, _ = method_stats(cls)
            lines.append(f"| {cls} | {' | '.join(glyphs)} | {n_exer}/{total_m} |")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## No live coverage")
    lines.append("")
    lines.append(f"{len(untested)} classes have no `test_*_live.py` file yet.")
    lines.append("")
    if untested:
        lines.append("<details><summary>Click to expand</summary>")
        lines.append("")
        for cls in untested:
            n_methods = len(classes[cls]["methods"])
            lines.append(f"- `{cls}` ({n_methods} @OperationsMethod methods)")
        lines.append("")
        lines.append("</details>")
    lines.append("")

    lines.append("## Method-level coverage (tested classes only)")
    lines.append("")
    lines.append("Methods are counted as \"exercised\" if their name appears in a live-test file for that class. This is an approximation: it does not verify the call actually ran or passed, only that the test calls that method by name.")
    lines.append("")
    lines.append("| Class | Methods | Exercised | % |")
    lines.append("|-------|---------|-----------|---|")
    for cls in tested:
        total_m, n_exer, _ = method_stats(cls)
        lines.append(f"| {cls} | {total_m} | {n_exer} | {pct(n_exer, total_m)} |")
    lines.append("")

    lines.append("## How to regenerate")
    lines.append("")
    lines.append("```")
    lines.append("python scripts/live_coverage_metric.py")
    lines.append("```")
    lines.append("")
    lines.append("Inputs:")
    lines.append("- `flexicon/code/**/*Operations.py` -- Operations class inventory")
    lines.append("- `tests/operations/test_*_live.py` -- live test files (live_phase markers)")
    lines.append("- `tests/live_status.json` -- per-test outcomes from the most recent live pytest run")
    lines.append("")
    lines.append("Output: this file (`tests/LIVE_COVERAGE.md`).")
    lines.append("")

    return "\n".join(lines)


def main():
    root = repo_root()
    classes = scan_operations_classes(root)
    tests = scan_live_test_markers(root)
    methods_called = scan_methods_called_in_tests(root)
    status = load_live_status(root)
    outcomes = phase_outcomes(status)

    out = render(classes, tests, methods_called, outcomes)
    target = root / "tests" / "LIVE_COVERAGE.md"
    target.write_text(out, encoding="utf-8")
    print(f"[OK] Wrote {target.relative_to(root).as_posix()}")
    print(f"     Operations classes: {len(classes)}")
    print(f"     Classes with live test: {sum(1 for c in classes if c in tests)}")
    print(f"     Phases passed: {sum(1 for v in outcomes.values() if v == 'pass')}")
    print(f"     Phases failed: {sum(1 for v in outcomes.values() if v == 'fail')}")
    print(f"     Phases skipped: {sum(1 for v in outcomes.values() if v == 'skip')}")


if __name__ == "__main__":
    main()
