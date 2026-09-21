#
#   test_datanotebook_duplicate.py
#
#   Class: TestDataNotebookOwnershipFormAndHvoEntryPathLive /
#          TestDataNotebookDuplicateTopLevelLive /
#          TestDataNotebookDuplicateSubRecordOwnerDetectionLive /
#          TestDataNotebookRecordsOCHasNoInsertLive /
#          TestDataNotebookInvalidHvoLive /
#          TestDataNotebookAttributeErrorNotRelabelledLive
#
#          Live regression coverage for issue #158 Pattern I
#          (DataNotebookOperations.Duplicate(insert_after=True) on a
#          top-level record must use RecordsOC.Add(), never
#          RecordsOC.Insert() -- an ILcmOwningCollection (OC) has no
#          Insert() method), AND for rulings C1/C6 (#302/#261) landed
#          under T2.2/T2.3, which this file is the first live coverage
#          of.
#
#   DELETED AND REWRITTEN under ruling C4 (spec.md
#   specs/lcm-member-truth-sweep/spec.md, section 3). The file this
#   replaces never imported DataNotebookOperations at all: it hand-
#   re-typed the Duplicate() top-level/sub-record branching logic
#   against a `_MockRepository` that DEFINED a `RecordsOC` attribute --
#   a member the real `IRnResearchNbkRepository` does not have (ruling
#   C2/C3, ground truth #302). Because the mock invented the very
#   member whose absence is the production bug, the old file's 9 tests
#   passed unconditionally, before and after any production fix, and
#   would keep passing no matter what DataNotebookOperations actually
#   does. That is C4's "non-test": it verified a hand-rolled simulation
#   of the logic, never the module.
#
#   NEW LIVE FINDINGS SURFACED WHILE WRITING THIS FILE (all out of
#   scope for T2.4/T2.5, reported separately in
#   specs/lcm-member-truth-sweep/reviews/cycle2-programmer-T2.4-T2.5.md,
#   NONE fixed here). Once T2.2's ownership-form fix let Create() get
#   PAST the #302 RecordsOC crash for the first time ever, three more,
#   independent, previously-masked defects became reachable:
#
#     1. IRnGenericRec.Title is a bare ITsString (settable only by
#        direct assignment, e.g. `record.Title = mkstr`) -- NOT an
#        IMultiString/IMultiUnicode with .get_String()/.set_String()/
#        .CopyAlternatives(). IRnGenericRec has NO `Text` member at
#        all. Create(), CreateSubRecord(), SetTitle(), SetContent(),
#        and Duplicate()'s Title/Text copy lines all crash
#        unconditionally. GetTitle()/GetContent() do NOT crash: their
#        own try/except (AttributeError, TypeError) silently returns
#        "" every time instead -- a silent-failure defect in the same
#        family this campaign is chartered against, but not one of
#        its six issues.
#     2. IRnGenericRec's Status/Type/Confidence members are actually
#        named StatusRA/TypeRA/ConfidenceRA. GetStatus()/GetRecordType()
#        read the wrong bare name and silently return None always;
#        SetStatus()/SetRecordType() write that same wrong bare name,
#        which pythonnet accepts as a throwaway Python-side instance
#        attribute instead of raising, so the write silently never
#        reaches the LCM at all.
#     3. IRnGenericRec.DateOfEvent is CLR-typed as GenDate, not
#        System.DateTime -- SetDateOfEvent() crashes with TypeError on
#        every call (it always constructs/receives a .NET DateTime).
#     4. Duplicate()'s (and GetParentRecord()'s) sub-record detection
#        used to do `isinstance(owner, IRnGenericRec)` on the raw,
#        uncast `source.Owner`, which is always False live because
#        pythonnet types `.Owner` as the base ICmObject interface.
#        Delete() in this SAME file already fixed the identical class
#        of bug under issue #133 via `self._GetTypedOwner(record)`;
#        Duplicate()/GetParentRecord now match that pattern.
#
#   Fixing any of this is outside T2.4/T2.5's mandate (T2.4 is a
#   test-file rewrite; T2.5 is explicitly production-edit-free). This
#   file therefore ROUTES AROUND Create()/CreateSubRecord()'s
#   title-writing lines for SETUP purposes only (raw
#   IRnGenericRecFactory + direct collection Add() + direct `.Title =`
#   assignment), exactly the precedent already established in
#   tests/operations/test_cycle2_live_299_300_290.py
#   (TestIssue300DataNotebookGetSequence) for the pre-T2.2 RecordsOC
#   crash, and uses only genuinely-correct methods (Delete,
#   GetSubRecords, GetLocations/AddLocation/RemoveLocation,
#   GetParentRecord for the top-level case) for the positive int-HVO
#   coverage. Duplicate() itself IS still called directly (not routed
#   around) in both the top-level and sub-record classes below: it
#   partially succeeds before hitting the Title-copy crash, and the
#   placement side effect is inspected afterward from the live LCM --
#   genuine coverage of what actually happens today, including finding
#   4 above for the sub-record case.
#
#   This file:
#     - imports and calls the real DataNotebookOperations methods
#       (Duplicate, Delete, GetSubRecords, GetParentRecord, GetLocations,
#       AddLocation, RemoveLocation, GetTitle) through
#       project.DataNotebook, live, against target_sandbox (a tempdir
#       copy of the Target .fwbackup; nothing leaks into the real
#       Target);
#     - re-reads every asserted value BACK FROM THE LCM by HVO after
#       the write, never asserting on the value just passed in;
#     - exercises the __GetRecordObject int-HVO entry path (ruling C6 /
#       issue #261) directly by calling six of its 38 routed public
#       methods with a bare Python int, not a wrapped object -- an
#       entry path this suite had ZERO coverage of before, and the
#       exact path that was broken (self.project.project.GetObject(hvo)
#       on the raw LcmCache, which has no GetObject member);
#     - asserts the negative both ways: a genuinely invalid HVO still
#       raises FP_ParameterError, and a genuine AttributeError raised
#       from inside the resolution path is no longer laundered into
#       that same FP_ParameterError message (the mask C6 required
#       removed).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.Notebook.DataNotebookOperations import DataNotebookOperations
from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_DND_"


