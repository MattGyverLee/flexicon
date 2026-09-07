#
#   test_prohibition_wrappers.py
#
#   Test Suite: AdhocProhibition wrapper and ProhibitionCollection
#               Ad hoc morphosyntactic prohibitions wrapper tests
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Comprehensive test suite for AdhocProhibition wrapper and ProhibitionCollection.

Tests cover:
- Wrapper initialization and property access
- Type detection (is_* properties)
- Type-specific casting
- Collection initialization and iteration
- Collection filtering by type
- Collection type breakdown display
- Backward compatibility
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock, PropertyMock, patch

# Try the real flexicon first (works when FieldWorks is installed). Only
# fall back to mocking SIL.* if that fails (CI / no-FW environment).
try:
    from flexicon.code.Grammar.adhoc_prohibition import AdhocProhibition
    from flexicon.code.Grammar.prohibition_collection import ProhibitionCollection
except Exception:
    sys.modules["SIL"] = MagicMock()
    sys.modules["SIL.LCModel"] = MagicMock()
    sys.modules["SIL.LCModel.Core"] = MagicMock()
    sys.modules["SIL.LCModel.Core.KernelInterfaces"] = MagicMock()
    sys.modules["SIL.LCModel.Core.Text"] = MagicMock()

    from flexicon.code.Grammar.adhoc_prohibition import AdhocProhibition
    from flexicon.code.Grammar.prohibition_collection import ProhibitionCollection


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_grammatical_prohibition():
    """Create a mock grammatical feature prohibition."""
    prohib = Mock()
    prohib.ClassName = "MoAdhocProhibGr"
    prohib.Guid = "12345678-1234-1234-1234-123456789012"
    prohib.Owner = Mock()
    prohib.FeatureRA = Mock()
    prohib.FeatureValueRA = Mock()
    prohib.ProhibitedFeatureValueRA = Mock()
    return prohib


@pytest.fixture
def mock_morpheme_prohibition():
    """Create a mock morpheme co-occurrence prohibition."""
    prohib = Mock()
    prohib.ClassName = "MoAdhocProhibMorph"
    prohib.Guid = "87654321-4321-4321-4321-210987654321"
    prohib.Owner = Mock()
    prohib.MorphemeRA = Mock()
    prohib.ProhibitedMorphemeRA = Mock()
    return prohib


@pytest.fixture
def mock_allomorph_prohibition():
    """Create a mock allomorph variant prohibition."""
    prohib = Mock()
    prohib.ClassName = "MoAdhocProhibAllomorph"
    prohib.Guid = "abcdefab-cdef-abcd-efab-cdefabcdefab"
    prohib.Owner = Mock()
    prohib.AllomorphRA = Mock()
    prohib.ProhibitedAllomorphRA = Mock()
    return prohib


@pytest.fixture
def mock_unknown_prohibition():
    """Create a mock prohibition with unknown type."""
    prohib = Mock()
    prohib.ClassName = "MoUnknownProhibition"
    prohib.Guid = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    prohib.Owner = Mock()
    return prohib


# ============================================================================
# AdhocProhibition Wrapper Tests
# ============================================================================


class TestAdhocProhibitionInitialization:
    """Test AdhocProhibition wrapper initialization."""

    def test_init_with_grammatical_prohibition(self, mock_grammatical_prohibition):
        """Test initialization with grammatical prohibition."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        assert wrapped is not None
        assert wrapped.class_type == "MoAdhocProhibGr"

    def test_init_with_morpheme_prohibition(self, mock_morpheme_prohibition):
        """Test initialization with morpheme prohibition."""
        wrapped = AdhocProhibition(mock_morpheme_prohibition)
        assert wrapped is not None
        assert wrapped.class_type == "MoAdhocProhibMorph"

    def test_init_with_allomorph_prohibition(self, mock_allomorph_prohibition):
        """Test initialization with allomorph prohibition."""
        wrapped = AdhocProhibition(mock_allomorph_prohibition)
        assert wrapped is not None
        assert wrapped.class_type == "MoAdhocProhibAllomorph"


class TestAdhocProhibitionGuid:
    """Test GUID property access."""

    def test_guid_grammatical(self, mock_grammatical_prohibition):
        """Test GUID retrieval from grammatical prohibition."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        guid = wrapped.guid
        assert guid == "12345678-1234-1234-1234-123456789012"

    def test_guid_morpheme(self, mock_morpheme_prohibition):
        """Test GUID retrieval from morpheme prohibition."""
        wrapped = AdhocProhibition(mock_morpheme_prohibition)
        guid = wrapped.guid
        assert guid == "87654321-4321-4321-4321-210987654321"

    def test_guid_allomorph(self, mock_allomorph_prohibition):
        """Test GUID retrieval from allomorph prohibition."""
        wrapped = AdhocProhibition(mock_allomorph_prohibition)
        guid = wrapped.guid
        assert guid == "abcdefab-cdef-abcd-efab-cdefabcdefab"


