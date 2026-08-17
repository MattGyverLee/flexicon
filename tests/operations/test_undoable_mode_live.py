#
#   test_undoable_mode_live.py
#
#   Live write-path verification for the `undoable=True` mode: the mode
#   B1/B2/B3 exist to serve, and the destination D3 designates.
#
#   WHY THIS FILE EXISTS (the DEF blocker, recorded in this feature's
#   concerns after A3's live run):
#
#     Every live suite landed before this one -- batches 8-11
#     (test_lexicon_brackets_live.py, test_grammar_brackets_live.py, ...),
#     test_target_live_smoke.py, and most of test_abort_session_live.py --
#     uses the `target_sandbox` fixture, which opens `undoable=False`. So
#     B1 (the UndoableUnitOfWorkHelper rewrite) and B2 (the 295-site
#     bracket sweep) were marked complete, for the mode they exist to
#     serve, on offline-double evidence alone.
#
#     That was not a theoretical gap. The doubles had ENCODED a bug: they
#     modelled `RollBack` as an assignable attribute, so 30 offline tests
#     passed against code that discarded every single write when run live
#     (D9 -- pythonnet synthesizes no property for a `{private get; set;}`
#     member, so `helper.RollBack = False` landed as a Python attribute on
#     the wrapper while the real field kept its constructor default of
#     True, and Dispose() rolled back every clean unit of work). A3's live
#     run found it by accident. The D9 fix is a POINT fix; this file is the
#     coverage.
#
#   DEF (flip the default to `undoable=True`) is gated on this file, so
#   the standard it has to meet is not "the happy path works" but "each
#   claim the mode makes is verified against the real liblcm FSM, and each
#   is read back through the LCM rather than asserted on the value passed
#   in". The claims, and where they are covered:
#
#     1. A clean block COMMITS               -- TestCleanBlockCommits
#        (the direct D9 regression: this is what silently failed live)
#     2. An exception ROLLS BACK, for real   -- TestExceptionRollsBackLive
#        (the entire point of the mode; never once verified live before)
#     3. Each operation is its own UoW       -- TestPerOperationUnitOfWork
#        (the `per-operation-uow` capability token B4 ships)
#     4. Nesting joins, never re-opens       -- TestNestingLive
#        (B1's core claim; B1t proved it against doubles only)
#     5. Undo/Redo drive the live stack      -- TestUndoRedoLive  (B3)
#     6. The 295 brackets work in THIS mode  -- TestBracketsAcrossDomains
#        (batches 8-11 proved them under `undoable=False` only)
#     7. Writes SURVIVE close and reopen     -- TestPersistenceAcrossReopen
#        (issue #237 / task B2t -- the one question a rolled-back-everything
#        build still answers "yes" to on every in-session assertion)
#     8. D9 cannot silently return           -- TestD9RollBackRegression
#
#   Structure copied from tests/operations/test_abort_session_live.py,
#   itself from tests/operations/test_target_live_smoke.py, the canonical
#   template. Every test runs against a tempdir sandbox restored from the
#   Target `.fwbackup` -- the user's real Target project is never touched.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pathlib

import pytest

from flexicon.code.FLExProject import FLExProject, FP_TransactionError

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


class _Boom(Exception):
    """Raised on purpose inside a block, to force the rollback path."""


def _ah(project):
    """The live liblcm action handler."""
    return project.project.ActionHandlerAccessor


def _depth(project):
    """CurrentDepth straight off the live action handler."""
    return _ah(project).CurrentDepth


def _seq_count(project):
    """Number of undoable sequences (one per committed UnitOfWork)."""
    return _ah(project).UndoableSequenceCount


def _make_entry(project, tag):
    """Create a TEST_-prefixed entry on the live sandbox."""
    return project.LexEntry.Create(f"{TEST_PREFIX}{tag}")


