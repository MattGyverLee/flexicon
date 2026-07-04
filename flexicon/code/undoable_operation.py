#
#   undoable_operation.py
#
#   Class: _FLExUndoableOperation
#          Context manager for operations that integrate with FLEx Ctrl+Z.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)


class _FLExUndoableOperation:
    """
    Context manager for undoable operations that appear in FLEx's Ctrl+Z menu.

    Unlike Phase 1 Transaction (rollback-only), Phase 2 UndoableOperation:
    - Changes made inside the block appear as ONE named operation in FLEx Ctrl+Z
    - Ctrl+Z in FLEx will undo the entire operation
    - Ctrl+Y in FLEx will redo the entire operation
    - The project MUST be opened with undoable=True

    Usage::

        project.OpenProject("MyProject", writeEnabled=True, undoable=True)

        with project.UndoableOperation("Add entry 'run'"):
            entry = project.LexEntry.Create("run", "stem")
            project.Senses.Create(entry, "to move", "en")

        # Now "Add entry 'run'" appears in FLEx Edit > Undo menu
        # User can Ctrl+Z to undo both the entry AND sense creation together

    Note:
        This class is internal. Obtain instances via FLExProject.UndoableOperation().
        Requires the project to be opened with undoable=True.
    """

    def __init__(self, project, label: str, begin_undo_fn, end_undo_fn) -> None:
        """
        Initialize undoable operation.

        Args:
            project:       The FLExProject instance
            label:         Operation name shown in FLEx undo menu
            begin_undo_fn: Callable(label) to start undoable task
            end_undo_fn:   Callable() to end undoable task
        """
        self._project = project
        self._label = label
        self._begin_undo_fn = begin_undo_fn
        self._end_undo_fn = end_undo_fn
        self._started = False

    def __enter__(self) -> "_FLExUndoableOperation":
        """
        Start the undoable operation.

        Calls BeginUndoTask(label) on the LCM project.
        If the project is not in undoable mode, raises FP_TransactionError.
        """
        if not self._project.writeEnabled:
            # Lazy import to prevent circular dependency: FLExProject imports undoable_operation at module level
            from .FLExProject import FP_ReadOnlyError

            raise FP_ReadOnlyError()

        if not self._project._undoable:
            # Lazy import to prevent circular dependency: FLExProject imports undoable_operation at module level
            from .FLExProject import FP_TransactionError

            raise FP_TransactionError(
                "Project must be opened with undoable=True to use UndoableOperation. "
                f"Current project was opened with undoable=False."
            )

        try:
            self._begin_undo_fn(self._label)
            self._started = True
            logger.debug(f"UndoableOperation '{self._label}': started")
        except Exception as e:
            logger.error(f"UndoableOperation '{self._label}': BeginUndoTask failed: {e}")
            raise

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        End the undoable operation.

        Calls EndUndoTask() on the LCM project to finalize the operation.
        If an exception occurred in the block, it is re-raised after EndUndoTask.
        """
        if not self._started:
            return False

        try:
            self._end_undo_fn()
            if exc_type is None:
                logger.debug(f"UndoableOperation '{self._label}': committed")
            else:
                logger.warning(
                    f"UndoableOperation '{self._label}': exception {exc_type.__name__}, "
                    f"but changes are still in undo stack"
                )
        except Exception as e:
            logger.error(f"UndoableOperation '{self._label}': EndUndoTask failed: {e}")

        return False  # Re-raise original exception if any


class _UndoRedoNotSupportedError(Exception):
    """
    Internal error when Undo/Redo APIs are not available.
    """

    pass
