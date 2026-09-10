#
#   test_from_open_project.py
#
#   Class: (module-level tests)
#          CP2 unit tests for FLExProject.FromOpenProject() -- the seam that
#          attaches a flexicon facade to a project the HOST already opened.
#
#          Spec:     specs/flexicon-project-bridge/spec.md (FlexToolsMCP repo)
#          Contract: specs/flexicon-project-bridge/contracts/from-open-project.md
#
#   NO live project is opened anywhere in this file, and therefore NO
#   `requires_live_project` marker: pyproject.toml:90-92 registers that marker
#   for tests that call FLExProject.OpenProject() on a real .fwdata, and the
#   bridge by construction opens nothing (research.md R6). Marking these would
#   be a lie that costs them their place in the default run.
#
#   "Needs no FieldWorks" here means "opens no project" -- NOT "imports with no
#   CLR". flexicon/code/FLExProject.py imports System / clr / SIL.LCModel at
#   module scope, so this file imports flexicon normally and must NEVER stub
#   sys.modules["SIL"]: conftest.py collect_ignores three files that do exactly
#   that, because the stub poisons the real CLR namespace for every later
#   import in the same process.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import (
    FLExProject,
    _ATTACHED_VIEW_SAVE_REFUSAL,
    _ATTACHED_VIEW_UNDOABLE_REFUSAL,
    _IsAttachedView,
)
from flexicon.code.exceptions import (
    FP_ParameterError,
    FP_ReadOnlyError,
    FP_RuntimeError,
    FP_TransactionError,
)


# ---------------------------------------------------------------------------
# Doubles
# ---------------------------------------------------------------------------
#
# The donor is duck-typed at the seam and is NEVER isinstance-checked against
# flexlibs (data-model.md section 2) -- flexlibs may not even be importable in
# the MCP process. So the fake below does not subclass anything: it just
# carries the attributes the contract names.
#
# Every spy here exists to prove a NEGATIVE. The whole point of the attached
# view is that CloseProject() reaches none of EndNonUndoableTask(), usm.Save()
# or Dispose() -- and "did not happen" is only assertable if something was
# watching for it.


class _SpyActionHandler:
    """Stands in for `cache.ActionHandlerAccessor`.

    `CurrentDepth` is a plain int here. On the real interface it is get-only
    and is 1 while a data-changing task is open; a write-enabled flexlibs
    donor therefore arrives with depth already at 1, held for the whole
    session by the host's BeginNonUndoableTask() envelope
    (flexlibs/code/FLExProject.py:262). That standing 1 is precisely why the
    attached-view guard in SaveChanges must come BEFORE the issue-#243 depth
    guard -- otherwise the caller hears a transaction-depth story instead of
    the true one (research.md R3).
    """

    def __init__(self, current_depth=0):
        self.CurrentDepth = current_depth


class _SpyMainCacheAccessor:
    """Stands in for `cache.MainCacheAccessor`, recording envelope calls."""

    def __init__(self):
        self.begin_calls = 0
        self.end_calls = 0

    def BeginNonUndoableTask(self):
        self.begin_calls += 1

    def EndNonUndoableTask(self):
        self.end_calls += 1


class _SpyLexDb:
    pass


class _SpyLangProject:
    def __init__(self):
        self.LexDbOA = _SpyLexDb()


class _FakeCache:
    """Stands in for the borrowed LcmCache.

    The host owns this object. An attached view holding a reference to it must
    be unable to end its envelope or dispose it -- Invariant B
    (data-model.md section 1).
    """

    def __init__(self, current_depth=0):
        self.LangProject = _SpyLangProject()
        self.MainCacheAccessor = _SpyMainCacheAccessor()
        self.ActionHandlerAccessor = _SpyActionHandler(current_depth)
        self.disposed = False

    def Dispose(self):
        self.disposed = True

    @property
    def envelope_ended(self):
        return self.MainCacheAccessor.end_calls > 0


class _FakeDonor:
    """The object a host hands Main().

    Deliberately minimal: `project` and `writeEnabled` are the only two
    attributes the contract REQUIRES of a donor. `lp` and `lexDB` are absent
    on purpose so the default construction also exercises the derive-from-cache
    path (contract section 2.2).
    """

    def __init__(self, write_enabled=True, current_depth=None):
        if current_depth is None:
            # Mirror the real hosts: a write-enabled flexlibs donor arrives
            # inside an open non-undoable task (depth 1); a read-only one has
            # no envelope at all (depth 0).
            current_depth = 1 if write_enabled else 0
        self.project = _FakeCache(current_depth)
        self.writeEnabled = write_enabled


