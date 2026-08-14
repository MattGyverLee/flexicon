#
#   transaction.py
#
#   Classes: _NestingAwareTransaction
#                Phase-aware, nesting-safe context manager returned by
#                BaseOperations._TransactionCM(); auto-selects Phase 1
#                (Transaction, no rollback) or Phase 2 (a real, rollback-
#                capable liblcm UnitOfWork, backed by
#                UndoableUnitOfWorkHelper).
#            _FLExTransaction
#                Context manager for safe rollback transactions within a
#                FLEx project (Phase 1).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025-2026
#

import logging

from SIL.LCModel.Infrastructure import UndoableUnitOfWorkHelper

logger = logging.getLogger(__name__)


class _NestingAwareTransaction:
    """
    Phase-aware, nesting-safe wrapper returned by ``BaseOperations._TransactionCM``.

    Chooses behavior at ``__enter__`` time based on the project mode:

        * Phase 1 (``_undoable`` False): always delegates to
          ``project.Transaction()``, regardless of nesting depth. ``Transaction()``
          never opens an LCM undo task itself -- the single non-undoable
          envelope for the whole session is opened once, at ``OpenProject()``
          (``MainCacheAccessor.BeginNonUndoableTask()``), and stays open until
          ``CloseProject()``. So nested ``with`` blocks in this mode compose
          without any LCM-level nesting concern; there is nothing to join or
          open per block.
        * Phase 2 (``_undoable`` True): joins or opens a real liblcm
          ``UndoableUnitOfWorkHelper`` UnitOfWork, following the *exact* idiom
          liblcm itself uses in
          ``UndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW``
          (``UndoableUnitOfWorkHelper.cs:91-98``)::

              if (actionHandler.CurrentDepth > 0) task();
              else Do(undoText, redoText, actionHandler, task);

          Nesting depth is asked of LCM itself
          (``cache.ActionHandlerAccessor.CurrentDepth``) at every
          ``__enter__`` call -- it is never tracked locally in Python. This
          is deliberate: a hand-maintained depth counter, formerly stored on
          the project instance, is exactly what issue #234 was -- it
          permanently leaked when an inner ``__enter__`` raised, because
          nothing on that path ever decremented it. There is no longer any
          local counter to leak; ``CurrentDepth`` also correctly reflects a
          task opened by ANY caller (e.g.
          ``FLExProject.UndoableOperation()`` called directly, not just
          through this class), which the old Python-side counter could not
          see. See ``docs/EXCEPTION_HANDLING.md`` and
          ``specs/write-path-transactions/spec.md`` section 5, B1.

    A second ``BeginUndoTask`` while one is already open does not merely
    raise in liblcm -- ``UndoStack.cs:209-216`` rolls back the *already-open*
    UnitOfWork first (discarding its changes), resets the FSM, and only then
    throws. Joining (never opening a second task while one is active) is
    therefore not an optional nicety; it is what keeps this class from
    silently destroying whatever the outer block already did.
    """

    def __init__(self, project, label: str) -> None:
        self._project = project
        self._label = label
        self._inner = None  # Phase 1: the _FLExTransaction context manager.
        self._helper = None  # Phase 2, outermost block only: the raw
        # UndoableUnitOfWorkHelper instance this block opened. None both
        # for Phase 1 and for a nested (joined) Phase 2 block -- in the
        # latter case the enclosing helper (wherever it lives) owns
        # Dispose(), not this instance.

    def __enter__(self) -> "_NestingAwareTransaction":
        project = self._project
        undoable = getattr(project, "_undoable", False)

        if not undoable:
            # Phase 1: always delegate, regardless of nesting depth -- see
            # class docstring. No LCM undo task is opened here at all.
            self._inner = project.Transaction(self._label)
            self._inner.__enter__()
            return self

        # Phase 2: ask LCM's own state; never track it ourselves (kills
        # #234 by construction -- see class docstring).
        depth = self._current_depth(project)

        if depth > 0:
            # JOIN: liblcm's own idiom -- "if (actionHandler.CurrentDepth > 0)
            # task();" (UndoableUnitOfWorkHelper.cs:94). Simply run the body;
            # the enclosing UnitOfWork (opened by this class, by
            # UndoableOperation(), or by any other caller) already owns
            # these mutations. Nothing to construct or close.
            logger.debug(
                f"_TransactionCM '{self._label}': joining open UnitOfWork "
                f"(CurrentDepth={depth})"
            )
            return self

        # OPEN: "else Do(undoText, redoText, actionHandler, task);"
        # (UndoableUnitOfWorkHelper.cs:97). A Python context manager cannot
        # hand liblcm a callable body the way Do() wants one, so this
        # replicates Do()'s constructor-then-Dispose shape directly:
        # construct the helper (its ctor begins the undo task --
        # UnitOfWorkHelper.cs:31, via BeginUndoTask(label, label)), run the
        # body, then clear RollBack on a clean exit before Dispose() (see
        # __exit__). The ctor takes both an undo and a redo string, so this
        # can never repeat the one-argument BeginUndoTask call that was
        # issue #233. (Module-level import above -- not lazy -- so tests can
        # patch `flexicon.code.transaction.UndoableUnitOfWorkHelper`
        # directly with a double, without touching a live LcmCache.)
        action_handler = project.project.ActionHandlerAccessor
        self._helper = UndoableUnitOfWorkHelper(action_handler, self._label, self._label)
        logger.debug(f"_TransactionCM '{self._label}': opened new UnitOfWork")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        try:
            if self._inner is not None:
                # Phase 1.
                return self._inner.__exit__(exc_type, exc_val, exc_tb)

            if self._helper is not None:
                # Phase 2, outermost block. RollBack defaults to True from
                # the helper's constructor (UnitOfWorkHelper.cs:31);
                # Dispose() rolls back when it is True, or calls
                # EndUndoTask() when it is False (UnitOfWorkHelper.cs:115-118).
                # RollBack is write-only (no getter) -- only ever set it,
                # never read it back.
                self._helper.RollBack = exc_type is not None
                self._helper.Dispose()
                if exc_type is None:
                    logger.debug(f"_TransactionCM '{self._label}': committed")
                else:
                    logger.warning(
                        f"_TransactionCM '{self._label}': exception "
                        f"{exc_type.__name__}, UnitOfWork rolled back"
                    )

            # Either Phase 2 nested (joined an already-open UnitOfWork, so
            # self._helper is None) or nothing was opened: do not suppress
            # the exception in any case.
            return False
        finally:
            self._inner = None
            self._helper = None

    @staticmethod
    def _current_depth(project) -> int:
        """
        Read ``CurrentDepth`` from LCM's own action handler.

        Only ever called in Phase 2 (``_undoable`` True), where
        ``project.project`` (the ``LcmCache``) and its
        ``ActionHandlerAccessor`` are expected to be real. Returns 0 (treat
        as outermost) if the value is not a real ``int`` -- a defensive
        fallback for test doubles that stand in an incomplete
        ``IActionHandler``, so a malformed double degrades to "open a new
        UnitOfWork" rather than raising.
        """
        try:
            depth = project.project.ActionHandlerAccessor.CurrentDepth
        except Exception:
            depth = 0
        return depth if isinstance(depth, int) else 0


