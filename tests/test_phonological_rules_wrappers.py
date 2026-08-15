"""
Tests for phonological rule wrappers and smart collection.

This module tests the PhonologicalRule wrapper class and RuleCollection
smart collection, verifying that they transparently handle the three
concrete types of phonological rules without exposing ClassName or casting.

Tests verify:
- RuleCollection creation and type breakdown display
- Filtering by name, direction, type, and custom predicates
- Convenience filters (regular_rules(), metathesis_rules(), redup_rules())
- Chaining filters
- Backward compatibility with existing code

Note: PhonologicalRule wrapper tests are limited here because they require
FLEx initialization (casting to concrete interfaces). Full tests should be
run in integration tests with a real FLEx project.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class MockPhonologicalRule:
    """Mock PhonologicalRule for testing RuleCollection."""

    def __init__(self, class_type, name="Test Rule", direction=0):
        """
        Create a mock PhonologicalRule.

        Args:
            class_type: The ClassName (PhRegularRule, etc.)
            name: Rule name
            direction: Direction value (0=LTR, 1=RTL, 2=simultaneous)
        """
        self.class_type = class_type
        self.ClassName = class_type
        self._name = name
        self._direction = direction

    @property
    def name(self):
        return self._name

    @property
    def direction(self):
        return self._direction

    @property
    def stratum(self):
        return None

    @property
    def has_output_specs(self):
        return self.class_type == "PhRegularRule"

    @property
    def output_specs(self):
        return [] if self.class_type != "PhRegularRule" else [Mock()]

    @property
    def has_metathesis_parts(self):
        return self.class_type == "PhMetathesisRule"

    @property
    def metathesis_parts(self):
        if self.class_type != "PhMetathesisRule":
            return [], []
        return [Mock()], [Mock()]

    @property
    def has_redup_parts(self):
        return self.class_type == "PhReduplicationRule"

    @property
    def redup_parts(self):
        if self.class_type != "PhReduplicationRule":
            return [], []
        return [Mock()], [Mock()]

    def as_regular_rule(self):
        return Mock() if self.class_type == "PhRegularRule" else None

    def as_metathesis_rule(self):
        return Mock() if self.class_type == "PhMetathesisRule" else None

    def as_reduplication_rule(self):
        return Mock() if self.class_type == "PhReduplicationRule" else None

    @property
    def concrete(self):
        return Mock()


class TestRuleCollection:
    """Tests for RuleCollection smart collection."""

    def test_collection_initialization_empty(self):
        """Test creating empty RuleCollection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        collection = RuleCollection()
        assert len(collection) == 0

    def test_collection_initialization_with_items(self):
        """Test creating RuleCollection with items."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rule = MockPhonologicalRule("PhRegularRule")
        collection = RuleCollection([rule])
        assert len(collection) == 1

    def test_collection_iteration(self):
        """Test iterating over RuleCollection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [MockPhonologicalRule("PhRegularRule") for _ in range(3)]
        collection = RuleCollection(rules)

        count = 0
        for rule in collection:
            count += 1
        assert count == 3

    def test_collection_indexing(self):
        """Test indexing RuleCollection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [MockPhonologicalRule("PhRegularRule") for _ in range(3)]
        collection = RuleCollection(rules)

        assert collection[0] is rules[0]
        assert collection[1] is rules[1]

    def test_collection_slicing(self):
        """Test slicing RuleCollection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [MockPhonologicalRule("PhRegularRule") for _ in range(5)]
        collection = RuleCollection(rules)

        sliced = collection[1:3]
        assert isinstance(sliced, RuleCollection)
        assert len(sliced) == 2

    def test_collection_str_shows_type_breakdown(self):
        """Test that __str__ shows type breakdown."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule"),
            MockPhonologicalRule("PhRegularRule"),
            MockPhonologicalRule("PhMetathesisRule"),
        ]
        collection = RuleCollection(rules)

        str_repr = str(collection)
        assert "RuleCollection" in str_repr
        assert "3 total" in str_repr
        assert "PhRegularRule: 2" in str_repr
        assert "PhMetathesisRule: 1" in str_repr

    def test_collection_str_empty(self):
        """Test __str__ on empty collection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        collection = RuleCollection()
        str_repr = str(collection)
        assert "empty" in str_repr

    def test_by_type_filter(self):
        """Test filtering by concrete type."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule"),
            MockPhonologicalRule("PhMetathesisRule"),
            MockPhonologicalRule("PhRegularRule"),
        ]
        collection = RuleCollection(rules)

        regular_only = collection.by_type("PhRegularRule")
        assert len(regular_only) == 2
        assert isinstance(regular_only, RuleCollection)

    def test_filter_by_direction(self):
        """Test filtering by direction."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule", direction=0),
            MockPhonologicalRule("PhRegularRule", direction=1),
            MockPhonologicalRule("PhRegularRule", direction=0),
        ]
        collection = RuleCollection(rules)

        ltr_rules = collection.filter(direction=0)
        assert len(ltr_rules) == 2

    def test_filter_where_custom_predicate(self):
        """Test filtering with custom predicate."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule"),
            MockPhonologicalRule("PhRegularRule"),
            MockPhonologicalRule("PhMetathesisRule"),
        ]
        collection = RuleCollection(rules)

        # Filter where class_type is PhRegularRule
        regular = collection.where(lambda r: r.class_type == "PhRegularRule")
        assert len(regular) == 2

    def test_regular_rules_convenience_filter(self):
        """Test regular_rules() convenience method."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule"),
            MockPhonologicalRule("PhMetathesisRule"),
            MockPhonologicalRule("PhRegularRule"),
        ]
        collection = RuleCollection(rules)

        regular = collection.regular_rules()
        assert len(regular) == 2
        for rule in regular:
            assert rule.class_type == "PhRegularRule"

    def test_metathesis_rules_convenience_filter(self):
        """Test metathesis_rules() convenience method."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule"),
            MockPhonologicalRule("PhMetathesisRule"),
            MockPhonologicalRule("PhMetathesisRule"),
        ]
        collection = RuleCollection(rules)

        metathesis = collection.metathesis_rules()
        assert len(metathesis) == 2
        for rule in metathesis:
            assert rule.class_type == "PhMetathesisRule"

    def test_redup_rules_convenience_filter(self):
        """Test redup_rules() convenience method."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule"),
            MockPhonologicalRule("PhReduplicationRule"),
            MockPhonologicalRule("PhReduplicationRule"),
        ]
        collection = RuleCollection(rules)

        redup = collection.redup_rules()
        assert len(redup) == 2
        for rule in redup:
            assert rule.class_type == "PhReduplicationRule"

    def test_filter_chaining(self):
        """Test chaining multiple filters."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule", direction=0),
            MockPhonologicalRule("PhRegularRule", direction=1),
            MockPhonologicalRule("PhMetathesisRule", direction=0),
        ]
        collection = RuleCollection(rules)

        # Chain: get regular rules, then filter by direction
        regular_ltr = collection.regular_rules().filter(direction=0)
        assert len(regular_ltr) == 1
        assert regular_ltr[0].class_type == "PhRegularRule"
        assert regular_ltr[0].direction == 0

    def test_repr(self):
        """Test string representation of collection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [MockPhonologicalRule("PhRegularRule") for _ in range(5)]
        collection = RuleCollection(rules)

        repr_str = repr(collection)
        assert "RuleCollection" in repr_str
        assert "5" in repr_str

    def test_append(self):
        """Test appending to collection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        collection = RuleCollection()
        rule = MockPhonologicalRule("PhRegularRule")
        collection.append(rule)

        assert len(collection) == 1
        assert collection[0] is rule

    def test_extend(self):
        """Test extending collection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        collection = RuleCollection()
        rules = [MockPhonologicalRule("PhRegularRule") for _ in range(3)]
        collection.extend(rules)

        assert len(collection) == 3

    def test_clear(self):
        """Test clearing collection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [MockPhonologicalRule("PhRegularRule") for _ in range(3)]
        collection = RuleCollection(rules)

        collection.clear()
        assert len(collection) == 0

    def test_filter_name_contains(self):
        """Test filtering by name contains."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule", name="Voicing Assimilation"),
            MockPhonologicalRule("PhRegularRule", name="Final Devoicing"),
            MockPhonologicalRule("PhMetathesisRule", name="Voicing Metathesis"),
        ]
        collection = RuleCollection(rules)

        voicing_rules = collection.filter(name_contains="Voicing")
        assert len(voicing_rules) == 2

    def test_filter_multiple_criteria(self):
        """Test filtering with multiple criteria."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule", name="Voicing", direction=0),
            MockPhonologicalRule("PhRegularRule", name="Devoicing", direction=1),
            MockPhonologicalRule("PhRegularRule", name="Voicing", direction=1),
        ]
        collection = RuleCollection(rules)

        # Filter: name contains 'Voicing' AND direction is 0
        voicing_ltr = collection.filter(name_contains="Voicing", direction=0)
        assert len(voicing_ltr) == 1
        assert voicing_ltr[0].name == "Voicing"
        assert voicing_ltr[0].direction == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
