#
#   transaction.py
#
#   Classes: _NestingAwareTransaction
#                Phase-aware, nesting-safe context manager returned by
#                BaseOperations._TransactionCM(); auto-selects Phase 1
#                (Transaction, no rollback) or Phase 2 (UndoableOperation).
#            _FLExTransaction
#                Context manager for safe rollback transactions within a
#                FLEx project (Phase 1).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)


class _NestingAwareTransaction:
    """
    Phase-aware, nesting-safe wrapper returned by ``BaseOperations._TransactionCM``.

    Chooses the underlying context manager at ``__enter__`` time based on the
    project mode and the current nesting depth, then maintains the depth count:

        * Phase 1 (``_undoable`` False): always delegates to
          ``project.Transaction()``. Phase 1 nests safely - each block marks an
          independent rollback point on the LCM undo stack, so nested blocks are
          fine at any depth.
        * Phase 2 (``_undoable`` True), OUTERMOST block (depth 0): delegates to
          ``project.UndoableOperation()``, opening a single named FLEx undo task.
        * Phase 2, NESTED block (depth > 0): becomes a NO-OP. ``BeginUndoTask`` /
          ``EndUndoTask`` cannot nest - opening a second undo task inside an
          active one corrupts the undo stack. The outermost ``UndoableOperation``
          already groups every inner mutation into its single named task, which
          is exactly the Phase 2 contract (recover via FLEx Ctrl+Z), so the inner
          block must touch no undo API at all.

    Depth is tracked on the project (``project._transaction_depth``) rather than
    on the Operations instance, because nesting routinely crosses Operations
    boundaries (e.g. ``LexEntry.Create`` calling ``Senses.Create``).
    """

    def __init__(self, project, label: str) -> None:
        self._project = project
        self._label = label
        self._inner = None  # underlying CM, or None for a nested Phase 2 no-op

    def __enter__(self) -> "_NestingAwareTransaction":
        project = self._project
        depth = getattr(project, "_transaction_depth", 0)
        if not isinstance(depth, int):
            # Defensive: a project that bypassed __init__ (or a test double)
            # may not carry a real counter; treat it as the outermost block.
            depth = 0
        undoable = getattr(project, "_undoable", False)

        if undoable and depth > 0:
            # Nested Phase 2: no-op. Outer UndoableOperation owns these mutations.
            self._inner = None
            logger.debug(
                f"_TransactionCM '{self._label}': nested in undoable mode "
                f"(depth {depth}), reusing outer undo task (no-op)"
            )
        elif undoable:
            self._inner = project.UndoableOperation(self._label)
        else:
            self._inner = project.Transaction(self._label)

        project._transaction_depth = depth + 1
        if self._inner is not None:
            self._inner.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        project = self._project
        try:
            if self._inner is not None:
                return self._inner.__exit__(exc_type, exc_val, exc_tb)
            return False  # no-op: do not suppress exceptions
        finally:
            project._transaction_depth = getattr(project, "_transaction_depth", 1) - 1


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
