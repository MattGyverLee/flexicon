#
#   transaction.py
#
#   Class: _FLExTransaction
#          Context manager for safe rollback transactions within a FLEx project.
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
    Context manager providing safe rollback transactions on a FLEx project.

    Marks a point in the LCM undo stack (if supported) and rolls back to
    that mark if an exception occurs inside the block.

    This is Phase 1 (rollback-only) behavior. The transaction does NOT
    appear in the FLEx Ctrl+Z undo menu - it is a programmatic safety net.

    Usage::

        with project.Transaction("Import entries") as txn:
            project.LexEntry.Create("run", "stem")
            project.LexEntry.Create("walk", "stem")
        # If any line raises, all changes in the block are rolled back.

    Nesting Behavior:
        Nested transactions are allowed but share outer-level semantics:
        a rollback in an inner transaction rolls back to the outer mark.
        This is documented behavior, not an error.

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
            When the LCM rollback API (mark_fn / rollback_fn) is unavailable on a
            write-enabled project, this logs a warning and proceeds WITHOUT rollback
            capability rather than raising. The Phase-1 Mark/RollbackToMark API is
            not yet discoverable in the shipped LCM build (see docs/RESEARCH_NEEDED.md),
            so failing fast here would make every write operation impossible. Until
            that API exists, degraded-but-functional is the only viable default; a
            strict opt-in mode is tracked separately (see issue #210).
        """
        if not self._project.writeEnabled:
            # Silently allow entering on read-only project;
            # any writes will fail anyway at BaseOperations validation.
            self._mark = None
            logger.debug(f"Transaction '{self._label}': read-only project, skipping mark")
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
