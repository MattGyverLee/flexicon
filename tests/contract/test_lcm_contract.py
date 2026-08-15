#
#   test_lcm_contract.py
#
#   Pytest-based contract tests for flexicon <-> liblcm compatibility.
#
#   These tests operate in two modes:
#
#   Mode 1 (runs anywhere, no deps):
#     - Extracts the expected contract from source via AST
#     - Validates contract structure and consistency
#     - Compares against a checked-in baseline snapshot
#     - Detects when flexicon code changes introduce new LCM deps
#
#   Mode 2 (requires FieldWorks + pythonnet):
#     - Introspects installed liblcm assemblies
#     - Verifies every expected type/member actually exists
#     - Generates a new snapshot for regression tracking
#
#   Platform: Python 3.8+
#   Copyright 2025
#

"""
LibLCM contract tests.

Run with::

    # Mode 1: static analysis only (runs anywhere)
    pytest tests/contract/test_lcm_contract.py -m "not requires_liblcm"

    # Mode 2: full verification (requires FieldWorks)
    pytest tests/contract/test_lcm_contract.py

    # Verbose output with affected file details
    pytest tests/contract/test_lcm_contract.py -v -s
"""

import json
import os
import pytest
from pathlib import Path

from tests.contract.extract_lcm_contract import extract_contract

# Paths
CONTRACT_DIR = Path(__file__).parent
SNAPSHOTS_DIR = CONTRACT_DIR / "snapshots"
BASELINE_CONTRACT_PATH = SNAPSHOTS_DIR / "expected_contract.json"
BASELINE_SNAPSHOT_PATH = SNAPSHOTS_DIR / "liblcm_baseline.json"


# --- Markers ---


def _add_fieldworks_path():
    """
    Add the FieldWorks install directory to sys.path so clr.AddReference
    can find SIL.LCModel. Mirrors the bootstrap in tests/conftest.py, which
    runs as an autouse session fixture -- too late for the module-level
    skipif marker below, which is evaluated at collection time.

    Best-effort: silently no-op if the registry/key isn't readable or if
    pythonnet/CLR isn't on the box.
    """
    import sys as _sys

    try:
        import clr  # noqa: F401  # ensure pythonnet is loaded first
        from Microsoft.Win32 import Registry
    except Exception:
        return

    for hive in (Registry.LocalMachine, Registry.CurrentUser):
        try:
            key = hive.OpenSubKey(r"SOFTWARE\SIL\FieldWorks\9")
            if key is None:
                continue
            code_dir = key.GetValue("RootCodeDir")
            if code_dir and code_dir not in _sys.path:
                _sys.path.append(code_dir)
                return
        except Exception:
            continue


def _has_liblcm():
    """Check if liblcm is available via pythonnet."""
    try:
        import clr

        _add_fieldworks_path()
        clr.AddReference("SIL.LCModel")
        return True
    except Exception:
        return False


requires_liblcm = pytest.mark.skipif(
    not _has_liblcm(),
    reason="Requires FieldWorks/liblcm (pythonnet + SIL.LCModel)",
)


# --- Fixtures ---


@pytest.fixture(scope="session")
def expected_contract():
    """Extract the expected LCM contract from flexicon source."""
    return extract_contract()


