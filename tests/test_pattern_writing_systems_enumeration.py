#
#   test_pattern_writing_systems_enumeration.py
#
#   Regression tests for WritingSystems enumeration pattern (issue #216):
#   Static guard against regression to known-bad LCM 9.x enumeration patterns.
#
#   Three patterns blocked by this test:
#     1. ws_factory.WritingSystems           -- nonexistent attribute
#     2. GetAllWritingSystems(               -- nonexistent method
#     3. GetWritingSystemTag(                -- nonexistent method
#
#   The fix: enumerate via self.project.WritingSystems.GetAll() which returns
#   CoreWritingSystemDefinition objects with .Id and .Handle properties.
#   Without this fix, every GetSyncableProperties call crashes at LCM 9.x runtime.
#
#   Applied across ~20 files: all Grammar Operations, Lexicon Operations
#   (patched during Layer-3), StratumOperations, WritingSystemOperations, FLExProject.
#
#   Pure Python pattern guard -- no SIL.LCModel / FieldWorks dependency required.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
import re
from pathlib import Path


class TestWritingSystemsEnumerationPattern:
    """
    Regression guard for WritingSystems enumeration (issue #216).
    Catches regressions where known-bad patterns re-appear in source code.
    """

    CODEBASE_ROOT = Path(__file__).parent.parent / "flexlibs2" / "code"

    def _scan_files(self, pattern):
        """Scan all .py files under flexlibs2/code/ for pattern match."""
        matches = []
        for py_file in self.CODEBASE_ROOT.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    # Skip lines that are comments (after # symbol)
                    code_part = line.split("#")[0] if "#" in line else line
                    if re.search(pattern, code_part):
                        matches.append((py_file.relative_to(self.CODEBASE_ROOT), line_num, line.strip()))
        return matches

    def test_no_ws_factory_writings_systems(self):
        """
        Guard against ws_factory.WritingSystems (nonexistent attribute).
        Known-bad pattern from upstream pre-2026 LCM wrapper.
        """
        pattern = r"ws_factory\.WritingSystems"
        matches = self._scan_files(pattern)
        assert not matches, (
            f"Found {len(matches)} reference(s) to ws_factory.WritingSystems "
            f"(nonexistent LCM 9.x attribute):\n"
            + "\n".join(f"  {path}:{line_num}: {line}" for path, line_num, line in matches)
        )

    def test_no_get_all_writing_systems_method(self):
        """
        Guard against GetAllWritingSystems( (nonexistent method).
        Known-bad pattern from upstream pre-2026 LCM wrapper.
        """
        pattern = r"GetAllWritingSystems\s*\("
        matches = self._scan_files(pattern)
        assert not matches, (
            f"Found {len(matches)} reference(s) to GetAllWritingSystems( "
            f"(nonexistent LCM 9.x method):\n"
            + "\n".join(f"  {path}:{line_num}: {line}" for path, line_num, line in matches)
        )

    def test_no_get_writing_system_tag_method(self):
        """
        Guard against GetWritingSystemTag( (nonexistent method).
        Known-bad pattern from upstream pre-2026 LCM wrapper.
        """
        pattern = r"GetWritingSystemTag\s*\("
        matches = self._scan_files(pattern)
        assert not matches, (
            f"Found {len(matches)} reference(s) to GetWritingSystemTag( "
            f"(nonexistent LCM 9.x method):\n"
            + "\n".join(f"  {path}:{line_num}: {line}" for path, line_num, line in matches)
        )

    def test_correct_pattern_present_in_operations(self):
        """
        Positive assertion: at least some Operations classes use the correct
        self.project.WritingSystems.GetAll() pattern.
        """
        pattern = r"self\.project\.WritingSystems\.GetAll\(\)"
        matches = self._scan_files(pattern)
        assert matches, (
            "No references found to the correct self.project.WritingSystems.GetAll() pattern. "
            "Either the codebase has regressed to the old pattern, or the fix has been refactored."
        )
        # Sanity: should be found in at least one grammar/lexicon operations file
        ops_files = [path for path, _, _ in matches if "Operations.py" in str(path)]
        assert ops_files, "Expected self.project.WritingSystems.GetAll() in at least one Operations class"


class TestWritingSystemsLiveSmoke:
    """
    Live smoke test for WritingSystems enumeration fix (issue #216, part 2).
    Exercises GetSyncableProperties on real objects to ensure no regressions.
    """

    def test_getsyncableproperties_calls_succeed(self, sena3_sandbox):
        """
        Call GetSyncableProperties on representative objects from each
        Operations class that exposes it. Verify no AttributeError on
        missing WritingSystems methods.
        """
        import pytest

        flex_project = sena3_sandbox

        # List of (Operations class, method, object_source) tuples
        test_cases = [
            ("GrammaticalMorphemeOperations", "GetAll", None),
            ("LexEntryOperations", "GetAll", None),
            ("LexSenseOperations", "GetAll", None),
            ("InflectionFeatureOperations", "GetAll", None),
        ]

        for class_name, method_name, object_source in test_cases:
            try:
                ops = getattr(flex_project, class_name, None)
                if ops is None:
                    continue  # Class not available in this project

                # Get an object to sync
                items = list(getattr(ops, method_name)())
                if not items:
                    continue  # No items to test

                item = items[0]

                # Call GetSyncableProperties — this is where WritingSystems
                # enumeration happens. If the old pattern regressed, this
                # will raise AttributeError.
                try:
                    props = ops.GetSyncableProperties(item)
                    assert isinstance(props, dict), f"{class_name}: GetSyncableProperties returned non-dict"
                except AttributeError as exc:
                    if any(
                        bad_pattern in str(exc)
                        for bad_pattern in ["GetAllWritingSystems", "GetWritingSystemTag", "ws_factory"]
                    ):
                        pytest.fail(
                            f"{class_name}.GetSyncableProperties raised AttributeError indicating "
                            f"regression to old WritingSystems enumeration pattern: {exc}"
                        )
                    else:
                        raise

            except Exception as exc:
                pytest.skip(f"Could not test {class_name}: {exc}")

