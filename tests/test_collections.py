#
# test_collections.py
#
# Unit tests for SmartCollection class
#
# Tests the smart collection functionality for managing multiple concrete
# types while providing unified interface, type-aware display, and filtering.
#
# Platform: Python.NET
#           FieldWorks Version 9+
#
# Copyright 2025
#

"""
Unit tests for SmartCollection base class.

This test suite validates that the SmartCollection class correctly:
- Initializes with items or empty
- Supports iteration (__iter__)
- Supports length (__len__)
- Displays type breakdown in __str__()
- Filters by type with by_type()
- Supports indexing and slicing
- Handles empty collections
- Works with mixed types
- Raises NotImplementedError for filter()
- Implements append(), extend(), and clear()
"""

import pytest
from unittest.mock import Mock, MagicMock
from collections.abc import Iterable
import sys
import os

# Add project root to path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
sys.path.insert(0, _project_root)

from flexicon.code.Shared.smart_collection import SmartCollection


# =============================================================================
# FIXTURES FOR MOCK WRAPPER OBJECTS
# =============================================================================


@pytest.fixture
def mock_wrapped_rule_regular():
    """
    Fixture: Mock wrapped phonological rule (PhRegularRule type).

    Simulates a wrapper object with class_type and ClassName properties.
    """
    item = Mock()
    item.class_type = "PhRegularRule"
    item.ClassName = "PhRegularRule"
    item.Name = "voicing_rule"
    item.Direction = "LTR"
    return item


@pytest.fixture
def mock_wrapped_rule_metathesis():
    """
    Fixture: Mock wrapped metathesis rule (PhMetathesisRule type).

    Simulates a wrapper object of a different concrete type.
    """
    item = Mock()
    item.class_type = "PhMetathesisRule"
    item.ClassName = "PhMetathesisRule"
    item.Name = "metathesis_rule"
    item.Direction = "LTR"
    return item


@pytest.fixture
def mock_wrapped_rule_reduplication():
    """
    Fixture: Mock wrapped reduplication rule (PhReduplicationRule type).

    Simulates a third concrete type.
    """
    item = Mock()
    item.class_type = "PhReduplicationRule"
    item.ClassName = "PhReduplicationRule"
    item.Name = "reduplication_rule"
    item.Direction = "RTL"
    return item


@pytest.fixture
def mock_wrapped_msa_stem():
    """Fixture: Mock wrapped MSA object (MoStemMsa type)."""
    item = Mock()
    item.class_type = "MoStemMsa"
    item.ClassName = "MoStemMsa"
    item.Id = "msa-stem-001"
    return item


@pytest.fixture
def mock_wrapped_msa_inflaf():
    """Fixture: Mock wrapped MSA object (MoInflAffMsa type)."""
    item = Mock()
    item.class_type = "MoInflAffMsa"
    item.ClassName = "MoInflAffMsa"
    item.Id = "msa-inflaf-001"
    return item


@pytest.fixture
def sample_mixed_collection(mock_wrapped_rule_regular, mock_wrapped_rule_metathesis, mock_wrapped_rule_reduplication):
    """
    Fixture: SmartCollection with mixed phonological rule types.

    Contains 7 regular rules, 3 metathesis rules, and 2 reduplication rules.
    """
    items = [mock_wrapped_rule_regular] * 7 + [mock_wrapped_rule_metathesis] * 3 + [mock_wrapped_rule_reduplication] * 2
    return SmartCollection(items)


# =============================================================================
# TESTS FOR INITIALIZATION
# =============================================================================