def _make_toplevel_record(project, title):
    """
    Build a real IRnGenericRec directly, via the raw factory + the
    SAME owning collection Create() uses (ResearchNotebookOA.RecordsOC,
    ruling C1) -- bypassing DataNotebookOperations.Create() only
    because Create() unconditionally crashes on the separate,
    newly-discovered Title bug documented at the top of this file (not
    #302/#261). Title is set by direct assignment, which live
    reflection in this session confirms is the real, correct way to
    write it (`record.Title = mkstr`, not `.set_String(...)`).
    """
    from SIL.LCModel import IRnGenericRecFactory
    from SIL.LCModel.Core.Text import TsStringUtils

    factory = project.project.ServiceLocator.GetService(IRnGenericRecFactory)
    ws = project.project.DefaultAnalWs

    record = factory.Create()
    project.lp.ResearchNotebookOA.RecordsOC.Add(record)
    record.Title = TsStringUtils.MakeString(title, ws)
    return record


def _make_subrecord(project, parent, title):
    """Same as _make_toplevel_record, but owned by parent.SubRecordsOS."""
    from SIL.LCModel import IRnGenericRecFactory
    from SIL.LCModel.Core.Text import TsStringUtils

    factory = project.project.ServiceLocator.GetService(IRnGenericRecFactory)
    ws = project.project.DefaultAnalWs

    subrecord = factory.Create()
    parent.SubRecordsOS.Add(subrecord)
    subrecord.Title = TsStringUtils.MakeString(title, ws)
    return subrecord


