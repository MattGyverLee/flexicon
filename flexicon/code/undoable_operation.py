#
#   undoable_operation.py
#
#   Class: _FLExUndoableOperation
#          Context manager for operations that integrate with FLEx Ctrl+Z.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025-2026
#

import logging

from SIL.LCModel.Infrastructure import UndoableUnitOfWorkHelper

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

    Implementation (issue #233 -- ``BeginUndoTask`` arity bug):
        This used to discover a ``BeginUndoTask``/``EndUndoTask`` callable
        pair (``FLExProject._GetUndoRedoAPI()``) and call
        ``begin_undo_fn(label)`` with a single argument, against liblcm's
        actual two-argument ``IActionHandler.BeginUndoTask(String undoText,
        String redoText)``. That discovery layer is gone; this class now
        constructs liblcm's own ``UndoableUnitOfWorkHelper`` directly
        (``SIL.LCModel.Infrastructure``), whose constructor takes both
        strings, so the one-argument call can no longer occur. It also
        joins an already-open UnitOfWork (``ActionHandlerAccessor.CurrentDepth
        > 0``) instead of opening a second one -- the same idiom
        ``_NestingAwareTransaction`` uses in ``transaction.py`` and liblcm's
        own ``UndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW``
        (``UndoableUnitOfWorkHelper.cs:91-98``). See
        `specs/write-path-transactions/spec.md` B1.

    Note:
        This class is internal. Obtain instances via FLExProject.UndoableOperation().
        Requires the project to be opened with undoable=True.
    """

    def __init__(self, project, label: str) -> None:
        """
        Initialize undoable operation.

        Args:
            project: The FLExProject instance
            label:   Operation name shown in FLEx undo menu, used as both
                     the undo text and the redo text passed to liblcm's
                     ``UndoableUnitOfWorkHelper`` constructor.
        """
        self._project = project
        self._label = label
        self._helper = None  # Set only when this block opens a new
        # UnitOfWork (outermost); left None when joining an already-open one.

    def __enter__(self) -> "_FLExUndoableOperation":
        """
        Start the undoable operation.

        Joins an already-open UnitOfWork if one exists
        (``ActionHandlerAccessor.CurrentDepth > 0``), otherwise constructs a
        new ``UndoableUnitOfWorkHelper`` (which begins the undo task).
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

        action_handler = self._project.project.ActionHandlerAccessor
        depth = getattr(action_handler, "CurrentDepth", 0)
        if not isinstance(depth, int):
            depth = 0

        if depth > 0:
            # JOIN: an enclosing UndoableOperation() or _TransactionCM block
            # already has a task open; do not open a second one (liblcm
            # would roll the open one back and throw -- UndoStack.cs:209-216).
            logger.debug(
                f"UndoableOperation '{self._label}': joining open UnitOfWork "
                f"(CurrentDepth={depth})"
            )
            return self

        # OPEN: construct the helper directly. Its constructor takes both an
        # undo and a redo string, so this cannot repeat the one-argument
        # BeginUndoTask call that was issue #233. (Module-level import above
        # -- not lazy -- so tests can patch
        # `flexicon.code.undoable_operation.UndoableUnitOfWorkHelper`
        # directly with a double, without touching a live LcmCache.)
        self._helper = UndoableUnitOfWorkHelper(action_handler, self._label, self._label)
        logger.debug(f"UndoableOperation '{self._label}': started (opened new UnitOfWork)")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        End the undoable operation.

        If this block opened the UnitOfWork (outermost), clears ``RollBack``
        on a clean exit and disposes the helper -- disposal rolls back when
        ``RollBack`` is still True (the constructor default) or calls
        ``EndUndoTask()`` when it has been cleared. If this block joined an
        already-open UnitOfWork, there is nothing to close here; the
        enclosing block owns disposal.
        """
        if self._helper is None:
            return False  # Joined block, or never started: nothing to do.

        try:
            # RollBack is write-only (no getter) -- only ever set it.
            self._helper.RollBack = exc_type is not None
            self._helper.Dispose()
            if exc_type is None:
                logger.debug(f"UndoableOperation '{self._label}': committed")
            else:
                logger.warning(
                    f"UndoableOperation '{self._label}': exception {exc_type.__name__}, "
                    f"UnitOfWork rolled back"
                )
        except Exception as e:
            logger.error(f"UndoableOperation '{self._label}': Dispose() failed: {e}")
        finally:
            self._helper = None

        return False  # Re-raise original exception if any


class _UndoRedoNotSupportedError(Exception):
    """
    Internal error when Undo/Redo APIs are not available.
    """

    pass