class TestSmartCollectionInit:
    """Test __init__() method."""

    def test_init_with_none_creates_empty(self):
        """Test __init__() with None creates empty collection."""
        collection = SmartCollection(None)
        assert len(collection) == 0
        assert collection._items == []

    def test_init_with_empty_list(self):
        """Test __init__() with empty list."""
        collection = SmartCollection([])
        assert len(collection) == 0

    def test_init_with_items(self, mock_wrapped_rule_regular):
        """Test __init__() stores items."""
        items = [mock_wrapped_rule_regular] * 3
        collection = SmartCollection(items)
        assert len(collection) == 3
        assert collection._items == items

    def test_init_converts_iterable_to_list(self, mock_wrapped_rule_regular):
        """Test __init__() converts iterable to internal list."""
        items = (item for item in [mock_wrapped_rule_regular] * 3)
        collection = SmartCollection(items)
        assert isinstance(collection._items, list)
        assert len(collection) == 3

    def test_init_preserves_item_order(self, mock_wrapped_rule_regular, mock_wrapped_rule_metathesis):
        """Test __init__() preserves order of items."""
        items = [mock_wrapped_rule_regular, mock_wrapped_rule_metathesis, mock_wrapped_rule_regular]
        collection = SmartCollection(items)
        assert collection._items[0] == mock_wrapped_rule_regular
        assert collection._items[1] == mock_wrapped_rule_metathesis
        assert collection._items[2] == mock_wrapped_rule_regular


# =============================================================================
# TESTS FOR __len__
# =============================================================================


class TestSmartCollectionLen:
    """Test __len__() method."""

    def test_len_empty_collection(self):
        """Test __len__() on empty collection."""
        collection = SmartCollection()
        assert len(collection) == 0

    def test_len_single_item(self, mock_wrapped_rule_regular):
        """Test __len__() with single item."""
        collection = SmartCollection([mock_wrapped_rule_regular])
        assert len(collection) == 1

    def test_len_multiple_items(self, sample_mixed_collection):
        """Test __len__() with multiple items."""
        assert len(sample_mixed_collection) == 12

    def test_len_after_append(self, mock_wrapped_rule_regular, mock_wrapped_rule_metathesis):
        """Test __len__() after appending items."""
        collection = SmartCollection([mock_wrapped_rule_regular])
        assert len(collection) == 1
        collection.append(mock_wrapped_rule_metathesis)
        assert len(collection) == 2

    def test_len_after_extend(self, mock_wrapped_rule_regular):
        """Test __len__() after extending collection."""
        collection = SmartCollection([mock_wrapped_rule_regular])
        collection.extend([mock_wrapped_rule_regular] * 3)
        assert len(collection) == 4

    def test_len_after_clear(self, sample_mixed_collection):
        """Test __len__() after clearing collection."""
        assert len(sample_mixed_collection) == 12
        sample_mixed_collection.clear()
        assert len(sample_mixed_collection) == 0


# =============================================================================
# TESTS FOR __iter__
# =============================================================================


class TestSmartCollectionIter:
    """Test __iter__() method and iteration behavior."""

    def test_iter_empty_collection(self):
        """Test iteration on empty collection."""
        collection = SmartCollection()
        items = list(collection)
        assert items == []

    def test_iter_yields_items_in_order(self, mock_wrapped_rule_regular, mock_wrapped_rule_metathesis):
        """Test iteration yields items in order."""
        items_input = [mock_wrapped_rule_regular, mock_wrapped_rule_metathesis, mock_wrapped_rule_regular]
        collection = SmartCollection(items_input)
        items_output = list(collection)
        assert items_output == items_input

    def test_iter_in_for_loop(self, sample_mixed_collection):
        """Test iteration in for loop."""
        count = 0
        for item in sample_mixed_collection:
            count += 1
        assert count == 12

    def test_iter_unpacking(
        self, mock_wrapped_rule_regular, mock_wrapped_rule_metathesis, mock_wrapped_rule_reduplication
    ):
        """Test unpacking items using iteration."""
        items = [mock_wrapped_rule_regular, mock_wrapped_rule_metathesis, mock_wrapped_rule_reduplication]
        collection = SmartCollection(items)
        first, second, third = collection
        assert first == mock_wrapped_rule_regular
        assert second == mock_wrapped_rule_metathesis
        assert third == mock_wrapped_rule_reduplication

    def test_iter_multiple_iterations(self, sample_mixed_collection):
        """Test that collection can be iterated multiple times."""
        count1 = sum(1 for _ in sample_mixed_collection)
        count2 = sum(1 for _ in sample_mixed_collection)
        assert count1 == count2 == 12

    def test_iter_is_iterable(self):
        """Test that SmartCollection is an Iterable."""
        collection = SmartCollection()
        assert isinstance(collection, Iterable)