class TestDataNotebookOwnershipFormAndHvoEntryPathLive:
    """
    T2.4 core coverage: create a notebook record in the SAME owning
    collection Create()/Delete() use (ResearchNotebookOA.RecordsOC,
    ruling C1), re-read it BY HVO (never the in-hand handle), exercise
    at least three (this test uses six) of the 38 __GetRecordObject-
    routed public methods with a bare Python int HVO -- the entry path
    ruling C6 fixed and this suite had zero prior coverage of -- and
    delete it, confirming removal from the same live collection.
    """

    @pytest.mark.live_phase("DataNotebookOperations", "delete")
    def test_ownership_form_reread_hvo_entry_methods_delete(self, target_sandbox):
        notebook = target_sandbox.DataNotebook
        assert isinstance(notebook, DataNotebookOperations)

        record = _make_toplevel_record(
            target_sandbox, f"{TEST_PREFIX}ownership_hvo_entry"
        )
        hvo = int(record.Hvo)  # plain Python int -- NOT the wrapped object
        assert type(hvo) is int

        # Re-read from the LCM by HVO, from RecordsOC itself (not the
        # in-hand `record` reference), and assert on that re-read value.
        owner_records = list(target_sandbox.lp.ResearchNotebookOA.RecordsOC)
        owner_hvos = {r.Hvo for r in owner_records}
        assert hvo in owner_hvos
        reread_source = next(r for r in owner_records if r.Hvo == hvo)
        assert reread_source.Title.Text == f"{TEST_PREFIX}ownership_hvo_entry"

        location = None
        try:
            # -- Six of the 38 __GetRecordObject-routed methods, called
            # with the bare int HVO. GetTitle/SetTitle,
            # GetRecordType/SetRecordType, GetStatus/SetStatus, and
            # GetDateOfEvent/SetDateOfEvent are deliberately NOT used
            # here: live probing in this same session found each of
            # them independently broken for reasons unrelated to
            # #302/#261 (see the module docstring) --
            # GetRecordType/GetStatus read the wrong bare property name
            # (`Type`/`Status`; the real names are `TypeRA`/`StatusRA`)
            # and silently return None always; SetRecordType/SetStatus
            # write that same wrong bare name, which pythonnet accepts
            # as a throwaway Python-side instance attribute rather than
            # raising, so the write silently never reaches the LCM;
            # SetDateOfEvent crashes with TypeError because
            # IRnGenericRec.DateOfEvent is CLR-typed as GenDate, not
            # System.DateTime. All are reported separately in
            # cycle2-programmer-T2.4-T2.5.md; none are fixed here.
            #
            # GetSubRecords, GetParentRecord, GetLocations,
            # AddLocation, and RemoveLocation all use real, correctly-
            # named LCM members (SubRecordsOS, Owner, LocationsRC) and
            # are confirmed live-working in this same session.
            assert notebook.GetSubRecords(hvo) == []
            assert notebook.GetParentRecord(hvo) is None

            assert notebook.GetLocations(hvo) == []
            location = target_sandbox.Location.Create(
                f"{TEST_PREFIX}ownership_hvo_entry_loc"
            )
            notebook.AddLocation(hvo, location)
            reread_locations = notebook.GetLocations(hvo)
            assert len(reread_locations) == 1
            assert reread_locations[0].Hvo == location.Hvo

            notebook.RemoveLocation(hvo, location)
            assert notebook.GetLocations(hvo) == []
        finally:
            notebook.Delete(hvo)
            if location is not None:
                try:
                    target_sandbox.Location.Delete(location)
                except Exception:
                    pass

        # Re-read RecordsOC again, live, to confirm removal.
        owner_hvos_after = {
            r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
        }
        assert hvo not in owner_hvos_after


