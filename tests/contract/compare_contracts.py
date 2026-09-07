#
#   compare_contracts.py
#
#   Diff engine that compares the expected contract (what flexicon
#   needs) against a liblcm snapshot (what liblcm provides).
#   Produces a structured report of breakage, regressions, and changes.
#
#   Runs anywhere (no FieldWorks/pythonnet required).
#
#   Platform: Python 3.8+
#   Copyright 2025
#

"""
Compare flexicon's expected LCM contract against a liblcm snapshot.

This is the core of the contract test: it answers "which of my ~1400
functions will break with this version of liblcm?"

Usage::

    from tests.contract.compare_contracts import compare

    report = compare(expected_contract, liblcm_snapshot)
    print(report["summary"])

    # Or compare two snapshots (regression detection):
    report = compare_snapshots(old_snapshot, new_snapshot)
"""

import json
from pathlib import Path


def compare(expected_contract, liblcm_snapshot):
    """
    Compare expected contract against a liblcm snapshot.

    Args:
        expected_contract: Output of extract_lcm_contract.extract_contract().
        liblcm_snapshot: Output of generate_lcm_snapshot.generate_snapshot().

    Returns:
        dict with:
        - missing_types: Types flexicon needs but liblcm doesn't have
        - missing_members: Per-type members that are expected but absent
        - affected_files: Which flexicon files are impacted by each gap
        - summary: Counts and severity assessment
    """
    snapshot_types = liblcm_snapshot.get("types", {})
    expected_imports = expected_contract.get("imports", {})
    expected_usage = expected_contract.get("type_usage", {})
    file_contracts = expected_contract.get("files", {})

    # 1. Find missing types
    missing_types = []
    for type_name, info in snapshot_types.items():
        if not info.get("found", False):
            missing_types.append(
                {
                    "type": type_name,
                    "error": info.get("error", "Not found"),
                    "used_in_modules": _find_modules_using(type_name, expected_imports),
                }
            )

    # 2. Find missing members on types that DO exist
    missing_members = []
    for type_name, usage in expected_usage.items():
        if type_name not in snapshot_types:
            continue
        provided = snapshot_types[type_name]
        if not provided.get("found", False):
            continue

        provided_props = set(provided.get("properties", []))
        provided_methods = set(provided.get("methods", []))

        for prop in usage.get("properties", []):
            if prop not in provided_props and prop not in provided_methods:
                missing_members.append(
                    {
                        "type": type_name,
                        "member": prop,
                        "kind": "property",
                    }
                )

        for method in usage.get("methods", []):
            if method not in provided_methods and method not in provided_props:
                missing_members.append(
                    {
                        "type": type_name,
                        "member": method,
                        "kind": "method",
                    }
                )

    # 3. Map breakage back to source files
    affected_files = {}
    broken_type_names = {mt["type"] for mt in missing_types}
    broken_members_by_type = {}
    for mm in missing_members:
        broken_members_by_type.setdefault(mm["type"], []).append(mm["member"])

    for filepath, fcontract in file_contracts.items():
        file_issues = []

        # Check if file imports a missing type
        for mod, names in fcontract.get("imports", {}).items():
            for name in names:
                if name in broken_type_names:
                    file_issues.append(
                        {
                            "severity": "ERROR",
                            "issue": f"Imports missing type: {name}",
                        }
                    )

        # Check if file uses missing members
        for type_name, usage in fcontract.get("type_usage", {}).items():
            broken = broken_members_by_type.get(type_name, [])
            for prop in usage.get("properties", []):
                if prop in broken:
                    file_issues.append(
                        {
                            "severity": "ERROR",
                            "issue": f"Uses missing {type_name}.{prop}",
                        }
                    )
            for method in usage.get("methods", []):
                if method in broken:
                    file_issues.append(
                        {
                            "severity": "ERROR",
                            "issue": f"Calls missing {type_name}.{method}()",
                        }
                    )

        if file_issues:
            affected_files[filepath] = file_issues

    # 4. Summary
    total_expected = sum(len(names) for names in expected_imports.values())
    total_found = sum(1 for t in snapshot_types.values() if t.get("found", False))
    total_missing = len(missing_types)

    summary = {
        "total_types_expected": total_expected,
        "total_types_found": total_found,
        "total_types_missing": total_missing,
        "total_missing_members": len(missing_members),
        "total_affected_files": len(affected_files),
        "compatibility_score": (round(total_found / max(total_expected, 1) * 100, 1)),
        "verdict": ("PASS" if total_missing == 0 and len(missing_members) == 0 else "FAIL"),
    }

    return {
        "missing_types": missing_types,
        "missing_members": missing_members,
        "affected_files": affected_files,
        "summary": summary,
    }


