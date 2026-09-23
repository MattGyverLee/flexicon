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
conflicting save. The default implementation used by FieldWorks, and formerly
used unconditionally by flexicon (until issue #285 flipped the default to
``HeadlessLcmUI``), is ``FwLcmUI``, a WinForms adapter whose members open
modal dialogs and marshal through ``Control.Invoke``. In a process with no
message pump that produces three distinct failures (issue #238):

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
    from flexicon import HeadlessLcmUI  # also importable from
                                         # flexicon.code.headless_ui

    project = FLExProject()
    project.OpenProject("MyProject", writeEnabled=True)  # ui=None -> HeadlessLcmUI()

Since issue #285, passing no ``ui`` already gets you a bare ``HeadlessLcmUI()``
-- that is now the library-wide default. Pass ``ui=FwLcmUI(None,
ThreadHelper())`` explicitly to opt back into the historical, WinForms-dialog
behaviour.
"""

import logging

import System
from System import DateTime

from SIL.LCModel import ILcmUI, MessageType, FileSelection, YesNoCancel
from SIL.LCModel.Utils import IThreadedProgress

# FP_ConflictingSaveError lives in exceptions.py alongside every other FP_*
# type so `except FP_RuntimeError` catches it too (see docs/EXCEPTION_HANDLING.md).
# Re-imported here (not re-defined) so
# `from flexicon.code.headless_ui import FP_ConflictingSaveError` keeps working.
from .exceptions import FP_ConflictingSaveError, FP_ParameterError

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

        CONTINGENCY (cycle-1 domain audit, issue #285): ``None`` here is
        dereferenced unguarded at exactly two liblcm sites --
        ``UnitOfWorkService.SendPropChangedNotifications``
        (``UnitOfWorkService.cs:537``, reached via ``UnitOfWork.cs:307/422``
        and ``UndoStack.cs:343``) and
        ``UndoStack.DoTasksForEndOfPropChanged`` (``UndoStack.cs:383``). Both
        are no-ops for flexicon TODAY only because (1) nothing in the current
        Operations surface calls ``AddNotification`` to register an
        ``IVwNotifyChange`` subscriber, and (2) nothing touches ``Scripture``,
        liblcm's sole ``IPropertyChangeNotifier`` implementer. If a future
        feature adds a change-watcher or touches Scripture, re-check both
        call sites before assuming ``None`` is still safe here.
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


class HeadlessThreadedProgress(IThreadedProgress):
    """
    ``IThreadedProgress`` that runs work on the calling thread with no UI.

    FieldWorks' ``ProgressDialogWithTask`` allocates a WinForms ``Form`` and
    forces a Win32 handle on construction (issue #289). ``OpenProject`` now
    defaults to this class instead, mirroring FieldWorks' own
    ``NullThreadedProgress`` console tools.
    """

    __namespace__ = "Flexicon.Headless"

    def __init__(self):
        self._title = ""
        self._message = ""
        self._minimum = 0
        self._maximum = 100
        self._position = 0
        self._step_size = 1
        self._is_indeterminate = False
        self._allow_cancel = False
        self._cancel_button_text = ""
        self._cancel_label_text = ""
        self._restartable = False
        self._is_canceling = False
        self._canceled = False
        self._is_disposed = False

    # -- IDisposable (via concrete ProgressDialogWithTask; safe no-op here) --

    def Dispose(self):
        self._is_disposed = True

    def get_IsDisposed(self):
        return self._is_disposed

    @property
    def IsDisposed(self):
        return self._is_disposed

    # -- IProgress / IThreadedProgress surface ---------------------------

    @property
    def SynchronizeInvoke(self):
        return None

    def get_SynchronizeInvoke(self):
        return None

    @property
    def Title(self):
        return self._title

    @Title.setter
    def Title(self, value):
        self._title = value or ""

    def get_Title(self):
        return self._title

    def set_Title(self, value):
        self.Title = value

    @property
    def Message(self):
        return self._message

    @Message.setter
    def Message(self, value):
        self._message = value or ""

    def get_Message(self):
        return self._message

    def set_Message(self, value):
        self.Message = value

    @property
    def Minimum(self):
        return self._minimum

    @Minimum.setter
    def Minimum(self, value):
        self._minimum = int(value)

    def get_Minimum(self):
        return self._minimum

    def set_Minimum(self, value):
        self.Minimum = value

    @property
    def Maximum(self):
        return self._maximum

    @Maximum.setter
    def Maximum(self, value):
        self._maximum = int(value)

    def get_Maximum(self):
        return self._maximum

    def set_Maximum(self, value):
        self.Maximum = value

    @property
    def Position(self):
        return self._position

    @Position.setter
    def Position(self, value):
        self._position = int(value)

    def get_Position(self):
        return self._position

    def set_Position(self, value):
        self.Position = value

    @property
    def StepSize(self):
        return self._step_size

    @StepSize.setter
    def StepSize(self, value):
        self._step_size = int(value)

    def get_StepSize(self):
        return self._step_size

    def set_StepSize(self, value):
        self.StepSize = value

    @property
    def IsIndeterminate(self):
        return self._is_indeterminate

    @IsIndeterminate.setter
    def IsIndeterminate(self, value):
        self._is_indeterminate = bool(value)

    def get_IsIndeterminate(self):
        return self._is_indeterminate

    def set_IsIndeterminate(self, value):
        self.IsIndeterminate = value

    @property
    def AllowCancel(self):
        return self._allow_cancel

    @AllowCancel.setter
    def AllowCancel(self, value):
        self._allow_cancel = bool(value)

    def get_AllowCancel(self):
        return self._allow_cancel

    def set_AllowCancel(self, value):
        self.AllowCancel = value

    @property
    def CancelButtonText(self):
        return self._cancel_button_text

    @CancelButtonText.setter
    def CancelButtonText(self, value):
        self._cancel_button_text = value or ""

    def get_CancelButtonText(self):
        return self._cancel_button_text

    def set_CancelButtonText(self, value):
        self.CancelButtonText = value

    @property
    def CancelLabelText(self):
        return self._cancel_label_text

    @CancelLabelText.setter
    def CancelLabelText(self, value):
        self._cancel_label_text = value or ""

    def get_CancelLabelText(self):
        return self._cancel_label_text

    def set_CancelLabelText(self, value):
        self.CancelLabelText = value

    @property
    def Restartable(self):
        return self._restartable

    @Restartable.setter
    def Restartable(self, value):
        self._restartable = bool(value)

    def get_Restartable(self):
        return self._restartable

    def set_Restartable(self, value):
        self.Restartable = value

    @property
    def Canceled(self):
        return self._canceled

    def get_Canceled(self):
        return self._canceled

    @property
    def IsCanceling(self):
        return self._is_canceling

    @IsCanceling.setter
    def IsCanceling(self, value):
        self._is_canceling = bool(value)

    def get_IsCanceling(self):
        return self._is_canceling

    def set_IsCanceling(self, value):
        self.IsCanceling = value

    def Step(self, amount):
        self._position += int(amount)

    def RunTask(self, *args):
        """
        Run ``task(self, args)`` synchronously on the calling thread.

        Accepts both ``RunTask(task, args)`` and
        ``RunTask(useSeparateThread, task, args)`` overloads.
        """
        if len(args) == 2:
            task, task_args = args[0], args[1]
        elif len(args) == 3:
            use_separate_thread, task, task_args = args
            if use_separate_thread:
                logger.debug(
                    "HeadlessThreadedProgress.RunTask: ignoring "
                    "useSeparateThread=True; running on caller thread."
                )
        else:
            raise FP_ParameterError(
                f"RunTask expected 2 or 3 arguments, got {len(args)}"
            )

        if task is not None:
            task(self, task_args)
        return not self._canceled
