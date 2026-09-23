#
#   FLExLCM.py
#
#   Module:     Project access functions for FieldWorks Language Explorer
#               via SIL Language and Culture Model (LCM).
#               (Prior to FW 9 this was known as "FDO" -- "FieldWorks
#               Data Objects")
#
#   Platform: Python.NET
#             (ITsString doesn't work in IRONPython)
#             FieldWorks Version 9
#
#   Copyright Craig Farrow, 2008 - 2022
#

import os

import clr

clr.AddReference("System")
import System

clr.AddReference("FwUtils")
clr.AddReference("FieldWorks")
clr.AddReference("FwCoreDlgs")
clr.AddReference("FwControls")
clr.AddReference("FdoUi")
clr.AddReference("SIL.Core")
clr.AddReference("SIL.Core.Desktop")
clr.AddReference("SIL.LCModel")
clr.AddReference("SIL.LCModel.Core")

# Classes needed for loading the Cache
from SIL.LCModel import LcmCache, LcmSettings, LcmFileHelper
from SIL.LCModel.Core.Cellar import CellarPropertyType as _LCMCellarPropertyType

from SIL.FieldWorks import ProjectId
from SIL.FieldWorks.Common.Controls import ProgressDialogWithTask
from SIL.FieldWorks.Common.FwUtils import ThreadHelper
from SIL.FieldWorks.Common.FwUtils import FwDirectoryFinder
from SIL.FieldWorks.Common.FwUtils import FwUtils
from SIL.FieldWorks.FdoUi import FwLcmUI
from SIL.FieldWorks.FwCoreDlgs import ChooseLangProjectDialog

# Import Python mirror of CellarPropertyType constants
from .Shared.lcm_constants import CellarPropertyType
from .headless_ui import HeadlessLcmUI, HeadlessThreadedProgress

# --- Globals --------------------------------------------------------

CellarStringTypes = {
    _LCMCellarPropertyType.String,
}
CellarMultiStringTypes = {_LCMCellarPropertyType.MultiUnicode, _LCMCellarPropertyType.MultiString}
CellarAllStringTypes = CellarStringTypes | CellarMultiStringTypes
# -----------------------------------------------------------


def GetListOfProjects():
    # Enumerates local projects only; network drives are not yet supported.
    projectsPath = FwDirectoryFinder.ProjectsDirectory
    objs = os.listdir(str(projectsPath))
    projectList = []
    for dirname in objs:
        # FieldWorks can leave ghost directories, so we test
        # for the fwdata file, not just the directory. (Issue #48)
        suffix = LcmFileHelper.ksFwDataXmlFileExtension
        if os.path.isfile(os.path.join(projectsPath, dirname, dirname + suffix)):
            projectList.append(dirname)
    return sorted(projectList)


# -----------------------------------------------------------


def OpenProject(projectName, ui=None, progress=None):
    """
    Open a FieldWorks project.

    projectName:
        - Either the full path including ".fwdata" suffix, or
        - The name only, opened from the default project location.

    ui:
        - Optional ILcmUI implementation. When None (the default, since
          issue #285) a bare `HeadlessLcmUI()` is used: it never blocks and
          never silently discards a conflicting save, instead raising
          `FP_ConflictingSaveError` so the condition surfaces to the caller.
        - Interactive, FLEx-hosted callers that genuinely want the WinForms
          dialogs should pass `ui=FwLcmUI(None, ThreadHelper())` explicitly.
          `FwLcmUI` opens modal dialogs and marshals through
          `Control.Invoke`, which in a process with no message pump blocks
          the commit thread and, on a conflicting save, silently discards
          this session's unsaved writes. See issues #238 and #285.

    progress:
        - Optional ``IThreadedProgress`` implementation. When None (the
          default, since issue #289) a bare ``HeadlessThreadedProgress()``
          is used: it runs any progress task on the calling thread and
          allocates no WinForms handle.
        - Interactive callers that want the historical FieldWorks progress
          dialog may pass ``progress=ProgressDialogWithTask(ThreadHelper())``
          explicitly. That object is ``IDisposable`` and is disposed after
          the open completes so Win32 handles do not leak per call.
    """

    projectFileName = LcmFileHelper.GetXmlDataFileName(projectName)

    projId = ProjectId(projectFileName)

    if ui is None:
        ui = HeadlessLcmUI()
    if progress is None:
        progress = HeadlessThreadedProgress()
    dirs = FwDirectoryFinder.LcmDirectories
    settings = LcmSettings()
    # Migration should be done within FieldWorks
    settings.DisableDataMigration = True

    # SIL.LCModel\LcmCache.cs
    # public static LcmCache CreateCacheFromExistingData(
    #    IProjectIdentifier projectId,
    #    string userWsIcuLocale,
    #    ILcmUI ui,
    #    ILcmDirectories dirs,
    #    LcmSettings settings,
    #    IThreadedProgress progressDlg)
    try:
        return LcmCache.CreateCacheFromExistingData(
            projId, "en", ui, dirs, settings, progress
        )
    finally:
        if isinstance(progress, ProgressDialogWithTask):
            progress.Dispose()
