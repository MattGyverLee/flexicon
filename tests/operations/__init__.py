"""
Shared Test Fixtures and Utilities for Operations Tests

This module provides:
- Mock FLExProject factories for testing without real FLEx connection
- Shared test fixtures for common operations testing patterns
- Mock LCM object builders
- Common assertions and validators
- Test data generators

Author: Programmer Team 3 - Test Infrastructure
Date: 2025-12-05
"""

import pytest
from unittest.mock import Mock, MagicMock, PropertyMock
import sys
import os


# =============================================================================
# MOCK LCM OBJECTS
# =============================================================================


class MockLCMObject:
    """
    Mock base LCM object with common properties.

    Provides standard properties found on all LCM objects:
    - Hvo (Handle Value Object - integer ID)
    - Guid (Global Unique Identifier)
    - Owner (parent object)
    - OwningFlid (field ID of owning property)
    """

    def __init__(self, hvo=1, guid=None, owner=None):
        self.Hvo = hvo
        self.Guid = guid if guid else self._generate_guid()
        self.Owner = owner
        self.OwningFlid = 0

    @staticmethod
    def _generate_guid():
        """Generate a mock GUID."""
        import uuid

        return uuid.uuid4()


class MockMultiString:
    """
    Mock IMultiString object for multilingual text fields.

    Simulates FLEx MultiString which stores text in multiple writing systems.
    """

    def __init__(self, text_dict=None):
        """
        Initialize mock MultiString.

        Args:
            text_dict: Dictionary mapping writing system codes to text strings.
                      Example: {'en': 'hello', 'fr': 'bonjour'}
        """
        self._texts = text_dict if text_dict else {}

    def get_String(self, ws_hvo):
        """Get text for a writing system HVO."""
        return Mock(Text=self._texts.get(ws_hvo, ""))

    def set_String(self, ws_hvo, text):
        """Set text for a writing system HVO."""
        self._texts[ws_hvo] = text


class MockOwningSequence:
    """
    Mock ILcmOwningSequence for testing reordering operations.

    Simulates FLEx owning sequences (e.g., entry.SensesOS).
    """

    def __init__(self, items=None):
        """
        Initialize mock owning sequence.

        Args:
            items: List of items in the sequence
        """
        self._items = list(items) if items else []

    @property
    def Count(self):
        """Get count of items in sequence."""
        return len(self._items)

    def __getitem__(self, index):
        """Get item at index."""
        return self._items[index]

    def __iter__(self):
        """Iterate over items."""
        return iter(self._items)

    def MoveTo(self, start_index, end_index, dest_sequence, dest_index):
        """
        Mock MoveTo operation.

        Simulates FLEx's MoveTo method for reordering.
        """
        # Remove item from current position
        item = self._items.pop(start_index)
        # Insert at new position
        # Adjust index if moving forward
        if dest_index > start_index:
            dest_index -= 1
        self._items.insert(dest_index, item)

    def Append(self, item):
        """Add item to end of sequence."""
        self._items.append(item)

    def Remove(self, item):
        """Remove item from sequence."""
        self._items.remove(item)


# =============================================================================
# MOCK FLEXPROJECT FACTORY
# =============================================================================


