"""
Tests for allomorph wrappers and smart collection.

This module tests the Allomorph wrapper class and AllomorphCollection
smart collection, verifying that they transparently handle the two
concrete types of allomorphs without exposing ClassName or casting.

Tests verify:
- AllomorphCollection creation and type breakdown display
- Filtering by form, environment, type, and custom predicates
- Convenience filters (stem_allomorphs(), affix_allomorphs())
- Chaining filters
- Backward compatibility with existing code

Note: Allomorph wrapper tests are limited here because they require
FLEx initialization (casting to concrete interfaces). Full tests should be
run in integration tests with a real FLEx project.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class MockAllomorph:
    """Mock Allomorph for testing AllomorphCollection."""

    def __init__(self, class_type, form="test", environment=None):
        """
        Create a mock Allomorph.

        Args:
            class_type: The ClassName (MoStemAllomorph or MoAffixAllomorph)
            form: Allomorph form string
            environment: List of mock environment objects
        """
        self.class_type = class_type
        self.ClassName = class_type
        self._form = form
        self._environment = environment or []

    @property
    def form(self):
        return self._form

    @property
    def environment(self):
        return self._environment

    @property
    def is_stem_allomorph(self):
        return self.class_type == "MoStemAllomorph"

    @property
    def is_affix_allomorph(self):
        return self.class_type == "MoAffixAllomorph"

    @property
    def stem_name(self):
        return "test_stem" if self.is_stem_allomorph else ""

    @property
    def affix_type(self):
        return Mock() if self.is_affix_allomorph else None

    def as_stem_allomorph(self):
        return Mock() if self.class_type == "MoStemAllomorph" else None

    def as_affix_allomorph(self):
        return Mock() if self.class_type == "MoAffixAllomorph" else None

    @property
    def concrete(self):
        return Mock()


class MockEnvironment:
    """Mock phonological environment."""

    def __init__(self, guid):
        self.Guid = guid


class TestAllomorphCollection:
    """Tests for AllomorphCollection smart collection."""

    def test_collection_initialization_empty(self):
        """Test creating empty AllomorphCollection."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        collection = AllomorphCollection()
        assert len(collection) == 0

    def test_collection_initialization_with_items(self):
        """Test creating AllomorphCollection with items."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorph = MockAllomorph("MoStemAllomorph")
        collection = AllomorphCollection([allomorph])
        assert len(collection) == 1

    def test_collection_iteration(self):
        """Test iterating over AllomorphCollection."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [MockAllomorph("MoStemAllomorph") for _ in range(3)]
        collection = AllomorphCollection(allomorphs)

        count = 0
        for allomorph in collection:
            count += 1
        assert count == 3

    def test_collection_indexing(self):
        """Test indexing AllomorphCollection."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [MockAllomorph("MoStemAllomorph") for _ in range(3)]
        collection = AllomorphCollection(allomorphs)

        assert collection[0] is allomorphs[0]
        assert collection[1] is allomorphs[1]

    def test_collection_slicing(self):
        """Test slicing AllomorphCollection."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [MockAllomorph("MoStemAllomorph") for _ in range(5)]
        collection = AllomorphCollection(allomorphs)

        sliced = collection[1:3]
        assert isinstance(sliced, AllomorphCollection)
        assert len(sliced) == 2

    def test_collection_str_shows_type_breakdown(self):
        """Test that __str__ shows type breakdown."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph"),
            MockAllomorph("MoStemAllomorph"),
            MockAllomorph("MoAffixAllomorph"),
        ]
        collection = AllomorphCollection(allomorphs)

        str_repr = str(collection)
        assert "AllomorphCollection" in str_repr
        assert "3 total" in str_repr
        assert "MoStemAllomorph: 2" in str_repr
        assert "MoAffixAllomorph: 1" in str_repr

    def test_collection_str_empty(self):
        """Test __str__ on empty collection."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        collection = AllomorphCollection()
        str_repr = str(collection)
        assert "empty" in str_repr

    def test_by_type_filter(self):
        """Test filtering by concrete type."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph"),
            MockAllomorph("MoAffixAllomorph"),
            MockAllomorph("MoStemAllomorph"),
        ]
        collection = AllomorphCollection(allomorphs)

        stem_only = collection.by_type("MoStemAllomorph")
        assert len(stem_only) == 2
        assert isinstance(stem_only, AllomorphCollection)

    def test_filter_form_contains(self):
        """Test filtering by form contains."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph", form="walk"),
            MockAllomorph("MoStemAllomorph", form="walking"),
            MockAllomorph("MoAffixAllomorph", form="-ing"),
        ]
        collection = AllomorphCollection(allomorphs)

        ing_allomorphs = collection.filter(form_contains="ing")
        assert len(ing_allomorphs) == 2

    def test_filter_where_custom_predicate(self):
        """Test filtering with custom predicate."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph"),
            MockAllomorph("MoStemAllomorph"),
            MockAllomorph("MoAffixAllomorph"),
        ]
        collection = AllomorphCollection(allomorphs)

        # Filter where class_type is MoStemAllomorph
        stems = collection.where(lambda a: a.class_type == "MoStemAllomorph")
        assert len(stems) == 2

    def test_stem_allomorphs_convenience_filter(self):
        """Test stem_allomorphs() convenience method."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph"),
            MockAllomorph("MoAffixAllomorph"),
            MockAllomorph("MoStemAllomorph"),
        ]
        collection = AllomorphCollection(allomorphs)

        stems = collection.stem_allomorphs()
        assert len(stems) == 2
        for allomorph in stems:
            assert allomorph.class_type == "MoStemAllomorph"

    def test_affix_allomorphs_convenience_filter(self):
        """Test affix_allomorphs() convenience method."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph"),
            MockAllomorph("MoAffixAllomorph"),
            MockAllomorph("MoAffixAllomorph"),
        ]
        collection = AllomorphCollection(allomorphs)

        affixes = collection.affix_allomorphs()
        assert len(affixes) == 2
        for allomorph in affixes:
            assert allomorph.class_type == "MoAffixAllomorph"

    def test_filter_chaining(self):
        """Test chaining multiple filters."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph", form="walk"),
            MockAllomorph("MoStemAllomorph", form="running"),
            MockAllomorph("MoAffixAllomorph", form="-ing"),
        ]
        collection = AllomorphCollection(allomorphs)

        # Chain: get stem allomorphs, then filter by form
        stem_ing = collection.stem_allomorphs().filter(form_contains="ing")
        assert len(stem_ing) == 1
        assert stem_ing[0].class_type == "MoStemAllomorph"
        assert "ing" in stem_ing[0].form

    def test_repr(self):
        """Test string representation of collection."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [MockAllomorph("MoStemAllomorph") for _ in range(5)]
        collection = AllomorphCollection(allomorphs)

        repr_str = repr(collection)
        assert "AllomorphCollection" in repr_str
        assert "5" in repr_str

    def test_append(self):
        """Test appending to collection."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        collection = AllomorphCollection()
        allomorph = MockAllomorph("MoStemAllomorph")
        collection.append(allomorph)

        assert len(collection) == 1
        assert collection[0] is allomorph

    def test_extend(self):
        """Test extending collection."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        collection = AllomorphCollection()
        allomorphs = [MockAllomorph("MoStemAllomorph") for _ in range(3)]
        collection.extend(allomorphs)

        assert len(collection) == 3

    def test_clear(self):
        """Test clearing collection."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [MockAllomorph("MoStemAllomorph") for _ in range(3)]
        collection = AllomorphCollection(allomorphs)

        collection.clear()
        assert len(collection) == 0

    def test_filter_environment(self):
        """Test filtering by environment."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        env1 = MockEnvironment("guid-1")
        env2 = MockEnvironment("guid-2")

        allomorphs = [
            MockAllomorph("MoStemAllomorph", form="walk", environment=[env1]),
            MockAllomorph("MoStemAllomorph", form="ran", environment=[env2]),
            MockAllomorph("MoAffixAllomorph", form="-ing", environment=[env1]),
        ]
        collection = AllomorphCollection(allomorphs)

        # Filter by env1
        env1_allomorphs = collection.filter(environment=env1)
        assert len(env1_allomorphs) == 2

    def test_filter_multiple_criteria(self):
        """Test filtering with multiple criteria."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph", form="walking"),
            MockAllomorph("MoStemAllomorph", form="ran"),
            MockAllomorph("MoAffixAllomorph", form="-ing"),
        ]
        collection = AllomorphCollection(allomorphs)

        # Filter: form contains 'ing' AND type is stem
        ing_stems = collection.stem_allomorphs().filter(form_contains="ing")
        assert len(ing_stems) == 1
        assert ing_stems[0].form == "walking"

    def test_collection_with_mixed_types(self):
        """Test collection with mixed allomorph types."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph", form="walk"),
            MockAllomorph("MoStemAllomorph", form="ran"),
            MockAllomorph("MoStemAllomorph", form="walked"),
            MockAllomorph("MoAffixAllomorph", form="-ing"),
            MockAllomorph("MoAffixAllomorph", form="-ed"),
        ]
        collection = AllomorphCollection(allomorphs)

        # Check mixed collection display
        str_repr = str(collection)
        assert "5 total" in str_repr
        assert "MoStemAllomorph: 3" in str_repr
        assert "MoAffixAllomorph: 2" in str_repr

    def test_filter_returns_new_collection(self):
        """Test that filter returns new collection without modifying original."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph", form="walk"),
            MockAllomorph("MoAffixAllomorph", form="-ing"),
        ]
        original = AllomorphCollection(allomorphs)
        original_len = len(original)

        # Filter
        ing_only = original.filter(form_contains="ing")

        # Check original is unchanged
        assert len(original) == original_len
        assert len(ing_only) == 1
        assert ing_only[0].form == "-ing"

    def test_where_with_complex_predicate(self):
        """Test where() with complex predicates."""
        from flexicon.code.Lexicon.allomorph_collection import AllomorphCollection

        allomorphs = [
            MockAllomorph("MoStemAllomorph", form="walk"),  # length 4
            MockAllomorph("MoStemAllomorph", form="ran"),  # length 3
            MockAllomorph("MoAffixAllomorph", form="-ing"),  # length 4
            MockAllomorph("MoAffixAllomorph", form="-ed"),  # length 3
        ]
        collection = AllomorphCollection(allomorphs)

        # Complex predicate: long forms (length > 3)
        # Should match: 'walk' (4) and '-ing' (4)
        long_forms = collection.where(lambda a: len(a.form) > 3)
        assert len(long_forms) == 2

        # Complex predicate: stems without environment
        stems_no_env = collection.where(lambda a: a.is_stem_allomorph and len(a.environment) == 0)
        assert len(stems_no_env) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
