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

import clr
import System
from System import DateTime

from SIL.LCModel import ILcmUI, MessageType, FileSelection, YesNoCancel
from SIL.LCModel.Utils import IThreadedProgress, SingleThreadedSynchronizeInvoke

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
        # Inline invoker: InvokeRequired is False, so LCM never marshals to a
        # UI thread (#238) but SendPropChangedNotifications does not NRE once
        # a change listener is registered (e.g. HermitCrab HCParser, #441).
        self._synchronize_invoke = SingleThreadedSynchronizeInvoke()

    # -- Properties ---------------------------------------------------

    @property
    def SynchronizeInvoke(self):
        """
        ``SingleThreadedSynchronizeInvoke`` -- runs LCM notification callbacks
        inline on the calling thread.

        ``FwLcmUI`` marshals through a real UI pump and can deadlock headless
        processes (#238). Returning ``None`` avoided that but breaks every
        write once an ``IVwNotifyChange`` subscriber exists (HermitCrab parser,
        issue #441): liblcm dereferences ``SynchronizeInvoke`` unguarded in
        ``UnitOfWorkService.SendPropChangedNotifications`` and
        ``UndoStack.DoTasksForEndOfPropChanged``.

        ``SingleThreadedSynchronizeInvoke.InvokeRequired`` is ``False``, so
        ``SynchronizeInvokeExtensions.Invoke`` executes the action immediately
        without cross-thread dispatch. ``HeadlessLcmUI.DisplayMessage`` still
        logs directly and does not use this property.
        """
        return self._synchronize_invoke

    def get_SynchronizeInvoke(self):
        return self._synchronize_invoke

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


# ---------------------------------------------------------------------------
# HeadlessThreadedProgress
#
# This cannot be a Python subclass of IThreadedProgress. IThreadedProgress
# inherits IProgress, which declares a .NET event (Canceling), and pythonnet
# 3.x cannot emit event members on a derived type: the class statement
# raises "Method 'add_Canceling' ... does not have an implementation" and
# takes `import flexicon` down with it (regression of issue #289).
# FieldWorks ships no public no-UI implementation (its NullThreadedProgress
# lives in test assemblies), so the type is compiled once per process from
# the C# below -- the same shape as FieldWorks' NullThreadedProgress.
# ---------------------------------------------------------------------------

_HEADLESS_PROGRESS_CS = r"""
using System;
using System.ComponentModel;
using SIL.LCModel.Utils;

namespace Flexicon.Headless
{
    /// IThreadedProgress that runs work on the calling thread with no UI.
    public class HeadlessThreadedProgress : IThreadedProgress, IDisposable
    {
        private string m_title = "";
        private string m_message = "";

        public event CancelEventHandler Canceling;

        public HeadlessThreadedProgress()
        {
            Maximum = 100;
            StepSize = 1;
        }

        public string Title
        {
            get { return m_title; }
            set { m_title = value ?? ""; }
        }

        public string Message
        {
            get { return m_message; }
            set { m_message = value ?? ""; }
        }

        public int Position { get; set; }
        public int StepSize { get; set; }
        public int Minimum { get; set; }
        public int Maximum { get; set; }
        public bool IsIndeterminate { get; set; }
        public bool AllowCancel { get; set; }
        public bool IsCanceling { get; set; }
        public bool Canceled { get; private set; }
        public bool IsDisposed { get; private set; }

        // No UI thread to marshal to; callers run work directly.
        public ISynchronizeInvoke SynchronizeInvoke { get { return null; } }

        public void Step(int amount)
        {
            Position += amount;
        }

        // Nothing here ever cancels; present so the event is not flagged unused.
        internal bool HasCancelingHandlers { get { return Canceling != null; } }

        public object RunTask(Func<IThreadedProgress, object[], object> backgroundTask,
            params object[] parameters)
        {
            return RunTask(true, backgroundTask, parameters);
        }

        // useSeparateThread is ignored: headless callers have no message pump
        // to keep responsive, so the task always runs on the calling thread.
        public object RunTask(bool useSeparateThread,
            Func<IThreadedProgress, object[], object> backgroundTask,
            params object[] parameters)
        {
            if (backgroundTask == null)
                return null;
            return backgroundTask(this, parameters);
        }

        public void Dispose()
        {
            IsDisposed = true;
        }
    }
}
"""


def _compile_headless_progress():
    """
    Compile ``_HEADLESS_PROGRESS_CS`` in memory and return the .NET type.

    Uses CodeDom, available because FieldWorks 9 runs on .NET Framework 4.8.
    Compile errors are raised with csc's messages so a mismatch with a future
    LCM ``IThreadedProgress`` surface names the member at fault.
    """
    from Microsoft.CSharp import CSharpCodeProvider
    from System.CodeDom.Compiler import CompilerParameters

    lcm_utils_path = clr.GetClrType(IThreadedProgress).Assembly.Location

    params = CompilerParameters()
    params.GenerateInMemory = True
    params.GenerateExecutable = False
    params.ReferencedAssemblies.Add("System.dll")
    params.ReferencedAssemblies.Add(lcm_utils_path)

    provider = CSharpCodeProvider()
    try:
        results = provider.CompileAssemblyFromSource(params, _HEADLESS_PROGRESS_CS)
    finally:
        provider.Dispose()

    if results.Errors.HasErrors:
        messages = "; ".join(
            str(e) for e in results.Errors if not e.IsWarning
        )
        raise FP_ParameterError(
            f"Could not compile HeadlessThreadedProgress against "
            f"{lcm_utils_path}: {messages}"
        )

    return results.CompiledAssembly.GetType(
        "Flexicon.Headless.HeadlessThreadedProgress", True
    )


def _load_headless_progress_class():
    _compile_headless_progress()
    # pythonnet indexes assemblies as they load, so the in-memory one is
    # importable by namespace as soon as CompileAssemblyFromSource returns.
    from Flexicon.Headless import HeadlessThreadedProgress as compiled

    return compiled


# IThreadedProgress that runs work on the calling thread with no UI.
#
# FieldWorks' ProgressDialogWithTask allocates a WinForms Form and forces a
# Win32 handle on construction (issue #289); OpenProject defaults to this
# class instead. RunTask(task, args) and RunTask(useSeparateThread, task,
# args) both run task(progress, args) synchronously and return its result.
HeadlessThreadedProgress = _load_headless_progress_class()