# =============================================================================
# TESTS FOR __getitem__ (INDEXING AND SLICING)
# =============================================================================


class TestSmartCollectionGetItem:
    """Test __getitem__() method for indexing and slicing."""

    def test_getitem_first_item(self, mock_wrapped_rule_regular):
        """Test indexing to get first item."""
        items = [mock_wrapped_rule_regular] * 3
        collection = SmartCollection(items)
        assert collection[0] == mock_wrapped_rule_regular

    def test_getitem_middle_item(
        self, mock_wrapped_rule_regular, mock_wrapped_rule_metathesis, mock_wrapped_rule_reduplication
    ):
        """Test indexing to get item in middle."""
        items = [mock_wrapped_rule_regular, mock_wrapped_rule_metathesis, mock_wrapped_rule_reduplication]
        collection = SmartCollection(items)
        assert collection[1] == mock_wrapped_rule_metathesis

    def test_getitem_last_item(self, sample_mixed_collection):
        """Test indexing to get last item."""
        assert sample_mixed_collection[-1] == sample_mixed_collection._items[-1]

    def test_getitem_negative_index(self, sample_mixed_collection):
        """Test negative indexing."""
        assert sample_mixed_collection[-1] == sample_mixed_collection._items[-1]
        assert sample_mixed_collection[-2] == sample_mixed_collection._items[-2]

    def test_getitem_out_of_bounds_raises_indexerror(self, sample_mixed_collection):
        """Test that out-of-bounds index raises IndexError."""
        with pytest.raises(IndexError):
            _ = sample_mixed_collection[999]

    def test_getitem_slice_returns_new_collection(self, sample_mixed_collection):
        """Test that slicing returns a new SmartCollection."""
        sliced = sample_mixed_collection[0:3]
        assert isinstance(sliced, SmartCollection)
        assert len(sliced) == 3

    def test_getitem_slice_preserves_type(self, sample_mixed_collection):
        """Test that slice returns same collection type."""
        sliced = sample_mixed_collection[2:5]
        assert type(sliced) == SmartCollection

    def test_getitem_slice_empty(self, sample_mixed_collection):
        """Test slicing beyond collection bounds."""
        sliced = sample_mixed_collection[100:200]
        assert len(sliced) == 0

    def test_getitem_slice_step(self, sample_mixed_collection):
        """Test slicing with step."""
        sliced = sample_mixed_collection[::2]
        assert isinstance(sliced, SmartCollection)
        assert len(sliced) == 6

    def test_getitem_full_slice(self, sample_mixed_collection):
        """Test full slice [:] returns new collection."""
        sliced = sample_mixed_collection[:]
        assert isinstance(sliced, SmartCollection)
        assert len(sliced) == len(sample_mixed_collection)

    def test_getitem_single_item_not_wrapped(self, mock_wrapped_rule_regular):
        """Test that single item access returns item, not wrapped."""
        collection = SmartCollection([mock_wrapped_rule_regular])
        item = collection[0]
        assert item == mock_wrapped_rule_regular


# =============================================================================
# TESTS FOR __str__
# =============================================================================