def compare_snapshots(old_snapshot, new_snapshot):
    """
    Compare two liblcm snapshots to detect regressions.

    Args:
        old_snapshot: Previous liblcm snapshot (baseline).
        new_snapshot: New liblcm snapshot to check.

    Returns:
        dict with regressions (types/members that disappeared),
        additions (new types/members), and summary.
    """
    old_types = old_snapshot.get("types", {})
    new_types = new_snapshot.get("types", {})

    regressions = []
    additions = []

    all_type_names = set(old_types.keys()) | set(new_types.keys())

    for type_name in sorted(all_type_names):
        old_info = old_types.get(type_name, {"found": False})
        new_info = new_types.get(type_name, {"found": False})

        old_found = old_info.get("found", False)
        new_found = new_info.get("found", False)

        # Type disappeared
        if old_found and not new_found:
            regressions.append(
                {
                    "type": type_name,
                    "change": "type_removed",
                    "detail": f"Type {type_name} was present, now missing",
                }
            )
            continue

        # Type appeared
        if not old_found and new_found:
            additions.append(
                {
                    "type": type_name,
                    "change": "type_added",
                    "detail": f"Type {type_name} is now available",
                }
            )
            continue

        if not old_found and not new_found:
            continue

        # Both exist -- check members
        old_props = set(old_info.get("properties", []))
        new_props = set(new_info.get("properties", []))
        old_methods = set(old_info.get("methods", []))
        new_methods = set(new_info.get("methods", []))

        for prop in sorted(old_props - new_props):
            regressions.append(
                {
                    "type": type_name,
                    "change": "property_removed",
                    "detail": f"{type_name}.{prop} removed",
                }
            )
        for prop in sorted(new_props - old_props):
            additions.append(
                {
                    "type": type_name,
                    "change": "property_added",
                    "detail": f"{type_name}.{prop} added",
                }
            )
        for method in sorted(old_methods - new_methods):
            regressions.append(
                {
                    "type": type_name,
                    "change": "method_removed",
                    "detail": f"{type_name}.{method}() removed",
                }
            )
        for method in sorted(new_methods - old_methods):
            additions.append(
                {
                    "type": type_name,
                    "change": "method_added",
                    "detail": f"{type_name}.{method}() added",
                }
            )

    summary = {
        "old_version": old_snapshot.get("metadata", {}).get("liblcm_version", "unknown"),
        "new_version": new_snapshot.get("metadata", {}).get("liblcm_version", "unknown"),
        "total_regressions": len(regressions),
        "total_additions": len(additions),
        "verdict": "PASS" if len(regressions) == 0 else "FAIL",
    }

    return {
        "regressions": regressions,
        "additions": additions,
        "summary": summary,
    }


def _find_modules_using(type_name, imports):
    """Find which SIL modules export a given type name."""
    modules = []
    for mod, names in imports.items():
        if type_name in names:
            modules.append(mod)
    return modules


def format_report(report, verbose=False):
    """
    Format a comparison report as human-readable text.

    Args:
        report: Output of compare() or compare_snapshots().
        verbose: Include per-file details.

    Returns:
        str with the formatted report.
    """
    lines = []
    s = report.get("summary", {})

    # Header
    if "verdict" in s:
        verdict = s["verdict"]
        lines.append(f"LibLCM Contract Test: [{verdict}]")
        lines.append("=" * 50)

    # Summary
    if "compatibility_score" in s:
        lines.append(f"Compatibility: {s['compatibility_score']}%")
        lines.append(f"Types expected: {s['total_types_expected']}")
        lines.append(f"Types found:    {s['total_types_found']}")
        lines.append(f"Types missing:  {s['total_types_missing']}")
        lines.append(f"Missing members: {s['total_missing_members']}")
        lines.append(f"Affected files:  {s['total_affected_files']}")

    if "old_version" in s:
        lines.append(f"Old version: {s['old_version']}")
        lines.append(f"New version: {s['new_version']}")
        lines.append(f"Regressions: {s['total_regressions']}")
        lines.append(f"Additions:   {s['total_additions']}")

    # Missing types
    missing_types = report.get("missing_types", [])
    if missing_types:
        lines.append("")
        lines.append("MISSING TYPES:")
        for mt in missing_types:
            modules = ", ".join(mt.get("used_in_modules", []))
            lines.append(f"  [ERROR] {mt['type']} (from {modules})")

    # Missing members
    missing_members = report.get("missing_members", [])
    if missing_members:
        lines.append("")
        lines.append("MISSING MEMBERS:")
        for mm in missing_members:
            lines.append(f"  [ERROR] {mm['type']}.{mm['member']} ({mm['kind']})")

    # Regressions
    regressions = report.get("regressions", [])
    if regressions:
        lines.append("")
        lines.append("REGRESSIONS:")
        for r in regressions:
            lines.append(f"  [WARN] {r['detail']}")

    # Additions
    additions = report.get("additions", [])
    if additions and verbose:
        lines.append("")
        lines.append("ADDITIONS:")
        for a in additions:
            lines.append(f"  [INFO] {a['detail']}")

    # Affected files
    affected = report.get("affected_files", {})
    if affected and verbose:
        lines.append("")
        lines.append("AFFECTED FILES:")
        for filepath, issues in sorted(affected.items()):
            lines.append(f"  {filepath}:")
            for issue in issues:
                lines.append(f"    [{issue['severity']}] {issue['issue']}")

    return "\n".join(lines)


def main():
    """CLI: compare a contract against a snapshot, or two snapshots."""
    import argparse

    parser = argparse.ArgumentParser(description="Compare LCM contract vs snapshot, or two snapshots.")
    subparsers = parser.add_subparsers(dest="command")

    # compare contract vs snapshot
    check_parser = subparsers.add_parser("check", help="Compare expected contract against liblcm snapshot")
    check_parser.add_argument("--contract", "-c", required=True)
    check_parser.add_argument("--snapshot", "-s", required=True)
    check_parser.add_argument("--verbose", "-v", action="store_true")

    # compare two snapshots
    diff_parser = subparsers.add_parser("diff", help="Compare two liblcm snapshots for regressions")
    diff_parser.add_argument("--old", required=True)
    diff_parser.add_argument("--new", required=True)
    diff_parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.command == "check":
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        report = compare(contract, snapshot)
        print(format_report(report, verbose=args.verbose))
        sys.exit(0 if report["summary"]["verdict"] == "PASS" else 1)

    elif args.command == "diff":
        old = json.loads(Path(args.old).read_text(encoding="utf-8"))
        new = json.loads(Path(args.new).read_text(encoding="utf-8"))
        report = compare_snapshots(old, new)
        print(format_report(report, verbose=args.verbose))
        sys.exit(0 if report["summary"]["verdict"] == "PASS" else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    import sys

    main()