class _PartialDonor:
    """A donor that is missing the cache entirely.

    This is the shape that used to fail as an AttributeError fifty frames deep
    inside an operation -- unreadable to the non-programmer this project exists
    for (SPEC 3c).
    """

    def __init__(self):
        self.writeEnabled = True


class _EmptyDonor:
    """Missing BOTH required attributes -- the seam must name both, not just
    the first it happens to check."""


class _OwnedProjectDouble:
    """A minimal double for a project that OWNS its cache (never went
    through FromOpenProject) -- used only by the T2.2c owned-project
    regression lock.

    Deliberately NOT `unittest.mock.Mock`: a bare `Mock()` auto-vivifies
    any attribute access, so `hasattr(mock, "_attached_donor")` is True on
    ANY Mock even though nothing ever assigned it -- which would make
    `_IsAttachedView` silently misclassify an owned project as an attached
    view, which is exactly the false pass this lock exists to catch. A
    plain object with only the two attributes it actually carries is the
    only double that proves the negative honestly.
    """

    def __init__(self):
        self.writeEnabled = True
        self._undoable = False


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def donor():
    """A write-enabled donor, in the state a real FlexTools host produces."""

    return _FakeDonor(write_enabled=True)


@pytest.fixture
def view(donor):
    """An attached view over that donor's cache."""

    return FLExProject.FromOpenProject(donor)


# ---------------------------------------------------------------------------
# US1 -- attach a flexicon facade to a project the host already opened
# ---------------------------------------------------------------------------


class TestAttach:
    """T2.1a -- the view borrows the donor's cache and derives the rest."""

    def test_borrows_the_cache_by_identity(self, donor, view):
        # Identity, not equality: the whole design is that ONE cache exists
        # and the view merely points at it (Invariant B).
        assert view.project is donor.project

    def test_derives_lp_and_lexdb_when_the_donor_omits_them(self, donor, view):
        # _FakeDonor carries neither `lp` nor `lexDB`, so this exercises the
        # derive-from-cache branch of contract section 2.2.
        assert view.lp is donor.project.LangProject
        assert view.lexDB is donor.project.LangProject.LexDbOA

    def test_prefers_the_donors_lp_and_lexdb_when_present(self, donor):
        # A flexlibs donor DOES carry both. Preferring them over a re-derive
        # keeps the view pointing at the same objects the host is using.
        donor.lp = _SpyLangProject()
        donor.lexDB = _SpyLexDb()

        view = FLExProject.FromOpenProject(donor)

        assert view.lp is donor.lp
        assert view.lexDB is donor.lexDB

    def test_derives_past_a_none_valued_lp(self, donor):
        # "Present" is not enough -- a donor carrying lp=None must fall through
        # to the cache rather than installing None as the view's lp.
        donor.lp = None
        donor.lexDB = None

        view = FLExProject.FromOpenProject(donor)

        assert view.lp is donor.project.LangProject
        assert view.lexDB is donor.project.LangProject.LexDbOA

    @pytest.mark.parametrize("write_enabled", [True, False])
    def test_borrows_write_enabled_verbatim(self, write_enabled):
        # Including False. The view never upgrades its own permissions.
        donor = _FakeDonor(write_enabled=write_enabled)

        view = FLExProject.FromOpenProject(donor)

        assert view.writeEnabled is write_enabled

    def test_marks_itself_as_attached(self, donor, view):
        assert view._attached_donor is donor

    def test_does_not_mutate_the_donor(self, donor):
        before = dict(donor.__dict__)

        FLExProject.FromOpenProject(donor)

        assert donor.__dict__ == before

    def test_opens_nothing_and_closes_nothing(self, donor, view):
        # The seam must not touch the host's envelope on the way in. This is
        # the property that makes the bridge safe to call on a project FLEx
        # is holding -- reopening it would raise FP_FileLockedError.
        assert donor.project.MainCacheAccessor.begin_calls == 0
        assert donor.project.MainCacheAccessor.end_calls == 0
        assert donor.project.disposed is False

    def test_is_a_real_flexproject_with_the_full_facade(self, view):
        # Invariant C: operations receive the VIEW, so every flexicon
        # attribute resolves on flexicon's own class and only the cache is
        # foreign. This is what makes the 42-missing-attribute measurement in
        # SPEC section 1 irrelevant to this design rather than fatal to it.
        assert isinstance(view, FLExProject)

        for facade in ("LexEntry", "Senses", "Variants"):
            assert hasattr(type(view), facade), f"missing facade: {facade}"