class TestUndoableFixtureReachesLiveLCM:
    """Prove these writes land on a real LCM cache, in the right mode,
    from THIS checkout."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_sandbox_is_live_and_undoable(self, target_sandbox_undoable):
        assert target_sandbox_undoable.writeEnabled is True
        assert target_sandbox_undoable._undoable is True
        assert getattr(target_sandbox_undoable, "project", None) is not None, (
            "target_sandbox_undoable has no underlying LCM cache -- this is "
            "a mock, not a live project."
        )

    @pytest.mark.live_phase("FLExProject", "read")
    def test_code_under_test_is_this_checkout_not_site_packages(self):
        """
        Recorded concern: the FlexTools MCP runner imports pyflexicon from
        site-packages rather than this checkout, and a live run against the
        RELEASED package would prove nothing about uncommitted work. pytest
        resolves imports differently, but the failure is silent either way,
        so assert it rather than assume it.
        """
        from flexicon.code import BaseOperations

        repo_root = pathlib.Path(__file__).resolve().parents[2]
        module_path = pathlib.Path(BaseOperations.__file__).resolve()
        assert repo_root in module_path.parents, (
            f"BaseOperations was imported from {module_path}, which is "
            f"outside this checkout ({repo_root}) -- this run is testing "
            f"the installed package, not the working tree."
        )

    @pytest.mark.live_phase("FLExProject", "read")
    def test_no_session_envelope_is_open(self, target_sandbox_undoable):
        """
        The structural difference from `undoable=False`, and the reason a
        `undoable=False` fixture cannot stand in for this one: this mode
        opens no `BeginNonUndoableTask()` envelope at OpenProject, so
        nothing is open until a block or a bracketed operation opens it.
        """
        assert _depth(target_sandbox_undoable) == 0


class TestD9RollBackRegression:
    """
    Claim 8. D9 was invisible offline because the doubles modelled the
    .NET surface from the C# source rather than from pythonnet. Pin the
    real surface here, where only a live LCM can answer.
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_pythonnet_exposes_set_rollback_but_no_rollback_property(
        self, target_sandbox_undoable
    ):
        """
        `RollBack` is `{private get; set;}`. pythonnet synthesizes no
        property when the getter is private -- it surfaces only
        `set_RollBack`. The lethal part is that `helper.RollBack = False`
        does NOT raise: it lands as a plain Python attribute on the wrapper
        while the real field keeps its constructor default of True.

        Asserting `hasattr(helper, "RollBack") is False` on a REAL helper is
        what the doubles could not do, and it is what makes a future
        reviewer unable to "simplify" the two `set_RollBack(...)` call sites
        back into the assignment form without a live test going red.
        """
        from SIL.LCModel.Infrastructure import UndoableUnitOfWorkHelper

        helper = UndoableUnitOfWorkHelper(
            _ah(target_sandbox_undoable), f"{TEST_PREFIX}d9 probe", f"{TEST_PREFIX}d9 probe"
        )
        try:
            assert not hasattr(helper, "RollBack"), (
                "pythonnet now exposes a `RollBack` property. D9's premise "
                "has changed -- re-verify both call sites in transaction.py "
                "and undoable_operation.py before relying on either form."
            )
            assert hasattr(helper, "set_RollBack"), (
                "`set_RollBack` is gone -- the only path this build has to "
                "clear the rollback flag no longer exists."
            )
        finally:
            helper.set_RollBack(True)
            helper.Dispose()

        assert _depth(target_sandbox_undoable) == 0


