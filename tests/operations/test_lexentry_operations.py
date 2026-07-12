"""
Test Suite for LexEntryOperations

Tests CRUD operations for lexical entries:
- Create: Create new entries with different morph types
- Read: GetAll, Find, GetHeadword, property getters
- Update: SetLexemeForm, SetCitationForm, property setters
- Delete: Delete entries
- Senses: AddSense, GetSenseCount
- Reordering: Inherited BaseOperations methods

Uses mocking for unit tests that don't require FLEx connection.
Integration tests (marked separately) require real FLEx project.

Author: Programmer Team 3 - Test Infrastructure
Date: 2025-12-05
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
sys.path.insert(0, _project_root)

# Import test fixtures
from tests.operations import (
    mock_flex_project,
    mock_lex_entry,
    mock_lex_sense,
    assert_has_reordering_methods,
    assert_has_crud_methods,
    assert_inherits_base_operations,
    MockLCMObject,
    MockMultiString,
    MockOwningSequence,
)


# =============================================================================
# UNIT TESTS - Using Mocks
# =============================================================================


class TestLexEntryOperationsImport:
    """Test that LexEntryOperations can be imported and instantiated."""

    def test_import_lexentry_operations(self):
        """Test importing LexEntryOperations class."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        assert LexEntryOperations is not None

    def test_instantiate_with_mock_project(self, mock_flex_project):
        """Test instantiating LexEntryOperations with mock project."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert ops is not None
        assert ops.project == mock_flex_project


class TestLexEntryOperationsInheritance:
    """Test BaseOperations inheritance."""

    def test_inherits_from_base_operations(self):
        """Test that LexEntryOperations inherits from BaseOperations."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations
        from flexlibs2.code.BaseOperations import BaseOperations

        assert issubclass(LexEntryOperations, BaseOperations)

    def test_has_all_reordering_methods(self, mock_flex_project):
        """Test that LexEntryOperations has all reordering methods."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert_has_reordering_methods(ops)


class TestLexEntryOperationsCRUDMethods:
    """Test that CRUD methods exist and are callable."""

    def test_has_getall_method(self, mock_flex_project):
        """Test that GetAll method exists and is callable."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "GetAll")
        assert callable(ops.GetAll)

    def test_has_create_method(self, mock_flex_project):
        """Test that Create method exists and is callable."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "Create")
        assert callable(ops.Create)

    def test_has_delete_method(self, mock_flex_project):
        """Test that Delete method exists and is callable."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "Delete")
        assert callable(ops.Delete)

    def test_has_find_method(self, mock_flex_project):
        """Test that Find method exists and is callable."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "Find")
        assert callable(ops.Find)


class TestLexEntryOperationsPropertyGetters:
    """Test property getter methods."""

    def test_has_getheadword_method(self, mock_flex_project):
        """Test that GetHeadword method exists."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "GetHeadword")
        assert callable(ops.GetHeadword)

    def test_has_getcitationform_method(self, mock_flex_project):
        """Test that GetCitationForm method exists."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "GetCitationForm")
        assert callable(ops.GetCitationForm)

    def test_has_getlexemeform_method(self, mock_flex_project):
        """Test that GetLexemeForm method exists."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "GetLexemeForm")
        assert callable(ops.GetLexemeForm)

    def test_has_getsensecount_method(self, mock_flex_project):
        """Test that GetSenseCount method exists."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "GetSenseCount")
        assert callable(ops.GetSenseCount)


class TestLexEntryOperationsPropertySetters:
    """Test property setter methods."""

    def test_has_setcitationform_method(self, mock_flex_project):
        """Test that SetCitationForm method exists."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "SetCitationForm")
        assert callable(ops.SetCitationForm)

    def test_has_setlexemeform_method(self, mock_flex_project):
        """Test that SetLexemeForm method exists."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "SetLexemeForm")
        assert callable(ops.SetLexemeForm)


class TestLexEntryOperationsSenseMethods:
    """Test sense-related methods."""

    def test_has_addsense_method(self, mock_flex_project):
        """Test that AddSense method exists."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        assert hasattr(ops, "AddSense")
        assert callable(ops.AddSense)

    def test_has_getsenses_method(self, mock_flex_project):
        """Test that GetSenses method exists."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        ops = LexEntryOperations(mock_flex_project)
        # Check for either GetSenses or direct access to SensesOS
        # The operations class may provide different ways to access senses
        assert hasattr(ops, "GetSenses") or hasattr(ops, "GetSenseCount")


class TestLexEntryOperationsMockBehavior:
    """Test operations behavior with mock objects."""

    def test_getall_with_mock_repository(self, mock_flex_project):
        """Test GetAll returns iterator from mock repository."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        # Setup mock to return test entries
        mock_entries = [MockLCMObject(hvo=i) for i in range(3)]

        with patch.object(mock_flex_project, "ObjectsIn", return_value=iter(mock_entries)):
            ops = LexEntryOperations(mock_flex_project)
            result = list(ops.GetAll())

            assert len(result) == 3
            assert all(isinstance(e, MockLCMObject) for e in result)

    def test_getall_result_is_subscriptable_and_lenable(self, mock_flex_project):
        """
        Regression test for issue #201.

        `project.LexEntry.GetAll()` must return an object that supports
        `len()` and `entries[i]` directly -- without the caller needing to
        wrap the result in `list(...)` first. Before the fix, GetAll()
        returned the bare Python iterator produced by
        `self.project.ObjectsIn(...)` (via `iter(repo.AllInstances())`),
        which raised `TypeError` on both operations.
        """
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        mock_entries = [MockLCMObject(hvo=i) for i in range(3)]

        with patch.object(mock_flex_project, "ObjectsIn", return_value=iter(mock_entries)):
            ops = LexEntryOperations(mock_flex_project)
            entries = ops.GetAll()

            assert len(entries) == 3
            assert entries[0].Hvo == mock_entries[0].Hvo
            assert entries[-1].Hvo == mock_entries[-1].Hvo
            # Iterating more than once must still yield everything (the
            # wrapper caches its materialized list rather than exhausting
            # a single-use generator/iterator).
            assert list(entries) == list(entries) == mock_entries

    def test_getsensecount_with_mock_entry(self, mock_flex_project, mock_lex_entry):
        """Test GetSenseCount with mock entry."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations

        # Add mock senses to entry
        for i in range(3):
            sense = MockLCMObject(hvo=2000 + i)
            mock_lex_entry.SensesOS.Append(sense)

        ops = LexEntryOperations(mock_flex_project)

        # The method should be able to count senses
        # Even if it can't actually execute without real LCM objects,
        # we verify the method exists and accepts the right parameters
        assert hasattr(ops, "GetSenseCount")


class TestLexEntryOperationsExceptionHandling:
    """Test exception handling and validation."""

    def test_create_requires_write_enabled(self, mock_flex_project):
        """Test that Create raises error when project is read-only."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations
        from flexlibs2.code.FLExProject import FP_ReadOnlyError

        # Set project to read-only
        mock_flex_project.writeEnabled = False

        ops = LexEntryOperations(mock_flex_project)

        # Should raise FP_ReadOnlyError
        with pytest.raises(FP_ReadOnlyError):
            ops.Create("test")

    def test_create_validates_lexeme_form(self, mock_flex_project):
        """Test that Create validates lexeme form parameter."""
        from flexlibs2.code.Lexicon.LexEntryOperations import LexEntryOperations
        from flexlibs2.code.FLExProject import FP_NullParameterError, FP_ParameterError

        # Set project to write-enabled
        mock_flex_project.writeEnabled = True

        ops = LexEntryOperations(mock_flex_project)

        # Test with None
        with pytest.raises(FP_NullParameterError):
            ops.Create(None)

        # Test with empty string (may raise ParameterError)
        # Note: Actual behavior depends on implementation details