class TestUndoableModeIsForcedOff:
    """T2.1b -- a view is Phase 1, unconditionally."""

    def test_undoable_is_false_even_for_a_write_enabled_donor(self, view):
        # The donor is write-enabled and, under a real host, already sits
        # inside a session-long BeginNonUndoableTask() envelope. Opening a
        # Phase 2 undoable unit of work inside that nests the wrong kind of
        # task, so the view is Phase 1 no matter what (research.md R2).
        assert view.writeEnabled is True
        assert view._undoable is False

    def test_undoable_is_false_for_a_read_only_donor(self):
        view = FLExProject.FromOpenProject(_FakeDonor(write_enabled=False))

        assert view._undoable is False

    def test_ignores_an_undoable_flag_on_the_donor(self, donor):
        # A flexicon donor carries _undoable. It is NOT honoured: mode is a
        # property of who owns the envelope, not of who was asked.
        donor._undoable = True

        view = FLExProject.FromOpenProject(donor)

        assert view._undoable is False


class TestIdempotence:
    """T2.1c -- calling the seam under the MCP is a no-op."""

    def test_returns_a_flexicon_donor_unchanged(self, donor):
        # Under the MCP the donor is ALREADY a flexicon FLExProject that owns
        # its project. Returning it by identity preserves that ownership, its
        # Phase 2 mode, and its cached operations objects. Building a fresh
        # view instead would silently downgrade an MCP session to Phase 1 and
        # leave two objects believing they own one cache (research.md R4).
        owned = FLExProject.__new__(FLExProject)
        owned.project = donor.project
        owned.lp = donor.project.LangProject
        owned.lexDB = donor.project.LangProject.LexDbOA
        owned.writeEnabled = True
        owned._undoable = True

        assert FLExProject.FromOpenProject(owned) is owned

    def test_does_not_mark_an_owned_project_as_attached(self, donor):
        owned = FLExProject.__new__(FLExProject)
        owned.project = donor.project
        owned.lp = donor.project.LangProject
        owned.lexDB = donor.project.LangProject.LexDbOA
        owned.writeEnabled = True
        owned._undoable = True

        result = FLExProject.FromOpenProject(owned)

        # It still owns its project, so it must NOT acquire the marker that
        # would strip its ability to save and close (Invariant A).
        assert not hasattr(result, "_attached_donor")
        assert result._undoable is True

    def test_a_view_passed_back_through_the_seam_is_returned_unchanged(self, view):
        # A view IS a FLExProject, so the isinstance short-circuit catches it
        # first and it is never re-attached to itself.
        assert FLExProject.FromOpenProject(view) is view


class TestDonorValidation:
    """T2.3 -- an unusable donor fails AT the seam, readably."""

    def test_missing_project_raises_parameter_error(self):
        with pytest.raises(FP_ParameterError) as excinfo:
            FLExProject.FromOpenProject(_PartialDonor())

        message = str(excinfo.value)
        assert "project" in message
        assert "FromOpenProject" in message
        # __module__ is the only honest discriminator: both candidate donor
        # classes are literally named FLExProject (SPEC section 2).
        assert _PartialDonor.__module__ in message

    def test_none_valued_project_is_treated_as_missing(self):
        donor = _PartialDonor()
        donor.project = None

        with pytest.raises(FP_ParameterError):
            FLExProject.FromOpenProject(donor)

    def test_names_every_missing_attribute_not_just_the_first(self):
        with pytest.raises(FP_ParameterError) as excinfo:
            FLExProject.FromOpenProject(_EmptyDonor())

        message = str(excinfo.value)
        assert "project" in message
        assert "writeEnabled" in message

    def test_parameter_error_is_catchable_as_runtime_error(self):
        # Callers already catch FP_RuntimeError broadly; reusing the existing
        # "you passed me the wrong thing" signal rather than inventing a new
        # exception type keeps them working (research.md R5).
        assert issubclass(FP_ParameterError, FP_RuntimeError)

    def test_validation_failure_leaves_the_donor_untouched(self):
        donor = _PartialDonor()
        before = dict(donor.__dict__)

        with pytest.raises(FP_ParameterError):
            FLExProject.FromOpenProject(donor)

        assert donor.__dict__ == before


