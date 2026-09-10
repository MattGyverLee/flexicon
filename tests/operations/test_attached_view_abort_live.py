#
#   test_attached_view_abort_live.py
#
#   Live write-path verification for the attached-view guard on
#   `FLExProject.AbortSession()` (the FromOpenProject bridge).
#
#   Structure copied from tests/operations/test_abort_session_live.py, which
#   in turn follows tests/operations/test_target_live_smoke.py, the canonical
#   template. Runs against tempdir sandboxes restored from the Target
#   `.fwbackup` -- never the user's real Target project, because the failure
#   this guard prevents is precisely an unwanted Rollback(0) of a whole
#   session, and a regression here would destroy live data.
#
#   Why this cannot be verified offline: the offline doubles in
#   tests/test_from_open_project.py model liblcm's UndoStack from source but
#   do not execute it. Two claims need the real FSM:
#
#     1. The refusal really leaves the HOST's uncommitted data in place. The
#        doubles can only show that Rollback was not CALLED; only a live
#        cache can show that a real pending edit survives and is still
#        readable back through a fresh query.
#     2. The refusal really leaves the host's envelope intact and usable --
#        CurrentDepth still 1, and the host still able to write and to run
#        its OWN AbortSession() afterwards. A guard that returned early but
#        disturbed the FSM would pass every offline assertion.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import (
    FLExProject,
    _ATTACHED_VIEW_ABORT_REFUSAL,
)
from flexicon.code.exceptions import (
    FP_ReadOnlyError,
    FP_RuntimeError,
    FP_TransactionError,
)

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


def _depth(project):
    """CurrentDepth straight off the live action handler (1 or 0 only)."""
    return project.project.ActionHandlerAccessor.CurrentDepth


class _HostDonor:
    """A duck-typed stand-in for the flexlibs FLExProject a real host hands
    Main(), wrapping a LIVE cache.

    Deliberately not a flexicon FLExProject: FromOpenProject() is idempotent
    and returns a flexicon donor unchanged, so a flexicon donor could never
    produce the attached view under test. A real FlexTools host hands over a
    *flexlibs* object, which is duck-typed at the seam and never
    isinstance-checked -- this class is that shape, over the sandbox's real
    LcmCache.
    """

    def __init__(self, live_project):
        self.project = live_project.project
        self.lp = live_project.lp
        self.lexDB = live_project.lexDB
        self.writeEnabled = live_project.writeEnabled


class TestFixtureReachesLiveLCM:
    """Prove the view under test wraps a real LCM cache, not a mock."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_view_borrows_the_live_cache_and_is_attached(self, target_sandbox):
        view = FLExProject.FromOpenProject(_HostDonor(target_sandbox))

        assert getattr(view, "project", None) is not None, (
            "the view has no underlying LCM cache -- this is a mock, not a "
            "live project."
        )
        assert view.project is target_sandbox.project
        assert view._attached_donor is not None
        # The host's session-long envelope is open: this is the unit of work
        # an unguarded AbortSession() would roll back.
        assert _depth(view) == 1


class TestRefusalOnALiveAttachedView:
    """The guard fires against a real action handler."""

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_refuses_with_the_attached_view_wording(self, target_sandbox):
        view = FLExProject.FromOpenProject(_HostDonor(target_sandbox))

        with pytest.raises(FP_RuntimeError) as excinfo:
            view.AbortSession()

        # Exact type: FP_ReadOnlyError and the undoable-mode
        # FP_TransactionError are both FP_RuntimeError subclasses.
        assert type(excinfo.value) is FP_RuntimeError
        assert not isinstance(excinfo.value, (FP_ReadOnlyError, FP_TransactionError))
        assert _ATTACHED_VIEW_ABORT_REFUSAL in str(excinfo.value)


class TestHostDataSurvivesTheRefusal:
    """Claim 1: the host's uncommitted edits are not discarded.

    This is the incident the guard exists to prevent -- a module aborting
    after its own error and taking the host's unrelated pending work with it.
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_host_edit_made_before_the_module_ran_survives(self, target_sandbox):
        pos_ops = target_sandbox.POS

        # Edit A: the HOST's, made before any module was invoked.
        host_name = f"{TEST_PREFIX}host_edit_A"
        pos_ops.Create(host_name, f"{TEST_PREFIX}hA")
        # Pre-state, read back from the LCM rather than assumed.
        assert pos_ops.Find(host_name) is not None, (
            "setup failed: host POS was not created"
        )

        # The module attaches and makes edit B, then hits an error and tries
        # to abandon its own work.
        view = FLExProject.FromOpenProject(_HostDonor(target_sandbox))
        module_name = f"{TEST_PREFIX}module_edit_B"
        view.POS.Create(module_name, f"{TEST_PREFIX}mB")

        with pytest.raises(FP_RuntimeError):
            view.AbortSession()

        # Post-state, re-queried after the refusal. Edit A is the assertion
        # that matters: an unguarded abort discards it along with B.
        assert pos_ops.Find(host_name) is not None, (
            "AbortSession() on an attached view discarded the HOST's "
            "uncommitted edit -- the exact incident the guard prevents."
        )
        # B survives too, and that is correct: the module cannot discard on a
        # view, which is why the refusal tells it to report the error instead.
        assert pos_ops.Find(module_name) is not None


class TestHostEnvelopeSurvivesTheRefusal:
    """Claim 2: the host's unit of work is left exactly as it was."""

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_current_depth_is_unchanged(self, target_sandbox):
        view = FLExProject.FromOpenProject(_HostDonor(target_sandbox))
        before = _depth(target_sandbox)
        assert before == 1

        with pytest.raises(FP_RuntimeError):
            view.AbortSession()

        assert _depth(target_sandbox) == before, (
            "the refusal disturbed the host's FSM state"
        )

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_host_can_still_write_after_the_refusal(self, target_sandbox):
        """The behavioural form of the same claim, and the stronger one:
        liblcm refuses data changes outside an open unit of work, so a
        successful host write after the refusal proves the envelope was
        neither ended nor replaced."""
        view = FLExProject.FromOpenProject(_HostDonor(target_sandbox))

        with pytest.raises(FP_RuntimeError):
            view.AbortSession()

        name = f"{TEST_PREFIX}host_write_after_refusal"
        target_sandbox.POS.Create(name, f"{TEST_PREFIX}hwar")
        assert target_sandbox.POS.Find(name) is not None

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_the_host_itself_can_still_abort(self, target_sandbox):
        """The owner's own AbortSession() still works normally afterwards --
        the guard adds a refusal on the view without changing the owned
        path's behaviour on the very same cache."""
        view = FLExProject.FromOpenProject(_HostDonor(target_sandbox))
        name = f"{TEST_PREFIX}owner_aborts_this"
        target_sandbox.POS.Create(name, f"{TEST_PREFIX}oat")
        assert target_sandbox.POS.Find(name) is not None

        with pytest.raises(FP_RuntimeError):
            view.AbortSession()

        # The host owns the decision, and can still take it.
        assert target_sandbox.AbortSession() is True
        assert target_sandbox.POS.Find(name) is None
        assert _depth(target_sandbox) == 1
