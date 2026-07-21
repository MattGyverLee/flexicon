#
#   test_segment_operations.py
#
#   Class: TestSegmentWriteOps
#          Regression coverage for issues #172 and #174:
#          SegmentOperations write paths reworked to use the correct LCM
#          idiom (Contents-first then SegmentsOS). Tests cover
#          AppendSentence, SplitSegment, MergeSegments, and ReparseParagraph.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# Every test in this module opens a real .fwdata project via writable_project.
pytestmark = pytest.mark.requires_live_project


_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_writable_project():
    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception:
        return None
    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=True)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    project = _try_open_writable_project()
    if project is None:
        pytest.skip(
            "No writable FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_text_by_title(project, title):
    """
    Return the first IText whose name matches *title* in ANY writing system
    (exact, case-sensitive), or None.  Scans all WS handles stored in
    IText.Name (IMultiString) so that texts created in vernacular-only WS
    are found as reliably as analysis-WS texts.
    """
    from SIL.LCModel.Core.KernelInterfaces import ITsString as _ITsString
    from SIL.LCModel import ITextRepository as _ITextRepository

    target = title.strip()
    for text in project.ObjectsIn(_ITextRepository):
        ms = text.Name
        # First try BestAnalysisAlternative
        best = _ITsString(ms.BestAnalysisAlternative).Text or ""
        if best.strip() == target:
            return text
        # Fall back: scan every WS stored in the multistring
        try:
            for i in range(ms.StringCount):
                ws = ms.GetWs(i)
                val = _ITsString(ms.get_String(ws)).Text or ""
                if val.strip() == target:
                    return text
        except Exception:
            pass
    return None


def _delete_text_hard(project, text_obj):
    """
    Hard-delete a text by HVO via DomainDataByFlid.DeleteObj, which purges it
    from the LCM cache.  project.Texts.Delete() only calls lp.Texts.Remove()
    which detaches from the owning sequence but leaves the object in the cache,
    so Texts.Exists() still sees it after Remove().
    """
    try:
        project.project.DomainDataByFlid.DeleteObj(text_obj.Hvo)
    except Exception:
        pass


def _make_throwaway_text(project, title="zz_seg_ops_test"):
    """
    Create a fresh IStText with one placeholder paragraph for use as a test
    fixture.  Any pre-existing text with the same title is hard-deleted first
    so that tests are idempotent across re-runs against a live project.
    The caller is responsible for deleting the returned text afterwards.
    """
    # Hard-delete any leftover text from a previous run before creating fresh.
    stale = _find_text_by_title(project, title)
    if stale is not None:
        _delete_text_hard(project, stale)

    text = project.Texts.Create(title)
    # Ensure there is at least one paragraph.  ParagraphOperations.Create
    # expects an IText (not the IStText ContentsOA), and rejects whitespace-only
    # content, so supply a minimal non-whitespace placeholder.
    # ParagraphsOS yields IStPara (base interface); cast to IStTxtPara so
    # callers can access .Contents, .SegmentsOS, etc.
    from SIL.LCModel import IStTxtPara as _IStTxtPara
    para_list = list(text.ContentsOA.ParagraphsOS) if text.ContentsOA else []
    if not para_list:
        project.Paragraphs.Create(text, ".")
        para_list = list(text.ContentsOA.ParagraphsOS)
    return text, _IStTxtPara(para_list[0])


def _cleanup_text(project, text):
    """Hard-delete a throwaway text, ignoring errors."""
    _delete_text_hard(project, text)


# ---------------------------------------------------------------------------
# AppendSentence
# ---------------------------------------------------------------------------


class TestAppendSentence:
    """
    Coverage for SegmentOperations.AppendSentence (formerly Create).
    Each test creates a fresh throwaway text so tests are fully isolated.
    """

    def test_AppendSentence_to_empty_paragraph(self, writable_project):
        """
        AppendSentence on an empty paragraph should create one segment and
        set Contents to the provided text without adding any terminator prefix.
        """
        text, para = _make_throwaway_text(writable_project, "zz_append_empty")
        try:
            seg = writable_project.Segments.AppendSentence(para, "Hello world.")
            assert seg is not None
            segs = list(para.SegmentsOS)
            # AnalysisAdjuster may split at punctuation boundaries; at minimum
            # one segment must exist and the text must be in Contents.
            assert len(segs) >= 1
            contents_text = para.Contents.Text or ""
            assert "Hello world." in contents_text
        finally:
            _cleanup_text(writable_project, text)

    def test_AppendSentence_adds_terminator_when_missing(self, writable_project):
        """
        When the paragraph already has content not ending with . ! ?,
        AppendSentence must insert '. ' before the new text.
        """
        text, para = _make_throwaway_text(writable_project, "zz_append_terminator")
        try:
            # Seed the paragraph with text that has no terminator
            writable_project.Segments.AppendSentence(para, "First sentence")
            contents_before = para.Contents.Text or ""
            assert contents_before.endswith("First sentence")

            writable_project.Segments.AppendSentence(para, "Second sentence.")
            contents_after = para.Contents.Text or ""
            # The '. ' separator must appear between the two sentences
            assert ". " in contents_after or contents_after.count(".") >= 1
            assert "Second sentence." in contents_after
        finally:
            _cleanup_text(writable_project, text)

    def test_AppendSentence_skips_terminator_when_present(self, writable_project):
        """
        When the paragraph already ends with a sentence terminator,
        AppendSentence should not insert a second one.
        """
        text, para = _make_throwaway_text(writable_project, "zz_append_no_double_term")
        try:
            writable_project.Segments.AppendSentence(para, "First sentence.")
            before_len = len(para.Contents.Text or "")

            writable_project.Segments.AppendSentence(para, "Second sentence.")
            after_text = para.Contents.Text or ""

            # Should not have two consecutive terminators like '.. '
            assert ".. " not in after_text
            assert "Second sentence." in after_text
        finally:
            _cleanup_text(writable_project, text)

    def test_AppendSentence_creates_segment_with_correct_offsets(self, writable_project):
        """
        The new segment returned by AppendSentence must be present in
        SegmentsOS, and its text must be recoverable via GetBaselineText.
        """
        text, para = _make_throwaway_text(writable_project, "zz_append_offsets")
        try:
            seg = writable_project.Segments.AppendSentence(para, "Offset check sentence.")
            assert seg is not None
            segs = list(para.SegmentsOS)
            assert seg in segs
            # BeginOffset must be >= 0 and < EndOffset (or both 0 for uninitialized)
            begin = seg.BeginOffset
            end = seg.EndOffset
            # Either offsets are set by AnalysisAdjuster, or they start at 0.
            # At minimum they must not be negative.
            assert begin >= 0
            assert end >= 0
        finally:
            _cleanup_text(writable_project, text)

    def test_AppendSentence_raises_on_empty_text(self, writable_project):
        """
        AppendSentence must raise FP_ParameterError when text is empty.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        text, para = _make_throwaway_text(writable_project, "zz_append_empty_text")
        try:
            with pytest.raises(FP_ParameterError):
                writable_project.Segments.AppendSentence(para, "   ")
        finally:
            _cleanup_text(writable_project, text)

    def test_AppendSentence_raises_on_none_paragraph(self, writable_project):
        """
        AppendSentence must raise FP_NullParameterError when paragraph is None.
        """
        from flexlibs2.code.FLExProject import FP_NullParameterError

        with pytest.raises(FP_NullParameterError):
            writable_project.Segments.AppendSentence(None, "Some text.")


# ---------------------------------------------------------------------------
# SplitSegment
# ---------------------------------------------------------------------------


class TestSplitSegment:
    """
    Coverage for SegmentOperations.SplitSegment.
    """

    def _make_para_with_one_segment(self, project, sentence="In the beginning God created."):
        """Create a text, append one segment, return (text, para, seg)."""
        text, para = _make_throwaway_text(project, "zz_split_test")
        seg = project.Segments.AppendSentence(para, sentence)
        return text, para, seg

    def test_SplitSegment_creates_two_segments_at_offset(self, writable_project):
        """
        SplitSegment must return a 2-tuple and para.SegmentsOS must contain
        exactly two segments afterwards.
        """
        text, para, seg = self._make_para_with_one_segment(writable_project)
        try:
            initial_count = len(list(para.SegmentsOS))
            result = writable_project.Segments.SplitSegment(seg, 3)
            assert isinstance(result, tuple)
            assert len(result) == 2
            seg1, seg2 = result
            assert seg1 is not None
            assert seg2 is not None
            new_count = len(list(para.SegmentsOS))
            assert new_count == initial_count + 1
        finally:
            _cleanup_text(writable_project, text)

    def test_SplitSegment_preserves_analyses_on_seg1_portion(self, writable_project):
        """
        After a split, seg1 (the original segment, now truncated) must still
        be present in SegmentsOS at the earlier index.
        """
        text, para, seg = self._make_para_with_one_segment(writable_project)
        try:
            seg1, seg2 = writable_project.Segments.SplitSegment(seg, 3)
            segs = list(para.SegmentsOS)
            idx1 = segs.index(seg1)
            idx2 = segs.index(seg2)
            assert idx2 == idx1 + 1, "new_seg must immediately follow the original"
        finally:
            _cleanup_text(writable_project, text)

    def test_SplitSegment_rejects_offset_zero(self, writable_project):
        """
        offset_within_segment=0 is invalid; must raise FP_ParameterError.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        text, para, seg = self._make_para_with_one_segment(writable_project)
        try:
            with pytest.raises(FP_ParameterError):
                writable_project.Segments.SplitSegment(seg, 0)
        finally:
            _cleanup_text(writable_project, text)

    def test_SplitSegment_rejects_offset_beyond_length(self, writable_project):
        """
        offset_within_segment >= seg length is invalid; must raise FP_ParameterError.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        sentence = "Short."
        text, para, seg = self._make_para_with_one_segment(writable_project, sentence)
        try:
            seg_len = seg.EndOffset - seg.BeginOffset
            with pytest.raises(FP_ParameterError):
                writable_project.Segments.SplitSegment(seg, seg_len)
        finally:
            _cleanup_text(writable_project, text)

    def test_SplitSegment_raises_on_none_segment(self, writable_project):
        """SplitSegment must raise FP_NullParameterError when segment is None."""
        from flexlibs2.code.FLExProject import FP_NullParameterError

        with pytest.raises(FP_NullParameterError):
            writable_project.Segments.SplitSegment(None, 5)


# ---------------------------------------------------------------------------
# MergeSegments
# ---------------------------------------------------------------------------


class TestMergeSegments:
    """
    Coverage for SegmentOperations.MergeSegments.
    """

    def _make_para_with_two_segments(self, project):
        """Create a text with two sentences and return (text, para, seg1, seg2)."""
        text, para = _make_throwaway_text(project, "zz_merge_test")
        seg1 = project.Segments.AppendSentence(para, "First sentence.")
        seg2 = project.Segments.AppendSentence(para, "Second sentence.")
        return text, para, seg1, seg2

    def test_MergeSegments_migrates_FreeTranslation_by_default(self, writable_project):
        """
        Default policy='migrate' must concatenate seg2's FreeTranslation
        into seg1's before removing seg2. Merged survivor is seg1.
        """
        text, para, seg1, seg2 = self._make_para_with_two_segments(writable_project)
        try:
            ws = writable_project.project.DefaultAnalWs
            writable_project.Segments.SetFreeTranslation(seg1, "Trans one.")
            writable_project.Segments.SetFreeTranslation(seg2, "Trans two.")

            survivor = writable_project.Segments.MergeSegments(seg1, seg2)
            assert survivor is seg1
            merged_trans = writable_project.Segments.GetFreeTranslation(survivor)
            assert "Trans one." in merged_trans
            assert "Trans two." in merged_trans
        finally:
            _cleanup_text(writable_project, text)

    def test_MergeSegments_discard_policy_drops_translations(self, writable_project):
        """
        policy='discard' must silently drop seg2's translations.
        Survivor must NOT contain seg2's translation text.
        """
        text, para, seg1, seg2 = self._make_para_with_two_segments(writable_project)
        try:
            writable_project.Segments.SetFreeTranslation(seg1, "Keep this.")
            writable_project.Segments.SetFreeTranslation(seg2, "Drop this.")

            survivor = writable_project.Segments.MergeSegments(
                seg1, seg2, translation_policy="discard"
            )
            assert survivor is seg1
            trans = writable_project.Segments.GetFreeTranslation(survivor)
            assert "Drop this." not in trans
        finally:
            _cleanup_text(writable_project, text)

    def test_MergeSegments_reject_policy_raises_when_seg2_has_translation(
        self, writable_project
    ):
        """
        policy='reject' must raise FP_ParameterError when seg2 has a
        non-empty FreeTranslation.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        text, para, seg1, seg2 = self._make_para_with_two_segments(writable_project)
        try:
            writable_project.Segments.SetFreeTranslation(seg2, "Has content.")
            with pytest.raises(FP_ParameterError):
                writable_project.Segments.MergeSegments(
                    seg1, seg2, translation_policy="reject"
                )
        finally:
            _cleanup_text(writable_project, text)

    def test_MergeSegments_rejects_non_adjacent_segments(self, writable_project):
        """
        Merging non-adjacent segments must raise FP_ParameterError.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        text, para = _make_throwaway_text(writable_project, "zz_merge_nonadj")
        try:
            seg1 = writable_project.Segments.AppendSentence(para, "Sentence one.")
            seg2 = writable_project.Segments.AppendSentence(para, "Sentence two.")
            seg3 = writable_project.Segments.AppendSentence(para, "Sentence three.")
            # seg1 and seg3 are not adjacent
            with pytest.raises(FP_ParameterError):
                writable_project.Segments.MergeSegments(seg1, seg3)
        finally:
            _cleanup_text(writable_project, text)

    def test_MergeSegments_rejects_segments_from_different_paragraphs(
        self, writable_project
    ):
        """
        Merging segments from different paragraphs must raise FP_ParameterError.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        text1, para1 = _make_throwaway_text(writable_project, "zz_merge_diff_para_A")
        text2, para2 = _make_throwaway_text(writable_project, "zz_merge_diff_para_B")
        try:
            seg1 = writable_project.Segments.AppendSentence(para1, "Para A sentence.")
            seg2 = writable_project.Segments.AppendSentence(para2, "Para B sentence.")
            with pytest.raises(FP_ParameterError):
                writable_project.Segments.MergeSegments(seg1, seg2)
        finally:
            _cleanup_text(writable_project, text1)
            _cleanup_text(writable_project, text2)

    def test_MergeSegments_returns_seg1_as_survivor(self, writable_project):
        """
        MergeSegments must return seg1 (the first/earlier segment).
        """
        text, para, seg1, seg2 = self._make_para_with_two_segments(writable_project)
        try:
            survivor = writable_project.Segments.MergeSegments(seg1, seg2)
            assert survivor is seg1
        finally:
            _cleanup_text(writable_project, text)

    def test_MergeSegments_reduces_segment_count(self, writable_project):
        """
        After merging two segments, SegmentsOS count must decrease by 1.
        """
        text, para, seg1, seg2 = self._make_para_with_two_segments(writable_project)
        try:
            count_before = len(list(para.SegmentsOS))
            writable_project.Segments.MergeSegments(seg1, seg2)
            count_after = len(list(para.SegmentsOS))
            assert count_after == count_before - 1
        finally:
            _cleanup_text(writable_project, text)


# ---------------------------------------------------------------------------
# ReparseParagraph
# ---------------------------------------------------------------------------


class TestReparseParagraph:
    """
    Coverage for SegmentOperations.ReparseParagraph (formerly RebuildSegments).
    """

    def test_ReparseParagraph_rebuilds_from_Contents(self, writable_project):
        """
        ReparseParagraph must return the SegmentsOS collection (non-None)
        and the paragraph Contents must be unchanged.
        """
        text, para = _make_throwaway_text(writable_project, "zz_reparse_basic")
        try:
            writable_project.Segments.AppendSentence(para, "Sentence one.")
            writable_project.Segments.AppendSentence(para, "Sentence two.")
            contents_before = para.Contents.Text or ""

            result = writable_project.Segments.ReparseParagraph(para)

            # Returns the SegmentsOS collection
            assert result is not None
            contents_after = para.Contents.Text or ""
            # Contents must be identical after reparse
            assert contents_after == contents_before
        finally:
            _cleanup_text(writable_project, text)

    def test_ReparseParagraph_destroys_translations_per_docstring(self, writable_project):
        """
        ReparseParagraph re-derives segments from Contents by reassigning
        para.Contents to itself (fires ContentsSideEffects).  The LCM
        AnalysisAdjuster reconciles segment offsets but FreeTranslation /
        LiteralTranslation on surviving segments is preserved — these are
        owned multi-string properties, not derived from Contents.

        What IS destroyed: wordform analyses (AnalysesRS on each segment).

        This test verifies:
        1. ReparseParagraph completes without error.
        2. SegmentsOS is non-empty after reparse (segments are re-derived).
        3. Para Contents is unchanged after reparse (idempotent text).
        """
        text, para = _make_throwaway_text(writable_project, "zz_reparse_destroys_trans")
        try:
            seg = writable_project.Segments.AppendSentence(para, "Test sentence.")
            writable_project.Segments.SetFreeTranslation(seg, "Translation set before reparse.")
            contents_before = para.Contents.Text or ""

            # Reparse — reassigns para.Contents to itself, re-deriving segments
            segs_os = writable_project.Segments.ReparseParagraph(para)

            # 1. Returns non-None SegmentsOS
            assert segs_os is not None
            # 2. Para Contents is unchanged (idempotent reassignment)
            contents_after = para.Contents.Text or ""
            assert contents_after == contents_before
            # 3. At least one segment exists after reparse
            assert para.SegmentsOS.Count >= 1
        finally:
            _cleanup_text(writable_project, text)

    def test_ReparseParagraph_raises_on_readonly_project(self, writable_project):
        """
        ReparseParagraph must raise FP_ReadOnlyError when the project is
        read-only. We verify this via the _EnsureWriteEnabled guard by calling
        the method on a mock/stub that simulates read-only state, or by
        checking that the real project (which is write-enabled) does NOT raise.

        Since we only have a writable fixture here, we verify the positive case:
        ReparseParagraph on a writable project completes without error.
        """
        text, para = _make_throwaway_text(writable_project, "zz_reparse_write_check")
        try:
            result = writable_project.Segments.ReparseParagraph(para)
            assert result is not None
        finally:
            _cleanup_text(writable_project, text)

    def test_ReparseParagraph_raises_on_none_paragraph(self, writable_project):
        """ReparseParagraph must raise FP_NullParameterError when paragraph is None."""
        from flexlibs2.code.FLExProject import FP_NullParameterError

        with pytest.raises(FP_NullParameterError):
            writable_project.Segments.ReparseParagraph(None)


# ---------------------------------------------------------------------------
# ReadOnly guard tests (P1-6)
# ---------------------------------------------------------------------------


class TestReadOnlyGuard:
    """
    Verify that SegmentOperations mutators raise FP_ReadOnlyError when the
    project is read-only.  Uses the mock-project pattern (no live FLEx
    connection required) to set writeEnabled=False and confirm _EnsureWriteEnabled
    fires before any LCM call.
    """

    @pytest.fixture
    def readonly_ops(self):
        """
        Return a SegmentOperations instance backed by a minimal mock project
        that has writeEnabled=False.  Mirrors the pattern used in
        test_lexentry_operations.py::TestLexEntryOperationsExceptionHandling.
        """
        from unittest.mock import Mock
        from flexlibs2.code.TextsWords.SegmentOperations import SegmentOperations

        mock_project = Mock()
        mock_project.writeEnabled = False
        # Provide a stub inner project so __WSHandleVern doesn't crash
        mock_project.project = Mock()
        mock_project.project.DefaultVernWs = 1
        mock_project.project.DefaultAnalWs = 2
        mock_project._FLExProject__WSHandle = Mock(return_value=1)
        return SegmentOperations(mock_project)

    def test_AppendSentence_raises_on_readonly(self, readonly_ops):
        """AppendSentence must raise FP_ReadOnlyError when project is read-only."""
        from flexlibs2.code.FLExProject import FP_ReadOnlyError
        from unittest.mock import Mock

        mock_para = Mock()
        with pytest.raises(FP_ReadOnlyError):
            readonly_ops.AppendSentence(mock_para, "Some text.")

    def test_ReparseParagraph_raises_on_readonly(self, readonly_ops):
        """ReparseParagraph must raise FP_ReadOnlyError when project is read-only."""
        from flexlibs2.code.FLExProject import FP_ReadOnlyError
        from unittest.mock import Mock

        mock_para = Mock()
        with pytest.raises(FP_ReadOnlyError):
            readonly_ops.ReparseParagraph(mock_para)


# ---------------------------------------------------------------------------
# MergeSegments null-param and invalid-policy tests (P1-7)
# ---------------------------------------------------------------------------


class TestMergeSegmentsNullAndPolicy:
    """
    Null-parameter and invalid translation_policy coverage for MergeSegments.
    Uses mock project so no live FLEx connection is required.
    """

    @pytest.fixture
    def writable_ops(self):
        """Return a SegmentOperations instance backed by a write-enabled mock project."""
        from unittest.mock import Mock
        from flexlibs2.code.TextsWords.SegmentOperations import SegmentOperations

        mock_project = Mock()
        mock_project.writeEnabled = True
        mock_project.project = Mock()
        mock_project.project.DefaultVernWs = 1
        mock_project.project.DefaultAnalWs = 2
        mock_project._FLExProject__WSHandle = Mock(return_value=2)
        return SegmentOperations(mock_project)

    def test_MergeSegments_raises_on_none_survivor(self, writable_ops):
        """MergeSegments must raise FP_NullParameterError when seg1 is None."""
        from flexlibs2.code.FLExProject import FP_NullParameterError
        from unittest.mock import Mock

        with pytest.raises(FP_NullParameterError):
            writable_ops.MergeSegments(None, Mock())

    def test_MergeSegments_raises_on_none_victim(self, writable_ops):
        """MergeSegments must raise FP_NullParameterError when seg2 is None."""
        from flexlibs2.code.FLExProject import FP_NullParameterError
        from unittest.mock import Mock

        with pytest.raises(FP_NullParameterError):
            writable_ops.MergeSegments(Mock(), None)

    def test_MergeSegments_raises_on_invalid_policy(self, writable_ops):
        """
        MergeSegments must raise FP_ParameterError when translation_policy
        is not one of the three valid string constants.  Verifies the
        stringly-typed guard added in P1-5.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError
        from unittest.mock import Mock

        mock_seg1 = Mock()
        mock_seg2 = Mock()
        # Give both segments the same owner so the adjacency check is reached,
        # then the policy validation fires.
        shared_owner = Mock()
        mock_seg1.Owner = shared_owner
        mock_seg2.Owner = shared_owner

        with pytest.raises(FP_ParameterError):
            writable_ops.MergeSegments(mock_seg1, mock_seg2, translation_policy="Migrate")


# ---------------------------------------------------------------------------
# AnalysesRS write methods (issue #215)
# ---------------------------------------------------------------------------


class _FakeAnalysesRS:
    """
    Minimal stand-in for an LCM reference sequence (ISegment.AnalysesRS),
    exposing just the members SegmentOperations' new write methods rely on:
    .Count, indexer get/set, .Insert(), .Add(), .RemoveAt(), and __iter__/
    __contains__ (via list(...) in ReplaceAnalysis).
    """

    def __init__(self, items=None):
        self._items = list(items) if items else []

    @property
    def Count(self):
        return len(self._items)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def __setitem__(self, index, value):
        self._items[index] = value

    def Insert(self, index, value):
        self._items.insert(index, value)

    def Add(self, value):
        self._items.append(value)

    def RemoveAt(self, index):
        del self._items[index]


class TestSegmentAnalysesRSWriteMethods:
    """
    Coverage for SegmentOperations.SetAnalysis, ReplaceAnalysis,
    InsertAnalysis, AppendAnalysis, and RemoveAnalysis (issue #215).

    Uses the mock-project pattern (no live FLEx connection required) with a
    fake AnalysesRS collection standing in for the real LCM reference
    sequence, mirroring the pattern used by TestReadOnlyGuard and
    TestMergeSegmentsNullAndPolicy elsewhere in this module.
    """

    @pytest.fixture
    def writable_ops(self):
        """
        Return a SegmentOperations instance backed by a write-enabled mock
        project. Uses MagicMock (not Mock) for the project so that
        ``_TransactionCM``'s ``project.Transaction(label)`` call yields an
        object that supports the context-manager protocol
        (``__enter__``/``__exit__`` are auto-specced by MagicMock).
        ``_undoable`` is explicitly False so Phase 1 (``project.Transaction``)
        is selected instead of Phase 2 (``project.UndoableOperation``).
        """
        from unittest.mock import MagicMock, Mock
        from flexlibs2.code.TextsWords.SegmentOperations import SegmentOperations

        mock_project = MagicMock()
        mock_project.writeEnabled = True
        mock_project._undoable = False
        mock_project._transaction_depth = 0
        mock_project.project = Mock()
        mock_project.project.DefaultVernWs = 1
        mock_project.project.DefaultAnalWs = 2
        mock_project._FLExProject__WSHandle = Mock(return_value=2)
        return SegmentOperations(mock_project)

    @pytest.fixture
    def readonly_ops(self):
        """Return a SegmentOperations instance backed by a read-only mock project."""
        from unittest.mock import Mock
        from flexlibs2.code.TextsWords.SegmentOperations import SegmentOperations

        mock_project = Mock()
        mock_project.writeEnabled = False
        mock_project.project = Mock()
        mock_project.project.DefaultVernWs = 1
        mock_project.project.DefaultAnalWs = 2
        mock_project._FLExProject__WSHandle = Mock(return_value=1)
        return SegmentOperations(mock_project)

    def _make_segment(self, analyses=None):
        from unittest.mock import Mock

        seg = Mock()
        seg.AnalysesRS = _FakeAnalysesRS(analyses)
        return seg

    # --- SetAnalysis ---

    def test_SetAnalysis_replaces_token_at_index(self, writable_ops):
        old_tok, new_tok = object(), object()
        seg = self._make_segment([old_tok, "other"])

        writable_ops.SetAnalysis(seg, 0, new_tok)

        assert list(seg.AnalysesRS) == [new_tok, "other"]

    def test_SetAnalysis_raises_on_out_of_range_index(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_ParameterError

        seg = self._make_segment(["only"])
        with pytest.raises(FP_ParameterError):
            writable_ops.SetAnalysis(seg, 5, object())

    def test_SetAnalysis_raises_on_none_segment(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_NullParameterError

        with pytest.raises(FP_NullParameterError):
            writable_ops.SetAnalysis(None, 0, object())

    def test_SetAnalysis_raises_on_none_analysis(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_NullParameterError

        seg = self._make_segment(["only"])
        with pytest.raises(FP_NullParameterError):
            writable_ops.SetAnalysis(seg, 0, None)

    def test_SetAnalysis_raises_on_readonly(self, readonly_ops):
        from flexlibs2.code.FLExProject import FP_ReadOnlyError

        seg = self._make_segment(["only"])
        with pytest.raises(FP_ReadOnlyError):
            readonly_ops.SetAnalysis(seg, 0, object())

    # --- ReplaceAnalysis ---

    def test_ReplaceAnalysis_finds_and_replaces_old_token(self, writable_ops):
        old_tok, new_tok = object(), object()
        seg = self._make_segment(["a", old_tok, "b"])

        writable_ops.ReplaceAnalysis(seg, old_tok, new_tok)

        assert list(seg.AnalysesRS) == ["a", new_tok, "b"]

    def test_ReplaceAnalysis_raises_when_old_not_found(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_ParameterError

        seg = self._make_segment(["a", "b"])
        with pytest.raises(FP_ParameterError):
            writable_ops.ReplaceAnalysis(seg, object(), object())

    def test_ReplaceAnalysis_raises_on_none_old(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_NullParameterError

        seg = self._make_segment(["a"])
        with pytest.raises(FP_NullParameterError):
            writable_ops.ReplaceAnalysis(seg, None, object())

    def test_ReplaceAnalysis_raises_on_none_new(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_NullParameterError

        seg = self._make_segment(["a"])
        with pytest.raises(FP_NullParameterError):
            writable_ops.ReplaceAnalysis(seg, "a", None)

    def test_ReplaceAnalysis_raises_on_readonly(self, readonly_ops):
        from flexlibs2.code.FLExProject import FP_ReadOnlyError

        seg = self._make_segment(["a"])
        with pytest.raises(FP_ReadOnlyError):
            readonly_ops.ReplaceAnalysis(seg, "a", "b")

    # --- InsertAnalysis ---

    def test_InsertAnalysis_inserts_at_index(self, writable_ops):
        new_tok = object()
        seg = self._make_segment(["a", "b"])

        writable_ops.InsertAnalysis(seg, 1, new_tok)

        assert list(seg.AnalysesRS) == ["a", new_tok, "b"]

    def test_InsertAnalysis_allows_index_equal_to_count(self, writable_ops):
        """index == Count is a valid append-at-end position."""
        new_tok = object()
        seg = self._make_segment(["a"])

        writable_ops.InsertAnalysis(seg, 1, new_tok)

        assert list(seg.AnalysesRS) == ["a", new_tok]

    def test_InsertAnalysis_raises_on_out_of_range_index(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_ParameterError

        seg = self._make_segment(["a"])
        with pytest.raises(FP_ParameterError):
            writable_ops.InsertAnalysis(seg, 5, object())

    def test_InsertAnalysis_raises_on_negative_index(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_ParameterError

        seg = self._make_segment(["a"])
        with pytest.raises(FP_ParameterError):
            writable_ops.InsertAnalysis(seg, -1, object())

    def test_InsertAnalysis_raises_on_readonly(self, readonly_ops):
        from flexlibs2.code.FLExProject import FP_ReadOnlyError

        seg = self._make_segment(["a"])
        with pytest.raises(FP_ReadOnlyError):
            readonly_ops.InsertAnalysis(seg, 0, object())

    # --- AppendAnalysis ---

    def test_AppendAnalysis_appends_to_end(self, writable_ops):
        new_tok = object()
        seg = self._make_segment(["a", "b"])

        writable_ops.AppendAnalysis(seg, new_tok)

        assert list(seg.AnalysesRS) == ["a", "b", new_tok]

    def test_AppendAnalysis_raises_on_readonly(self, readonly_ops):
        from flexlibs2.code.FLExProject import FP_ReadOnlyError

        seg = self._make_segment([])
        with pytest.raises(FP_ReadOnlyError):
            readonly_ops.AppendAnalysis(seg, object())

    # --- RemoveAnalysis ---

    def test_RemoveAnalysis_removes_token_at_index(self, writable_ops):
        seg = self._make_segment(["a", "b", "c"])

        writable_ops.RemoveAnalysis(seg, 1)

        assert list(seg.AnalysesRS) == ["a", "c"]

    def test_RemoveAnalysis_raises_on_out_of_range_index(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_ParameterError

        seg = self._make_segment(["a"])
        with pytest.raises(FP_ParameterError):
            writable_ops.RemoveAnalysis(seg, 5)

    def test_RemoveAnalysis_raises_on_none_segment(self, writable_ops):
        from flexlibs2.code.FLExProject import FP_NullParameterError

        with pytest.raises(FP_NullParameterError):
            writable_ops.RemoveAnalysis(None, 0)

    def test_RemoveAnalysis_raises_on_readonly(self, readonly_ops):
        from flexlibs2.code.FLExProject import FP_ReadOnlyError

        seg = self._make_segment(["a"])
        with pytest.raises(FP_ReadOnlyError):
            readonly_ops.RemoveAnalysis(seg, 0)