# ---------------------------------------------------------------------------
# US2 -- lifecycle refusals on an attached view
# ---------------------------------------------------------------------------
#
# All three guards below branch on `_IsAttachedView(self)`
# (`hasattr(self, "_attached_donor")`) -- never on `writeEnabled` or
# `_undoable` (contract section 4). T009-T012 land the guards themselves;
# this file only proves what MUST be true once they do, and that the
# existing owned-project behaviour is untouched in the meantime.


class TestAttachedViewCloseProject:
    """T2.2a -- CloseProject() on a view is a no-op.

    It must never reach EndNonUndoableTask(), usm.Save(), Dispose(), or
    the owned path's `del self.project` in its `finally` -- the host's
    cache, and the view's reference to it, must both survive untouched.
    """

    def test_returns_none_without_raising(self, view):
        assert view.CloseProject() is None

    def test_does_not_end_the_hosts_non_undoable_task(self, view, donor):
        view.CloseProject()

        assert donor.project.MainCacheAccessor.end_calls == 0

    def test_does_not_save_or_dispose_the_hosts_cache(self, view, donor):
        view.CloseProject()

        assert donor.project.disposed is False

    def test_leaves_the_view_pointed_at_the_donors_cache(self, view, donor):
        # The owned path's CloseProject() ends in `finally: ... del
        # self.project`. Proving the view never got there is only honest
        # if we check the attribute still exists at all, not just that it
        # still equals what it did.
        view.CloseProject()

        assert hasattr(view, "project")
        assert view.project is donor.project


class TestAttachedViewSaveChanges:
    """T2.2b -- SaveChanges() on a view must refuse with the ATTACHED-VIEW
    story, in EVERY donor state -- not with FP_ReadOnlyError, and not with
    the session-envelope's FP_TransactionError. Both of those are also
    FP_RuntimeError subclasses, so a bare `pytest.raises(FP_RuntimeError)`
    is blind to either wrong outcome; every assertion here also pins the
    EXACT type.
    """

    @staticmethod
    def _assert_is_the_attached_view_refusal(exc):
        assert type(exc) is FP_RuntimeError
        assert not isinstance(exc, (FP_ReadOnlyError, FP_TransactionError))
        assert _ATTACHED_VIEW_SAVE_REFUSAL in str(exc)

    def test_write_enabled_donor_at_depth_zero(self):
        donor = _FakeDonor(write_enabled=True, current_depth=0)
        view = FLExProject.FromOpenProject(donor)

        with pytest.raises(FP_RuntimeError) as excinfo:
            view.SaveChanges()

        self._assert_is_the_attached_view_refusal(excinfo.value)

    def test_write_enabled_donor_at_depth_one_does_not_tell_a_depth_story(self):
        # The real flexlibs host holds the session-long envelope at depth 1
        # for the WHOLE session (research.md R3) -- the attached-view guard
        # must fire BEFORE the issue-#243 depth guard, or the caller hears a
        # transaction-depth story instead of "the host owns the save".
        donor = _FakeDonor(write_enabled=True, current_depth=1)
        view = FLExProject.FromOpenProject(donor)

        with pytest.raises(FP_RuntimeError) as excinfo:
            view.SaveChanges()

        self._assert_is_the_attached_view_refusal(excinfo.value)
        assert "CurrentDepth" not in str(excinfo.value)

    def test_read_only_donor_still_gets_the_attached_view_refusal(self):
        # Not FP_ReadOnlyError: the attached-view guard is checked BEFORE
        # the writeEnabled check (contract section 4), on a read-only donor
        # too.
        donor = _FakeDonor(write_enabled=False)
        view = FLExProject.FromOpenProject(donor)

        with pytest.raises(FP_RuntimeError) as excinfo:
            view.SaveChanges()

        self._assert_is_the_attached_view_refusal(excinfo.value)

    def test_the_refusal_constant_does_not_repeat_closeproject_advice(self):
        # research.md R7: on a view, CloseProject() is a silent no-op
        # (TestAttachedViewCloseProject above), so repeating that standing
        # advice would produce a green run that writes nothing -- the exact
        # failure class this seam exists to end. Asserted against the
        # CONSTANT, not against a caught exception's str(), so prose drift
        # elsewhere in the module cannot mask a regression here.
        assert "CloseProject" not in _ATTACHED_VIEW_SAVE_REFUSAL

    def test_the_refusal_constant_is_ascii(self):
        # CLAUDE.md Windows console rule.
        _ATTACHED_VIEW_SAVE_REFUSAL.encode("ascii")


