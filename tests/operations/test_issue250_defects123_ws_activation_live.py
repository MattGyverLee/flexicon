#
#   test_issue250_defects123_ws_activation_live.py
#
#   Class: TestExistsAndExistsInStoreLive / TestCreateActivationLive /
#          TestEnsureLive / TestApplyPropsLoopDefect3DiagnosticsLive
#          Live verification for issue #250 Defects 1-3 against a real LCM
#          project.
#
#   Project: target_sandbox ONLY (fresh tempdir copy of the Target
#   .fwbackup) -- never the in-place Target, never Sena 3. Every created
#   object is prefixed TEST_ or uses a qaa-x- private-use writing-system
#   tag reserved for this file (D250a..D250e).
#
#   Constructing "store-present-but-inactive" live (the state Defects 1-3
#   are about): a project whose LDML store holds a writing system absent
#   from CurVernWss/CurAnalysisWss is ordinary FLEx state (deactivating a
#   WS via the UI leaves its LDML on disk -- see the issue's own named
#   reproduction). It is constructed here rather than hunted for: create +
#   activate a genuinely new WS via the public Create() API (a path this
#   fix leaves unaffected), then deactivate it by removing it ONLY from
#   the current list (CurrentVernacularWritingSystems /
#   CurrentAnalysisWritingSystems), leaving it in the full per-project list
#   and in the WritingSystemManager's store (ServiceLocator.WritingSystems.
#   AllWritingSystems) untouched -- confirmed live, by direct exploration,
#   to reproduce exactly the store-vs-active divergence the issue
#   describes (see specs/250-writingsystem-activation/evidence/
#   live-250-defects123.md for the transcript).
#
#   Invocation (never bare `pytest` -- it executes ~322 live tests in place):
#     $env:FLEXLIBS_REQUIRE_LIVE = "1"
#     python -m pytest tests/operations/test_issue250_defects123_ws_activation_live.py \
#         -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import logging

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def _make_store_present_inactive_ws(project, tag, name, is_vernacular):
    """
    Create + activate a genuinely new writing system via the public API,
    then deactivate it by removing it ONLY from the current
    (Vernacular/Analysis) list -- leaving the WritingSystemManager's store
    and the full per-project list untouched. Reproduces "a writing system
    that was configured and later deactivated" (issue #250's description
    of the ordinary, common trigger state) without needing FieldWorks' UI.

    Returns the IWritingSystemDefinition (still valid -- it is not removed
    from the LCM cache, only deactivated).
    """
    ws = project.WritingSystems.Create(tag, name, is_vernacular=is_vernacular)
    lp = project.lp
    current_list = (
        lp.CurrentVernacularWritingSystems
        if is_vernacular
        else lp.CurrentAnalysisWritingSystems
    )
    if current_list.Contains(ws):
        current_list.Remove(ws)
    return ws


def _all_store_ids(project):
    return [
        w.Id
        for w in project.project.ServiceLocator.WritingSystems.AllWritingSystems
    ]


class TestExistsAndExistsInStoreLive:
    """Defect 1: Exists() must be active-only; ExistsInStore() answers the
    whole-store question under its own name."""

    @pytest.mark.live_phase("WritingSystemOperations", "read")
    def test_store_present_inactive_tag_diverges_exists_vs_existsinstore(
        self, target_sandbox
    ):
        project = target_sandbox
        tag = "qaa-x-d250a"
        _make_store_present_inactive_ws(project, tag, "D250a", is_vernacular=False)

        # Setup sanity, re-read from the LCM (not the local `ws` reference).
        assert tag in _all_store_ids(project), (
            "Setup sanity: tag must be present in the LDML store."
        )
        assert tag not in project.lp.CurAnalysisWss.split(), (
            "Setup sanity: tag must NOT be in the active analysis set."
        )

        assert project.WritingSystems.Exists(tag) is False, (
            "Defect 1: Exists() must read False for a store-present but "
            "inactive tag -- it is active-only, matching its own "
            "docstring and GetAll()'s semantics."
        )
        assert project.WritingSystems.ExistsInStore(tag) is True, (
            "The whole-store predicate must still find the LDML."
        )


class TestCreateActivationLive:
    """Defect 2: Create() must activate a store-present-but-inactive tag
    instead of refusing it or duplicating its LDML."""

    @pytest.mark.live_phase("WritingSystemOperations", "modify")
    def test_create_activates_without_raising_or_duplicating(
        self, target_sandbox
    ):
        project = target_sandbox
        tag = "qaa-x-d250b"
        original_ws = _make_store_present_inactive_ws(
            project, tag, "D250b", is_vernacular=False
        )
        pre_count = len(_all_store_ids(project))
        assert tag not in project.lp.CurAnalysisWss.split()

        # Must NOT raise "already exists" (the pre-fix Defect 2 failure).
        ws = project.WritingSystems.Create(tag, "D250b Renamed", is_vernacular=False)

        # Post-state re-read from the LCM.
        post_count = len(_all_store_ids(project))
        assert post_count == pre_count, (
            "Create() must reuse the existing store entry rather than "
            "create a duplicate WritingSystemDefinition -- the store's "
            "writing-system count must not change."
        )
        assert ws.Handle == original_ws.Handle, (
            "Create() must return the SAME writing system, now activated, "
            "not a fresh object."
        )
        assert tag in project.lp.CurAnalysisWss.split(), (
            "Defect 2: Create() must activate a store-present-but-inactive "
            "tag -- confirmed by re-reading CurAnalysisWss after the call."
        )


