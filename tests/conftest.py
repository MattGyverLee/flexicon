#
# conftest.py
#
# Pytest configuration and fixtures for FlexLibs2 validation test suite
#
# Provides:
# - Mock FLExProject fixture with write-enabled flags
# - Mock operations class instances
# - Assertion helpers for validation errors
# - Sample data generators
# - Test categorization markers
#
# Platform: Python.NET
#           FieldWorks Version 9+
#
# Copyright 2025
#

import faulthandler
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
import importlib

# Add the package root to sys.path so flexlibs2 can be imported
# This must be done BEFORE test collection
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# Pytest hook to ensure sys.path is set up early
def pytest_configure(config):
    """Configure pytest and set up sys.path before test collection."""
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)


# Mock-only test files that stub sys.modules["SIL"] = MagicMock() at module
# scope. That stub poisons the real CLR namespace pythonnet would otherwise
# populate, so importing flexlibs2 anywhere later in the same process fails
# with "'SIL' is not a package". These tests never exercise real library
# behavior (they just test mock orchestration), so skip collection and let
# the live-DB suite carry the actual coverage. Replace with live tests if
# the wrapper logic needs verification.
collect_ignore = [
    "test_affix_template_wrappers.py",
    "test_annotation_wrappers.py",
    "test_prohibition_wrappers.py",
]


# ========== SESSION-SCOPED FIXTURE FOR FIELDWORKS INITIALIZATION ==========
# Using autouse=True ensures this runs before any tests, regardless of scope

# Records whether this session actually reached a live LCM, or silently
# degraded to mocks. Written into tests/live_status.json as "run_mode" so
# a verification claim can be checked mechanically rather than trusted.
_LCM_MODE = "unknown"


