#
#   headless_ui.py
#
#   Class: HeadlessLcmUI
#          Non-blocking ILcmUI implementation for headless / server-hosted
#          use of the SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
A non-blocking ``ILcmUI`` for processes with no WinForms message pump.

LCM asks its ``ILcmUI`` for decisions at several points, most importantly on a
conflicting save. The default implementation used by FieldWorks -- and, until
now, unconditionally by flexicon -- is ``FwLcmUI``, a WinForms adapter whose
members open modal dialogs and marshal through ``Control.Invoke``. In a process
with no message pump that produces three distinct failures (issue #238):

1. ``ConflictingSave()`` opens ``ConflictingSaveDlg``, which has no close box
   (``ControlBox = false``), on the desktop with no owning application. Worse,
   its polarity is dangerous: anything other than ``OK`` returns ``true``, and
   ``UnitOfWorkService.GetUserInputOnConflictingSave`` responds to ``true`` by
   calling ``RevertToSavedState()`` -- discarding the caller's unsaved work.
2. ``DisplayMessage`` marshals through ``ISynchronizeInvoke``. It is reached
   from ``XMLBackendProvider.ReportProblem`` on the background commit thread,
   so a failed write hangs that thread, and ``CompleteAllCommits()`` then hangs
   the main thread on cache dispose.
3. ``FwLcmUI`` is constructed with ``helpTopicProvider = None``, and
   ``DisplayMessage`` dereferences ``m_helpTopicProvider.HelpFile`` for any
   non-empty help topic.

``SIL.LCModel.SilentLcmUI`` is *not* a safe substitute: its ``ConflictingSave()``
returns ``true`` unconditionally, i.e. silent total discard of unsaved changes
with no message and no exception. That is strictly worse than the dialog.

``HeadlessLcmUI`` never blocks, never marshals, and never silently discards.
Every decision point takes the non-destructive branch and logs; a conflicting
save raises ``FP_ConflictingSaveError`` so the condition surfaces to the caller
as an exception it can handle.

Usage::

    from flexicon import FLExProject
    from flexicon.code.headless_ui import HeadlessLcmUI

    project = FLExProject()
    project.OpenProject("MyProject", writeEnabled=True, ui=HeadlessLcmUI())

Passing no ``ui`` preserves the historical ``FwLcmUI`` behaviour.
"""

import logging

import System
from System import DateTime

from SIL.LCModel import ILcmUI, MessageType, FileSelection, YesNoCancel

# FP_ConflictingSaveError lives in exceptions.py alongside every other FP_*
# type so `except FP_RuntimeError` catches it too (see docs/EXCEPTION_HANDLING.md).
# Re-imported here (not re-defined) so
# `from flexicon.code.headless_ui import FP_ConflictingSaveError` keeps working.
from .exceptions import FP_ConflictingSaveError

logger = logging.getLogger(__name__)


class HeadlessLcmUI(ILcmUI):
    """
    ``ILcmUI`` that makes non-destructive decisions without blocking.

    Implements all ten methods and both properties of ``SIL.LCModel.ILcmUI``.
    """

    # Required by pythonnet to emit a real .NET type implementing the interface.
    __namespace__ = "Flexicon.Headless"

    def __init__(self, raise_on_conflicting_save=True):
        """
        Args:
            raise_on_conflicting_save (bool): When True (default),
                ``ConflictingSave()`` raises ``FP_ConflictingSaveError``. When
                False it logs and returns False, which tells LCM to keep this
                session's changes and skip ``RevertToSavedState()``.
        """
        self._raise_on_conflicting_save = raise_on_conflicting_save
        self._last_activity = DateTime.Now

    # -- Properties ---------------------------------------------------

    @property
    def SynchronizeInvoke(self):
        """
        None - nothing may marshal to a UI thread that does not exist.

        Returning None is what keeps ``DisplayMessage`` off the deadlock path
        described in the module docstring.
        """
        return None

    def get_SynchronizeInvoke(self):
        return None

    @property
    def LastActivityTime(self):
        return self._last_activity

    def get_LastActivityTime(self):
        return self._last_activity

    def TouchActivity(self):
        """
        Record caller activity. ``UnitOfWorkService.SaveOnIdle`` consults
        ``LastActivityTime`` to decide whether to defer an auto-save, so a
        long-running caller should touch this periodically.
        """
        self._last_activity = DateTime.Now

    # -- The decision that can lose data ------------------------------

    def ConflictingSave(self):
        """
        Report whether to revert this session's changes to the saved state.

        Returns False -- never revert -- and by default raises so the caller
        learns that a reconcile failed. LCM calls this only after
        ``ChangeReconciler.OkToReconcileChanges()`` has already determined the
        foreign changes cannot be merged, so by this point some manual
        resolution is required either way.
        """
        logger.error(
            "ConflictingSave: another client saved changes that cannot be "
            "reconciled with this session's unsaved changes. Refusing to "
            "revert to saved state."
        )
        if self._raise_on_conflicting_save:
            raise FP_ConflictingSaveError(
                "Another client saved conflicting changes to this project. "
                "This session's unsaved changes were NOT discarded. Close "
                "without saving, or reopen and re-apply the operation."
            )
        return False

    # -- Non-blocking reports -----------------------------------------

    def DisplayMessage(self, type, message, caption, helpTopic):
        level = {
            MessageType.Error: logging.ERROR,
            MessageType.Warning: logging.WARNING,
        }.get(type, logging.INFO)
        logger.log(level, f"LCM message [{caption}]: {message}")

    def ReportException(self, error, isLethal):
        """
        Returns False: do not attempt to continue after a lethal error.
        """
        logger.error(f"LCM exception (isLethal={isLethal}): {error}")
        return False

    def ReportDuplicateGuids(self, errorText):
        logger.error(f"LCM duplicate GUIDs: {errorText}")

    def DisplayCircularRefBreakerReport(self, msg, caption):
        logger.warning(f"LCM circular reference breaker [{caption}]: {msg}")

    # -- Decisions with a non-destructive branch -----------------------

    def Retry(self, msg, caption):
        """
        Returns False. Retrying unattended risks an unbounded loop on a
        persistent condition such as a locked file.
        """
        logger.warning(f"LCM retry request declined [{caption}]: {msg}")
        return False

    def OfferToRestore(self, projectPath, backupPath):
        """
        Returns False. Restoring from a backup unattended would overwrite the
        project; that decision belongs to a human.
        """
        logger.warning(
            f"LCM offered to restore '{projectPath}' from '{backupPath}'. "
            "Declined - restore is not performed unattended."
        )
        return False

    def RestoreLinkedFilesInProjectFolder(self):
        """
        Returns False -- leave linked files at their original location.

        True would move/restore linked files into the project folder, an
        unattended file-system side effect. False is the non-destructive
        branch: linked files are left where they already are.
        """
        logger.info(
            "LCM RestoreLinkedFilesInProjectFolder: leaving linked files at "
            "their original location (non-destructive branch)."
        )
        return False

    def ChooseFilesToUse(self):
        logger.info("LCM ChooseFilesToUse: defaulting to OkKeepNewer.")
        return FileSelection.OkKeepNewer

    def CannotRestoreLinkedFilesToOriginalLocation(self):
        """
        Returns OkNo - skip restoring linked files. The least destructive of
        the three branches.
        """
        logger.warning(
            "LCM cannot restore linked files to their original location. "
            "Skipping linked-file restore."
        )
        return YesNoCancel.OkNo
