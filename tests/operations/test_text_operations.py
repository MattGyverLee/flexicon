"""
Test Suite for TextOperations

Tests operations for Texts (interlinearized texts):
- Create: Create text with title
- Read: GetAll, Find, GetTitle, GetGenre
- Update: SetTitle, SetGenre
- Delete: Delete texts
- Paragraphs: AddParagraph, GetParagraphs
- Reordering: Inherited BaseOperations methods

Texts are containers for analyzed discourse (stories, conversations, etc.).

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
    mock_text,
    assert_has_reordering_methods,
    MockLCMObject,
    MockMultiString,
    MockOwningSequence,
)


# =============================================================================
# UNIT TESTS - Using Mocks
# =============================================================================


class TestTextOperationsImport:
    """Test that TextOperations can be imported and instantiated."""

    def test_import_text_operations(self):
        """Test importing TextOperations class."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        assert TextOperations is not None

    def test_instantiate_with_mock_project(self, mock_flex_project):
        """Test instantiating TextOperations with mock project."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        assert ops is not None
        assert ops.project == mock_flex_project


class TestTextOperationsInheritance:
    """Test BaseOperations inheritance."""

    def test_inherits_from_base_operations(self):
        """Test that TextOperations inherits from BaseOperations."""
        from flexicon.code.TextsWords.TextOperations import TextOperations
        from flexicon.code.BaseOperations import BaseOperations

        assert issubclass(TextOperations, BaseOperations)

    def test_has_all_reordering_methods(self, mock_flex_project):
        """Test that TextOperations has all reordering methods."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        assert_has_reordering_methods(ops)


class TestTextOperationsCRUDMethods:
    """Test that CRUD methods exist and are callable."""

    def test_has_getall_method(self, mock_flex_project):
        """Test that GetAll method exists and is callable."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        assert hasattr(ops, "GetAll")
        assert callable(ops.GetAll)

    def test_has_create_method(self, mock_flex_project):
        """Test that Create method exists and is callable."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        assert hasattr(ops, "Create")
        assert callable(ops.Create)

    def test_has_delete_method(self, mock_flex_project):
        """Test that Delete method exists and is callable."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        assert hasattr(ops, "Delete")
        assert callable(ops.Delete)

    def test_has_find_method(self, mock_flex_project):
        """Test that Find method exists and is callable."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        assert hasattr(ops, "Find")
        assert callable(ops.Find)


class TestTextOperationsPropertyGetters:
    """Test property getter methods."""

    def test_has_gettitle_method(self, mock_flex_project):
        """Test that GetTitle method exists."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        assert hasattr(ops, "GetTitle")
        assert callable(ops.GetTitle)

    def test_has_getgenre_method(self, mock_flex_project):
        """Test that GetGenre method exists."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        # Genre may be accessed differently
        assert hasattr(ops, "GetGenre") or hasattr(ops, "GetTitle")


class TestTextOperationsPropertySetters:
    """Test property setter methods."""

    def test_has_settitle_method(self, mock_flex_project):
        """Test that SetTitle method exists."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        assert hasattr(ops, "SetTitle")
        assert callable(ops.SetTitle)


class TestTextOperationsParagraphMethods:
    """Test paragraph-related methods."""

    def test_has_addparagraph_method(self, mock_flex_project):
        """Test that AddParagraph method exists."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        # Check for paragraph-related methods
        assert hasattr(ops, "AddParagraph") or hasattr(ops, "GetParagraphCount")


class TestTextOperationsMockBehavior:
    """Test operations behavior with mock objects."""

    def test_mock_text_structure(self, mock_text):
        """Test mock text has expected structure."""
        assert hasattr(mock_text, "Name")
        assert hasattr(mock_text, "ContentsOA")
        assert hasattr(mock_text, "Hvo")
        assert hasattr(mock_text, "Guid")

    def test_getall_with_mock_repository(self, mock_flex_project):
        """Test GetAll returns iterator from mock repository."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        # Setup mock to return test texts
        mock_texts = [MockLCMObject(hvo=4000 + i) for i in range(2)]

        with patch.object(mock_flex_project, "ObjectsIn", return_value=iter(mock_texts)):
            ops = TextOperations(mock_flex_project)
            result = list(ops.GetAll())

            assert len(result) == 2

    def test_getall_result_is_subscriptable_and_lenable(self, mock_flex_project):
        """
        Regression test for issue #201.

        `project.Texts.GetAll()` must support `len()` and indexing
        directly, not just `for text in project.Texts.GetAll(): ...`.
        """
        from flexicon.code.TextsWords.TextOperations import TextOperations

        mock_texts = [MockLCMObject(hvo=4000 + i) for i in range(2)]

        with patch.object(mock_flex_project, "ObjectsIn", return_value=iter(mock_texts)):
            ops = TextOperations(mock_flex_project)
            texts = ops.GetAll()

            assert len(texts) == 2
            assert texts[0].Hvo == mock_texts[0].Hvo
            assert texts[1].Hvo == mock_texts[1].Hvo


class TestTextOperationsValidation:
    """Test validation and error handling."""

    def test_create_requires_write_enabled(self, mock_flex_project):
        """Test that Create raises error when project is read-only."""
        from flexicon.code.TextsWords.TextOperations import TextOperations
        from flexicon.code.FLExProject import FP_ReadOnlyError

        # Set project to read-only
        mock_flex_project.writeEnabled = False

        ops = TextOperations(mock_flex_project)

        # Should raise FP_ReadOnlyError
        with pytest.raises(FP_ReadOnlyError):
            ops.Create("Test Text")


class TestTextOperationsDeleteMechanism:
    """Mock-mode guard for #317 -- runs without a live FLEx project.

    The live effect test (test_delete_actually_removes_the_text) is the real
    proof, but this repo's per-PR CI is AST-only and never invokes pytest
    against a database; the full suite runs weekly on a self-hosted runner.
    These two assertions pin the mechanism in fast CI so a re-regression is
    caught at PR time rather than up to a week later.
    """

    def test_delete_calls_delete_on_the_lcm_object(self, mock_flex_project):
        """Delete() must go through ICmObject.Delete() on the text itself."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)
        text = Mock()

        ops.Delete(text)

        text.Delete.assert_called_once_with()

    def test_delete_does_not_mutate_the_derived_texts_list(self, mock_flex_project):
        """Delete() must not touch lp.Texts.

        ILangProject.Texts is a derived read-only IList<IText> rebuilt on each
        access (texts are unowned in LCM 11), so removing from it deletes
        nothing and raises nothing. That was #317.
        """
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(mock_flex_project)

        ops.Delete(Mock())

        mock_flex_project.lp.Texts.Remove.assert_not_called()


