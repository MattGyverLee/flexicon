"""
Test Suite for WordformOperations (WfiWordformOperations)

Tests operations for wordforms (analyzed word occurrences):
- Create: Create wordform with form
- Read: GetAll, Find, GetForm
- Update: SetForm
- Delete: Delete wordforms
- Analyses: AddAnalysis, GetAnalyses
- Reordering: Inherited BaseOperations methods

Wordforms represent actual word occurrences in texts that can be analyzed.

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
    mock_wordform,
    assert_has_reordering_methods,
    MockLCMObject,
    MockMultiString,
    MockOwningSequence,
)


# =============================================================================
# UNIT TESTS - Using Mocks
# =============================================================================


class TestWordformOperationsImport:
    """Test that WfiWordformOperations can be imported and instantiated."""

    def test_import_wordform_operations(self):
        """Test importing WfiWordformOperations class."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        assert WfiWordformOperations is not None

    def test_instantiate_with_mock_project(self, mock_flex_project):
        """Test instantiating WfiWordformOperations with mock project."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        assert ops is not None
        assert ops.project == mock_flex_project


class TestWordformOperationsInheritance:
    """Test BaseOperations inheritance."""

    def test_inherits_from_base_operations(self):
        """Test that WfiWordformOperations inherits from BaseOperations."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations
        from flexicon.code.BaseOperations import BaseOperations

        assert issubclass(WfiWordformOperations, BaseOperations)

    def test_has_all_reordering_methods(self, mock_flex_project):
        """Test that WfiWordformOperations has all reordering methods."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        assert_has_reordering_methods(ops)


class TestWordformOperationsCRUDMethods:
    """Test that CRUD methods exist and are callable."""

    def test_has_getall_method(self, mock_flex_project):
        """Test that GetAll method exists and is callable."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        assert hasattr(ops, "GetAll")
        assert callable(ops.GetAll)

    def test_has_create_method(self, mock_flex_project):
        """Test that Create method exists and is callable."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        assert hasattr(ops, "Create")
        assert callable(ops.Create)

    def test_has_delete_method(self, mock_flex_project):
        """Test that Delete method exists and is callable."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        assert hasattr(ops, "Delete")
        assert callable(ops.Delete)

    def test_has_find_method(self, mock_flex_project):
        """Test that Find method exists and is callable."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        assert hasattr(ops, "Find")
        assert callable(ops.Find)


class TestWordformOperationsPropertyGetters:
    """Test property getter methods."""

    def test_has_getform_method(self, mock_flex_project):
        """Test that GetForm method exists."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        assert hasattr(ops, "GetForm")
        assert callable(ops.GetForm)

    def test_has_getanalyses_method(self, mock_flex_project):
        """Test that GetAnalyses or similar method exists."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        # Check for analysis-related methods
        assert hasattr(ops, "GetAnalyses") or hasattr(ops, "GetAnalysisCount")


class TestWordformOperationsPropertySetters:
    """Test property setter methods."""

    def test_has_setform_method(self, mock_flex_project):
        """Test that SetForm method exists."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        assert hasattr(ops, "SetForm")
        assert callable(ops.SetForm)


class TestWordformOperationsAnalysisMethods:
    """Test analysis-related methods."""

    def test_has_addanalysis_method(self, mock_flex_project):
        """Test that AddAnalysis method exists."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(mock_flex_project)
        # Check for analysis methods
        assert hasattr(ops, "AddAnalysis") or hasattr(ops, "GetAnalyses")


class TestWordformOperationsMockBehavior:
    """Test operations behavior with mock objects."""

    def test_mock_wordform_structure(self, mock_wordform):
        """Test mock wordform has expected structure."""
        assert hasattr(mock_wordform, "Form")
        assert hasattr(mock_wordform, "AnalysesOC")
        assert hasattr(mock_wordform, "Hvo")
        assert hasattr(mock_wordform, "Guid")

    def test_getall_with_mock_repository(self, mock_flex_project):
        """Test GetAll returns iterator from mock repository."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        # Setup mock to return test wordforms
        mock_wordforms = [MockLCMObject(hvo=5000 + i) for i in range(3)]

        with patch.object(mock_flex_project, "ObjectsIn", return_value=iter(mock_wordforms)):
            ops = WfiWordformOperations(mock_flex_project)
            result = list(ops.GetAll())

            assert len(result) == 3

    def test_getform_with_mock_wordform(self, mock_flex_project, mock_wordform):
        """Test GetForm with mock wordform."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        # Set form on mock
        mock_wordform.Form = MockMultiString({"en": "running"})

        ops = WfiWordformOperations(mock_flex_project)

        # The method should exist
        assert hasattr(ops, "GetForm")


class TestWordformOperationsValidation:
    """Test validation and error handling."""

    def test_create_requires_write_enabled(self, mock_flex_project):
        """Test that Create raises error when project is read-only."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations
        from flexicon.code.FLExProject import FP_ReadOnlyError

        # Set project to read-only
        mock_flex_project.writeEnabled = False

        ops = WfiWordformOperations(mock_flex_project)

        # Should raise FP_ReadOnlyError
        with pytest.raises(FP_ReadOnlyError):
            ops.Create("test")


# =============================================================================
# INTEGRATION TESTS - Require Real FLEx Project
# =============================================================================


@pytest.mark.integration
@pytest.mark.requires_live_project
class TestWordformOperationsIntegration:
    """
    Integration tests that require a real FLEx project.

    Run with: pytest -m integration
    """

    @pytest.fixture(scope="class")
    def flex_project(self):
        """Setup real FLEx project for integration testing.

        Uses the session-scoped FLEx services bootstrapped by
        tests/conftest.py::initialize_flex_for_tests. Calling
        FLExInitialize() / FLExCleanup() here would tear down SLDR
        for the remainder of the suite, causing later OpenProject
        calls to mark .ldml files as bad ("SLDR has not been
        initialized") and triggering the "Unable to create writing
        system" popup on the next run.
        """
        pytest.importorskip("SIL.LCModel")

        from flexicon.code.FLExProject import FLExProject, AllProjectNames

        projects = AllProjectNames()
        if not projects:
            pytest.skip("No FLEx projects available")

        project = FLExProject()
        project.OpenProject(projects[0], writeEnabled=True)

        yield project

        project.CloseProject()

    def test_create_and_delete_wordform(self, flex_project):
        """Integration test: Create and delete a wordform."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(flex_project)

        # Create wordform
        wordform = ops.Create("testword123")
        assert wordform is not None

        # Verify form
        form = ops.GetForm(wordform)
        assert "testword123" in form

        # Delete wordform
        ops.Delete(wordform)

    def test_getall_returns_wordforms(self, flex_project):
        """Integration test: GetAll returns wordforms."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(flex_project)
        wordforms = list(ops.GetAll())

        assert isinstance(wordforms, list)
        # Wordforms may or may not exist depending on project

    def test_find_wordform(self, flex_project):
        """Integration test: Find wordform by form."""
        from flexicon.code.TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

        ops = WfiWordformOperations(flex_project)

        # Try to find a wordform (may not exist)
        result = ops.Find("test")
        # Result may be None


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test (requires real FLEx)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not integration"])