class TestCleanBlockCommits:
    """
    Claim 1, and the direct regression test for D9: under the bug, every
    assertion below failed live while the whole offline suite stayed green.
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_write_in_undoable_operation_survives_block_exit(
        self, target_sandbox_undoable
    ):
        pos_ops = target_sandbox_undoable.POS
        name = f"{TEST_PREFIX}clean_commit"

        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}commit probe"):
            pos_ops.Create(name, f"{TEST_PREFIX}cc")

        # Re-queried through the Operations layer AFTER the helper disposed.
        assert pos_ops.Find(name) is not None, (
            "A clean UndoableOperation block discarded its write -- this is "
            "the D9 failure shape (Dispose() rolling back a clean unit of "
            "work because RollBack never reached .NET)."
        )
        assert _depth(target_sandbox_undoable) == 0, (
            "the block's UnitOfWork was left open"
        )

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_committed_block_lands_on_the_undo_stack(self, target_sandbox_undoable):
        """
        A clean commit must leave something to undo. Under D9 the rollback
        left `CanUndo()` False and the sequence count unmoved -- which is
        the machine-checkable signature of the bug, independent of any
        data read-back.
        """
        before = _seq_count(target_sandbox_undoable)

        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}stack probe"):
            target_sandbox_undoable.POS.Create(
                f"{TEST_PREFIX}stack_entry", f"{TEST_PREFIX}se"
            )

        assert _seq_count(target_sandbox_undoable) == before + 1
        assert _ah(target_sandbox_undoable).CanUndo() is True


class TestExceptionRollsBackLive:
    """
    Claim 2 -- the promise `undoable=True` exists to make, and the one
    `undoable=False` explicitly cannot make (there, the atomicity unit is
    the whole session; see docs/EXCEPTION_HANDLING.md).
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_created_object_is_gone_after_an_exception(self, target_sandbox_undoable):
        pos_ops = target_sandbox_undoable.POS
        name = f"{TEST_PREFIX}rollback_me"

        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}doomed"):
                pos_ops.Create(name, f"{TEST_PREFIX}rm")
                # Pre-state inside the block, read back rather than assumed.
                assert pos_ops.Find(name) is not None
                raise _Boom()

        assert pos_ops.Find(name) is None, (
            "the UnitOfWork was not rolled back -- an exception inside an "
            "UndoableOperation left its writes applied."
        )
        assert _depth(target_sandbox_undoable) == 0, (
            "the failed block leaked an open UnitOfWork (#234's shape)"
        )

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_modification_to_preexisting_object_is_reverted(
        self, target_sandbox_undoable
    ):
        """
        A create-then-rollback could in principle be explained by the
        object never having been persisted. This rolls back a MODIFICATION
        to an object that exists on both sides of the boundary, so its
        field value must return to the pre-block reading.
        """
        pos_ops = target_sandbox_undoable.POS
        existing = list(pos_ops.GetAll())
        assert existing, "sandbox has no pre-existing POS to modify"

        original = pos_ops.GetName(existing[0])
        assert original, "pre-existing POS has no name to revert to"
        renamed = f"{TEST_PREFIX}renamed_then_rolled_back"

        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}rename"):
                pos_ops.SetName(pos_ops.Find(original), renamed)
                assert pos_ops.Find(renamed) is not None
                raise _Boom()

        # Re-query by name; the handle from before the rollback is stale.
        assert pos_ops.Find(original) is not None, (
            f"rollback did not restore the original name {original!r}"
        )
        assert pos_ops.Find(renamed) is None, "rollback left the rename in place"

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_multi_object_block_is_all_or_nothing(self, target_sandbox_undoable):
        """
        Atomicity across several objects and two Operations classes -- the
        property a per-operation UoW alone would NOT give you, and the
        reason UndoableOperation() takes a block at all.
        """
        entry_ops = target_sandbox_undoable.LexEntry
        pos_ops = target_sandbox_undoable.POS
        form = f"{TEST_PREFIX}atomic_entry"
        pos_name = f"{TEST_PREFIX}atomic_pos"

        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}atomic"):
                entry_ops.Create(form)
                pos_ops.Create(pos_name, f"{TEST_PREFIX}ap")
                assert entry_ops.Find(form) is not None
                assert pos_ops.Find(pos_name) is not None
                raise _Boom()

        assert entry_ops.Find(form) is None, "entry survived an all-or-nothing rollback"
        assert pos_ops.Find(pos_name) is None, "POS survived an all-or-nothing rollback"

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_rolled_back_block_leaves_no_undo_entry(self, target_sandbox_undoable):
        """A rolled-back unit of work must not appear in the FLEx Ctrl+Z
        menu -- there is nothing for a linguist to undo."""
        before = _seq_count(target_sandbox_undoable)

        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}no entry"):
                target_sandbox_undoable.POS.Create(
                    f"{TEST_PREFIX}no_entry", f"{TEST_PREFIX}ne"
                )
                raise _Boom()

        assert _seq_count(target_sandbox_undoable) == before, (
            "a rolled-back block still added an entry to the undo stack"
        )

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_session_is_still_usable_after_a_rollback(self, target_sandbox_undoable):
        """A rollback must not wedge the FSM: the next write still works."""
        pos_ops = target_sandbox_undoable.POS

        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}first"):
                pos_ops.Create(f"{TEST_PREFIX}wave_one", f"{TEST_PREFIX}w1")
                raise _Boom()

        name = f"{TEST_PREFIX}wave_two"
        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}second"):
            pos_ops.Create(name, f"{TEST_PREFIX}w2")

        assert pos_ops.Find(name) is not None
        assert pos_ops.Find(f"{TEST_PREFIX}wave_one") is None