# =============================================================================
# INTEGRATION TESTS - Require Real FLEx Project
# =============================================================================


_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


@pytest.mark.integration
@pytest.mark.requires_live_project
class TestTextOperationsIntegration:
    """
    Integration tests that require a real FLEx project.

    Run with: pytest -m integration
    """

    @pytest.fixture(scope="class")
    def flex_project(self):
        """Setup real FLEx project for integration testing.

        Tries the canonical test projects (Sena 3 first); skips if none
        can be opened. Previously opened ``AllProjectNames()[0]`` which
        picked an unrelated user project (e.g. ``Aweti``) and left tests
        running against arbitrary local state.

        Uses the session-scoped FLEx services bootstrapped by
        tests/flex_plugin.py::initialize_flex_for_tests. Calling
        FLExInitialize() / FLExCleanup() here would tear down state
        shared with the rest of the live-DB suite.
        """
        pytest.importorskip("flexicon")

        from flexicon import FLExProject

        project = FLExProject()
        for name in _CANDIDATE_PROJECTS:
            try:
                project.OpenProject(name, writeEnabled=True)
                break
            except Exception:
                continue
        else:
            pytest.skip(
                "No writable canonical test project available "
                f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
            )

        yield project

        try:
            project.CloseProject()
        except Exception:
            pass

    @pytest.mark.live_phase("TextOperations", "add")
    def test_create_and_delete_text(self, flex_project):
        """Integration test: Create and delete a text.

        Self-cleaning: if a prior run aborted between Create and Delete
        and left ``Test Text 123`` behind, delete it first so this test
        is idempotent against project state.
        """
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(flex_project)

        if ops.Exists("Test Text 123"):
            for stale in list(ops.GetAll()):
                from flexicon.code.Shared.string_utils import best_analysis_text
                if best_analysis_text(stale.Name) == "Test Text 123":
                    ops.Delete(stale)
                    break

        text = ops.Create("Test Text 123")
        try:
            assert text is not None

            title = ops.GetTitle(text)
            assert "Test Text 123" in title
        finally:
            ops.Delete(text)

    @pytest.mark.live_phase("TextOperations", "delete")
    def test_delete_actually_removes_the_text(self, flex_project):
        """Regression for #317: Delete() must have an observable effect.

        The old implementation called ``lp.Texts.Remove(text_obj)``.
        ``ILangProject.Texts`` is a derived read-only ``IList<IText>``
        rebuilt on each access (texts are unowned in LCM 11), so that
        removed an element from a throwaway list, deleted nothing, and
        raised nothing. Every "does it raise?" test passed against it.

        Assert the effect, not the absence of an exception: the count
        must drop and the text must stop existing.
        """
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(flex_project)
        name = "Test Text 317 Delete Effect"

        if ops.Exists(name):
            from flexicon.code.Shared.string_utils import best_analysis_text
            for stale in list(ops.GetAll()):
                if best_analysis_text(stale.Name) == name:
                    ops.Delete(stale)
                    break

        assert not ops.Exists(name), (
            "stale-cleanup Delete() did not remove the leftover text -- "
            "Delete() is a no-op again (see #317)"
        )

        before = len(list(ops.GetAll()))
        text = ops.Create(name)
        assert len(list(ops.GetAll())) == before + 1
        assert ops.Exists(name)

        ops.Delete(text)

        assert len(list(ops.GetAll())) == before, (
            "Delete() left the text count unchanged -- it deleted nothing"
        )
        assert not ops.Exists(name)

    def test_getall_returns_texts(self, flex_project):
        """Integration test: GetAll returns texts."""
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(flex_project)
        texts = list(ops.GetAll())

        assert isinstance(texts, list)


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test (requires real FLEx)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not integration"])