@pytest.fixture(scope="session", autouse=True)
def initialize_flex_for_tests():
    """
    Initialize FieldWorks and flexlibs2 before running any tests.

    This fixture runs once per test session and ensures:
    1. FieldWorks DLLs are in sys.path
    2. FLEx services are initialized
    3. flexlibs2 package is fully imported with all operations
    4. Operations classes are available for tests

    Using autouse=True ensures this runs even if no test explicitly uses it.
    Using scope="session" ensures it runs only once for the entire test session.

    Falls back to mock mode if FLEx initialization fails (e.g., in CI/test environments).
    """
    global _LCM_MODE

    print("[INFO] [SESSION FIXTURE] Initializing FieldWorks for tests...")
    print("[INFO] Attempting full FLEx initialization (may fail in non-GUI environments)...")
    try:
        # Step 1: Set up Windows registry access and FW paths
        import clr
        from System import Environment
        from Microsoft.Win32 import Registry

        # Get FieldWorks installation path from registry
        RegKey = r"SOFTWARE\SIL\FieldWorks\9"
        try:
            rKey = Registry.LocalMachine.OpenSubKey(RegKey)
            if rKey is None:
                rKey = Registry.CurrentUser.OpenSubKey(RegKey)

            if rKey:
                fw_code_dir = rKey.GetValue("RootCodeDir")
                if fw_code_dir and os.path.exists(os.path.join(fw_code_dir, "FieldWorks.exe")):
                    sys.path.append(fw_code_dir)
                    print(f"[OK] FieldWorks path added: {fw_code_dir}")
        except Exception as e:
            print(f"[WARN] Could not read registry: {e}")

        # Step 2: Load SIL assemblies
        print("[INFO] Loading SIL assemblies...")
        clr.AddReference("FwUtils")
        clr.AddReference("SIL.WritingSystems")
        clr.AddReference("SIL.LCModel")
        print("[OK] SIL assemblies loaded")

        # Step 3: Initialize FLEx services
        print("[INFO] Initializing FLEx services...")
        from SIL.FieldWorks.Common.FwUtils import FwRegistryHelper, FwUtils
        from SIL.WritingSystems import Sldr

        FwRegistryHelper.Initialize()
        # FwUtils.InitializeIcu() triggers a benign Win32 SEH during
        # the native ICU bootstrap. Pytest enables faulthandler by
        # default, which intercepts the SEH and prints a noisy
        # "Windows fatal exception: access violation" stack to stderr
        # before the call completes successfully. Temporarily disable
        # faulthandler across the InitializeIcu call so the trace
        # doesn't pollute test output. Re-enable immediately after.
        # Tests are unaffected -- they ran fine before this change;
        # the trace was cosmetic. (issue #35)
        _faulthandler_was_enabled = faulthandler.is_enabled()
        try:
            if _faulthandler_was_enabled:
                faulthandler.disable()
            FwUtils.InitializeIcu()
        finally:
            if _faulthandler_was_enabled:
                faulthandler.enable()
        Sldr.Initialize(True)
        print("[OK] FLEx services initialized")

        # Step 4: Initialize FLEx using FLExInitialize()
        print("[INFO] Running FLExInitialize()...")
        from flexlibs2.code.FLExInit import FLExInitialize

        FLExInitialize()
        print("[OK] FLExInitialize() complete")

        # Step 5: Import flexlibs2 package
        print("[INFO] Importing flexlibs2 package...")
        import flexlibs2

        print("[OK] flexlibs2 imported successfully")

        # Step 6: Manually import and add operations to flexlibs2 namespace
        # The __init__.py imports may not execute fully, so do it explicitly here
        print("[INFO] Loading operations modules...")
        operations_modules = [
            # Grammar
            ("flexlibs2.code.Grammar.POSOperations", "POSOperations"),
            ("flexlibs2.code.Grammar.PhonemeOperations", "PhonemeOperations"),
            ("flexlibs2.code.Grammar.NaturalClassOperations", "NaturalClassOperations"),
            ("flexlibs2.code.Grammar.EnvironmentOperations", "EnvironmentOperations"),
            ("flexlibs2.code.Grammar.PhonologicalRuleOperations", "PhonologicalRuleOperations"),
            ("flexlibs2.code.Grammar.MorphRuleOperations", "MorphRuleOperations"),
            ("flexlibs2.code.Grammar.GramCatOperations", "GramCatOperations"),
            ("flexlibs2.code.Grammar.InflectionFeatureOperations", "InflectionFeatureOperations"),
            # Lexicon
            ("flexlibs2.code.Lexicon.LexEntryOperations", "LexEntryOperations"),
            ("flexlibs2.code.Lexicon.LexSenseOperations", "LexSenseOperations"),
            ("flexlibs2.code.Lexicon.ExampleOperations", "ExampleOperations"),
            ("flexlibs2.code.Lexicon.LexReferenceOperations", "LexReferenceOperations"),
            ("flexlibs2.code.Lexicon.VariantOperations", "VariantOperations"),
            ("flexlibs2.code.Lexicon.PronunciationOperations", "PronunciationOperations"),
            ("flexlibs2.code.Lexicon.SemanticDomainOperations", "SemanticDomainOperations"),
            ("flexlibs2.code.Lexicon.EtymologyOperations", "EtymologyOperations"),
            ("flexlibs2.code.Lexicon.AllomorphOperations", "AllomorphOperations"),
            ("flexlibs2.code.Lexicon.MSAOperations", "MSAOperations"),
            # TextsWords
            ("flexlibs2.code.TextsWords.TextOperations", "TextOperations"),
            ("flexlibs2.code.TextsWords.WordformOperations", "WordformOperations"),
            ("flexlibs2.code.TextsWords.WfiAnalysisOperations", "WfiAnalysisOperations"),
            ("flexlibs2.code.TextsWords.ParagraphOperations", "ParagraphOperations"),
            ("flexlibs2.code.TextsWords.SegmentOperations", "SegmentOperations"),
            ("flexlibs2.code.TextsWords.WfiGlossOperations", "WfiGlossOperations"),
            ("flexlibs2.code.TextsWords.WfiMorphBundleOperations", "WfiMorphBundleOperations"),
            ("flexlibs2.code.TextsWords.DiscourseOperations", "DiscourseOperations"),
            # Notebook
            ("flexlibs2.code.Notebook.NoteOperations", "NoteOperations"),
            ("flexlibs2.code.Notebook.PersonOperations", "PersonOperations"),
            ("flexlibs2.code.Notebook.LocationOperations", "LocationOperations"),
            ("flexlibs2.code.Notebook.AnthropologyOperations", "AnthropologyOperations"),
            ("flexlibs2.code.Notebook.DataNotebookOperations", "DataNotebookOperations"),
            # Lists
            ("flexlibs2.code.Lists.PublicationOperations", "PublicationOperations"),
            ("flexlibs2.code.Lists.AgentOperations", "AgentOperations"),
            ("flexlibs2.code.Lists.ConfidenceOperations", "ConfidenceOperations"),
            ("flexlibs2.code.Lists.OverlayOperations", "OverlayOperations"),
            ("flexlibs2.code.Lists.TranslationTypeOperations", "TranslationTypeOperations"),
            ("flexlibs2.code.Lists.PossibilityListOperations", "PossibilityListOperations"),
            # System
            ("flexlibs2.code.System.WritingSystemOperations", "WritingSystemOperations"),
            ("flexlibs2.code.System.ProjectSettingsOperations", "ProjectSettingsOperations"),
            ("flexlibs2.code.System.AnnotationDefOperations", "AnnotationDefOperations"),
            ("flexlibs2.code.System.CheckOperations", "CheckOperations"),
            ("flexlibs2.code.System.CustomFieldOperations", "CustomFieldOperations"),
            # Scripture
            ("flexlibs2.code.Scripture.ScrBookOperations", "ScrBookOperations"),
            ("flexlibs2.code.Scripture.ScrSectionOperations", "ScrSectionOperations"),
            ("flexlibs2.code.Scripture.ScrTxtParaOperations", "ScrTxtParaOperations"),
            ("flexlibs2.code.Scripture.ScrNoteOperations", "ScrNoteOperations"),
            ("flexlibs2.code.Scripture.ScrAnnotationsOperations", "ScrAnnotationsOperations"),
            ("flexlibs2.code.Scripture.ScrDraftOperations", "ScrDraftOperations"),
            # Reversal
            ("flexlibs2.code.Reversal.ReversalIndexOperations", "ReversalIndexOperations"),
            ("flexlibs2.code.Reversal.ReversalIndexEntryOperations", "ReversalIndexEntryOperations"),
            # Discourse
            ("flexlibs2.code.Discourse.ConstChartOperations", "ConstChartOperations"),
            ("flexlibs2.code.Discourse.ConstChartRowOperations", "ConstChartRowOperations"),
            ("flexlibs2.code.Discourse.ConstChartMarkerOperations", "ConstChartMarkerOperations"),
            ("flexlibs2.code.Discourse.ConstChartCellTagOperations", "ConstChartCellTagOperations"),
            ("flexlibs2.code.Discourse.ConstChartClauseMarkerOperations", "ConstChartClauseMarkerOperations"),
            ("flexlibs2.code.Discourse.ConstChartWordGroupOperations", "ConstChartWordGroupOperations"),
            ("flexlibs2.code.Discourse.ConstChartMovedTextOperations", "ConstChartMovedTextOperations"),
            # Shared
            ("flexlibs2.code.Shared.MediaOperations", "MediaOperations"),
            ("flexlibs2.code.Shared.FilterOperations", "FilterOperations"),
        ]

        loaded_count = 0
        failed_modules = []
        for module_path, class_name in operations_modules:
            try:
                module = importlib.import_module(module_path)
                ops_class = getattr(module, class_name)
                setattr(flexlibs2, class_name, ops_class)
                loaded_count += 1
            except ImportError as e:
                failed_modules.append((class_name, e))
            except AttributeError as e:
                failed_modules.append((class_name, e))
            except Exception as e:
                failed_modules.append((class_name, e))

        total = len(operations_modules)
        if failed_modules:
            lines = "\n".join(f"  {cls}: {err}" for cls, err in failed_modules)
            print(f"[ERROR] {len(failed_modules)}/{total} operations classes failed to import:\n{lines}")
            if os.environ.get("FLEXLIBS_ALLOW_PARTIAL_LOAD") != "1":
                raise pytest.UsageError(
                    f"{len(failed_modules)} operations class(es) failed to import "
                    f"(set FLEXLIBS_ALLOW_PARTIAL_LOAD=1 to continue anyway):\n{lines}"
                )
        print(f"[OK] Loaded {loaded_count}/{total} operations classes")

        # Verify
        ops_found = [x for x in dir(flexlibs2) if "Operations" in x]
        print(f"[INFO] flexlibs2 now has {len(ops_found)} operations available")

        _LCM_MODE = "live"

    except Exception as e:
        _LCM_MODE = "mock"
        if os.environ.get("FLEXLIBS_REQUIRE_LIVE") == "1":
            raise pytest.UsageError(
                f"FLEXLIBS_REQUIRE_LIVE=1 set but FLEx initialization failed: {e}. "
                "Refusing to fall back to mock mode."
            )
        print(f"\n[WARN] FLEx initialization failed: {e}")
        print("[WARN] Continuing in MOCK MODE - tests will use mock objects")
        print("[WARN] This is expected in CI/test environments without FieldWorks GUI")
        print("[INFO] Import tests and class structure tests will still work\n")

    yield  # Let tests run

    # Cleanup after all tests (if needed)
    print("[INFO] Test session complete")