class TestSmartCollectionStr:
    """Test __str__() method displays type breakdown."""

    def test_str_empty_collection(self):
        """Test __str__() on empty collection."""
        collection = SmartCollection()
        result = str(collection)
        assert "empty" in result.lower()

    def test_str_single_type(self, mock_wrapped_rule_regular):
        """Test __str__() with single type."""
        items = [mock_wrapped_rule_regular] * 5
        collection = SmartCollection(items)
        result = str(collection)

        assert "PhRegularRule" in result
        assert "5" in result

    def test_str_mixed_types(self, sample_mixed_collection):
        """Test __str__() shows breakdown of mixed types."""
        result = str(sample_mixed_collection)

        # Should show total count
        assert "12" in result or "total" in result.lower()
        # Should show each type
        assert "PhRegularRule" in result
        assert "PhMetathesisRule" in result
        assert "PhReduplicationRule" in result

    def test_str_shows_percentage(self, sample_mixed_collection):
        """Test __str__() includes percentage for each type."""
        result = str(sample_mixed_collection)
        # PhRegularRule is 7/12 = 58%
        assert "58%" in result

    def test_str_sorted_by_count(self, sample_mixed_collection):
        """Test __str__() sorts types by count (descending)."""
        result = str(sample_mixed_collection)
        lines = result.split("\n")

        # First type listed should be most common
        assert "PhRegularRule" in lines[1]

    def test_str_includes_collection_name(self):
        """Test __str__() includes collection class name."""
        collection = SmartCollection()
        result = str(collection)
        assert "SmartCollection" in result

    def test_str_format_is_readable(self, sample_mixed_collection):
        """Test __str__() format is human-readable."""
        result = str(sample_mixed_collection)
        # Should have multiple lines
        assert "\n" in result
        # Should use consistent formatting
        assert "(" in result and ")" in result


# =============================================================================
# TESTS FOR __repr__
# =============================================================================


class TestSmartCollectionRepr:
    """Test __repr__() method."""

    def test_repr_shows_item_count(self):
        """Test __repr__() shows number of items."""
        collection = SmartCollection()
        result = repr(collection)
        assert "0 items" in result

    def test_repr_with_items(self, mock_wrapped_rule_regular):
        """Test __repr__() with items."""
        items = [mock_wrapped_rule_regular] * 5
        collection = SmartCollection(items)
        result = repr(collection)
        assert "5 items" in result

    def test_repr_includes_class_name(self):
        """Test __repr__() includes class name."""
        collection = SmartCollection()
        result = repr(collection)
        assert "SmartCollection" in result

    def test_repr_format(self, sample_mixed_collection):
        """Test __repr__() format."""
        result = repr(sample_mixed_collection)
        assert result == "SmartCollection(12 items)"


# =============================================================================
# TESTS FOR BY_TYPE FILTERING
# =============================================================================


class TestSmartCollectionByType:
    """Test by_type() method for filtering by concrete type."""

    def test_by_type_filters_to_specific_type(self, sample_mixed_collection):
        """Test by_type() returns only items of specified type."""
        regular_only = sample_mixed_collection.by_type("PhRegularRule")
        assert len(regular_only) == 7
        # All items should be PhRegularRule
        for item in regular_only:
            assert item.class_type == "PhRegularRule"

    def test_by_type_returns_new_collection(self, sample_mixed_collection):
        """Test by_type() returns a new collection instance."""
        filtered = sample_mixed_collection.by_type("PhRegularRule")
        assert filtered is not sample_mixed_collection
        assert isinstance(filtered, SmartCollection)

    def test_by_type_doesnt_modify_original(self, sample_mixed_collection):
        """Test by_type() doesn't modify original collection."""
        original_len = len(sample_mixed_collection)
        _ = sample_mixed_collection.by_type("PhRegularRule")
        assert len(sample_mixed_collection) == original_len

    def test_by_type_different_types(self, sample_mixed_collection):
        """Test by_type() with different type filters."""
        metathesis = sample_mixed_collection.by_type("PhMetathesisRule")
        assert len(metathesis) == 3

        reduplication = sample_mixed_collection.by_type("PhReduplicationRule")
        assert len(reduplication) == 2

    def test_by_type_no_matches_returns_empty(self, sample_mixed_collection):
        """Test by_type() returns empty collection when no matches."""
        nonexistent = sample_mixed_collection.by_type("NonExistentType")
        assert len(nonexistent) == 0
        assert isinstance(nonexistent, SmartCollection)

    def test_by_type_with_classname_fallback(self, mock_wrapped_msa_stem):
        """Test by_type() works with items using ClassName fallback."""
        # Create items without class_type, only ClassName
        item = Mock()
        item.ClassName = "MoStemMsa"
        del item.class_type  # Remove class_type to test fallback
        collection = SmartCollection([item])

        filtered = collection.by_type("MoStemMsa")
        assert len(filtered) == 1

    def test_by_type_chaining(self, sample_mixed_collection):
        """Test that by_type() result can be used with other methods."""
        regular = sample_mixed_collection.by_type("PhRegularRule")
        # Should be iterable
        count = sum(1 for _ in regular)
        assert count == 7