@pytest.fixture
def mock_flex_project():
    """
    Create a comprehensive mock FLExProject for testing.

    This fixture provides a mock project that can be used to instantiate
    and test operations classes without requiring a real FLEx connection.

    Returns:
        Mock: A configured mock FLExProject with common properties and methods
    """
    # Create base mock project
    mock_project = Mock()

    # Mock LcmCache
    mock_cache = Mock()
    mock_project.LcmCache = mock_cache

    # Mock ServiceLocator
    mock_service_locator = Mock()
    mock_cache.ServiceLocator = mock_service_locator

    # Mock repositories
    mock_repository = Mock()
    mock_repository.AllInstances = Mock(return_value=[])
    mock_repository.Count = 0
    mock_service_locator.GetInstance = Mock(return_value=mock_repository)

    # Mock Object() method for HVO resolution
    def mock_object(hvo):
        """Mock Object() method that returns a mock LCM object."""
        return MockLCMObject(hvo=hvo)

    mock_project.Object = Mock(side_effect=mock_object)

    # Mock writing systems
    mock_ws = Mock()
    mock_ws.DefaultVernacularWritingSystem = Mock()
    mock_ws.DefaultVernacularWritingSystem.Handle = 1
    mock_ws.DefaultAnalysisWritingSystem = Mock()
    mock_ws.DefaultAnalysisWritingSystem.Handle = 2
    mock_cache.WritingSystemFactory = mock_ws

    # Mock language project
    mock_lang_project = Mock()
    mock_cache.LanguageProject = mock_lang_project

    # Pin the transaction mode to Phase 1 (undoable=False).
    #
    # This MUST be an explicit False. `_undoable` is read by
    # _NestingAwareTransaction.__enter__ via
    # `getattr(project, "_undoable", False)`, and on a bare Mock that getattr
    # returns an auto-created *child Mock*, which is truthy. A mock project
    # would therefore select Phase 2 and try to construct a real
    # `UndoableUnitOfWorkHelper` from a Mock action handler, failing with
    # "TypeError: No method matches given arguments for
    # UndoableUnitOfWorkHelper..ctor".
    #
    # That is not a production defect -- it is only reachable because a Mock
    # answers every attribute truthily. Phase 1 is also the honest mode for
    # this fixture: there is no real LcmCache behind it, so there is no undo
    # stack for Phase 2 to drive. Any test that wants to exercise Phase 2
    # should set `_undoable = True` itself and patch
    # `flexicon.code.transaction.UndoableUnitOfWorkHelper` with a double, as
    # tests/test_b1t_action_handler_double.py does.
    mock_project._undoable = False

    # Phase 1 delegates to `project.Transaction(label)` and uses the result as
    # a context manager. A plain Mock does NOT support `__enter__`/`__exit__`
    # (magic methods raise AttributeError on Mock), so hand back a MagicMock,
    # which does.
    mock_project.Transaction = Mock(return_value=MagicMock())

    return mock_project


@pytest.fixture
def mock_lex_entry():
    """
    Create a mock ILexEntry for testing.

    Returns:
        Mock: A mock lexical entry with common properties
    """
    entry = MockLCMObject(hvo=1000)

    # Add lexical entry specific properties
    entry.SensesOS = MockOwningSequence()
    entry.AlternateFormsOS = MockOwningSequence()
    entry.LexemeFormOA = None
    entry.CitationForm = MockMultiString()

    return entry


@pytest.fixture
def mock_lex_sense():
    """
    Create a mock ILexSense for testing.

    Returns:
        Mock: A mock lexical sense with common properties
    """
    sense = MockLCMObject(hvo=2000)

    # Add sense-specific properties
    sense.Gloss = MockMultiString()
    sense.Definition = MockMultiString()
    sense.ExamplesOS = MockOwningSequence()
    sense.PartOfSpeech = None

    return sense


@pytest.fixture
def mock_pos():
    """
    Create a mock IPartOfSpeech for testing.

    Returns:
        Mock: A mock part of speech with common properties
    """
    pos = MockLCMObject(hvo=3000)

    # Add POS-specific properties
    pos.Name = MockMultiString({"en": "Noun"})
    pos.Abbreviation = MockMultiString({"en": "N"})
    pos.SubPossibilitiesOS = MockOwningSequence()

    return pos


@pytest.fixture
def mock_text():
    """
    Create a mock IText for testing.

    Returns:
        Mock: A mock text with common properties
    """
    text = MockLCMObject(hvo=4000)

    # Add text-specific properties
    text.Name = MockMultiString()
    text.ContentsOA = None
    text.ParagraphsOS = MockOwningSequence()

    return text


@pytest.fixture
def mock_wordform():
    """
    Create a mock IWfiWordform for testing.

    Returns:
        Mock: A mock wordform with common properties
    """
    wordform = MockLCMObject(hvo=5000)

    # Add wordform-specific properties
    wordform.Form = MockMultiString()
    wordform.AnalysesOC = MockOwningSequence()

    return wordform


# =============================================================================
# COMMON TEST ASSERTIONS
# =============================================================================


def assert_has_reordering_methods(ops_instance):
    """
    Assert that an operations instance has all 7 reordering methods.

    Args:
        ops_instance: Instance of an operations class

    Raises:
        AssertionError: If any reordering method is missing
    """
    reordering_methods = ["Sort", "MoveUp", "MoveDown", "MoveToIndex", "MoveBefore", "MoveAfter", "Swap"]

    for method_name in reordering_methods:
        assert hasattr(ops_instance, method_name), f"Operations class missing reordering method: {method_name}"
        assert callable(getattr(ops_instance, method_name)), f"Reordering method {method_name} is not callable"