class TestPerOperationUnitOfWork:
    """
    Claim 3 -- the `per-operation-uow` capability token B4 ships. An
    Operations call made OUTSIDE any explicit block must open, commit and
    close its own UnitOfWork, because B2 bracketed all 295 mutation sites.
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_bare_operation_commits_and_closes_its_own_unit_of_work(
        self, target_sandbox_undoable
    ):
        pos_ops = target_sandbox_undoable.POS
        name = f"{TEST_PREFIX}bare_op"
        before = _seq_count(target_sandbox_undoable)

        assert _depth(target_sandbox_undoable) == 0
        pos_ops.Create(name, f"{TEST_PREFIX}bo")

        assert _depth(target_sandbox_undoable) == 0, (
            "a bracketed operation left its UnitOfWork open"
        )
        assert pos_ops.Find(name) is not None
        assert _seq_count(target_sandbox_undoable) == before + 1, (
            "the operation's bracket did not produce exactly one undo entry"
        )

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_each_operation_is_a_separate_undo_entry(self, target_sandbox_undoable):
        pos_ops = target_sandbox_undoable.POS
        before = _seq_count(target_sandbox_undoable)

        for i in range(3):
            pos_ops.Create(f"{TEST_PREFIX}sep_{i}", f"{TEST_PREFIX}s{i}")

        assert _seq_count(target_sandbox_undoable) == before + 3

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_undo_label_is_the_per_site_label_not_the_method_name(
        self, target_sandbox_undoable
    ):
        """
        D5 rationale #2, verified live for the first time. The per-site
        bracket shape was chosen partly to keep argument-derived labels
        ("Create part of speech 'X'") in the FLEx undo menu, which a
        central `func.__name__` bracket would have degraded to
        "POSOperations.Create". That menu is product surface a linguist
        reads, so the claim is worth pinning against the real undo stack
        rather than the source string.
        """
        name = f"{TEST_PREFIX}label_probe"
        target_sandbox_undoable.POS.Create(name, f"{TEST_PREFIX}lp")

        undo_text = _ah(target_sandbox_undoable).GetUndoText()
        assert f"Create part of speech '{name}'" in undo_text, (
            f"undo label lost its argument-derived form: {undo_text!r}"
        )

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_a_failed_operation_adds_no_undo_entry(self, target_sandbox_undoable):
        """
        The property D5's per-site shape exists to preserve: validation
        runs OUTSIDE the bracket, so a rejected input must not open (and,
        under B1, immediately roll back) an empty named undo task. Under a
        dispatch-layer bracket every rejected call would land here.
        """
        before = _seq_count(target_sandbox_undoable)

        with pytest.raises(Exception):
            target_sandbox_undoable.POS.Create("", "")

        assert _seq_count(target_sandbox_undoable) == before, (
            "a rejected operation still opened a unit of work -- validation "
            "has moved inside the bracket"
        )
        assert _depth(target_sandbox_undoable) == 0


class TestNestingLive:
    """
    Claim 4 -- B1's central claim, and the one B1t could only test against
    doubles. A second `BeginUndoTask` while one is open does not merely
    raise in liblcm: `UndoStack.cs:209-216` rolls the ALREADY-OPEN unit
    back first, then throws. Joining is what prevents that.
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_inner_block_joins_rather_than_opening_a_second_task(
        self, target_sandbox_undoable
    ):
        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}outer"):
            assert _depth(target_sandbox_undoable) == 1
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}inner"):
                assert _depth(target_sandbox_undoable) == 1, (
                    "the inner block opened a second undo task instead of "
                    "joining -- liblcm has already rolled the outer one back."
                )
            assert _depth(target_sandbox_undoable) == 1, (
                "the inner block closed the OUTER block's unit of work"
            )
        assert _depth(target_sandbox_undoable) == 0

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_a_bracketed_operation_joins_an_enclosing_block(
        self, target_sandbox_undoable
    ):
        """
        The mixed case that actually occurs in the wild: an explicit
        UndoableOperation() wrapping calls that each carry their own B2
        bracket. All of it must be ONE undo entry, not one per call.
        """
        pos_ops = target_sandbox_undoable.POS
        before = _seq_count(target_sandbox_undoable)

        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}batch"):
            pos_ops.Create(f"{TEST_PREFIX}batch_a", f"{TEST_PREFIX}ba")
            pos_ops.Create(f"{TEST_PREFIX}batch_b", f"{TEST_PREFIX}bb")
            assert _depth(target_sandbox_undoable) == 1

        assert _seq_count(target_sandbox_undoable) == before + 1, (
            "the nested brackets produced more than one undo entry -- they "
            "opened their own units of work instead of joining"
        )
        assert pos_ops.Find(f"{TEST_PREFIX}batch_a") is not None
        assert pos_ops.Find(f"{TEST_PREFIX}batch_b") is not None

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_exception_through_both_levels_rolls_back_everything(
        self, target_sandbox_undoable
    ):
        pos_ops = target_sandbox_undoable.POS
        outer_name = f"{TEST_PREFIX}nest_outer"
        inner_name = f"{TEST_PREFIX}nest_inner"

        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}outer"):
                pos_ops.Create(outer_name, f"{TEST_PREFIX}no")
                with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}inner"):
                    pos_ops.Create(inner_name, f"{TEST_PREFIX}ni")
                    raise _Boom()

        assert pos_ops.Find(outer_name) is None
        assert pos_ops.Find(inner_name) is None
        assert _depth(target_sandbox_undoable) == 0

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_inner_exception_caught_inside_the_outer_block_still_commits(
        self, target_sandbox_undoable
    ):
        """
        The honesty test, and the one consumers most need stated: because
        the inner block JOINS, it has no independent rollback. Catching an
        inner exception inside the outer block therefore commits the
        inner's partial writes along with the outer's -- the unit of work
        belongs to the outermost block, and only its exit decides.

        This is not a defect to fix: opening a real nested unit is exactly
        what liblcm punishes (it would roll the outer one back). It is a
        semantic that must be documented rather than discovered, so it is
        pinned here.
        """
        pos_ops = target_sandbox_undoable.POS
        partial = f"{TEST_PREFIX}inner_partial"

        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}outer commits"):
            try:
                with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}inner"):
                    pos_ops.Create(partial, f"{TEST_PREFIX}ip")
                    raise _Boom()
            except _Boom:
                pass

        assert pos_ops.Find(partial) is not None, (
            "the inner block rolled back independently -- it opened its own "
            "unit of work rather than joining, which is what B1 forbids."
        )


