#
#   test_issue290_const_chart_reflection.py
#
#   Live LCM reflection pass required by GitHub issue #290 BEFORE any
#   fix is written to ConstChartRowOperations / DiscourseOperations
#   Label/Notes/Comment handling.
#
#   Read-only reflection plus isolating live calls only -- this file
#   does not fix anything it observes; it only records type()/dir()
#   reflection and traceback/success evidence.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import json
import pathlib
import traceback

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_290_"

_EVIDENCE_DIR = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "specs" / "299-300-290-reorder-and-tsstring" / "evidence"
)
_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
_EVIDENCE_JSON_PATH = _EVIDENCE_DIR / "live-290-reflection-raw.json"


def _describe(obj):
    py_type = type(obj).__name__
    try:
        clr_type = obj.GetType().FullName
    except Exception:
        clr_type = None
    return py_type, clr_type


def _write_evidence(evidence):
    existing = {}
    if _EVIDENCE_JSON_PATH.exists():
        try:
            existing = json.loads(_EVIDENCE_JSON_PATH.read_text())
        except Exception:
            existing = {}
    existing.update(evidence)
    _EVIDENCE_JSON_PATH.write_text(json.dumps(existing, indent=2, default=str))


class TestIssue290ConstChartRowLabelNotesReflection:
    # Q1, Q2, Q3 -- IConstChartRow.Label / .Notes reflection.

    @pytest.mark.live_phase("ConstChartRowOperations", "read")
    def test_q1_q2_q3_label_notes_reflection(self, target_sandbox):
        charts = target_sandbox.ConstCharts
        rows = target_sandbox.ConstChartRows
        evidence = {}
        chart = None
        try:
            chart = charts.Create(f"{TEST_PREFIX}chart_labelnotes")

            # Q1 + read-side reflection of Notes: row created with NO
            # label/notes -- Create uses if-label / if-notes guards
            # that are falsy for empty string, so this row creation
            # cannot hit the buggy set_String call and is safe purely
            # for reflection.
            plain_row = rows.Create(chart)

            label_py, label_clr = _describe(plain_row.Label)
            evidence["q1_label_py_type"] = label_py
            evidence["q1_label_clr_type"] = label_clr
            evidence["q1_label_has_set_String"] = hasattr(plain_row.Label, "set_String")
            evidence["q1_label_has_get_String"] = hasattr(plain_row.Label, "get_String")
            evidence["q1_label_dir_members"] = sorted(
                n for n in dir(plain_row.Label) if not n.startswith("_")
            )

            notes_py, notes_clr = _describe(plain_row.Notes)
            evidence["notes_py_type"] = notes_py
            evidence["notes_clr_type"] = notes_clr
            evidence["notes_has_set_String"] = hasattr(plain_row.Notes, "set_String")
            evidence["notes_has_get_String"] = hasattr(plain_row.Notes, "get_String")
            evidence["notes_dir_members"] = sorted(
                n for n in dir(plain_row.Notes) if not n.startswith("_")
            )

            # Q2 -- isolating live hit: notes=..., label=None so a crash
            # (if any) happens at line 137 (Notes), never reaching the
            # already-confirmed line 132 (Label) crash.
            try:
                notes_row = rows.Create(
                    chart, label=None, notes=f"{TEST_PREFIX}notes"
                )
                evidence["q2_outcome"] = "success"
                evidence["q2_created_row_hvo"] = notes_row.Hvo
            except Exception:
                evidence["q2_outcome"] = "raised"
                evidence["q2_traceback"] = traceback.format_exc()

            # Q3 -- GetLabel / GetNotes exercised live on plain_row
            # (Label/Notes both unset but present as live bare
            # ITsString objects).
            try:
                result = rows.GetLabel(plain_row)
                evidence["q3_getlabel_outcome"] = "success: " + repr(result)
            except Exception:
                evidence["q3_getlabel_outcome"] = "raised"
                evidence["q3_getlabel_traceback"] = traceback.format_exc()

            try:
                result = rows.GetNotes(plain_row)
                evidence["q3_getnotes_outcome"] = "success: " + repr(result)
            except Exception:
                evidence["q3_getnotes_outcome"] = "raised"
                evidence["q3_getnotes_traceback"] = traceback.format_exc()

        finally:
            _write_evidence(evidence)
            if chart is not None:
                try:
                    charts.Delete(chart)
                except Exception:
                    pass

        assert evidence.get("q1_label_clr_type"), (
            "No CLR type observed for Label -- live reflection did not run"
        )


