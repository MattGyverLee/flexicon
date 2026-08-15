"""
Tests for morphosyntactic analysis wrappers and smart collection.

This module tests the MorphosyntaxAnalysis wrapper class and MSACollection
smart collection, verifying that they transparently handle the four
concrete types of MSAs without exposing ClassName or casting.

Tests verify:
- MSACollection creation and type breakdown display
- Filtering by type, POS, has_pos, and custom predicates
- Convenience filters (stem_msas(), deriv_aff_msas(), etc.)
- Chaining filters
- Backward compatibility with existing code

Note: MorphosyntaxAnalysis wrapper tests are limited here because they require
FLEx initialization (casting to concrete interfaces). Full tests should be
run in integration tests with a real FLEx project.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class MockMorphosyntaxAnalysis:
    """Mock MorphosyntaxAnalysis for testing MSACollection."""

    def __init__(self, class_type, pos_main=None, pos_from=None, pos_to=None):
        """
        Create a mock MorphosyntaxAnalysis.

        Args:
            class_type: The ClassName (MoStemMsa, etc.)
            pos_main: The main POS (or Mock with Guid)
            pos_from: The from POS (for derivational)
            pos_to: The to POS (for derivational)
        """
        self.class_type = class_type
        self.ClassName = class_type
        self._pos_main = pos_main
        self._pos_from = pos_from
        self._pos_to = pos_to

    @property
    def pos_main(self):
        return self._pos_main

    @property
    def pos_from(self):
        return self._pos_from

    @property
    def pos_to(self):
        return self._pos_to

    @property
    def has_from_pos(self):
        return self._pos_from is not None

    @property
    def is_stem_msa(self):
        return self.class_type == "MoStemMsa"

    @property
    def is_deriv_aff_msa(self):
        return self.class_type == "MoDerivAffMsa"

    @property
    def is_infl_aff_msa(self):
        return self.class_type == "MoInflAffMsa"

    @property
    def is_unclassified_aff_msa(self):
        return self.class_type == "MoUnclassifiedAffixMsa"

    def as_stem_msa(self):
        return Mock() if self.class_type == "MoStemMsa" else None

    def as_deriv_aff_msa(self):
        return Mock() if self.class_type == "MoDerivAffMsa" else None

    def as_infl_aff_msa(self):
        return Mock() if self.class_type == "MoInflAffMsa" else None

    def as_unclassified_aff_msa(self):
        return Mock() if self.class_type == "MoUnclassifiedAffixMsa" else None

    @property
    def concrete(self):
        return Mock()


class TestMSACollection:
    """Tests for MSACollection smart collection."""

    def test_collection_initialization_empty(self):
        """Test creating empty MSACollection."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        collection = MSACollection()
        assert len(collection) == 0
        assert list(collection) == []

    def test_collection_initialization_with_items(self):
        """Test creating MSACollection with items."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoDerivAffMsa")
        msa3 = MockMorphosyntaxAnalysis("MoInflAffMsa")

        collection = MSACollection([msa1, msa2, msa3])
        assert len(collection) == 3
        assert list(collection) == [msa1, msa2, msa3]

    def test_collection_iteration(self):
        """Test iterating over MSACollection."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoDerivAffMsa")

        collection = MSACollection([msa1, msa2])

        items = []
        for msa in collection:
            items.append(msa)

        assert items == [msa1, msa2]

    def test_collection_indexing(self):
        """Test indexing into MSACollection."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoDerivAffMsa")
        msa3 = MockMorphosyntaxAnalysis("MoInflAffMsa")

        collection = MSACollection([msa1, msa2, msa3])

        assert collection[0] == msa1
        assert collection[1] == msa2
        assert collection[2] == msa3

    def test_collection_slicing(self):
        """Test slicing MSACollection."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoDerivAffMsa")
        msa3 = MockMorphosyntaxAnalysis("MoInflAffMsa")

        collection = MSACollection([msa1, msa2, msa3])
        sliced = collection[0:2]

        assert isinstance(sliced, MSACollection)
        assert len(sliced) == 2
        assert list(sliced) == [msa1, msa2]

    def test_collection_str_empty(self):
        """Test string representation of empty collection."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        collection = MSACollection()
        output = str(collection)
        assert "empty" in output.lower()

    def test_collection_str_with_items(self):
        """Test string representation shows type breakdown."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa3 = MockMorphosyntaxAnalysis("MoDerivAffMsa")
        msa4 = MockMorphosyntaxAnalysis("MoInflAffMsa")

        collection = MSACollection([msa1, msa2, msa3, msa4])
        output = str(collection)

        # Should show type breakdown
        assert "4 total" in output
        assert "MoStemMsa: 2" in output
        assert "MoDerivAffMsa: 1" in output
        assert "MoInflAffMsa: 1" in output

    def test_stem_msas_filter(self):
        """Test filtering to only stem MSAs."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoDerivAffMsa")
        msa3 = MockMorphosyntaxAnalysis("MoStemMsa")

        collection = MSACollection([msa1, msa2, msa3])
        stem_only = collection.stem_msas()

        assert len(stem_only) == 2
        assert all(m.class_type == "MoStemMsa" for m in stem_only)

    def test_deriv_aff_msas_filter(self):
        """Test filtering to only derivational affix MSAs."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoDerivAffMsa")
        msa3 = MockMorphosyntaxAnalysis("MoInflAffMsa")
        msa4 = MockMorphosyntaxAnalysis("MoDerivAffMsa")

        collection = MSACollection([msa1, msa2, msa3, msa4])
        deriv_only = collection.deriv_aff_msas()

        assert len(deriv_only) == 2
        assert all(m.class_type == "MoDerivAffMsa" for m in deriv_only)

    def test_infl_aff_msas_filter(self):
        """Test filtering to only inflectional affix MSAs."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoInflAffMsa")
        msa3 = MockMorphosyntaxAnalysis("MoInflAffMsa")

        collection = MSACollection([msa1, msa2, msa3])
        infl_only = collection.infl_aff_msas()

        assert len(infl_only) == 2
        assert all(m.class_type == "MoInflAffMsa" for m in infl_only)

    def test_unclassified_aff_msas_filter(self):
        """Test filtering to only unclassified affix MSAs."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoUnclassifiedAffixMsa")
        msa3 = MockMorphosyntaxAnalysis("MoUnclassifiedAffixMsa")

        collection = MSACollection([msa1, msa2, msa3])
        unclass_only = collection.unclassified_aff_msas()

        assert len(unclass_only) == 2
        assert all(m.class_type == "MoUnclassifiedAffixMsa" for m in unclass_only)

    def test_filter_by_has_pos_true(self):
        """Test filtering MSAs that have POS."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        pos_mock = Mock()
        pos_mock.Guid = "test-guid"

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa", pos_main=pos_mock)
        msa2 = MockMorphosyntaxAnalysis("MoStemMsa", pos_main=None)
        msa3 = MockMorphosyntaxAnalysis("MoDerivAffMsa", pos_main=pos_mock)

        collection = MSACollection([msa1, msa2, msa3])
        with_pos = collection.filter(has_pos=True)

        assert len(with_pos) == 2
        assert all(m.pos_main is not None for m in with_pos)

    def test_filter_by_has_pos_false(self):
        """Test filtering MSAs that don't have POS."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        pos_mock = Mock()
        pos_mock.Guid = "test-guid"

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa", pos_main=pos_mock)
        msa2 = MockMorphosyntaxAnalysis("MoStemMsa", pos_main=None)
        msa3 = MockMorphosyntaxAnalysis("MoDerivAffMsa", pos_main=None)

        collection = MSACollection([msa1, msa2, msa3])
        without_pos = collection.filter(has_pos=False)

        assert len(without_pos) == 2
        assert all(m.pos_main is None for m in without_pos)

    def test_filter_by_pos_main(self):
        """Test filtering MSAs by specific POS."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        pos1 = Mock()
        pos1.Guid = "pos1-guid"
        pos2 = Mock()
        pos2.Guid = "pos2-guid"

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa", pos_main=pos1)
        msa2 = MockMorphosyntaxAnalysis("MoStemMsa", pos_main=pos2)
        msa3 = MockMorphosyntaxAnalysis("MoDerivAffMsa", pos_main=pos1)
        msa4 = MockMorphosyntaxAnalysis("MoInflAffMsa", pos_main=pos2)

        collection = MSACollection([msa1, msa2, msa3, msa4])
        matching = collection.filter(pos_main=pos1)

        assert len(matching) == 2
        assert all(m.pos_main is not None and str(m.pos_main.Guid) == "pos1-guid" for m in matching)

    def test_filter_chaining(self):
        """Test chaining filters together."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        pos_mock = Mock()
        pos_mock.Guid = "test-guid"

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa", pos_main=pos_mock)
        msa2 = MockMorphosyntaxAnalysis("MoStemMsa", pos_main=None)
        msa3 = MockMorphosyntaxAnalysis("MoDerivAffMsa", pos_main=pos_mock)
        msa4 = MockMorphosyntaxAnalysis("MoInflAffMsa", pos_main=pos_mock)

        collection = MSACollection([msa1, msa2, msa3, msa4])

        # Chain: get stems, then filter to those with POS
        result = collection.stem_msas().filter(has_pos=True)

        assert len(result) == 1
        assert result[0].class_type == "MoStemMsa"
        assert result[0].pos_main is not None

    def test_filter_with_where_custom_predicate(self):
        """Test filtering with custom predicate."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        pos1 = Mock()
        pos1.Guid = "pos1-guid"
        pos2 = Mock()
        pos2.Guid = "pos2-guid"

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa", pos_main=pos1)
        msa2 = MockMorphosyntaxAnalysis("MoDerivAffMsa", pos_main=pos1, pos_from=pos2)
        msa3 = MockMorphosyntaxAnalysis("MoInflAffMsa", pos_main=pos2)

        collection = MSACollection([msa1, msa2, msa3])

        # Filter: derivational affixes with from_pos set
        result = collection.where(lambda m: m.is_deriv_aff_msa and m.has_from_pos)

        assert len(result) == 1
        assert result[0].class_type == "MoDerivAffMsa"

    def test_by_type_filter(self):
        """Test filtering by ClassName."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoDerivAffMsa")
        msa3 = MockMorphosyntaxAnalysis("MoStemMsa")

        collection = MSACollection([msa1, msa2, msa3])
        result = collection.by_type("MoStemMsa")

        assert len(result) == 2
        assert all(m.class_type == "MoStemMsa" for m in result)

    def test_collection_returns_new_instance(self):
        """Test that filters return new collections, not modifying original."""
        from flexicon.code.Lexicon.msa_collection import MSACollection

        msa1 = MockMorphosyntaxAnalysis("MoStemMsa")
        msa2 = MockMorphosyntaxAnalysis("MoDerivAffMsa")

        collection = MSACollection([msa1, msa2])
        filtered = collection.stem_msas()

        # Original should be unchanged
        assert len(collection) == 2
        # New collection should be filtered
        assert len(filtered) == 1
        # Should be different objects
        assert filtered is not collection