class TestAdhocProhibitionType:
    """Test prohibition_type property."""

    def test_type_grammatical(self, mock_grammatical_prohibition):
        """Test prohibition_type for grammatical prohibition."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        assert wrapped.prohibition_type == "Grammatical"

    def test_type_morpheme(self, mock_morpheme_prohibition):
        """Test prohibition_type for morpheme prohibition."""
        wrapped = AdhocProhibition(mock_morpheme_prohibition)
        assert wrapped.prohibition_type == "Morpheme"

    def test_type_allomorph(self, mock_allomorph_prohibition):
        """Test prohibition_type for allomorph prohibition."""
        wrapped = AdhocProhibition(mock_allomorph_prohibition)
        assert wrapped.prohibition_type == "Allomorph"

    def test_type_unknown(self, mock_unknown_prohibition):
        """Test prohibition_type for unknown prohibition type."""
        wrapped = AdhocProhibition(mock_unknown_prohibition)
        assert wrapped.prohibition_type == "Unknown"


class TestAdhocProhibitionCapabilities:
    """Test capability check properties."""

    def test_is_grammatical_grammatical(self, mock_grammatical_prohibition):
        """Test is_grammatical_prohibition on grammatical type."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        assert wrapped.is_grammatical_prohibition is True
        assert wrapped.is_morpheme_prohibition is False
        assert wrapped.is_allomorph_prohibition is False

    def test_is_morpheme_morpheme(self, mock_morpheme_prohibition):
        """Test is_morpheme_prohibition on morpheme type."""
        wrapped = AdhocProhibition(mock_morpheme_prohibition)
        assert wrapped.is_grammatical_prohibition is False
        assert wrapped.is_morpheme_prohibition is True
        assert wrapped.is_allomorph_prohibition is False

    def test_is_allomorph_allomorph(self, mock_allomorph_prohibition):
        """Test is_allomorph_prohibition on allomorph type."""
        wrapped = AdhocProhibition(mock_allomorph_prohibition)
        assert wrapped.is_grammatical_prohibition is False
        assert wrapped.is_morpheme_prohibition is False
        assert wrapped.is_allomorph_prohibition is True

    def test_is_unknown(self, mock_unknown_prohibition):
        """Test capability checks on unknown type."""
        wrapped = AdhocProhibition(mock_unknown_prohibition)
        assert wrapped.is_grammatical_prohibition is False
        assert wrapped.is_morpheme_prohibition is False
        assert wrapped.is_allomorph_prohibition is False


