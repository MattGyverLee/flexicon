#
#   test_abort_session_live.py
#
#   Live write-path verification for task A3
#   (specs/write-path-transactions/tasks.md): `FLExProject.AbortSession()`
#   exposing `IActionHandler.Rollback(0)`.
#
#   Structure copied from tests/operations/test_target_live_smoke.py, the
#   canonical template. Runs against tempdir sandboxes restored from the
#   Target `.fwbackup` -- never the user's real Target project, because
#   Rollback(0) discards the WHOLE open unit of work and under
#   `undoable=False` that unit is the entire session.
#
#   Why this cannot be verified offline: every claim below is a claim about
#   liblcm's UndoStack finite state machine, which the offline doubles in
#   tests/write_path_transactions/test_a3_abort_session.py model from source
#   but do not execute. Three things need the real FSM:
#
#     1. Rollback(0) really discards uncommitted mutations, rather than
#        merely discarding undo records (the O3 question, still open for
#        DiscardToMark -- this test settles it for Rollback).
#     2. The FSM really lands in ReadyForBeginTask afterwards (the O2 catch),
#        so the reopened BeginNonUndoableTask() is load-bearing and not
#        defensive noise. Proven by writing AGAIN after the abort: liblcm
#        refuses data changes outside an open task, so a successful
#        post-abort write is only possible if the envelope was reopened.
#     3. CurrentDepth really is 0 between operations under `undoable=True`,
#        which is what makes AbortSession() return False rather than raise
#        in that mode.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_TransactionError

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


def _depth(project):
    """CurrentDepth straight off the live action handler (1 or 0 only)."""
    return project.project.ActionHandlerAccessor.CurrentDepth


class TestFixtureReachesLiveLCM:
    """Prove these writes land on a real LCM cache, not a mock."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_sandbox_opens_write_enabled_non_undoable(self, target_sandbox):
        assert target_sandbox.writeEnabled is True
        assert target_sandbox._undoable is False
        assert getattr(target_sandbox, "project", None) is not None, (
            "target_sandbox has no underlying LCM cache -- this is a "
            "mock, not a live project."
        )

    @pytest.mark.live_phase("FLExProject", "read")
    def test_undoable_sandbox_opens_in_undoable_mode(self, target_sandbox_undoable):
        assert target_sandbox_undoable.writeEnabled is True
        assert target_sandbox_undoable._undoable is True
        assert getattr(target_sandbox_undoable, "project", None) is not None


class TestNonUndoableSessionEnvelope:
    """The mode A3 exists for: undoable=False, one session-long envelope."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_envelope_is_open_for_the_whole_session(self, target_sandbox):
        """
        CurrentDepth == 1 iff CurrentProcessingState is ProcessingDataChanges
        (UndoStack.cs:731-734). Under undoable=False that state is held from
        OpenProject to CloseProject, so a freshly opened session already has
        the unit of work AbortSession() will roll back. This is the live
        precondition the offline doubles assume.
        """
        assert _depth(target_sandbox) == 1


