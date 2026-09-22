"""
Tests for phonological rule wrappers and smart collection.

This module tests the PhonologicalRule wrapper class and RuleCollection
smart collection, verifying that they transparently handle the concrete
phonological rule types that exist in this LCM (PhRegularRule and
PhMetathesisRule) without exposing ClassName or casting.

Tests verify:
- RuleCollection creation and type breakdown display
- Filtering by name, direction, type, and custom predicates
- Convenience filters (regular_rules(), metathesis_rules())
- Chaining filters
- Deprecation warnings for the PhReduplicationRule public surface
  (issue #326, T4)

Note: PhonologicalRule wrapper tests are limited here because they require
FLEx initialization (casting to concrete interfaces). Full tests should be
run in integration tests with a real FLEx project.
"""

import warnings

import pytest
from unittest.mock import Mock, patch, MagicMock


class MockPhonologicalRule:
    """Mock PhonologicalRule for testing RuleCollection."""

    def __init__(self, class_type, name="Test Rule", direction=0):
        """
        Create a mock PhonologicalRule.

        Args:
            class_type: The ClassName (PhRegularRule, PhMetathesisRule)
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
        return False

    @property
    def redup_parts(self):
        return [], []

    def as_regular_rule(self):
        return Mock() if self.class_type == "PhRegularRule" else None

    def as_metathesis_rule(self):
        return Mock() if self.class_type == "PhMetathesisRule" else None

    def as_reduplication_rule(self):
        return None

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
        assert "PhReduplicationRule" not in str_repr

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

    def test_redup_rules_emits_deprecation_warning_and_returns_empty(self):
        """redup_rules() is deprecated and returns an empty collection."""
        from flexicon.code.Grammar.rule_collection import RuleCollection

        rules = [
            MockPhonologicalRule("PhRegularRule"),
            MockPhonologicalRule("PhMetathesisRule"),
        ]
        collection = RuleCollection(rules)

        with pytest.warns(DeprecationWarning, match=r"redup_rules.*deprecated.*v5\.0\.0"):
            redup = collection.redup_rules()

        assert len(redup) == 0
        assert isinstance(redup, RuleCollection)

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


class TestPhonologicalRuleDeprecation:
    """Offline deprecation tests for the PhonologicalRule public surface."""

    @pytest.fixture
    def mock_lcm_rule(self):
        """Return a mock LCM rule object with ClassName PhRegularRule."""
        rule = Mock()
        rule.ClassName = "PhRegularRule"
        return rule

    def _make_wrapper(self, mock_lcm_rule):
        """Build a PhonologicalRule with cast_to_concrete patched to identity."""
        from flexicon.code.Grammar.phonological_rule import PhonologicalRule

        with patch(
            "flexicon.code.Shared.wrapper_base.cast_to_concrete",
            return_value=mock_lcm_rule,
        ):
            return PhonologicalRule(mock_lcm_rule)

    def test_has_redup_parts_warns_and_returns_false(self, mock_lcm_rule):
        """has_redup_parts emits DeprecationWarning and returns False."""
        wrapped = self._make_wrapper(mock_lcm_rule)
        with pytest.warns(DeprecationWarning, match=r"has_redup_parts.*deprecated.*v5\.0\.0"):
            result = wrapped.has_redup_parts
        assert result is False

    def test_redup_parts_warns_and_returns_empty_collections(self, mock_lcm_rule):
        """redup_parts emits DeprecationWarning and returns two empty collections."""
        from flexicon.code.System.context_collection import ContextCollection

        wrapped = self._make_wrapper(mock_lcm_rule)
        with pytest.warns(DeprecationWarning, match=r"redup_parts.*deprecated.*v5\.0\.0"):
            left, right = wrapped.redup_parts
        assert isinstance(left, ContextCollection)
        assert isinstance(right, ContextCollection)
        assert len(left) == 0
        assert len(right) == 0

    def test_as_reduplication_rule_warns_and_returns_none(self, mock_lcm_rule):
        """as_reduplication_rule emits DeprecationWarning and returns None."""
        wrapped = self._make_wrapper(mock_lcm_rule)
        with pytest.warns(DeprecationWarning, match=r"as_reduplication_rule.*deprecated.*v5\.0\.0"):
            result = wrapped.as_reduplication_rule()
        assert result is None


class TestPhonologicalRuleMetathesisParts:
    """Offline tests for metathesis_parts derived from StrucDescOS indices."""

    def _make_metathesis_rule(self, contexts, left_index, left_limit, right_index, right_limit):
        """Build a mock IPhMetathesisRule with the given StrucDescOS and indices."""
        concrete = Mock()
        concrete.ClassName = "PhMetathesisRule"
        concrete.StrucDescOS = contexts
        concrete.LeftSwitchIndex = left_index
        concrete.LeftSwitchLimit = left_limit
        concrete.RightSwitchIndex = right_index
        concrete.RightSwitchLimit = right_limit

        base = Mock()
        base.ClassName = "PhMetathesisRule"

        from flexicon.code.Grammar.phonological_rule import PhonologicalRule

        def _fake_cast(obj):
            return concrete if getattr(obj, "ClassName", None) == "PhMetathesisRule" else obj

        with patch(
            "flexicon.code.Shared.wrapper_base.cast_to_concrete",
            side_effect=_fake_cast,
        ):
            return PhonologicalRule(base), concrete

    def test_metathesis_parts_slices_struc_desc(self):
        """metathesis_parts returns ContextCollections sliced by switch ranges."""
        contexts = [Mock() for _ in range(4)]
        for ctx in contexts:
            ctx.ClassName = "PhSimpleContextSeg"

        wrapped, _ = self._make_metathesis_rule(
            contexts, left_index=1, left_limit=2, right_index=2, right_limit=4
        )

        assert wrapped.has_metathesis_parts is True
        left, right = wrapped.metathesis_parts
        assert len(left) == 1
        assert len(right) == 2

    def test_metathesis_parts_empty_for_unset_indices(self):
        """Unset/-1 indices produce empty collections gracefully."""
        contexts = []
        wrapped, _ = self._make_metathesis_rule(
            contexts, left_index=-1, left_limit=0, right_index=-1, right_limit=0
        )

        assert wrapped.has_metathesis_parts is False
        left, right = wrapped.metathesis_parts
        assert len(left) == 0
        assert len(right) == 0

    def test_metathesis_parts_empty_for_invalid_range(self):
        """Out-of-order switch indices produce empty collections."""
        contexts = [Mock(), Mock()]
        for ctx in contexts:
            ctx.ClassName = "PhSimpleContextSeg"

        wrapped, _ = self._make_metathesis_rule(
            contexts, left_index=2, left_limit=1, right_index=0, right_limit=2
        )

        assert wrapped.has_metathesis_parts is False


class TestPhonologicalContext:
    """Offline tests for PhonologicalContext segment/natural_class links."""

    @pytest.fixture
    def sil_module(self):
        """Provide a fake SIL.LCModel module with phonology interfaces."""
        import sys
        import types

        mod = types.ModuleType("SIL.LCModel")
        mod.IPhPhoneme = lambda obj: obj
        mod.IPhNaturalClass = lambda obj: obj
        sys.modules["SIL.LCModel"] = mod
        yield mod
        del sys.modules["SIL.LCModel"]

    def _make_context_wrapper(self, class_name, fsra=None):
        """Build a PhonologicalContext with cast_to_concrete patched."""
        from flexicon.code.System.phonological_context import PhonologicalContext

        concrete = Mock()
        concrete.ClassName = class_name
        if fsra is not None:
            concrete.FeatureStructureRA = fsra
        else:
            del concrete.FeatureStructureRA

        base = Mock()
        base.ClassName = class_name

        with patch(
            "flexicon.code.Shared.wrapper_base.cast_to_concrete",
            return_value=concrete,
        ):
            return PhonologicalContext(base), concrete

    def test_segment_returns_phoneme_via_feature_structure_ra(self, sil_module):
        """PhSimpleContextSeg.segment casts FeatureStructureRA to IPhPhoneme."""
        fsra = Mock()
        wrapped, concrete = self._make_context_wrapper("PhSimpleContextSeg", fsra=fsra)

        result = wrapped.segment

        assert result is fsra
        assert concrete.FeatureStructureRA is fsra

    def test_segment_returns_none_for_non_segment_context(self, sil_module):
        """segment is only meaningful on PhSimpleContextSeg."""
        wrapped, _ = self._make_context_wrapper("PhSimpleContextNC", fsra=Mock())
        assert wrapped.segment is None

    def test_segment_returns_none_when_feature_structure_ra_missing(self, sil_module):
        """segment returns None if FeatureStructureRA is absent."""
        wrapped, _ = self._make_context_wrapper("PhSimpleContextSeg", fsra=None)
        assert wrapped.segment is None

    def test_natural_class_returns_natural_class_via_feature_structure_ra(self, sil_module):
        """PhSimpleContextNC.natural_class casts FeatureStructureRA to IPhNaturalClass."""
        fsra = Mock()
        wrapped, concrete = self._make_context_wrapper("PhSimpleContextNC", fsra=fsra)

        result = wrapped.natural_class

        assert result is fsra
        assert concrete.FeatureStructureRA is fsra

    def test_natural_class_returns_none_for_non_nc_context(self, sil_module):
        """natural_class is only meaningful on PhSimpleContextNC."""
        wrapped, _ = self._make_context_wrapper("PhSimpleContextSeg", fsra=Mock())
        assert wrapped.natural_class is None

    def test_natural_class_returns_none_when_feature_structure_ra_missing(self, sil_module):
        """natural_class returns None if FeatureStructureRA is absent."""
        wrapped, _ = self._make_context_wrapper("PhSimpleContextNC", fsra=None)
        assert wrapped.natural_class is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