# ========== PYTEST CONFIGURATION ==========


def pytest_configure(config):
    """Register custom markers for test categorization."""
    config.addinivalue_line("markers", "validation: mark test as validation test")
    config.addinivalue_line("markers", "phase2: mark test as Phase 2 (TextsWords, Grammar basics)")
    config.addinivalue_line("markers", "phase3: mark test as Phase 3 (Lexicon, more Grammar)")
    config.addinivalue_line("markers", "phase4: mark test as Phase 4 (all other categories)")
    config.addinivalue_line("markers", "write_enabled: mark test for write-enabled functionality")
    config.addinivalue_line("markers", "read_only: mark test for read-only project behavior")
    config.addinivalue_line("markers", "parameter_validation: mark test for parameter validation")
    config.addinivalue_line("markers", "type_checking: mark test for type validation")
    config.addinivalue_line("markers", "bounds_checking: mark test for bounds validation")
    config.addinivalue_line("markers", "string_validation: mark test for string validation")
    config.addinivalue_line(
        "markers",
        "requires_live_project: test opens a real .fwdata project "
        "(Target for write-path work; Sena 3 / Test / SampleLexicon for read-path)",
    )
    config.addinivalue_line(
        "markers",
        "live_phase(operations_class, phase): tag a live-DB test with which operations class and phase it exercises (phase: read|add|reorder|modify|delete)",
    )


# ========== MOCK PROJECT FIXTURE ==========


class MockFLExProject:
    """
    Mock FLExProject for testing validation without actual database.

    Simulates write-enabled/read-only states and CanModify() behavior.
    """

    def __init__(self, write_enabled=True):
        """
        Initialize mock project.

        Args:
            write_enabled: If True, project can be modified. If False, read-only.
        """
        self.write_enabled = write_enabled
        self._can_modify = write_enabled
        self.project = Mock()

    def CanModify(self):
        """Return whether project can be modified."""
        return self._can_modify

    def set_write_enabled(self, enabled):
        """Change write-enabled state."""
        self.write_enabled = enabled
        self._can_modify = enabled

    def set_can_modify(self, can_modify):
        """Set CanModify() return value."""
        self._can_modify = can_modify


@pytest.fixture
def mock_project_write_enabled():
    """
    Fixture: Mock FLExProject with write enabled.

    Used for testing modification operations that require write access.
    """
    return MockFLExProject(write_enabled=True)


@pytest.fixture
def mock_project_read_only():
    """
    Fixture: Mock FLExProject in read-only mode.

    Used for testing behavior when write access is disabled.
    """
    return MockFLExProject(write_enabled=False)


@pytest.fixture
def mock_project():
    """
    Fixture: Default mock project (write-enabled).

    Convenience fixture for most tests.
    """
    return MockFLExProject(write_enabled=True)


# ========== MOCK OBJECT FIXTURES ==========


@pytest.fixture
def mock_lex_entry():
    """Fixture: Mock ILexEntry object."""
    entry = Mock()
    entry.Id = "guid-12345"
    entry.Hvo = 1001
    entry.SensesOS = Mock()
    entry.SensesOS.Count = 3
    entry.AlternateFormsOS = Mock()
    entry.AlternateFormsOS.Count = 2
    entry.Owner = None  # Will be set by test if needed
    return entry


@pytest.fixture
def mock_lex_sense():
    """Fixture: Mock ILexSense object."""
    sense = Mock()
    sense.Id = "guid-67890"
    sense.Hvo = 1002
    sense.Gloss = Mock()
    sense.Definition = Mock()
    sense.ExamplesOS = Mock()
    sense.ExamplesOS.Count = 2
    sense.Owner = None  # Will be set to entry by test if needed
    return sense


@pytest.fixture
def mock_writing_system():
    """Fixture: Mock IWritingSystemDefinition object."""
    ws = Mock()
    ws.Id = "en"
    ws.Handle = 1  # Writing system handle
    ws.LanguageName = "English"
    return ws


@pytest.fixture
def mock_allomorph():
    """Fixture: Mock IMoAllomorph object."""
    allo = Mock()
    allo.Id = "guid-allo-123"
    allo.Hvo = 1003
    allo.Form = Mock()
    allo.Owner = None  # Will be set to entry by test
    return allo


# ========== MOCK OPERATIONS FIXTURES ==========


