"""
Tests for phonological context wrappers and smart collection.

This module tests the PhonologicalContext wrapper class and ContextCollection
smart collection, verifying that they transparently handle the multiple
concrete types of phonological contexts without exposing ClassName or casting.

Tests verify:
- ContextCollection creation and type breakdown display
- Filtering by name, type, and custom predicates
- Convenience filters (simple_contexts(), boundary_contexts(), etc.)
- Chaining filters
- Backward compatibility with existing code

Note: PhonologicalContext wrapper tests are limited here because they require
FLEx initialization (casting to concrete interfaces). Full tests should be
run in integration tests with a real FLEx project.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class MockPhonologicalContext:
    """Mock PhonologicalContext for testing ContextCollection."""

    def __init__(self, class_type, name="Test Context"):
        """
        Create a mock PhonologicalContext.

        Args:
            class_type: The ClassName (PhSimpleContextSeg, etc.)
            name: Context name
        """
        self.class_type = class_type
        self.ClassName = class_type
        self._name = name

    @property
    def context_name(self):
        return self._name

    @property
    def description(self):
        return f"Description of {self._name}"

    @property
    def is_simple_context_seg(self):
        return self.class_type == "PhSimpleContextSeg"

    @property
    def is_simple_context_nc(self):
        return self.class_type == "PhSimpleContextNC"

    @property
    def is_simple_context(self):
        return self.is_simple_context_seg or self.is_simple_context_nc

    @property
    def is_complex_context_seg(self):
        return self.class_type == "PhComplexContextSeg"

    @property
    def is_complex_context_nc(self):
        return self.class_type == "PhComplexContextNC"

    @property
    def is_complex_context(self):
        return self.is_complex_context_seg or self.is_complex_context_nc

    @property
    def is_boundary_context(self):
        return self.class_type == "PhBoundaryContext"

    @property
    def segment(self):
        if self.is_simple_context_seg:
            return Mock(Name="test_segment")
        return None

    @property
    def natural_class(self):
        if self.is_simple_context_nc:
            return Mock(Name="test_nc")
        return None

    @property
    def boundary_type(self):
        if self.is_boundary_context:
            return 0  # word boundary
        return -1

    def as_simple_context_seg(self):
        return Mock() if self.is_simple_context_seg else None

    def as_simple_context_nc(self):
        return Mock() if self.is_simple_context_nc else None

    def as_complex_context_seg(self):
        return Mock() if self.is_complex_context_seg else None

    def as_complex_context_nc(self):
        return Mock() if self.is_complex_context_nc else None

    def as_boundary_context(self):
        return Mock() if self.is_boundary_context else None

    @property
    def concrete(self):
        return Mock()


class TestContextCollection:
    """Tests for ContextCollection smart collection."""

    def test_collection_initialization_empty(self):
        """Test creating empty ContextCollection."""
        from flexicon.code.System.context_collection import ContextCollection

        collection = ContextCollection()
        assert len(collection) == 0

    def test_collection_initialization_with_items(self):
        """Test creating ContextCollection with items."""
        from flexicon.code.System.context_collection import ContextCollection

        context = MockPhonologicalContext("PhSimpleContextSeg")
        collection = ContextCollection([context])
        assert len(collection) == 1

    def test_collection_iteration(self):
        """Test iterating over ContextCollection."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [MockPhonologicalContext("PhSimpleContextSeg") for _ in range(3)]
        collection = ContextCollection(contexts)

        count = 0
        for context in collection:
            count += 1
        assert count == 3

    def test_collection_indexing(self):
        """Test indexing ContextCollection."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [MockPhonologicalContext("PhSimpleContextSeg") for _ in range(3)]
        collection = ContextCollection(contexts)

        assert collection[0] is contexts[0]
        assert collection[1] is contexts[1]

    def test_collection_slicing(self):
        """Test slicing ContextCollection."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [MockPhonologicalContext("PhSimpleContextSeg") for _ in range(5)]
        collection = ContextCollection(contexts)

        sliced = collection[1:3]
        assert isinstance(sliced, ContextCollection)
        assert len(sliced) == 2

    def test_collection_str_shows_type_breakdown(self):
        """Test that __str__ shows type breakdown."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhBoundaryContext"),
        ]
        collection = ContextCollection(contexts)

        str_repr = str(collection)
        assert "ContextCollection" in str_repr
        assert "3 total" in str_repr
        assert "PhSimpleContextSeg: 2" in str_repr
        assert "PhBoundaryContext: 1" in str_repr

    def test_collection_str_empty(self):
        """Test __str__ on empty collection."""
        from flexicon.code.System.context_collection import ContextCollection

        collection = ContextCollection()
        str_repr = str(collection)
        assert "empty" in str_repr

    def test_by_type_filter(self):
        """Test filtering by concrete type."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhBoundaryContext"),
            MockPhonologicalContext("PhSimpleContextSeg"),
        ]
        collection = ContextCollection(contexts)

        seg_only = collection.by_type("PhSimpleContextSeg")
        assert len(seg_only) == 2
        assert isinstance(seg_only, ContextCollection)

    def test_filter_where_custom_predicate(self):
        """Test filtering with custom predicate."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhBoundaryContext"),
        ]
        collection = ContextCollection(contexts)

        # Filter where class_type is PhSimpleContextSeg
        simple = collection.where(lambda c: c.is_simple_context)
        assert len(simple) == 2

    def test_simple_contexts_convenience_filter(self):
        """Test simple_contexts() convenience method."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhBoundaryContext"),
            MockPhonologicalContext("PhSimpleContextNC"),
        ]
        collection = ContextCollection(contexts)

        simple = collection.simple_contexts()
        assert len(simple) == 2
        for ctx in simple:
            assert ctx.is_simple_context

    def test_simple_context_seg_convenience_filter(self):
        """Test simple_context_seg() convenience method."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhSimpleContextNC"),
            MockPhonologicalContext("PhSimpleContextSeg"),
        ]
        collection = ContextCollection(contexts)

        seg_only = collection.simple_context_seg()
        assert len(seg_only) == 2
        for ctx in seg_only:
            assert ctx.is_simple_context_seg

    def test_simple_context_nc_convenience_filter(self):
        """Test simple_context_nc() convenience method."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhSimpleContextNC"),
            MockPhonologicalContext("PhSimpleContextNC"),
        ]
        collection = ContextCollection(contexts)

        nc_only = collection.simple_context_nc()
        assert len(nc_only) == 2
        for ctx in nc_only:
            assert ctx.is_simple_context_nc

    def test_complex_contexts_convenience_filter(self):
        """Test complex_contexts() convenience method."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhComplexContextSeg"),
            MockPhonologicalContext("PhBoundaryContext"),
            MockPhonologicalContext("PhComplexContextNC"),
        ]
        collection = ContextCollection(contexts)

        complex_only = collection.complex_contexts()
        assert len(complex_only) == 2
        for ctx in complex_only:
            assert ctx.is_complex_context

    def test_complex_context_seg_convenience_filter(self):
        """Test complex_context_seg() convenience method."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhComplexContextSeg"),
            MockPhonologicalContext("PhComplexContextNC"),
            MockPhonologicalContext("PhComplexContextSeg"),
        ]
        collection = ContextCollection(contexts)

        seg_only = collection.complex_context_seg()
        assert len(seg_only) == 2

    def test_complex_context_nc_convenience_filter(self):
        """Test complex_context_nc() convenience method."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhComplexContextSeg"),
            MockPhonologicalContext("PhComplexContextNC"),
            MockPhonologicalContext("PhComplexContextNC"),
        ]
        collection = ContextCollection(contexts)

        nc_only = collection.complex_context_nc()
        assert len(nc_only) == 2

    def test_boundary_contexts_convenience_filter(self):
        """Test boundary_contexts() convenience method."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhBoundaryContext"),
            MockPhonologicalContext("PhBoundaryContext"),
        ]
        collection = ContextCollection(contexts)

        boundary = collection.boundary_contexts()
        assert len(boundary) == 2
        for ctx in boundary:
            assert ctx.is_boundary_context

    def test_filter_chaining(self):
        """Test chaining multiple filters."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg", "word_initial"),
            MockPhonologicalContext("PhSimpleContextSeg", "word_final"),
            MockPhonologicalContext("PhBoundaryContext", "word_boundary"),
        ]
        collection = ContextCollection(contexts)

        # Chain: get simple contexts, then filter by name
        simple_word = collection.simple_contexts().filter(name_contains="word")
        assert len(simple_word) == 2
        assert simple_word[0].is_simple_context
        assert simple_word[0].context_name == "word_initial"

    def test_repr(self):
        """Test string representation of collection."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [MockPhonologicalContext("PhSimpleContextSeg") for _ in range(5)]
        collection = ContextCollection(contexts)

        repr_str = repr(collection)
        assert "ContextCollection" in repr_str
        assert "5" in repr_str

    def test_append(self):
        """Test appending to collection."""
        from flexicon.code.System.context_collection import ContextCollection

        collection = ContextCollection()
        context = MockPhonologicalContext("PhSimpleContextSeg")
        collection.append(context)

        assert len(collection) == 1
        assert collection[0] is context

    def test_extend(self):
        """Test extending collection."""
        from flexicon.code.System.context_collection import ContextCollection

        collection = ContextCollection()
        contexts = [MockPhonologicalContext("PhSimpleContextSeg") for _ in range(3)]
        collection.extend(contexts)

        assert len(collection) == 3

    def test_clear(self):
        """Test clearing collection."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [MockPhonologicalContext("PhSimpleContextSeg") for _ in range(3)]
        collection = ContextCollection(contexts)

        collection.clear()
        assert len(collection) == 0

    def test_filter_name_contains(self):
        """Test filtering by name contains."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg", "word_initial"),
            MockPhonologicalContext("PhSimpleContextSeg", "syllable_final"),
            MockPhonologicalContext("PhBoundaryContext", "word_boundary"),
        ]
        collection = ContextCollection(contexts)

        word_contexts = collection.filter(name_contains="word")
        assert len(word_contexts) == 2

    def test_filter_multiple_context_types(self):
        """Test filtering mixed context types."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg", "voiceless"),
            MockPhonologicalContext("PhSimpleContextNC", "obstruents"),
            MockPhonologicalContext("PhComplexContextSeg", "complex1"),
            MockPhonologicalContext("PhComplexContextNC", "complex2"),
            MockPhonologicalContext("PhBoundaryContext", "word_boundary"),
        ]
        collection = ContextCollection(contexts)

        assert len(collection) == 5
        assert len(collection.simple_contexts()) == 2
        assert len(collection.complex_contexts()) == 2
        assert len(collection.boundary_contexts()) == 1

    def test_filter_all_types_in_breakdown(self):
        """Test type breakdown display with all context types."""
        from flexicon.code.System.context_collection import ContextCollection

        contexts = [
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhSimpleContextSeg"),
            MockPhonologicalContext("PhSimpleContextNC"),
            MockPhonologicalContext("PhComplexContextSeg"),
            MockPhonologicalContext("PhComplexContextNC"),
            MockPhonologicalContext("PhBoundaryContext"),
        ]
        collection = ContextCollection(contexts)

        str_repr = str(collection)
        assert "PhSimpleContextSeg: 2" in str_repr
        assert "PhSimpleContextNC: 1" in str_repr
        assert "PhComplexContextSeg: 1" in str_repr
        assert "PhComplexContextNC: 1" in str_repr
        assert "PhBoundaryContext: 1" in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