# =============================================================================
# TESTS FOR FILTER METHOD
# =============================================================================


class TestSmartCollectionFilter:
    """Test filter() method raises NotImplementedError on base class."""

    def test_filter_raises_not_implemented(self):
        """Test filter() raises NotImplementedError on base class."""
        collection = SmartCollection()
        with pytest.raises(NotImplementedError) as exc_info:
            collection.filter()
        assert "does not implement filter" in str(exc_info.value)

    def test_filter_with_kwargs_raises_not_implemented(self, sample_mixed_collection):
        """Test filter() with keyword args raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            sample_mixed_collection.filter(name_contains="rule")

    def test_filter_error_message_includes_class_name(self):
        """Test filter() error message mentions class name."""
        collection = SmartCollection()
        with pytest.raises(NotImplementedError) as exc_info:
            collection.filter()
        assert "SmartCollection" in str(exc_info.value)

    def test_subclass_can_override_filter(self):
        """Test that subclasses can override filter()."""

        class TestCollection(SmartCollection):
            def filter(self, **criteria):
                return TestCollection([item for item in self._items])

        collection = TestCollection()
        # Should not raise NotImplementedError
        result = collection.filter()
        assert isinstance(result, TestCollection)


# =============================================================================
# TESTS FOR APPEND AND EXTEND
# =============================================================================


class TestSmartCollectionAppendExtend:
    """Test append() and extend() methods."""

    def test_append_single_item(self, mock_wrapped_rule_regular):
        """Test append() adds single item."""
        collection = SmartCollection()
        collection.append(mock_wrapped_rule_regular)
        assert len(collection) == 1
        assert collection[0] == mock_wrapped_rule_regular

    def test_append_multiple_items_sequentially(self, mock_wrapped_rule_regular, mock_wrapped_rule_metathesis):
        """Test multiple appends."""
        collection = SmartCollection()
        collection.append(mock_wrapped_rule_regular)
        collection.append(mock_wrapped_rule_metathesis)
        collection.append(mock_wrapped_rule_regular)
        assert len(collection) == 3

    def test_extend_with_list(self, mock_wrapped_rule_regular, mock_wrapped_rule_metathesis):
        """Test extend() adds multiple items."""
        collection = SmartCollection([mock_wrapped_rule_regular])
        new_items = [mock_wrapped_rule_metathesis] * 3
        collection.extend(new_items)
        assert len(collection) == 4

    def test_extend_with_empty_list(self, sample_mixed_collection):
        """Test extend() with empty list."""
        original_len = len(sample_mixed_collection)
        sample_mixed_collection.extend([])
        assert len(sample_mixed_collection) == original_len

    def test_extend_with_generator(self, mock_wrapped_rule_regular):
        """Test extend() with generator."""
        collection = SmartCollection()
        items = (mock_wrapped_rule_regular for _ in range(3))
        collection.extend(items)
        assert len(collection) == 3

    def test_append_after_extend(self, mock_wrapped_rule_regular, mock_wrapped_rule_metathesis):
        """Test append() after extend()."""
        collection = SmartCollection()
        collection.extend([mock_wrapped_rule_regular] * 3)
        collection.append(mock_wrapped_rule_metathesis)
        assert len(collection) == 4


# =============================================================================
# TESTS FOR CLEAR
# =============================================================================


class TestSmartCollectionClear:
    """Test clear() method."""

    def test_clear_empty_collection(self):
        """Test clear() on empty collection."""
        collection = SmartCollection()
        collection.clear()
        assert len(collection) == 0

    def test_clear_populated_collection(self, sample_mixed_collection):
        """Test clear() removes all items."""
        assert len(sample_mixed_collection) == 12
        sample_mixed_collection.clear()
        assert len(sample_mixed_collection) == 0

    def test_clear_then_append(self, sample_mixed_collection, mock_wrapped_rule_regular):
        """Test that append() works after clear()."""
        sample_mixed_collection.clear()
        sample_mixed_collection.append(mock_wrapped_rule_regular)
        assert len(sample_mixed_collection) == 1

    def test_clear_resets_iteration(self, sample_mixed_collection):
        """Test that clear() allows proper iteration."""
        sample_mixed_collection.clear()
        count = sum(1 for _ in sample_mixed_collection)
        assert count == 0


# =============================================================================
# TESTS FOR EDGE CASES
# =============================================================================


class TestSmartCollectionEdgeCases:
    """Test edge cases and special scenarios."""

    def test_collection_with_duplicate_items(self, mock_wrapped_rule_regular):
        """Test collection with same item repeated."""
        items = [mock_wrapped_rule_regular] * 10
        collection = SmartCollection(items)
        assert len(collection) == 10

    def test_collection_preserves_item_references(self, mock_wrapped_rule_regular):
        """Test that collection preserves item object references."""
        items = [mock_wrapped_rule_regular]
        collection = SmartCollection(items)
        assert collection[0] is mock_wrapped_rule_regular

    def test_collection_with_items_missing_class_type(self):
        """Test collection with items missing class_type property."""
        item = Mock(spec=["Name"])
        item.Name = "test"
        item.ClassName = "TestType"
        # Don't set class_type
        collection = SmartCollection([item])
        # Should still work, using ClassName fallback
        result = str(collection)
        assert "TestType" in result

    def test_large_collection(self, mock_wrapped_rule_regular):
        """Test collection with many items."""
        items = [mock_wrapped_rule_regular] * 1000
        collection = SmartCollection(items)
        assert len(collection) == 1000
        assert collection[500] == mock_wrapped_rule_regular

    def test_collection_with_msa_types(self, mock_wrapped_msa_stem, mock_wrapped_msa_inflaf):
        """Test collection with different domain types (MSAs)."""
        items = [mock_wrapped_msa_stem, mock_wrapped_msa_inflaf, mock_wrapped_msa_stem]
        collection = SmartCollection(items)

        assert len(collection) == 3
        stems = collection.by_type("MoStemMsa")
        assert len(stems) == 2
        inflaf = collection.by_type("MoInflAffMsa")
        assert len(inflaf) == 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestSmartCollectionIntegration:
    """Integration tests combining multiple operations."""

    def test_workflow_filter_then_iterate(self, sample_mixed_collection):
        """Test typical workflow: filter then iterate."""
        regular_rules = sample_mixed_collection.by_type("PhRegularRule")
        count = sum(1 for rule in regular_rules)
        assert count == 7

    def test_workflow_modify_and_refilter(self, sample_mixed_collection, mock_wrapped_rule_reduplication):
        """Test modifying collection and re-filtering."""
        initial_redup = len(sample_mixed_collection.by_type("PhReduplicationRule"))
        sample_mixed_collection.append(mock_wrapped_rule_reduplication)
        updated_redup = len(sample_mixed_collection.by_type("PhReduplicationRule"))
        assert updated_redup == initial_redup + 1

    def test_workflow_slice_then_filter(self, sample_mixed_collection):
        """Test slicing result then filtering."""
        subset = sample_mixed_collection[0:6]
        regular = subset.by_type("PhRegularRule")
        assert len(regular) <= 6

    def test_workflow_clear_and_rebuild(self, sample_mixed_collection, mock_wrapped_rule_regular):
        """Test clearing and rebuilding collection."""
        sample_mixed_collection.clear()
        assert len(sample_mixed_collection) == 0

        sample_mixed_collection.extend([mock_wrapped_rule_regular] * 5)
        assert len(sample_mixed_collection) == 5

        filtered = sample_mixed_collection.by_type("PhRegularRule")
        assert len(filtered) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