def assert_has_crud_methods(ops_instance, has_create=True, has_delete=True):
    """
    Assert that an operations instance has expected CRUD methods.

    Args:
        ops_instance: Instance of an operations class
        has_create: Whether to check for Create method
        has_delete: Whether to check for Delete method

    Raises:
        AssertionError: If expected methods are missing
    """
    # GetAll should be present on most operations
    if hasattr(ops_instance, "GetAll"):
        assert callable(ops_instance.GetAll)

    # Find should be present on most operations
    if hasattr(ops_instance, "Find"):
        assert callable(ops_instance.Find)

    if has_create:
        assert hasattr(ops_instance, "Create"), "Operations class should have Create method"
        assert callable(ops_instance.Create)

    if has_delete:
        assert hasattr(ops_instance, "Delete"), "Operations class should have Delete method"
        assert callable(ops_instance.Delete)


def assert_inherits_base_operations(ops_class):
    """
    Assert that an operations class inherits from BaseOperations.

    Args:
        ops_class: The operations class (not instance)

    Raises:
        AssertionError: If class doesn't inherit from BaseOperations
    """
    from flexlibs2.code.BaseOperations import BaseOperations

    assert issubclass(ops_class, BaseOperations), f"{ops_class.__name__} does not inherit from BaseOperations"


# =============================================================================
# TEST DATA GENERATORS
# =============================================================================


def generate_test_entries(count=5):
    """
    Generate a list of mock lexical entries for testing.

    Args:
        count: Number of entries to generate

    Returns:
        list: List of mock ILexEntry objects
    """
    entries = []
    for i in range(count):
        entry = MockLCMObject(hvo=1000 + i)
        entry.SensesOS = MockOwningSequence()
        entry.AlternateFormsOS = MockOwningSequence()
        entry.LexemeFormOA = None
        entry.CitationForm = MockMultiString({"en": f"entry{i}"})
        entries.append(entry)
    return entries


def generate_test_senses(entry, count=3):
    """
    Generate and attach mock senses to an entry.

    Args:
        entry: Mock lexical entry
        count: Number of senses to generate

    Returns:
        list: List of mock ILexSense objects
    """
    senses = []
    for i in range(count):
        sense = MockLCMObject(hvo=2000 + i, owner=entry)
        sense.Gloss = MockMultiString({"en": f"meaning{i}"})
        sense.Definition = MockMultiString({"en": f"definition{i}"})
        sense.ExamplesOS = MockOwningSequence()
        entry.SensesOS.Append(sense)
        senses.append(sense)
    return senses


# =============================================================================
# MODULE-LEVEL UTILITIES
# =============================================================================


def skip_without_flex():
    """
    Decorator to skip tests that require a real FLEx connection.

    Use this for integration tests that can't run with mocks.
    """
    try:
        from flexlibs2 import FLExInitialize

        return lambda func: func
    except ImportError:
        return pytest.mark.skip(reason="FLEx not available")


def requires_flex_project(project_name="Sena 3"):
    """
    Decorator to skip tests that require a specific FLEx project.

    Args:
        project_name: Name of required project

    Returns:
        Decorator function
    """

    def decorator(func):
        try:
            from flexlibs2 import FLExProject, AllProjectNames

            if project_name not in AllProjectNames():
                return pytest.mark.skip(reason=f"FLEx project '{project_name}' not available")(func)
            return func
        except ImportError:
            return pytest.mark.skip(reason="FLEx not available")(func)

    return decorator


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Mock classes
    "MockLCMObject",
    "MockMultiString",
    "MockOwningSequence",
    # Fixtures
    "mock_flex_project",
    "mock_lex_entry",
    "mock_lex_sense",
    "mock_pos",
    "mock_text",
    "mock_wordform",
    # Assertions
    "assert_has_reordering_methods",
    "assert_has_crud_methods",
    "assert_inherits_base_operations",
    # Data generators
    "generate_test_entries",
    "generate_test_senses",
    # Decorators
    "skip_without_flex",
    "requires_flex_project",
]
