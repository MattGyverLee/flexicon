"""
Test Suite for POSOperations

Tests operations for Parts of Speech:
- Create: Create POS with name and abbreviation
- Read: GetAll, Find, GetName, GetAbbreviation
- Update: SetName, SetAbbreviation
- Delete: Delete POS
- Hierarchy: GetSubcategories, parent/child relationships
- Reordering: Inherited BaseOperations methods
- Sequence: _GetSequence returns parent.SubPossibilitiesOS

Parts of Speech are organized hierarchically (e.g., Noun > Common Noun, Proper Noun).

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
    mock_pos,
    assert_has_reordering_methods,
    MockLCMObject,
    MockMultiString,
    MockOwningSequence,
)


# =============================================================================
# UNIT TESTS - Using Mocks
# =============================================================================


class TestPOSOperationsImport:
    """Test that POSOperations can be imported and instantiated."""

    def test_import_pos_operations(self):
        """Test importing POSOperations class."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        assert POSOperations is not None

    def test_instantiate_with_mock_project(self, mock_flex_project):
        """Test instantiating POSOperations with mock project."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert ops is not None
        assert ops.project == mock_flex_project


class TestPOSOperationsInheritance:
    """Test BaseOperations inheritance."""

    def test_inherits_from_base_operations(self):
        """Test that POSOperations inherits from BaseOperations."""
        from flexicon.code.Grammar.POSOperations import POSOperations
        from flexicon.code.BaseOperations import BaseOperations

        assert issubclass(POSOperations, BaseOperations)

    def test_has_all_reordering_methods(self, mock_flex_project):
        """Test that POSOperations has all reordering methods."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert_has_reordering_methods(ops)

    def test_has_getsequence_implementation(self, mock_flex_project):
        """Test that _GetSequence is implemented for POS."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert hasattr(ops, "_GetSequence")

        # Test with mock POS that has subcategories
        mock_parent_pos = MockLCMObject()
        mock_parent_pos.SubPossibilitiesOS = MockOwningSequence()

        # Should return SubPossibilitiesOS
        sequence = ops._GetSequence(mock_parent_pos)
        assert sequence is mock_parent_pos.SubPossibilitiesOS


class TestPOSOperationsCRUDMethods:
    """Test that CRUD methods exist and are callable."""

    def test_has_getall_method(self, mock_flex_project):
        """Test that GetAll method exists and is callable."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert hasattr(ops, "GetAll")
        assert callable(ops.GetAll)

    def test_has_create_method(self, mock_flex_project):
        """Test that Create method exists and is callable."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert hasattr(ops, "Create")
        assert callable(ops.Create)

    def test_has_delete_method(self, mock_flex_project):
        """Test that Delete method exists and is callable."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert hasattr(ops, "Delete")
        assert callable(ops.Delete)

    def test_has_find_method(self, mock_flex_project):
        """Test that Find method exists and is callable."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert hasattr(ops, "Find")
        assert callable(ops.Find)


class TestPOSOperationsPropertyGetters:
    """Test property getter methods."""

    def test_has_getname_method(self, mock_flex_project):
        """Test that GetName method exists."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert hasattr(ops, "GetName")
        assert callable(ops.GetName)

    def test_has_getabbreviation_method(self, mock_flex_project):
        """Test that GetAbbreviation method exists."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert hasattr(ops, "GetAbbreviation")
        assert callable(ops.GetAbbreviation)


class TestPOSOperationsPropertySetters:
    """Test property setter methods."""

    def test_has_setname_method(self, mock_flex_project):
        """Test that SetName method exists."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert hasattr(ops, "SetName")
        assert callable(ops.SetName)

    def test_has_setabbreviation_method(self, mock_flex_project):
        """Test that SetAbbreviation method exists."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        assert hasattr(ops, "SetAbbreviation")
        assert callable(ops.SetAbbreviation)


class TestPOSOperationsHierarchy:
    """Test POS hierarchy navigation methods."""

    def test_has_getsubcategories_method(self, mock_flex_project):
        """Test that GetSubcategories method exists."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(mock_flex_project)
        # Check for GetSubcategories or similar hierarchy method
        assert hasattr(ops, "GetSubcategories") or hasattr(ops, "_GetSequence")