@pytest.fixture
def mock_operations_class(mock_project_write_enabled):
    """
    Fixture: Mock operations class with validation methods.

    Simulates any operation class inheriting from BaseOperations.
    """

    class MockOperations:
        """Mock operations class with all validation methods."""

        def __init__(self, project):
            self.project = project

        def _EnsureWriteEnabled(self):
            """Ensure write is enabled (from BaseOperations)."""
            if not self.project.CanModify():
                raise Exception(
                    "Project is read-only or not open. "
                    "Cannot perform modifications. "
                    "Open the project with writeEnabled=True."
                )

        def _ValidateParam(self, param, param_name="parameter"):
            """Validate parameter is not None."""
            if param is None:
                raise Exception(f"{param_name} cannot be None")

        def _ValidateParamNotEmpty(self, param, param_name="parameter"):
            """Validate parameter is not None and not empty."""
            if param is None:
                raise Exception(f"{param_name} cannot be None")
            if len(param) == 0:
                raise Exception(f"{param_name} cannot be empty")

        def _ValidateInstanceOf(self, obj, expected_type, param_name="object"):
            """Validate object is instance of expected type."""
            if not isinstance(obj, expected_type):
                if isinstance(expected_type, tuple):
                    type_names = " or ".join(t.__name__ for t in expected_type)
                else:
                    type_names = expected_type.__name__
                raise TypeError(f"{param_name} must be {type_names}, " f"got {type(obj).__name__}")

        def _ValidateStringNotEmpty(self, text, param_name="text"):
            """Validate string is not None and not empty."""
            if not isinstance(text, str):
                raise TypeError(f"{param_name} must be a string, got {type(text).__name__}")
            if text is None:
                raise Exception(f"{param_name} cannot be None")
            if len(text.strip()) == 0:
                raise Exception(f"{param_name} cannot be empty or contain only whitespace")

        def _ValidateIndexBounds(self, index, max_count, param_name="index"):
            """Validate index is within bounds [0, max_count-1]."""
            if not isinstance(index, int):
                raise TypeError(f"{param_name} must be an integer, got {type(index).__name__}")
            if index < 0:
                raise ValueError(f"{param_name} cannot be negative, got {index}")
            if index >= max_count:
                raise IndexError(
                    f"{param_name} out of bounds: {index} >= {max_count} " f"(valid range: 0-{max_count - 1})"
                )

        def _ValidateOwner(self, obj, expected_owner, param_name="object"):
            """Validate object has expected owner."""
            if not hasattr(obj, "Owner"):
                raise AttributeError(f"{param_name} does not have Owner property")
            if obj.Owner != expected_owner:
                raise ValueError(
                    f"{param_name} owner does not match expected owner. "
                    f"Object owner: {obj.Owner}, Expected: {expected_owner}"
                )

        def _NormalizeMultiString(self, value):
            """Convert FLEx empty placeholder to Python empty string."""
            if value is None:
                return None
            if value == "***":
                return ""
            return value

    return MockOperations(mock_project_write_enabled)


# ========== ASSERTION HELPERS ==========


class ValidationAssertions:
    """Helper class with assertion methods for validation errors."""

    @staticmethod
    def assert_write_enabled_error(func, *args, **kwargs):
        """
        Assert that function raises exception for read-only project.

        Args:
            func: Callable to execute
            *args, **kwargs: Arguments to pass to func

        Returns:
            The exception message
        """
        with pytest.raises(Exception) as exc_info:
            func(*args, **kwargs)

        assert "read-only" in str(exc_info.value).lower()
        return str(exc_info.value)

    @staticmethod
    def assert_param_error(func, *args, **kwargs):
        """
        Assert that function raises error for invalid parameter.

        Args:
            func: Callable to execute
            *args, **kwargs: Arguments to pass to func

        Returns:
            The exception message
        """
        with pytest.raises(Exception) as exc_info:
            func(*args, **kwargs)

        assert "cannot be None" in str(exc_info.value)
        return str(exc_info.value)

    @staticmethod
    def assert_type_error(func, *args, **kwargs):
        """
        Assert that function raises TypeError for wrong type.

        Args:
            func: Callable to execute
            *args, **kwargs: Arguments to pass to func

        Returns:
            The exception message
        """
        with pytest.raises(TypeError) as exc_info:
            func(*args, **kwargs)

        return str(exc_info.value)

    @staticmethod
    def assert_index_error(func, *args, **kwargs):
        """
        Assert that function raises IndexError for out-of-bounds index.

        Args:
            func: Callable to execute
            *args, **kwargs: Arguments to pass to func

        Returns:
            The exception message
        """
        with pytest.raises(IndexError) as exc_info:
            func(*args, **kwargs)

        assert "out of bounds" in str(exc_info.value)
        return str(exc_info.value)

    @staticmethod
    def assert_value_error(func, *args, **kwargs):
        """
        Assert that function raises ValueError.

        Args:
            func: Callable to execute
            *args, **kwargs: Arguments to pass to func

        Returns:
            The exception message
        """
        with pytest.raises(ValueError) as exc_info:
            func(*args, **kwargs)

        return str(exc_info.value)


@pytest.fixture
def assert_validation():
    """Fixture: Access validation assertion helpers."""
    return ValidationAssertions()


# ========== DATA GENERATORS ==========


class TestDataFactory:
    """Factory for generating test data."""

    @staticmethod
    def create_entries(count=5):
        """
        Generate mock lexical entries.

        Args:
            count: Number of entries to create

        Returns:
            List of mock ILexEntry objects
        """
        entries = []
        for i in range(count):
            entry = Mock()
            entry.Id = f"guid-entry-{i}"
            entry.Hvo = 2000 + i
            entry.SensesOS = Mock()
            entry.SensesOS.Count = (i % 3) + 1
            entries.append(entry)
        return entries

    @staticmethod
    def create_senses(count=3, owner=None):
        """
        Generate mock senses.

        Args:
            count: Number of senses to create
            owner: Owner (entry) for senses

        Returns:
            List of mock ILexSense objects
        """
        senses = []
        for i in range(count):
            sense = Mock()
            sense.Id = f"guid-sense-{i}"
            sense.Hvo = 3000 + i
            sense.Owner = owner
            senses.append(sense)
        return senses

    @staticmethod
    def create_writing_systems(count=2):
        """
        Generate mock writing systems.

        Args:
            count: Number of writing systems to create

        Returns:
            List of mock IWritingSystemDefinition objects
        """
        ws_list = [
            ("en", "English"),
            ("fr", "French"),
            ("es", "Spanish"),
            ("pt", "Portuguese"),
        ]

        systems = []
        for i in range(min(count, len(ws_list))):
            ws_id, ws_name = ws_list[i]
            ws = Mock()
            ws.Id = ws_id
            ws.LanguageName = ws_name
            ws.Handle = i + 1
            systems.append(ws)
        return systems


@pytest.fixture
def test_data():
    """Fixture: Access test data factory."""
    return TestDataFactory()


# ========== TEMPORARY DIRECTORY FIXTURE ==========


@pytest.fixture
def temp_test_dir(tmp_path):
    """
    Fixture: Temporary directory for test files.

    Args:
        tmp_path: Pytest's tmp_path fixture

    Returns:
        Path to temporary directory
    """
    return tmp_path


# ========== LIVE-PROJECT LEDGER (real-world test tracking) ==========
#
# Two-marker pattern:
#   - requires_live_project: selector marker. Tag every test that opens a
#     real .fwdata project so the suite can be run / excluded via
#     `pytest -m requires_live_project` (or `not requires_live_project`).
#   - live_phase(operations_class, phase): metadata marker. Records which
#     operations class and CRUD phase (read|add|reorder|modify|delete)
#     the test exercises, so pytest_sessionfinish can emit a per-class
#     status ledger at tests/live_status.json.
#
# The ledger is written ONLY when at least one requires_live_project test
# actually ran (call phase reported). Mock-only runs never overwrite it.