class TestAbortDiscardsUncommittedWrites:
    """Claim 1: Rollback(0) reverts DATA, not merely undo records."""

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_created_object_is_gone_after_abort(self, target_sandbox):
        """
        Create a POS, abort, then re-query the LCM. The object must be gone.
        Asserting on the return value of Create() would prove nothing -- the
        assertion is a fresh Find() through the Operations layer after the
        rollback.
        """
        pos_ops = target_sandbox.POS
        name = f"{TEST_PREFIX}abort_me"

        pos_ops.Create(name, f"{TEST_PREFIX}am")
        # Pre-state, read back from the LCM rather than assumed.
        assert pos_ops.Find(name) is not None, "setup failed: POS was not created"

        assert target_sandbox.AbortSession() is True

        # Post-state, re-queried after the rollback.
        assert pos_ops.Find(name) is None, (
            "AbortSession() returned True but the created POS survived -- "
            "Rollback(0) discarded undo records only, not the data."
        )

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_modification_to_preexisting_object_is_reverted(self, target_sandbox):
        """
        A create-then-abort could in principle be explained by the object
        never having existed on disk. This aborts a MODIFICATION to an object
        restored from the `.fwbackup` instead: it exists across the rollback
        boundary, so its field value must return to the pre-abort reading.

        Note the object is taken from the fixture's existing data rather than
        created-and-committed here, because `SaveChanges()` cannot be used to
        commit mid-session in this mode -- see
        `TestSaveChangesIsUnusableInThisMode` below.
        """
        pos_ops = target_sandbox.POS
        existing = list(pos_ops.GetAll())
        assert existing, "fixture has no pre-existing POS to modify"
        target = existing[0]

        before = pos_ops.GetName(target)
        assert before, "pre-existing POS has no name to revert to"

        pos_ops.SetName(target, f"{TEST_PREFIX}renamed_then_aborted")
        assert pos_ops.GetName(target) == f"{TEST_PREFIX}renamed_then_aborted"

        assert target_sandbox.AbortSession() is True

        # Re-query by name rather than trusting the stale handle.
        assert pos_ops.Find(before) is not None, (
            f"AbortSession() did not restore the original name {before!r}"
        )
        assert pos_ops.Find(f"{TEST_PREFIX}renamed_then_aborted") is None, (
            "AbortSession() left the rename in place"
        )


class TestEnvelopeIsReopened:
    """Claim 2: the O2 catch -- Rollback ENDS the task; A3 must reopen it."""

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_current_depth_is_one_again_after_abort(self, target_sandbox):
        """
        Direct FSM evidence. Rollback(0) sets CurrentProcessingState to
        ReadyForBeginTask (UndoStack.cs:724), which would read as
        CurrentDepth == 0. Reading 1 here can only mean AbortSession()
        reopened BeginNonUndoableTask().
        """
        assert _depth(target_sandbox) == 1
        target_sandbox.POS.Create(f"{TEST_PREFIX}depth_probe", f"{TEST_PREFIX}dp")

        assert target_sandbox.AbortSession() is True

        assert _depth(target_sandbox) == 1, (
            "AbortSession() left the FSM in ReadyForBeginTask -- the session "
            "envelope was not reopened and CloseProject()'s "
            "EndNonUndoableTask() now has no task to end."
        )

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_session_still_writable_after_abort(self, target_sandbox):
        """
        The behavioral form of the same claim, and the stronger one: liblcm
        refuses data changes outside an open unit of work, so a write that
        succeeds AFTER the abort could not have happened unless the envelope
        was genuinely reopened.
        """
        pos_ops = target_sandbox.POS
        pos_ops.Create(f"{TEST_PREFIX}first_wave", f"{TEST_PREFIX}fw")
        target_sandbox.AbortSession()

        name = f"{TEST_PREFIX}second_wave"
        pos_ops.Create(name, f"{TEST_PREFIX}sw")

        assert pos_ops.Find(name) is not None
        # And the write is durable within the session: a further read-modify
        # cycle on it also succeeds, which an FSM stuck in ReadyForBeginTask
        # could not support.
        pos_ops.SetName(pos_ops.Find(name), f"{TEST_PREFIX}second_wave_renamed")
        assert pos_ops.Find(f"{TEST_PREFIX}second_wave_renamed") is not None

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_abort_is_repeatable_in_one_session(self, target_sandbox):
        """Non-terminal: because the envelope is reopened each time, a second
        and third abort behave exactly like the first."""
        pos_ops = target_sandbox.POS

        for i in range(3):
            name = f"{TEST_PREFIX}repeat_{i}"
            pos_ops.Create(name, f"{TEST_PREFIX}r{i}")
            assert target_sandbox.AbortSession() is True
            assert pos_ops.Find(name) is None
            assert _depth(target_sandbox) == 1