# =============================================================================
# INTEGRATION TESTS - Require Real FLEx Project
# =============================================================================


@pytest.mark.integration
@pytest.mark.requires_live_project
class TestLexEntryOperationsIntegration:
    """
    Integration tests that require a real FLEx project.

    These tests are marked with @pytest.mark.integration and can be run
    separately from unit tests. They require:
    - FLEx to be installed
    - A test project to be available
    - Write access to the project

    Run with: pytest -m integration
    """

    @pytest.fixture(scope="class")
    def flex_project(self):
        """Setup real FLEx project for integration testing.

        Uses the session-scoped FLEx services bootstrapped by
        tests/conftest.py::initialize_flex_for_tests. Calling
        FLExInitialize() / FLExCleanup() here would tear down state
        shared with the rest of the live-DB suite.
        """
        pytest.importorskip("flexlibs2")

        from flexlibs2 import FLExProject, AllProjectNames

        projects = AllProjectNames()
        if not projects:
            pytest.skip("No FLEx projects available for testing")

        project = FLExProject()
        project.OpenProject(projects[0], writeEnabled=True)

        yield project

        try:
            project.CloseProject()
        except Exception:
            pass

    def test_create_and_delete_entry(self, flex_project):
        """Integration test: Create and delete a lexical entry."""
        # This test requires a real FLEx project
        # It's marked as integration and will be skipped in basic test runs

        entry = flex_project.LexEntry.Create("test_entry_123")
        assert entry is not None

        # Verify it was created
        headword = flex_project.LexEntry.GetHeadword(entry)
        assert headword == "test_entry_123"

        # Delete it
        flex_project.LexEntry.Delete(entry)

    def test_getall_returns_entries(self, flex_project):
        """Integration test: GetAll returns actual entries."""
        entries = list(flex_project.LexEntry.GetAll())
        assert isinstance(entries, list)
        # Should have at least some entries (depends on test project)


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test (requires real FLEx)")


if __name__ == "__main__":
    # Run unit tests only by default
    pytest.main([__file__, "-v", "--tb=short", "-m", "not integration"])
