"""
Test fixtures and utilities for flexicon operations testing.

Provides mock implementations and factories for testing without requiring
a full FieldWorks installation.

Author: Claude Code
Date: 2026-04-06
"""

import pytest
from unittest.mock import Mock, MagicMock, PropertyMock


class MockLcmCache:
    """Mock implementation of LcmCache for testing."""

    def __init__(self):
        self.ServiceLocator = Mock()
        self._objects = {}

    def GetObject(self, hvo):
        """Get object by HVO."""
        return self._objects.get(hvo, Mock())

    def CreateObject(self, class_name):
        """Create a mock object of the given class."""
        obj = Mock()
        obj.__class__.__name__ = class_name
        return obj


class MockFLExProject:
    """Mock implementation of FLExProject for unit testing."""

    def __init__(self):
        self.LcmCache = MockLcmCache()
        self.writeEnabled = True
        self.project = Mock()  # Raw FW project object
        self.project.LcmCache = self.LcmCache

        # Mock common FW properties
        self.project.UndoStack = Mock()
        self.project.MainCacheAccessor = Mock()

    def GetObject(self, hvo):
        """Get object by HVO."""
        return self.LcmCache.GetObject(hvo)

    def Object(self, obj):
        """Get or wrap an object."""
        return obj if obj else Mock()


@pytest.fixture
def mock_flex_project():
    """
    Provide a mock FLExProject for testing operations classes.

    This fixture allows operations classes to be instantiated and tested
    without requiring a full FieldWorks installation or GUI context.
    """
    return MockFLExProject()


@pytest.fixture
def mock_flex_project_with_objects():
    """
    Provide a mock FLExProject with pre-populated test objects.

    Useful for integration tests that need multiple objects in the cache.
    """
    project = MockFLExProject()

    # Add some test objects to the cache
    for i in range(10):
        obj = Mock()
        obj.Hvo = i
        project.LcmCache._objects[i] = obj

    return project


@pytest.fixture
def consolidation_test_data():
    """
    Provide test data for consolidated operations classes.

    Maps class names to their parent classes and expected domain methods.
    Used to verify inheritance and method preservation during consolidation.
    """
    return {
        'AgentOperations': {
            'parent': 'PossibilityItemOperations',
            'domain_methods': [
                'GetName', 'SetName', 'GetDescription', 'SetDescription',
                'GetGuid', 'CompareTo'
            ],
            'preserved_in': ['GetAll', 'Create', 'Delete', 'Duplicate', 'Find', 'Exists']
        },
        'OverlayOperations': {
            'parent': 'PossibilityItemOperations',
            'domain_methods': [
                'GetName', 'SetName', 'GetDescription', 'SetDescription',
                'GetGuid', 'CompareTo'
            ],
            'preserved_in': ['GetAll', 'Create', 'Delete', 'Duplicate', 'Find', 'Exists']
        },
        'TranslationTypeOperations': {
            'parent': 'PossibilityItemOperations',
            'domain_methods': [
                'GetName', 'SetName', 'GetDescription', 'SetDescription',
                'GetGuid', 'CompareTo'
            ],
            'preserved_in': ['GetAll', 'Create', 'Delete', 'Duplicate', 'Find', 'Exists']
        },
        'PublicationOperations': {
            'parent': 'PossibilityItemOperations',
            'domain_methods': [
                'GetPageLayout', 'SetPageLayout', 'GetIsDefault', 'SetIsDefault',
                'GetPageHeight', 'SetPageHeight', 'GetPageWidth', 'SetPageWidth',
                'GetDivisions', 'AddDivision', 'GetHeaderFooter', 'GetIsLandscape',
                'GetSubPublications', 'GetParent', 'GetDateCreated', 'GetDateModified'
            ],
            'preserved_in': ['GetAll', 'Create', 'Delete', 'Duplicate', 'Find', 'Exists']
        },
    }
