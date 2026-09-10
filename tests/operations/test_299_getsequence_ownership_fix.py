#
#   test_299_getsequence_ownership_fix.py
#
#   Class: TestParagraphOperationsGetSequence /
#          TestSegmentOperationsGetSequence /
#          TestTextOperationsGetSequenceRemoved
#          Regression coverage for issue #299: `_GetSequence` ownership
#          ruling in specs/299-300-290-reorder-and-tsstring/reviews/
#          cycle1-domain.md.
#
#          - TextOperations._GetSequence is DELETED (no replacement).
#            `project.lp.Texts` is an owning COLLECTION (TextsOC), which
#            has no indexer and no .MoveTo(), so Sort/MoveUp/MoveDown/
#            MoveToIndex cannot operate on it. This mirrors the existing
#            LexEntryOperations precedent (also no override), and
#            BaseOperations._GetSequence's own NotImplementedError becomes
#            the correct, honest behavior.
#          - ParagraphOperations._GetSequence now returns
#            parent.ContentsOA.ParagraphsOS, parent being an IText (the
#            same type Create()/GetAll()/InsertAt() already require).
#            Previously it wrongly read parent.SegmentsOS -- a text's
#            paragraphs, not a paragraph's segments.
#          - SegmentOperations._GetSequence now returns parent.SegmentsOS,
#            parent being an IStTxtPara (the same type GetAll()/
#            AppendSentence() already require). Previously it wrongly
#            read parent.AnalysesRS -- AnalysesRS has its own dedicated
#            API (SetAnalysis/ReplaceAnalysis/InsertAnalysis/
#            AppendAnalysis/RemoveAnalysis, issue #215) and must not be
#            reachable via Sort/MoveUp/MoveDown/MoveToIndex.
#
#          These are mock-only regression tests (no live LCM project).
#          Live verification is scheduled for a later cycle.
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


class _MockWriteEnabledProject:
    """
    Minimal stand-in for a FLExProject that is open write-enabled, so
    that MoveUp's _EnsureWriteEnabled() precondition check passes and
    execution reaches _GetSequence(), which is what this test targets.
    """

    writeEnabled = True


class _MockStText:
    """
    Stand-in for IStText exposing only ParagraphsOS, the sequence
    ParagraphOperations._GetSequence must return via parent.ContentsOA.
    """

    def __init__(self, paragraphs=None):
        self.ParagraphsOS = list(paragraphs) if paragraphs else []


class _MockText:
    """
    Stand-in for IText exposing only ContentsOA (an _MockStText).
    Deliberately has no SegmentsOS attribute -- accessing it must raise
    AttributeError, guarding against a regression back to the old,
    wrong property.
    """

    def __init__(self, paragraphs=None):
        self.ContentsOA = _MockStText(paragraphs)


class _MockStTxtPara:
    """
    Stand-in for IStTxtPara exposing only SegmentsOS, the sequence
    SegmentOperations._GetSequence must return. Deliberately has no
    AnalysesRS attribute -- accessing it must raise AttributeError,
    guarding against a regression back to the old, wrong target.
    """

    def __init__(self, segments=None):
        self.SegmentsOS = list(segments) if segments else []


class TestParagraphOperationsGetSequence:
    """
    Pins ParagraphOperations._GetSequence to read
    parent.ContentsOA.ParagraphsOS off an IText-shaped parent.
    """

    def test_get_sequence_returns_paragraphs_os(self):
        from flexicon.code.TextsWords.ParagraphOperations import (
            ParagraphOperations,
        )

        para_a, para_b = object(), object()
        parent = _MockText(paragraphs=[para_a, para_b])

        sequence = ParagraphOperations._GetSequence(_MockSelf(), parent)

        assert sequence is parent.ContentsOA.ParagraphsOS, (
            "_GetSequence must return the parent's "
            "ContentsOA.ParagraphsOS sequence object itself, not a copy"
        )
        assert list(sequence) == [para_a, para_b]

    def test_parent_has_no_segments_os_attribute(self):
        """
        Guards the mock's own shape: if the old, wrong attribute
        (SegmentsOS, a paragraph's segments, not a text's paragraphs)
        ever exists on the IText mock, the regression test above could
        pass for the wrong reason.
        """
        parent = _MockText()
        assert not hasattr(parent, "SegmentsOS"), (
            "test setup error: mock IText stand-in must not expose "
            "SegmentsOS -- that is precisely the wrong-level property "
            "issue #299 is pinning against"
        )

    def test_get_sequence_raises_on_unfixed_property_name(self):
        """
        Direct falsifier: reading the OLD target (SegmentsOS) off this
        mock raises AttributeError, exactly as it would on the real
        IText. This is what made ParagraphOperations.Sort/MoveUp/
        MoveDown/MoveToIndex reorder the wrong sequence (a paragraph's
        segments instead of a text's paragraphs) before the fix.
        """
        parent = _MockText()
        with pytest.raises(AttributeError):
            parent.SegmentsOS


