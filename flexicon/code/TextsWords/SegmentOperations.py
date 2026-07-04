#
#   SegmentOperations.py
#
#   Class: SegmentOperations
#          Segment operations for FieldWorks Language Explorer projects
#          via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging
import clr

clr.AddReference("System")

from SIL.LCModel import (
    ISegment,
    ISegmentFactory,
    IStTxtPara,
)

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

from ..FLExProject import (
    FP_NullParameterError,
    FP_ParameterError,
    FP_ReadOnlyError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MergeSegments translation_policy constants
# Use these instead of bare strings to avoid silent routing to the wrong branch.
# ---------------------------------------------------------------------------

TRANSLATION_POLICY_MIGRATE = "migrate"
TRANSLATION_POLICY_DISCARD = "discard"
TRANSLATION_POLICY_REJECT = "reject"

_VALID_TRANSLATION_POLICIES = {
    TRANSLATION_POLICY_MIGRATE,
    TRANSLATION_POLICY_DISCARD,
    TRANSLATION_POLICY_REJECT,
}


class SegmentOperations(BaseOperations):
    """
    This class provides operations for managing segments in a FieldWorks project.

    Segments represent the units of text analysis in FLEx, typically sentences
    or clauses within paragraphs. Each segment can have baseline text, analyses,
    translations (free and literal), and notes.

    The write path follows the LCM idiom:
    1. Edit IStTxtPara.Contents (via TsStringBuilder) first.
    2. Assign builder.GetString() to para.Contents - this fires ContentsSideEffects
       which triggers AnalysisAdjuster to reconcile segment offsets automatically.
    3. Then update SegmentsOS (Add/Insert/Remove) as needed.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all segments in a paragraph
        para = project.Object(para_hvo)
        for segment in project.Segments.GetAll(para):
            baseline = project.Segments.GetBaselineText(segment)
            print(baseline)

        # Append a new sentence to a paragraph
        new_seg = project.Segments.AppendSentence(para, "A new sentence.")

        # Split a segment at a character offset within that segment
        seg1, seg2 = project.Segments.SplitSegment(new_seg, 5)

        # Merge two adjacent segments (migrates translations by default)
        merged = project.Segments.MergeSegments(seg1, seg2)

        # Set translations on a segment
        project.Segments.SetFreeTranslation(merged, "In the beginning...")
        project.Segments.SetLiteralTranslation(merged, "In-the beginning...")

        # Reparse a paragraph from its Contents (use only to repair corruption)
        project.Segments.ReparseParagraph(para)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize SegmentOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """Specify which sequence to reorder for segment analyses (reference sequence)."""
        return parent.AnalysesRS

    def __WSHandle(self, wsHandle):
        """
        Internal helper for writing system handles (analysis).

        Args:
            wsHandle: Writing system handle or None for default analysis WS.

        Returns:
            int: The writing system handle to use.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    def __WSHandleVern(self, wsHandle):
        """
        Internal helper for writing system handles (vernacular).

        Args:
            wsHandle: Writing system handle or None for default vernacular WS.

        Returns:
            int: The writing system handle to use.
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)

    def __GetParagraphObject(self, para_or_hvo):
        """
        Internal helper to get paragraph object from HVO or object.

        Args:
            para_or_hvo: IStTxtPara object or HVO integer.

        Returns:
            IStTxtPara: The paragraph object.
        """
        if isinstance(para_or_hvo, int):
            return self.project.Object(para_or_hvo)
        return para_or_hvo

    def __GetSegmentObject(self, segment_or_hvo):
        """
        Internal helper to get segment object from HVO or object.

        Args:
            segment_or_hvo: ISegment object or HVO integer.

        Returns:
            ISegment: The segment object.
        """
        if isinstance(segment_or_hvo, int):
            return self.project.Object(segment_or_hvo)
        return segment_or_hvo

    def __GetSegmentFactory(self):
        """Return the ISegmentFactory from the service locator."""
        return self.project.project.ServiceLocator.GetService(ISegmentFactory)

    # ========== READ METHODS ==========

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, paragraph_or_hvo):
        """
        Get all segments in a paragraph.

        Args:
            paragraph_or_hvo: The IStTxtPara object or HVO.

        Yields:
            ISegment: Each segment in the paragraph.

        Raises:
            FP_NullParameterError: If paragraph_or_hvo is None.

        Example:
            >>> para = project.Object(para_hvo)
            >>> for segment in project.Segments.GetAll(para):
            ...     text = project.Segments.GetBaselineText(segment)
            ...     print(text)
            In the beginning God created the heavens and the earth.
            Now the earth was formless and empty.

        See Also:
            GetBaselineText, GetFreeTranslation, GetAnalyses
        """
        self._ValidateParam(paragraph_or_hvo, "paragraph_or_hvo")

        para_obj = self.__GetParagraphObject(paragraph_or_hvo)
        segments = list(para_obj.SegmentsOS)

        for segment in segments:
            yield segment

    @OperationsMethod
    def GetAnalyses(self, segment_or_hvo):
        """
        Get all analyses (wordforms and their linguistic analyses) for a segment.

        Args:
            segment_or_hvo: The ISegment object or HVO.

        Returns:
            list: List of IAnalysis objects representing the wordforms in the segment.

        Raises:
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> analyses = project.Segments.GetAnalyses(segment)
            >>> print(f"Segment has {len(analyses)} wordforms")
            Segment has 5 wordforms

        See Also:
            GetAll, GetBaselineText

        Notes:
            Each analysis can be an IWfiWordform, IWfiGloss, or IWfiAnalysis object.
            These represent different levels of linguistic analysis for each word.
        """
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)
        analyses = list(segment_obj.AnalysesRS)
        return analyses

    @OperationsMethod
    def GetBaselineText(self, segment_or_hvo):
        """
        Get the baseline text of a segment (the original text in the vernacular language).

        Args:
            segment_or_hvo: The ISegment object or HVO.

        Returns:
            str: The baseline text, or empty string if not set.

        Raises:
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> text = project.Segments.GetBaselineText(segment)
            >>> print(text)
            In the beginning God created the heavens and the earth.

        See Also:
            GetFreeTranslation, GetLiteralTranslation, GetAnalyses
        """
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)
        # ISegment.BaselineText is ITsString (WS already resolved by LCM),
        # not ITsMultiString.  Calling .get_String(ws) on it raises
        # AttributeError at runtime.  See issue #170.
        return segment_obj.BaselineText.Text or ""

    @OperationsMethod
    def SetBaselineText(self, segment_or_hvo, text, wsHandle=None):
        """
        Set the baseline text of a segment by editing the owning paragraph Contents.

        The correct write idiom is to edit IStTxtPara.Contents via a TsStrBldr;
        ContentsSideEffects then fires AnalysisAdjuster.AdjustAnalysis which
        reconciles segment offsets automatically.

        Args:
            segment_or_hvo: The ISegment object or HVO.
            text: The baseline text to set.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If segment_or_hvo is None.
            FP_ParameterError: If segment has no owning paragraph.

        Example:
            >>> segment = segments[0]
            >>> project.Segments.SetBaselineText(segment, "In the beginning...")

        See Also:
            GetBaselineText, SetFreeTranslation, SetLiteralTranslation
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)
        ws = self.__WSHandleVern(wsHandle)

        para = segment_obj.Paragraph
        if para is None:
            raise FP_ParameterError("Segment has no owning paragraph; cannot write BaselineText")
        begin = segment_obj.BeginOffset
        end = segment_obj.EndOffset
        bldr = para.Contents.GetBldr()
        new_run = TsStringUtils.MakeString(text, ws)
        bldr.ReplaceTsString(begin, end, new_run)
        para.Contents = bldr.GetString()

    @OperationsMethod
    def GetFreeTranslation(self, segment_or_hvo, wsHandle=None):
        """
        Get the free translation for a segment.

        Args:
            segment_or_hvo: The ISegment object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The free translation text, or empty string if not set.

        Raises:
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> trans = project.Segments.GetFreeTranslation(segment)
            >>> print(trans)
            In the beginning God created the heavens and the earth.

        See Also:
            SetFreeTranslation, GetLiteralTranslation, GetBaselineText
        """
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)
        ws = self.__WSHandle(wsHandle)

        if segment_obj.FreeTranslation:
            text = ITsString(segment_obj.FreeTranslation.get_String(ws)).Text
            return text or ""
        return ""

    @OperationsMethod
    def SetFreeTranslation(self, segment_or_hvo, text, wsHandle=None):
        """
        Set the free translation for a segment.

        Args:
            segment_or_hvo: The ISegment object or HVO.
            text: The free translation text to set.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> project.Segments.SetFreeTranslation(segment, "In the beginning God created...")

        See Also:
            GetFreeTranslation, SetLiteralTranslation, SetBaselineText
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)
        ws = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(text, ws)
        segment_obj.FreeTranslation.set_String(ws, mkstr)

    @OperationsMethod
    def GetLiteralTranslation(self, segment_or_hvo, wsHandle=None):
        """
        Get the literal (word-for-word) translation of a segment.

        Args:
            segment_or_hvo: The ISegment object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The literal translation text, or empty string if not set.

        Raises:
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> trans = project.Segments.GetLiteralTranslation(segment)
            >>> print(trans)
            In-the beginning God created the-heavens and-the-earth

        See Also:
            SetLiteralTranslation, GetFreeTranslation, GetBaselineText
        """
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)
        ws = self.__WSHandle(wsHandle)

        if segment_obj.LiteralTranslation:
            text = ITsString(segment_obj.LiteralTranslation.get_String(ws)).Text
            return text or ""
        return ""

    @OperationsMethod
    def SetLiteralTranslation(self, segment_or_hvo, text, wsHandle=None):
        """
        Set the literal (word-for-word) translation of a segment.

        Args:
            segment_or_hvo: The ISegment object or HVO.
            text: The literal translation text to set.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> project.Segments.SetLiteralTranslation(segment, "In-the beginning God created...")

        See Also:
            GetLiteralTranslation, SetFreeTranslation, SetBaselineText
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)
        ws = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(text, ws)
        segment_obj.LiteralTranslation.set_String(ws, mkstr)

    @OperationsMethod
    def GetNotes(self, segment_or_hvo):
        """
        Get all notes associated with a segment.

        Args:
            segment_or_hvo: The ISegment object or HVO.

        Returns:
            list: List of note objects associated with the segment.

        Raises:
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> notes = project.Segments.GetNotes(segment)
            >>> print(f"Segment has {len(notes)} notes")
            Segment has 2 notes

        See Also:
            GetAll, GetBaselineText, GetFreeTranslation
        """
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)

        if hasattr(segment_obj, "NotesOS"):
            notes = list(segment_obj.NotesOS)
            return notes
        return []

    # ========== WRITE METHODS ==========

    @OperationsMethod
    def AppendSentence(self, paragraph_or_hvo, text, wsHandle=None):
        """
        Append a new sentence to a paragraph, creating a new segment.

        Edits IStTxtPara.Contents first (firing AnalysisAdjuster on existing
        segments), then adds the new ISegment to SegmentsOS.

        A sentence terminator ('. ') is automatically inserted before the new
        text when the current paragraph Contents is non-empty and does not
        already end with one of {. ! ?}. When the paragraph is empty, the
        text is written directly.

        Args:
            paragraph_or_hvo: The IStTxtPara object or HVO.
            text: The sentence text to append. Must be non-empty.
            wsHandle: Optional writing system handle. Defaults to project
                      default vernacular WS.

        Returns:
            ISegment: The newly created segment object.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If paragraph_or_hvo or text is None.
            FP_ParameterError: If text is empty or paragraph is invalid.

        Example:
            >>> para = project.Object(para_hvo)
            >>> seg = project.Segments.AppendSentence(para, "A new sentence.")
            >>> print(project.Segments.GetBaselineText(seg))
            A new sentence.

        See Also:
            SplitSegment, MergeSegments, ReparseParagraph
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(paragraph_or_hvo, "paragraph_or_hvo")
        self._ValidateParam(text, "text")

        text_str = text.strip() if isinstance(text, str) else str(text).strip()
        if not text_str:
            raise FP_ParameterError("text cannot be empty")

        para = self.__GetParagraphObject(paragraph_or_hvo)
        ws = self.__WSHandleVern(wsHandle)

        with self._TransactionCM("Append sentence"):
            # --- Step 1: edit Contents ---
            bldr = para.Contents.GetBldr()
            current_length = para.Contents.Length

            if current_length > 0:
                # Check the last character of the current contents
                last_char_pos = current_length - 1
                last_char = para.Contents.Text[last_char_pos] if para.Contents.Text else ""

                if last_char not in (".", "!", "?"):
                    # Insert ". " as sentence terminator
                    terminator = TsStringUtils.MakeString(". ", ws)
                    bldr.ReplaceTsString(current_length, current_length, terminator)
                    # Recalculate insertion point after terminator
                    insert_at = current_length + 2
                else:
                    # Already terminated — just insert a space separator
                    sep = TsStringUtils.MakeString(" ", ws)
                    bldr.ReplaceTsString(current_length, current_length, sep)
                    insert_at = current_length + 1

                new_text_ts = TsStringUtils.MakeString(text_str, ws)
                bldr.ReplaceTsString(insert_at, insert_at, new_text_ts)
            else:
                # Paragraph is empty — write text directly
                new_text_ts = TsStringUtils.MakeString(text_str, ws)
                bldr.ReplaceTsString(0, 0, new_text_ts)

            # Assign Contents — fires ContentsSideEffects -> AnalysisAdjuster on
            # existing segments, setting their BeginOffset/EndOffset correctly.
            para.Contents = bldr.GetString()

            # --- Step 2: add new segment to SegmentsOS ---
            factory = self.__GetSegmentFactory()
            seg = factory.Create()
            para.SegmentsOS.Add(seg)
            # AnalysisAdjuster (fired by the Contents setter above) will set
            # seg.BeginOffset / seg.EndOffset when the paragraph is re-parsed.

            return seg

    @OperationsMethod
    def Delete(self, segment_or_hvo):
        """
        Delete a segment from its paragraph.

        Removes the segment from its parent paragraph's segment collection.
        All analyses, translations, and notes associated with the segment
        are also deleted.

        Args:
            segment_or_hvo: The ISegment object or HVO.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If segment_or_hvo is None.
            FP_ParameterError: If segment has no owning paragraph.

        Example:
            >>> segment = segments[0]
            >>> project.Segments.Delete(segment)

        See Also:
            AppendSentence, Exists, MergeSegments
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)

        owner = self._GetTypedOwner(segment_obj)
        if owner is None:
            raise FP_ParameterError("Segment has no owning paragraph")
        owner.SegmentsOS.Remove(segment_obj)

    @OperationsMethod
    def SplitSegment(self, segment_or_hvo, offset_within_segment):
        """
        Split a segment at a character offset measured from the start of the segment.

        Inserts a sentence terminator ('. ') into IStTxtPara.Contents at the
        absolute position corresponding to the split, then adds the new ISegment
        to SegmentsOS. AnalysisAdjuster (fired by the Contents setter) shifts
        all subsequent segment offsets right by 2.

        Args:
            segment_or_hvo: The ISegment object or HVO to split.
            offset_within_segment: Character offset from the segment's BeginOffset
                where the split occurs. Must satisfy:
                0 < offset_within_segment < (seg.EndOffset - seg.BeginOffset).

        Returns:
            tuple: (seg, new_seg) - the original (now shorter) segment and the
                   newly inserted segment that follows it.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If segment_or_hvo is None.
            FP_ParameterError: If offset_within_segment is out of range or
                               segment has no owning paragraph.

        Example:
            >>> seg = segments[0]
            >>> print(project.Segments.GetBaselineText(seg))
            In the beginning God created the heavens.
            >>> seg1, seg2 = project.Segments.SplitSegment(seg, 17)
            >>> print(project.Segments.GetBaselineText(seg1))
            In the beginning
            >>> print(project.Segments.GetBaselineText(seg2))
            God created the heavens.

        See Also:
            MergeSegments, AppendSentence, ReparseParagraph
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        seg = self.__GetSegmentObject(segment_or_hvo)

        seg_len = seg.EndOffset - seg.BeginOffset
        if offset_within_segment is None or not (0 < offset_within_segment < seg_len):
            raise FP_ParameterError(
                f"offset_within_segment must be between 1 and {seg_len - 1} "
                f"(exclusive); got {offset_within_segment}"
            )

        para = seg.Paragraph
        if para is None:
            raise FP_ParameterError("Segment has no owning paragraph")

        absolute_offset = seg.BeginOffset + offset_within_segment

        # --- Step 1: edit Contents ---
        # Resolve the paragraph's vernacular WS from the existing text run so
        # the inserted terminator uses the same writing system as its neighbours.
        ws = self.__WSHandleVern(None)
        with self._TransactionCM("Split segment"):
            bldr = para.Contents.GetBldr()
            terminator = TsStringUtils.MakeString(". ", ws)
            bldr.ReplaceTsString(absolute_offset, absolute_offset, terminator)
            # Assign — fires AnalysisAdjuster which shifts seg3+ offsets right by 2
            para.Contents = bldr.GetString()

            # --- Step 2: insert new segment into SegmentsOS ---
            idx = para.SegmentsOS.IndexOf(seg)
            factory = self.__GetSegmentFactory()
            new_seg = factory.Create()
            para.SegmentsOS.Insert(idx + 1, new_seg)

            return (seg, new_seg)

    @OperationsMethod
    def MergeSegments(self, seg1_or_hvo, seg2_or_hvo, translation_policy="migrate"):
        """
        Merge two adjacent segments into one, removing the inter-segment boundary.

        Edits IStTxtPara.Contents first (removing the terminator+whitespace
        between the two segments), then removes seg2 from SegmentsOS.
        AnalysisAdjuster (fired by the Contents setter) shifts all subsequent
        segment offsets left automatically.

        Args:
            seg1_or_hvo: The first (earlier) ISegment object or HVO.
            seg2_or_hvo: The second (later) ISegment object or HVO. Must be
                         immediately after seg1 in SegmentsOS.
            translation_policy (str): One of:
                - TRANSLATION_POLICY_MIGRATE / 'migrate' (default): Concatenate
                  seg2's FreeTranslation and LiteralTranslation into seg1's,
                  joined by ' / ' per writing system that has content. Also moves
                  all Notes from seg2.NotesOS into seg1.NotesOS via re-parenting.
                  Migration happens BEFORE seg2 is removed.
                - TRANSLATION_POLICY_DISCARD / 'discard': Drop seg2's
                  translations and notes silently.
                - TRANSLATION_POLICY_REJECT / 'reject': Raise FP_ParameterError
                  if seg2 has any non-empty FreeTranslation, LiteralTranslation
                  (across ALL writing systems), or Notes. Caller must explicitly
                  pass 'migrate' or 'discard' to proceed.

        Returns:
            ISegment: seg1 (the survivor segment).

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If either segment is None.
            FP_ParameterError: If segments are not adjacent, not in the same
                paragraph, or 'reject' policy triggered.

        Example:
            >>> seg1 = segments[0]
            >>> seg2 = segments[1]
            >>> merged = project.Segments.MergeSegments(seg1, seg2)
            >>> print(project.Segments.GetBaselineText(merged))
            In the beginning God created the heavens and the earth.

        See Also:
            SplitSegment, AppendSentence, ReparseParagraph

        Notes:
            All wordform analyses on seg2 are lost. Prefer 'migrate' (default)
            to preserve translations across the merge.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(seg1_or_hvo, "seg1_or_hvo")
        self._ValidateParam(seg2_or_hvo, "seg2_or_hvo")

        seg1 = self.__GetSegmentObject(seg1_or_hvo)
        seg2 = self.__GetSegmentObject(seg2_or_hvo)

        # Validate translation_policy early — before any LCM calls — so a
        # typo like 'Migrate' raises immediately on a plain mock without needing
        # a real SegmentsOS collection.
        if translation_policy not in _VALID_TRANSLATION_POLICIES:
            raise FP_ParameterError(
                f"translation_policy must be one of {_VALID_TRANSLATION_POLICIES!r}, "
                f"got {translation_policy!r}"
            )

        if seg1.Owner != seg2.Owner:
            raise FP_ParameterError("Segments must be in the same paragraph")

        para = self._GetTypedOwner(seg1)
        if para is None:
            raise FP_ParameterError("Segments have no valid owner paragraph")

        segments_list = list(para.SegmentsOS)
        idx1 = segments_list.index(seg1)
        idx2 = segments_list.index(seg2)

        # Ensure seg1 is the earlier segment
        if idx1 > idx2:
            seg1, seg2 = seg2, seg1
            idx1, idx2 = idx2, idx1

        if idx2 != idx1 + 1:
            raise FP_ParameterError(
                f"Segments must be adjacent; seg1 is at index {idx1}, "
                f"seg2 is at index {idx2}"
            )

        # Enforce translation_policy
        if translation_policy == TRANSLATION_POLICY_REJECT:
            has_content = False
            # Check ALL writing systems in both FreeTranslation and LiteralTranslation,
            # not just the default WS, to honour the docstring promise.
            # IMultiString.GetStringFromIndex(i) returns (ITsString, ws_int) tuple.
            for attr in ("FreeTranslation", "LiteralTranslation"):
                ms = getattr(seg2, attr, None)
                if ms is None:
                    continue
                for i in range(ms.StringCount):
                    ts, _ws = ms.GetStringFromIndex(i)
                    text_val = ts.Text if hasattr(ts, "Text") else None
                    if text_val:
                        has_content = True
                        break
                if has_content:
                    break
            # Also check Notes
            if not has_content:
                notes = list(seg2.NotesOS) if hasattr(seg2, "NotesOS") else []
                if notes:
                    has_content = True
            if has_content:
                raise FP_ParameterError(
                    "seg2 has non-empty translations/notes and translation_policy='reject'. "
                    "Pass translation_policy='migrate' to concatenate into seg1, or "
                    "'discard' to drop them."
                )

        with self._TransactionCM("Merge segments"):
            if translation_policy == TRANSLATION_POLICY_MIGRATE:
                # Migrate FreeTranslation, LiteralTranslation, and Notes for all WS
                self.__MigrateTranslations(seg1, seg2)

            # TRANSLATION_POLICY_DISCARD: do nothing — seg2's data is lost on removal

            # --- Step 1: edit Contents to remove the inter-segment boundary ---
            bldr = para.Contents.GetBldr()
            # Remove characters from end of seg1 (the terminator) through start of seg2
            # seg1.EndOffset is the position just after seg1's last char (includes terminator)
            # seg2.BeginOffset is the first char of seg2's text
            bldr.Replace(seg1.EndOffset, seg2.BeginOffset, "", None)
            # Assign — fires AnalysisAdjuster which shifts seg3+ offsets left
            para.Contents = bldr.GetString()

            # --- Step 2: remove seg2 from SegmentsOS if it still exists ---
            if seg2 in list(para.SegmentsOS):
                para.SegmentsOS.Remove(seg2)

            return seg1

    def __MigrateTranslations(self, seg1, seg2):
        """
        Concatenate seg2's FreeTranslation and LiteralTranslation into seg1
        per writing system that has content, joined by ' / '. Also moves all
        Notes from seg2's NotesOS into seg1's NotesOS (re-parenting ownership).

        Args:
            seg1: The survivor segment.
            seg2: The segment being merged away.
        """
        # Collect all WS handles present in either FreeTranslation or LiteralTranslation.
        # IMultiString.GetStringFromIndex(i) returns (ITsString, ws_int) tuple.
        ws_set = set()
        for seg in (seg1, seg2):
            for attr in ("FreeTranslation", "LiteralTranslation"):
                ms = getattr(seg, attr, None)
                if ms is not None:
                    for i in range(ms.StringCount):
                        _ts, ws = ms.GetStringFromIndex(i)
                        ws_set.add(ws)

        for ws in ws_set:
            # FreeTranslation
            if seg1.FreeTranslation and seg2.FreeTranslation:
                t1 = ITsString(seg1.FreeTranslation.get_String(ws)).Text or ""
                t2 = ITsString(seg2.FreeTranslation.get_String(ws)).Text or ""
                if t2:
                    merged_text = (t1 + " / " + t2) if t1 else t2
                    mkstr = TsStringUtils.MakeString(merged_text, ws)
                    seg1.FreeTranslation.set_String(ws, mkstr)

            # LiteralTranslation
            if seg1.LiteralTranslation and seg2.LiteralTranslation:
                t1 = ITsString(seg1.LiteralTranslation.get_String(ws)).Text or ""
                t2 = ITsString(seg2.LiteralTranslation.get_String(ws)).Text or ""
                if t2:
                    merged_text = (t1 + " / " + t2) if t1 else t2
                    mkstr = TsStringUtils.MakeString(merged_text, ws)
                    seg1.LiteralTranslation.set_String(ws, mkstr)

        # Notes: move all ICmBaseAnnotation objects from seg2.NotesOS to seg1.NotesOS.
        # ILcmOwningSequence.MoveTo(srcStart, srcEnd, dest, destStart) re-parents
        # ownership without creating new objects.
        if hasattr(seg2, "NotesOS") and hasattr(seg1, "NotesOS"):
            notes2 = list(seg2.NotesOS)
            if notes2:
                dest_index = seg1.NotesOS.Count
                seg2.NotesOS.MoveTo(0, len(notes2) - 1, seg1.NotesOS, dest_index)

    @OperationsMethod
    def ReparseParagraph(self, paragraph_or_hvo):
        """
        Re-derive segment offsets and wordform analyses for a paragraph by
        reassigning para.Contents to itself; FreeTranslation, LiteralTranslation,
        and Notes on surviving segments are preserved.

        Implementation: assigns para.Contents back to itself. That single setter
        assignment fires ContentsSideEffects -> AnalysisAdjuster, which is an
        offset reconciler -- it rebuilds AnalysesRS (wordform analyses) but does
        NOT touch FreeTranslation, LiteralTranslation, or NotesOS on surviving
        segments (those are independently-owned LCM objects with no dependency
        on Contents). When the assignment is a self-assignment (the only path
        through this method), segment objects survive with identical offsets,
        so their translations are never cleared. No regex, no manual
        SegmentsOS.Clear(), no factory.Create() calls are needed or used.

        Args:
            paragraph_or_hvo: The IStTxtPara object or HVO.

        Returns:
            The freshly rebuilt SegmentsOS collection (ILcmOwningSequence).

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If paragraph_or_hvo is None.

        Example:
            >>> para = project.Object(para_hvo)
            >>> segs = project.Segments.ReparseParagraph(para)
            >>> print(f"Rebuilt {segs.Count} segments")
            Rebuilt 3 segments

        See Also:
            SplitSegment, MergeSegments, AppendSentence

        Warning:
            This destroys all existing wordform analyses (AnalysesRS) on the
            paragraph. FreeTranslation, LiteralTranslation, and Notes are NOT
            cleared. Use SplitSegment or MergeSegments for non-destructive
            structural edits.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(paragraph_or_hvo, "paragraph_or_hvo")

        para = self.__GetParagraphObject(paragraph_or_hvo)

        # Snapshot the current Contents and reassign. The setter fires
        # ContentsSideEffects -> AnalysisAdjuster which re-derives SegmentsOS
        # entirely from the punctuation pattern in the text.
        snapshot = para.Contents
        para.Contents = snapshot

        return para.SegmentsOS

    # ========== QUERY/VALIDATION METHODS ==========

    @OperationsMethod
    def Exists(self, paragraph_or_hvo, segment_or_hvo):
        """
        Check if a segment exists in a paragraph.

        Args:
            paragraph_or_hvo: The IStTxtPara object or HVO.
            segment_or_hvo: The ISegment object or HVO to check for.

        Returns:
            bool: True if the segment exists in the paragraph, False otherwise.

        Raises:
            FP_NullParameterError: If paragraph_or_hvo or segment_or_hvo is None.

        Example:
            >>> para = project.Object(para_hvo)
            >>> segment = segments[0]
            >>> exists = project.Segments.Exists(para, segment)
            >>> print(exists)
            True

        See Also:
            AppendSentence, Delete, GetAll
        """
        self._ValidateParam(paragraph_or_hvo, "paragraph_or_hvo")
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        para_obj = self.__GetParagraphObject(paragraph_or_hvo)
        segment_obj = self.__GetSegmentObject(segment_or_hvo)

        segments_list = list(para_obj.SegmentsOS)
        return segment_obj in segments_list

    @OperationsMethod
    def GetBeginOffset(self, segment_or_hvo):
        """
        Get the beginning character offset of a segment within its paragraph.

        Args:
            segment_or_hvo: The ISegment object or HVO.

        Returns:
            int: The beginning offset (0-based character position).

        Raises:
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> offset = project.Segments.GetBeginOffset(segment)
            >>> print(offset)
            0

        See Also:
            GetEndOffset
        """
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)

        if hasattr(segment_obj, "BeginOffset"):
            return segment_obj.BeginOffset
        return 0

    @OperationsMethod
    def GetEndOffset(self, segment_or_hvo):
        """
        Get the ending character offset of a segment within its paragraph.

        Args:
            segment_or_hvo: The ISegment object or HVO.

        Returns:
            int: The ending offset (0-based character position).

        Raises:
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> offset = project.Segments.GetEndOffset(segment)
            >>> print(offset)
            45

        See Also:
            GetBeginOffset
        """
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)

        if hasattr(segment_obj, "EndOffset"):
            return segment_obj.EndOffset
        return 0

    @OperationsMethod
    def IsLabel(self, segment_or_hvo):
        """
        Check if a segment is marked as a label (section header).

        Args:
            segment_or_hvo: The ISegment object or HVO.

        Returns:
            bool: True if the segment is a label, False otherwise.

        Raises:
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> is_header = project.Segments.IsLabel(segment)
            >>> print(is_header)
            False

        See Also:
            SetIsLabel
        """
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)

        if hasattr(segment_obj, "IsLabel"):
            return segment_obj.IsLabel
        return False

    @OperationsMethod
    def SetIsLabel(self, segment_or_hvo, is_label):
        """
        Set whether a segment is a label (section header).

        Args:
            segment_or_hvo: The ISegment object or HVO.
            is_label: Boolean value - True to mark as label, False for regular segment.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If segment_or_hvo is None.

        Example:
            >>> segment = segments[0]
            >>> project.Segments.SetIsLabel(segment, True)

        See Also:
            IsLabel
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(segment_or_hvo, "segment_or_hvo")

        segment_obj = self.__GetSegmentObject(segment_or_hvo)

        if hasattr(segment_obj, "IsLabel"):
            segment_obj.IsLabel = bool(is_label)

    @OperationsMethod
    def ValidateSegments(self, paragraph_or_hvo):
        """
        Validate the integrity of all segments in a paragraph.

        Checks that segments are properly structured with valid offsets,
        non-overlapping ranges, and complete coverage of the paragraph text.

        Args:
            paragraph_or_hvo: The IStTxtPara object or HVO.

        Returns:
            dict: Validation results with keys:
                - 'valid': bool - Overall validity
                - 'errors': list - List of error messages
                - 'warnings': list - List of warning messages
                - 'segment_count': int - Number of segments checked

        Raises:
            FP_NullParameterError: If paragraph_or_hvo is None.

        Example:
            >>> para = project.Object(para_hvo)
            >>> result = project.Segments.ValidateSegments(para)
            >>> if result['valid']:
            ...     print("All segments are valid")
            ... else:
            ...     for error in result['errors']:
            ...         print(f"Error: {error}")

        See Also:
            ReparseParagraph, GetBeginOffset, GetEndOffset
        """
        self._ValidateParam(paragraph_or_hvo, "paragraph_or_hvo")

        para_obj = self.__GetParagraphObject(paragraph_or_hvo)
        segments_list = list(para_obj.SegmentsOS)

        errors = []
        warnings = []

        if not segments_list:
            warnings.append("Paragraph has no segments")
            return {"valid": True, "errors": errors, "warnings": warnings, "segment_count": 0}

        prev_end = -1
        for i, segment in enumerate(segments_list):
            if not hasattr(segment, "BeginOffset") or not hasattr(segment, "EndOffset"):
                warnings.append(f"Segment {i} missing offset attributes")
                continue

            begin = segment.BeginOffset
            end = segment.EndOffset

            if begin < 0 or end < 0:
                errors.append(f"Segment {i} has negative offset (begin={begin}, end={end})")

            if begin >= end:
                errors.append(f"Segment {i} has invalid offsets (begin={begin} >= end={end})")

            if prev_end >= 0:
                if begin > prev_end + 1:
                    warnings.append(
                        f"Gap between segment {i-1} and {i} "
                        f"(prev_end={prev_end}, begin={begin})"
                    )
                elif begin < prev_end:
                    errors.append(
                        f"Overlap between segment {i-1} and {i} "
                        f"(prev_end={prev_end}, begin={begin})"
                    )

            baseline = self.GetBaselineText(segment)
            if not baseline:
                warnings.append(f"Segment {i} has empty baseline text")

            prev_end = end

        valid = len(errors) == 0

        return {"valid": valid, "errors": errors, "warnings": warnings, "segment_count": len(segments_list)}

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a segment.

        Args:
            item: The ISegment object.

        Returns:
            dict: Dictionary of syncable properties with their values.

        Example:
            >>> props = project.Segments.GetSyncableProperties(segment)
            >>> print(props['BaselineText'])
            {'en': 'In the beginning...'}
            >>> print(props['IsLabel'])
            False
            >>> print(props['BeginOffset'])
            0

        Notes:
            - MultiString properties: FreeTranslation, LiteralTranslation
            - BaselineText is ITsString (single-WS, read-only computed from para Contents)
            - Boolean property: IsLabel
            - Integer properties: BeginOffset, EndOffset
            - Does NOT include analyses (those are children)
        """
        props = {}

        # BaselineText is ITsString (single-WS, read-only computed from para Contents).
        if hasattr(item, "BaselineText") and item.BaselineText:
            bt = item.BaselineText
            ws_handle = bt.get_Properties(0).GetIntPropValues(1, 0)[0]
            props["BaselineText"] = {ws_handle: bt.Text or ""}

        # FreeTranslation and LiteralTranslation are genuine IMultiString fields.
        if hasattr(item, "FreeTranslation") and item.FreeTranslation:
            props["FreeTranslation"] = self.project.GetMultiStringDict(item.FreeTranslation)

        if hasattr(item, "LiteralTranslation") and item.LiteralTranslation:
            props["LiteralTranslation"] = self.project.GetMultiStringDict(item.LiteralTranslation)

        if hasattr(item, "IsLabel"):
            props["IsLabel"] = bool(item.IsLabel)

        if hasattr(item, "BeginOffset"):
            props["BeginOffset"] = int(item.BeginOffset)

        if hasattr(item, "EndOffset"):
            props["EndOffset"] = int(item.EndOffset)

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two segments for differences.

        Args:
            item1: First segment object (from project 1)
            item2: Second segment object (from project 2)
            ops1: Optional SegmentOperations instance for project 1 (defaults to self)
            ops2: Optional SegmentOperations instance for project 2 (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
                - is_different (bool): True if segments differ, False if identical
                - differences_dict (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> is_diff, diffs = ops1.CompareTo(seg1, seg2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} != {val2}")
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}
        all_keys = set(props1.keys()) | set(props2.keys())

        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            if self.project._CompareValues(val1, val2):
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return (is_different, differences)