class TestMorphosyntaxAnalysisWrapper:
    """Tests for MorphosyntaxAnalysis wrapper (without FLEx)."""

    def test_wrapper_type_checks(self):
        """Test type checking properties on wrapper."""
        from flexicon.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis

        # Mock the LCMObjectWrapper init
        with patch("flexicon.code.Lexicon.morphosyntax_analysis.LCMObjectWrapper.__init__"):
            msa = MorphosyntaxAnalysis.__new__(MorphosyntaxAnalysis)
            msa._obj = Mock()
            msa._obj.ClassName = "MoStemMsa"
            msa._concrete = Mock()

            assert msa.is_stem_msa is True
            assert msa.is_deriv_aff_msa is False
            assert msa.is_infl_aff_msa is False
            assert msa.is_unclassified_aff_msa is False

    def test_wrapper_as_stem_msa(self):
        """Test as_stem_msa method."""
        from flexicon.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis

        with patch("flexicon.code.Lexicon.morphosyntax_analysis.LCMObjectWrapper.__init__"):
            msa = MorphosyntaxAnalysis.__new__(MorphosyntaxAnalysis)
            msa._obj = Mock()
            msa._obj.ClassName = "MoStemMsa"
            msa._concrete = Mock(spec=["PartOfSpeechRA"])

            result = msa.as_stem_msa()
            assert result is msa._concrete

    def test_wrapper_as_deriv_aff_msa(self):
        """Test as_deriv_aff_msa method."""
        from flexicon.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis

        with patch("flexicon.code.Lexicon.morphosyntax_analysis.LCMObjectWrapper.__init__"):
            msa = MorphosyntaxAnalysis.__new__(MorphosyntaxAnalysis)
            msa._obj = Mock()
            msa._obj.ClassName = "MoDerivAffMsa"
            msa._concrete = Mock()

            result = msa.as_deriv_aff_msa()
            assert result is msa._concrete

            # Should return None for non-deriv MSAs
            msa._obj.ClassName = "MoStemMsa"
            result = msa.as_deriv_aff_msa()
            assert result is None

    def test_wrapper_as_infl_aff_msa(self):
        """Test as_infl_aff_msa method."""
        from flexicon.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis

        with patch("flexicon.code.Lexicon.morphosyntax_analysis.LCMObjectWrapper.__init__"):
            msa = MorphosyntaxAnalysis.__new__(MorphosyntaxAnalysis)
            msa._obj = Mock()
            msa._obj.ClassName = "MoInflAffMsa"
            msa._concrete = Mock()

            result = msa.as_infl_aff_msa()
            assert result is msa._concrete

    def test_wrapper_as_unclassified_aff_msa(self):
        """Test as_unclassified_aff_msa method."""
        from flexicon.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis

        with patch("flexicon.code.Lexicon.morphosyntax_analysis.LCMObjectWrapper.__init__"):
            msa = MorphosyntaxAnalysis.__new__(MorphosyntaxAnalysis)
            msa._obj = Mock()
            msa._obj.ClassName = "MoUnclassifiedAffixMsa"
            msa._concrete = Mock()

            result = msa.as_unclassified_aff_msa()
            assert result is msa._concrete

    def test_wrapper_concrete_property(self):
        """Test concrete property returns _concrete."""
        from flexicon.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis

        with patch("flexicon.code.Lexicon.morphosyntax_analysis.LCMObjectWrapper.__init__"):
            msa = MorphosyntaxAnalysis.__new__(MorphosyntaxAnalysis)
            msa._obj = Mock()
            msa._obj.ClassName = "MoStemMsa"
            msa._concrete = Mock()

            assert msa.concrete is msa._concrete

    def test_wrapper_repr(self):
        """Test wrapper string representations."""
        from flexicon.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis

        with patch("flexicon.code.Lexicon.morphosyntax_analysis.LCMObjectWrapper.__init__"):
            msa = MorphosyntaxAnalysis.__new__(MorphosyntaxAnalysis)
            msa._obj = Mock()
            msa._obj.ClassName = "MoStemMsa"
            msa._concrete = Mock()

            repr_str = repr(msa)
            assert "MorphosyntaxAnalysis" in repr_str
            assert "MoStemMsa" in repr_str

    def test_wrapper_str_without_pos(self):
        """Test wrapper string representation without POS."""
        from flexicon.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis

        with patch("flexicon.code.Lexicon.morphosyntax_analysis.LCMObjectWrapper.__init__"):
            with patch("flexicon.code.Lexicon.morphosyntax_analysis.get_pos_from_msa", return_value=None):
                msa = MorphosyntaxAnalysis.__new__(MorphosyntaxAnalysis)
                msa._obj = Mock()
                msa._obj.ClassName = "MoStemMsa"
                msa._concrete = Mock()

                str_repr = str(msa)
                assert "MoStemMsa" in str_repr
