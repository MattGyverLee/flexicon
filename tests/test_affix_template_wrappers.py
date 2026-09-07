#
#   test_affix_template_wrappers.py
#
#   Tests for AffixTemplate and AffixTemplateCollection wrapper classes.
#
#   Platform: Python.NET
#            FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Comprehensive test suite for AffixTemplate wrapper and AffixTemplateCollection.

Tests cover:
1. Wrapper functionality (property access, capabilities)
2. Collection operations (filtering, searching, chaining)
3. Integration with MorphRuleOperations
4. Edge cases and error handling
5. Duplication and merging operations
"""

import pytest
from unittest.mock import Mock, MagicMock, PropertyMock, patch
import sys

# Try the real flexicon first (works when FieldWorks is installed). If that
# fails (CI / no-FW environment), fall back to mocking SIL.* so the wrapper
# modules can still be imported in isolation. When the real SIL is loaded,
# tests that rely on a lambda ITsString patch (the property/edge-case suites
# below) cannot pass -- the real .NET ITsString interface rejects Mock()
# inputs and the type does not allow attribute replacement. Those tests
# self-skip via SIL_IS_REAL below.
SIL_IS_REAL = False
try:
    import flexicon.code.lcm_casting as lcm_casting  # noqa: F401

    SIL_IS_REAL = True
except Exception:
    sil_lcmodel = MagicMock()
    sil_lcmodel.IMoInflAffixTemplate = MagicMock()

    sys.modules["SIL"] = MagicMock()
    sys.modules["SIL.LCModel"] = sil_lcmodel
    sys.modules["SIL.LCModel.Core"] = MagicMock()
    sil_kernel = MagicMock()
    # Create a mock ITsString class that just returns the object passed to it
    sil_kernel.ITsString = lambda x: x
    sys.modules["SIL.LCModel.Core.KernelInterfaces"] = sil_kernel
    sys.modules["SIL.LCModel.Core.Text"] = MagicMock()

    import flexicon.code.lcm_casting as lcm_casting

# Patch cast_to_concrete to just return the object as-is (no actual casting needed for tests)
original_cast = lcm_casting.cast_to_concrete
lcm_casting.cast_to_concrete = lambda obj: obj

# Skip mock-only tests when running against a real FieldWorks install.
_real_sil_skip = pytest.mark.skipif(
    SIL_IS_REAL,
    reason="Mock fixtures here cannot satisfy real .NET ITsString interface",
)


# ==============================================================================
# TEST FIXTURES
# ==============================================================================


@pytest.fixture
def mock_template():
    """Create a mock affix template object."""

    # Create mock ITsString that properly returns text
    def create_ts_string(text):
        ts_string = Mock()
        ts_string.Text = text
        return ts_string

    template = Mock()
    template.ClassName = "MoInflAffixTemplate"
    template.Name = Mock()
    template.Name.get_String = Mock(return_value=create_ts_string("Verb Template"))
    template.Description = Mock()
    template.Description.get_String = Mock(return_value=create_ts_string("Template for verbs"))
    template.StratumRA = Mock()
    template.Disabled = False
    template.PrefixSlotsRS = [Mock(Name="Prefix1"), Mock(Name="Prefix2")]
    template.SuffixSlotsRS = [Mock(Name="Suffix1")]
    template.ProcliticSlotsRS = []
    template.EncliticSlotsRS = []
    template.OwnerOfClass = Mock()
    template.Owner = Mock()
    return template


@pytest.fixture
def mock_template_no_slots():
    """Create a mock template without slots."""

    def create_ts_string(text):
        ts_string = Mock()
        ts_string.Text = text
        return ts_string

    template = Mock()
    template.ClassName = "MoInflAffixTemplate"
    template.Name = Mock()
    template.Name.get_String = Mock(return_value=create_ts_string("Empty Template"))
    template.Description = Mock()
    template.Description.get_String = Mock(return_value=create_ts_string(""))
    template.StratumRA = None
    template.Disabled = False
    template.PrefixSlotsRS = []
    template.SuffixSlotsRS = []
    template.ProcliticSlotsRS = []
    template.EncliticSlotsRS = []
    template.OwnerOfClass = Mock()
    return template


@pytest.fixture
def mock_template_all_slots():
    """Create a mock template with all slot types."""

    def create_ts_string(text):
        ts_string = Mock()
        ts_string.Text = text
        return ts_string

    template = Mock()
    template.ClassName = "MoInflAffixTemplate"
    template.Name = Mock()
    template.Name.get_String = Mock(return_value=create_ts_string("Full Template"))
    template.Description = Mock()
    template.Description.get_String = Mock(return_value=create_ts_string("All slots"))
    template.StratumRA = Mock()
    template.Disabled = False
    template.PrefixSlotsRS = [Mock(Name="P1"), Mock(Name="P2")]
    template.SuffixSlotsRS = [Mock(Name="S1"), Mock(Name="S2")]
    template.ProcliticSlotsRS = [Mock(Name="Pro1")]
    template.EncliticSlotsRS = [Mock(Name="Enc1")]
    template.OwnerOfClass = Mock()
    return template


# ==============================================================================
# TEST 1: AffixTemplate Wrapper Properties
# ==============================================================================


@_real_sil_skip
class TestAffixTemplateProperties:
    """Test basic property access on AffixTemplate wrapper."""

    def test_name_property(self, mock_template):
        """Test getting template name."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.name == "Verb Template"

    def test_description_property(self, mock_template):
        """Test getting template description."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.description == "Template for verbs"

    def test_stratum_property(self, mock_template):
        """Test getting template stratum."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.stratum is not None

    def test_disabled_property(self, mock_template):
        """Test getting disabled flag."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.disabled is False

    def test_disabled_property_true(self, mock_template):
        """Test disabled flag when True."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        mock_template.Disabled = True
        wrapped = AffixTemplate(mock_template)
        assert wrapped.disabled is True

    def test_empty_name_handling(self, mock_template):
        """Test handling of empty name."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        mock_template.Name.get_String = Mock(return_value=Mock(Text=""))
        wrapped = AffixTemplate(mock_template)
        assert wrapped.name == ""

    def test_null_stratum_handling(self, mock_template):
        """Test handling of null stratum."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        mock_template.StratumRA = None
        wrapped = AffixTemplate(mock_template)
        assert wrapped.stratum is None