class TestIssue290CellPartLabelCommentReflection:
    # Q4, Q5 -- dir()/hasattr reflection on live instances of the four
    # concrete cell-part types (ConstChartWordGroup, ConstChartTag,
    # ConstChartClauseMarker, ConstChartMovedTextMarker), plus a live
    # exercise of DiscourseOperations.GetCells/SetCellContent/
    # GetCellContent against whatever cast_to_concrete actually returns
    # for a real row, to settle reachability of hasattr(cell, "Label")
    # and hasattr(cell, "Comment") for real cells (not a row).

    @pytest.mark.live_phase("DiscourseOperations", "read")
    def test_q4_q5_cellpart_reflection(self, target_sandbox):
        from SIL.LCModel import IStTxtPara

        charts = target_sandbox.ConstCharts
        rows = target_sandbox.ConstChartRows
        word_groups = target_sandbox.ConstChartWordGroups
        cell_tags = target_sandbox.ConstChartCellTags
        clause_markers = target_sandbox.ConstChartClauseMarkers
        moved_text = target_sandbox.ConstChartMovedText
        markers = target_sandbox.ConstChartMarkers
        texts = target_sandbox.Texts
        paragraphs = target_sandbox.Paragraphs
        segments = target_sandbox.Segments
        discourse = target_sandbox.Discourse

        evidence = {}
        chart = None
        text = None
        col = marker_vocab = None
        word_group = tag = clause_marker = moved_marker = None
        try:
            text = texts.Create(f"{TEST_PREFIX}text")
            paragraphs.Create(text, f"{TEST_PREFIX}sentence one.")
            para_list = list(text.ContentsOA.ParagraphsOS)
            para = IStTxtPara(para_list[0])
            seg = segments.AppendSentence(para, f"{TEST_PREFIX}sentence one.")
            if seg is None:
                segs = list(para.SegmentsOS)
                assert segs, "No segment available to build a word group"
                seg = segs[0]

            chart = charts.Create(f"{TEST_PREFIX}chart_cellparts")
            row = rows.Create(chart)

            col = markers.Create(f"{TEST_PREFIX}col")
            marker_vocab = markers.Create(f"{TEST_PREFIX}marker")

            word_group = word_groups.Create(row, seg, seg)
            evidence["wordgroup_classname"] = word_group.ClassName
            evidence["wordgroup_has_label"] = hasattr(word_group, "Label")
            evidence["wordgroup_has_comment"] = hasattr(word_group, "Comment")

            tag = cell_tags.Create(row, col, marker_vocab)
            evidence["tag_classname"] = tag.ClassName
            evidence["tag_has_label"] = hasattr(tag, "Label")
            evidence["tag_has_comment"] = hasattr(tag, "Comment")

            try:
                clause_marker = clause_markers.Create(row, word_group)
                evidence["clausemarker_create_outcome"] = "success"
            except Exception:
                evidence["clausemarker_create_outcome"] = "raised"
                evidence["clausemarker_create_traceback"] = traceback.format_exc()
                clause_marker = None

            if clause_marker is not None:
                evidence["clausemarker_classname"] = clause_marker.ClassName
                evidence["clausemarker_has_label"] = hasattr(clause_marker, "Label")
                evidence["clausemarker_has_comment"] = hasattr(clause_marker, "Comment")
                cells_hvos = [c.Hvo for c in row.CellsOS]
                evidence["clausemarker_in_row_cellsos"] = clause_marker.Hvo in cells_hvos

            try:
                moved_marker = moved_text.Create(word_group, preposed=True)
                evidence["movedtext_create_outcome"] = "success"
            except Exception:
                evidence["movedtext_create_outcome"] = "raised"
                evidence["movedtext_create_traceback"] = traceback.format_exc()
                moved_marker = None

            if moved_marker is not None:
                evidence["movedtext_classname"] = moved_marker.ClassName
                evidence["movedtext_has_label"] = hasattr(moved_marker, "Label")
                evidence["movedtext_has_comment"] = hasattr(moved_marker, "Comment")
                cells_hvos = [c.Hvo for c in row.CellsOS]
                evidence["movedtext_in_row_cellsos"] = moved_marker.Hvo in cells_hvos

            named_objects = [
                ("wordgroup", word_group),
                ("tag", tag),
                ("clausemarker", clause_marker),
                ("movedtext", moved_marker),
            ]
            for label, obj in named_objects:
                if obj is not None and hasattr(obj, "Comment"):
                    py_t, clr_t = _describe(obj.Comment)
                    evidence[label + "_comment_py_type"] = py_t
                    evidence[label + "_comment_clr_type"] = clr_t
                    evidence[label + "_comment_has_get_String"] = hasattr(
                        obj.Comment, "get_String"
                    )

            live_cells = discourse.GetCells(row)
            live_cells_info = []
            for c in live_cells:
                info = {
                    "hvo": c.Hvo,
                    "classname": c.ClassName,
                    "has_label": hasattr(c, "Label"),
                    "has_comment": hasattr(c, "Comment"),
                }
                try:
                    discourse.SetCellContent(c, f"{TEST_PREFIX}content")
                    info["set_cell_content_outcome"] = "success"
                except Exception as exc:
                    info["set_cell_content_outcome"] = (
                        "raised " + type(exc).__name__ + ": " + str(exc)
                    )
                try:
                    got = discourse.GetCellContent(c)
                    info["get_cell_content_outcome"] = "success: " + repr(got)
                except Exception as exc:
                    info["get_cell_content_outcome"] = (
                        "raised " + type(exc).__name__ + ": " + str(exc)
                    )
                live_cells_info.append(info)
            evidence["live_getcells_row_cellsos_count"] = row.CellsOS.Count
            evidence["live_getcells_info"] = live_cells_info

        finally:
            _write_evidence(evidence)
            if chart is not None:
                try:
                    charts.Delete(chart)
                except Exception:
                    pass
            for item in (marker_vocab, col):
                if item is not None:
                    try:
                        markers.Delete(item)
                    except Exception:
                        pass
            if text is not None:
                try:
                    texts.Delete(text)
                except Exception:
                    pass

        assert evidence.get("wordgroup_classname"), (
            "No live word group observed -- reflection did not run"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestIssue290MovedTextMarkerDirectFactoryReflection:
    # Supplementary to Q4: ConstChartMovedTextOperations.Create raised a
    # System.NullReferenceException on the Preposed setter (an unrelated
    # defect, not part of #290) when reached through the documented
    # Operations path, which blocked getting a live
    # ConstChartMovedTextMarker instance for the Q4 dir() reflection.
    # This diagnostic bypasses only the Preposed setter (raw factory +
    # MovedTextMarkerOA assignment, matching lines 124-128 of
    # ConstChartMovedTextOperations.py) purely to obtain a live instance
    # for reflection. It asserts nothing about the Preposed bug and does
    # not fix it.

    @pytest.mark.live_phase("DiscourseOperations", "read")
    def test_movedtextmarker_label_reflection_bypassing_preposed_bug(
        self, target_sandbox
    ):
        from SIL.LCModel import IStTxtPara, IConstChartMovedTextMarkerFactory

        charts = target_sandbox.ConstCharts
        rows = target_sandbox.ConstChartRows
        word_groups = target_sandbox.ConstChartWordGroups
        texts = target_sandbox.Texts
        paragraphs = target_sandbox.Paragraphs
        segments = target_sandbox.Segments

        evidence = {}
        chart = None
        text = None
        try:
            text = texts.Create(f"{TEST_PREFIX}text_mtm")
            paragraphs.Create(text, f"{TEST_PREFIX}sentence two.")
            para_list = list(text.ContentsOA.ParagraphsOS)
            para = IStTxtPara(para_list[0])
            seg = segments.AppendSentence(para, f"{TEST_PREFIX}sentence two.")
            if seg is None:
                segs = list(para.SegmentsOS)
                assert segs, "No segment available to build a word group"
                seg = segs[0]

            chart = charts.Create(f"{TEST_PREFIX}chart_mtm")
            row = rows.Create(chart)
            word_group = word_groups.Create(row, seg, seg)

            factory = target_sandbox.project.ServiceLocator.GetService(
                IConstChartMovedTextMarkerFactory
            )
            # target_sandbox is opened undoable=False (one session-long
            # non-undoable task already open), so a raw LCM write here
            # needs no extra UnitOfWork wrapper -- UndoableOperation()
            # would raise FP_TransactionError on this fixture.
            new_marker = factory.Create()
            word_group.MovedTextMarkerOA = new_marker

            evidence["movedtext_direct_classname"] = new_marker.ClassName
            evidence["movedtext_direct_has_label"] = hasattr(new_marker, "Label")
            evidence["movedtext_direct_has_comment"] = hasattr(new_marker, "Comment")
            evidence["movedtext_direct_dir_members"] = sorted(
                n for n in dir(new_marker) if not n.startswith("_")
            )
            # Confirm the Preposed-setter NullReferenceException reproduces
            # in isolation, independent of the rest of Create().
            try:
                new_marker.Preposed = True
                evidence["movedtext_preposed_setter_outcome"] = "success"
            except Exception as exc:
                evidence["movedtext_preposed_setter_outcome"] = (
                    "raised " + type(exc).__name__ + ": " + str(exc)
                )

        finally:
            _write_evidence(evidence)
            if chart is not None:
                try:
                    charts.Delete(chart)
                except Exception:
                    pass
            if text is not None:
                try:
                    texts.Delete(text)
                except Exception:
                    pass

        assert evidence.get("movedtext_direct_classname"), (
            "No live ConstChartMovedTextMarker observed -- reflection did not run"
        )