class TestAbortDoesNotTouchCommittedData:
    """The honesty boundary stated in the docstring."""

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_data_committed_before_the_session_survives(self, target_sandbox):
        """
        AbortSession() reverts the OPEN unit of work only. Data that was
        already on disk when the session opened is past aborting -- the
        docstring says so, and this proves it is not overselling in the safe
        direction either (an abort that wiped the project would also make
        every other assertion in this file "pass").
        """
        pos_ops = target_sandbox.POS
        preexisting = [pos_ops.GetName(p) for p in pos_ops.GetAll()]
        assert preexisting, "fixture has no pre-existing POS"

        discarded = f"{TEST_PREFIX}uncommitted"
        pos_ops.Create(discarded, f"{TEST_PREFIX}uc")

        assert target_sandbox.AbortSession() is True

        surviving = [pos_ops.GetName(p) for p in pos_ops.GetAll()]
        assert sorted(surviving) == sorted(preexisting), (
            "AbortSession() disturbed data committed before the session: "
            f"{sorted(preexisting)} -> {sorted(surviving)}"
        )
        assert pos_ops.Find(discarded) is None


class TestSaveChangesIsUnusableInThisMode:
    """
    PRE-EXISTING DEFECT, not an A3 regression -- pinned here because A3's
    first draft used `SaveChanges()` to establish committed state and could
    not.

    Under `undoable=False` the session envelope holds the FSM in
    `ProcessingDataChanges` for the whole session, but `SaveInternal()` runs
    `CheckReadyForCommit("Commit at wrong place.")`, which demands
    `ReadyForBeginTask` (`UnitOfWorkService.cs:304`). So `SaveChanges()`
    cannot succeed in the DEFAULT write mode. Worse, per
    `UndoStack.cs:239-246` that check ROLLS BACK the open bundle before
    throwing -- so the failed save also silently discards the session's
    uncommitted work, and it surfaces as a raw
    `System.InvalidOperationException` rather than an `FP_*` error.

    `CloseProject()` is unaffected: it calls `EndNonUndoableTask()` first,
    returning the FSM to `ReadyForBeginTask` before `usm.Save()`.

    This test asserts the CURRENT broken behavior so the defect is recorded
    and measurable. It must be inverted when the defect is fixed.
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_save_changes_raises_commit_at_wrong_place(self, target_sandbox):
        import System

        target_sandbox.POS.Create(f"{TEST_PREFIX}save_probe", f"{TEST_PREFIX}sp")

        with pytest.raises(System.InvalidOperationException) as excinfo:
            target_sandbox.SaveChanges()

        assert "Commit at wrong place" in str(excinfo.value)


class TestUndoableMode:
    """Claim 3: undoable=True has no session envelope to abort."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_nothing_open_between_operations(self, target_sandbox_undoable):
        """
        The live fact that makes AbortSession() return False in this mode:
        no envelope is opened at OpenProject(), so CurrentDepth is 0 until a
        block opens its own UnitOfWork.
        """
        assert _depth(target_sandbox_undoable) == 0
        assert target_sandbox_undoable.AbortSession() is False

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_refuses_inside_an_open_unit_of_work(self, target_sandbox_undoable):
        """
        Inside a block the unit belongs to an UndoableUnitOfWorkHelper.
        AbortSession() must refuse rather than roll back underneath it --
        and, critically, the refusal must leave the unit intact so the block
        still commits normally on exit. A rollback here would instead make
        the helper's Dispose() raise on the way out.
        """
        pos_ops = target_sandbox_undoable.POS
        name = f"{TEST_PREFIX}undoable_block"

        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}abort probe"):
            assert _depth(target_sandbox_undoable) == 1
            with pytest.raises(FP_TransactionError):
                target_sandbox_undoable.AbortSession()
            pos_ops.Create(name, f"{TEST_PREFIX}ub")

        # The block exited cleanly and its write survived: the refusal did
        # not disturb the helper's unit of work.
        assert _depth(target_sandbox_undoable) == 0
        assert pos_ops.Find(name) is not None