# Module-level recorder populated by pytest_runtest_logreport and consumed
# by pytest_sessionfinish. Keyed by nodeid -> {"status": ..., "duration": ...}.
_LIVE_RESULTS = {}

# Parallel recorder for the dashboard JSON. Stores per-test detail across
# all phases (setup/call/teardown) so the dashboard report has stdout,
# stderr, and tracebacks. Keyed by nodeid -> dict.
_DASHBOARD_RESULTS = {}


# Operations-class -> FLEx domain map, used by the dashboard JSON producer
# to label each test. Mirrors the operations_modules list in
# initialize_flex_for_tests; keep them in sync when adding a new class.
_OPERATIONS_CLASS_DOMAIN = {
    # Grammar
    "POSOperations": "Grammar",
    "PhonemeOperations": "Grammar",
    "NaturalClassOperations": "Grammar",
    "EnvironmentOperations": "Grammar",
    "PhonologicalRuleOperations": "Grammar",
    "MorphRuleOperations": "Grammar",
    "GramCatOperations": "Grammar",
    "InflectionFeatureOperations": "Grammar",
    # Lexicon
    "LexEntryOperations": "Lexicon",
    "LexSenseOperations": "Lexicon",
    "ExampleOperations": "Lexicon",
    "LexReferenceOperations": "Lexicon",
    "VariantOperations": "Lexicon",
    "PronunciationOperations": "Lexicon",
    "SemanticDomainOperations": "Lexicon",
    "EtymologyOperations": "Lexicon",
    "AllomorphOperations": "Lexicon",
    "MSAOperations": "Lexicon",
    # Texts & Words
    "TextOperations": "Texts & Words",
    "WordformOperations": "Texts & Words",
    "WfiAnalysisOperations": "Texts & Words",
    "ParagraphOperations": "Texts & Words",
    "SegmentOperations": "Texts & Words",
    "WfiGlossOperations": "Texts & Words",
    "WfiMorphBundleOperations": "Texts & Words",
    "DiscourseOperations": "Texts & Words",
    # Notebook
    "NoteOperations": "Notebook",
    "PersonOperations": "Notebook",
    "LocationOperations": "Notebook",
    "AnthropologyOperations": "Notebook",
    "DataNotebookOperations": "Notebook",
    # Lists
    "PublicationOperations": "Lists",
    "AgentOperations": "Lists",
    "ConfidenceOperations": "Lists",
    "OverlayOperations": "Lists",
    "TranslationTypeOperations": "Lists",
    "PossibilityListOperations": "Lists",
    # System
    "WritingSystemOperations": "System",
    "ProjectSettingsOperations": "System",
    "AnnotationDefOperations": "System",
    "CheckOperations": "System",
    "CustomFieldOperations": "System",
    # Scripture
    "ScrBookOperations": "Scripture",
    "ScrSectionOperations": "Scripture",
    "ScrTxtParaOperations": "Scripture",
    "ScrNoteOperations": "Scripture",
    "ScrAnnotationsOperations": "Scripture",
    "ScrDraftOperations": "Scripture",
    # Reversal
    "ReversalIndexOperations": "Reversal",
    "ReversalIndexEntryOperations": "Reversal",
    # Discourse
    "ConstChartOperations": "Discourse",
    "ConstChartRowOperations": "Discourse",
    "ConstChartMarkerOperations": "Discourse",
    "ConstChartCellTagOperations": "Discourse",
    "ConstChartClauseMarkerOperations": "Discourse",
    "ConstChartWordGroupOperations": "Discourse",
    "ConstChartMovedTextOperations": "Discourse",
    # Shared
    "MediaOperations": "Shared",
    "FilterOperations": "Shared",
}


# Fallback file-path substring -> domain. Matched against the lower-cased
# nodeid path; ordered most-specific first. Used when no live_phase marker
# pins down the operations class. The catch-all "Infrastructure" bucket at
# the end soaks up cross-cutting tests (BaseOperations, wrappers, LCM
# contract, smart collections, etc.) so nothing falls through as Unknown.
_FILE_PATH_DOMAIN_HINTS = (
    # Subdirectory hints (most specific)
    ("/lexicon/", "Lexicon"),
    ("/grammar/", "Grammar"),
    ("/textswords/", "Texts & Words"),
    ("/texts_words/", "Texts & Words"),
    ("/textwords/", "Texts & Words"),
    ("/notebook/", "Notebook"),
    ("/lists/", "Lists"),
    ("/system/", "System"),
    ("/scripture/", "Scripture"),
    ("/reversal/", "Reversal"),
    ("/discourse/", "Discourse"),
    ("/shared/", "Shared"),
    # Lexicon-flavored file names
    ("test_lex", "Lexicon"),
    ("test_example", "Lexicon"),
    ("test_sense", "Lexicon"),
    ("test_variant", "Lexicon"),
    ("test_pronunciation", "Lexicon"),
    ("test_semantic", "Lexicon"),
    ("test_etymology", "Lexicon"),
    ("test_allomorph", "Lexicon"),
    ("test_msa", "Lexicon"),
    ("test_homograph", "Lexicon"),
    ("test_set_pos_msa", "Lexicon"),
    # Grammar-flavored
    ("test_pos", "Grammar"),
    ("test_phoneme", "Grammar"),
    ("test_phonological", "Grammar"),
    ("test_phon_rule", "Grammar"),
    ("test_phon_feature", "Grammar"),
    ("test_morph", "Grammar"),
    ("test_natural_class", "Grammar"),
    ("test_environment", "Grammar"),
    ("test_gram_cat", "Grammar"),
    ("test_inflection", "Grammar"),
    ("test_compound_rule", "Grammar"),
    ("test_context_wrapper", "Grammar"),
    ("test_rule_pattern", "Grammar"),
    ("test_basic_ipa", "Grammar"),
    # Texts & Words
    ("test_text", "Texts & Words"),
    ("test_wordform", "Texts & Words"),
    ("test_wfi", "Texts & Words"),
    ("test_paragraph", "Texts & Words"),
    ("test_segment", "Texts & Words"),
    ("test_discourse", "Texts & Words"),
    # Notebook
    ("test_note", "Notebook"),
    ("test_person", "Notebook"),
    ("test_location", "Notebook"),
    ("test_anthropology", "Notebook"),
    # Lists
    ("test_publication", "Lists"),
    ("test_agent", "Lists"),
    ("test_confidence", "Lists"),
    ("test_overlay", "Lists"),
    ("test_translation_type", "Lists"),
    ("test_possibility", "Lists"),
    ("test_import_localized_lists", "Lists"),
    # System
    ("test_writing_system", "System"),
    ("test_project_settings", "System"),
    ("test_annotation_def", "System"),
    ("test_check", "System"),
    ("test_custom_field", "System"),
    # Scripture
    ("test_scr", "Scripture"),
    # Reversal
    ("test_reversal", "Reversal"),
    # Discourse
    ("test_const_chart", "Discourse"),
    # Shared
    ("test_media", "Shared"),
    ("test_filter", "Shared"),
    # Infrastructure / cross-cutting catch-all (must stay last, before
    # the final Unknown fallback in _infer_dashboard_domain)
    ("test_operations_baseline", "Infrastructure"),
    ("test_collections", "Infrastructure"),
    ("test_wrappers", "Infrastructure"),
    ("test_owner_cast_pattern", "Infrastructure"),
    ("test_catalog", "Infrastructure"),
    ("test_exception_handling", "Infrastructure"),
    ("test_lcm_contract", "Infrastructure"),
    ("test_lcm_api", "Infrastructure"),
    ("test_lcm_method", "Infrastructure"),
    ("test_lcm_direct", "Infrastructure"),
    ("test_consolidation_coverage", "Infrastructure"),
    ("test_flexproject_discoverability", "Infrastructure"),
    ("test_normalize_match_key", "Infrastructure"),
    ("test_write_enabled_fix", "Infrastructure"),
    ("test_itsstring_fix", "Infrastructure"),
    ("test_helpers", "Infrastructure"),
    ("/contract/", "Infrastructure"),
)