class TestSegmentOperationsGetSequence:
    """
    Pins SegmentOperations._GetSequence to read parent.SegmentsOS off an
    IStTxtPara-shaped parent, not parent.AnalysesRS.
    """

    def test_get_sequence_returns_segments_os(self):
        from flexicon.code.TextsWords.SegmentOperations import (
            SegmentOperations,
        )

        seg_a, seg_b = object(), object()
        parent = _MockStTxtPara(segments=[seg_a, seg_b])

        sequence = SegmentOperations._GetSequence(_MockSelf(), parent)

        assert sequence is parent.SegmentsOS, (
            "_GetSequence must return the parent's SegmentsOS sequence "
            "object itself, not a copy"
        )
        assert list(sequence) == [seg_a, seg_b]

    def test_parent_has_no_analyses_rs_attribute(self):
        """
        Guards the mock's own shape: if the old, wrong target
        (AnalysesRS) ever exists on the IStTxtPara mock, the regression
        test above could pass for the wrong reason. AnalysesRS has its
        own dedicated API (issue #215) and must not be reachable via
        Sort/MoveUp/MoveDown/MoveToIndex.
        """
        parent = _MockStTxtPara()
        assert not hasattr(parent, "AnalysesRS"), (
            "test setup error: mock IStTxtPara stand-in must not "
            "expose AnalysesRS -- that is precisely the wrong target "
            "issue #299 is pinning against"
        )

    def test_get_sequence_raises_on_unfixed_property_name(self):
        """
        Direct falsifier: reading the OLD target (AnalysesRS) off this
        mock raises AttributeError, exactly as it would on the real
        IStTxtPara used this way. This is what made SegmentOperations
        .Sort/MoveUp/MoveDown/MoveToIndex target the wrong sequence
        before the fix.
        """
        parent = _MockStTxtPara()
        with pytest.raises(AttributeError):
            parent.AnalysesRS


class TestTextOperationsGetSequenceRemoved:
    """
    Issue #299: TextOperations must NOT override _GetSequence.
    `project.lp.Texts` is an owning COLLECTION (TextsOC), which has no
    indexer and no .MoveTo(), so Sort/MoveUp/MoveDown/MoveToIndex cannot
    operate on it. The inherited BaseOperations._GetSequence's
    NotImplementedError is the correct, honest behavior -- mirroring the
    existing LexEntryOperations precedent (also no override).
    """

    def test_no_get_sequence_override_on_text_operations(self):
        from flexicon.code.TextsWords.TextOperations import TextOperations
        from flexicon.code.BaseOperations import BaseOperations

        assert "_GetSequence" not in TextOperations.__dict__, (
            "TextOperations must not define its own _GetSequence -- "
            "Texts is an unordered owning collection (TextsOC), not a "
            "reorderable sequence"
        )
        assert TextOperations._GetSequence is BaseOperations._GetSequence, (
            "TextOperations._GetSequence must resolve to the inherited "
            "BaseOperations implementation"
        )

    def test_sort_raises_not_implemented(self):
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(project=None)
        with pytest.raises(NotImplementedError):
            ops.Sort(object())

    def test_move_up_raises_not_implemented(self):
        from flexicon.code.TextsWords.TextOperations import TextOperations

        ops = TextOperations(project=_MockWriteEnabledProject())
        with pytest.raises(NotImplementedError):
            ops.MoveUp(object(), object())