@pytest.fixture(scope="session")
def baseline_contract():
    """Load the checked-in baseline contract, if it exists."""
    if not BASELINE_CONTRACT_PATH.exists():
        pytest.skip(
            "No baseline contract snapshot found. Run: "
            "python -m tests.contract.extract_lcm_contract "
            f"-o {BASELINE_CONTRACT_PATH}"
        )
    return json.loads(BASELINE_CONTRACT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def baseline_snapshot():
    """Load the checked-in liblcm baseline snapshot, if it exists."""
    if not BASELINE_SNAPSHOT_PATH.exists():
        pytest.skip("No liblcm baseline snapshot found. Generate one on a " "machine with FieldWorks installed.")
    return json.loads(BASELINE_SNAPSHOT_PATH.read_text(encoding="utf-8"))


# ============================================================
# MODE 1: Static analysis tests (run anywhere)
# ============================================================


class TestContractExtraction:
    """Verify that the contract extractor works and produces valid output."""

    def test_contract_has_imports(self, expected_contract):
        """Contract should find SIL.LCModel imports."""
        imports = expected_contract["imports"]
        assert len(imports) > 0, "No SIL imports found"
        assert "SIL.LCModel" in imports, "SIL.LCModel not in imports"

    def test_contract_has_files(self, expected_contract):
        """Contract should cover multiple source files."""
        files = expected_contract["files"]
        assert len(files) > 30, f"Expected 30+ files with LCM deps, found {len(files)}"

    def test_contract_has_factories(self, expected_contract):
        """Contract should identify factory types."""
        factories = expected_contract["factories"]
        assert len(factories) > 10, f"Expected 10+ factories, found {len(factories)}"

    def test_contract_has_repositories(self, expected_contract):
        """Contract should identify repository types."""
        repos = expected_contract["repositories"]
        assert len(repos) > 5, f"Expected 5+ repositories, found {len(repos)}"

    def test_contract_has_interfaces(self, expected_contract):
        """Contract should identify interface types (I-prefixed)."""
        interfaces = expected_contract["interfaces"]
        assert len(interfaces) > 20, f"Expected 20+ interfaces, found {len(interfaces)}"

    def test_critical_types_present(self, expected_contract):
        """
        The most critical LCM types must appear in the contract.
        If these are missing, the extractor is broken.
        """
        all_names = set()
        for names in expected_contract["imports"].values():
            all_names.update(names)

        critical = [
            "ITsString",
            "TsStringUtils",
            "ILexEntry",
            "ILexSense",
            "IPartOfSpeech",
        ]
        for name in critical:
            assert name in all_names, f"Critical type {name} not found in contract"

    def test_summary_is_consistent(self, expected_contract):
        """Summary counts should match actual data."""
        s = expected_contract["summary"]
        assert s["total_files_with_lcm_deps"] == len(expected_contract["files"])
        assert s["total_factories"] == len(expected_contract["factories"])
        assert s["total_repositories"] == len(expected_contract["repositories"])


class TestContractStability:
    """
    Compare current contract against the checked-in baseline.
    Detects when code changes introduce new LCM dependencies.
    """

    def test_no_new_type_dependencies(self, expected_contract, baseline_contract):
        """
        New LCM type imports should be deliberate.
        Fails if flexicon code now imports types not in the baseline.
        """
        current_names = set()
        for names in expected_contract["imports"].values():
            current_names.update(names)

        baseline_names = set()
        for names in baseline_contract["imports"].values():
            baseline_names.update(names)

        new_deps = current_names - baseline_names
        if new_deps:
            pytest.fail(
                f"New LCM type dependencies detected (update baseline if intentional):\n"
                + "\n".join(f"  + {n}" for n in sorted(new_deps))
            )

    def test_no_removed_type_dependencies(self, expected_contract, baseline_contract):
        """
        Detect when LCM imports are removed (might indicate refactoring).
        This is informational -- removal is usually fine.
        """
        current_names = set()
        for names in expected_contract["imports"].values():
            current_names.update(names)

        baseline_names = set()
        for names in baseline_contract["imports"].values():
            baseline_names.update(names)

        removed = baseline_names - current_names
        if removed:
            # This is a warning, not a failure
            import warnings

            warnings.warn(
                f"LCM type dependencies removed (update baseline):\n" + "\n".join(f"  - {n}" for n in sorted(removed))
            )

    def test_file_count_not_dramatically_changed(self, expected_contract, baseline_contract):
        """
        Sanity check: file count shouldn't change by more than 20%
        without updating the baseline.
        """
        current = expected_contract["summary"]["total_files_with_lcm_deps"]
        baseline = baseline_contract["summary"]["total_files_with_lcm_deps"]
        diff_pct = abs(current - baseline) / max(baseline, 1) * 100

        assert diff_pct < 20, (
            f"File count changed by {diff_pct:.0f}% "
            f"(baseline={baseline}, current={current}). "
            "Update baseline if this is expected."
        )


# ============================================================
# MODE 2: Live liblcm verification (requires deps)
# ============================================================


@requires_liblcm
class TestLiveContractVerification:
    """
    Verify the expected contract against the installed liblcm.
    Only runs when FieldWorks/pythonnet is available.
    """

    @pytest.fixture(scope="class")
    def liblcm_snapshot(self, expected_contract):
        """Generate a live snapshot from installed liblcm."""
        from tests.contract.generate_lcm_snapshot import generate_snapshot

        return generate_snapshot(expected_contract)

    def test_all_types_found(self, liblcm_snapshot):
        """Every type flexicon imports should exist in liblcm."""
        missing = liblcm_snapshot.get("missing_types", [])
        if missing:
            lines = [f"  - {t}" for t in missing]
            pytest.fail(f"{len(missing)} types not found in liblcm:\n" + "\n".join(lines))

    def test_no_missing_members(self, expected_contract, liblcm_snapshot):
        """
        Every property/method flexicon uses should exist on the type.
        """
        from tests.contract.compare_contracts import compare

        report = compare(expected_contract, liblcm_snapshot)

        missing = report["missing_members"]
        if missing:
            lines = [f"  - {mm['type']}.{mm['member']} ({mm['kind']})" for mm in missing]
            pytest.fail(f"{len(missing)} missing members:\n" + "\n".join(lines))

    def test_compatibility_score(self, expected_contract, liblcm_snapshot):
        """Compatibility score should be 100%."""
        from tests.contract.compare_contracts import compare

        report = compare(expected_contract, liblcm_snapshot)
        score = report["summary"]["compatibility_score"]
        assert score == 100.0, f"Compatibility score: {score}% (expected 100%)"

    def test_save_snapshot_for_regression(self, liblcm_snapshot, tmp_path):
        """
        Save the live snapshot so it can be committed as a new baseline.
        """
        from tests.contract.generate_lcm_snapshot import save_snapshot

        version = liblcm_snapshot["metadata"]["liblcm_version"]
        output = SNAPSHOTS_DIR / f"liblcm_{version}.json"

        # Only save if snapshots dir exists
        if SNAPSHOTS_DIR.exists():
            save_snapshot(liblcm_snapshot, output)


@requires_liblcm
class TestLiveRegressionCheck:
    """
    Compare live liblcm against the baseline snapshot.
    Detects when a liblcm upgrade removes types/members.
    """

    @pytest.fixture(scope="class")
    def liblcm_snapshot(self, expected_contract):
        from tests.contract.generate_lcm_snapshot import generate_snapshot

        return generate_snapshot(expected_contract)

    def test_no_regressions_from_baseline(self, liblcm_snapshot, baseline_snapshot):
        """
        No types or members should disappear compared to baseline.
        """
        from tests.contract.compare_contracts import compare_snapshots

        report = compare_snapshots(baseline_snapshot, liblcm_snapshot)

        regressions = report["regressions"]
        if regressions:
            lines = [f"  - {r['detail']}" for r in regressions]
            pytest.fail(f"{len(regressions)} regressions from baseline:\n" + "\n".join(lines))


# ============================================================
# Transaction-layer shape checks (write-path-transactions CB task)
# ============================================================
#
# Issues #233, #235, #236 were all API-*shape* errors that a plain
# "does this member name exist" check cannot catch:
#   #233 BeginUndoTask(str) called against a 2-arg API
#   #235 LcmCache.UndoStack referenced -- a member that never existed
#   #236 RollbackToMark() called -- an API that exists nowhere in liblcm
#
# These tests read the checked-in baseline_snapshot fixture directly (no
# live liblcm required -- Mode 1), asserting on the deep-reflection fields
# (constructors/method_signatures/interfaces/reflected_properties) that
# generate_lcm_snapshot.py's _introspect_signatures() adds on top of the
# plain member-name lists. A missing-member assertion (RollbackToMark must
# NOT exist) is exercised alongside the present-member assertions, since
# #235/#236 were both non-existent members flexicon code assumed existed.


class TestTransactionLayerContract:
    """Shape assertions for the four transaction-layer LCM types."""

    def test_action_handler_begin_undo_task_is_two_string_args(self, baseline_snapshot):
        """
        Issue #233: BeginUndoTask was called with 1 arg. liblcm's actual
        signature takes exactly 2 string parameters (undo text, redo text).
        """
        info = baseline_snapshot["types"]["IActionHandler"]
        sigs = info["method_signatures"].get("BeginUndoTask")
        assert sigs is not None, "IActionHandler.BeginUndoTask not found at all"
        assert sigs == [["String", "String"]], (
            f"BeginUndoTask signature changed: expected exactly one 2-string-arg "
            f"overload, got {sigs}"
        )

    def test_action_handler_exposes_expected_undo_redo_surface(self, baseline_snapshot):
        """
        The nesting/undo/redo/mark surface that transaction.py's rewrite (B1)
        and AbortSession (A3) are specified to build on.
        """
        info = baseline_snapshot["types"]["IActionHandler"]
        properties = set(info["properties"])
        methods = set(info["methods"])

        assert "CurrentDepth" in properties, "IActionHandler.CurrentDepth missing"
        for method in (
            "CanUndo", "CanRedo", "Undo", "Redo", "Rollback",
            "Mark", "DiscardToMark", "CollapseToMark",
        ):
            assert method in methods, f"IActionHandler.{method} missing"

        # Rollback(Int32) specifically -- not a parameterless overload.
        rollback_sigs = info["method_signatures"].get("Rollback")
        assert rollback_sigs is not None, "IActionHandler.Rollback not found"
        assert ["Int32"] in rollback_sigs, (
            f"IActionHandler.Rollback(Int32) overload not found, got {rollback_sigs}"
        )

    def test_action_handler_does_not_expose_rollback_to_mark(self, baseline_snapshot):
        """
        Issue #236: RollbackToMark() was called as if it existed. It does
        not, anywhere in liblcm. This is the missing-member half of the
        contract: a positive assertion that this name is ABSENT.
        """
        info = baseline_snapshot["types"]["IActionHandler"]
        assert "RollbackToMark" not in info["methods"]
        assert "RollbackToMark" not in info["method_signatures"]

    def test_undoable_unit_of_work_helper_shape(self, baseline_snapshot):
        """
        UndoableUnitOfWorkHelper: 3-arg ctor (IActionHandler, String, String),
        a RollBack property (write-only -- see O1 in tasks.md, hence checked
        via reflected_properties rather than the dir()-based properties
        list), and IDisposable.
        """
        info = baseline_snapshot["types"]["UndoableUnitOfWorkHelper"]
        assert info["found"], "UndoableUnitOfWorkHelper not found in liblcm"

        ctors = info["constructors"]
        assert ["IActionHandler", "String", "String"] in ctors, (
            f"3-arg (IActionHandler, String, String) constructor not found, got {ctors}"
        )

        assert "RollBack" in info["reflected_properties"], "RollBack property missing"
        assert info["reflected_properties"]["RollBack"]["can_write"] is True

        assert info["implements_idisposable"] is True, (
            "UndoableUnitOfWorkHelper no longer implements IDisposable"
        )

    def test_non_undoable_unit_of_work_helper_is_disposable(self, baseline_snapshot):
        """Sibling helper for undoable=False; same disposal contract."""
        info = baseline_snapshot["types"]["NonUndoableUnitOfWorkHelper"]
        assert info["found"], "NonUndoableUnitOfWorkHelper not found in liblcm"
        assert info["implements_idisposable"] is True

    def test_ilcm_ui_full_surface(self, baseline_snapshot):
        """
        HeadlessLcmUI (A1b) and FwLcmUI both implement ILcmUI. Lock its full
        surface: 10 methods + LastActivityTime + SynchronizeInvoke.
        """
        info = baseline_snapshot["types"]["ILcmUI"]
        assert info["found"], "ILcmUI not found in liblcm"

        properties = set(info["properties"])
        methods = set(info["methods"])

        assert {"LastActivityTime", "SynchronizeInvoke"} <= properties

        expected_methods = {
            "ConflictingSave", "ChooseFilesToUse", "RestoreLinkedFilesInProjectFolder",
            "CannotRestoreLinkedFilesToOriginalLocation", "DisplayMessage", "ReportException",
            "ReportDuplicateGuids", "DisplayCircularRefBreakerReport", "Retry", "OfferToRestore",
        }
        assert len(expected_methods) == 10
        assert expected_methods <= methods, (
            f"ILcmUI methods missing: {expected_methods - methods}"
        )


# ============================================================
# Utility: per-file impact tests
# ============================================================


class TestPerFileImpact:
    """
    When a baseline snapshot exists, verify which specific files
    would break with the current liblcm.
    """

    def test_report_affected_files(self, expected_contract, baseline_snapshot):
        """
        Generate and print the full impact report.
        This test always passes but prints the report for visibility.
        """
        from tests.contract.compare_contracts import compare, format_report

        report = compare(expected_contract, baseline_snapshot)
        text = format_report(report, verbose=True)
        print("\n" + text)

        # Store report as test artifact
        report_path = SNAPSHOTS_DIR / "latest_report.json"
        if SNAPSHOTS_DIR.exists():
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