class TestEnsureLive:
    """Ensure(): the idempotent activate-or-create call the issue asks for."""

    @pytest.mark.live_phase("WritingSystemOperations", "modify")
    def test_ensure_activates_store_present_tag_and_is_idempotent(
        self, target_sandbox
    ):
        project = target_sandbox
        tag = "qaa-x-d250c"
        original_ws = _make_store_present_inactive_ws(
            project, tag, "D250c", is_vernacular=True
        )
        pre_count = len(_all_store_ids(project))

        ws1, created1 = project.WritingSystems.Ensure(tag, "D250c", is_vernacular=True)
        assert created1 is False, (
            "Store-present-but-inactive: created must be False (activated, "
            "not created)."
        )
        assert tag in project.lp.CurVernWss.split(), (
            "Re-read CurVernWss after Ensure(): tag must now be active."
        )
        assert len(_all_store_ids(project)) == pre_count, (
            "Ensure() must never widen the store when reusing an existing "
            "definition."
        )

        # Idempotent second call.
        ws2, created2 = project.WritingSystems.Ensure(tag, "D250c", is_vernacular=True)
        assert created2 is False
        assert ws2.Handle == ws1.Handle == original_ws.Handle
        assert len(_all_store_ids(project)) == pre_count, (
            "A second Ensure() call for an already-active tag must be a "
            "true no-op -- store count unchanged."
        )

    @pytest.mark.live_phase("WritingSystemOperations", "add")
    def test_ensure_creates_genuinely_new_tag(self, target_sandbox):
        project = target_sandbox
        tag = "qaa-x-d250d"
        assert tag not in _all_store_ids(project), (
            "Setup sanity: tag must not already exist anywhere."
        )
        pre_count = len(_all_store_ids(project))

        ws, created = project.WritingSystems.Ensure(tag, "D250d", is_vernacular=False)

        assert created is True
        post_count = len(_all_store_ids(project))
        assert post_count == pre_count + 1, (
            "A genuinely new tag must add exactly one writing system to "
            "the store (re-read from the LCM)."
        )
        assert tag in project.lp.CurAnalysisWss.split()


class TestApplyPropsLoopDefect3DiagnosticsLive:
    """Defect 3: the silent drop for a genuinely-inactive target WS must be
    observable (a logged warning), and must stop dropping once the target
    WS is activated via Ensure() -- proving the diagnostic and the
    Defect-2 fix compose correctly for a real cross-project-sync caller."""

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_drop_is_logged_then_resolves_after_ensure(self, target_sandbox, caplog):
        project = target_sandbox
        pos_ops = project.POS
        tag = "qaa-x-d250e"
        _make_store_present_inactive_ws(project, tag, "D250e", is_vernacular=False)
        assert tag not in project.lp.CurAnalysisWss.split()

        pos = pos_ops.Create(f"{TEST_PREFIX}D250e", "TD250e")
        hvo = pos.Hvo
        try:
            with caplog.at_level(logging.WARNING, logger="flexicon"):
                pos_ops.ApplySyncableProperties(
                    pos, {"Name": {tag: "ShouldBeDropped"}}, ws_map=None,
                )

            warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
            assert any(tag in r.getMessage() for r in warnings), (
                f"Defect 3: expected a WARNING naming the dropped writing "
                f"system {tag!r}; got "
                f"{[r.getMessage() for r in warnings]}"
            )
            # The drop itself is unaffected by this fix -- the target
            # project's active set is unchanged (C-D4-6-style guard).
            assert tag not in project.lp.CurAnalysisWss.split()

            # Now activate via Ensure() and prove the SAME call path saves
            # instead of dropping -- re-read from the LCM, not the value
            # passed in.
            _, created = project.WritingSystems.Ensure(
                tag, "D250e", is_vernacular=False
            )
            assert created is False

            all_ws_by_id = {w.Id: w.Handle for w in project.WritingSystems.GetAll()}
            handle = all_ws_by_id[tag]

            caplog.clear()
            with caplog.at_level(logging.WARNING, logger="flexicon"):
                pos_ops.ApplySyncableProperties(
                    pos, {"Name": {tag: "ShouldBeSaved"}}, ws_map=None,
                )
            post_warnings = [
                r for r in caplog.records if r.levelno == logging.WARNING
            ]
            assert not any(tag in r.getMessage() for r in post_warnings), (
                "After Ensure() activates the writing system, the same "
                "tag must resolve cleanly -- no warning this time."
            )

            from SIL.LCModel import IPartOfSpeech
            from SIL.LCModel.Core.KernelInterfaces import ITsString

            post_pos = IPartOfSpeech(project.Object(hvo))
            saved_text = ITsString(post_pos.Name.get_String(handle)).Text
            assert saved_text == "ShouldBeSaved", (
                "Re-read from the LCM after re-fetching the object: the "
                "alt must now be saved, proving the drop was specific to "
                "the writing system being inactive, not some other fault."
            )
        finally:
            pos_ops.Delete(pos)