class TestDataNotebookDuplicateTopLevelLive:
    """
    Issue #158 Pattern I -- Duplicate() on a TOP-LEVEL record. RecordsOC
    is owned by ResearchNotebookOA (ruling C1) and is an unordered
    ILcmOwningCollection with no Insert() method, so insert_after must
    be silently ignored and the duplicate always appended via Add() --
    never crash by attempting Insert() on an OC.

    Issue #352 fixed the Title copy (`CopyAlternatives` on a bare
    ITsString raised AttributeError after placement ran), so Duplicate()
    now succeeds end to end: this test asserts the returned duplicate
    lands in RecordsOC with the title conserved.
    """

    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_duplicate_toplevel_uses_add_not_insert(self, target_sandbox):
        notebook = target_sandbox.DataNotebook

        record = _make_toplevel_record(
            target_sandbox, f"{TEST_PREFIX}Interview 1"
        )
        record_hvo = record.Hvo

        before_hvos = {
            r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
        }

        try:
            # insert_after=True is passed deliberately to prove it is
            # ignored (not an Insert()-on-an-OC crash) at the top level
            # -- this is exactly the shape of the pre-#158 defect.
            dup = notebook.Duplicate(record, insert_after=True)

            after_hvos = {
                r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
            }
            new_hvos = after_hvos - before_hvos
            assert len(new_hvos) == 1, (
                "Duplicate() must have added exactly one new record to "
                "RecordsOC via Add() -- if this is now 0, the #158/#302 "
                "Add()-into-ResearchNotebookOA.RecordsOC placement regressed"
            )
            assert record_hvo in after_hvos, "source record must be untouched"
            assert dup.Hvo in after_hvos
            assert notebook.GetTitle(dup) == notebook.GetTitle(record)
        finally:
            after_hvos = {
                r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
            }
            new_hvos = after_hvos - before_hvos
            for hvo in new_hvos | {record_hvo}:
                try:
                    notebook.Delete(hvo)
                except Exception:
                    pass


class TestDataNotebookDuplicateSubRecordOwnerDetectionLive:
    """
    SubRecordsOS (the OS branch) is an ordered sequence: positional
    IndexOf()/Insert() is valid there, unlike the top-level OC. Issue
    #331 fixed Duplicate()/GetParentRecord() to mirror Delete()'s owner
    casting pattern from issue #133: route raw `.Owner` values through
    `self._GetTypedOwner(record)` before deciding whether a record is a
    true sub-record. Live, that restores the intended behavior: a
    sub-record duplicate stays under the same parent, and
    GetParentRecord() returns that parent instead of None.
    """

    @pytest.mark.live_phase("DataNotebookOperations", "add")
    def test_duplicate_subrecord_stays_in_parent_subrecords(self, target_sandbox):
        notebook = target_sandbox.DataNotebook

        parent = _make_toplevel_record(
            target_sandbox, f"{TEST_PREFIX}Interview parent"
        )
        s1 = _make_subrecord(target_sandbox, parent, f"{TEST_PREFIX}sub1")
        s2 = _make_subrecord(target_sandbox, parent, f"{TEST_PREFIX}sub2")

        before_toplevel = {
            r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
        }

        try:
            # Issue #352 fixed the Title copy, so Duplicate() now returns
            # the new sub-record instead of raising after placement.
            dup = notebook.Duplicate(s1, insert_after=True)

            # Re-read both collections live from the LCM.
            reread_subrecords = [r.Hvo for r in parent.SubRecordsOS]
            after_toplevel = {
                r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
            }
            new_toplevel = after_toplevel - before_toplevel

            assert len(reread_subrecords) == 3, (
                "Duplicate() must insert a new sub-record under the same "
                "parent instead of appending it into top-level RecordsOC"
            )
            assert reread_subrecords[0] == s1.Hvo
            assert reread_subrecords[1] not in {s1.Hvo, s2.Hvo}, (
                "insert_after=True must place the duplicate immediately "
                "after the source sub-record"
            )
            assert reread_subrecords[2] == s2.Hvo
            assert len(new_toplevel) == 0, (
                "duplicating a sub-record must not create a stray top-level "
                "record in ResearchNotebookOA.RecordsOC"
            )
            assert reread_subrecords[1] == dup.Hvo
            assert notebook.GetTitle(dup) == notebook.GetTitle(s1)
        finally:
            after_toplevel = {
                r.Hvo for r in target_sandbox.lp.ResearchNotebookOA.RecordsOC
            }
            stray_toplevel = after_toplevel - before_toplevel
            for hvo in stray_toplevel:
                try:
                    notebook.Delete(hvo)
                except Exception:
                    pass
            # Delete() on the parent recursively deletes all genuine
            # sub-records, per Delete()'s own contract.
            try:
                notebook.Delete(parent.Hvo)
            except Exception:
                pass

    @pytest.mark.live_phase("DataNotebookOperations", "read")
    def test_getparentrecord_returns_parent_for_subrecord(self, target_sandbox):
        notebook = target_sandbox.DataNotebook

        parent = _make_toplevel_record(
            target_sandbox, f"{TEST_PREFIX}Interview parent getparent"
        )
        child = _make_subrecord(target_sandbox, parent, f"{TEST_PREFIX}child")

        try:
            reread_child = next(r for r in parent.SubRecordsOS if r.Hvo == child.Hvo)
            found_parent = notebook.GetParentRecord(reread_child.Hvo)
            assert found_parent is not None
            assert found_parent.Hvo == parent.Hvo
        finally:
            # Delete() on the parent recursively deletes all genuine
            # sub-records, per Delete()'s own contract.
            try:
                notebook.Delete(parent.Hvo)
            except Exception:
                pass