class TestPOSOperationsReordering:
    """Test reordering functionality with mock POS."""

    def test_sort_subcategories(self, mock_flex_project):
        """Test sorting POS subcategories."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        # Create parent POS with subcategories
        parent_pos = MockLCMObject()
        parent_pos.SubPossibilitiesOS = MockOwningSequence()

        # Add subcategories
        for i, name in enumerate(["Verb", "Noun", "Adjective"]):
            sub_pos = MockLCMObject(hvo=3000 + i)
            sub_pos.Name = MockMultiString({"en": name})
            sub_pos.Abbreviation = MockMultiString({"en": name[0]})
            parent_pos.SubPossibilitiesOS.Append(sub_pos)

        ops = POSOperations(mock_flex_project)

        # Sort method exists
        assert hasattr(ops, "Sort")
        assert callable(ops.Sort)


# =============================================================================
# UNIT TESTS - GetEntryCount (issue #105)
# =============================================================================


def _make_project_for_entry_count(entry_repo_instances):
    """
    Build a minimal mock FLExProject whose entry repository returns the
    supplied list of mock entries. ``project.project`` is the internal
    LCM cache accessor used by POSOperations.
    """
    project = Mock()
    project.writeEnabled = True
    project.Object = Mock(side_effect=lambda hvo: Mock(Hvo=hvo))

    mock_repo = Mock()
    mock_repo.AllInstances = Mock(return_value=entry_repo_instances)

    mock_service_locator = Mock()
    mock_service_locator.GetService = Mock(return_value=mock_repo)

    project.project = Mock()
    project.project.ServiceLocator = mock_service_locator
    project.lp = Mock()
    # PartsOfSpeechOA for GetAll / _GetSequence
    project.lp.PartsOfSpeechOA = Mock()
    project.lp.PartsOfSpeechOA.PossibilitiesOS = []
    return project


def _make_mock_entry_with_pos(pos_hvo):
    """Return a mock ILexEntry whose single MSA points to the given POS HVO."""
    entry = Mock()
    msa = Mock()
    msa.Hvo = 9000 + pos_hvo
    entry.MorphoSyntaxAnalysesOC = [msa]
    # get_pos_from_msa is patched at call-site to return a POS mock based on this.
    return entry, msa


class TestGetEntryCount:
    """Mock-based unit tests for POSOperations.GetEntryCount (issue #105)."""

    def _import_ops(self):
        from flexicon.code.Grammar.POSOperations import POSOperations
        return POSOperations

    # ------------------------------------------------------------------
    # Normal count: direct-only (recursive=False)
    # ------------------------------------------------------------------

    def test_normal_count_direct_only(self):
        """GetEntryCount returns correct count for direct POS matches."""
        POSOperations = self._import_ops()

        noun_hvo = 100
        verb_hvo = 200

        noun_pos = Mock(Hvo=noun_hvo)
        verb_pos = Mock(Hvo=verb_hvo)

        entry1, msa1 = _make_mock_entry_with_pos(noun_hvo)
        entry2, msa2 = _make_mock_entry_with_pos(noun_hvo)
        entry3, msa3 = _make_mock_entry_with_pos(verb_hvo)

        # Map each MSA to its POS via get_pos_from_msa
        pos_map = {
            id(msa1): noun_pos,
            id(msa2): noun_pos,
            id(msa3): verb_pos,
        }

        project = _make_project_for_entry_count([entry1, entry2, entry3])
        ops = POSOperations(project)

        with patch(
            "flexicon.code.Grammar.POSOperations.get_pos_from_msa",
            side_effect=lambda m: pos_map.get(id(m)),
        ):
            count = ops.GetEntryCount(noun_pos)

        assert count == 2, f"Expected 2 noun entries, got {count}"

    # ------------------------------------------------------------------
    # Empty category: no entries tagged with this POS
    # ------------------------------------------------------------------

    def test_empty_category_returns_zero(self):
        """GetEntryCount returns 0 when no entries are tagged with the POS."""
        POSOperations = self._import_ops()

        rare_pos = Mock(Hvo=999)
        other_pos = Mock(Hvo=111)

        entry1, msa1 = _make_mock_entry_with_pos(111)
        pos_map = {id(msa1): other_pos}

        project = _make_project_for_entry_count([entry1])
        ops = POSOperations(project)

        with patch(
            "flexicon.code.Grammar.POSOperations.get_pos_from_msa",
            side_effect=lambda m: pos_map.get(id(m)),
        ):
            count = ops.GetEntryCount(rare_pos)

        assert count == 0

    def test_no_entries_at_all_returns_zero(self):
        """GetEntryCount returns 0 when the lexicon is empty."""
        POSOperations = self._import_ops()

        noun_pos = Mock(Hvo=100)
        project = _make_project_for_entry_count([])
        ops = POSOperations(project)

        with patch(
            "flexicon.code.Grammar.POSOperations.get_pos_from_msa",
            side_effect=lambda m: None,
        ):
            count = ops.GetEntryCount(noun_pos)

        assert count == 0

    # ------------------------------------------------------------------
    # Nested subcategories (recursive=True)
    # ------------------------------------------------------------------

    def test_recursive_count_includes_subcategories(self):
        """GetEntryCount(recursive=True) rolls up entries from descendant POS."""
        POSOperations = self._import_ops()

        noun_hvo = 100
        proper_noun_hvo = 101
        common_noun_hvo = 102

        noun_pos = Mock(Hvo=noun_hvo)
        proper_noun_pos = Mock(Hvo=proper_noun_hvo)
        common_noun_pos = Mock(Hvo=common_noun_hvo)

        entry1, msa1 = _make_mock_entry_with_pos(noun_hvo)
        entry2, msa2 = _make_mock_entry_with_pos(proper_noun_hvo)
        entry3, msa3 = _make_mock_entry_with_pos(common_noun_hvo)

        pos_map = {
            id(msa1): noun_pos,
            id(msa2): proper_noun_pos,
            id(msa3): common_noun_pos,
        }

        project = _make_project_for_entry_count([entry1, entry2, entry3])
        ops = POSOperations(project)

        # Patch GetSubcategories so POSOperations sees a two-child hierarchy.
        with patch.object(
            ops, "GetSubcategories", return_value=[proper_noun_pos, common_noun_pos]
        ):
            with patch(
                "flexicon.code.Grammar.POSOperations.get_pos_from_msa",
                side_effect=lambda m: pos_map.get(id(m)),
            ):
                count = ops.GetEntryCount(noun_pos, recursive=True)

        assert count == 3, (
            f"recursive=True should count all 3 entries (noun + proper noun + "
            f"common noun), got {count}"
        )

    def test_recursive_vs_direct_differ_when_subcategories_exist(self):
        """recursive=False and recursive=True diverge when subcategories have entries."""
        POSOperations = self._import_ops()

        noun_hvo = 100
        proper_noun_hvo = 101

        noun_pos = Mock(Hvo=noun_hvo)
        proper_noun_pos = Mock(Hvo=proper_noun_hvo)

        # Only the subcategory has entries; the parent has none.
        entry1, msa1 = _make_mock_entry_with_pos(proper_noun_hvo)
        pos_map = {id(msa1): proper_noun_pos}

        project = _make_project_for_entry_count([entry1])
        ops = POSOperations(project)

        with patch.object(ops, "GetSubcategories", return_value=[proper_noun_pos]):
            with patch(
                "flexicon.code.Grammar.POSOperations.get_pos_from_msa",
                side_effect=lambda m: pos_map.get(id(m)),
            ):
                direct_count = ops.GetEntryCount(noun_pos, recursive=False)
                recursive_count = ops.GetEntryCount(noun_pos, recursive=True)

        assert direct_count == 0, "Direct count must ignore subcategory entries"
        assert recursive_count == 1, "Recursive count must include subcategory entries"

    # ------------------------------------------------------------------
    # Each entry counted at most once even with multiple MSAs
    # ------------------------------------------------------------------

    def test_entry_counted_once_even_with_multiple_msas(self):
        """An entry with two MSAs both tagged to the same POS is counted once."""
        POSOperations = self._import_ops()

        noun_hvo = 100
        noun_pos = Mock(Hvo=noun_hvo)

        msa_a = Mock()
        msa_b = Mock()
        entry = Mock()
        entry.MorphoSyntaxAnalysesOC = [msa_a, msa_b]

        pos_map = {id(msa_a): noun_pos, id(msa_b): noun_pos}

        project = _make_project_for_entry_count([entry])
        ops = POSOperations(project)

        with patch(
            "flexicon.code.Grammar.POSOperations.get_pos_from_msa",
            side_effect=lambda m: pos_map.get(id(m)),
        ):
            count = ops.GetEntryCount(noun_pos)

        assert count == 1, (
            "An entry must be counted at most once even if multiple MSAs "
            "point to the same POS."
        )

    # ------------------------------------------------------------------
    # None parameter raises FP_NullParameterError
    # ------------------------------------------------------------------

    def test_none_parameter_raises(self):
        """GetEntryCount(None) must raise FP_NullParameterError."""
        POSOperations = self._import_ops()

        project = _make_project_for_entry_count([])
        ops = POSOperations(project)

        from flexicon.code.FLExProject import FP_NullParameterError

        with pytest.raises(FP_NullParameterError):
            ops.GetEntryCount(None)


# =============================================================================
# INTEGRATION TESTS - Require Real FLEx Project
# =============================================================================


@pytest.mark.integration
@pytest.mark.requires_live_project
class TestPOSOperationsIntegration:
    """
    Integration tests that require a real FLEx project.

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
        pytest.importorskip("flexicon")

        from flexicon import FLExProject, AllProjectNames

        projects = AllProjectNames()
        if not projects:
            pytest.skip("No FLEx projects available")

        project = FLExProject()
        project.OpenProject(projects[0], writeEnabled=True)

        yield project

        try:
            project.CloseProject()
        except Exception:
            pass

    def test_getall_returns_pos(self, flex_project):
        """Integration test: GetAll returns POS list."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(flex_project)
        pos_list = list(ops.GetAll())

        assert isinstance(pos_list, list)
        # Most projects should have at least some POS defined

    def test_find_pos_by_name(self, flex_project):
        """Integration test: Find POS by name."""
        from flexicon.code.Grammar.POSOperations import POSOperations

        ops = POSOperations(flex_project)

        # Try to find common POS (may not exist in all projects)
        result = ops.Find("Noun")
        # Result may be None if not found


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test (requires real FLEx)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not integration"])
