#
#   test_300_getsequence_property_rename.py
#
#   Class: TestWfiMorphBundleGetSequenceProperty /
#          TestDataNotebookGetSequenceProperty
#          Regression coverage for issue #300: two `_GetSequence`
#          overrides read a property name that does not exist on their
#          parent type.
#
#          - WfiMorphBundleOperations._GetSequence (parent: IWfiAnalysis)
#            read `parent.MorphsOS`. `IWfiAnalysis` has no `MorphsOS`;
#            the ordered morph-bundle sequence is `MorphBundlesOS`, which
#            Duplicate()/Reorder() in the same file already use.
#          - DataNotebookOperations._GetSequence (parent: IRnGenericRec)
#            read `parent.RecordsOS`. `IRnGenericRec` has no `RecordsOS`;
#            the ordered child-record sequence is `SubRecordsOS`, which
#            Duplicate() in the same file already uses (with
#            IndexOf/Insert/Add), per the "ordered" comment at line ~2462.
#
#          Every BaseOperations reorder method (`Sort`, `MoveUp`,
#          `MoveDown`, `MoveToIndex`) calls `self._GetSequence(parent)`,
#          so all four raised `AttributeError` for both types before this
#          fix.
#
#          These are mock-only regression tests (no live LCM project).
#          Each mock parent exposes ONLY the correct property
#          (MorphBundlesOS / SubRecordsOS) and deliberately does NOT
#          expose the old, wrong property (MorphsOS / RecordsOS), so a
#          regression back to the old attribute name fails loudly with
#          AttributeError rather than silently reading stale mock state.
#          Live verification of these two sites is scheduled for cycle 2.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest


class _MockSelf:
    """Minimal stand-in for an Operations instance -- _GetSequence does
    not touch self, but it is an instance method so it needs a receiver.
    """

    project = None


class _MockWfiAnalysis:
    """
    Stand-in for IWfiAnalysis exposing only the real ordered sequence,
    MorphBundlesOS. Deliberately has no MorphsOS attribute -- accessing
    it must raise AttributeError, mirroring the real LCM interface.
    """

    def __init__(self, bundles=None):
        self.MorphBundlesOS = list(bundles) if bundles else []


class _MockRnGenericRec:
    """
    Stand-in for IRnGenericRec exposing only the real ordered sequence,
    SubRecordsOS. Deliberately has no RecordsOS attribute -- accessing
    it must raise AttributeError, mirroring the real LCM interface.
    """

    def __init__(self, records=None):
        self.SubRecordsOS = list(records) if records else []


class TestWfiMorphBundleGetSequenceProperty:
    """
    Pins WfiMorphBundleOperations._GetSequence to read MorphBundlesOS,
    not MorphsOS, off an IWfiAnalysis-shaped parent.
    """

    def test_get_sequence_returns_morph_bundles_os(self):
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )

        bundle_a, bundle_b = object(), object()
        parent = _MockWfiAnalysis(bundles=[bundle_a, bundle_b])

        sequence = WfiMorphBundleOperations._GetSequence(_MockSelf(), parent)

        assert sequence is parent.MorphBundlesOS, (
            "_GetSequence must return the parent's MorphBundlesOS "
            "sequence object itself, not a copy"
        )
        assert list(sequence) == [bundle_a, bundle_b]

    def test_parent_has_no_morphs_os_attribute(self):
        """
        Guards the mock's own shape: if the old, wrong attribute name
        ever exists on the mock, the regression test above could pass
        for the wrong reason (reading stale/matching mock state instead
        of genuinely exercising the fixed property name).
        """
        parent = _MockWfiAnalysis()
        assert not hasattr(parent, "MorphsOS"), (
            "test setup error: mock IWfiAnalysis stand-in must not "
            "expose MorphsOS -- that is precisely the nonexistent "
            "property issue #300 is pinning against"
        )

    def test_get_sequence_raises_on_unfixed_property_name(self):
        """
        Direct falsifier: reading the OLD property name off this mock
        raises AttributeError, exactly as it would on the real
        IWfiAnalysis. This is what made Sort/MoveUp/MoveDown/
        MoveToIndex fail loudly (never silently misorder) before the
        fix.
        """
        parent = _MockWfiAnalysis()
        with pytest.raises(AttributeError):
            parent.MorphsOS


class TestDataNotebookGetSequenceProperty:
    """
    Pins DataNotebookOperations._GetSequence to read SubRecordsOS, not
    RecordsOS, off an IRnGenericRec-shaped parent.
    """

    def test_get_sequence_returns_sub_records_os(self):
        from flexicon.code.Notebook.DataNotebookOperations import (
            DataNotebookOperations,
        )

        rec_a, rec_b = object(), object()
        parent = _MockRnGenericRec(records=[rec_a, rec_b])

        sequence = DataNotebookOperations._GetSequence(_MockSelf(), parent)

        assert sequence is parent.SubRecordsOS, (
            "_GetSequence must return the parent's SubRecordsOS "
            "sequence object itself, not a copy"
        )
        assert list(sequence) == [rec_a, rec_b]

    def test_parent_has_no_records_os_attribute(self):
        """
        Guards the mock's own shape: if the old, wrong attribute name
        ever exists on the mock, the regression test above could pass
        for the wrong reason (reading stale/matching mock state instead
        of genuinely exercising the fixed property name).
        """
        parent = _MockRnGenericRec()
        assert not hasattr(parent, "RecordsOS"), (
            "test setup error: mock IRnGenericRec stand-in must not "
            "expose RecordsOS -- that is precisely the nonexistent "
            "property issue #300 is pinning against"
        )

    def test_get_sequence_raises_on_unfixed_property_name(self):
        """
        Direct falsifier: reading the OLD property name off this mock
        raises AttributeError, exactly as it would on the real
        IRnGenericRec. This is what made Sort/MoveUp/MoveDown/
        MoveToIndex fail loudly (never silently misorder) before the
        fix.
        """
        parent = _MockRnGenericRec()
        with pytest.raises(AttributeError):
            parent.RecordsOS
