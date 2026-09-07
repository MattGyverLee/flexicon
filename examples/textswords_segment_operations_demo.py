#!/usr/bin/env python3
"""
SegmentOperations Demo - flexicon

Demonstrates the SegmentOperations public API introduced in issues #172 / #174.

Key changes from the old CRUD template (auto-generated):
- GetAll(paragraph) requires a paragraph argument - segments are owned by paragraphs.
- Create() was removed - segments are created implicitly via AppendSentence().
- ReparseParagraph() replaces the old RebuildSegments() for full reparse from Contents.

Operations demonstrated:
    AppendSentence  -- append a sentence to a paragraph (creates the new segment)
    SplitSegment    -- split a segment at a character offset
    MergeSegments   -- merge two adjacent segments (with translation_policy control)
    ReparseParagraph -- force re-derive all segments from paragraph Contents
    GetAll          -- enumerate segments in a paragraph
    GetBaselineText -- read back the segment text
    SetFreeTranslation / GetFreeTranslation -- per-segment translation round-trip
    Delete          -- remove a segment from its paragraph

Requirements:
  - FieldWorks installed with SIL.LCModel available
  - A writable project (tries "Sena 3" by default)
  - Python.NET runtime
"""

from flexicon import FLExProject, FLExInitialize, FLExCleanup

_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_project():
    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=True)
            print(f"  Opened project: {name}")
            return project
        except Exception:
            continue
    return None


def _make_throwaway_text(project, title="zz_seg_demo"):
    """Create a fresh IStText with one empty paragraph for demo use."""
    text = project.Texts.Create(title)
    para_list = list(text.ContentsOA.ParagraphsOS) if text.ContentsOA else []
    if not para_list:
        project.Paragraphs.Create(text.ContentsOA, "")
        para_list = list(text.ContentsOA.ParagraphsOS)
    return text, para_list[0]