class _FLExTransaction:
    """
    Context manager for FLExProject.Transaction() -- labelling/nesting only.

    If constructed with a real ``mark_fn``/``rollback_fn`` pair, marks a
    point in the LCM undo stack and rolls back to it on exception. In the
    current build, ``FLExProject.Transaction()`` always constructs this
    class with ``(None, None)``: no such LCM rollback-to-mark API exists
    (issue #236; see `specs/write-path-transactions/spec.md` section 2 for
    the specific API confirmed absent by reflection). So in
    practice today this class provides labelling and safe nesting only --
    it does NOT roll anything back. See ``FLExProject.Transaction()``'s
    docstring for the full mode-dependent explanation, and
    ``docs/EXCEPTION_HANDLING.md`` for the atomicity-unit consequence.

    This does NOT appear in the FLEx Ctrl+Z undo menu regardless of mode -
    it is (or, once real, would be) a programmatic safety net only.

    Usage::

        with project.Transaction("Import entries") as txn:
            project.LexEntry.Create("run", "stem")
            project.LexEntry.Create("walk", "stem")
        # No exception here is rolled back in the current build (see above).

    Note:
        This class is internal. Obtain instances via FLExProject.Transaction().
    """

    def __init__(self, project, label: str, mark_fn, rollback_fn) -> None:
        """
        Initialize transaction.

        Args:
            project:     The FLExProject instance
            label:       Human-readable description (for logging)
            mark_fn:     Callable() -> mark_token  (LCM mark API)
            rollback_fn: Callable(mark_token)      (LCM rollback API)
        """
        self._project = project
        self._label = label
        self._mark_fn = mark_fn
        self._rollback_fn = rollback_fn
        self._mark = None
        self._committed = False

    def __enter__(self) -> "_FLExTransaction":
        """
        Enter the transaction context.

        If the project is write-enabled, marks a rollback point.
        If the project is read-only, skips marking (any write will fail at validation).

        Note:
            When no LCM rollback API (mark_fn / rollback_fn) has been supplied
            to this instance, entering proceeds WITHOUT rollback capability
            rather than raising. In the current build ``FLExProject.Transaction()``
            always passes ``(None, None)`` here: no rollback-to-mark API
            exists anywhere in liblcm or FieldWorks (issue #236, confirmed by
            reflection over ``SIL.LCModel.dll`` -- see
            ``specs/write-path-transactions/spec.md`` D1 for the specific API
            name checked). This is not a
            build-specific gap that might resolve later; there is no such API
            to discover. Failing fast here would make every write operation
            under ``undoable=False`` impossible, so degraded-but-functional
            (no rollback, body still runs, exceptions still propagate) is the
            permanent behavior in this mode. A per-session warning to this
            effect is logged once per ``FLExProject.OpenProject()`` call (not
            once per process or per instance -- a second ``OpenProject()``
            call in the same session re-logs it), and not per transaction
            (issue #221) -- see ``docs/EXCEPTION_HANDLING.md``.
        """
        if not self._project.writeEnabled:
            # Silently allow entering on read-only project;
            # any writes will fail anyway at BaseOperations validation.
            self._mark = None
            logger.debug(f"Transaction '{self._label}': read-only project, skipping mark")
            return self

        if self._mark_fn is None:
            # No rollback API exists to use (see docstring above). Expected
            # and permanent in the current build, not an error -- the
            # one-shot OpenProject() warning already told the caller this
            # mode has no rollback, so no further per-call logging here.
            self._mark = None
            return self

        try:
            self._mark = self._mark_fn()
            logger.debug(f"Transaction '{self._label}': marked at {self._mark}")
        except Exception as e:
            logger.warning(f"Transaction '{self._label}': could not set mark: {e}")
            self._mark = None

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the transaction context.

        On success (no exception): commits changes (nothing explicit needed).
        On failure (exception raised): attempts rollback to the mark.
        Re-raises the original exception in all cases.
        """
        if exc_type is None:
            # Success path: commit (nothing explicit needed in non-undoable mode)
            self._committed = True
            logger.debug(f"Transaction '{self._label}': committed")
            return False  # Do not suppress exceptions (none occurred)

        # Failure path: rollback
        logger.warning(
            f"Transaction '{self._label}': exception {exc_type.__name__}, " f"rolling back to mark {self._mark}"
        )

        if self._mark is not None and self._rollback_fn is not None:
            try:
                self._rollback_fn(self._mark)
                logger.info(f"Transaction '{self._label}': rollback successful")
            except Exception as rollback_err:
                logger.error(
                    f"Transaction '{self._label}': ROLLBACK FAILED: {rollback_err}. "
                    f"Project may be in inconsistent state. Consider closing without saving."
                )
        else:
            logger.warning(
                f"Transaction '{self._label}': no mark available, "
                f"rollback not performed. Changes from this block are NOT reversed."
            )

        return False  # Re-raise the original exception