def pytest_runtest_logreport(report):
    """Record per-test outcomes for both the live-project ledger and the dashboard JSON."""
    nodeid = report.nodeid

    # --- Live-project ledger recorder (existing behavior) ---------------
    if report.when == "call" or (report.when == "setup" and report.skipped):
        if report.skipped:
            status = "skip"
        elif report.passed:
            status = "pass"
        elif report.failed:
            status = "error" if report.when != "call" else "fail"
        else:
            status = None

        if status is not None:
            existing = _LIVE_RESULTS.get(nodeid)
            if not (
                existing is not None
                and existing.get("status") in ("pass", "fail", "error")
                and status == "skip"
            ):
                _LIVE_RESULTS[nodeid] = {
                    "status": status,
                    "duration": getattr(report, "duration", 0.0),
                }

    # --- Dashboard JSON recorder ---------------------------------------
    # Capture detail across all phases so the dashboard has stdout/stderr
    # and tracebacks. The call phase is authoritative; setup/teardown
    # failures upgrade the record to "error".
    stdout_text = getattr(report, "capstdout", None) or None
    stderr_text = getattr(report, "capstderr", None) or None
    longrepr_text = getattr(report, "longreprtext", None) or None
    if longrepr_text == "":
        longrepr_text = None

    current = _DASHBOARD_RESULTS.get(nodeid)

    if report.when == "call":
        if report.passed:
            new_status = "pass"
            new_tb = None
        elif report.failed:
            new_status = "fail"
            new_tb = longrepr_text
        elif report.skipped:
            new_status = "skip"
            new_tb = longrepr_text
        else:
            return

        _DASHBOARD_RESULTS[nodeid] = {
            "status": new_status,
            "duration": getattr(report, "duration", 0.0),
            "stdout": stdout_text,
            "stderr": stderr_text,
            "traceback": new_tb,
        }

    elif report.when == "setup":
        if report.failed:
            _DASHBOARD_RESULTS[nodeid] = {
                "status": "error",
                "duration": getattr(report, "duration", 0.0),
                "stdout": stdout_text,
                "stderr": stderr_text,
                "traceback": longrepr_text,
            }
        elif report.skipped and current is None:
            _DASHBOARD_RESULTS[nodeid] = {
                "status": "skip",
                "duration": getattr(report, "duration", 0.0),
                "stdout": stdout_text,
                "stderr": stderr_text,
                "traceback": longrepr_text,
            }

    elif report.when == "teardown":
        if report.failed and current is not None and current.get("status") == "pass":
            current["status"] = "error"
            current["traceback"] = longrepr_text or current.get("traceback")
            if stderr_text and not current.get("stderr"):
                current["stderr"] = stderr_text


def _extract_live_phase(item):
    """Return (operations_class, phase) from a live_phase marker, or (None, None)."""
    marker = item.get_closest_marker("live_phase")
    if marker is None:
        return None, None
    args = marker.args
    kwargs = marker.kwargs
    if len(args) >= 2:
        return args[0], args[1]
    if "operations_class" in kwargs and "phase" in kwargs:
        return kwargs["operations_class"], kwargs["phase"]
    if len(args) == 1 and "phase" in kwargs:
        return args[0], kwargs["phase"]
    return None, None


_LIVE_PHASES = ("read", "add", "reorder", "modify", "delete")


def _infer_dashboard_domain(item):
    """Resolve a FLEx domain string for a test item."""
    marker = item.get_closest_marker("live_phase")
    if marker is not None:
        ops_class = None
        if marker.args:
            ops_class = marker.args[0]
        elif "operations_class" in marker.kwargs:
            ops_class = marker.kwargs["operations_class"]
        if ops_class and ops_class in _OPERATIONS_CLASS_DOMAIN:
            return _OPERATIONS_CLASS_DOMAIN[ops_class]

    try:
        path_str = str(item.fspath).replace("\\", "/").lower()
    except Exception:
        path_str = item.nodeid.replace("\\", "/").lower()
    for keyword, domain in _FILE_PATH_DOMAIN_HINTS:
        if keyword in path_str:
            return domain
    return "Unknown"