def _cleanup_text(project, text):
    try:
        project.Texts.Delete(text)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo_segment_operations():
    print("=" * 70)
    print("SEGMENT OPERATIONS DEMO")
    print("=" * 70)

    FLExInitialize()
    project = _open_project()
    if project is None:
        print("  Cannot run demo - no writable FLEx project available.")
        print(f"  Tried: {', '.join(_CANDIDATE_PROJECTS)}")
        FLExCleanup()
        return

    demo_text = None
    try:
        # ------------------------------------------------------------------ #
        # STEP 1: Setup - create a throwaway text + paragraph                #
        # ------------------------------------------------------------------ #
        print("\n" + "=" * 70)
        print("STEP 1: Setup - create throwaway text")
        print("=" * 70)
        demo_text, para = _make_throwaway_text(project, "zz_seg_demo")
        print(f"  Created text with HVO: {demo_text.Hvo}")
        print(f"  Working paragraph HVO: {para.Hvo}")

        # ------------------------------------------------------------------ #
        # STEP 2: AppendSentence (replaces the old Create)                   #
        # ------------------------------------------------------------------ #
        print("\n" + "=" * 70)
        print("STEP 2: AppendSentence - add sentences to paragraph")
        print("=" * 70)

        seg1 = project.Segments.AppendSentence(para, "In the beginning God created.")
        print(f"  Appended seg1, HVO: {seg1.Hvo}")

        seg2 = project.Segments.AppendSentence(para, "Now the earth was formless.")
        print(f"  Appended seg2, HVO: {seg2.Hvo}")

        seg3 = project.Segments.AppendSentence(para, "Darkness covered the deep.")
        print(f"  Appended seg3, HVO: {seg3.Hvo}")

        para_text = para.Contents.Text or ""
        print(f"  Paragraph Contents: {para_text!r}")

        # ------------------------------------------------------------------ #
        # STEP 3: GetAll - enumerate segments (requires paragraph arg)       #
        # ------------------------------------------------------------------ #
        print("\n" + "=" * 70)
        print("STEP 3: GetAll(paragraph) - list segments")
        print("=" * 70)

        segments = list(project.Segments.GetAll(para))
        print(f"  Segment count: {len(segments)}")
        for i, seg in enumerate(segments):
            baseline = project.Segments.GetBaselineText(seg)
            print(f"  [{i}] {baseline!r}")

        # ------------------------------------------------------------------ #
        # STEP 4: SetFreeTranslation / GetFreeTranslation                    #
        # ------------------------------------------------------------------ #
        print("\n" + "=" * 70)
        print("STEP 4: SetFreeTranslation / GetFreeTranslation")
        print("=" * 70)

        project.Segments.SetFreeTranslation(seg1, "At the start, God made everything.")
        project.Segments.SetFreeTranslation(seg2, "The earth had no shape.")
        trans = project.Segments.GetFreeTranslation(seg1)
        print(f"  seg1 FreeTranslation: {trans!r}")

        # ------------------------------------------------------------------ #
        # STEP 5: MergeSegments (default policy='migrate')                   #
        # ------------------------------------------------------------------ #
        print("\n" + "=" * 70)
        print("STEP 5: MergeSegments - merge seg1 + seg2 (policy='migrate')")
        print("=" * 70)

        count_before = len(list(para.SegmentsOS))
        merged = project.Segments.MergeSegments(seg1, seg2)
        count_after = len(list(para.SegmentsOS))
        print(f"  Segment count: {count_before} -> {count_after}")
        merged_baseline = project.Segments.GetBaselineText(merged)
        merged_trans = project.Segments.GetFreeTranslation(merged)
        print(f"  Merged baseline: {merged_baseline!r}")
        print(f"  Merged translation: {merged_trans!r}")

        # ------------------------------------------------------------------ #
        # STEP 6: SplitSegment                                               #
        # ------------------------------------------------------------------ #
        print("\n" + "=" * 70)
        print("STEP 6: SplitSegment - split merged segment at offset 10")
        print("=" * 70)

        count_before = len(list(para.SegmentsOS))
        s_a, s_b = project.Segments.SplitSegment(merged, 10)
        count_after = len(list(para.SegmentsOS))
        print(f"  Segment count: {count_before} -> {count_after}")
        print(f"  s_a baseline: {project.Segments.GetBaselineText(s_a)!r}")
        print(f"  s_b baseline: {project.Segments.GetBaselineText(s_b)!r}")

        # ------------------------------------------------------------------ #
        # STEP 7: ReparseParagraph                                           #
        # ------------------------------------------------------------------ #
        print("\n" + "=" * 70)
        print("STEP 7: ReparseParagraph - re-derive segments from Contents")
        print("=" * 70)

        segs_os = project.Segments.ReparseParagraph(para)
        print(f"  Rebuilt {segs_os.Count} segments from Contents")

        # Re-enumerate after reparse
        segments_after = list(project.Segments.GetAll(para))
        print(f"  Segments after reparse: {len(segments_after)}")
        for i, seg in enumerate(segments_after):
            baseline = project.Segments.GetBaselineText(seg)
            print(f"  [{i}] {baseline!r}")

        # ------------------------------------------------------------------ #
        # STEP 8: Delete a segment                                           #
        # ------------------------------------------------------------------ #
        print("\n" + "=" * 70)
        print("STEP 8: Delete - remove last segment")
        print("=" * 70)

        if segments_after:
            last_seg = segments_after[-1]
            count_before = len(list(para.SegmentsOS))
            project.Segments.Delete(last_seg)
            count_after = len(list(para.SegmentsOS))
            print(f"  Segment count: {count_before} -> {count_after}")

        print("\n" + "=" * 70)
        print("DEMO COMPLETE - All operations exercised successfully")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] during demo: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nCleaning up demo text...")
        if demo_text is not None:
            _cleanup_text(project, demo_text)
        print("Closing project...")
        project.CloseProject()
        FLExCleanup()


if __name__ == "__main__":
    print(
        """
Segment Operations Demo
=======================

Demonstrates the SegmentOperations API (issues #172 / #174):
  - AppendSentence (replaces removed Create)
  - GetAll(paragraph)  -- paragraph argument is required
  - SplitSegment, MergeSegments (with translation_policy)
  - ReparseParagraph (replaces removed RebuildSegments)
  - SetFreeTranslation / GetFreeTranslation
  - Delete

Requirements:
  - FieldWorks installed
  - A writable project (tries Sena 3, Test, SampleLexicon, SampleLexicon3)

WARNING: Creates and deletes a temporary text in the database.
    """
    )
    response = input("\nRun demo? (y/N): ")
    if response.lower() == "y":
        demo_segment_operations()
    else:
        print("\nDemo skipped.")