class TestUndoRedoLive:
    """
    Claim 5 -- B3, on the live `ActionHandlerAccessor`. Also the live
    evidence behind CO1's in-process-only scope caveat on issue #235.
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_undo_reverts_and_redo_reapplies(self, target_sandbox_undoable):
        pos_ops = target_sandbox_undoable.POS
        name = f"{TEST_PREFIX}undo_redo"

        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}undoable op"):
            pos_ops.Create(name, f"{TEST_PREFIX}ur")
        assert pos_ops.Find(name) is not None

        assert target_sandbox_undoable.Undo() is True
        assert pos_ops.Find(name) is None, "Undo() did not revert the data"

        assert target_sandbox_undoable.Redo() is True
        assert pos_ops.Find(name) is not None, "Redo() did not reapply the data"

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_undo_reverts_a_whole_block_not_one_mutation(
        self, target_sandbox_undoable
    ):
        """One Ctrl+Z reverses the entire named operation -- the reason
        UndoableOperation() exists as product surface."""
        pos_ops = target_sandbox_undoable.POS
        a, b = f"{TEST_PREFIX}undo_a", f"{TEST_PREFIX}undo_b"

        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}two writes"):
            pos_ops.Create(a, f"{TEST_PREFIX}ua")
            pos_ops.Create(b, f"{TEST_PREFIX}ub")

        assert target_sandbox_undoable.Undo() is True
        assert pos_ops.Find(a) is None
        assert pos_ops.Find(b) is None

    @pytest.mark.live_phase("FLExProject", "read")
    def test_undo_returns_false_on_a_freshly_opened_project(
        self, target_sandbox_undoable
    ):
        """
        Nothing has been done yet, so `CanUndo()` is False and `Undo()`
        must report that rather than raising. This is also half the #235
        scope caveat: a freshly opened LcmCache always starts with an
        empty stack, because undo records live in RAM and are never
        serialized into `.fwdata`.
        """
        assert _ah(target_sandbox_undoable).CanUndo() is False
        assert target_sandbox_undoable.Undo() is False
        assert target_sandbox_undoable.Redo() is False

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_redo_is_dropped_by_a_new_write(self, target_sandbox_undoable):
        """Standard undo-stack semantics, confirmed live: writing after an
        undo discards the redo branch."""
        pos_ops = target_sandbox_undoable.POS

        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}first"):
            pos_ops.Create(f"{TEST_PREFIX}redo_drop", f"{TEST_PREFIX}rd")
        assert target_sandbox_undoable.Undo() is True
        assert _ah(target_sandbox_undoable).CanRedo() is True

        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}second"):
            pos_ops.Create(f"{TEST_PREFIX}redo_drop2", f"{TEST_PREFIX}rd2")

        assert _ah(target_sandbox_undoable).CanRedo() is False
        assert target_sandbox_undoable.Redo() is False


class TestBracketsAcrossDomains:
    """
    Claim 6. Batches 8-11 verified the 295 brackets under `undoable=False`,
    where `_TransactionCM` delegates to `Transaction()` and opens no LCM
    task at all -- so those runs exercised a code path that this mode never
    takes. Re-verify a cross-domain sample where the bracket really does
    construct an `UndoableUnitOfWorkHelper`.

    Domains are sampled rather than exhausted, and deliberately avoid the
    Notebook, Etymology and Example methods this feature's concerns record
    as pre-existing-broken on any live project -- those fail before the
    bracket is entered, so they cannot say anything about bracket behavior
    in either mode.
    """

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_grammar_pos_setname_round_trips_and_rolls_back(
        self, target_sandbox_undoable
    ):
        pos_ops = target_sandbox_undoable.POS
        pos_ops.Create(f"{TEST_PREFIX}dom_pos", f"{TEST_PREFIX}dp")

        renamed = f"{TEST_PREFIX}dom_pos_renamed"
        pos_ops.SetName(pos_ops.Find(f"{TEST_PREFIX}dom_pos"), renamed)
        assert pos_ops.Find(renamed) is not None

        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}dom pos"):
                pos_ops.SetName(pos_ops.Find(renamed), f"{TEST_PREFIX}dom_pos_again")
                raise _Boom()

        assert pos_ops.Find(renamed) is not None, "POS rename rollback failed"

    @pytest.mark.live_phase("LexEntryOperations", "modify")
    def test_lexicon_entry_create_round_trips_and_rolls_back(
        self, target_sandbox_undoable
    ):
        entry_ops = target_sandbox_undoable.LexEntry

        kept = f"{TEST_PREFIX}dom_entry_kept"
        entry_ops.Create(kept)
        assert entry_ops.Find(kept) is not None

        dropped = f"{TEST_PREFIX}dom_entry_dropped"
        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}dom entry"):
                entry_ops.Create(dropped)
                raise _Boom()

        assert entry_ops.Find(dropped) is None
        assert entry_ops.Find(kept) is not None, (
            "the rollback reached past its own unit of work and removed an "
            "entry committed by an earlier one"
        )

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_lexicon_sense_setgloss_round_trips_and_rolls_back(
        self, target_sandbox_undoable
    ):
        sense_ops = target_sandbox_undoable.Senses
        entry = _make_entry(target_sandbox_undoable, "dom_sense")
        sense = sense_ops.Create(entry, f"{TEST_PREFIX}original gloss")

        assert sense_ops.GetGloss(sense) == f"{TEST_PREFIX}original gloss"

        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}dom gloss"):
                sense_ops.SetGloss(sense, f"{TEST_PREFIX}doomed gloss")
                raise _Boom()

        # Re-read through the entry rather than the stale sense handle.
        senses = target_sandbox_undoable.LexEntry.GetSenses(
            target_sandbox_undoable.LexEntry.Find(f"{TEST_PREFIX}dom_sense")
        )
        glosses = [sense_ops.GetGloss(s) for s in senses]
        assert f"{TEST_PREFIX}original gloss" in glosses
        assert f"{TEST_PREFIX}doomed gloss" not in glosses

    @pytest.mark.live_phase("LexEntryOperations", "delete")
    def test_delete_is_rolled_back_too(self, target_sandbox_undoable):
        """
        Rollback of a DELETE, not just of a create or a field write -- the
        direction where "it looks fine" and "the object is gone forever"
        are hardest to tell apart.
        """
        entry_ops = target_sandbox_undoable.LexEntry
        form = f"{TEST_PREFIX}dom_delete"
        entry_ops.Create(form)
        assert entry_ops.Find(form) is not None

        with pytest.raises(_Boom):
            with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}dom delete"):
                entry_ops.Delete(entry_ops.Find(form))
                assert entry_ops.Find(form) is None
                raise _Boom()

        assert entry_ops.Find(form) is not None, (
            "a rolled-back Delete did not restore the entry -- data loss "
            "that no in-block assertion would catch."
        )


class TestPersistenceAcrossReopen:
    """
    Claim 7 -- issue #237, task B2t. THE test for this mode.

    Every other assertion in this file reads the LCM cache that is still
    in memory. A build that committed nothing to disk would pass all of
    them. Only a close-and-reopen cycle distinguishes "the write reached
    the cache" from "the write reached the project", and #237 is precisely
    the report that it did not.

    Uses `target_sandbox_path`, which hands over a tempdir `.fwdata` path
    and lets the test own the project lifecycle. The real Target project is
    never opened.
    """

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_setgloss_persists_across_close_and_reopen(self, target_sandbox_path):
        """The exact scenario from issue #237: undoable=True -> SetGloss ->
        CloseProject -> reopen -> assert persisted."""
        form = f"{TEST_PREFIX}persist_entry"
        gloss = f"{TEST_PREFIX}persisted gloss"

        project = FLExProject()
        project.OpenProject(target_sandbox_path, writeEnabled=True, undoable=True)
        try:
            with project.UndoableOperation(f"{TEST_PREFIX}persist"):
                entry = project.LexEntry.Create(form)
                project.Senses.Create(entry, gloss)
        finally:
            project.CloseProject()

        # A brand-new FLExProject on the same file: nothing survives here
        # except what actually reached disk.
        reopened = FLExProject()
        reopened.OpenProject(target_sandbox_path, writeEnabled=False)
        try:
            entry = reopened.LexEntry.Find(form)
            assert entry is not None, (
                f"entry {form!r} did not survive CloseProject() -- this is "
                f"issue #237: the write never reached disk."
            )
            glosses = [reopened.Senses.GetGloss(s) for s in reopened.LexEntry.GetSenses(entry)]
            assert gloss in glosses, (
                f"the entry persisted but its gloss did not: {glosses!r}"
            )
        finally:
            reopened.CloseProject()

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_a_rolled_back_write_does_not_persist(self, target_sandbox_path):
        """
        The other half of #237, and the half a broken build passes by
        accident: a rollback must be durable too. If rollback only cleared
        the cache while the mutation had already been flushed, the object
        would reappear on reopen.
        """
        kept = f"{TEST_PREFIX}durable_kept"
        dropped = f"{TEST_PREFIX}durable_dropped"

        project = FLExProject()
        project.OpenProject(target_sandbox_path, writeEnabled=True, undoable=True)
        try:
            with project.UndoableOperation(f"{TEST_PREFIX}kept"):
                project.LexEntry.Create(kept)

            with pytest.raises(_Boom):
                with project.UndoableOperation(f"{TEST_PREFIX}dropped"):
                    project.LexEntry.Create(dropped)
                    raise _Boom()
        finally:
            project.CloseProject()

        reopened = FLExProject()
        reopened.OpenProject(target_sandbox_path, writeEnabled=False)
        try:
            assert reopened.LexEntry.Find(kept) is not None, (
                "the committed entry did not persist"
            )
            assert reopened.LexEntry.Find(dropped) is None, (
                "a rolled-back entry reappeared after reopen -- the rollback "
                "cleared the cache but the mutation had already been flushed."
            )
        finally:
            reopened.CloseProject()

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_per_operation_writes_persist_without_an_explicit_block(
        self, target_sandbox_path
    ):
        """
        The `per-operation-uow` token's durability claim: a bare Operations
        call, with no `UndoableOperation()` around it, must also reach disk.
        This is the shape FlexToolsMCP actually generates.
        """
        form = f"{TEST_PREFIX}bare_persist"

        project = FLExProject()
        project.OpenProject(target_sandbox_path, writeEnabled=True, undoable=True)
        try:
            project.LexEntry.Create(form)
        finally:
            project.CloseProject()

        reopened = FLExProject()
        reopened.OpenProject(target_sandbox_path, writeEnabled=False)
        try:
            assert reopened.LexEntry.Find(form) is not None, (
                "a bare bracketed operation did not persist -- the "
                "per-operation-uow capability does not hold end to end."
            )
        finally:
            reopened.CloseProject()

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_undo_stack_does_not_survive_reopen(self, target_sandbox_path):
        """
        Live evidence for the CO1 scope caveat on issue #235: `Undo()` is
        IN-PROCESS ONLY. A reopened project starts with an empty stack, so
        work committed by a previous session is past undoing -- exactly the
        caveat that must be recorded when #235 is closed.
        """
        form = f"{TEST_PREFIX}stack_gone"

        project = FLExProject()
        project.OpenProject(target_sandbox_path, writeEnabled=True, undoable=True)
        try:
            with project.UndoableOperation(f"{TEST_PREFIX}committed work"):
                project.LexEntry.Create(form)
            assert project.project.ActionHandlerAccessor.CanUndo() is True
        finally:
            project.CloseProject()

        reopened = FLExProject()
        reopened.OpenProject(target_sandbox_path, writeEnabled=True, undoable=True)
        try:
            assert reopened.LexEntry.Find(form) is not None, "setup: write did not persist"
            assert reopened.project.ActionHandlerAccessor.CanUndo() is False, (
                "the undo stack survived a reopen -- #235's in-process-only "
                "caveat would be wrong."
            )
            assert reopened.Undo() is False
        finally:
            reopened.CloseProject()


class TestUndoableModeGuards:
    """The mode's refusals, live -- so DEF cannot flip the default into a
    state where the guards were only ever exercised offline."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_abort_session_returns_false_between_operations(
        self, target_sandbox_undoable
    ):
        """D8: no session envelope exists in this mode, so there is nothing
        to abort and AbortSession() must say so rather than raise."""
        assert _depth(target_sandbox_undoable) == 0
        assert target_sandbox_undoable.AbortSession() is False

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_abort_session_refuses_inside_a_block(self, target_sandbox_undoable):
        """D8: rolling back underneath the owning helper would make its
        Dispose() raise a second exception on the way out."""
        with target_sandbox_undoable.UndoableOperation(f"{TEST_PREFIX}guard"):
            with pytest.raises(FP_TransactionError):
                target_sandbox_undoable.AbortSession()