def _extract_dashboard_docstring(item):
    """Return the first non-empty line of the test function's docstring."""
    func = getattr(item, "function", None)
    if func is None:
        return None
    doc = getattr(func, "__doc__", None)
    if not doc:
        return None
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _write_dashboard_results_json(session):
    """
    Emit tests/test_results.json in the schema consumed by
    scripts/generate_dashboard.py. Always runs, regardless of which
    subset of tests was selected, so partial runs are still reflected
    (and merged into the persistent store by the dashboard generator).
    """
    import datetime
    import json

    tests_out = []
    for item in session.items:
        recorded = _DASHBOARD_RESULTS.get(item.nodeid)
        if recorded is None:
            continue

        parts = item.nodeid.split("::")
        name = parts[-1] if parts else item.nodeid
        class_name = parts[1] if len(parts) >= 3 else None

        is_live = item.get_closest_marker("requires_live_project") is not None
        tests_out.append(
            {
                "class_name": class_name,
                "docstring": _extract_dashboard_docstring(item),
                "domain": _infer_dashboard_domain(item),
                "duration": round(float(recorded.get("duration") or 0.0), 3),
                "name": name,
                "nodeid": item.nodeid,
                "status": recorded["status"],
                "stderr": recorded.get("stderr"),
                "stdout": recorded.get("stdout"),
                "traceback": recorded.get("traceback"),
                "type": "live" if is_live else "mock",
            }
        )

    if not tests_out:
        # No tests ran (e.g. collection failed); leave the file alone.
        return

    total = len(tests_out)
    passed = sum(1 for t in tests_out if t["status"] == "pass")
    failed = sum(1 for t in tests_out if t["status"] == "fail")
    skipped = sum(1 for t in tests_out if t["status"] == "skip")
    error = sum(1 for t in tests_out if t["status"] == "error")
    duration = round(sum(t["duration"] for t in tests_out), 3)
    pass_rate = round(passed / total * 100, 1) if total else 0

    payload = {
        "run_timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "duration_seconds": duration,
            "error": error,
            "failed": failed,
            "pass_rate_percent": pass_rate,
            "passed": passed,
            "skipped": skipped,
            "total": total,
        },
        "tests": tests_out,
    }

    out_path = os.path.join(_test_dir, "test_results.json")
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"\n[OK] Wrote {out_path} ({total} tests recorded)")
    except OSError as exc:
        print(f"[WARN] Could not write {out_path}: {exc}")


def pytest_sessionfinish(session, exitstatus):
    """
    Emit tests/test_results.json (always) and tests/live_status.json
    (only when at least one requires_live_project test actually executed).
    """
    import datetime
    import json

    _write_dashboard_results_json(session)

    live_items = [
        item
        for item in session.items
        if item.get_closest_marker("requires_live_project") is not None
    ]
    if not live_items:
        return

    # Filter to items that actually ran (have a recorded outcome).
    ran_items = [item for item in live_items if item.nodeid in _LIVE_RESULTS]
    if not ran_items:
        return

    by_test = {}
    by_class = {}
    uncategorized = []

    for item in ran_items:
        outcome = _LIVE_RESULTS[item.nodeid]
        ops_class, phase = _extract_live_phase(item)

        by_test[item.nodeid] = {
            "status": outcome["status"],
            "operations_class": ops_class,
            "phase": phase,
            "duration_seconds": round(float(outcome["duration"]), 3),
        }

        if ops_class is None or phase is None:
            uncategorized.append(
                f"{item.nodeid} -- missing live_phase marker"
            )
            continue

        cls_entry = by_class.setdefault(
            ops_class,
            {
                p: {"status": "untested", "tests": [], "last_verified": None}
                for p in _LIVE_PHASES
            },
        )
        if phase not in cls_entry:
            # Non-standard phase name; record it anyway.
            cls_entry[phase] = {"status": "untested", "tests": [], "last_verified": None}
        cls_entry[phase]["tests"].append(item.nodeid)

    today = datetime.date.today().isoformat()
    for ops_class, phases in by_class.items():
        for phase_name, cell in phases.items():
            tests = cell["tests"]
            if not tests:
                continue
            statuses = [by_test[t]["status"] for t in tests]
            if any(s == "fail" or s == "error" for s in statuses):
                cell["status"] = "fail"
                cell["last_verified"] = None
            elif all(s == "skip" for s in statuses):
                cell["status"] = "skip"
                cell["last_verified"] = None
            elif all(s == "pass" for s in statuses):
                cell["status"] = "pass"
                cell["last_verified"] = today
            else:
                # Mixed pass/skip without fail counts as pass for verification.
                if any(s == "pass" for s in statuses) and not any(
                    s in ("fail", "error") for s in statuses
                ):
                    cell["status"] = "pass"
                    cell["last_verified"] = today
                else:
                    cell["status"] = "untested"
                    cell["last_verified"] = None

    payload = {
        "run_timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        # "live" means the session reached a real LCM; "mock" means FLEx
        # initialization failed and the run silently degraded. A verification
        # claim citing this file must check run_mode == "live".
        "run_mode": _LCM_MODE,
        "by_test": by_test,
        "by_class": by_class,
        "uncategorized_live_tests": uncategorized,
    }

    out_path = os.path.join(_test_dir, "live_status.json")
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
    except OSError as exc:
        print(f"[WARN] Could not write {out_path}: {exc}")


# ========== LIVE SANDBOX FIXTURES (Phase E: destructive tests) ==========
#
# Phase E tests modify a sandbox copy of a live project, never the user's
# real one. Each invocation unzips a tests/fixtures/*.fwbackup into a
# fresh tempdir and opens the .fwdata by absolute path. Teardown removes
# the tempdir.
#
# Why a separate fixture: Phases A-D run in-place on the real project with
# self-restoring tests; Phase E is genuinely destructive so it gets its
# own isolated environment.


class _FwBackupSandbox:
    """Unzip an .fwbackup into a tempdir, yield the .fwdata path, clean up."""

    def __init__(self, fwbackup_path, prefix="fw_sandbox_"):
        import pathlib

        self.fwbackup_path = pathlib.Path(fwbackup_path)
        self.prefix = prefix
        self.temp_dir = None
        self.fwdata_path = None

    def __enter__(self):
        import pathlib
        import tempfile
        import zipfile

        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix=self.prefix))
        with zipfile.ZipFile(self.fwbackup_path) as zf:
            zf.extractall(self.temp_dir)
        fwdatas = list(self.temp_dir.glob("*.fwdata"))
        if not fwdatas:
            raise FileNotFoundError(
                f"No .fwdata found after unzipping {self.fwbackup_path} "
                f"to {self.temp_dir}"
            )
        self.fwdata_path = fwdatas[0]
        return self.fwdata_path

    def __exit__(self, exc_type, exc, tb):
        import shutil

        if self.temp_dir is not None and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        return False