# ==============================================================================
# TEST 2: Slot Properties
# ==============================================================================


class TestAffixTemplateSlots:
    """Test slot access and counting."""

    def test_prefix_slots(self, mock_template):
        """Test accessing prefix slots."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert len(wrapped.prefix_slots) == 2

    def test_suffix_slots(self, mock_template):
        """Test accessing suffix slots."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert len(wrapped.suffix_slots) == 1

    def test_proclitic_slots_empty(self, mock_template):
        """Test empty proclitic slots."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert len(wrapped.proclitic_slots) == 0

    def test_enclitic_slots_empty(self, mock_template):
        """Test empty enclitic slots."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert len(wrapped.enclitic_slots) == 0

    def test_prefix_slot_count(self, mock_template):
        """Test prefix slot count."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.prefix_slot_count == 2

    def test_suffix_slot_count(self, mock_template):
        """Test suffix slot count."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.suffix_slot_count == 1

    def test_total_slots(self, mock_template):
        """Test total slot count."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.total_slots == 3

    def test_total_slots_all_types(self, mock_template_all_slots):
        """Test total slots with all types."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template_all_slots)
        assert wrapped.total_slots == 6  # 2+2+1+1


# ==============================================================================
# TEST 3: Capability Checks
# ==============================================================================