class TestAdhocProhibitionCasting:
    """Test type-safe casting methods."""

    def test_as_grammatical_when_grammatical(self, mock_grammatical_prohibition):
        """Test as_grammatical_prohibition when type matches."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        concrete = wrapped.as_grammatical_prohibition()
        assert concrete is not None

    def test_as_grammatical_when_morpheme(self, mock_morpheme_prohibition):
        """Test as_grammatical_prohibition when type doesn't match."""
        wrapped = AdhocProhibition(mock_morpheme_prohibition)
        concrete = wrapped.as_grammatical_prohibition()
        assert concrete is None

    def test_as_morpheme_when_morpheme(self, mock_morpheme_prohibition):
        """Test as_morpheme_prohibition when type matches."""
        wrapped = AdhocProhibition(mock_morpheme_prohibition)
        concrete = wrapped.as_morpheme_prohibition()
        assert concrete is not None

    def test_as_morpheme_when_allomorph(self, mock_allomorph_prohibition):
        """Test as_morpheme_prohibition when type doesn't match."""
        wrapped = AdhocProhibition(mock_allomorph_prohibition)
        concrete = wrapped.as_morpheme_prohibition()
        assert concrete is None

    def test_as_allomorph_when_allomorph(self, mock_allomorph_prohibition):
        """Test as_allomorph_prohibition when type matches."""
        wrapped = AdhocProhibition(mock_allomorph_prohibition)
        concrete = wrapped.as_allomorph_prohibition()
        assert concrete is not None

    def test_as_allomorph_when_grammatical(self, mock_grammatical_prohibition):
        """Test as_allomorph_prohibition when type doesn't match."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        concrete = wrapped.as_allomorph_prohibition()
        assert concrete is None


class TestAdhocProhibitionRepresentation:
    """Test string representation of wrapper."""

    def test_repr_grammatical(self, mock_grammatical_prohibition):
        """Test __repr__ for grammatical prohibition."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        repr_str = repr(wrapped)
        assert "AdhocProhibition" in repr_str
        assert "MoAdhocProhibGr" in repr_str

    def test_repr_morpheme(self, mock_morpheme_prohibition):
        """Test __repr__ for morpheme prohibition."""
        wrapped = AdhocProhibition(mock_morpheme_prohibition)
        repr_str = repr(wrapped)
        assert "AdhocProhibition" in repr_str
        assert "MoAdhocProhibMorph" in repr_str

    def test_str_grammatical(self, mock_grammatical_prohibition):
        """Test __str__ for grammatical prohibition."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        str_repr = str(wrapped)
        assert "Grammatical prohibition" in str_repr

    def test_str_morpheme(self, mock_morpheme_prohibition):
        """Test __str__ for morpheme prohibition."""
        wrapped = AdhocProhibition(mock_morpheme_prohibition)
        str_repr = str(wrapped)
        assert "Morpheme prohibition" in str_repr


# ============================================================================
# ProhibitionCollection Tests
# ============================================================================


class TestProhibitionCollectionInitialization:
    """Test ProhibitionCollection initialization."""

    def test_init_empty(self):
        """Test initialization with no items."""
        collection = ProhibitionCollection()
        assert len(collection) == 0

    def test_init_with_items(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test initialization with items."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)
        assert len(collection) == 2

    def test_init_with_none(self):
        """Test initialization with None."""
        collection = ProhibitionCollection(None)
        assert len(collection) == 0


class TestProhibitionCollectionIteration:
    """Test collection iteration."""

    def test_iteration(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test iterating over collection."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        items = list(collection)
        assert len(items) == 2
        assert items[0].is_grammatical_prohibition
        assert items[1].is_morpheme_prohibition

    def test_indexing(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test indexing into collection."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        assert collection[0].is_grammatical_prohibition
        assert collection[1].is_morpheme_prohibition

    def test_slicing(self, mock_grammatical_prohibition, mock_morpheme_prohibition, mock_allomorph_prohibition):
        """Test slicing collection."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
            AdhocProhibition(mock_allomorph_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        sliced = collection[0:2]
        assert len(sliced) == 2
        assert isinstance(sliced, ProhibitionCollection)

    def test_len(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test len() on collection."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)
        assert len(collection) == 2


class TestProhibitionCollectionFiltering:
    """Test collection filtering."""

    def test_filter_by_grammatical(
        self, mock_grammatical_prohibition, mock_morpheme_prohibition, mock_allomorph_prohibition
    ):
        """Test filtering by grammatical type."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
            AdhocProhibition(mock_allomorph_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.filter(prohibition_type="Grammatical")
        assert len(filtered) == 1
        assert filtered[0].is_grammatical_prohibition

    def test_filter_by_morpheme(
        self, mock_grammatical_prohibition, mock_morpheme_prohibition, mock_allomorph_prohibition
    ):
        """Test filtering by morpheme type."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
            AdhocProhibition(mock_allomorph_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.filter(prohibition_type="Morpheme")
        assert len(filtered) == 1
        assert filtered[0].is_morpheme_prohibition

    def test_filter_by_allomorph(
        self, mock_grammatical_prohibition, mock_morpheme_prohibition, mock_allomorph_prohibition
    ):
        """Test filtering by allomorph type."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
            AdhocProhibition(mock_allomorph_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.filter(prohibition_type="Allomorph")
        assert len(filtered) == 1
        assert filtered[0].is_allomorph_prohibition

    def test_filter_case_insensitive(self, mock_grammatical_prohibition):
        """Test that filter type is case-insensitive."""
        wrapped_items = [AdhocProhibition(mock_grammatical_prohibition)]
        collection = ProhibitionCollection(wrapped_items)

        # Test lowercase
        filtered = collection.filter(prohibition_type="grammatical")
        assert len(filtered) == 1

        # Test uppercase
        filtered = collection.filter(prohibition_type="GRAMMATICAL")
        assert len(filtered) == 1

    def test_filter_by_abbreviation_gr(self, mock_grammatical_prohibition):
        """Test filtering by 'Gr' abbreviation."""
        wrapped_items = [AdhocProhibition(mock_grammatical_prohibition)]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.filter(prohibition_type="Gr")
        assert len(filtered) == 1

    def test_filter_by_abbreviation_morph(self, mock_morpheme_prohibition):
        """Test filtering by 'Morph' abbreviation."""
        wrapped_items = [AdhocProhibition(mock_morpheme_prohibition)]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.filter(prohibition_type="Morph")
        assert len(filtered) == 1

    def test_filter_by_abbreviation_allo(self, mock_allomorph_prohibition):
        """Test filtering by 'Allo' abbreviation."""
        wrapped_items = [AdhocProhibition(mock_allomorph_prohibition)]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.filter(prohibition_type="Allo")
        assert len(filtered) == 1


class TestProhibitionCollectionConvenienceMethods:
    """Test type-specific convenience filter methods."""

    def test_grammatical_prohibitions(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test grammatical_prohibitions() method."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.grammatical_prohibitions()
        assert len(filtered) == 1
        assert filtered[0].is_grammatical_prohibition

    def test_morpheme_prohibitions(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test morpheme_prohibitions() method."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.morpheme_prohibitions()
        assert len(filtered) == 1
        assert filtered[0].is_morpheme_prohibition

    def test_allomorph_prohibitions(self, mock_morpheme_prohibition, mock_allomorph_prohibition):
        """Test allomorph_prohibitions() method."""
        wrapped_items = [
            AdhocProhibition(mock_morpheme_prohibition),
            AdhocProhibition(mock_allomorph_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.allomorph_prohibitions()
        assert len(filtered) == 1
        assert filtered[0].is_allomorph_prohibition


class TestProhibitionCollectionCustomFiltering:
    """Test where() custom filtering."""

    def test_where_basic(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test basic where() filtering."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.where(lambda p: p.is_grammatical_prohibition)
        assert len(filtered) == 1
        assert filtered[0].is_grammatical_prohibition

    def test_where_combining_conditions(
        self, mock_grammatical_prohibition, mock_morpheme_prohibition, mock_allomorph_prohibition
    ):
        """Test where() with multiple conditions."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
            AdhocProhibition(mock_allomorph_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        # Morpheme or Allomorph (not Grammatical)
        filtered = collection.where(lambda p: p.is_morpheme_prohibition or p.is_allomorph_prohibition)
        assert len(filtered) == 2

    def test_where_by_guid(self, mock_grammatical_prohibition):
        """Test where() checking GUID."""
        wrapped_items = [AdhocProhibition(mock_grammatical_prohibition)]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.where(lambda p: "1234" in p.guid)
        assert len(filtered) == 1


class TestProhibitionCollectionChaining:
    """Test chainable filtering."""

    def test_chain_type_and_where(
        self, mock_grammatical_prohibition, mock_morpheme_prohibition, mock_allomorph_prohibition
    ):
        """Test chaining filter() with where()."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
            AdhocProhibition(mock_allomorph_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        # Filter by type first, then custom filter
        filtered = collection.filter(prohibition_type="Morpheme").where(lambda p: "8765" in p.guid)
        assert len(filtered) == 1

    def test_chain_convenience_and_where(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test chaining convenience method with where()."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.morpheme_prohibitions().where(lambda p: "8765" in p.guid)
        assert len(filtered) == 1


class TestProhibitionCollectionRepresentation:
    """Test collection string representation."""

    def test_repr_empty(self):
        """Test __repr__ for empty collection."""
        collection = ProhibitionCollection()
        assert "ProhibitionCollection(0 items)" in repr(collection)

    def test_repr_with_items(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test __repr__ for collection with items."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        collection = ProhibitionCollection(wrapped_items)
        assert "ProhibitionCollection(2 items)" in repr(collection)


# ============================================================================
# Integration and Edge Cases
# ============================================================================


class TestProhibitionIntegration:
    """Integration tests for wrapper and collection."""

    def test_wrapper_accessed_from_collection(self, mock_grammatical_prohibition):
        """Test accessing wrapper properties from collection item."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        collection = ProhibitionCollection([wrapped])

        item = collection[0]
        assert item.is_grammatical_prohibition
        assert item.prohibition_type == "Grammatical"

    def test_collection_filter_returns_new_collection(self, mock_grammatical_prohibition, mock_morpheme_prohibition):
        """Test that filter returns new collection, not modifying original."""
        wrapped_items = [
            AdhocProhibition(mock_grammatical_prohibition),
            AdhocProhibition(mock_morpheme_prohibition),
        ]
        original = ProhibitionCollection(wrapped_items)
        filtered = original.filter(prohibition_type="Grammatical")

        assert len(original) == 2
        assert len(filtered) == 1

    def test_empty_filter_result(self, mock_grammatical_prohibition):
        """Test filter that returns no items."""
        wrapped_items = [AdhocProhibition(mock_grammatical_prohibition)]
        collection = ProhibitionCollection(wrapped_items)

        filtered = collection.filter(prohibition_type="Morpheme")
        assert len(filtered) == 0


# ============================================================================
# Backward Compatibility
# ============================================================================


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_wrapper_preserves_original_object(self, mock_grammatical_prohibition):
        """Test that wrapper stores original object."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        assert wrapped._obj is not None
        assert wrapped._obj.ClassName == "MoAdhocProhibGr"

    def test_collection_iteration_preserves_type(self, mock_grammatical_prohibition):
        """Test that iteration returns AdhocProhibition objects."""
        wrapped = AdhocProhibition(mock_grammatical_prohibition)
        collection = ProhibitionCollection([wrapped])

        for item in collection:
            assert isinstance(item, AdhocProhibition)