@pytest.fixture
def sena3_sandbox():
    """
    Yield an open, write-enabled FLExProject restored fresh from the
    Sena 3 .fwbackup fixture. Teardown closes the project and deletes
    the temporary directory.

    Skips the dependent test if SIL.LCModel isn't loaded, if no .fwbackup
    is present in tests/fixtures/, or if OpenProject cannot accept the
    absolute path.

    Used by Phase E (destructive) tests so the user's real Sena 3
    project is never mutated.
    """
    import pathlib

    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    fixtures_dir = repo_root / "tests" / "fixtures"
    backups = sorted(fixtures_dir.glob("Sena 3*.fwbackup"))
    if not backups:
        pytest.skip(
            f"No Sena 3 .fwbackup found in {fixtures_dir}; run "
            "scripts/restore_sena3.py prerequisites or place the backup."
        )

    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception as exc:
        pytest.skip(f"Could not import FLExProject: {exc}")

    sandbox = _FwBackupSandbox(backups[-1], prefix="sena3_sandbox_")
    fwdata_path = sandbox.__enter__()

    project = FLExProject()
    try:
        try:
            project.OpenProject(str(fwdata_path), writeEnabled=True)
        except Exception as exc:
            sandbox.__exit__(None, None, None)
            pytest.skip(
                f"OpenProject rejected sandbox path {fwdata_path}: {exc}"
            )
        yield project
    finally:
        try:
            project.CloseProject()
        except Exception:
            pass
        sandbox.__exit__(None, None, None)


# ========== TARGET FIXTURES (write-path verification, blank scratch) ==========
#
# "Target" is the blank scratch FLEx project. It is the DEFAULT live
# database for write-path work: creating, modifying, and deleting objects
# against a clean slate, where a leaked TEST_ object is obvious and a
# restore is cheap (~1.3 MB backup vs Sena 3's ~15 MB).
#
# Division of labour:
#   Target  -- write-path verification. Mostly blank. Restore with
#              `python scripts/restore_target.py`.
#   Sena 3  -- read-path coverage and modify-pre-existing-data tests.
#              Populated. Restore with `python scripts/restore_sena3.py`.
#
# Any change written against the LCM write path MUST carry live evidence
# from one of these. See CLAUDE.md "Live LCM Verification (required)".

_TARGET_PROJECT_NAME = "Target"


@pytest.fixture(scope="module")
def target_project():
    """
    Module-scoped write-enabled FLExProject opened in-place on the real
    'Target' scratch project.

    Use for Phase B/C/D live verification (create-verify-delete,
    reorder, modify-and-restore). Tests MUST clean up after themselves
    in a `finally:` block -- prefix created objects with `TEST_`.

    Skips if SIL.LCModel isn't loaded or Target cannot be opened for
    writing, UNLESS FLEXLIBS_REQUIRE_LIVE=1, in which case it fails
    loudly rather than letting a write-path change pass unverified.
    """
    require_live = os.environ.get("FLEXLIBS_REQUIRE_LIVE") == "1"

    def _unavailable(reason):
        if require_live:
            if "another program" in reason or "in use" in reason:
                remedy = (
                    "Close the Target project in FieldWorks (the LCM file "
                    "lock is exclusive), then retry. If FLEx is already "
                    "closed the lock is stale -- log off and on again."
                )
            else:
                remedy = (
                    "Run `python scripts/restore_target.py` and retry."
                )
            pytest.fail(
                f"FLEXLIBS_REQUIRE_LIVE=1 but the Target project is "
                f"unavailable: {reason}\n{remedy}\n"
                f"Refusing to skip a live write-path verification. "
                f"If this change genuinely cannot be verified in-place, "
                f"use the target_sandbox fixture instead."
            )
        pytest.skip(reason)

    if "SIL.LCModel" not in sys.modules:
        _unavailable("Requires SIL.LCModel (FieldWorks installed)")

    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception as exc:
        _unavailable(f"Could not import FLExProject: {exc}")

    project = FLExProject()
    try:
        project.OpenProject(_TARGET_PROJECT_NAME, writeEnabled=True)
    except Exception as exc:
        _unavailable(
            f"Could not open {_TARGET_PROJECT_NAME!r} write-enabled: {exc}"
        )

    yield project

    try:
        project.CloseProject()
    except Exception:
        pass


@pytest.fixture
def target_sandbox():
    """
    Yield an open, write-enabled FLExProject restored fresh from the
    Target .fwbackup fixture into a tempdir. Teardown closes the project
    and deletes the temporary directory.

    Use for Phase E (destructive) tests, or any test that cannot restore
    the state it mutates. The user's real Target project is never touched.
    """
    import pathlib

    require_live = os.environ.get("FLEXLIBS_REQUIRE_LIVE") == "1"

    def _unavailable(reason):
        if require_live:
            pytest.fail(
                f"FLEXLIBS_REQUIRE_LIVE=1 but the Target sandbox is "
                f"unavailable: {reason}. Refusing to skip a live "
                f"write-path verification."
            )
        pytest.skip(reason)

    if "SIL.LCModel" not in sys.modules:
        _unavailable("Requires SIL.LCModel (FieldWorks installed)")

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    fixtures_dir = repo_root / "tests" / "fixtures"
    backups = sorted(fixtures_dir.glob("Target*.fwbackup"))
    if not backups:
        _unavailable(
            f"No Target .fwbackup found in {fixtures_dir}; copy the golden "
            "backup in (see tests/LIVE_TESTING.md)."
        )

    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception as exc:
        _unavailable(f"Could not import FLExProject: {exc}")

    sandbox = _FwBackupSandbox(backups[-1], prefix="target_sandbox_")
    fwdata_path = sandbox.__enter__()

    project = FLExProject()
    try:
        try:
            project.OpenProject(str(fwdata_path), writeEnabled=True)
        except Exception as exc:
            sandbox.__exit__(None, None, None)
            _unavailable(f"OpenProject rejected sandbox path {fwdata_path}: {exc}")
        yield project
    finally:
        try:
            project.CloseProject()
        except Exception:
            pass
        sandbox.__exit__(None, None, None)