class TestDataNotebookRecordsOCHasNoInsertLive:
    """
    Live confirmation of the #158/#302 premise: the real owning
    collection genuinely has no Insert(). If this ever starts failing,
    Duplicate()'s "insert_after is ignored at the top level" behaviour
    needs to be re-derived, not merely re-asserted.
    """

    @pytest.mark.live_phase("DataNotebookOperations", "read")
    def test_recordsoc_has_no_insert_live(self, target_sandbox):
        owner_collection = target_sandbox.lp.ResearchNotebookOA.RecordsOC
        assert not hasattr(owner_collection, "Insert"), (
            "IRnResearchNbk.RecordsOC unexpectedly gained an Insert() "
            "method -- re-derive whether Duplicate's top-level "
            "insert_after-is-ignored behaviour is still justified"
        )


class TestDataNotebookInvalidHvoLive:
    """
    Negative coverage for ruling C6: a genuinely invalid HVO must still
    raise FP_ParameterError (the correct, intended error path is
    untouched by C6 -- only the incidental AttributeError-laundering
    was removed). __GetRecordObject's resolution fails before ever
    reaching Title/Text, so this is unaffected by the separate,
    unrelated Title bug documented above.
    """

    @pytest.mark.live_phase("DataNotebookOperations", "read")
    def test_invalid_hvo_raises_fp_parameter_error(self, target_sandbox):
        notebook = target_sandbox.DataNotebook

        with pytest.raises(FP_ParameterError):
            notebook.GetTitle(999999999)


class TestDataNotebookAttributeErrorNotRelabelledLive:
    """
    Ruling C6's second half: AttributeError was deliberately DROPPED
    from __GetRecordObject's catch tuple (not merely chained), because
    it was the exact shape of the original #261 bug (accessing a
    nonexistent GetObject attribute on LcmCache). Catching it
    unconditionally would keep laundering any FUTURE genuine
    AttributeError -- e.g. a real coding mistake reachable through this
    path -- into the same misleading "Invalid notebook record object or
    HVO" message. Simulates exactly that future genuine AttributeError
    (by making the underlying project.Object() resolution raise it) and
    confirms it propagates unmasked, not as FP_ParameterError.
    """

    @pytest.mark.live_phase("DataNotebookOperations", "read")
    def test_genuine_attributeerror_propagates_unmasked(
        self, target_sandbox, monkeypatch
    ):
        notebook = target_sandbox.DataNotebook

        record = _make_toplevel_record(target_sandbox, f"{TEST_PREFIX}AttrErr")
        hvo = record.Hvo
        try:
            def _boom(_hvo):
                raise AttributeError(
                    "simulated genuine coding-mistake AttributeError, "
                    "not the fixed missing-GetObject shape"
                )

            monkeypatch.setattr(target_sandbox, "Object", _boom)

            with pytest.raises(AttributeError) as excinfo:
                notebook.GetTitle(hvo)

            # It must be the exact AttributeError we raised, not a
            # relabelled wrapper exception.
            assert type(excinfo.value) is AttributeError
            assert "simulated genuine coding-mistake" in str(excinfo.value)
        finally:
            monkeypatch.undo()
            try:
                notebook.Delete(hvo)
            except Exception:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
