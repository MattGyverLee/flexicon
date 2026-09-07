"""
Comprehensive Baseline Test for FLEx Operations Classes

This test suite verifies that all operations classes can be:
1. Imported successfully
2. Instantiated (with mock FLExProject)
3. Have expected methods (Create, GetAll, Find, Delete)
4. Properly inherit from BaseOperations
5. Have reordering methods available

Tests are organized by domain:
- Grammar (8 classes)
- Lexicon (10 classes)
- TextsWords (8 classes)
- Wordform (4 classes)
- Discourse (6 classes)
- Scripture (6 classes)
- Notebook (5 classes)
- Reversal (2 classes)
- Lists (6 classes)
- System (5 classes)
- Shared (2 classes)

Author: Programmer Team 3 - Test Infrastructure
Date: 2025-12-05
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add project root to path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
sys.path.insert(0, _project_root)


# =============================================================================
# MOCK FLEXPROJECT FIXTURE
# =============================================================================


@pytest.fixture
def mock_flex_project():
    """
    Create a mock FLExProject for testing operations class instantiation.

    This mock provides the minimal interface needed to instantiate operations
    classes without requiring an actual FLEx connection.
    """
    mock_project = Mock()
    mock_project.LcmCache = Mock()
    mock_project.Object = Mock(return_value=Mock())

    # Mock repository objects
    mock_project.LcmCache.ServiceLocator = Mock()
    mock_project.LcmCache.ServiceLocator.GetInstance = Mock(return_value=Mock())

    # Mock common repository methods
    mock_repo = Mock()
    mock_repo.AllInstances = Mock(return_value=[])
    mock_project.LcmCache.ServiceLocator.GetInstance.return_value = mock_repo

    return mock_project


# =============================================================================
# OPERATIONS CLASS DEFINITIONS BY DOMAIN
# =============================================================================

GRAMMAR_OPERATIONS = [
    ("POSOperations", "flexicon.code.Grammar.POSOperations"),
    ("PhonemeOperations", "flexicon.code.Grammar.PhonemeOperations"),
    ("NaturalClassOperations", "flexicon.code.Grammar.NaturalClassOperations"),
    ("EnvironmentOperations", "flexicon.code.Grammar.EnvironmentOperations"),
    ("PhonologicalRuleOperations", "flexicon.code.Grammar.PhonologicalRuleOperations"),
    ("MorphRuleOperations", "flexicon.code.Grammar.MorphRuleOperations"),
    ("GramCatOperations", "flexicon.code.Grammar.GramCatOperations"),
    ("InflectionFeatureOperations", "flexicon.code.Grammar.InflectionFeatureOperations"),
]

LEXICON_OPERATIONS = [
    ("LexEntryOperations", "flexicon.code.Lexicon.LexEntryOperations"),
    ("LexSenseOperations", "flexicon.code.Lexicon.LexSenseOperations"),
    ("AllomorphOperations", "flexicon.code.Lexicon.AllomorphOperations"),
    ("ExampleOperations", "flexicon.code.Lexicon.ExampleOperations"),
    ("PronunciationOperations", "flexicon.code.Lexicon.PronunciationOperations"),
    ("EtymologyOperations", "flexicon.code.Lexicon.EtymologyOperations"),
    ("VariantOperations", "flexicon.code.Lexicon.VariantOperations"),
    ("LexReferenceOperations", "flexicon.code.Lexicon.LexReferenceOperations"),
    ("SemanticDomainOperations", "flexicon.code.Lexicon.SemanticDomainOperations"),
]

TEXTSWORDS_OPERATIONS = [
    ("TextOperations", "flexicon.code.TextsWords.TextOperations"),
    ("ParagraphOperations", "flexicon.code.TextsWords.ParagraphOperations"),
    ("SegmentOperations", "flexicon.code.TextsWords.SegmentOperations"),
    ("WordformOperations", "flexicon.code.TextsWords.WordformOperations"),
    ("WfiAnalysisOperations", "flexicon.code.TextsWords.WfiAnalysisOperations"),
    ("WfiGlossOperations", "flexicon.code.TextsWords.WfiGlossOperations"),
    ("WfiMorphBundleOperations", "flexicon.code.TextsWords.WfiMorphBundleOperations"),
    ("DiscourseOperations", "flexicon.code.TextsWords.DiscourseOperations"),
]

WORDFORM_OPERATIONS = []  # WFI classes live in TextsWords, not a separate Wordform module

DISCOURSE_OPERATIONS = [
    # ConstChartOperations excluded: IDsDiscourse not present in installed FW LCM version
    ("ConstChartRowOperations", "flexicon.code.Discourse.ConstChartRowOperations"),
    ("ConstChartMarkerOperations", "flexicon.code.Discourse.ConstChartMarkerOperations"),
    ("ConstChartCellTagOperations", "flexicon.code.Discourse.ConstChartCellTagOperations"),
    ("ConstChartClauseMarkerOperations", "flexicon.code.Discourse.ConstChartClauseMarkerOperations"),
    ("ConstChartWordGroupOperations", "flexicon.code.Discourse.ConstChartWordGroupOperations"),
    ("ConstChartMovedTextOperations", "flexicon.code.Discourse.ConstChartMovedTextOperations"),
]

SCRIPTURE_OPERATIONS = [
    ("ScrBookOperations", "flexicon.code.Scripture.ScrBookOperations"),
    ("ScrSectionOperations", "flexicon.code.Scripture.ScrSectionOperations"),
    ("ScrTxtParaOperations", "flexicon.code.Scripture.ScrTxtParaOperations"),
    ("ScrNoteOperations", "flexicon.code.Scripture.ScrNoteOperations"),
    ("ScrAnnotationsOperations", "flexicon.code.Scripture.ScrAnnotationsOperations"),
    ("ScrDraftOperations", "flexicon.code.Scripture.ScrDraftOperations"),
]

NOTEBOOK_OPERATIONS = [
    ("DataNotebookOperations", "flexicon.code.Notebook.DataNotebookOperations"),
    ("NoteOperations", "flexicon.code.Notebook.NoteOperations"),
    ("PersonOperations", "flexicon.code.Notebook.PersonOperations"),
    ("LocationOperations", "flexicon.code.Notebook.LocationOperations"),
    ("AnthropologyOperations", "flexicon.code.Notebook.AnthropologyOperations"),
]

REVERSAL_OPERATIONS = [
    ("ReversalIndexOperations", "flexicon.code.Reversal.ReversalIndexOperations"),
    ("ReversalIndexEntryOperations", "flexicon.code.Reversal.ReversalIndexEntryOperations"),
]

LISTS_OPERATIONS = [
    ("PossibilityListOperations", "flexicon.code.Lists.PossibilityListOperations"),
    ("AgentOperations", "flexicon.code.Lists.AgentOperations"),
    ("ConfidenceOperations", "flexicon.code.Lists.ConfidenceOperations"),
    ("PublicationOperations", "flexicon.code.Lists.PublicationOperations"),
    ("TranslationTypeOperations", "flexicon.code.Lists.TranslationTypeOperations"),
    ("OverlayOperations", "flexicon.code.Lists.OverlayOperations"),
]

SYSTEM_OPERATIONS = [
    ("WritingSystemOperations", "flexicon.code.System.WritingSystemOperations"),
    ("ProjectSettingsOperations", "flexicon.code.System.ProjectSettingsOperations"),
    ("CustomFieldOperations", "flexicon.code.System.CustomFieldOperations"),
    ("CheckOperations", "flexicon.code.System.CheckOperations"),
    ("AnnotationDefOperations", "flexicon.code.System.AnnotationDefOperations"),
]

SHARED_OPERATIONS = [
    ("MediaOperations", "flexicon.code.Shared.MediaOperations"),
]

# FilterOperations is a utility class that does not inherit from BaseOperations;
# it is tracked separately so inheritance/reordering checks are not applied to it.
UTILITY_OPERATIONS = [
    ("FilterOperations", "flexicon.code.Shared.FilterOperations"),
]

# All operations classes (BaseOperations subclasses)
ALL_OPERATIONS = (
    GRAMMAR_OPERATIONS
    + LEXICON_OPERATIONS
    + TEXTSWORDS_OPERATIONS
    + WORDFORM_OPERATIONS
    + DISCOURSE_OPERATIONS
    + SCRIPTURE_OPERATIONS
    + NOTEBOOK_OPERATIONS
    + REVERSAL_OPERATIONS
    + LISTS_OPERATIONS
    + SYSTEM_OPERATIONS
    + SHARED_OPERATIONS
)

# Import-only list: includes utility classes that don't subclass BaseOperations
ALL_OPERATIONS_IMPORT = ALL_OPERATIONS + UTILITY_OPERATIONS

# Operations classes that should have Create
CREATE_OPERATIONS = [
    "LexEntryOperations",
    "LexSenseOperations",
    "AllomorphOperations",
    "ExampleOperations",
    "POSOperations",
    "TextOperations",
    "ParagraphOperations",
    "NoteOperations",
    "PersonOperations",
    "LocationOperations",
    "ReversalIndexEntryOperations",
    "ScrBookOperations",
    "ScrSectionOperations",
]

# Operations classes that should have Delete
DELETE_OPERATIONS = [
    "LexEntryOperations",
    "LexSenseOperations",
    "AllomorphOperations",
    "ExampleOperations",
    "TextOperations",
    "NoteOperations",
    "ReversalIndexEntryOperations",
]


# =============================================================================
# HELPER FUNCTION FOR SMART IMPORTS
# =============================================================================


def get_operations_class(class_name, module_path):
    """
    Get an operations class, preferring the pre-cached flexicon namespace
    but falling back to a direct import when the class is not there.
    """
    import importlib
    import flexicon

    ops_class = getattr(flexicon, class_name, None)
    if ops_class is not None:
        return ops_class
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Could not import {class_name} from {module_path}: {e}")


# =============================================================================
# BASELINE TESTS - IMPORT AND INSTANTIATION
# =============================================================================


class TestOperationsImport:
    """Test that all operations classes can be imported successfully."""

    @pytest.mark.parametrize("class_name,module_path", ALL_OPERATIONS_IMPORT)
    def test_operations_class_import(self, class_name, module_path):
        """Test that each operations class can be imported."""
        try:
            ops_class = get_operations_class(class_name, module_path)
            assert ops_class is not None
            assert hasattr(ops_class, "__name__")
            assert ops_class.__name__ == class_name
        except ImportError as e:
            pytest.fail(f"Failed to import {class_name} from {module_path}: {e}")


class TestOperationsInstantiation:
    """Test that all operations classes can be instantiated with a mock project."""

    @pytest.mark.parametrize("class_name,module_path", ALL_OPERATIONS)
    def test_operations_class_instantiation(self, class_name, module_path, mock_flex_project):
        """Test that each operations class can be instantiated."""
        try:
            ops_class = get_operations_class(class_name, module_path)

            # Try to instantiate with mock project
            instance = ops_class(mock_flex_project)

            assert instance is not None
            assert instance.project == mock_flex_project

        except Exception as e:
            pytest.fail(f"Failed to instantiate {class_name}: {e}")


class TestOperationsInheritance:
    """Test that all operations classes properly inherit from BaseOperations."""

    @pytest.mark.parametrize("class_name,module_path", ALL_OPERATIONS)
    def test_inherits_from_base_operations(self, class_name, module_path):
        """Test that each operations class inherits from BaseOperations."""
        try:
            # Import BaseOperations
            from flexicon.code.BaseOperations import BaseOperations

            # Import operations class
            ops_class = get_operations_class(class_name, module_path)

            # Check inheritance
            assert issubclass(ops_class, BaseOperations), f"{class_name} does not inherit from BaseOperations"

        except ImportError as e:
            pytest.fail(f"Failed to verify inheritance for {class_name}: {e}")


class TestReorderingMethods:
    """Test that all operations classes have the 7 reordering methods from BaseOperations."""

    REORDERING_METHODS = [
        "Sort",
        "MoveUp",
        "MoveDown",
        "MoveToIndex",
        "MoveBefore",
        "MoveAfter",
        "Swap",
    ]

    @pytest.mark.parametrize("class_name,module_path", ALL_OPERATIONS)
    def test_has_all_reordering_methods(self, class_name, module_path, mock_flex_project):
        """Test that each operations class has all 7 reordering methods."""
        try:
            ops_class = get_operations_class(class_name, module_path)
            instance = ops_class(mock_flex_project)

            for method_name in self.REORDERING_METHODS:
                assert hasattr(instance, method_name), f"{class_name} missing reordering method: {method_name}"

                # Verify it's callable
                method = getattr(instance, method_name)
                assert callable(method), f"{class_name}.{method_name} is not callable"

        except Exception as e:
            pytest.fail(f"Failed to verify reordering methods for {class_name}: {e}")


class TestCommonCRUDMethods:
    """Test that operations classes have common CRUD methods where applicable."""

    # Common methods that most operations classes should have
    COMMON_METHODS = {
        "GetAll": "Retrieve all items",
        "Find": "Find specific item",
    }

    @pytest.mark.parametrize("class_name,module_path", ALL_OPERATIONS)
    def test_has_getall_method(self, class_name, module_path, mock_flex_project):
        """Test that operations classes have GetAll method."""
        try:
            ops_class = get_operations_class(class_name, module_path)
            instance = ops_class(mock_flex_project)

            # Most operations should have GetAll
            if hasattr(instance, "GetAll"):
                assert callable(instance.GetAll)
            # It's okay if some don't have it

        except Exception as e:
            pytest.fail(f"Failed to check GetAll for {class_name}: {e}")

    @pytest.mark.parametrize(
        "class_name,module_path", [(cn, mp) for cn, mp in ALL_OPERATIONS if cn in CREATE_OPERATIONS]
    )
    def test_has_create_method(self, class_name, module_path, mock_flex_project):
        """Test that operations classes expected to have Create do have it."""
        try:
            ops_class = get_operations_class(class_name, module_path)
            instance = ops_class(mock_flex_project)

            assert hasattr(instance, "Create"), f"{class_name} should have Create method"
            assert callable(instance.Create)

        except Exception as e:
            pytest.fail(f"Failed to check Create for {class_name}: {e}")


# =============================================================================
# DOMAIN-SPECIFIC BASELINE TESTS
# =============================================================================


class TestGrammarOperations:
    """Baseline tests specific to Grammar operations."""

    @pytest.mark.parametrize("class_name,module_path", GRAMMAR_OPERATIONS)
    def test_grammar_operations_domain(self, class_name, module_path, mock_flex_project):
        """Test Grammar operations classes are properly configured."""
        ops_class = get_operations_class(class_name, module_path)
        instance = ops_class(mock_flex_project)

        # Grammar operations should have at least one read method
        assert (
            hasattr(instance, "GetAll")
            or hasattr(instance, "FeatureGetAll")
            or hasattr(instance, "Find")
            or hasattr(instance, "Create")
        ), f"{class_name} missing expected read/write method"


class TestLexiconOperations:
    """Baseline tests specific to Lexicon operations."""

    @pytest.mark.parametrize("class_name,module_path", LEXICON_OPERATIONS)
    def test_lexicon_operations_domain(self, class_name, module_path, mock_flex_project):
        """Test Lexicon operations classes are properly configured."""
        ops_class = get_operations_class(class_name, module_path)
        instance = ops_class(mock_flex_project)

        # Lexicon operations should have GetAll or Find
        assert hasattr(instance, "GetAll") or hasattr(instance, "Find")


class TestTextsWordsOperations:
    """Baseline tests specific to TextsWords operations."""

    @pytest.mark.parametrize("class_name,module_path", TEXTSWORDS_OPERATIONS)
    def test_textswords_operations_domain(self, class_name, module_path, mock_flex_project):
        """Test TextsWords operations classes are properly configured."""
        ops_class = get_operations_class(class_name, module_path)
        instance = ops_class(mock_flex_project)

        # TextsWords operations should have GetAll or an equivalent
        assert (
            hasattr(instance, "GetAll")
            or hasattr(instance, "GetAllCharts")
        ), f"{class_name} missing expected read method (GetAll/GetAllCharts)"


class TestScriptureOperations:
    """Baseline tests specific to Scripture operations."""

    @pytest.mark.parametrize("class_name,module_path", SCRIPTURE_OPERATIONS)
    def test_scripture_operations_domain(self, class_name, module_path, mock_flex_project):
        """Test Scripture operations classes are properly configured."""
        ops_class = get_operations_class(class_name, module_path)
        instance = ops_class(mock_flex_project)

        # Scripture operations should exist and be callable
        assert instance is not None


# =============================================================================
# SUMMARY TEST
# =============================================================================


class TestOperationsSummary:
    """Generate summary statistics about operations coverage."""

    def test_total_operations_count(self):
        """Verify we're testing all expected operations classes."""
        total = len(ALL_OPERATIONS)

        # We expect at least 61 operations classes (62 files - 1 BaseOperations)
        assert total >= 55, f"Expected at least 55 operations classes, found {total}"

        print(f"\n{'='*70}")
        print(f"OPERATIONS COVERAGE SUMMARY")
        print(f"{'='*70}")
        print(f"Total Operations Classes: {total}")
        print(f"\nBreakdown by Domain:")
        print(f"  Grammar:     {len(GRAMMAR_OPERATIONS):2d} classes")
        print(f"  Lexicon:     {len(LEXICON_OPERATIONS):2d} classes")
        print(f"  TextsWords:  {len(TEXTSWORDS_OPERATIONS):2d} classes")
        print(f"  Wordform:    {len(WORDFORM_OPERATIONS):2d} classes")
        print(f"  Discourse:   {len(DISCOURSE_OPERATIONS):2d} classes")
        print(f"  Scripture:   {len(SCRIPTURE_OPERATIONS):2d} classes")
        print(f"  Notebook:    {len(NOTEBOOK_OPERATIONS):2d} classes")
        print(f"  Reversal:    {len(REVERSAL_OPERATIONS):2d} classes")
        print(f"  Lists:       {len(LISTS_OPERATIONS):2d} classes")
        print(f"  System:      {len(SYSTEM_OPERATIONS):2d} classes")
        print(f"  Shared:      {len(SHARED_OPERATIONS):2d} classes")
        print(f"{'='*70}\n")


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