class TestAttachedViewUndoableOperation:
    """T2.2c -- UndoableOperation() on a write-enabled view must refuse
    with the ATTACHED-VIEW wording, not the owned-project "opened with
    undoable=False" wording -- nobody called OpenProject on a view
    (research.md R2)."""

    def test_raises_transaction_error_with_the_attached_view_wording(self, view):
        with pytest.raises(FP_TransactionError) as excinfo:
            with view.UndoableOperation("label"):
                pass

        assert _ATTACHED_VIEW_UNDOABLE_REFUSAL in str(excinfo.value)

    def test_the_refusal_constant_does_not_blame_an_argument_never_passed(self):
        # research.md R2: the owned-project wording blames an
        # OpenProject(undoable=...) call that never happened on a view.
        # Asserted against the CONSTANT, not str(exc).
        assert "opened with undoable=False" not in _ATTACHED_VIEW_UNDOABLE_REFUSAL

    def test_the_refusal_constant_is_ascii(self):
        _ATTACHED_VIEW_UNDOABLE_REFUSAL.encode("ascii")

    def test_read_only_attached_view_reports_read_only_not_attached_view(self):
        """A read-only view gets FP_ReadOnlyError, and that is CORRECT.

        This is the one place an attached-view guard deliberately does NOT
        come first, and the asymmetry with SaveChanges() is the point:

        * SaveChanges() must refuse even a WRITE-ENABLED view, because the
          reason is that the host owns the save -- not read-onlyness. A
          read-only diagnosis there would misdescribe the refusal.
        * Here a read-only view cannot write by any route at all. "Project
          is not write-enabled" is true and actionable (the host must open
          it write-enabled). The attached-view message would instead point
          at Transaction(), which on a read-only project also fails -- a
          wrong answer in the shape of a helpful one, which is the exact
          failure class this feature exists to end.

        QC flagged the ordering as a contract violation against section 4's
        "never branch on writeEnabled". That rule is Invariant A -- it
        governs how a guard DETECTS a view (only `_attached_donor` can,
        since a read-only owned project and a read-only view agree on
        `writeEnabled`) -- not the order against an unrelated pre-existing
        check. Behaviour kept; pinned here so a future reorder breaks a
        named test instead of silently changing the message.
        """

        read_only_view = FLExProject.FromOpenProject(
            _FakeDonor(write_enabled=False)
        )
        assert _IsAttachedView(read_only_view) is True

        with pytest.raises(FP_ReadOnlyError) as excinfo:
            with read_only_view.UndoableOperation("label"):
                pass

        # The attached-view wording must NOT appear: it would advise
        # Transaction(), which cannot write on a read-only project either.
        assert _ATTACHED_VIEW_UNDOABLE_REFUSAL not in str(excinfo.value)


class TestOwnedProjectRegressionLocks:
    """Tripwire: the guards T009-T012 add must layer IN FRONT of the
    existing owned-project behaviour, never replace it. These must stay
    GREEN both before and after that implementation lands.
    """

    def test_is_attached_view_is_false_for_an_owned_project(self):
        assert _IsAttachedView(_OwnedProjectDouble()) is False

    def test_is_attached_view_is_true_for_an_attached_view(self, view):
        assert _IsAttachedView(view) is True

    def test_owned_project_keeps_the_original_undoable_false_wording(self):
        from flexicon.code.undoable_operation import _FLExUndoableOperation

        owned = _OwnedProjectDouble()
        assert not hasattr(owned, "_attached_donor")

        with pytest.raises(FP_TransactionError) as excinfo:
            with _FLExUndoableOperation(owned, "label"):
                pass

        assert "opened with undoable=False" in str(excinfo.value)


class TestExportSurface:
    """SPEC T1.4 -- the classmethod rides along on an existing export."""

    def test_reachable_from_the_package_root(self):
        # No new export is added; FLExProject is already exported from
        # flexicon/__init__.py. This asserts the seam is reachable exactly as
        # the portable module shape spells it: `from flexicon import
        # FLExProject`.
        import flexicon

        assert hasattr(flexicon.FLExProject, "FromOpenProject")

    def test_is_a_classmethod_not_an_instance_method(self):
        # The portable shape calls it on the CLASS, before any instance
        # exists on the module's side.
        assert isinstance(
            FLExProject.__dict__["FromOpenProject"], classmethod
        )