class TestAffixTemplateCapabilities:
    """Test capability check properties."""

    def test_has_prefix_slots(self, mock_template):
        """Test has_prefix_slots check."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.has_prefix_slots is True

    def test_has_suffix_slots(self, mock_template):
        """Test has_suffix_slots check."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.has_suffix_slots is True

    def test_has_no_proclitic_slots(self, mock_template):
        """Test has_proclitic_slots when empty."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.has_proclitic_slots is False

    def test_has_any_slots(self, mock_template):
        """Test has_any_slots."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.has_any_slots is True

    def test_no_slots_has_any(self, mock_template_no_slots):
        """Test has_any_slots when no slots."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template_no_slots)
        assert wrapped.has_any_slots is False

    def test_all_slot_types_check(self, mock_template_all_slots):
        """Test all capability checks with full template."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template_all_slots)
        assert wrapped.has_prefix_slots is True
        assert wrapped.has_suffix_slots is True
        assert wrapped.has_proclitic_slots is True
        assert wrapped.has_enclitic_slots is True


# ==============================================================================
# TEST 4: AffixTemplateCollection Filtering
# ==============================================================================


@_real_sil_skip
class TestAffixTemplateCollectionFiltering:
    """Test collection filtering operations."""

    def test_create_empty_collection(self):
        """Test creating empty collection."""
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        collection = AffixTemplateCollection()
        assert len(collection) == 0

    def test_create_collection_with_items(self, mock_template, mock_template_no_slots):
        """Test creating collection with items."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        assert len(collection) == 2

    def test_iteration(self, mock_template, mock_template_no_slots):
        """Test iterating over collection."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        items = list(collection)
        assert len(items) == 2
        assert items[0].name == "Verb Template"

    def test_indexing(self, mock_template, mock_template_no_slots):
        """Test indexing into collection."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        assert collection[0].name == "Verb Template"
        assert collection[1].name == "Empty Template"

    def test_filter_by_name(self, mock_template, mock_template_no_slots):
        """Test filtering by name."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        filtered = collection.filter(name_contains="Verb")
        assert len(filtered) == 1
        assert filtered[0].name == "Verb Template"

    def test_where_clause_filtering(self, mock_template, mock_template_no_slots):
        """Test where() custom filtering."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        filtered = collection.where(lambda t: t.has_any_slots)
        assert len(filtered) == 1
        assert filtered[0].name == "Verb Template"

    def test_with_prefix_slots(self, mock_template, mock_template_no_slots):
        """Test filtering to templates with prefix slots."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        prefix_only = collection.with_prefix_slots()
        assert len(prefix_only) == 1
        assert prefix_only[0].name == "Verb Template"

    def test_with_suffix_slots(self, mock_template, mock_template_no_slots):
        """Test filtering to templates with suffix slots."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        suffix_only = collection.with_suffix_slots()
        assert len(suffix_only) == 1

    def test_chainable_filters(self, mock_template, mock_template_no_slots):
        """Test chaining multiple filters."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        filtered = collection.with_prefix_slots().filter(name_contains="Verb")
        assert len(filtered) == 1

    def test_filter_with_no_results(self, mock_template):
        """Test filter that returns no results."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped = AffixTemplate(mock_template)
        collection = AffixTemplateCollection([wrapped])
        filtered = collection.filter(name_contains="NonExistent")
        assert len(filtered) == 0


# ==============================================================================
# TEST 5: Collection Convenience Methods
# ==============================================================================


@_real_sil_skip
class TestAffixTemplateCollectionConvenience:
    """Test convenience filtering methods."""

    def test_full_templates(self, mock_template_all_slots, mock_template):
        """Test filtering to full templates."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template_all_slots)
        wrapped2 = AffixTemplate(mock_template)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        full = collection.full_templates()
        assert len(full) == 1
        assert full[0].name == "Full Template"

    def test_with_slots_prefix(self, mock_template, mock_template_no_slots):
        """Test with_slots('prefix')."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        prefix = collection.with_slots("prefix")
        assert len(prefix) == 1

    def test_with_slots_suffix(self, mock_template, mock_template_no_slots):
        """Test with_slots('suffix')."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        suffix = collection.with_slots("suffix")
        assert len(suffix) == 1

    def test_with_any_slots(self, mock_template, mock_template_no_slots):
        """Test with_any_slots filter."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped1 = AffixTemplate(mock_template)
        wrapped2 = AffixTemplate(mock_template_no_slots)
        collection = AffixTemplateCollection([wrapped1, wrapped2])
        with_slots = collection.with_any_slots()
        assert len(with_slots) == 1


# ==============================================================================
# TEST 6: String Representations
# ==============================================================================


@_real_sil_skip
class TestAffixTemplateRepresentations:
    """Test string representations and display."""

    def test_wrapper_repr(self, mock_template):
        """Test wrapper repr."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert "AffixTemplate" in repr(wrapped)
        assert "Verb Template" in repr(wrapped)

    def test_wrapper_str(self, mock_template):
        """Test wrapper str."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        result = str(wrapped)
        assert "Verb Template" in result
        assert "slots" in result

    def test_collection_repr(self, mock_template):
        """Test collection repr."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped = AffixTemplate(mock_template)
        collection = AffixTemplateCollection([wrapped])
        result = repr(collection)
        assert "AffixTemplateCollection" in result
        assert "1" in result

    def test_collection_str_empty(self):
        """Test collection str with empty."""
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        collection = AffixTemplateCollection()
        result = str(collection)
        assert "empty" in result.lower()

    def test_collection_str_with_items(self, mock_template):
        """Test collection str with items."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped = AffixTemplate(mock_template)
        collection = AffixTemplateCollection([wrapped])
        result = str(collection)
        assert "total" in result.lower() or "template" in result.lower()


# ==============================================================================
# TEST 7: Edge Cases
# ==============================================================================


@_real_sil_skip
class TestAffixTemplateEdgeCases:
    """Test edge cases and error handling."""

    def test_template_with_no_slots(self, mock_template_no_slots):
        """Test template with no slots."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template_no_slots)
        assert wrapped.total_slots == 0
        assert wrapped.has_any_slots is False

    def test_template_with_all_slot_types(self, mock_template_all_slots):
        """Test template with all slot types."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template_all_slots)
        assert wrapped.prefix_slot_count > 0
        assert wrapped.suffix_slot_count > 0
        assert wrapped.proclitic_slot_count > 0
        assert wrapped.enclitic_slot_count > 0

    def test_uninitialized_collection(self):
        """Test uninitialized collection."""
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        collection = AffixTemplateCollection()
        assert len(collection) == 0
        filtered = collection.with_prefix_slots()
        assert len(filtered) == 0

    def test_filter_returns_new_collection(self, mock_template):
        """Test that filter returns new collection."""
        from flexicon.code.Grammar.affix_template import AffixTemplate
        from flexicon.code.Grammar.affix_template_collection import AffixTemplateCollection

        wrapped = AffixTemplate(mock_template)
        collection = AffixTemplateCollection([wrapped])
        filtered = collection.with_prefix_slots()
        assert filtered is not collection
        assert len(collection) == 1  # Original unchanged

    def test_access_slots_safety(self, mock_template):
        """Test safe slot access."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        # Should not raise even if slots don't exist
        assert wrapped.prefix_slots is not None
        assert isinstance(wrapped.prefix_slots, list)

    def test_exception_handling_in_properties(self, mock_template):
        """Test that exceptions don't break property access."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        # Even with exception-prone mocks, should return safe defaults
        wrapped = AffixTemplate(mock_template)
        # These should not raise
        name = wrapped.name
        desc = wrapped.description
        assert name is not None
        assert desc is not None


# ==============================================================================
# TEST 8: Concrete Access
# ==============================================================================


class TestAffixTemplateConcrete:
    """Test direct concrete interface access."""

    def test_concrete_property(self, mock_template):
        """Test accessing concrete property."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        concrete = wrapped.concrete
        assert concrete is not None

    def test_class_type_property(self, mock_template):
        """Test class_type property."""
        from flexicon.code.Grammar.affix_template import AffixTemplate

        wrapped = AffixTemplate(mock_template)
        assert wrapped.class_type == "MoInflAffixTemplate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
