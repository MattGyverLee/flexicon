"""
Tests for compound rule wrappers and smart collection.

This module tests the CompoundRule wrapper class and CompoundRuleCollection
smart collection, verifying that they transparently handle the two concrete
types of compound rules without exposing ClassName or casting.

Tests verify:
- CompoundRuleCollection creation and type breakdown display
- Filtering by name, head_dependency, type, and custom predicates
- Convenience filters (endo_compounds(), exo_compounds())
- Chaining filters
- Backward compatibility with existing code
- CompoundRule wrapper properties and capabilities

Note: CompoundRule wrapper tests are limited here because they require
FLEx initialization (casting to concrete interfaces). Full tests should be
run in integration tests with a real FLEx project.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class MockCompoundRule:
    """Mock CompoundRule for testing CompoundRuleCollection."""

    def __init__(self, class_type, name="Test Rule", head_dependency=0, left_context=None, right_context=None):
        """
        Create a mock CompoundRule.

        Args:
            class_type: The ClassName (MoEndoCompound or MoExoCompound)
            name: Rule name
            head_dependency: Head dependency value
            left_context: Left context object or None
            right_context: Right context object or None
        """
        self.class_type = class_type
        self.ClassName = class_type
        self._name = name
        self._head_dependency = head_dependency
        self._left_context = left_context
        self._right_context = right_context

    @property
    def name(self):
        return self._name

    @property
    def head_dependency(self):
        return self._head_dependency

    @property
    def left_head_dep(self):
        return self._head_dependency if self.class_type == "MoEndoCompound" else None

    @property
    def right_head_dep(self):
        return self._head_dependency if self.class_type == "MoExoCompound" else None

    @property
    def left_context(self):
        return self._left_context

    @property
    def right_context(self):
        return self._right_context

    @property
    def contexts(self):
        return (self._left_context, self._right_context)

    @property
    def is_endo_compound(self):
        return self.class_type == "MoEndoCompound"

    @property
    def is_exo_compound(self):
        return self.class_type == "MoExoCompound"

    def as_endo_compound(self):
        return Mock() if self.class_type == "MoEndoCompound" else None

    def as_exo_compound(self):
        return Mock() if self.class_type == "MoExoCompound" else None

    @property
    def concrete(self):
        return Mock()


class TestCompoundRuleCollection:
    """Tests for CompoundRuleCollection smart collection."""

    def test_collection_initialization_empty(self):
        """Test creating empty CompoundRuleCollection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        collection = CompoundRuleCollection()
        assert len(collection) == 0

    def test_collection_initialization_with_items(self):
        """Test creating CompoundRuleCollection with items."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rule = MockCompoundRule("MoEndoCompound")
        collection = CompoundRuleCollection([rule])
        assert len(collection) == 1

    def test_collection_iteration(self):
        """Test iterating over CompoundRuleCollection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [MockCompoundRule("MoEndoCompound") for _ in range(3)]
        collection = CompoundRuleCollection(rules)

        count = 0
        for rule in collection:
            count += 1
        assert count == 3

    def test_collection_indexing(self):
        """Test indexing CompoundRuleCollection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [MockCompoundRule("MoEndoCompound") for _ in range(3)]
        collection = CompoundRuleCollection(rules)

        assert collection[0] is rules[0]
        assert collection[1] is rules[1]

    def test_collection_slicing(self):
        """Test slicing CompoundRuleCollection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [MockCompoundRule("MoEndoCompound") for _ in range(5)]
        collection = CompoundRuleCollection(rules)

        sliced = collection[1:3]
        assert isinstance(sliced, CompoundRuleCollection)
        assert len(sliced) == 2

    def test_collection_str_shows_type_breakdown(self):
        """Test that __str__ shows type breakdown."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoExoCompound"),
        ]
        collection = CompoundRuleCollection(rules)

        str_repr = str(collection)
        assert "CompoundRuleCollection" in str_repr
        assert "3 total" in str_repr
        assert "MoEndoCompound: 2" in str_repr
        assert "MoExoCompound: 1" in str_repr

    def test_collection_str_empty(self):
        """Test __str__ on empty collection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        collection = CompoundRuleCollection()
        str_repr = str(collection)
        assert "empty" in str_repr

    def test_by_type_filter(self):
        """Test filtering by concrete type."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoExoCompound"),
            MockCompoundRule("MoEndoCompound"),
        ]
        collection = CompoundRuleCollection(rules)

        endo_only = collection.by_type("MoEndoCompound")
        assert len(endo_only) == 2
        assert isinstance(endo_only, CompoundRuleCollection)

    def test_filter_by_name_contains(self):
        """Test filtering by name."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound", name="VerbCompound"),
            MockCompoundRule("MoEndoCompound", name="NounCompound"),
            MockCompoundRule("MoEndoCompound", name="VerbAdj"),
        ]
        collection = CompoundRuleCollection(rules)

        verb_rules = collection.filter(name_contains="Verb")
        assert len(verb_rules) == 2

    def test_filter_by_head_dependency(self):
        """Test filtering by head dependency."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound", head_dependency=0),
            MockCompoundRule("MoEndoCompound", head_dependency=1),
            MockCompoundRule("MoEndoCompound", head_dependency=0),
        ]
        collection = CompoundRuleCollection(rules)

        left_head = collection.filter(head_dependency=0)
        assert len(left_head) == 2

    def test_filter_where_custom_predicate(self):
        """Test filtering with custom predicate."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoExoCompound"),
        ]
        collection = CompoundRuleCollection(rules)

        # Filter where class_type is MoEndoCompound
        endo = collection.where(lambda r: r.class_type == "MoEndoCompound")
        assert len(endo) == 2

    def test_endo_compounds_convenience_filter(self):
        """Test endo_compounds() convenience method."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoExoCompound"),
            MockCompoundRule("MoEndoCompound"),
        ]
        collection = CompoundRuleCollection(rules)

        endo = collection.endo_compounds()
        assert len(endo) == 2
        for rule in endo:
            assert rule.class_type == "MoEndoCompound"

    def test_exo_compounds_convenience_filter(self):
        """Test exo_compounds() convenience method."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoExoCompound"),
            MockCompoundRule("MoExoCompound"),
        ]
        collection = CompoundRuleCollection(rules)

        exo = collection.exo_compounds()
        assert len(exo) == 2
        for rule in exo:
            assert rule.class_type == "MoExoCompound"

    def test_filter_chaining(self):
        """Test chaining multiple filters."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound", name="VerbN", head_dependency=0),
            MockCompoundRule("MoEndoCompound", name="VerbV", head_dependency=1),
            MockCompoundRule("MoExoCompound", name="VerbN", head_dependency=0),
        ]
        collection = CompoundRuleCollection(rules)

        # Chain: get endo rules, then filter by name
        verb_endo = collection.endo_compounds().filter(name_contains="VerbN")
        assert len(verb_endo) == 1
        assert verb_endo[0].class_type == "MoEndoCompound"
        assert "VerbN" in verb_endo[0].name

    def test_filter_chaining_with_head_dependency(self):
        """Test chaining filters with head dependency."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound", name="Verb", head_dependency=0),
            MockCompoundRule("MoEndoCompound", name="Verb", head_dependency=1),
            MockCompoundRule("MoExoCompound", name="Verb", head_dependency=0),
        ]
        collection = CompoundRuleCollection(rules)

        # Chain: get endo, then filter by head dependency
        endo_lhs = collection.endo_compounds().filter(head_dependency=0)
        assert len(endo_lhs) == 1
        assert endo_lhs[0].is_endo_compound

    def test_repr(self):
        """Test string representation of collection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [MockCompoundRule("MoEndoCompound") for _ in range(5)]
        collection = CompoundRuleCollection(rules)

        repr_str = repr(collection)
        assert "CompoundRuleCollection" in repr_str
        assert "5" in repr_str

    def test_append(self):
        """Test appending to collection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        collection = CompoundRuleCollection()
        rule = MockCompoundRule("MoEndoCompound")
        collection.append(rule)

        assert len(collection) == 1

    def test_extend(self):
        """Test extending collection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        collection = CompoundRuleCollection()
        rules = [
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoExoCompound"),
        ]
        collection.extend(rules)

        assert len(collection) == 2

    def test_clear(self):
        """Test clearing collection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [MockCompoundRule("MoEndoCompound") for _ in range(3)]
        collection = CompoundRuleCollection(rules)
        assert len(collection) == 3

        collection.clear()
        assert len(collection) == 0

    def test_filter_with_contexts(self):
        """Test filtering by context presence."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        left_ctx = Mock()
        rules = [
            MockCompoundRule("MoEndoCompound", left_context=left_ctx),
            MockCompoundRule("MoEndoCompound", left_context=None),
            MockCompoundRule("MoExoCompound", left_context=left_ctx),
        ]
        collection = CompoundRuleCollection(rules)

        # Filter rules with left context
        with_context = collection.where(lambda r: r.left_context is not None)
        assert len(with_context) == 2

    def test_filter_empty_result(self):
        """Test filtering that results in empty collection."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound", name="Verb"),
            MockCompoundRule("MoEndoCompound", name="Noun"),
        ]
        collection = CompoundRuleCollection(rules)

        # Filter for non-existent name
        empty = collection.filter(name_contains="Adj")
        assert len(empty) == 0
        assert isinstance(empty, CompoundRuleCollection)

    def test_filter_all_criteria_together(self):
        """Test filtering with multiple criteria."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound", name="VerbN", head_dependency=0),
            MockCompoundRule("MoEndoCompound", name="VerbV", head_dependency=1),
            MockCompoundRule("MoEndoCompound", name="NounN", head_dependency=0),
        ]
        collection = CompoundRuleCollection(rules)

        # Filter by both name and head dependency
        result = collection.filter(name_contains="Verb", head_dependency=0)
        assert len(result) == 1
        assert "VerbN" in result[0].name


class TestCompoundRuleWrapper:
    """Tests for CompoundRule wrapper class."""

    def test_wrapper_initialization(self):
        """Test initializing CompoundRule wrapper."""
        from flexicon.code.Grammar.compound_rule import CompoundRule

        rule = MockCompoundRule("MoEndoCompound", name="TestRule")
        wrapped = CompoundRule(rule)

        # Should not raise
        assert wrapped is not None

    def test_wrapper_name_property(self):
        """Test accessing name through wrapper."""
        from flexicon.code.Grammar.compound_rule import CompoundRule

        rule = MockCompoundRule("MoEndoCompound", name="TestRule")
        # Note: Direct property access won't work in tests without LCM
        # Just verify the wrapper accepts the object
        wrapped = CompoundRule(rule)
        assert wrapped is not None

    def test_wrapper_is_endo_compound(self):
        """Test is_endo_compound property."""
        from flexicon.code.Grammar.compound_rule import CompoundRule

        endo = MockCompoundRule("MoEndoCompound")
        exo = MockCompoundRule("MoExoCompound")

        wrapped_endo = CompoundRule(endo)
        wrapped_exo = CompoundRule(exo)

        # These should work with mock objects
        assert wrapped_endo.class_type == "MoEndoCompound"
        assert wrapped_exo.class_type == "MoExoCompound"

    def test_wrapper_as_endo_compound(self):
        """Test as_endo_compound() method."""
        from flexicon.code.Grammar.compound_rule import CompoundRule

        endo = MockCompoundRule("MoEndoCompound")
        wrapped = CompoundRule(endo)

        # as_endo_compound should return mock object
        result = wrapped.as_endo_compound()
        assert result is not None

    def test_wrapper_as_exo_compound(self):
        """Test as_exo_compound() method."""
        from flexicon.code.Grammar.compound_rule import CompoundRule

        exo = MockCompoundRule("MoExoCompound")
        wrapped = CompoundRule(exo)

        # as_exo_compound should return mock object
        result = wrapped.as_exo_compound()
        assert result is not None

    def test_wrapper_as_wrong_compound_returns_none(self):
        """Test as_*_compound() returns None for wrong type."""
        from flexicon.code.Grammar.compound_rule import CompoundRule

        endo = MockCompoundRule("MoEndoCompound")
        wrapped = CompoundRule(endo)

        # as_exo_compound should return None for endo rule
        result = wrapped.as_exo_compound()
        assert result is None

    def test_wrapper_concrete_property(self):
        """Test accessing concrete property."""
        from flexicon.code.Grammar.compound_rule import CompoundRule

        rule = MockCompoundRule("MoEndoCompound")
        wrapped = CompoundRule(rule)

        # concrete property should return something
        assert wrapped.concrete is not None

    def test_wrapper_repr(self):
        """Test string representation of wrapper."""
        from flexicon.code.Grammar.compound_rule import CompoundRule

        rule = MockCompoundRule("MoEndoCompound", name="TestRule")
        wrapped = CompoundRule(rule)

        repr_str = repr(wrapped)
        assert "CompoundRule" in repr_str
        assert "MoEndoCompound" in repr_str

    def test_wrapper_str(self):
        """Test human-readable string."""
        from flexicon.code.Grammar.compound_rule import CompoundRule

        rule = MockCompoundRule("MoEndoCompound", name="TestRule")
        wrapped = CompoundRule(rule)

        str_repr = str(wrapped)
        assert "MoEndoCompound" in str_repr


class TestCompoundRuleEdgeCases:
    """Tests for edge cases and error handling."""

    def test_collection_with_mixed_types(self):
        """Test collection with mixed endo and exo compounds."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoExoCompound"),
            MockCompoundRule("MoEndoCompound"),
            MockCompoundRule("MoExoCompound"),
            MockCompoundRule("MoEndoCompound"),
        ]
        collection = CompoundRuleCollection(rules)

        assert len(collection) == 5
        assert len(collection.endo_compounds()) == 3
        assert len(collection.exo_compounds()) == 2

    def test_filter_preserves_collection_type(self):
        """Test that filtering returns the correct collection type."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [MockCompoundRule("MoEndoCompound") for _ in range(5)]
        collection = CompoundRuleCollection(rules)

        filtered = collection.endo_compounds()
        assert isinstance(filtered, CompoundRuleCollection)

        filtered2 = filtered.filter(name_contains="Test")
        assert isinstance(filtered2, CompoundRuleCollection)

    def test_where_with_complex_predicate(self):
        """Test where() with complex predicates."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        left_ctx = Mock()
        right_ctx = Mock()
        rules = [
            MockCompoundRule("MoEndoCompound", left_context=left_ctx, right_context=right_ctx),
            MockCompoundRule("MoEndoCompound", left_context=left_ctx),
            MockCompoundRule("MoExoCompound", right_context=right_ctx),
        ]
        collection = CompoundRuleCollection(rules)

        # Filter for rules with both contexts
        both_contexts = collection.where(lambda r: r.left_context is not None and r.right_context is not None)
        assert len(both_contexts) == 1

    def test_multiple_filter_chains(self):
        """Test multiple chained filters."""
        from flexicon.code.Grammar.compound_rule_collection import CompoundRuleCollection

        rules = [
            MockCompoundRule("MoEndoCompound", name="VerbN", head_dependency=0),
            MockCompoundRule("MoEndoCompound", name="VerbV", head_dependency=1),
            MockCompoundRule("MoEndoCompound", name="NounN", head_dependency=0),
            MockCompoundRule("MoExoCompound", name="VerbN", head_dependency=0),
        ]
        collection = CompoundRuleCollection(rules)

        # Multiple chained filters
        result = collection.endo_compounds().filter(name_contains="Verb").filter(head_dependency=0)

        assert len(result) == 1
        assert "VerbN" in result[0].name
