#
#   FLExProject.py
#
#   Class: FLExProject
#            Fieldworks Language Explorer project access functions
#            via SIL Language and Culture Model (LCM) API.
#
#
#   Platform: Python.NET
#             (ITsString doesn't work in IRONPython)
#             FieldWorks Version 9
#
#   Copyright Craig Farrow, 2008 - 2024
#

# Initialise low-level FLEx data access
from . import FLExInit
from . import FLExLCM

from subprocess import Popen, DETACHED_PROCESS
from .FLExGlobals import FWExecutable
from . import FLExGlobals

from .exceptions import (
    FP_ProjectError,
    FP_FileNotFoundError,
    FP_FileLockedError,
    FP_MigrationRequired,
    FP_RuntimeError,
    FP_ReadOnlyError,
    FP_WritingSystemError,
    FP_NullParameterError,
    FP_ParameterError,
    FP_TransactionError,
    FP_ConflictingSaveError,
)

import logging
import os
import clr

from .Shared.string_utils import normalize_ws_handle, best_multistring_alternative

clr.AddReference("System")
import System

from SIL.LCModel import (
    ICmObjectRepository,
    ILexEntryRepository,
    ILexEntry,
    LexEntryTags,
    ILexSense,
    LexSenseTags,
    IWfiWordformRepository,
    WfiWordformTags,
    WfiGlossTags,
    IWfiAnalysisRepository,
    IWfiAnalysis,
    WfiAnalysisTags,
    WfiMorphBundleTags,
    LexExampleSentenceTags,
    MoFormTags,
    ILexRefTypeRepository,
    ICmPossibilityRepository,
    ICmPossibilityList,
    ICmSemanticDomain,
    TextTags,
    ITextRepository,
    IStTxtPara,
    ISegmentRepository,
    IReversalIndex,
    IReversalIndexEntry,
    ReversalIndexEntryTags,
    IMoMorphType,
    SpecialWritingSystemCodes,
    LcmInvalidClassException,
    LcmInvalidFieldException,
    LcmFileLockedException,
    LcmDataMigrationForbiddenException,
    IUndoStackManager,
)

from SIL.LCModel.Core.Cellar import (
    CellarPropertyType,
    CellarPropertyTypeFilter,
)

from SIL.LCModel.Infrastructure import (
    IFwMetaDataCacheManaged,
)

from SIL.LCModel.Core.KernelInterfaces import ITsString, ITsStrBldr
from SIL.LCModel.Core.Text import TsStringUtils
from SIL.LCModel.Utils import WorkerThreadException, ReflectionHelper
from SIL.LCModel.Application.ApplicationServices import XmlTranslatedLists
from SIL.FieldWorks.Common.FwUtils import (
    StartupException,
    FwAppArgs,
)

# -----------------------------------------------------------


def AllProjectNames():
    """
    Returns a list of FieldWorks projects that are in the default location.
    """

    return FLExLCM.GetListOfProjects()


# -----------------------------------------------------------


def OpenProjectInFW(projectName):

    Popen([FWExecutable, "-db", projectName], creationflags=DETACHED_PROCESS)


# -----------------------------------------------------------
#
# Attached views -- FLExProject.FromOpenProject()
#
# A FLExProject can be reached two ways: it can OWN a project it opened
# itself (OpenProject), or it can be an ATTACHED VIEW over a cache some
# other host already opened (FromOpenProject). The two differ in exactly
# one observable: an attached view carries `_attached_donor`.
#
# The constants below are the shared, ASCII-only refusal texts for the
# lifecycle paths a view must not take. They live at module scope so
# undoable_operation.py can reach them through the same lazy
# import-inside-the-method it already uses for the exception classes.
#
# On the laziness: the two modules import each other, but both directions
# are already lazy -- this module reaches undoable_operation only inside
# UndoableOperation() (see below), and undoable_operation reaches this one
# only inside __enter__. Keeping the reverse import lazy preserves that
# symmetry and leaves either module safe to import first. (The comments in
# undoable_operation.py assert a module-level import here that does not
# exist; they are pre-existing and left alone rather than widening this
# feature's diff.)


def _IsAttachedView(obj):
    """
    Is `obj` a FLExProject attached to a cache someone else opened?

    Invariant A (specs/flexicon-project-bridge/data-model.md section 1):
    `_attached_donor` is present iff the instance is an attached view, and
    every lifecycle guard branches on THIS -- never on `writeEnabled` and
    never on `_undoable`. Those two cannot carry the distinction: a
    read-only owned project and a read-only view agree on `writeEnabled`,
    and an owned project opened with `undoable=False` agrees with every
    view on `_undoable`.
    """

    return hasattr(obj, "_attached_donor")


# The host owns the save. Raised by SaveChanges() on a view.
#
# Deliberately does NOT repeat the standing "Use CloseProject() instead"
# advice that the owned-project path gives: on a view CloseProject() is a
# silent no-op, so a caller who followed it would get a run that reports
# success and writes nothing -- the exact failure class this seam exists
# to end (research.md R7).
_ATTACHED_VIEW_SAVE_REFUSAL = (
    "SaveChanges() is not available on a project attached with "
    "FromOpenProject(). This object is a view over a cache the host "
    "(FLExTools, or FieldWorks itself) opened and still owns, and the "
    "host saves it on its own schedule. Make your changes inside "
    "Transaction() and simply return from Main() -- do not save, and do "
    "not close."
)

# Phase 2 is unavailable on a view. Used by undoable_operation.py.
#
# The owned-project wording ("opened with undoable=False") is actively
# misleading here: nobody called OpenProject, and no argument the module
# could pass would change the answer (research.md R2).
_ATTACHED_VIEW_UNDOABLE_REFUSAL = (
    "UndoableOperation() is not available on a project attached with "
    "FromOpenProject(). The host opened a session-long non-undoable task "
    "over this cache, and starting an undoable unit of work inside it "
    "would nest the wrong kind of task. Use Transaction() instead, which "
    "is the supported construct on an attached view."
)

# The host owns the rollback. Raised by AbortSession() on a view.
#
# Deliberately does NOT offer Transaction() as the remedy the way
# _ATTACHED_VIEW_UNDOABLE_REFUSAL does. A view is always Phase 1, and in
# Phase 1 Transaction() has no rollback at all (issue #236; see
# Transaction()'s own docstring) -- so pointing a caller who asked to
# DISCARD work at it would be a wrong answer in the shape of a helpful
# one. There is no module-side discard on a view; say so.
_ATTACHED_VIEW_ABORT_REFUSAL = (
    "AbortSession() is not available on a project attached with "
    "FromOpenProject(). The open unit of work belongs to the host "
    "(FLExTools, or FieldWorks itself), which opened it over this cache "
    "before your module was called; rolling it back here would discard "
    "the host's own unsaved edits as well as yours, and would leave the "
    "host holding an envelope it did not open. A module cannot discard "
    "its writes on an attached view -- let the exception propagate out "
    "of Main() and report it, and leave the keep-or-discard decision to "
    "the host and its user."
)


# -----------------------------------------------------------


class FLExProject(object):
    """
    This class provides convenience methods for accessing a FieldWorks
    project by hiding some of the complexity of LCM.
    For functionality that isn't provided here, LCM data and methods
    can be used directly via `FLExProject.project`, `FLExProject.lp` and
    `FLExProject.lexDB`.
    However, for long term use, new methods should be added to this class.

    Usage::

        from SIL.LCModel.Core.KernelInterfaces import ITsString, ITsStrBldr
        from SIL.LCModel.Core.Text import TsStringUtils

        project = FLExProject()
        try:
            project.OpenProject("my project",
                                writeEnabled = True/False)
        except (FP_ProjectError, FP_FileNotFoundError, FP_FileLockedError,
                System.IO.FileNotFoundException, System.IO.IOException,
                LcmFileLockedException, LcmDataMigrationForbiddenException) as e:
            #"Failed to open project"
            print(f"Error opening project: {e}")
            del project
            exit(1)

        WSHandle = project.WSHandle('en')

        # Traverse the whole lexicon
        for lexEntry in project.LexiconAllEntries():
            headword = project.LexiconGetHeadword(lexEntry)

            # Use get_String() and set_String() with text fields:
            lexForm = lexEntry.LexemeFormOA
            lexEntryValue = ITsString(lexForm.Form.get_String(WSHandle)).Text
            newValue = convert_headword(lexEntryValue)
            mkstr = TsStringUtils.MakeString(newValue, WSHandle)
            lexForm.Form.set_String(WSHandle, mkstr)

    """

    def OpenProject(self, projectName, writeEnabled=False, undoable=True, ui=None):
        """
        Open a project. The project must be closed with `CloseProject()` to
        save any changes, and release the lock.

        projectName:
            - Either the full path including ".fwdata" suffix, or
            - The name only, to open from the default project location.

        writeEnabled:
            Enables changes to be written to the project, which will be
            saved on a call to `CloseProject()`.
            LCM will raise an exception if changes are attempted without
            opening the project in this mode.

        undoable:
            **Default since 4.4.0: True.** Each write runs inside its own
            named, nesting-aware LCM unit of work, so an exception escaping
            an operation rolls that operation's mutations back, and the
            operation appears in FLEx's Ctrl+Z menu under its own label.
            This is the mode the write path is designed for (decision D3 in
            `specs/write-path-transactions/tasks.md`).

            Only meaningful when writeEnabled=True; ignored otherwise.

            Passing ``undoable=False`` opts back into the legacy Phase 1
            behaviour: one session-long ``BeginNonUndoableTask()`` envelope,
            in which ``Transaction()`` is a labelling/nesting construct only
            and **nothing rolls back** -- the atomicity unit becomes the
            whole session (issue #236). It is retained for callers that
            depend on the old semantics, and it warns once per
            ``OpenProject()`` call. Do not use it when the project may be
            open in FLEx or another process (D3).

            Two consequences of the default worth knowing before you rely on
            per-operation rollback:

            * Nested blocks **join** the outer unit of work rather than
              opening an independent one, so catching an exception from an
              inner block while still inside the outer block commits that
              inner block's partial writes. See `docs/EXCEPTION_HANDLING.md`.
            * ``AbortSession()`` is an ``undoable=False`` primitive. Under
              this default it returns False between operations and raises
              ``FP_TransactionError`` inside one (D8) -- per-operation
              rollback covers that ground instead.

        ui:
            Optional `ILcmUI` implementation, passed through to
            `FLExLCM.OpenProject()`. **Default since issue #285: a bare
            `HeadlessLcmUI()`.** It never blocks and never silently
            reverts; a conflicting save raises `FP_ConflictingSaveError`
            instead of discarding this session's unsaved changes.

                from flexicon import FLExProject
                project = FLExProject()
                project.OpenProject("MyProject", writeEnabled=True)
                # ui=None -> HeadlessLcmUI() -> conflicting save raises
                # FP_ConflictingSaveError

            Interactive, FLEx-hosted callers that genuinely want the
            WinForms dialogs should opt in explicitly:

                from SIL.FieldWorks.FdoUi import FwLcmUI
                from SIL.FieldWorks.Common.FwUtils import ThreadHelper
                project.OpenProject("MyProject", writeEnabled=True,
                                     ui=FwLcmUI(None, ThreadHelper()))

            `FwLcmUI` opens modal dialogs and marshals through
            `Control.Invoke` -- fine for an interactive FLEx-hosted
            process, but unsafe in a headless one (issue #238): a
            conflicting save can block the commit thread on a dialog with
            no owner, or silently discard this session's unsaved changes.

        Note:
            A call to `OpenProject()` may fail with a `FP_FileLockedError`
            exception if the project is open in Fieldworks (or another
            application).
            To avoid this, project sharing can be enabled within the
            Fieldworks Project Properties dialog. In the Sharing tab,
            turn on the option "Share project contents with programs
            on this computer".

        """

        try:
            self.project = FLExLCM.OpenProject(projectName, ui)

        except System.IO.FileNotFoundException as e:
            raise FP_FileNotFoundError(projectName, e)

        except LcmFileLockedException as e:
            raise FP_FileLockedError()

        except (LcmDataMigrationForbiddenException, WorkerThreadException) as e:
            # Raised if the FW project needs to be migrated
            # to a later version. The user needs to open the project
            # in FW to do the migration.
            # Jason Naylor [Dec2018] said not to do migration from an external
            # program: "We think that is something a FieldWorks user should
            # explicitly decide."
            raise FP_MigrationRequired()

        except StartupException as e:
            # An unknown error -- pass on the full information
            raise FP_ProjectError(e.Message)

        self.lp = self.project.LangProject
        self.lexDB = self.lp.LexDbOA

        # Set up FieldWorks for making changes to the project.
        # All changes will be automatically saved when this object is
        # deleted.

        self.writeEnabled = writeEnabled
        self._undoable = undoable and writeEnabled  # Only meaningful if write-enabled
        # Note: nesting depth of active _TransactionCM / UndoableOperation
        # blocks is intentionally NOT tracked here. A hand-maintained Python
        # counter (formerly `self._transaction_depth`) was issue #234: it
        # leaked permanently whenever an inner block's __enter__ raised,
        # because nothing on that path decremented it. `_NestingAwareTransaction`
        # and `_FLExUndoableOperation` now ask LCM's own
        # `ActionHandlerAccessor.CurrentDepth` at every __enter__ instead --
        # there is no local state left to leak. See
        # specs/write-path-transactions/spec.md B1.

        if self.writeEnabled and not self._undoable:
            # One-shot warning (issue #236 honesty pass): emitted once per
            # OpenProject() call rather than once per Transaction(), so it
            # cannot train callers to tune it out. See A2 in
            # specs/write-path-transactions/spec.md and
            # docs/EXCEPTION_HANDLING.md.
            #
            # Since 4.4.0 (task DEF) this is the OPT-OUT path, not the
            # default -- reaching it means the caller passed undoable=False
            # explicitly, so the warning names that choice rather than
            # describing an unavoidable limitation.
            logging.getLogger(__name__).warning(
                "OpenProject: writeEnabled=True with an explicit "
                "undoable=False. This opts OUT of per-operation units of "
                "work, which is the default since 4.4.0. In this legacy "
                "mode Transaction() is a labelling/nesting construct only -- "
                "liblcm exposes no reachable rollback-to-mark API in this "
                "mode (issue #236). The atomicity unit for this whole "
                "session is the SESSION, not the operation: if code raises "
                "mid-operation, every mutation applied before the failure "
                "remains in the in-memory cache and will be written to disk "
                "by CloseProject()/SaveChanges(). Drop the argument to get "
                "rollback back. See docs/EXCEPTION_HANDLING.md."
            )
            # Phase 1 behavior: whole session is non-undoable (rollback transactions only)
            try:
                # This must be called before calling any methods that change
                # the project.
                self.project.MainCacheAccessor.BeginNonUndoableTask()
            except System.InvalidOperationException:
                raise FP_ProjectError("BeginNonUndoableTask() failed.")
        elif self.writeEnabled and self._undoable:
            # Phase 2 behavior: no envelope; each UndoableOperation wraps its own task
            logging.getLogger(__name__).debug("OpenProject: undoable mode enabled")
            # Nothing to do here; BeginUndoTask called per-operation by UndoableOperation

    @classmethod
    def FromOpenProject(cls, donor) -> "FLExProject":
        """
        Attach a flexicon facade to a project someone else already opened.

        `donor` is whatever the host handed `Main()`: under real FLExTools a
        **flexlibs** ``FLExProject`` (flextoolslib/code/FTModules.py:75), under
        the FLExTools MCP a **flexicon** one. Returns an object exposing the
        full flexicon facade over the donor's cache.

        **Never opens a project, and never closes one.** Reopening a project
        the host is holding raises ``FP_FileLockedError``, which is the trap
        any "just make your own flexicon project" advice walks into.

        The portable module shape -- identical under both hosts::

            from flexicon import FLExProject

            def Main(project, report, modifyAllowed):
                fx = FLExProject.FromOpenProject(project)
                lex, variants = fx.LexEntry, fx.Variants

        Importing the class is not enough on its own: it does not change the
        instance ``Main()`` is handed. This classmethod is what makes that
        import load-bearing.

        Notes:

        * **Idempotent.** A donor that is already a flexicon ``FLExProject``
          is returned unchanged, by identity -- it owns its project, and a
          module written against this seam must stay correct under the MCP.
        * **Phase 1 only.** The view is always ``_undoable = False``; the host
          owns the transaction envelope. Use ``Transaction()``;
          ``UndoableOperation()`` is refused.
        * **Owns nothing.** ``CloseProject()`` on the returned view is a
          no-op and ``SaveChanges()`` is refused. The host saves.

        Returns:
            FLExProject: A view over the donor's cache, or the donor itself
                when it is already a flexicon FLExProject.

        Raises:
            FP_ParameterError: the donor is missing the cache or
                ``writeEnabled``. The message names every absent attribute
                and the donor's module.
        """

        # Idempotence FIRST, before validation -- a flexicon donor is already
        # exactly what the caller asked for, and re-attaching would silently
        # downgrade an MCP session from Phase 2 to Phase 1 while leaving two
        # objects believing they own one cache.
        if isinstance(donor, cls):
            return donor

        cls._ValidateDonor(donor)

        # Allocate WITHOUT calling __init__: this class deliberately has none
        # (all state is born in OpenProject), and adding one now would be a
        # breaking change for every caller that constructs FLExProject() with
        # no arguments -- the documented construction.
        view = cls.__new__(cls)

        view.project = donor.project

        # Prefer the donor's own handles so the view points at the very
        # objects the host is using; fall back to deriving them from the
        # cache so a thinner donor still works.
        lp = getattr(donor, "lp", None)
        view.lp = lp if lp is not None else donor.project.LangProject

        lexDB = getattr(donor, "lexDB", None)
        view.lexDB = lexDB if lexDB is not None else view.lp.LexDbOA

        # Verbatim, including False. A view never upgrades its permissions.
        view.writeEnabled = donor.writeEnabled

        # Unconditionally Phase 1, regardless of the donor's own mode (a
        # flexlibs donor has no mode at all -- it has no _undoable). When the
        # host is write-enabled it holds a session-long BeginNonUndoableTask()
        # envelope, and an undoable unit of work inside that is the wrong kind
        # of nesting.
        view._undoable = False

        # The mode discriminator every lifecycle guard branches on.
        view._attached_donor = donor

        logging.getLogger(__name__).debug(
            "FromOpenProject: attached a view to a cache owned by %s "
            "(writeEnabled=%s)",
            type(donor).__module__,
            view.writeEnabled,
        )

        return view

    @classmethod
    def _ValidateDonor(cls, donor):
        """
        Refuse a donor we cannot build a view over, AT the seam.

        The failure this replaces is an ``AttributeError`` fifty frames deep
        inside an operation -- unreadable to the non-programmer this package
        exists for (SPEC 3c). Collecting *every* missing attribute into one
        message beats failing on whichever happens to be checked first: a
        donor that is wrong is usually wrong in more than one way, and one
        round-trip per missing attribute is a bad way to learn that.

        Only `project` and `writeEnabled` are required. `lp` and `lexDB` are
        derived from the cache when the donor does not carry them, so their
        absence is not an error.

        Raises:
            FP_ParameterError: naming every absent attribute and the donor's
                module.
        """

        missing = []

        # None counts as absent: a donor carrying project=None is no more
        # usable than one with no `project` at all, and installing that None
        # would just move the AttributeError deeper.
        if getattr(donor, "project", None) is None:
            missing.append("project")

        # Presence only -- the VALUE is borrowed verbatim, and False is a
        # perfectly good answer (a read-only host).
        if not hasattr(donor, "writeEnabled"):
            missing.append("writeEnabled")

        if not missing:
            return

        # type(donor).__module__ rather than the class name: BOTH candidate
        # donor classes are named "FLExProject" (flexlibs.code.FLExProject vs
        # flexicon.code.FLExProject), so the name discriminates nothing and
        # the module is the only honest answer to "what did I actually get?".
        raise FP_ParameterError(
            "FromOpenProject() cannot attach to this object: it is missing "
            "{missing}. Pass the project your module was handed as Main()'s "
            "first argument. (Received an object of type {name} from module "
            "{module}.)".format(
                missing=", ".join(missing),
                name=type(donor).__name__,
                module=type(donor).__module__,
            )
        )

    def CloseProject(self):
        """
        Save any pending changes and dispose of the LCM object.

        Guard added for issue #243 (spec.md C1/C6/C7): the Phase 1
        ``EndNonUndoableTask()`` mirror call below is guarded two ways so
        that a raise there can never skip ``usm.Save()``, which would
        otherwise discard the whole session's in-memory work with no
        data written to disk:

        1. ``HasOpenSessionTask()`` is checked first. If no envelope is
           open (e.g. a prior mid-session ``SaveChanges()`` call already
           collapsed it -- spec.md C9), the ``End`` call is skipped
           entirely rather than assuming ``writeEnabled and not
           _undoable`` implies the envelope is still present. This is an
           anomaly by construction in Phase 1 (spec.md C14/C18), so it is
           logged at ERROR (spec.md C23) rather than debug -- see the
           branch below for exactly what is and is not asserted.
        2. Even when the check says an envelope IS open, the ``End``
           call itself is wrapped in try/except so an unexpected raise
           there (not just the already-prevented depth-0 case) still
           cannot prevent ``usm.Save()`` from running.

        End-then-Save order is unchanged (C7) -- this does not reorder
        ``usm.Save()`` ahead of the ``End`` call; P-5 (spec.md section 2)
        proved that shape trades one guaranteed raise for another with
        no save occurring either way.

        ``Dispose()``/``del self.project`` run in a ``finally`` (spec.md
        C15) so the live LCM handle is never leaked, including when the
        ERROR branch below is taken or when ``usm.Save()`` itself raises.

        Attached-view no-op: on a project attached with
        ``FromOpenProject()``, this method does nothing and returns
        ``None`` -- the host owns the cache, and a defensive close in an
        otherwise-correct module must not fail (SPEC 3b).
        """
        if _IsAttachedView(self):
            logging.getLogger(__name__).debug(
                "CloseProject: no-op on a project attached with "
                "FromOpenProject(); the host owns this cache and its "
                "lifecycle."
            )
            return None
        if hasattr(self, "project"):
            try:
                if self.writeEnabled:
                    if not self._undoable:
                        # Phase 1: This must be called to mirror the call to
                        # BeginNonUndoableTask() -- but only if that envelope
                        # is actually still open (issue #243, spec.md C6).
                        if self.HasOpenSessionTask():
                            try:
                                self.project.MainCacheAccessor.EndNonUndoableTask()
                            except Exception as e:
                                # Any raise here -- not just the depth-0 case
                                # already prevented by the check above -- must
                                # not be allowed to skip usm.Save() below
                                # (spec.md C6 part 2). Log loudly: a single,
                                # easy-to-miss [WARN] elsewhere in this exact
                                # failure path is the defect issue #243 exists
                                # to fix, so swallowing this silently would
                                # repeat it.
                                logging.getLogger(__name__).warning(
                                    "CloseProject: EndNonUndoableTask() raised "
                                    "even though HasOpenSessionTask() reported "
                                    "an open envelope; continuing to "
                                    "usm.Save() below regardless. %s: %s",
                                    type(e).__name__, e,
                                )
                        else:
                            # PRIMARY detector (spec.md C18, unchanged in
                            # logic from C14; now feeds this log line
                            # rather than a raise -- C23 WITHDRAWS the
                            # FP_ProjectError this branch used to raise).
                            # Reaching this branch at all means
                            # writeEnabled and not self._undoable (Phase
                            # 1, where the session-long envelope should
                            # still be open) yet HasOpenSessionTask() read
                            # False -- unreachable by construction unless
                            # something already ended that envelope before
                            # CloseProject() was entered. This is the
                            # anomaly; naming it is the whole point of the
                            # ERROR level (a single easy-to-miss [WARN]
                            # elsewhere in this exact failure path was the
                            # original incident's only symptom -- spec.md
                            # QUEUE.md item 1 / C14).
                            #
                            # OPTIONAL/diagnostic-only (spec.md C18 point
                            # 3): a pre-Save() HasUnsavedChanges read,
                            # logged for context. It is a proxy for "did
                            # an End just succeed", not independent
                            # information, so it MUST NOT gate anything
                            # here and does not create a second code path.
                            # P-9 proved reading it as "nothing pending to
                            # save" when False is a FALSE NEGATIVE (all 25
                            # entries still existed in memory at that
                            # reading), so it is logged as a raw value
                            # only -- this log asserts NOTHING about
                            # whether data was lost.
                            diagnostic_has_unsaved = None
                            try:
                                diagnostic_has_unsaved = self.ObjectRepository(
                                    IUndoStackManager
                                ).HasUnsavedChanges
                            except Exception:
                                pass  # diagnostic-only; never gates the save below
                            logging.getLogger(__name__).error(
                                "CloseProject: HasOpenSessionTask() read False "
                                "inside Phase 1 (writeEnabled and not "
                                "_undoable) -- unreachable by construction "
                                "unless the session envelope was already "
                                "ended before CloseProject() was entered. "
                                "Skipping EndNonUndoableTask() and proceeding "
                                "to usm.Save() below regardless (pre-Save() "
                                "HasUnsavedChanges=%s, a diagnostic value "
                                "only -- spec.md C18 -- not proof of what "
                                "is or is not pending).",
                                diagnostic_has_unsaved,
                            )
                    # Phase 2: In undoable mode, no EndNonUndoableTask() to call
                    # (each UndoableOperation handles its own Begin/End)

                    # Save all changes to disk
                    usm = self.ObjectRepository(IUndoStackManager)
                    usm.Save()
            finally:
                # C15: always dispose, even if the ERROR branch above was
                # taken or usm.Save() itself raised -- a raise here must
                # never leak the live LCM handle.
                self.project.Dispose()
                del self.project

    def _ReadActionHandlerDepth(self):
        """
        Read the live LCM action handler's ``CurrentDepth`` verbatim.

        Private helper backing the public ``CurrentDepth`` property and
        ``HasOpenSessionTask()`` method (issue #243, spec.md C2/C5). It
        deliberately does NOT tolerate a closed/never-opened project by
        degrading to ``0`` -- it raises instead. The three existing
        internal call sites (`transaction.py:172`,
        `undoable_operation.py:102`, `System/CustomFieldOperations.py:306`)
        each wrap a read like this one in their own
        ``try/except``/``getattr(..., 0)`` to tolerate incomplete test
        doubles standing in for a real ``IActionHandler``; that tolerance
        is intentionally NOT inherited here (spec.md C5) -- a public
        surface that silently returns ``0`` for a closed project would
        reintroduce the exact depth ambiguity issue #243 exists to
        remove. A future caller wanting the lenient behaviour wraps a
        call to this helper in its own ``try/except`` (see T2); this
        helper never does that on their behalf.

        Returns:
            int: ``self.project.ActionHandlerAccessor.CurrentDepth``,
                unmodified.

        Raises:
            FP_ProjectError: If the project is closed or was never
                opened (``self.project`` does not exist).
        """
        if not hasattr(self, "project"):
            raise FP_ProjectError(
                "Cannot read action handler depth: project is not open."
            )
        return self.project.ActionHandlerAccessor.CurrentDepth

    @property
    def CurrentDepth(self):
        """
        Raw LCM action-handler nesting depth (issue #243, spec.md C2/C4).

        A direct, documented ``int`` passthrough of
        ``self.project.ActionHandlerAccessor.CurrentDepth`` -- the same
        value three internal call sites already read in a more lenient
        form (`transaction.py`, `undoable_operation.py`,
        `System/CustomFieldOperations.py`). Implemented as a property
        (matching the ``Cache`` property's precedent as a discoverable,
        no-argument, no-side-effect escape hatch onto raw LCM state)
        rather than a method, since reading the depth has no side effect
        and nothing to parameterize.

        Mode-dependence (frozen P-2 table, spec.md section 2): under
        ``undoable=False`` the session-long ``BeginNonUndoableTask()``
        envelope holds this at 1 for the whole session (unchanged inside
        ``Transaction()`` blocks); under ``undoable=True`` it is 0
        outside an ``UndoableOperation()`` block and 1 inside one
        (``Transaction()`` never changes it either way).

        Returns:
            int: The real, unmodified depth. For a read-only
                (``writeEnabled=False``) project this is legitimately
                ``0`` and is returned WITHOUT raising (spec.md C4) -- a
                pure read has no mutating consequence, so
                ``FP_ReadOnlyError`` would be domain-wrong here.

        Raises:
            FP_ProjectError: If the project is closed or was never
                opened.

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True,
            ...                     undoable=False)
            >>> project.CurrentDepth
            1
        """
        return self._ReadActionHandlerDepth()

    def HasOpenSessionTask(self):
        """
        Is the session-long ``BeginNonUndoableTask()`` envelope open?

        Answers exactly that narrow question (issue #243, spec.md C3) --
        it is NOT a mode-agnostic "is anything open" predicate, because
        ``CurrentDepth == 1`` means two structurally different things
        depending on mode:

        - Under ``undoable=False`` (Phase 1), ``OpenProject()`` opens one
          session-long envelope via ``BeginNonUndoableTask()`` that
          ``CloseProject()`` must mirror-close with
          ``EndNonUndoableTask()``. Here, depth > 0 means that envelope
          is open.
        - Under ``undoable=True`` (Phase 2, the 4.4.0 default), no such
          envelope is ever opened by construction -- each
          ``UndoableOperation()``/``Transaction()`` manages its own
          begin/end pair instead. So this method returns ``False``
          unconditionally in that mode -- a correct fact about that
          mode, not "nothing to report" -- WITHOUT using depth to decide
          it (depth is still read first, below, purely so a
          closed/never-opened project raises consistently regardless of
          mode).

        Returns:
            bool: ``False`` when ``self._undoable`` is ``True``.
                Otherwise ``self.CurrentDepth > 0``, read via the same
                private helper ``CurrentDepth`` uses.

        Raises:
            FP_ProjectError: If the project is closed or was never
                opened, in either mode.

        Example:
            >>> project.OpenProject("MyProject", writeEnabled=True,
            ...                     undoable=False)
            >>> project.HasOpenSessionTask()
            True
        """
        depth = self._ReadActionHandlerDepth()
        if self._undoable:
            return False
        return depth > 0

    @property
    def Cache(self):
        """
        The underlying LcmCache. For advanced users dropping to raw LCM.

        Provides discoverable access to the LcmCache instance that backs this
        project. Most users should prefer the operation classes (e.g.
        `project.Phonemes`, `project.LexEntry`), but this escape hatch is
        available for cases where raw LCM access is required.

        Returns:
            LcmCache: The underlying SIL.LCModel cache instance.

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject")
            >>> cache = project.Cache
            >>> # Use cache.ServiceLocator, cache.MainCacheAccessor, etc.
        """
        return self.project

    def GetService(self, interface_type):
        """
        Get an LCM service or factory by interface type.

        Discoverable wrapper around
        `self.project.ServiceLocator.GetService(interface_type)`.
        Use this to obtain factories and services when no higher-level
        operation class exposes the functionality you need.

        Args:
            interface_type: The .NET interface type to resolve
                (e.g. `IPhPhonemeFactory`).

        Returns:
            The service or factory instance registered for `interface_type`.

        Example:
            >>> from SIL.LCModel import IPhPhonemeFactory
            >>> factory = project.GetService(IPhPhonemeFactory)
            >>> phoneme = factory.Create()
        """
        return self.project.ServiceLocator.GetService(interface_type)

    def GetFactory(self, interface_type):
        """
        Resolve an LCM factory or service by interface type.

        Discoverable entry point for factory lookup that works around a
        pythonnet limitation: the generic
        `ILcmServiceLocator.GetInstance<T>()` method is not reachable
        via pythonnet's subscript syntax (`GetInstance[T]()`), which
        raises `AttributeError` on some pythonnet builds.

        Two resolution paths are tried in order:

          1. Direct overload-resolved call:
             `ServiceLocator.GetInstance(interface_type)`. Pythonnet
             normally binds this to the non-generic `GetInstance(Type)`
             overload. This is the pattern used throughout flexicon.
          2. Reflection: locate the parameterless `GetInstance<T>()`
             generic method, bind `T` to `interface_type`, and invoke.
             The resolved MethodInfo is cached on the FLExProject
             instance to avoid rescanning reflection on every call.

        Prefer this method when you need a factory and either:
          - `GetService` returned None for a registered interface, or
          - you want the explicit "this is a factory" semantic.

        Args:
            interface_type: A pythonnet interface type (e.g.
                `IMoInflAffMsaFactory`).

        Returns:
            The factory or service instance registered for
            `interface_type`.

        Raises:
            FP_NullParameterError: if `interface_type` is None.
            FP_ParameterError: if neither resolution path produces an
                instance.

        Example:
            >>> from SIL.LCModel import IMoInflAffMsaFactory
            >>> factory = project.GetFactory(IMoInflAffMsaFactory)
            >>> msa = factory.Create()
        """
        if interface_type is None:
            raise FP_NullParameterError()

        sl = self.project.ServiceLocator

        # Path 1: direct overload-resolved call. Matches the existing
        # ServiceLocator.GetInstance(InterfaceType) pattern used
        # throughout flexicon (e.g. FLExProject.py:3804, :4062). Works
        # on standard pythonnet builds where the Type-taking overload
        # of GetInstance binds cleanly.
        try:
            result = sl.GetInstance(interface_type)
            if result is not None:
                return result
        except Exception:
            # Pythonnet couldn't resolve the overload on this build.
            # Broad catch is intentional: Path 2 (reflection) is the
            # recovery path and we want it to engage on any Path-1
            # failure. Pythonnet 2.x surfaced overload-binding failures
            # as AttributeError / TypeError; pythonnet 3.x can surface
            # them as Python.Runtime.PythonException or
            # System.MissingMethodException. Listing exception types
            # makes this brittle across pythonnet versions; catching
            # any failure and falling through is correct here because
            # Path 2's MethodInfo lookup performs its own diagnostic
            # if the service surface is genuinely unusable. (issue #123)
            pass

        # Path 2: reflection over the parameterless generic
        # GetInstance<T>(). The open MethodInfo is cached on the
        # instance because GetType().GetMethods() scans the full
        # ServiceLocator surface; once is enough.
        method_def = getattr(self, "_get_instance_generic_method", None)
        if method_def is None:
            method_def = next(
                (
                    m for m in sl.GetType().GetMethods()
                    if m.Name == "GetInstance"
                    and m.IsGenericMethodDefinition
                    and m.GetParameters().Length == 0
                ),
                None,
            )
            if method_def is None:
                # Path 3: the interface-level IServiceProvider member.
                # ILcmServiceLocator's only base interface is
                # System.IServiceProvider, so GetService(Type) is always
                # present even when no GetInstance overload is reachable
                # -- this is the call the ~240 working lookups elsewhere
                # in flexicon use. Try it before giving up. (issue #272)
                result = sl.GetService(interface_type)
                if result is not None:
                    return result
                raise FP_ParameterError(
                    "ILcmServiceLocator exposes no resolvable "
                    f"GetInstance overload for {interface_type}"
                )
            self._get_instance_generic_method = method_def

        bound = method_def.MakeGenericMethod(clr.GetClrType(interface_type))
        result = bound.Invoke(sl, None)
        if result is None:
            raise FP_ParameterError(
                f"No factory or service registered for {interface_type}"
            )
        return result

    def Transaction(self, label="transaction"):
        """
        Return a context manager for labelling and nesting a group of writes.

        Mode-dependent semantics (read this before relying on it for safety):

        * ``undoable=False`` (the legacy opt-out mode; the default is
          ``undoable=True`` since 4.4.0): **there is no rollback.**
          liblcm exposes no reachable "roll back to a mark" primitive in
          this mode (issue #236; confirmed by reflection over
          `SIL.LCModel.dll` -- see `specs/write-path-transactions/spec.md`
          section 2 and D1 for the specific API name checked and confirmed
          absent). ``Transaction()`` still opens and closes cleanly, and nested
          ``with`` blocks (including the per-method
          ``BaseOperations._TransactionCM`` blocks used internally by
          Operations methods) still compose without error, but no exception
          raised inside the block undoes anything. The atomicity unit in
          this mode is the **whole session**: a mid-operation exception
          leaves every mutation applied up to that point sitting in the
          in-memory cache, and it will be written to disk on the next
          ``SaveChanges()``/``CloseProject()``. A per-session warning to this
          effect is logged once per ``OpenProject()`` call (not once per
          process or per instance -- a second ``OpenProject()`` call in the
          same session re-logs it), rather than on every ``Transaction()``
          call. See
          `docs/EXCEPTION_HANDLING.md`.
        * ``undoable=True``: this method itself is unchanged by the B1
          rewrite -- calling ``project.Transaction(label)`` directly still
          always returns the Phase 1, no-rollback ``_FLExTransaction``
          above (see ``test_transaction_body_always_passes_none_none``,
          which locks this). What changed under B1 is the internal
          ``BaseOperations._TransactionCM()`` wrapper that most Operations
          methods use: it no longer calls this method at all in
          ``undoable=True`` mode, and instead delegates to
          ``_NestingAwareTransaction``, which is genuinely transactional --
          backed directly by liblcm's ``UndoableUnitOfWorkHelper``, an
          exception rolls back everything written inside the block. See
          ``UndoableOperation()`` for the equivalent public, directly
          callable entry point in this mode.

        The name is kept (see D4 in `specs/write-path-transactions/tasks.md`):
        an earlier draft of this spec preferred renaming this method to
        avoid over-promising, but once the ``undoable=True`` rewrite lands
        the name is accurate for the mode this project is migrating
        towards, so renaming it away would make the name wrong exactly
        where it will soon be right.

        Args:
            label (str): Human-readable description for logging. Default: "transaction"

        Returns:
            _FLExTransaction: Context manager

        Raises:
            FP_ReadOnlyError: If project is not open (raised at write time, not here)

        Example::

            project = FLExProject()
            project.OpenProject("MyProject", writeEnabled=True)
            with project.Transaction("import batch"):
                for word, gloss in data:
                    entry = project.LexEntry.Create(word, "stem")
                    project.Senses.Create(entry, gloss, "en")
            project.CloseProject()

        See Also:
            UndoableOperation() - the ``undoable=True`` path; adds to FLEx Ctrl+Z menu.
        """
        from .transaction import _FLExTransaction

        # No LCM rollback API is reachable in this mode (see docstring and
        # issue #236) -- there is no discovery left to perform. Passing
        # (None, None) is the honest, permanent state; _FLExTransaction
        # still runs the body and re-raises any exception, it simply never
        # attempts a rollback.
        return _FLExTransaction(self, label, None, None)

    def SaveChanges(self):
        """
        Save all pending changes to disk without closing the project.

        This is equivalent to what CloseProject() does internally before Dispose().
        Useful after a successful Transaction block to ensure changes are persisted.

        Depth guard (issue #243, spec.md C20/C21): refuses to call
        ``usm.Save()`` whenever ``CurrentDepth > 0`` -- i.e. while a unit
        of work is open, in EITHER mode. Live probes (P-5/P-7/P-10-C)
        measured that calling ``usm.Save()`` at depth > 0 raises
        ``InvalidOperationException: Commit at wrong place.`` from liblcm,
        and that under ``undoable=False`` that failure's own path
        collapses the session-long envelope as a side effect, discarding
        the whole session's pending work with nothing written to disk
        (0/25 survivors measured pre-guard). This guard turns that into an
        honest, fail-fast ``FP_TransactionError`` before ``usm.Save()`` is
        ever attempted, so the refusal itself discards nothing.

        Note:
            Only valid for write-enabled, owned projects.
            Does NOT call EndNonUndoableTask() - the session stays open.
            Under ``undoable=False``, the session-long envelope opened by
            ``OpenProject()`` holds ``CurrentDepth`` at 1 for the entire
            session, so this method ALWAYS raises if called mid-session in
            that mode -- see the Example below. Use ``CloseProject()``
            instead, which ends that envelope before saving.
            Under ``undoable=True``, call this AFTER an
            ``UndoableOperation()``/``Transaction()`` block has exited
            (``CurrentDepth`` back to 0), never from inside one.

            That ``CloseProject()`` advice applies to OWNED projects only
            -- ones this instance opened via ``OpenProject()``. On a view
            obtained from ``FromOpenProject()`` it is actively wrong:
            ``CloseProject()`` is a no-op there, so following it would
            produce a run that reports success and saves nothing.

            On an attached view the host (FLExTools, or FieldWorks itself)
            opened the cache and saves it on its own schedule. Make the
            changes inside ``Transaction()`` and simply return from
            ``Main()``; there is nothing for the module to save or close.

        Raises:
            FP_RuntimeError: If this is a view obtained from
                ``FromOpenProject()``. Raised before the write-enabled and
                depth checks below, so the caller hears that the host owns
                the save rather than a read-only or transaction-depth
                diagnosis that would misdescribe the situation.
            FP_ReadOnlyError: If project is not write-enabled.
            FP_TransactionError: If ``CurrentDepth > 0`` -- a unit of work
                is currently open, in either mode. ``usm.Save()`` is never
                attempted when this is raised.

        Example (``undoable=True``, the 4.4.0 default)::

            with project.UndoableOperation("import batch"):
                for word in words:
                    project.LexEntry.Create(word, "stem")
            # SaveChanges() belongs AFTER the block, not inside it --
            # CurrentDepth is back to 0 here.
            project.SaveChanges()

        Example (``undoable=False``, explicit opt-out)::

            project.OpenProject("MyProject", writeEnabled=True,
                                 undoable=False)
            project.LexEntry.Create("word", "stem")
            # SaveChanges() here would raise FP_TransactionError: the
            # session-long envelope opened at OpenProject() holds
            # CurrentDepth at 1 for the whole session. CloseProject()
            # ends that envelope first, then saves.
            project.CloseProject()
        """
        if _IsAttachedView(self):
            raise FP_RuntimeError(_ATTACHED_VIEW_SAVE_REFUSAL)

        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        log = logging.getLogger(__name__)
        try:
            depth = self.CurrentDepth
        except Exception as e:
            # Fail OPEN (C21): catches Exception, not only
            # FP_ProjectError -- any depth-read exception falls through
            # to usm.Save() below; an unreadable depth never justifies
            # refusing a save that would otherwise succeed.
            # Measured-safe (cycle-8 QC code inspection, not live): if
            # self.project is absent, ObjectRepository() below shares
            # that dependency and raises before usm.Save() is reached.
            # Un-measured residual (C10 discipline): a depth-read
            # exception with ObjectRepository()/usm.Save() still
            # succeeding at depth > 0 would proceed blind into #243's
            # incident. No such state is known; not claimed safe, not
            # claimed a bug.
            log.warning(
                "SaveChanges: could not evaluate the issue #243 depth "
                "guard (CurrentDepth read raised %s: %s); proceeding to "
                "usm.Save() without it.",
                type(e).__name__, e,
            )
            depth = 0

        if depth > 0:
            if self._undoable:
                raise FP_TransactionError(
                    f"SaveChanges() refused: CurrentDepth is {depth} (a "
                    "unit of work is currently open). usm.Save() was NOT "
                    "attempted, so this refusal itself discarded "
                    "nothing. The enclosing UndoableOperation()/"
                    "Transaction() block owns the open unit of work; the "
                    "pending edit commits automatically when that block "
                    "exits normally. Call SaveChanges() AFTER the block, "
                    "not from inside it."
                )
            else:
                raise FP_TransactionError(
                    f"SaveChanges() refused: CurrentDepth is {depth} "
                    "(the session-long non-undoable envelope opened by "
                    "OpenProject(undoable=False) is still open). "
                    "usm.Save() was NOT attempted, so this refusal "
                    "itself discarded nothing -- your pending changes "
                    "are intact in memory and will be written to disk "
                    "by CloseProject(). Calling through here would "
                    "instead have discarded the session's pending "
                    "changes (measured 0/25 survivors when this guard "
                    "did not exist -- spec.md P-5/P-7/P-10-C). "
                    "Mid-session saving requires opening the project "
                    "with undoable=True instead."
                )

        usm = self.ObjectRepository(IUndoStackManager)
        usm.Save()

    def RefreshFromDisk(self):
        """
        Reconcile in-memory state with a foreign change and unblock auto-save.

        Wraps `IUndoStackManager.Refresh()`, obtained via the same
        `ObjectRepository(IUndoStackManager)` accessor used by `SaveChanges()`
        and `CloseProject()`.

        Rationale (issue A4, `specs/write-path-transactions/spec.md` D3):
        `UnitOfWorkService.cs:245` in liblcm refuses to auto-save while
        `m_pendingReconciliation` is non-null -- LCM's own comment is
        "don't auto-save until the user Refreshes." In FLEx a human clicks
        Edit > Refresh. Headless, nothing ever calls the equivalent, so once
        another client (typically FLEx itself, opened on the same project in
        shared mode) saves a change that this session must reconcile, saving
        is wedged for the remainder of the session -- in BOTH `undoable=True`
        and `undoable=False` modes, since the guard is in the shared
        `UnitOfWorkService`, not in either undo-stack implementation. Calling
        this method after a detected (or suspected) foreign change clears
        that pending-reconciliation state so subsequent saves proceed.

        Raises:
            FP_ReadOnlyError: If project is not write-enabled.

        Note on the write-enabled guard:
            The failure mode this method exists to fix -- auto-save
            permanently refusing to run -- is only possible while a
            write-enabled session holds an open UnitOfWork envelope
            (`BeginNonUndoableTask()`/`BeginUndoTask()`). A read-only
            session never saves, so there is nothing for a pending
            reconciliation to block. Guarding here matches `SaveChanges()`,
            which raises `FP_ReadOnlyError` for the same reason: the
            operation is meaningless outside a write-enabled session.

        Example::

            project.OpenProject("MyProject", writeEnabled=True,
                                 undoable=True)
            # ... FLEx (or another client) saves a conflicting change ...
            project.RefreshFromDisk()
            project.SaveChanges()  # No longer wedged

        Note on mode (issue #243, spec.md C21): the Example above requires
            ``undoable=True``. Under ``undoable=False`` the session-long
            envelope opened at ``OpenProject()`` holds ``CurrentDepth`` at
            1 for the whole session, so ``SaveChanges()`` always raises
            ``FP_TransactionError`` in that mode -- it cannot be called
            mid-session at all, reconciliation or not.
            ``CloseProject()`` ends that envelope before its own
            ``usm.Save()`` call, so it reaches ``usm.Save()`` at a legal
            depth; whether ``RefreshFromDisk()`` followed by
            ``CloseProject()`` fully clears a pending-reconciliation wedge
            under ``undoable=False`` has not been measured here and is
            not claimed.
        """
        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        usm = self.ObjectRepository(IUndoStackManager)
        usm.Refresh()

    def AbortSession(self):
        """
        Discard every uncommitted change in the currently open unit of work.

        Wraps liblcm's one real revert primitive, ``IActionHandler.Rollback(0)``
        (task A3, `specs/write-path-transactions/spec.md` section A3). It is
        coarse -- it reverts the *whole* open unit of work, not a selected
        subset -- but under ``undoable=False`` that unit is the entire session,
        which is exactly the granularity that mode's atomicity story needs and
        which was previously unreachable from flexicon.

        What it does NOT do: it cannot revert anything already written to
        disk -- data that was on disk when the session opened, or anything a
        prior ``CloseProject()`` committed. "Uncommitted" here means "still
        only in this process's cache".

        Under ``undoable=False`` that window is unusually wide, and for two
        reasons worth knowing. The session envelope holds the FSM in
        ``ProcessingDataChanges``, which blocks the auto-save timer outright
        (`UnitOfWorkService.cs:240`), so nothing is quietly committed behind
        your back between operations. For the same reason ``SaveChanges()``
        cannot be used to commit mid-session either: it reaches
        ``CheckReadyForCommit("Commit at wrong place.")``
        (`UnitOfWorkService.cs:304`), which requires ``ReadyForBeginTask``.
        The practical consequence is that in this mode essentially the whole
        session is abortable, right up to ``CloseProject()``.

        Mode-dependent behavior (read this before relying on it):

        * ``undoable=False`` (the legacy opt-out; you must ask for it
          explicitly since 4.4.0): this is the intended mode. The
          session-long ``BeginNonUndoableTask()`` opened at ``OpenProject()``
          is the open unit of work, so this rolls the session back to its
          state at open (or at the last commit) and then **reopens the
          envelope**, so the session stays usable and ``CloseProject()``'s
          matching ``EndNonUndoableTask()`` still has a task to end. See the
          O2 catch below for why reopening is not optional.
        * ``undoable=True``: rollback is already automatic and per-operation
          (``UndoableOperation()`` / ``_TransactionCM`` roll back their own
          block on exception), so there is no session-wide uncommitted state
          for this method to abort. Between operations nothing is open and
          this returns ``False``. Inside an open block it raises
          ``FP_TransactionError`` rather than rolling back -- see below.

        The O2 catch (`UndoStack.cs:705-724`, recorded in `spec.md` O2 and
        `reviews/cycle2-explore-liblcm-facts.md` F5c):

        1. ``Rollback(int nDepth)`` ignores ``nDepth`` entirely -- the
           parameter is documented "[Not used.]" -- so it always reverts the
           whole open unit. There is no partial rollback.
        2. It requires ``CurrentProcessingState == ProcessingDataChanges`` and
           otherwise throws ``InvalidOperationException("Rollback not
           supported in the current state.")``. ``CurrentDepth`` is exactly
           that state expressed as 1-or-0 (`UndoStack.cs:731-734`), so the
           ``CurrentDepth == 0`` check below is the precondition test, not a
           heuristic.
        3. On success it leaves the FSM in ``ReadyForBeginTask`` -- i.e. it
           **terminates** the open task rather than merely emptying it. In
           ``undoable=False`` that would silently end the session envelope,
           and ``CloseProject()`` would then call ``EndNonUndoableTask()``
           against a state that has no task to end. This method therefore
           reopens ``BeginNonUndoableTask()`` immediately, making the abort
           non-terminal in that mode.

        Why ``undoable=True`` refuses instead of rolling back: in that mode
        an open unit of work is always owned by an ``UndoableUnitOfWorkHelper``
        (there is no session envelope). Rolling back underneath it would leave
        that helper's ``Dispose()`` to call ``Rollback``/``EndUndoTask``
        against a FSM already back in ``ReadyForBeginTask``, raising a second
        exception from the ``with`` block's exit and masking whatever the
        caller was actually handling. Refusing loudly is the honest option;
        the correct tool inside a block is to let the exception propagate,
        which rolls that block back by design.

        Attached views refuse outright. On a project attached with
        ``FromOpenProject()`` the open unit of work is the HOST's -- a view
        is unconditionally ``_undoable = False``, so without a guard this
        method would take the ``undoable=False`` branch below and
        ``Rollback(0)`` the host's session-long envelope, discarding
        unsaved edits the host made before the module was ever called and
        then replacing that envelope with one this facade opened. Both are
        the host's to own (Invariant B), so the call is refused before any
        action-handler access.

        Returns:
            bool: True if a unit of work was open and was rolled back.
                False if nothing was open (nothing to abort) -- calling
                ``Rollback`` in that state would raise, so it is not called.

        Raises:
            FP_RuntimeError: If this is a view obtained from
                ``FromOpenProject()``. Raised before the write-enabled
                check, for the same reason as in ``SaveChanges()``: the
                refusal is about who owns the unit of work, and a
                read-only diagnosis would imply that a write-enabled host
                would make the call succeed, which it must not.
            FP_ReadOnlyError: If the project is not write-enabled.
            FP_TransactionError: If ``undoable=True`` and a unit of work is
                open (see above), or if the underlying LCM ``Rollback(0)``
                call fails unexpectedly.
            FP_ProjectError: If the ``undoable=False`` envelope could not be
                reopened after a successful rollback. The rollback itself has
                already taken effect at that point; the session is left
                without an open task and should be closed.

        Example::

            # NOTE the explicit undoable=False. Under the 4.4.0 default this
            # method has nothing session-wide to abort -- see the mode table
            # above -- and each Create() rolls itself back instead.
            project.OpenProject("MyProject", writeEnabled=True, undoable=False)
            try:
                for word, gloss in messy_input:
                    entry = project.LexEntry.Create(word, "stem")
                    project.Senses.Create(entry, gloss, "en")
            except Exception:
                project.AbortSession()   # discard the whole partial import
                raise
            else:
                # NOTE: not SaveChanges(). Under undoable=False the
                # session-long envelope keeps CurrentDepth at 1 for the
                # whole session (issue #243, spec.md C21), so
                # SaveChanges() always raises FP_TransactionError here.
                # CloseProject() ends that envelope first, then saves.
                project.CloseProject()

        See Also:
            Undo() - reverse one committed ``UndoableOperation``
                (``undoable=True`` only, in-process only).
            UndoableOperation() - per-operation rollback, the finer-grained
                and preferred mechanism once ``undoable=True`` is in use.
        """
        if _IsAttachedView(self):
            raise FP_RuntimeError(_ATTACHED_VIEW_ABORT_REFUSAL)

        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        log = logging.getLogger(__name__)
        action_handler = self.project.ActionHandlerAccessor

        # CurrentDepth is 1 iff CurrentProcessingState == ProcessingDataChanges
        # and 0 otherwise (UndoStack.cs:731-734) -- never 2+. It is therefore
        # the exact precondition Rollback checks at UndoStack.cs:712-713, so
        # this guard turns "would throw" into an honest False rather than
        # letting a raw InvalidOperationException escape.
        if action_handler.CurrentDepth == 0:
            log.debug("AbortSession(): no unit of work is open, nothing to abort")
            return False

        if self._undoable:
            # Depth > 0 in this mode means an UndoableUnitOfWorkHelper owns the
            # open unit (there is no session envelope here). See docstring.
            raise FP_TransactionError(
                "AbortSession() cannot roll back a unit of work opened by "
                "UndoableOperation()/_TransactionCM: rolling back underneath "
                "the owning UndoableUnitOfWorkHelper would make its Dispose() "
                "raise on exit and mask the original error. In undoable=True "
                "mode let the exception propagate out of the block instead -- "
                "that block rolls itself back."
            )

        try:
            # nDepth is "[Not used.]" in liblcm (UndoStack.cs:700); 0 is what
            # UnitOfWorkHelper.RollBackChanges() itself passes
            # (UnitOfWorkHelper.cs:135-138).
            action_handler.Rollback(0)
        except Exception as e:
            log.error(f"AbortSession() failed: {e}")
            raise FP_TransactionError(f"AbortSession() rollback failed: {e}")

        # The rollback left the FSM in ReadyForBeginTask (UndoStack.cs:724),
        # i.e. the session envelope opened at OpenProject() is gone. Reopen it
        # so this method is not terminal and CloseProject()'s matching
        # EndNonUndoableTask() still has a task to end. See the O2 catch.
        try:
            self.project.MainCacheAccessor.BeginNonUndoableTask()
        except System.InvalidOperationException as e:
            raise FP_ProjectError(
                "AbortSession(): the rollback succeeded but the non-undoable "
                f"session envelope could not be reopened ({e}). Uncommitted "
                "changes have been discarded and this session can no longer "
                "write; close it without saving."
            )

        log.debug("AbortSession(): rolled back and reopened the session envelope")
        return True

    def UndoableOperation(self, label):
        """
        Return a context manager for an undoable operation.

        Changes made within the block appear as a single named operation
        in FLEx's Ctrl+Z undo menu. The project MUST be opened with
        undoable=True for this to work.

        Args:
            label (str): Name shown in FLEx undo menu (e.g. "Add entry 'run'")

        Returns:
            _FLExUndoableOperation: Context manager

        Raises:
            FP_ReadOnlyError: If project is not write-enabled
            FP_TransactionError: If project was not opened with undoable=True

        Example::

            project = FLExProject()
            project.OpenProject("MyProject", writeEnabled=True, undoable=True)

            with project.UndoableOperation("Add entry 'run'"):
                entry = project.LexEntry.Create("run", "stem")
                project.Senses.Create(entry, "to move quickly", "en")

            # Now "Add entry 'run'" appears in FLEx Edit > Undo
            project.Undo()   # Ctrl+Z equivalent
            project.Redo()   # Ctrl+Y equivalent

        Note:
            Rollback-capable (issue #233, #236-for-undoable): this now
            delegates to ``_FLExUndoableOperation``, which constructs
            liblcm's own ``UndoableUnitOfWorkHelper`` directly (or joins an
            already-open one, via ``ActionHandlerAccessor.CurrentDepth``)
            instead of hand-rolling ``BeginUndoTask``/``EndUndoTask`` calls.
            If an exception is raised inside the block and this call was the
            one that opened the UnitOfWork, the mutations made inside it ARE
            rolled back -- ``UndoableUnitOfWorkHelper``'s ``RollBack`` flag
            defaults to True and is only cleared on a clean exit. If this
            call instead joined an already-open UnitOfWork (nested inside
            another ``UndoableOperation()`` or a ``_TransactionCM`` block),
            rollback authority belongs to whichever call opened it. See
            `specs/write-path-transactions/spec.md` B1.
        """
        from .undoable_operation import _FLExUndoableOperation

        return _FLExUndoableOperation(self, label)

    def _TransactionCM(self, label):
        """
        Internal: the mode-selecting transaction context manager, for the write
        methods that live on ``FLExProject`` itself.

        Identical in behavior to ``BaseOperations._TransactionCM`` -- see that
        docstring for the full Phase 1 / Phase 2 semantics, the nesting rules,
        and what each mode does and does not guarantee. It exists here too
        because a handful of write methods (``LexiconSetFieldText``,
        ``LexiconClearField``, ``LexiconSetListFieldMultiple``,
        ``LexiconDeleteObject``, ``LexiconSetComplexFormType``,
        ``LexiconAddComplexForm``, ``SetAudioPath``) are defined on this facade
        rather than on an Operations class, so they have no ``BaseOperations``
        to inherit it from. Without this they would be the only LCM mutators in
        the tree unable to use the standard bracket (decision D5,
        `specs/write-path-transactions/tasks.md` B2).

        ``_NestingAwareTransaction`` needs only ``_undoable``,
        ``Transaction(label)`` and ``project.ActionHandlerAccessor`` from the
        object it is handed, all of which this class provides directly -- so
        the same class serves both call sites with no special-casing.

        Args:
            label (str): Human-readable description, used for logging and, in
                Phase 2, as the FLEx undo-menu entry.

        Returns:
            A ``_NestingAwareTransaction`` context manager.
        """
        from .transaction import _NestingAwareTransaction

        return _NestingAwareTransaction(self, label)

    def Undo(self):
        """
        Undo the last UndoableOperation.

        Reverses the changes of the last operation added with UndoableOperation().
        Only valid when the project was opened with undoable=True.

        Scope -- IN-PROCESS ONLY (issue #235): liblcm's undo stack
        (``IActionHandler``, obtained here from
        ``LcmCache.ActionHandlerAccessor``) lives entirely in this process's
        RAM and holds live ``ICmObject`` references. Nothing serializes undo
        records into ``.fwdata``; a freshly opened ``LcmCache`` always starts
        at ``UndoableActionCount == 0``. There is no cross-process and no
        cross-session undo: closing and reopening the project -- even within
        the same script -- loses the entire stack. Cross-*session* reversal
        is a separate, still-open concern tracked at the wrapper layer
        (``flexicon/sync/engine.py``'s ``create_snapshot``/``Snapshot``
        stubs), not here.

        Returns:
            bool: True if undo succeeded, False if there was nothing to undo
                (``CanUndo()`` was False).

        Raises:
            FP_TransactionError: If project not opened with undoable=True,
                or if the underlying LCM ``Undo()`` call fails unexpectedly.

        Example::

            with project.UndoableOperation("Add entry"):
                project.LexEntry.Create("word", "stem")

            project.Undo()  # Removes the entry
        """
        if not self._undoable:
            raise FP_TransactionError(
                "Project must be opened with undoable=True to use Undo(). "
                f"Current project was opened with undoable=False."
            )

        action_handler = self.project.ActionHandlerAccessor

        if not action_handler.CanUndo():
            logging.getLogger(__name__).debug("Undo(): CanUndo() is False, nothing to undo")
            return False

        try:
            action_handler.Undo()
        except Exception as e:
            logging.getLogger(__name__).error(f"Undo() failed: {e}")
            raise FP_TransactionError(f"Undo() operation failed: {e}")

        logging.getLogger(__name__).debug("Undo() succeeded")
        return True

    def Redo(self):
        """
        Redo the last undone UndoableOperation.

        Re-applies a change reversed by Undo().
        Only valid when the project was opened with undoable=True.

        Scope -- IN-PROCESS ONLY (issue #235): the same RAM-only limitation
        documented on ``Undo()`` applies here. liblcm's redo stack lives
        entirely in this process's ``LcmCache.ActionHandlerAccessor``; there
        is no cross-process or cross-session redo, and a freshly opened
        project never has anything to redo.

        Returns:
            bool: True if redo succeeded, False if there was nothing to redo
                (``CanRedo()`` was False).

        Raises:
            FP_TransactionError: If project not opened with undoable=True,
                or if the underlying LCM ``Redo()`` call fails unexpectedly.

        Example::

            with project.UndoableOperation("Add entry"):
                project.LexEntry.Create("word", "stem")

            project.Undo()   # Removes the entry
            project.Redo()   # Restores the entry
        """
        if not self._undoable:
            raise FP_TransactionError(
                "Project must be opened with undoable=True to use Redo(). "
                f"Current project was opened with undoable=False."
            )

        action_handler = self.project.ActionHandlerAccessor

        if not action_handler.CanRedo():
            logging.getLogger(__name__).debug("Redo(): CanRedo() is False, nothing to redo")
            return False

        try:
            action_handler.Redo()
        except Exception as e:
            logging.getLogger(__name__).error(f"Redo() failed: {e}")
            raise FP_TransactionError(f"Redo() operation failed: {e}")

        logging.getLogger(__name__).debug("Redo() succeeded")
        return True

    # --- Advanced Operations ---

    @property
    def POS(self):
        """
        Access to Parts of Speech operations.

        Returns:
            POSOperations: Instance providing POS management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all parts of speech
            >>> for pos in project.POS.GetAll():
            ...     print(f"{project.POS.GetName(pos)} ({project.POS.GetAbbreviation(pos)})")
            >>> # Create a new POS
            >>> noun = project.POS.Create("Noun", "N")
            >>> # Find and update
            >>> verb = project.POS.Find("Verb")
            >>> if verb:
            ...     project.POS.SetAbbreviation(verb, "V")
        """
        if "_pos_ops" not in self.__dict__:
            from .Grammar.POSOperations import POSOperations

            self._pos_ops = POSOperations(self)
        return self._pos_ops

    @property
    def LexEntry(self):
        """
        Access to Lexical Entry operations.

        Returns:
            LexEntryOperations: Instance providing lexical entry management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all entries
            >>> for entry in project.LexEntry.GetAll():
            ...     print(project.LexEntry.GetHeadword(entry))
            >>> # Create a new entry
            >>> entry = project.LexEntry.Create("run", "stem")
            >>> # Add a sense
            >>> sense = project.LexEntry.AddSense(entry, "to move rapidly on foot")
            >>> # Set citation form
            >>> project.LexEntry.SetCitationForm(entry, "run")
        """
        if "_lexentry_ops" not in self.__dict__:
            from .Lexicon.LexEntryOperations import LexEntryOperations

            self._lexentry_ops = LexEntryOperations(self)
        return self._lexentry_ops

    @property
    def Texts(self):
        """
        Access to Text operations.

        Returns:
            TextOperations: Instance providing text management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a new text
            >>> text = project.Texts.Create("Genesis")
            >>> # List all texts
            >>> for t in project.Texts.GetAll():
            ...     print(project.Texts.GetName(t))
            >>> # Update text name
            >>> project.Texts.SetName(text, "Genesis Chapter 1")
        """
        if "_text_ops" not in self.__dict__:
            from .TextsWords.TextOperations import TextOperations

            self._text_ops = TextOperations(self)
        return self._text_ops

    @property
    def Wordforms(self):
        """
        Access to wordform operations (Work Stream 3 - MOST ACTIVE: 727+ commits in 2024).

        Returns:
            WfiWordformOperations: Instance providing wordform inventory management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Find or create wordform (most common pattern)
            >>> wf = project.Wordforms.FindOrCreate("hlauka")
            >>> # Get all analyses
            >>> for analysis in project.Wordforms.GetAnalyses(wf):
            ...     approved = project.WfiAnalyses.IsHumanApproved(analysis)
            ...     print(f"Analysis: {'approved' if approved else 'parser guess'}")
            >>> # Set approved analysis
            >>> if wf.AnalysesOC.Count > 0:
            ...     project.Wordforms.SetApprovedAnalysis(wf, wf.AnalysesOC[0])
        """
        if "_wordform_ops" not in self.__dict__:
            from .TextsWords.WordformOperations import WordformOperations as WfiWordformOperations

            self._wordform_ops = WfiWordformOperations(self)
        return self._wordform_ops

    @property
    def WfiAnalyses(self):
        """
        Access to wordform analysis operations (Work Stream 3).

        Returns:
            WfiAnalysisOperations: Instance providing wordform analysis management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get wordform and create analysis
            >>> wf = project.Wordforms.FindOrCreate("hlauka")
            >>> analysis = project.WfiAnalyses.Create(wf)
            >>> # Set category (part of speech)
            >>> verb = project.POS.Find("verb")
            >>> if verb:
            ...     project.WfiAnalyses.SetCategory(analysis, verb)
            >>> # Mark as human-approved
            >>> project.WfiAnalyses.ApproveAnalysis(analysis)
            >>> # Get morph bundles
            >>> bundles = project.WfiAnalyses.GetMorphBundles(analysis)
        """
        if "_wfianalysis_ops" not in self.__dict__:
            from .TextsWords.WfiAnalysisOperations import WfiAnalysisOperations

            self._wfianalysis_ops = WfiAnalysisOperations(self)
        return self._wfianalysis_ops

    @property
    def Paragraphs(self):
        """
        Access to paragraph operations.

        Returns:
            ParagraphOperations: Instance providing paragraph management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> text = list(project.Texts.GetAll())[0]
            >>> para = list(text.ContentsOA.ParagraphsOS)[0]
            >>> # Get text content
            >>> text_content = project.Paragraphs.GetText(para)
            >>> # Set text content
            >>> project.Paragraphs.SetText(para, "In the beginning...")
            >>> # Get segments
            >>> segments = project.Paragraphs.GetSegments(para)
            >>> print(f"{len(segments)} segments")
        """
        if "_paragraph_ops" not in self.__dict__:
            from .TextsWords.ParagraphOperations import ParagraphOperations

            self._paragraph_ops = ParagraphOperations(self)
        return self._paragraph_ops

    @property
    def Segments(self):
        """
        Access to segment operations.

        Returns:
            SegmentOperations: Instance providing segment management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all segments in a paragraph
            >>> para = project.Object(para_hvo)
            >>> for segment in project.Segments.GetAll(para):
            ...     baseline = project.Segments.GetBaselineText(segment)
            ...     print(baseline)
            >>> # Set translations
            >>> segment = list(project.Segments.GetAll(para))[0]
            >>> project.Segments.SetFreeTranslation(segment, "In the beginning...")
            >>> project.Segments.SetLiteralTranslation(segment, "In-the beginning...")
        """
        if "_segment_ops" not in self.__dict__:
            from .TextsWords.SegmentOperations import SegmentOperations

            self._segment_ops = SegmentOperations(self)
        return self._segment_ops

    @property
    def Phonemes(self):
        """
        Access to phoneme operations.

        Returns:
            PhonemeOperations: Instance providing phoneme management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all phonemes
            >>> for phoneme in project.Phonemes.GetAll():
            ...     repr = project.Phonemes.GetRepresentation(phoneme)
            ...     desc = project.Phonemes.GetDescription(phoneme)
            ...     print(f"{repr}: {desc}")
            >>> # Create a new phoneme
            >>> phoneme = project.Phonemes.Create("/p/")
            >>> project.Phonemes.SetDescription(phoneme, "voiceless bilabial stop")
            >>> # Add allophonic codes
            >>> project.Phonemes.AddCode(phoneme, "[p]")
            >>> project.Phonemes.AddCode(phoneme, "[pʰ]")
            >>> # Check phoneme type
            >>> if project.Phonemes.IsConsonant(phoneme):
            ...     print("Consonant phoneme")
        """
        if "_phoneme_ops" not in self.__dict__:
            from .Grammar.PhonemeOperations import PhonemeOperations

            self._phoneme_ops = PhonemeOperations(self)
        return self._phoneme_ops

    @property
    def NaturalClasses(self):
        """
        Access to natural class operations.

        Returns:
            NaturalClassOperations: Instance providing natural class management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all natural classes
            >>> for nc in project.NaturalClasses.GetAll():
            ...     name = project.NaturalClasses.GetName(nc)
            ...     print(f"Natural class: {name}")
            >>> # Create a new natural class
            >>> nc = project.NaturalClasses.Create("Voiced Stops")
            >>> # Add phonemes to the class
            >>> phoneme_b = project.Phonemes.Find("/b/")
            >>> project.NaturalClasses.AddPhoneme(nc, phoneme_b)
        """
        if "_naturalclass_ops" not in self.__dict__:
            from .Grammar.NaturalClassOperations import NaturalClassOperations

            self._naturalclass_ops = NaturalClassOperations(self)
        return self._naturalclass_ops

    @property
    def Environments(self):
        """
        Access to phonological environment operations.

        Returns:
            EnvironmentOperations: Instance providing environment management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all environments
            >>> for env in project.Environments.GetAll():
            ...     name = project.Environments.GetName(env)
            ...     repr = project.Environments.GetStringRepresentation(env)
            ...     print(f"{name}: {repr}")
            >>> # Create a new environment
            >>> env = project.Environments.Create("Between vowels", "V_V")
        """
        if "_environment_ops" not in self.__dict__:
            from .Grammar.EnvironmentOperations import EnvironmentOperations

            self._environment_ops = EnvironmentOperations(self)
        return self._environment_ops

    @property
    def Allomorphs(self):
        """
        Access to allomorph operations.

        Returns:
            AllomorphOperations: Instance providing allomorph management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all allomorphs for an entry
            >>> entry = project.LexiconGetEntry(0)
            >>> for allo in project.Allomorphs.GetAll(entry):
            ...     form = project.Allomorphs.GetForm(allo)
            ...     print(f"Allomorph: {form}")
            >>> # Create a new allomorph
            >>> allo = project.Allomorphs.Create(entry, "-ed")
        """
        if "_allomorph_ops" not in self.__dict__:
            from .Lexicon.AllomorphOperations import AllomorphOperations

            self._allomorph_ops = AllomorphOperations(self)
        return self._allomorph_ops

    @property
    def MorphRules(self):
        """
        Access to morphological rule operations.

        Returns:
            MorphRuleOperations: Instance providing morph rule management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all compound rules
            >>> for rule in project.MorphRules.GetAllCompoundRules():
            ...     name = project.MorphRules.GetName(rule)
            ...     print(f"{name} ({rule.ClassName})")
            >>> # Create a compound rule
            >>> rule = project.MorphRules.CreateCompoundRule("Noun-Noun Compound")
        """
        if "_morphrule_ops" not in self.__dict__:
            from .Grammar.MorphRuleOperations import MorphRuleOperations

            self._morphrule_ops = MorphRuleOperations(self)
        return self._morphrule_ops

    @property
    def InflectionFeatures(self):
        """
        Access to inflection feature operations.

        Returns:
            InflectionFeatureOperations: Instance providing inflection feature management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all inflection classes
            >>> for ic in project.InflectionFeatures.InflectionClassGetAll():
            ...     name = project.InflectionFeatures.InflectionClassGetName(ic)
            ...     print(f"Inflection class: {name}")
            >>> # Get all features
            >>> for feat in project.InflectionFeatures.FeatureGetAll():
            ...     name = feat.Name.BestAnalysisAlternative.Text
            ...     print(f"Feature: {name}")
        """
        if "_inflectionfeature_ops" not in self.__dict__:
            from .Grammar.InflectionFeatureOperations import InflectionFeatureOperations

            self._inflectionfeature_ops = InflectionFeatureOperations(self)
        return self._inflectionfeature_ops

    @property
    def Features(self):
        """
        Discoverability alias for InflectionFeatures.

        Inflection features (closed features with symbolic values like
        +/- gender, person 1/2/3, etc.) are owned by
        ``LangProject.MsFeatureSystemOA``. The full CRUD surface --
        ``Create``, ``CreateValue``, ``Find``, ``Exists``, ``MakeFeatStruc``,
        ``CreateClosedFeatureWithValues``, plus catalog import from MGA
        EticGlossList -- lives on ``project.InflectionFeatures``. This
        alias exists so callers thinking in FLEx UI terminology (the
        "Features" tab) can find the wrapper from either spelling.

        For phonological features (PhFeatureSystemOA, owned by phonemes
        and natural classes) see ``project.PhonFeatures``.

        Example:
            >>> # Equivalent calls:
            >>> project.Features.Create("gender", "gen")
            >>> project.InflectionFeatures.Create("gender", "gen")
            >>>
            >>> # One-shot for the very common case:
            >>> feature, values = project.Features.CreateClosedFeatureWithValues(
            ...     name="gender", abbreviation="gen",
            ...     values=[("masculine", "m"), ("feminine", "f"), ("neuter", "n")],
            ... )
        """
        return self.InflectionFeatures

    @property
    def GramCat(self):
        """
        Deprecated discoverability alias for POS.

        Returns:
            GramCatOperations: A distinct, lazily-cached deprecated
            subclass of ``POSOperations``. It **addresses the same list**
            as ``project.POS`` -- ``IPartOfSpeech`` in
            ``LangProject.PartsOfSpeechOA`` -- and inherits its
            behaviour, but it is *not* the same object:
            ``project.GramCat is project.POS`` is **False**.

        At list level, a "grammatical category" *is* a part of speech.
        The full CRUD surface -- ``GetAll``, ``Find``, ``Create``,
        ``AddSubcategory``, ``GetSubcategories``, ``GetParent``,
        ``Delete`` -- lives on ``project.POS``. This alias is retained
        only so callers thinking in FLEx UI terminology (Grammar >
        Categories) can find the wrapper from either spelling; new code
        should spell it ``project.POS``.

        Two things are deliberately *not* inherited transparently:

        - Constructing the alias emits a :class:`DeprecationWarning`.
          The instance is cached, so the warning fires once per project,
          not once per attribute access.
        - ``project.GramCat.Create(...)`` **always raises**
          :class:`FP_ParameterError`, before any write. The old
          ``Create(name, parent=None)`` signature is kept precisely so
          that a legacy caller gets that explanatory error -- naming
          ``project.POS.Create(name, abbreviation)`` for a top-level
          category and
          ``project.POS.AddSubcategory(parent, name, abbreviation)``
          for a subcategory -- instead of a bare ``TypeError`` about a
          missing ``abbreviation`` argument. That raising override is
          the migration signpost, which is why this property returns a
          ``GramCatOperations`` rather than ``self.POS`` (issue #276;
          see ``specs/276-gramcat-collection/spec.md`` section 4).

        Removal is scheduled for the v5.0.0 boundary, alongside the
        other deprecated compatibility surfaces.

        Three FLEx concepts wear confusingly similar names. They are
        different LCM classes, and only the first is a category
        (issue #276):

        - ``project.GramCat`` / ``project.POS`` -- the **category
          inventory** (FLEx: Grammar > Categories). Create, browse,
          nest and delete categories here.
        - ``project.Senses.GetGrammaticalInfo(sense)`` -- the sense's
          **MSA** (``ILexSense.MorphoSyntaxAnalysisRA``), which is what
          FLEx labels "Grammatical Info." That is a composite, not a
          kind of category: use
          ``project.Senses.GetPartOfSpeechObject(sense)`` for just the
          category behind it, and ``project.MSA.*`` to build one.
        - ``project.InflectionFeatures`` -- the feature side of that
          composite, including the feature-structure types in
          ``MsFeatureSystemOA.TypesOC`` via ``TypeFind`` /
          ``TypeCreate``. An ``IFsFeatStrucType`` is a structural
          template for feature structures; it is never a grammatical
          category.

        Example:
            >>> # Reads behave identically -- both address
            >>> # LangProject.PartsOfSpeechOA:
            >>> project.GramCat.Find("Verb")
            >>> project.POS.Find("Verb")
            >>>
            >>> # Browse the category inventory:
            >>> for pos in project.POS.GetAll():
            ...     print(project.POS.GetName(pos))
            >>>
            >>> # Writes must go through project.POS. Creating a category
            >>> # needs an abbreviation (it is what interlinear renders);
            >>> # nest with AddSubcategory:
            >>> verb = project.POS.Create("Verb", "v")
            >>> project.POS.AddSubcategory(verb, "Transitive Verb", "vt")
            >>>
            >>> # The deprecated spelling refuses, with a pointer:
            >>> # project.GramCat.Create("Transitive")
            >>> #   -> FP_ParameterError: GramCat.Create() has been
            >>> #      removed (issue #276) ... use
            >>> #      project.POS.Create(name, abbreviation)
        """
        if "_gramcat_ops" not in self.__dict__:
            from .Grammar.GramCatOperations import GramCatOperations

            self._gramcat_ops = GramCatOperations(self)
        return self._gramcat_ops

    @property
    def PhonRules(self):
        """
        Access to phonological rule operations.

        Returns:
            PhonologicalRuleOperations: Instance providing phonological rule management methods

        Example:
            >>> from flexicon import FLExProject, Seg, NC
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a phonological rule
            >>> rule = project.PhonRules.Create("Voicing Assimilation",
            ...     "Voiceless stops become voiced between vowels")
            >>> # Wire input, output, and contexts via WireRule (the composer)
            >>> phoneme_t = project.Phonemes.Find("/t/")
            >>> phoneme_d = project.Phonemes.Find("/d/")
            >>> vowels = project.NaturalClasses.Find("Vowels")
            >>> project.PhonRules.WireRule(rule,
            ...     input_pattern=[Seg(phoneme_t)],
            ...     output_change=[Seg(phoneme_d)],
            ...     left_context=[NC(vowels)],
            ...     right_context=[NC(vowels)],
            ... )
        """
        if "_phonrule_ops" not in self.__dict__:
            from .Grammar.PhonologicalRuleOperations import PhonologicalRuleOperations

            self._phonrule_ops = PhonologicalRuleOperations(self)
        return self._phonrule_ops

    @property
    def PhonFeatures(self):
        """
        Access to phonological feature operations.

        Returns:
            PhonFeatureOperations: Instance providing phonological feature
            and feature-value management methods, including catalog import
            from the MGA PhonFeatsEticGlossList.

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Bulk-import the standard MGA feature set
            >>> result = project.PhonFeatures.ImportCatalog()
            >>> print(f"Created {result.created_count} entries")
            >>> # Create a specific feature
            >>> cons = project.PhonFeatures.CreateFromCatalog("fPAConsonantal")
            >>> # Inspect its +/- values
            >>> for v in project.PhonFeatures.GetValues(cons):
            ...     print(project.PhonFeatures.GetAbbreviation(v))
        """
        if "_phonfeature_ops" not in self.__dict__:
            from .Grammar.PhonFeatureOperations import PhonFeatureOperations

            self._phonfeature_ops = PhonFeatureOperations(self)
        return self._phonfeature_ops

    @property
    def Strata(self):
        """
        Access to stratum operations.

        Strata are the ordered morphology/phonology layers owned by
        ``LangProject.MorphologicalDataOA.StrataOS`` and referenced by
        ``IMoInflAffixTemplate.StratumRA``, ``IMoDerivAffMsa.StratumRA``,
        ``IMoStemMsa.StratumRA``, ``IMoCompoundRule.StratumRA``, and
        ``IPhPhonologicalRule.StratumRA``.

        Returns:
            StratumOperations: Instance providing stratum management methods.

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Enumerate strata
            >>> for stratum in project.Strata.GetAll():
            ...     print(project.Strata.GetName(stratum))
            >>> # Create a new stratum
            >>> new_stratum = project.Strata.Create("Stem", abbreviation="stem")
            >>> # Round-trip syncable properties
            >>> props = project.Strata.GetSyncableProperties(new_stratum)
        """
        if "_stratum_ops" not in self.__dict__:
            from .Grammar.StratumOperations import StratumOperations

            self._stratum_ops = StratumOperations(self)
        return self._stratum_ops

    @property
    def Senses(self):
        """
        Access to lexical sense operations.

        Returns:
            LexSenseOperations: Instance providing sense management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all senses for an entry
            >>> entry = list(project.LexiconAllEntries())[0]
            >>> for sense in project.Senses.GetAll(entry):
            ...     gloss = project.Senses.GetGloss(sense)
            ...     print(f"Sense: {gloss}")
            >>> # Create a new sense
            >>> sense = project.Senses.Create(entry, "to run", "en")
            >>> # Set definition
            >>> project.Senses.SetDefinition(sense, "To move swiftly on foot")
            >>> # Add semantic domain
            >>> domains = project.GetAllSemanticDomains()  # default: recursive=True
            >>> if domains:
            ...     project.Senses.AddSemanticDomain(sense, domains[0])
        """
        if "_sense_ops" not in self.__dict__:
            from .Lexicon.LexSenseOperations import LexSenseOperations

            self._sense_ops = LexSenseOperations(self)
        return self._sense_ops

    @property
    def MSA(self):
        """
        Access to morphosyntactic-analysis (MSA) creation operations.

        Pairs with the reading wrapper in
        flexicon.code.Lexicon.morphosyntax_analysis and the iteration
        helper in msa_collection. Handles the four concrete MSA types
        (stem, derivational affix, inflectional affix, unclassified
        affix) and auto-attaches the new MSA to the supplied sense via
        sense.MorphoSyntaxAnalysisRA.

        Returns:
            MSAOperations: Instance providing MSA creation methods.

        Example:
            >>> entry = list(project.LexiconAllEntries())[0]
            >>> sense = entry.SensesOS[0]
            >>> verb_pos = project.POS.Find("Verb")
            >>> # Stem MSA with POS = Verb
            >>> project.MSA.CreateStem(sense, verb_pos)
            >>> # Derivational affix that turns nouns into verbs
            >>> n_pos = project.POS.Find("Noun")
            >>> v_pos = project.POS.Find("Verb")
            >>> project.MSA.CreateDerivAff(sense, from_pos=n_pos, to_pos=v_pos)
        """
        if "_msa_ops" not in self.__dict__:
            from .Lexicon.MSAOperations import MSAOperations

            self._msa_ops = MSAOperations(self)
        return self._msa_ops

    @property
    def Examples(self):
        """
        Access to example sentence operations.

        Returns:
            ExampleOperations: Instance providing example sentence management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get first entry and sense
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> # Get all examples
            >>> for example in project.Examples.GetAll(sense):
            ...     text = project.Examples.GetExample(example)
            ...     trans = project.Examples.GetTranslation(example)
            ...     print(f"{text} - {trans}")
            >>> # Create a new example
            >>> example = project.Examples.Create(sense, "The cat slept.")
            >>> project.Examples.SetTranslation(example, "Le chat a dormi.")
            >>> project.Examples.SetReference(example, "Corpus A:123")
        """
        if "_example_ops" not in self.__dict__:
            from .Lexicon.ExampleOperations import ExampleOperations

            self._example_ops = ExampleOperations(self)
        return self._example_ops

    @property
    def LexReferences(self):
        """
        Access to lexical reference and relation operations.

        Returns:
            LexReferenceOperations: Instance providing lexical reference management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all reference types
            >>> for ref_type in project.LexReferences.GetAllTypes():
            ...     name = project.LexReferences.GetTypeName(ref_type)
            ...     mapping = project.LexReferences.GetMappingType(ref_type)
            ...     print(f"{name}: {mapping}")
            >>> # Create a synonym relation
            >>> syn_type = project.LexReferences.FindType("Synonym")
            >>> if not syn_type:
            ...     syn_type = project.LexReferences.CreateType("Synonym", "Symmetric")
            >>> # Link two senses
            >>> entry1 = project.LexEntry.Find("run")
            >>> entry2 = project.LexEntry.Find("jog")
            >>> if entry1 and entry2:
            ...     sense1 = list(project.Senses.GetAll(entry1))[0]
            ...     sense2 = list(project.Senses.GetAll(entry2))[0]
            ...     ref = project.LexReferences.Create(syn_type, [sense1, sense2])
            >>> # Get all references for a sense
            >>> for ref in project.LexReferences.GetAll(sense1):
            ...     targets = project.LexReferences.GetTargets(ref)
            ...     print(f"Related to {len(targets)} items")
        """
        if "_lexref_ops" not in self.__dict__:
            from .Lexicon.LexReferenceOperations import LexReferenceOperations

            self._lexref_ops = LexReferenceOperations(self)
        return self._lexref_ops

    @property
    def ReversalIndexes(self):
        """
        Access to reversal index operations (Work Stream 3).

        Returns:
            ReversalIndexOperations: Instance providing reversal index management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create English reversal index
            >>> en_ws = project.WSHandle('en')
            >>> idx = project.ReversalIndexes.Create("English", en_ws)
            >>> # Find by writing system
            >>> idx = project.ReversalIndexes.FindByWritingSystem(en_ws)
            >>> # Get all entries in index
            >>> for entry in project.ReversalIndexes.GetEntries(idx):
            ...     form = project.ReversalEntries.GetForm(entry)
            ...     print(f"Reversal: {form}")
        """
        if "_reversalindex_ops" not in self.__dict__:
            from .Reversal.ReversalIndexOperations import ReversalIndexOperations

            self._reversalindex_ops = ReversalIndexOperations(self)
        return self._reversalindex_ops

    @property
    def ReversalEntries(self):
        """
        Access to reversal index entry operations (Work Stream 3).

        Returns:
            ReversalIndexEntryOperations: Instance providing reversal entry management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get reversal index
            >>> idx = project.ReversalIndexes.FindByWritingSystem('en')
            >>> # Create reversal entry
            >>> entry = project.ReversalEntries.Create(idx, "run")
            >>> # Link to lexical sense
            >>> lex_entry = project.LexEntry.Find("hlauka")
            >>> if lex_entry and lex_entry.SensesOS.Count > 0:
            ...     sense = lex_entry.SensesOS[0]
            ...     project.ReversalEntries.AddSense(entry, sense)
        """
        if "_reversalentry_ops" not in self.__dict__:
            from .Reversal.ReversalIndexEntryOperations import ReversalIndexEntryOperations

            self._reversalentry_ops = ReversalIndexEntryOperations(self)
        return self._reversalentry_ops

    @property
    def SemanticDomains(self):
        """
        Access to semantic domain operations.

        Returns:
            SemanticDomainOperations: Instance providing semantic domain management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all semantic domains
            >>> for domain in project.SemanticDomains.GetAll():
            ...     number = project.SemanticDomains.GetNumber(domain)
            ...     name = project.SemanticDomains.GetName(domain)
            ...     print(f"{number} - {name}")
            >>> # Find a specific domain
            >>> walk_domain = project.SemanticDomains.Find("7.2.1")
            >>> if walk_domain:
            ...     desc = project.SemanticDomains.GetDescription(walk_domain)
            ...     senses = project.SemanticDomains.GetSensesInDomain(walk_domain)
            ...     print(f"Domain has {len(senses)} senses")
            >>> # Create a custom domain
            >>> custom = project.SemanticDomains.Create("Technology", "900")
        """
        if "_semantic_domain_ops" not in self.__dict__:
            from .Lexicon.SemanticDomainOperations import SemanticDomainOperations

            self._semantic_domain_ops = SemanticDomainOperations(self)
        return self._semantic_domain_ops

    @property
    def Pronunciations(self):
        """
        Access to pronunciation operations.

        Returns:
            PronunciationOperations: Instance providing pronunciation management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all pronunciations for an entry
            >>> entry = list(project.LexiconAllEntries())[0]
            >>> for pron in project.Pronunciations.GetAll(entry):
            ...     ipa = project.Pronunciations.GetForm(pron, "en-fonipa")
            ...     print(f"IPA: {ipa}")
            >>> # Create a new pronunciation
            >>> pron = project.Pronunciations.Create(entry, "rʌn", "en-fonipa")
            >>> # Add audio file
            >>> project.Pronunciations.AddMediaFile(pron, "/path/to/audio.wav")
            >>> # Get media files
            >>> media = project.Pronunciations.GetMediaFiles(pron)
            >>> print(f"Audio files: {len(media)}")
        """
        if "_pronunciation_ops" not in self.__dict__:
            from .Lexicon.PronunciationOperations import PronunciationOperations

            self._pronunciation_ops = PronunciationOperations(self)
        return self._pronunciation_ops

    @property
    def Variants(self):
        """
        Access to variant form operations.

        Returns:
            VariantOperations: Instance providing variant management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all variant types
            >>> for vtype in project.Variants.GetAllTypes():
            ...     name = project.Variants.GetTypeName(vtype)
            ...     print(f"Variant type: {name}")
            >>> # Find a specific variant type
            >>> spelling_type = project.Variants.FindType("Spelling Variant")
            >>> # Create a variant
            >>> entry = project.LexEntry.Find("color")
            >>> variant = project.Variants.Create(entry, "colour", spelling_type)
            >>> # Get all variants for an entry
            >>> for var in project.Variants.GetAll(entry):
            ...     form = project.Variants.GetForm(var)
            ...     vtype = project.Variants.GetType(var)
            ...     print(f"Variant: {form}")
            >>> # For irregularly inflected forms
            >>> go_entry = project.LexEntry.Find("go")
            >>> went_entry = project.LexEntry.Find("went")
            >>> irregular_type = project.Variants.FindType("Irregularly Inflected Form")
            >>> variant_ref = project.Variants.Create(went_entry, "went", irregular_type)
            >>> project.Variants.AddComponentLexeme(variant_ref, go_entry)
        """
        if "_variant_ops" not in self.__dict__:
            from .Lexicon.VariantOperations import VariantOperations

            self._variant_ops = VariantOperations(self)
        return self._variant_ops

    @property
    def Etymology(self):
        """
        Access to etymology operations.

        Returns:
            EtymologyOperations: Instance providing etymology tracking methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get an entry
            >>> entry = project.LexEntry.Find("telephone")
            >>> # Create etymology for compound word components
            >>> etym1 = project.Etymology.Create(entry, "Ancient Greek", "τηλε (tele)", "far, distant")
            >>> project.Etymology.SetComment(etym1, "Combining form from Greek τῆλε")
            >>> etym2 = project.Etymology.Create(entry, "Ancient Greek", "φωνή (phōnē)", "sound, voice")
            >>> # Query etymologies
            >>> for etym in project.Etymology.GetAll(entry):
            ...     source = project.Etymology.GetSource(etym)
            ...     form = project.Etymology.GetForm(etym)
            ...     gloss = project.Etymology.GetGloss(etym)
            ...     print(f"{source}: {form} ({gloss})")
        """
        if "_etymology_ops" not in self.__dict__:
            from .Lexicon.EtymologyOperations import EtymologyOperations

            self._etymology_ops = EtymologyOperations(self)
        return self._etymology_ops

    @property
    def PossibilityLists(self):
        """
        Access to generic possibility list operations.

        Returns:
            PossibilityListOperations: Instance providing possibility list management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all possibility lists in the project
            >>> for poss_list in project.PossibilityLists.GetAllLists():
            ...     name = project.PossibilityLists.GetListName(poss_list)
            ...     items = project.PossibilityLists.GetItems(poss_list)
            ...     print(f"{name}: {len(items)} items")
            Semantic Domains: 1435 items
            Parts of Speech: 45 items
            Text Genres: 12 items
            ...
            >>> # Work with a specific list
            >>> genre_list = project.PossibilityLists.FindList("Text Genres")
            >>> if genre_list:
            ...     # Get all items
            ...     for item in project.PossibilityLists.GetItems(genre_list):
            ...         name = project.PossibilityLists.GetItemName(item)
            ...         depth = project.PossibilityLists.GetDepth(item)
            ...         print(f"{'  ' * depth}{name}")
            ...     # Create a new genre
            ...     narrative = project.PossibilityLists.CreateItem(
            ...         genre_list, "Narrative", "en")
            ...     # Create a sub-genre
            ...     folktale = project.PossibilityLists.CreateItem(
            ...         genre_list, "Folktale", "en", parent=narrative)
            ...     # Move items in hierarchy
            ...     project.PossibilityLists.MoveItem(folktale, None)  # Move to top
        """
        if "_possibilitylist_ops" not in self.__dict__:
            from .Lists.PossibilityListOperations import PossibilityListOperations

            self._possibilitylist_ops = PossibilityListOperations(self)
        return self._possibilitylist_ops

    @property
    def LocalizedLists(self):
        """
        Access to localized possibility-list translation-pack imports.

        Localized lists merge translated Name/Abbreviation alternatives
        onto canonical possibility-list items (SemanticDomains,
        AnthroList, DomainTypes, ...) by GUID. Translation packs ship
        at ``<FWCodeDir>/Templates/LocalizedLists-<lang>.zip``.

        Order matters: call after the relevant ``*Operations
        .ImportCatalog`` (e.g. ``project.SemanticDomains.ImportCatalog``)
        has seeded canonical items. Without canonical items present,
        the merger has nothing to land on.

        Returns:
            LocalizedListsOperations: Instance providing single-WS
            ``Import(code)`` and project-wide
            ``ImportForAllAnalysisWritingSystems()``.

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> project.SemanticDomains.ImportCatalog()
            >>> # Single WS:
            >>> project.LocalizedLists.Import("fr")
            >>> # Or fan out across every enabled analysis WS:
            >>> result = project.LocalizedLists.ImportForAllAnalysisWritingSystems()
            >>> print(result.imported)
            >>> for code, reason in result.skipped:
            ...     print(f"  skipped {code}: {reason}")
        """
        if "_localizedlists_ops" not in self.__dict__:
            from .Lists.LocalizedListsOperations import LocalizedListsOperations

            self._localizedlists_ops = LocalizedListsOperations(self)
        return self._localizedlists_ops

    @property
    def CustomFields(self):
        """
        Access to custom field operations.

        Returns:
            CustomFieldOperations: Instance providing custom field management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all custom fields for entries
            >>> entry_fields = project.CustomFields.GetAllFields("LexEntry")
            >>> for field_id, label in entry_fields:
            ...     print(f"Field: {label} (ID: {field_id})")
            >>> # Find a specific field
            >>> field_id = project.CustomFields.FindField("LexEntry", "Etymology Source")
            >>> # Get and set field values
            >>> entry = project.LexEntry.Find("run")
            >>> if field_id:
            ...     value = project.CustomFields.GetValue(entry, "Etymology Source")
            ...     print(f"Current value: {value}")
            ...     project.CustomFields.SetValue(entry, "Etymology Source", "Latin currere")
            >>> # Work with list fields
            >>> sense = entry.SensesOS[0]
            >>> regions = project.CustomFields.GetListValues(sense, "Regions")
            >>> project.CustomFields.AddListValue(sense, "Regions", "North")
        """
        if "_customfield_ops" not in self.__dict__:
            from .System.CustomFieldOperations import CustomFieldOperations

            self._customfield_ops = CustomFieldOperations(self)
        return self._customfield_ops

    @property
    def WritingSystems(self):
        """
        Access to writing system operations.

        Returns:
            WritingSystemOperations: Instance providing writing system management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all writing systems
            >>> for ws in project.WritingSystems.GetAll():
            ...     name = project.WritingSystems.GetDisplayName(ws)
            ...     tag = project.WritingSystems.GetLanguageTag(ws)
            ...     print(f"{name} ({tag})")
            >>> # Configure a writing system
            >>> ws = list(project.WritingSystems.GetVernacular())[0]
            >>> project.WritingSystems.SetFontName(ws, "Charis SIL")
            >>> project.WritingSystems.SetFontSize(ws, 14)
            >>> # Set RTL for Arabic
            >>> if project.WritingSystems.Exists("ar"):
            ...     project.WritingSystems.SetRightToLeft("ar", True)
        """
        if "_writingsystem_ops" not in self.__dict__:
            from .System.WritingSystemOperations import WritingSystemOperations

            self._writingsystem_ops = WritingSystemOperations(self)
        return self._writingsystem_ops

    @property
    def WfiGlosses(self):
        """
        Access to wordform gloss operations (Work Stream 3).

        Returns:
            WfiGlossOperations: Instance providing wordform gloss management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get analysis and create gloss
            >>> analysis = project.WfiAnalyses.Create(wordform)
            >>> gloss = project.WfiGlosses.Create(analysis, "run", project.WSHandle('en'))
            >>> # Mark the analysis as human-approved (glosses have no
            >>> # approval concept of their own -- it lives on the analysis)
            >>> project.WfiAnalyses.ApproveAnalysis(analysis)
            >>> # Get all glosses
            >>> for g in project.WfiGlosses.GetAll(analysis):
            ...         form = project.WfiGlosses.GetForm(g, "en")
            ...         print(f"Gloss: {form}")
        """
        if "_wfigloss_ops" not in self.__dict__:
            from .TextsWords.WfiGlossOperations import WfiGlossOperations

            self._wfigloss_ops = WfiGlossOperations(self)
        return self._wfigloss_ops

    @property
    def WfiMorphBundles(self):
        """
        Access to wordform morpheme bundle operations (Work Stream 3).

        Returns:
            WfiMorphBundleOperations: Instance providing morpheme bundle management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create morpheme bundles for morphological breakdown
            >>> analysis = project.WfiAnalyses.Create(wordform)
            >>> stem = project.WfiMorphBundles.Create(analysis, "hlauk-")
            >>> suffix = project.WfiMorphBundles.Create(analysis, "-a")
            >>> # Link to lexical entries
            >>> stem_entry = project.LexEntry.Find("hlauk")
            >>> if stem_entry and stem_entry.SensesOS.Count > 0:
            ...     project.WfiMorphBundles.SetSense(stem, stem_entry.SensesOS[0])
            >>> # Morph type lives on the allomorph, not the bundle --
            >>> # WfiMorphBundles.SetMorphType is a retired stub that always
            >>> # raises. Link the bundle to the entry's already-typed
            >>> # allomorph instead.
            >>> stem_allomorphs = list(project.Allomorphs.GetAll(stem_entry)) if stem_entry else []
            >>> if stem_allomorphs:
            ...     project.WfiMorphBundles.SetMorph(stem, stem_allomorphs[0])
        """
        if "_wfimorphbundle_ops" not in self.__dict__:
            from .TextsWords.WfiMorphBundleOperations import WfiMorphBundleOperations

            self._wfimorphbundle_ops = WfiMorphBundleOperations(self)
        return self._wfimorphbundle_ops

    @property
    def Media(self):
        """
        Access to media file operations.

        Returns:
            MediaOperations: Instance providing media file management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all media files
            >>> for media in project.Media.GetAll():
            ...     path = project.Media.GetInternalPath(media)
            ...     mtype = project.Media.GetMediaType(media)
            ...     print(f"{path} ({mtype})")
            >>> # Add a media file
            >>> media = project.Media.Create("/path/to/audio.wav", "My Recording")
            >>> # Copy file to project
            >>> project.Media.CopyToProject(media)
            >>> # Find orphaned media
            >>> orphans = project.Media.GetOrphanedMedia()
            >>> print(f"Found {len(orphans)} orphaned files")
        """
        if "_media_ops" not in self.__dict__:
            from .Shared.MediaOperations import MediaOperations

            self._media_ops = MediaOperations(self)
        return self._media_ops

    @property
    def Notes(self):
        """
        Access to note and annotation operations.

        Returns:
            NoteOperations: Instance providing note management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a note on an entry
            >>> entry = project.LexEntry.Find("run")
            >>> note = project.Notes.Create(entry, "Check etymology", "en")
            >>> # Add a reply
            >>> reply = project.Notes.AddReply(note, "Verified - from Latin currere", "en")
            >>> # Get all notes for an object
            >>> for n in project.Notes.GetAll(entry):
            ...     content = project.Notes.GetContent(n, "en")
            ...     replies = project.Notes.GetReplies(n)
            ...     print(f"Note: {content} ({len(replies)} replies)")
        """
        if "_note_ops" not in self.__dict__:
            from .Notebook.NoteOperations import NoteOperations

            self._note_ops = NoteOperations(self)
        return self._note_ops

    @property
    def Filters(self):
        """
        Access to filter and query operations.

        Returns:
            FilterOperations: Instance providing filter management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a filter for verbs ("LexEntry" is FilterTypes.LEXENTRY)
            >>> filter_obj = project.Filters.Create(
            ...     "Verbs", "LexEntry", {"pos": "verb"}
            ... )
            >>> # Apply the filter to a collection of entries
            >>> entries = list(project.LexEntry.GetAll())
            >>> results = project.Filters.ApplyFilter(filter_obj, entries)
            >>> print(f"Found {len(results)} verbs")
            >>> # Export filter to a file
            >>> project.Filters.ExportFilter(filter_obj, "/path/to/verbs.json")
        """
        if "_filter_ops" not in self.__dict__:
            from .Shared.FilterOperations import FilterOperations

            self._filter_ops = FilterOperations(self)
        return self._filter_ops

    @property
    def Discourse(self):
        """
        Access to discourse chart operations.

        Returns:
            DiscourseOperations: Instance providing discourse chart management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get a text
            >>> text = list(project.Texts.GetAll())[0]
            >>> # Create a discourse chart
            >>> chart = project.Discourse.CreateChart(text, "Constituent Chart")
            >>> # Add rows
            >>> row1 = project.Discourse.AddRow(chart)
            >>> # Get all charts
            >>> for c in project.Discourse.GetAllCharts(text):
            ...     name = project.Discourse.GetChartName(c, "en")
            ...     rows = project.Discourse.GetRows(c)
            ...     print(f"Chart: {name} ({len(rows)} rows)")
        """
        if "_discourse_ops" not in self.__dict__:
            from .TextsWords.DiscourseOperations import DiscourseOperations

            self._discourse_ops = DiscourseOperations(self)
        return self._discourse_ops

    @property
    def Person(self):
        """
        Access to person operations for managing consultants, speakers, and researchers.

        Returns:
            PersonOperations: Instance providing person management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a person
            >>> consultant = project.Person.Create("Maria Garcia", "en")
            >>> # Set properties
            >>> project.Person.SetGender(consultant, "Female", "en")
            >>> project.Person.SetEmail(consultant, "maria@example.com", "en")
            >>> project.Person.SetEducation(consultant, "PhD Linguistics", "en")
            >>> # Add residence
            >>> location = project.Location.Find("Lima")
            >>> if location:
            ...     project.Person.AddResidence(consultant, location)
            >>> # Get all people
            >>> for person in project.Person.GetAll():
            ...     name = project.Person.GetName(person)
            ...     email = project.Person.GetEmail(person)
            ...     print(f"{name}: {email}")
        """
        if "_person_ops" not in self.__dict__:
            from .Notebook.PersonOperations import PersonOperations

            self._person_ops = PersonOperations(self)
        return self._person_ops

    @property
    def Location(self):
        """
        Access to location operations for managing geographic places.

        Returns:
            LocationOperations: Instance providing location management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a location
            >>> region = project.Location.Create("Cusco Region", "en", alias="CUS")
            >>> project.Location.SetCoordinates(region, -13.5319, -71.9675)
            >>> project.Location.SetElevation(region, 3400)
            >>> # Create sublocation
            >>> city = project.Location.CreateSublocation(region, "Cusco", "en")
            >>> project.Location.SetDescription(city, "Historic capital of Inca Empire", "en")
            >>> # Find nearby locations
            >>> nearby = project.Location.GetNearby(city, radius_km=100)
            >>> for loc in nearby:
            ...     name = project.Location.GetName(loc)
            ...     coords = project.Location.GetCoordinates(loc)
            ...     print(f"{name}: {coords}")
        """
        if "_location_ops" not in self.__dict__:
            from .Notebook.LocationOperations import LocationOperations

            self._location_ops = LocationOperations(self)
        return self._location_ops

    @property
    def Anthropology(self):
        """
        Access to anthropology operations for managing cultural/ethnographic data.

        Returns:
            AnthropologyOperations: Instance providing anthropology management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create anthropology items
            >>> marriage = project.Anthropology.Create(
            ...     "Marriage Customs", "MAR", "586")
            >>> project.Anthropology.SetDescription(marriage,
            ...     "Traditional marriage practices and ceremonies", "en")
            >>> # Create subitem
            >>> wedding = project.Anthropology.CreateSubitem(
            ...     marriage, "Wedding Ceremony", "WED", "586.1")
            >>> # Link to text
            >>> text = project.Texts.Find("Wedding Story")
            >>> if text:
            ...     project.Anthropology.AddText(marriage, text)
            >>> # Query items
            >>> items = project.Anthropology.GetItemsForText(text)
            >>> for item in items:
            ...     name = project.Anthropology.GetName(item)
            ...     code = project.Anthropology.GetAnthroCode(item)
            ...     print(f"{code}: {name}")
        """
        if "_anthropology_ops" not in self.__dict__:
            from .Notebook.AnthropologyOperations import AnthropologyOperations

            self._anthropology_ops = AnthropologyOperations(self)
        return self._anthropology_ops

    @property
    def ProjectSettings(self):
        """
        Access to project settings operations.

        Returns:
            ProjectSettingsOperations: Instance providing project configuration methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get project info
            >>> name = project.ProjectSettings.GetProjectName()
            >>> desc = project.ProjectSettings.GetDescription("en")
            >>> # Configure writing systems
            >>> vern_wss = project.ProjectSettings.GetVernacularWSs()
            >>> project.ProjectSettings.SetDefaultVernacular("qaa-x-spec")
            >>> # Set default font
            >>> project.ProjectSettings.SetDefaultFont("en", "Charis SIL")
            >>> project.ProjectSettings.SetDefaultFontSize("en", 14)
        """
        if "_projectsettings_ops" not in self.__dict__:
            from .System.ProjectSettingsOperations import ProjectSettingsOperations

            self._projectsettings_ops = ProjectSettingsOperations(self)
        return self._projectsettings_ops

    @property
    def Publications(self):
        """
        Access to publication operations.

        Returns:
            PublicationOperations: Instance providing publication management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create publication
            >>> pub = project.Publications.Create("Dictionary", "en")
            >>> project.Publications.SetPageWidth(pub, 8.5)
            >>> project.Publications.SetPageHeight(pub, 11)
            >>> # Get all publications
            >>> for p in project.Publications.GetAll():
            ...     name = project.Publications.GetName(p)
            ...     is_default = project.Publications.GetIsDefault(p)
            ...     print(f"{name} (default: {is_default})")
        """
        if "_publication_ops" not in self.__dict__:
            from .Lists.PublicationOperations import PublicationOperations

            self._publication_ops = PublicationOperations(self)
        return self._publication_ops

    @property
    def Agents(self):
        """
        Access to agent operations.

        Returns:
            AgentOperations: Instance providing agent management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create human agent
            >>> person = project.Person.Create("John Smith", "en")
            >>> agent = project.Agents.Create("John Smith")
            >>> project.Agents.SetHuman(agent, person)
            >>> # Create parser agent (an agent is a "parser" simply by not
            >>> # calling SetHuman on it)
            >>> parser = project.Agents.Create("MyParser")
            >>> project.Agents.SetVersion(parser, "1.0.0")
            >>> # Query agents
            >>> for a in project.Agents.GetAll():
            ...     name = project.Agents.GetName(a)
            ...     if project.Agents.IsHuman(a):
            ...         print(f"Human: {name}")
            ...     else:
            ...         version = project.Agents.GetVersion(a)
            ...         print(f"Parser: {name} v{version}")
        """
        if "_agent_ops" not in self.__dict__:
            from .Lists.AgentOperations import AgentOperations

            self._agent_ops = AgentOperations(self)
        return self._agent_ops

    @property
    def Confidence(self):
        """
        Access to confidence level operations.

        Returns:
            ConfidenceOperations: Instance providing confidence management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all confidence levels
            >>> for level in project.Confidence.GetAll():
            ...     name = project.Confidence.GetName(level)
            ...     print(f"Confidence: {name}")
            >>> # Create custom confidence level
            >>> verified = project.Confidence.Create("Speaker Verified", "en")
            >>> project.Confidence.SetDescription(verified,
            ...     "Confirmed by native speaker", "en")
        """
        if "_confidence_ops" not in self.__dict__:
            from .Lists.ConfidenceOperations import ConfidenceOperations

            self._confidence_ops = ConfidenceOperations(self)
        return self._confidence_ops

    @property
    def Overlays(self):
        """
        Access to discourse overlay operations.

        Returns:
            OverlayOperations: Instance providing overlay management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get a chart
            >>> text = list(project.Texts.GetAll())[0]
            >>> chart = project.Discourse.CreateChart(text, "Chart")
            >>> # NOTE: OverlayOperations.Create() is currently broken -- it
            >>> # inherits PossibilityItemOperations.Create(), but
            >>> # OverlayOperations._get_list_object() always returns None
            >>> # (overlays are chart-scoped, no project-wide list), so this
            >>> # call always raises FP_ParameterError. See flexicon issue #309.
            >>> # overlay = project.Overlays.Create("Temporal")
            >>> # project.Overlays.SetVisible(overlay, True)
            >>> # for o in project.Overlays.GetVisibleOverlays(chart):
            >>> #     name = project.Overlays.GetName(o)
            >>> #     print(f"Overlay: {name}")
        """
        if "_overlay_ops" not in self.__dict__:
            from .Lists.OverlayOperations import OverlayOperations

            self._overlay_ops = OverlayOperations(self)
        return self._overlay_ops

    @property
    def TranslationTypes(self):
        """
        Access to translation type operations.

        Returns:
            TranslationTypeOperations: Instance providing translation type methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get predefined types
            >>> free = project.TranslationTypes.GetFreeTranslationType()
            >>> literal = project.TranslationTypes.GetLiteralTranslationType()
            >>> # Create custom type
            >>> gloss = project.TranslationTypes.Create("Interlinear Gloss", "en")
            >>> project.TranslationTypes.SetAbbreviation(gloss, "IG", "en")
            >>> # Get all types
            >>> for t in project.TranslationTypes.GetAll():
            ...     name = project.TranslationTypes.GetName(t)
            ...     abbr = project.TranslationTypes.GetAbbreviation(t)
            ...     print(f"{name} ({abbr})")
        """
        if "_translationtype_ops" not in self.__dict__:
            from .Lists.TranslationTypeOperations import TranslationTypeOperations

            self._translationtype_ops = TranslationTypeOperations(self)
        return self._translationtype_ops

    @property
    def AnnotationDefs(self):
        """
        Access to annotation definition operations.

        Returns:
            AnnotationDefOperations: Instance providing annotation definition methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all annotation definitions
            >>> for defn in project.AnnotationDefs.GetAll():
            ...     name = project.AnnotationDefs.GetName(defn)
            ...     can_create = project.AnnotationDefs.GetUserCanCreate(defn)
            ...     print(f"{name} (user-creatable: {can_create})")
            >>> # Create custom annotation type
            >>> note_type = project.AnnotationDefs.Create("Field Note", "en")
            >>> project.AnnotationDefs.SetUserCanCreate(note_type, True)
        """
        if "_annotationdef_ops" not in self.__dict__:
            from .System.AnnotationDefOperations import AnnotationDefOperations

            self._annotationdef_ops = AnnotationDefOperations(self)
        return self._annotationdef_ops

    @property
    def Checks(self):
        """
        Access to consistency check operations.

        Returns:
            CheckOperations: Instance providing check management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create check type
            >>> check = project.Checks.CreateCheckType("Missing Gloss", "en")
            >>> project.Checks.SetDescription(check,
            ...     "Find senses without glosses", "en")
            >>> # Run check
            >>> results = project.Checks.RunCheck(check)
            >>> print(f"Errors: {results['errors']}")
            >>> print(f"Warnings: {results['warnings']}")
            >>> # Get enabled checks
            >>> for c in project.Checks.GetEnabledChecks():
            ...     name = project.Checks.GetName(c)
            ...     status = project.Checks.GetCheckStatus(c)
            ...     print(f"{name}: {status}")
        """
        if "_check_ops" not in self.__dict__:
            from .System.CheckOperations import CheckOperations

            self._check_ops = CheckOperations(self)
        return self._check_ops

    @property
    def DataNotebook(self):
        """
        Access to data notebook operations for research notes and observations.

        Returns:
            DataNotebookOperations: Instance providing notebook record management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create notebook record
            >>> record = project.DataNotebook.Create(
            ...     "Field Interview", "Notes from interview with speaker")
            >>> project.DataNotebook.SetDateOfEvent(record, "2024-01-15")
            >>> # Link researcher
            >>> researcher = project.Person.Find("John Smith")
            >>> project.DataNotebook.AddResearcher(record, researcher)
            >>> # Create sub-record
            >>> sub = project.DataNotebook.CreateSubRecord(
            ...     record, "Kinship Terms", "Analysis of family terms")
            >>> # Set status
            >>> project.DataNotebook.SetStatus(record, "Reviewed")
            >>> # Query records
            >>> for rec in project.DataNotebook.FindByResearcher(researcher):
            ...     title = project.DataNotebook.GetTitle(rec)
            ...     date = project.DataNotebook.GetDateOfEvent(rec)
            ...     print(f"{title} ({date})")
        """
        if "_datanotebook_ops" not in self.__dict__:
            from .Notebook.DataNotebookOperations import DataNotebookOperations

            self._datanotebook_ops = DataNotebookOperations(self)
        return self._datanotebook_ops

    @property
    def ConstCharts(self):
        """
        Access to constituent chart operations for discourse analysis.

        Returns:
            ConstChartOperations: Instance providing constituent chart management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a constituent chart
            >>> chart = project.ConstCharts.Create("Genesis 1 Analysis")
            >>> # Set properties
            >>> project.ConstCharts.SetName(chart, "Genesis 1 - Updated")
            >>> # Get all charts
            >>> for chart in project.ConstCharts.GetAll():
            ...     name = project.ConstCharts.GetName(chart)
            ...     rows = project.ConstCharts.GetRows(chart)
            ...     print(f"Chart: {name} ({len(rows)} rows)")
        """
        if "_constchart_ops" not in self.__dict__:
            from .Discourse.ConstChartOperations import ConstChartOperations

            self._constchart_ops = ConstChartOperations(self)
        return self._constchart_ops

    @property
    def ConstChartRows(self):
        """
        Access to constituent chart row operations for discourse analysis.

        Returns:
            ConstChartRowOperations: Instance providing chart row management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get a chart
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> # Create a row
            >>> row = project.ConstChartRows.Create(chart, label="Verse 1")
            >>> # Set properties
            >>> project.ConstChartRows.SetLabel(row, "Verse 1a")
            >>> project.ConstChartRows.SetNotes(row, "Complex structure")
            >>> # Get all rows
            >>> for row in project.ConstChartRows.GetAll(chart):
            ...     label = project.ConstChartRows.GetLabel(row)
            ...     print(f"Row: {label}")
        """
        if "_constchartrow_ops" not in self.__dict__:
            from .Discourse.ConstChartRowOperations import ConstChartRowOperations

            self._constchartrow_ops = ConstChartRowOperations(self)
        return self._constchartrow_ops

    @property
    def ConstChartWordGroups(self):
        """
        Access to word group operations for constituent chart rows.

        Returns:
            ConstChartWordGroupOperations: Instance providing word group management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get text segments
            >>> text = project.Texts.Find("Genesis 1")
            >>> para = text.ContentsOA.ParagraphsOS[0]
            >>> segments = list(para.SegmentsOS)
            >>> # Create word group
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> wg = project.ConstChartWordGroups.Create(row, segments[0], segments[2])
            >>> # Get all word groups
            >>> for wg in project.ConstChartWordGroups.GetAll(row):
            ...     begin = project.ConstChartWordGroups.GetBeginSegment(wg)
            ...     print(f"Word group starts at segment {begin.Hvo}")
        """
        if "_constchartwordgroup_ops" not in self.__dict__:
            from .Discourse.ConstChartWordGroupOperations import ConstChartWordGroupOperations

            self._constchartwordgroup_ops = ConstChartWordGroupOperations(self)
        return self._constchartwordgroup_ops

    @property
    def ConstChartMovedText(self):
        """
        Access to moved text marker operations for constituent charts.

        Returns:
            ConstChartMovedTextOperations: Instance providing moved text marker methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get a word group
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> # Mark as preposed text
            >>> marker = project.ConstChartMovedText.Create(wg, preposed=True)
            >>> # Check if preposed
            >>> if project.ConstChartMovedText.IsPreposed(marker):
            ...     print("Text is preposed")
            >>> # Get all moved text markers in chart
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> for marker in project.ConstChartMovedText.GetAll(chart):
            ...     wg = project.ConstChartMovedText.GetWordGroup(marker)
            ...     print(f"Moved text in word group {wg.Hvo}")
        """
        if "_constchartmovedtext_ops" not in self.__dict__:
            from .Discourse.ConstChartMovedTextOperations import ConstChartMovedTextOperations

            self._constchartmovedtext_ops = ConstChartMovedTextOperations(self)
        return self._constchartmovedtext_ops

    @property
    def ConstChartMarkers(self):
        """
        Access to project-wide chart-marker (CmPossibility) operations.

        Markers categorise discourse-chart content (Topic, Focus, ...)
        and live in ``LangProject.DiscourseDataOA.ChartMarkersOA``,
        shared across every chart in the project.

        Returns:
            ConstChartMarkerOperations
        """
        if "_constchartmarker_ops" not in self.__dict__:
            from .Discourse.ConstChartMarkerOperations import (
                ConstChartMarkerOperations,
            )
            self._constchartmarker_ops = ConstChartMarkerOperations(self)
        return self._constchartmarker_ops

    @property
    def ConstChartCellTags(self):
        """
        Access to per-cell IConstChartTag operations.

        A cell tag is a chart-cell annotation living on
        ``IConstChartRow.CellsOS``; it references a marker from the
        project-wide vocabulary via ``TagRA``. Use this surface to
        annotate cells; use ``ConstChartMarkers`` to manage the
        vocabulary itself.

        Returns:
            ConstChartCellTagOperations
        """
        if "_constchartcelltag_ops" not in self.__dict__:
            from .Discourse.ConstChartCellTagOperations import (
                ConstChartCellTagOperations,
            )
            self._constchartcelltag_ops = ConstChartCellTagOperations(self)
        return self._constchartcelltag_ops

    @property
    def ConstChartClauseMarkers(self):
        """
        Access to clause marker operations for constituent chart rows.

        Returns:
            ConstChartClauseMarkerOperations: Instance providing clause marker methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get a row and word group
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> # Create clause marker
            >>> marker = project.ConstChartClauseMarkers.Create(row, wg)
            >>> # Add dependent clause
            >>> dep_wg = project.ConstChartWordGroups.Find(row, 1)
            >>> dep_marker = project.ConstChartClauseMarkers.Create(row, dep_wg)
            >>> project.ConstChartClauseMarkers.AddDependentClause(marker, dep_marker)
            >>> # Get all markers
            >>> for marker in project.ConstChartClauseMarkers.GetAll(row):
            ...     wg = project.ConstChartClauseMarkers.GetWordGroup(marker)
            ...     print(f"Clause marker for word group {wg.Hvo}")
        """
        if "_constchartclausemarker_ops" not in self.__dict__:
            from .Discourse.ConstChartClauseMarkerOperations import ConstChartClauseMarkerOperations

            self._constchartclausemarker_ops = ConstChartClauseMarkerOperations(self)
        return self._constchartclausemarker_ops

    # Singular/plural aliases for backward compatibility are generated at
    # module scope from FLExProject._OP_NAMESPACE_ALIASES (see the end of
    # this module). Each generated alias emits a DeprecationWarning that
    # names the canonical accessor. See issue #200.

    def ImportLocalizedLists(self, language_code, progress=None):
        """Deprecated. Use ``project.LocalizedLists.Import(language_code)``."""
        import warnings as _warnings
        _warnings.warn(
            "FLExProject.ImportLocalizedLists is deprecated; "
            "use project.LocalizedLists.Import(language_code) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.LocalizedLists.Import(language_code, progress=progress)

    def ImportLocalizedListsForEnabledWS(self, progress=None):
        """Deprecated. Use ``project.LocalizedLists.ImportForAllAnalysisWritingSystems()``."""
        import warnings as _warnings
        _warnings.warn(
            "FLExProject.ImportLocalizedListsForEnabledWS is deprecated; "
            "use project.LocalizedLists"
            ".ImportForAllAnalysisWritingSystems() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.LocalizedLists.ImportForAllAnalysisWritingSystems(
            progress=progress
        )

    # --- General ---

    def ProjectName(self):
        """
        Returns the display name of the current project.
        """

        return self.project.ProjectId.UiName

    # --- String Utilities ---

    def BestStr(self, stringObj):
        """
        Generic string function for `MultiUnicode` and `MultiString`
        objects, returning the best analysis or vernacular string.

        Note: This method now delegates to WritingSystemOperations for single source of truth.

        If a string is passed instead of a multistring object, it is returned as-is
        with a warning (for backwards compatibility).
        """
        # Handle strings gracefully - just return them with a warning
        if isinstance(stringObj, str):
            logger = logging.getLogger(__name__)
            logger.warning(
                f"BestStr() called with a string instead of IMultiUnicode/IMultiString. "
                f"This should be called on multistring objects only. Returning the string as-is."
            )
            return stringObj

        return self.WritingSystems.GetBestString(stringObj)

    # --- LCM Utilities ---

    def UnpackNestedPossibilityList(self, possibilityList, objClass, flat=False):
        """
        Returns a nested or flat list of a Fieldworks possibility list.
        `objClass` is the class of object to cast the `CmPossibility` elements into.

        Return items are objects with properties/methods:
            - `Hvo`         - ID (value not the same across projects)
            - `Guid`        - Global Unique ID (same across all projects)
            - `ToString()`  - String representation.
        """
        for i in possibilityList:
            yield objClass(i)
            if flat:
                for j in self.UnpackNestedPossibilityList(i.SubPossibilitiesOS, objClass, flat):
                    yield objClass(j)
            else:
                l = list(self.UnpackNestedPossibilityList(i.SubPossibilitiesOS, objClass, flat))
                if l:
                    yield l

    # --- Global: Writing Systems ---

    def GetAllVernacularWSs(self):
        """
        Returns a set of language tags for all vernacular writing systems used
        in this project.

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        return set(self.WritingSystems.GetLanguageTag(ws) for ws in self.WritingSystems.GetVernacular())

    def GetAllAnalysisWSs(self):
        """
        Returns a set of language tags for all analysis writing systems used
        in this project.

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        return set(self.WritingSystems.GetLanguageTag(ws) for ws in self.WritingSystems.GetAnalysis())

    def GetWritingSystems(self):
        """
        Returns the writing systems that are active in this project as a
        list of tuples: (Name, Language-tag, Handle, IsVernacular).
        Use the Language-tag when specifying writing system to other
        functions.

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        VernWSSet = self.GetAllVernacularWSs()

        WSList = []
        for ws in self.WritingSystems.GetAll():
            name = self.WritingSystems.GetDisplayName(ws)
            tag = self.WritingSystems.GetLanguageTag(ws)
            handle = ws.Handle
            isVern = tag in VernWSSet
            WSList.append((name, tag, handle, isVern))
        return WSList

    def WSUIName(self, languageTagOrHandle):
        """
        Returns the UI name of the writing system for the given language tag
        or handle.
        Ignores case and '-'/'_' differences.
        Returns `None` if the language tag is not found.

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        if isinstance(languageTagOrHandle, str):
            languageTagOrHandle = self.__NormaliseLangTag(languageTagOrHandle)

        try:
            return self.__WSNameCache[languageTagOrHandle]
        except AttributeError:
            # Create a lookup table on-demand using WritingSystemOperations
            self.__WSNameCache = {}
            for ws in self.project.ServiceLocator.WritingSystems.AllWritingSystems:
                langTag = self.__NormaliseLangTag(ws.Id)
                displayName = self.WritingSystems.GetDisplayName(ws)
                self.__WSNameCache[langTag] = displayName
                self.__WSNameCache[ws.Handle] = displayName
            # Recursive:
            return self.WSUIName(languageTagOrHandle)
        except KeyError:
            return None

    def WSHandle(self, languageTag):
        """
        Returns the handle of the writing system for `languageTag`.
        Ignores case and '-'/'_' differences.
        Returns `None` if the language tag is not found.
        """

        languageTag = self.__NormaliseLangTag(languageTag)

        try:
            return self.__WSLCIDCache[languageTag]
        except AttributeError:
            # Create a lookup table on-demand.
            self.__WSLCIDCache = {}
            for x in self.project.ServiceLocator.WritingSystems.AllWritingSystems:
                langTag = self.__NormaliseLangTag(x.Id)
                self.__WSLCIDCache[langTag] = x.Handle
            # Recursive:
            return self.WSHandle(languageTag)
        except KeyError:
            return None

    def GetDefaultVernacularWS(self):
        """
        Returns the default vernacular writing system: (Language-tag, Name)

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        ws = self.WritingSystems.GetDefaultVernacular()
        return (self.WritingSystems.GetLanguageTag(ws), self.WritingSystems.GetDisplayName(ws))

    def GetDefaultAnalysisWS(self):
        """
        Returns the default analysis writing system: (Language-tag, Name)

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        ws = self.WritingSystems.GetDefaultAnalysis()
        return (self.WritingSystems.GetLanguageTag(ws), self.WritingSystems.GetDisplayName(ws))

    def GetDefaultVernacularWSHandle(self):
        """
        Returns the default vernacular writing system as a handle (int)
        suitable for `TsStringUtils.MakeString(text, ws)` and other
        multistring accessors.

        Sibling to `GetDefaultVernacularWS()`, which returns a
        (Language-tag, Name) tuple. Use this method when you need the
        raw handle for LCM calls; use the tuple-returning method for
        display.

        Returns:
            int: The handle of the default vernacular writing system.

        Example:
            >>> ws = project.GetDefaultVernacularWSHandle()
            >>> tss = TsStringUtils.MakeString("hello", ws)
        """
        return self.WritingSystems.GetDefaultVernacular().Handle

    def GetDefaultAnalysisWSHandle(self):
        """
        Returns the default analysis writing system as a handle (int)
        suitable for `TsStringUtils.MakeString(text, ws)` and other
        multistring accessors.

        Sibling to `GetDefaultAnalysisWS()`, which returns a
        (Language-tag, Name) tuple. Use this method when you need the
        raw handle for LCM calls; use the tuple-returning method for
        display.

        Returns:
            int: The handle of the default analysis writing system.

        Example:
            >>> ws = project.GetDefaultAnalysisWSHandle()
            >>> tss = TsStringUtils.MakeString("gloss", ws)
        """
        return self.WritingSystems.GetDefaultAnalysis().Handle

    # --- Media and LinkedFiles support ---

    def GetLinkedFilesDir(self):
        """
        Get the full path to the project's LinkedFiles directory.

        The LinkedFiles directory contains media files organized in subdirectories:
        - AudioVisual/ - Audio and video files
        - Pictures/ - Image files
        - Others/ - Other linked files

        Returns:
            str: Absolute path to LinkedFiles directory

        Example:
            >>> proj = FLExProject()
            >>> linked_files = proj.GetLinkedFilesDir()
            >>> print(linked_files)
            C:\\FLExData\\MyProject\\LinkedFiles

        See also:
            :meth:`MediaOperations.GetInternalPath` - Get relative path within LinkedFiles
            :meth:`MediaOperations.GetExternalPath` - Get full filesystem path
        """
        import os

        # Try to get LinkedFilesRootDir. It lives on ILangProject (self.lp), not
        # on the LcmCache (self.project) — see issue #226.
        if getattr(self.lp, "LinkedFilesRootDir", None):
            return self.lp.LinkedFilesRootDir

        # Fallback: construct default path from project folder
        if hasattr(self.project, "ProjectId") and hasattr(self.project.ProjectId, "ProjectFolder"):
            return os.path.join(self.project.ProjectId.ProjectFolder, "LinkedFiles")

        # Last resort: raise error
        raise RuntimeError("Could not determine LinkedFiles directory path")

    def IsAudioWritingSystem(self, wsHandle):
        """
        Check if a writing system is an audio writing system.

        Audio writing systems use the special script code "Zxxx" (no written form)
        and typically have "audio" in their tag. They store audio file paths
        instead of text content.

        Args:
            wsHandle (int): Writing system handle to check

        Returns:
            bool: True if this is an audio writing system, False otherwise

        Example:
            >>> ws_handle = proj.WSHandle("en-Zxxx-x-audio")
            >>> if proj.IsAudioWritingSystem(ws_handle):
            ...     print("This is an audio writing system")

        See also:
            :meth:`GetAudioPath` - Extract audio file path from audio WS field
            :meth:`SetAudioPath` - Set audio file path in audio WS field
        """
        try:
            ws = self.project.WritingSystemFactory.get_EngineOrNull(wsHandle)
            if ws is None:
                return False

            ws_tag = ws.Id
            # Audio writing systems use Zxxx script code and typically contain "audio"
            return "-Zxxx-" in ws_tag and "audio" in ws_tag.lower()

        except Exception:
            return False

    def GetAudioPath(self, multistring_field, wsHandle):
        """
        Extract the audio file path from an audio writing system field.

        Audio writing systems embed file paths in ITsString objects using
        Object Replacement Characters (ORC, U+FFFC) with FwObjDataTypes.kodtExternalPathName.

        Args:
            multistring_field: ITsMultiString or similar field containing audio data
            wsHandle (int): Audio writing system handle

        Returns:
            str: Audio file path, or None if not found

        Example:
            >>> # Get audio path from allomorph form
            >>> form = proj.Allomorph.GetForm(allomorph)
            >>> audio_ws = proj.WSHandle("en-Zxxx-x-audio")
            >>> audio_path = proj.GetAudioPath(form, audio_ws)
            >>> if audio_path:
            ...     print(f"Audio file: {audio_path}")

        See also:
            :meth:`IsAudioWritingSystem` - Check if WS is audio type
            :meth:`SetAudioPath` - Set audio file path
        """
        try:
            # Get ITsString for this writing system
            ts_string = multistring_field.get_String(wsHandle)
            if ts_string is None or ts_string.Length == 0:
                return None

            # Look for ORC character with embedded path
            text = ts_string.Text
            if text is None or "\ufffc" not in text:
                return None

            # Get the ObjData property which contains the file path
            # Format: first char is FwObjDataTypes.kodtExternalPathName, rest is path
            #
            # The ObjData string property is read straight off the run
            # properties using the FwTextPropType.ktptObjData tag. The
            # previous implementation tried to derive that tag by calling
            # GetIntPropValues on an ITsPropsBldr resolved via
            # ServiceLocator.GetInstance("FwKernelLib.ITsPropsBldr"), which
            # was dead twice over: ILcmServiceLocator exposes no GetInstance
            # member at all (its only base is System.IServiceProvider, i.e.
            # GetService(Type)), and the tag it passed -- ord("k") == 107 --
            # is not ktptObjData (== 6) anyway. (issue #272)
            from SIL.LCModel.Core.KernelInterfaces import (
                FwObjDataTypes,
                FwTextPropType,
            )

            obj_data_tag = int(FwTextPropType.ktptObjData)
            external_path_marker = chr(int(FwObjDataTypes.kodtExternalPathName))

            for i in range(ts_string.Length):
                run_props = ts_string.get_Properties(i)
                obj_data = run_props.GetStrPropValue(obj_data_tag)
                if (
                    obj_data
                    and len(obj_data) > 1
                    and obj_data[0] == external_path_marker
                ):
                    # Skip first character (type code), return path
                    return obj_data[1:]

            return None

        except Exception as e:
            import logging

            logging.warning(f"Could not extract audio path: {e}")
            return None

    def SetAudioPath(self, multistring_field, wsHandle, file_path):
        """
        Set the audio file path in an audio writing system field.

        Embeds the file path using Object Replacement Character (ORC) with
        FwObjDataTypes.kodtExternalPathName.

        Args:
            multistring_field: ITsMultiString or similar field to update
            wsHandle (int): Audio writing system handle
            file_path (str): Path to audio file (can be relative or absolute)

        Example:
            >>> # Set audio for allomorph form
            >>> allomorph = proj.Allomorph.GetAll()[0]
            >>> audio_ws = proj.WSHandle("en-Zxxx-x-audio")
            >>> audio_path = "LinkedFiles/AudioVisual/hello.wav"
            >>> proj.Allomorph.SetFormAudio(allomorph, audio_path, audio_ws)

        Raises:
            FP_ReadOnlyError: If the project is not opened with
                writeEnabled=True.

        See also:
            :meth:`IsAudioWritingSystem` - Check if WS is audio type
            :meth:`GetAudioPath` - Get audio file path
        """
        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        try:
            # Create ITsString with embedded file path. The TsStrBldr work is
            # pure string building against a builder, not an LCM mutation, so
            # only the final set_String needs the transaction -- but the whole
            # sequence is bracketed together to keep the built string and the
            # write that consumes it in one unit.
            with self._TransactionCM(f"Set audio path '{file_path}'"):
                # Builders come from TsStringUtils, not from the
                # ServiceLocator: ILcmServiceLocator has no GetInstance
                # member (only System.IServiceProvider.GetService(Type)),
                # so the previous
                # ServiceLocator.GetInstance("TsStrBldr") /
                # GetInstance("ITsPropsBldr") string lookups could never
                # resolve. (issue #272)
                bldr = TsStringUtils.MakeStrBldr()
                bldr.Clear()

                # Add ORC character
                bldr.Replace(0, 0, "\ufffc", None)

                # Create properties with embedded path
                # Format: kodtExternalPathName character + file path
                from SIL.LCModel.Core.KernelInterfaces import (
                    FwObjDataTypes,
                    FwTextPropType,
                )

                obj_data = chr(int(FwObjDataTypes.kodtExternalPathName)) + file_path

                # Set the ObjData property on the character. The correct
                # property tag is FwTextPropType.ktptObjData (== 6); the
                # previous ord("k") (== 107) was a different property.
                props_bldr = TsStringUtils.MakePropsBldr()
                props_bldr.SetStrPropValue(int(FwTextPropType.ktptObjData), obj_data)

                # Apply properties to the ORC character
                bldr.SetProperties(0, 1, props_bldr.GetTextProps())

                # Set the string in the multistring field
                multistring_field.set_String(wsHandle, bldr.GetString())

        except Exception as e:
            import logging

            logging.error(f"Could not set audio path: {e}")
            raise

    # --- Global: other information ---

    def GetDateLastModified(self):
        return self.lp.DateModified

    def GetPartsOfSpeech(self):
        """
        Returns a list of the parts of speech defined in this project.

        .. note::
           This method delegates to :meth:`POSOperations.GetAll`.
        """
        return [self.POS.GetName(pos) for pos in self.POS.GetAll()]

    def GetAllSemanticDomains(self, recursive=True):
        """
        Returns a list of all semantic domains defined in this project.
        The list is ordered.

        Args:
            recursive (bool): When True (default), walks the full
                hierarchy and returns every descendant domain
                (e.g. ~700+ entries on Sena 3). When False, returns
                only the top-level domains (~7 entries).

        Return items are `ICmSemanticDomain` objects.

        .. note::
           This method delegates to :meth:`SemanticDomainOperations.GetAll`.
           The default of ``recursive=True`` matches every other
           ``GetAll`` accessor in the codebase (refactor d423e83).
        """
        return self.SemanticDomains.GetAll(recursive=recursive)

    # --- Global utility functions ---

    def BuildGotoURL(self, objectOrGuid):
        """
        Builds a URL that can be used with `os.startfile()` to jump to the
        object in Fieldworks. This method currently supports:

            - Lexical Entries, Senses and any object within the lexicon
            - Wordforms, Analyses and Wordform Glosses
            - Reversal Entries
            - Texts
        """

        if isinstance(objectOrGuid, System.Guid):
            flexObject = self.Object(objectOrGuid)
        else:
            flexObject = objectOrGuid

        # Quick sanity check that we have the right thing
        try:
            flexObject.Guid
        except (AttributeError, Exception):
            raise FP_ParameterError(
                "BuildGotoURL: objectOrGuid is neither System.Guid nor an object with attribute Guid"
            )

        if flexObject.ClassID == ReversalIndexEntryTags.kClassId:
            tool = "reversalToolEditComplete"

        elif flexObject.ClassID in (WfiWordformTags.kClassId, WfiAnalysisTags.kClassId, WfiGlossTags.kClassId):
            tool = "Analyses"

        elif flexObject.ClassID == TextTags.kClassId:
            tool = "interlinearEdit"

        else:
            tool = "lexiconEdit"  # Default tool is Lexicon Edit

        # Build the URL
        linkObj = FwAppArgs(self.project.ProjectId.Handle, tool, flexObject.Guid)

        return str(linkObj)

    # --- Generic Repository Access ---

    def ObjectRepository(self, repository):
        """
        Returns an object repository.
        `repository` is specified by the interface class, such as:

            - `ITextRepository`
            - `ILexEntryRepository`
        """

        return self.project.ServiceLocator.GetService(repository)

    def ObjectCountFor(self, repository):
        """
        Returns the number of objects in `repository`.
        `repository` is specified by the interface class, such as:

            - `ITextRepository`
            - `ILexEntryRepository`

        All repository names can be viewed by opening a project in
        LCMBrowser, which can be launched via the Help menu. Add "I"
        to the front and import from `SIL.LCModel`.
        """

        repo = self.ObjectRepository(repository)
        return repo.Count

    def ObjectsIn(self, repository):
        """
        Returns an iterator over all the objects in `repository`.
        `repository` is specified by the interface class, such as:

            - `ITextRepository`
            - `ILexEntryRepository`

        All repository names can be viewed by opening a project in
        LCMBrowser, which can be launched via the Help menu. Add "I"
        to the front and import from `SIL.LCModel`.
        """

        repo = self.ObjectRepository(repository)
        return iter(repo.AllInstances())

    def Object(self, hvoOrGuid):
        """
        Returns the `CmObject` for the given Hvo or guid (`str` or `System.Guid`).
        Refer to `.ClassName` to determine the LCM class.
        """
        if isinstance(hvoOrGuid, str):
            try:
                hvoOrGuid = System.Guid(hvoOrGuid)
            except System.FormatException:
                raise FP_ParameterError("Invalid parameter, hvoOrGuid")

        if isinstance(hvoOrGuid, (System.Guid, int)):
            return self.project.ServiceLocator.GetObject(hvoOrGuid)
        else:
            raise FP_ParameterError("hvoOrGuid must be an Hvo (int), System.Guid or str")

    # --- Lexicon ---

    def LexiconNumberOfEntries(self):
        return self.ObjectCountFor(ILexEntryRepository)

    def LexiconAllEntries(self):
        """
        Returns an iterator over all entries in the lexicon.

        Each entry is of type::

          SIL.LCModel.ILexEntry, which contains:
              - HomographNumber :: integer
              - HomographForm :: string
              - LexemeFormOA ::  SIL.LCModel.IMoForm
                   - Form :: SIL.LCModel.MultiUnicodeAccessor
                      - GetAlternative : Get String for given WS type
                      - SetAlternative : Set string for given WS type
              - SensesOS :: Ordered collection of SIL.LCModel.ILexSense
                  - Gloss :: SIL.LCModel.MultiUnicodeAccessor
                  - Definition :: SIL.LCModel.MultiStringAccessor
                  - SenseNumber :: string
                  - ExamplesOS :: Ordered collection of ILexExampleSentence
                      - Example :: MultiStringAccessor

        Note: This method delegates to LexEntryOperations.GetAll() for single source of truth.
        """

        return self.LexEntry.GetAll()

    def LexiconAllEntriesSorted(self):
        """
        Returns an iterator over all entries in the lexicon sorted by
        the (lower-case) headword.
        """
        entries = [(str(e.HeadWord), e) for e in self.LexiconAllEntries()]

        for h, e in sorted(entries, key=lambda x: x[0].lower()):
            yield e

    #  Private writing system utilities

    def __WSHandle(self, languageTagOrHandle, defaultWS):
        if languageTagOrHandle is None:
            handle = defaultWS
        else:
            # print "Specified ws =", languageTagOrHandle
            if isinstance(languageTagOrHandle, str):
                handle = self.WSHandle(languageTagOrHandle)
            else:
                # Coerce CoreWritingSystemDefinition (or any object with .Handle)
                # to int so callers can pass WS objects from project.WritingSystems
                # without a confusing pythonnet TypeError.  See issue #171.
                handle = normalize_ws_handle(languageTagOrHandle)
        if not handle:
            raise FP_WritingSystemError(languageTagOrHandle)
        return handle

    def __WSHandleVernacular(self, languageTagOrHandle):
        return self.__WSHandle(languageTagOrHandle, self.project.DefaultVernWs)

    def __WSHandleAnalysis(self, languageTagOrHandle):
        return self.__WSHandle(languageTagOrHandle, self.project.DefaultAnalWs)

    def __NormaliseLangTag(self, languageTag):
        return languageTag.replace("-", "_").lower()

    #  Vernacular WS fields

    def LexiconGetHeadword(self, entry):
        """
        Returns the headword for `entry`.

        Note: This method now delegates to LexEntryOperations for single source of truth.
        """
        return self.LexEntry.GetHeadword(entry)

    def LexiconGetLexemeForm(self, entry, languageTagOrHandle=None):
        """
        Returns the lexeme form for `entry` in the default vernacular WS
        or other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to LexEntryOperations for single source of truth.
        """
        return self.LexEntry.GetLexemeForm(entry, languageTagOrHandle)

    def LexiconSetLexemeForm(self, entry, form, languageTagOrHandle=None):
        """
        Set the lexeme form for `entry`:
            - `form` is the new lexeme form string.
            - `languageTagOrHandle` specifies a non-default writing system.

        Note: This method now delegates to LexEntryOperations for single source of truth.
        """
        return self.LexEntry.SetLexemeForm(entry, form, languageTagOrHandle)

    def LexiconGetCitationForm(self, entry, languageTagOrHandle=None):
        """
        Returns the citation form for `entry` in the default vernacular WS
        or other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to LexEntryOperations for single source of truth.
        """
        return self.LexEntry.GetCitationForm(entry, languageTagOrHandle)

    def LexiconGetAlternateForm(self, entry, languageTagOrHandle=None):
        """
        Returns the Alternate form for the entry in the Default Vernacular WS
        or other WS as specified by languageTagOrHandle.
        """
        WSHandle = self.__WSHandleVernacular(languageTagOrHandle)

        # MultiUnicodeAccessor
        form = ITsString(entry.AlternateFormsOS.Form.get_String(WSHandle)).Text
        return form or ""

    def LexiconGetPublishInCount(self, entry):
        """
        Returns the number of dictionaries that `entry` is configured
        to be published in.
        """
        return entry.PublishIn.Count

    def LexiconGetPronunciation(self, pronunciation, languageTagOrHandle=None):
        """
        Returns the form for `pronunciation` in the default vernacular WS
        or other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to PronunciationOperations for single source of truth.
        """
        return self.Pronunciations.GetForm(pronunciation, languageTagOrHandle)

    def LexiconGetExample(self, example, languageTagOrHandle=None):
        """
        Returns the example text in the default vernacular WS or
        other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to ExampleOperations for single source of truth.
        """
        return self.Examples.GetExample(example, languageTagOrHandle)

    def LexiconSetExample(self, example, newString, languageTagOrHandle=None):
        """
        Set the default vernacular string for `example`:
            - `newString` is the new string value.
            - `languageTagOrHandle` specifies a non-default writing system.

        NOTE: using this function will lose any formatting that might
        have been present in the example string.

        Note: This method now delegates to ExampleOperations for single source of truth.
        """
        return self.Examples.SetExample(example, newString, languageTagOrHandle)

    def LexiconGetExampleTranslation(self, translation, languageTagOrHandle=None):
        """
        Returns the translation of an example in the default analysis WS or
        other WS as specified by `languageTagOrHandle`.

        NOTE: Analysis language translations of example sentences are
        stored as a collection (list). E.g.::

            for translation in example.TranslationsOC:
                print (project.LexiconGetExampleTranslation(translation))

        Note: This method works with translation objects (ICmTranslation) directly.
        For getting translation text from an example object, use Examples.GetTranslation().
        """
        WSHandle = self.__WSHandleAnalysis(languageTagOrHandle)

        # Translation is a MultiString
        tr = ITsString(translation.Translation.get_String(WSHandle)).Text
        return tr or ""

    def LexiconGetSenseNumber(self, sense):
        """
        Returns the sense number for the sense. (This is not available
        directly from `ILexSense`.)

        Note: This method delegates to LexSenseOperations.GetSenseNumber() for single source of truth.
        """

        return self.Senses.GetSenseNumber(sense)

    #  Analysis WS fields

    def LexiconGetSenseGloss(self, sense, languageTagOrHandle=None):
        """
        Returns the gloss for the sense in the default analysis WS or
        other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.GetGloss(sense, languageTagOrHandle)

    def LexiconSetSenseGloss(self, sense, gloss, languageTagOrHandle=None):
        """
        Set the default analysis gloss for `sense`:
            - `gloss` is the new gloss string.
            - `languageTagOrHandle` specifies a non-default writing system.

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.SetGloss(sense, gloss, languageTagOrHandle)

    def LexiconGetSenseDefinition(self, sense, languageTagOrHandle=None):
        """
        Returns the definition for the sense in the default analysis WS or
        other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.GetDefinition(sense, languageTagOrHandle)

    #  Non-string types

    def LexiconGetSensePOS(self, sense):
        """
        Returns the part of speech abbreviation for the sense.

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.GetPartOfSpeech(sense)

    def LexiconGetSenseSemanticDomains(self, sense):
        """
        Returns a list of semantic domain objects belonging to the sense.
        `ToString()` and `Hvo` are available.

        Methods available for SemanticDomainsRC::

             Count
             Add(Hvo)
             Contains(Hvo)
             Remove(Hvo)
             RemoveAll()

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.GetSemanticDomains(sense)

    def LexiconEntryAnalysesCount(self, entry):
        """
        Returns a count of the occurrences of the entry in the text corpus.

        NOTE: This calculation can produce slightly different results to
        that shown in FieldWorks (where the same analysis in the same text
        segment is only counted once in some displays). See LT-13997 for
        more details.
        """

        # EntryAnalysesCount is not part of the interface ILexEntry,
        # and you can't cast to LexEntry outside the LCM assembly
        # because LexEntry is internal.
        # Therefore we use reflection since it is a public method which
        # any instance of ILexEntry implements.
        # (Instructions from JohnT)

        count = ReflectionHelper.GetProperty(entry, "EntryAnalysesCount")
        return count

    def LexiconSenseAnalysesCount(self, sense):
        """
        Returns a count of the occurrences of the sense in the text corpus.

        Note: This method delegates to LexSenseOperations.GetAnalysesCount() for single source of truth.
        """

        return self.Senses.GetAnalysesCount(sense)

    # --- Lexicon: field functions ---

    def GetFieldID(self, className, fieldName):
        """
        Return the `FieldID` ('flid') for the given field of an LCM class.
        `className` and `fieldName` are strings, where `fieldName` may omit
        the type suffix (e.g. 'OS'). Both are case-sensitive.
        For example, find the `FieldID` for academic domains with::

            GetFieldID("LexSense", "DomainTypes")
        """

        mdc = self.project.MetaDataCacheAccessor

        if fieldName[-2:] in ("OA", "OS", "OC", "RA", "RS", "RC"):
            fieldName = fieldName[:-2]

        try:
            # True=include base classes if needed.
            flid = mdc.GetFieldId(className, fieldName, True)
        except (LcmInvalidFieldException, LcmInvalidClassException) as e:
            # "from None" avoids confusion of both exceptions being reported.
            raise FP_ParameterError(e.Message) from None
        return flid

    def __ValidatedHvo(self, senseOrEntryOrHvo, fieldID):
        """
        Internal function to check for valid parameters to lexicon functions.
        """
        if not senseOrEntryOrHvo:
            raise FP_NullParameterError()
        if not fieldID:
            raise FP_NullParameterError()

        try:
            hvo = senseOrEntryOrHvo.Hvo
        except AttributeError:
            hvo = senseOrEntryOrHvo

        return hvo

    def GetCustomFieldValue(self, senseOrEntryOrHvo, fieldID, languageTagOrHandle=None):
        """
        Returns the field value for String, MultiString, Integer
        and List (both single and multiple) fields.
        Raises `FP_ParameterError` for other field types.

        `languageTagOrHandle` only applies to MultiStrings; if `None` the
        best analysis or venacular string is returned.

        Note: if the field is a vernacular WS field, then the
        `languageTagOrHandle` must be specified.
        """

        hvo = self.__ValidatedHvo(senseOrEntryOrHvo, fieldID)

        # Adapted from XDumper.cs::GetCustomFieldValue
        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        fieldType = CellarPropertyType(mdc.GetFieldType(fieldID))

        if fieldType in FLExLCM.CellarStringTypes:
            return ITsString(self.project.DomainDataByFlid.get_StringProp(hvo, fieldID))

        elif fieldType in FLExLCM.CellarMultiStringTypes:
            mua = self.project.DomainDataByFlid.get_MultiStringProp(hvo, fieldID)
            if languageTagOrHandle:
                WSHandle = self.__WSHandle(languageTagOrHandle, None)
                return mua.get_String(WSHandle)
            else:
                # mua is a bare ITsMultiString (SIL.LCModel.Core.KernelInterfaces),
                # which has no BestAnalysisVernacularAlternative accessor (that
                # lives on IMultiAccessorBase). Reimplement the "best available
                # alternative" priority walk on top of get_String() instead.
                # See issue #224.
                analWsHandles = [int(ws.Handle) for ws in self.lp.CurrentAnalysisWritingSystems]
                vernWsHandles = [int(ws.Handle) for ws in self.lp.CurrentVernacularWritingSystems]
                best = best_multistring_alternative(
                    mua,
                    self.project.DefaultAnalWs,
                    self.project.DefaultVernWs,
                    analWsHandles,
                    vernWsHandles,
                )
                if best is not None:
                    return best
                # Total miss across every configured WS: still return a
                # (possibly empty) ITsString so this branch's contract
                # matches the sibling branches above/below, which always
                # return ITsString.
                return ITsString(mua.get_String(self.project.DefaultAnalWs))

        elif fieldType == CellarPropertyType.Integer:
            return self.project.DomainDataByFlid.get_IntProp(hvo, fieldID)

        elif fieldType == CellarPropertyType.ReferenceAtom:
            item = self.project.DomainDataByFlid.get_ObjectProp(hvo, fieldID)
            if not item:
                return ""
            poss = self.ObjectRepository(ICmPossibilityRepository).GetObject(item)
            return poss.ShortName

        elif fieldType == CellarPropertyType.ReferenceCollection:
            numItems = self.project.DomainDataByFlid.get_VecSize(hvo, fieldID)
            getPossibilityObject = self.ObjectRepository(ICmPossibilityRepository).GetObject
            items = []
            for i in range(numItems):
                item = self.project.DomainDataByFlid.get_VecItem(hvo, fieldID, i)
                poss = getPossibilityObject(item)
                items.append(poss.ShortName)
            return items

        raise FP_ParameterError("GetCustomFieldValue: field is not a supported type")

    def LexiconFieldIsStringType(self, fieldID):
        """
        Returns `True` if the given field is a simple string type suitable
        for use with `LexiconAddTagToField()`, otherwise returns `False`.

        Delegates to: CustomFields.GetFieldType()
        """
        if not fieldID:
            raise FP_NullParameterError()

        field_type = self.CustomFields.GetFieldType(fieldID)
        return field_type == CellarPropertyType.String

    def LexiconFieldIsMultiType(self, fieldID):
        """
        Returns `True` if the given field is a multi string type
        (MultiUnicode or MultiString)

        Delegates to: CustomFields.IsMultiString()
        """
        if not fieldID:
            raise FP_NullParameterError()

        return self.CustomFields.IsMultiString(fieldID)

    def LexiconFieldIsAnyStringType(self, fieldID):
        """
        Returns `True` if the given field is any of the string types.

        Delegates to: CustomFields.GetFieldType()
        """
        if not fieldID:
            raise FP_NullParameterError()

        field_type = self.CustomFields.GetFieldType(fieldID)
        return field_type in (
            CellarPropertyType.String,
            CellarPropertyType.MultiString,
            CellarPropertyType.MultiUnicode,
        )

    def LexiconGetFieldText(self, senseOrEntryOrHvo, fieldID, languageTagOrHandle=None):
        """
        Return the text value for the given entry/sense and field ID.
        Provided for use with custom fields.
        Returns the empty string if the value is null.
        `languageTagOrHandle` only applies to MultiStrings; if `None` the
        default analysis writing system is returned.

        Note: if the field is a vernacular WS field, then
        `languageTagOrHandle` must be specified.

        For normal fields, the object can be used directly with
        `get_String()`. E.g.::

            lexForm = lexEntry.LexemeFormOA
            lexEntryValue = ITsString(lexForm.Form.get_String(WSHandle)).Text
        """

        value = self.GetCustomFieldValue(senseOrEntryOrHvo, fieldID, languageTagOrHandle)

        # (value.Text is None if the field is empty.)
        if value and value.Text and value.Text != "***":
            return value.Text
        else:
            return ""

    def LexiconSetFieldText(self, senseOrEntryOrHvo, fieldID, text, languageTagOrHandle=None):
        """
        Set the text value for the given entry/sense and field ID.
        Provided for use with custom fields.

        NOTE: writes the string in one writing system only (defaults
        to the default analysis WS).

        For normal fields the object can be used directly with
        `set_String()`. E.g.::

            lexForm = lexEntry.LexemeFormOA
            mkstr = TsStringUtils.MakeString("text to write", WSHandle)
            lexForm.Form.set_String(WSHandle, mkstr)
        """

        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntryOrHvo, fieldID)

        WSHandle = self.__WSHandleAnalysis(languageTagOrHandle)

        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        fieldType = CellarPropertyType(mdc.GetFieldType(fieldID))

        tss = TsStringUtils.MakeString(text, WSHandle)

        # The unsupported-type rejection is checked first, outside the
        # transaction, so a bad field type never opens an undo task.
        if fieldType not in FLExLCM.CellarStringTypes and fieldType not in FLExLCM.CellarMultiStringTypes:
            raise FP_ParameterError("LexiconSetFieldText: field is not a supported type")

        with self._TransactionCM("Set field text"):
            if fieldType in FLExLCM.CellarStringTypes:
                try:
                    self.project.DomainDataByFlid.SetString(hvo, fieldID, tss)
                except LcmInvalidFieldException as msg:
                    # This exception indicates that the project is not in write mode
                    raise FP_ReadOnlyError()
            else:
                # MultiUnicodeAccessor
                mua = self.project.DomainDataByFlid.get_MultiStringProp(hvo, fieldID)
                try:
                    mua.set_String(WSHandle, tss)
                except LcmInvalidFieldException as msg:
                    raise FP_ReadOnlyError()

    def LexiconClearField(self, senseOrEntryOrHvo, fieldID):
        """
        Clears the string field or all of the strings (writing systems)
        in a multi-string field.
        Can be used to clear out a custom field.
        """

        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntryOrHvo, fieldID)

        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        fieldType = CellarPropertyType(mdc.GetFieldType(fieldID))

        # The unsupported-type rejection is checked first, outside the
        # transaction, so a bad field type never opens an undo task.
        if fieldType not in FLExLCM.CellarStringTypes and fieldType not in FLExLCM.CellarMultiStringTypes:
            raise FP_ParameterError("LexiconClearField: field is not a supported type")

        # One transaction for the whole field: clearing a multistring writes
        # every analysis and vernacular WS, and a partial clear is not a state
        # any caller asked for.
        with self._TransactionCM("Clear field"):
            if fieldType in FLExLCM.CellarStringTypes:
                try:
                    self.project.DomainDataByFlid.SetString(hvo, fieldID, None)
                except LcmInvalidFieldException as msg:
                    # This exception indicates that the project is not in write mode
                    raise FP_ReadOnlyError()
            else:
                # MultiUnicodeAccessor
                mua = self.project.DomainDataByFlid.get_MultiStringProp(hvo, fieldID)
                try:
                    for ws in self.GetAllAnalysisWSs() | self.GetAllVernacularWSs():
                        mua.set_String(self.WSHandle(ws), None)
                except LcmInvalidFieldException as msg:
                    raise FP_ReadOnlyError()

    def LexiconSetFieldInteger(self, senseOrEntryOrHvo, fieldID, integer):
        """
        Sets the integer value for the given entry/sense and field ID.
        Provided for use with custom fields.
        """

        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntryOrHvo, fieldID)

        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        if CellarPropertyType(mdc.GetFieldType(fieldID)) != CellarPropertyType.Integer:
            raise FP_ParameterError("LexiconSetFieldInteger: field is not Integer type")

        # The equality guard stays OUTSIDE the bracket so an unchanged value
        # stays a true no-op that opens no unit of work.
        if self.project.DomainDataByFlid.get_IntProp(hvo, fieldID) != integer:
            try:
                with self._TransactionCM("Set field integer"):
                    self.project.DomainDataByFlid.SetInt(hvo, fieldID, integer)
            except LcmInvalidFieldException as msg:
                # This exception indicates that the project is not in write mode
                raise FP_ReadOnlyError()

    def LexiconAddTagToField(self, senseOrEntryOrHvo, fieldID, tag):
        """
        Appends the tag string to the end of the given field in the
        sense or entry inserting a semicolon between tags.
        If the tag is already in the field then it isn't added.
        """

        s = self.LexiconGetFieldText(senseOrEntryOrHvo, fieldID)

        if s:
            if tag in s:
                return
            newText = "; ".join((s, tag))
        else:
            newText = tag

        self.LexiconSetFieldText(senseOrEntryOrHvo, fieldID, newText)

        return

    # --- Lexicon: list field functions ---

    def ListFieldPossibilityList(self, senseOrEntry, fieldID):
        """
        Return the `CmPossibilityList` object for the given list field.
        Raises an exception if the field is not a list (single/Atomic
        or multiple/Collection)
        """

        if not senseOrEntry:
            raise FP_NullParameterError()
        if not fieldID:
            raise FP_NullParameterError()

        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        fieldType = CellarPropertyType(mdc.GetFieldType(fieldID))
        if fieldType not in (CellarPropertyType.ReferenceAtom, CellarPropertyType.ReferenceCollection):
            raise FP_ParameterError("ListFieldPossibilityList: field must be a List type")
        return ICmPossibilityList(senseOrEntry.ReferenceTargetOwner(fieldID))

    def ListFieldPossibilities(self, senseOrEntry, fieldID):
        """
        Returns the `PossibilitiesOS` for the given list field. This
        is a list of `CmPossibility` objects.
        Raises an exception if the field is not a list (single/Atomic
        or multiple/Collection)

        Note: this returns the top-level `CmPossibility` objects. Subitems
        can be found via the `SubPossibilitiesOS` attribute. Alternatively,
        a flat list of all possible options can be obtained with::

            options = project.UnpackNestedPossibilityList(possibilities,
                                                          str,
                                                          True)
        """

        pList = self.ListFieldPossibilityList(senseOrEntry, fieldID)
        return pList.PossibilitiesOS

    def ListFieldLookup(self, senseOrEntry, fieldID, value):
        """
        Looks up the value (a string) in the `CmPossibilityList` for the
        given field.
        Returns the `CmPossibility` object, or `None` if it can't be found.
        """

        pList = self.ListFieldPossibilityList(senseOrEntry, fieldID)
        wsa = self.lp.DefaultAnalysisWritingSystem.Handle
        return pList.FindPossibilityByName(pList.PossibilitiesOS, value, wsa)

    def LexiconSetListFieldSingle(self, senseOrEntry, fieldID, possibilityOrString):
        """
        Sets the value for a 'single' (Atomic) list field.
        `possibilityOrString` can be a `CmPossibility` object, or a string.
        A string value can be the full name or the abbreviation (case-sensitive).

        Use `ListFieldPossibilities()` to find the valid values for the list.

        Note: this function is primarily for use with custom fields,
        since regular list field values can be assigned directly. E.g.::

             status_poss = project.ListFieldPossibilities(
                               sense,
                               project.GetFieldID("LexSense", "Status"))
             sense.StatusRA = status_poss[3]    # Tentative
        """

        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntry, fieldID)

        if type(possibilityOrString) is str:
            possibility = self.ListFieldLookup(senseOrEntry, fieldID, possibilityOrString)
            if not possibility:
                raise FP_ParameterError(f"'{possibilityOrString}' not found in the Possibility list")
        else:
            try:
                if possibilityOrString.ClassName == "CmPossibility":
                    possibility = possibilityOrString
                else:
                    raise AttributeError
            except AttributeError:
                raise FP_ParameterError("possibilityOrString must be a string or CmPossibility")

        # Resolution/validation above stays outside the bracket (D5/P3).
        with self._TransactionCM("Set list field"):
            self.project.DomainDataByFlid.SetObjProp(hvo, fieldID, possibility.Hvo)

    def LexiconClearListFieldSingle(self, senseOrEntry, fieldID):
        """
        Clears the value for a 'single' (Atomic) list field.
        """

        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntry, fieldID)

        with self._TransactionCM("Clear list field"):
            self.project.DomainDataByFlid.SetObjProp(hvo, fieldID, 0)

    def LexiconSetListFieldMultiple(self, senseOrEntry, fieldID, listOfValues):
        """
        Sets the value(s) for a 'multiple' (Collection) list field.
        `listOfValues` can be a list of:

            - `CmPossibility` objects; or
            - `CmPossibility` hvos; or
            - `str` (either the full name or the abbreviation; case-sensitive).

        Use `ListFieldPossibilities()` to find the valid values for the list.

        Note: this function is primarily for use with custom fields,
        since regular fields can use the `Add()`, `Remove()` and `Clear()`
        methods of the field itself (see LcmReferenceCollection).
        """

        if not self.writeEnabled:
            raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntry, fieldID)

        if not listOfValues:
            raise FP_ParameterError("LexiconSetListFieldMultiple: listOfValues cannot be empty or None")

        if type(listOfValues[0]) is int:
            hvoList = listOfValues
        else:
            if type(listOfValues[0]) is str:
                possibilities = [self.ListFieldLookup(senseOrEntry, fieldID, s) for s in listOfValues]
                if not all(possibilities):
                    raise FP_ParameterError("LexiconSetListFieldMultiple: one or more values not valid.")
            else:
                possibilities = listOfValues

            try:
                hvoList = [p.Hvo for p in possibilities]
            except AttributeError:
                raise FP_ParameterError("LexiconSetListFieldMultiple: listOfValues is not valid.")

        # Get the count of current items in the field
        ddbf = self.project.DomainDataByFlid
        numItems = ddbf.get_VecSize(senseOrEntry.Hvo, fieldID)

        # Replace the current items with the new list
        with self._TransactionCM(f"Set list field ({len(hvoList)} value(s))"):
            ddbf.Replace(senseOrEntry.Hvo, fieldID, 0, numItems, hvoList, len(hvoList))

    # --- Lexicon: Custom fields ---

    def __GetCustomFieldsOfType(self, classID):
        """
        Generator for finding all the custom fields belonging to the
        given class.
        Returns tuples of (flid, label)
        """

        # The MetaDataCache defines the project structure: we can
        # find the custom fields in here.
        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)

        for flid in mdc.GetFields(classID, False, int(CellarPropertyTypeFilter.All)):
            if self.project.GetIsCustomField(flid):
                yield ((flid, mdc.GetFieldLabel(flid)))

    def __FindCustomField(self, classID, fieldName):
        for flid, name in self.__GetCustomFieldsOfType(classID):
            if name == fieldName:
                return flid
        return None

    def LexiconGetEntryCustomFields(self):
        """
        Returns a list of the custom fields defined at entry level.
        Each item in the list is a tuple of (flid, label)

        Delegates to: CustomFields.GetAllFields("LexEntry")
        """
        return self.CustomFields.GetAllFields("LexEntry")

    def LexiconGetSenseCustomFields(self):
        """
        Returns a list of the custom fields defined at sense level.
        Each item in the list is a tuple of (flid, label)

        Delegates to: CustomFields.GetAllFields("LexSense")
        """
        return self.CustomFields.GetAllFields("LexSense")

    def LexiconGetExampleCustomFields(self):
        """
        Returns a list of the custom fields defined at example level.
        Each item in the list is a tuple of (flid, label)

        Delegates to: CustomFields.GetAllFields("LexExampleSentence")
        """
        return self.CustomFields.GetAllFields("LexExampleSentence")

    def LexiconGetAllomorphCustomFields(self):
        """
        Returns a list of the custom fields defined at allomorph level.
        Each item in the list is a tuple of (flid, label)

        Delegates to: CustomFields.GetAllFields("MoForm")
        """
        return self.CustomFields.GetAllFields("MoForm")

    def LexiconGetEntryCustomFieldNamed(self, fieldName):
        """
        Return the entry-level field ID given its name.

        NOTE: `fieldName` is case-sensitive.

        Delegates to: CustomFields.FindField("LexEntry", name)
        """
        return self.CustomFields.FindField("LexEntry", fieldName)

    def LexiconGetSenseCustomFieldNamed(self, fieldName):
        """
        Return the sense-level field ID given its name.

        NOTE: `fieldName` is case-sensitive.

        Delegates to: CustomFields.FindField("LexSense", name)
        """
        return self.CustomFields.FindField("LexSense", fieldName)

    # --- Entry/Sense Operations (FlexTools Compatibility) ---

    def LexiconGetMorphType(self, entry):
        """
        Get the morph type of a lexical entry.

        Args:
            entry: ILexEntry object or HVO

        Returns:
            IMoMorphType: The morph type object

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> morph_type = project.LexiconGetMorphType(entry)
            >>> print(morph_type.Name.BestAnalysisAlternative.Text)
            stem

        Note:
            Delegates to: LexEntry.GetMorphType(entry)
        """
        return self.LexEntry.GetMorphType(entry)

    def LexiconSetMorphType(self, entry, morph_type_or_name):
        """
        Set the morph type of a lexical entry.

        Args:
            entry: ILexEntry object or HVO
            morph_type_or_name: IMoMorphType object or name string
                ("stem", "root", "prefix", "suffix", etc.)

        Example:
            >>> entry = project.LexEntry.Find("-ing")
            >>> project.LexiconSetMorphType(entry, "suffix")

        Note:
            Delegates to: LexEntry.SetMorphType(entry, morph_type_or_name)
        """
        return self.LexEntry.SetMorphType(entry, morph_type_or_name)

    def LexiconAllAllomorphs(self):
        """
        Get all allomorphs in the entire project.

        Yields:
            IMoForm: Each allomorph in the project

        Example:
            >>> for allomorph in project.LexiconAllAllomorphs():
            ...     form = project.Allomorphs.GetForm(allomorph)
            ...     print(form)

        Note:
            Delegates to: Allomorphs.GetAll()
        """
        return self.Allomorphs.GetAll()

    def LexiconNumberOfSenses(self, entry):
        """
        Get the number of senses in a lexical entry.

        Args:
            entry: ILexEntry object or HVO

        Returns:
            int: Number of senses

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> count = project.LexiconNumberOfSenses(entry)
            >>> print(f"Entry has {count} senses")

        Note:
            Delegates to: LexEntry.GetSenseCount(entry)
        """
        return self.LexEntry.GetSenseCount(entry)

    def LexiconGetSenseByName(self, entry, gloss_text, languageTagOrHandle=None):
        """
        Find a sense by its gloss text.

        Args:
            entry: ILexEntry object or HVO
            gloss_text (str): The gloss text to search for
            languageTagOrHandle: Optional writing system

        Returns:
            ILexSense or None: The first sense with matching gloss, or None

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> sense = project.LexiconGetSenseByName(entry, "to move rapidly")
            >>> if sense:
            ...     print(f"Found sense: {sense.Guid}")

        Note:
            This searches for exact match (case-sensitive).
            Returns first match if multiple senses have same gloss.
        """
        if languageTagOrHandle is None:
            languageTagOrHandle = self.GetDefaultAnalysisWSHandle()

        for sense in self.Senses.GetAll(entry):
            gloss = self.Senses.GetGloss(sense, languageTagOrHandle)
            if gloss == gloss_text:
                return sense
        return None

    def LexiconAddEntry(self, lexeme_form, morph_type_name="stem", languageTagOrHandle=None):
        """
        Create a new lexical entry.

        Args:
            lexeme_form (str): The lexeme form (headword)
            morph_type_name (str): Morph type ("stem", "root", "prefix", etc.)
            languageTagOrHandle: Optional writing system

        Returns:
            ILexEntry: The newly created entry

        Example:
            >>> entry = project.LexiconAddEntry("walk", "stem")
            >>> print(project.LexEntry.GetHeadword(entry))
            walk

        Note:
            Delegates to: LexEntry.Create(lexeme_form, morph_type_name, wsHandle)
        """
        wsHandle = None
        if languageTagOrHandle is not None:
            if isinstance(languageTagOrHandle, str):
                wsHandle = self.WSHandle(languageTagOrHandle)
            else:
                wsHandle = languageTagOrHandle

        return self.LexEntry.Create(lexeme_form, morph_type_name, wsHandle)

    def LexiconGetEntry(self, index):
        """
        Get a lexical entry by index.

        Args:
            index (int): Zero-based index into all entries

        Returns:
            ILexEntry: The entry at the specified index

        Example:
            >>> first_entry = project.LexiconGetEntry(0)
            >>> tenth_entry = project.LexiconGetEntry(9)

        Warning:
            Inefficient for large lexicons - iterates through all entries.
            Consider using LexEntry.Find() or LexEntry.GetAll() instead.

        Note:
            Returns entry in database order (not alphabetical).
        """
        for i, entry in enumerate(self.LexEntry.GetAll()):
            if i == index:
                return entry
        return None

    def LexiconAddSense(self, entry, gloss, languageTagOrHandle=None):
        """
        Add a sense to a lexical entry.

        Args:
            entry: ILexEntry object or HVO
            gloss (str): The gloss text
            languageTagOrHandle: Optional writing system

        Returns:
            ILexSense: The newly created sense

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> sense = project.LexiconAddSense(entry, "to move rapidly")

        Note:
            Delegates to: LexEntry.AddSense(entry, gloss, wsHandle)
        """
        wsHandle = None
        if languageTagOrHandle is not None:
            if isinstance(languageTagOrHandle, str):
                wsHandle = self.WSHandle(languageTagOrHandle)
            else:
                wsHandle = languageTagOrHandle

        return self.LexEntry.AddSense(entry, gloss, wsHandle)

    def LexiconGetSense(self, entry, index):
        """
        Get a sense by index from an entry.

        Args:
            entry: ILexEntry object or HVO
            index (int): Zero-based index

        Returns:
            ILexSense or None: The sense at the index, or None if out of range

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> first_sense = project.LexiconGetSense(entry, 0)
            >>> second_sense = project.LexiconGetSense(entry, 1)

        Note:
            Direct access via entry.SensesOS[index] is more efficient.
        """
        senses = list(self.Senses.GetAll(entry))
        if 0 <= index < len(senses):
            return senses[index]
        return None

    def LexiconDeleteObject(self, obj):
        """
        Delete an object from the database.

        Args:
            obj: The object to delete (ILexEntry, ILexSense, IMoForm, etc.)

        Example:
            >>> sense = entry.SensesOS[0]
            >>> project.LexiconDeleteObject(sense)
            >>> # Or delete entire entry:
            >>> project.LexiconDeleteObject(entry)

        Warning:
            This is a destructive operation and cannot be undone.

        Note:
            Delegates to appropriate Operations class Delete() method based on type.
        """
        class_name = obj.ClassName

        if class_name == "LexEntry":
            return self.LexEntry.Delete(obj)
        elif class_name == "LexSense":
            return self.Senses.Delete(obj)
        elif class_name in ("MoStemAllomorph", "MoAffixAllomorph", "MoForm"):
            return self.Allomorphs.Delete(obj)
        elif class_name == "LexPronunciation":
            return self.Pronunciations.Delete(obj)
        elif class_name == "LexExampleSentence":
            return self.Examples.Delete(obj)
        elif class_name == "LexEtymology":
            return self.Etymology.Delete(obj)
        elif class_name in ("LexEntryRef", "VariantEntryRef"):
            return self.Variants.Delete(obj)
        else:
            # Generic delete using LCM. Only this fallback branch is bracketed
            # here: every branch above delegates to an Operations class whose
            # own Delete() carries its own transaction (and would simply join
            # this one under Phase 2 if it were nested inside).
            with self._TransactionCM(f"Delete {class_name}"):
                if hasattr(obj, "Owner") and obj.Owner:
                    owner = obj.Owner
                    # Try to find and remove from owning collection
                    for prop_name in dir(owner):
                        if prop_name.endswith("OS") or prop_name.endswith("OC"):
                            try:
                                collection = getattr(owner, prop_name)
                                if hasattr(collection, "Remove") and obj in collection:
                                    collection.Remove(obj)
                                    return
                            except Exception:
                                pass

                # Fallback: delete via the object's own ICmObject.Delete().
                # The earlier code reached for IDataReader.DeleteUnderlyingObject,
                # but that interface is `internal` in liblcm and pythonnet only
                # exposes `public` types, so the import always failed.
                # ICmObject.Delete() is the documented public deletion entry point.
                obj.Delete()

    def LexiconGetHeadWord(self, entry):
        """
        Get the headword of an entry.

        This is an alias for LexiconGetHeadword() for FlexTools compatibility.

        Args:
            entry: ILexEntry object or HVO

        Returns:
            str: The headword

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> headword = project.LexiconGetHeadWord(entry)
            >>> print(headword)
            run

        Note:
            Delegates to: LexiconGetHeadword(entry)
        """
        return self.LexiconGetHeadword(entry)

    def LexiconGetAllomorphForms(self, entry, languageTagOrHandle=None):
        """
        Get all allomorph forms for an entry.

        Args:
            entry: ILexEntry object or HVO
            languageTagOrHandle: Optional writing system

        Returns:
            list: List of allomorph form strings

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> forms = project.LexiconGetAllomorphForms(entry)
            >>> print(forms)
            ['run', 'ran', 'runn-']

        Note:
            Returns forms from lexeme form and all alternate forms.
        """
        wsHandle = None
        if languageTagOrHandle is not None:
            if isinstance(languageTagOrHandle, str):
                wsHandle = self.WSHandle(languageTagOrHandle)
            else:
                wsHandle = languageTagOrHandle

        forms = []
        for allomorph in self.Allomorphs.GetAll(entry):
            form = self.Allomorphs.GetForm(allomorph, wsHandle)
            if form:
                forms.append(form)
        return forms

    def LexiconAddAllomorph(self, entry, form, morphType, languageTagOrHandle=None):
        """
        Add an allomorph to an entry.

        Args:
            entry: ILexEntry object or HVO
            form (str): The allomorph form
            morphType: IMoMorphType object or name string
            languageTagOrHandle: Optional writing system

        Returns:
            IMoForm: The newly created allomorph

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> morph_type = project.LexEntry.GetMorphType(entry)
            >>> allomorph = project.LexiconAddAllomorph(entry, "runn-", morph_type)

        Note:
            Delegates to: Allomorphs.Create(entry, form, morphType, wsHandle)
        """
        wsHandle = None
        if languageTagOrHandle is not None:
            if isinstance(languageTagOrHandle, str):
                wsHandle = self.WSHandle(languageTagOrHandle)
            else:
                wsHandle = languageTagOrHandle

        return self.Allomorphs.Create(entry, form, morphType, wsHandle)

    def LexiconGetPronunciations(self, entry):
        """
        Get all pronunciations for an entry.

        Args:
            entry: ILexEntry object or HVO

        Returns:
            iterator: Iterator of ILexPronunciation objects

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> for pron in project.LexiconGetPronunciations(entry):
            ...     form = project.Pronunciations.GetForm(pron)
            ...     print(form)

        Note:
            Delegates to: Pronunciations.GetAll(entry)
        """
        return self.Pronunciations.GetAll(entry)

    def LexiconAddPronunciation(self, entry, form, languageTagOrHandle=None):
        """
        Add a pronunciation to an entry.

        Args:
            entry: ILexEntry object or HVO
            form (str): The pronunciation form (IPA, etc.)
            languageTagOrHandle: Optional writing system

        Returns:
            ILexPronunciation: The newly created pronunciation

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> pron = project.LexiconAddPronunciation(entry, "rʌn")

        Note:
            Delegates to: Pronunciations.Create(entry, form, wsHandle)
        """
        wsHandle = None
        if languageTagOrHandle is not None:
            if isinstance(languageTagOrHandle, str):
                wsHandle = self.WSHandle(languageTagOrHandle)
            else:
                wsHandle = languageTagOrHandle

        return self.Pronunciations.Create(entry, form, wsHandle)

    def LexiconGetVariantType(self, variant):
        """
        Get the variant type of a variant entry reference.

        Args:
            variant: ILexEntryRef object

        Returns:
            ILexEntryType: The variant type

        Example:
            >>> for variant_ref in entry.EntryRefsOS:
            ...     var_type = project.LexiconGetVariantType(variant_ref)
            ...     if var_type:
            ...         print(var_type.Name.BestAnalysisAlternative.Text)

        Note:
            Delegates to: Variants.GetVariantType(variant)
        """
        return self.Variants.GetVariantType(variant)

    def LexiconAddVariantForm(self, entry, form, variant_type, languageTagOrHandle=None):
        """
        Add a variant form to an entry.

        Args:
            entry: ILexEntry object or HVO
            form (str): The variant form
            variant_type: ILexEntryType object or name string
            languageTagOrHandle: Optional writing system

        Returns:
            ILexEntryRef: The newly created variant entry reference

        Example:
            >>> entry = project.LexEntry.Find("color")
            >>> # This would typically need a variant type from the project
            >>> # variant = project.LexiconAddVariantForm(entry, "colour", variant_type)

        Note:
            Delegates to: Variants.Create(entry, form, variant_type, wsHandle)
        """
        wsHandle = None
        if languageTagOrHandle is not None:
            if isinstance(languageTagOrHandle, str):
                wsHandle = self.WSHandle(languageTagOrHandle)
            else:
                wsHandle = languageTagOrHandle

        return self.Variants.Create(entry, form, variant_type, wsHandle)

    def LexiconGetComplexFormType(self, entry_ref):
        """
        Get the complex form type of an entry reference.

        Args:
            entry_ref: ILexEntryRef object

        Returns:
            ILexEntryType or None: The complex form type

        Example:
            >>> for ref in entry.EntryRefsOS:
            ...     cf_type = project.LexiconGetComplexFormType(ref)
            ...     if cf_type:
            ...         print(cf_type.Name.BestAnalysisAlternative.Text)

        Note:
            Returns None if the entry reference is not a complex form type.
        """
        if hasattr(entry_ref, "ComplexEntryTypesRS") and entry_ref.ComplexEntryTypesRS.Count > 0:
            return entry_ref.ComplexEntryTypesRS[0]
        return None

    def LexiconSetComplexFormType(self, entry_ref, complex_form_type):
        """
        Set the complex form type of an entry reference.

        Args:
            entry_ref: ILexEntryRef object
            complex_form_type: ILexEntryType object

        Example:
            >>> # Get or create complex form type
            >>> # cf_type = ... (from project)
            >>> # entry_ref = entry.EntryRefsOS[0]
            >>> # project.LexiconSetComplexFormType(entry_ref, cf_type)

        Note:
            Replaces any existing complex form types with the specified one.
        """
        if hasattr(entry_ref, "ComplexEntryTypesRS"):
            # Clear-then-Add is two mutations: a failure between them would
            # leave the entry ref with no complex form type at all, which is
            # neither the old value nor the requested one.
            with self._TransactionCM("Set complex form type"):
                entry_ref.ComplexEntryTypesRS.Clear()
                entry_ref.ComplexEntryTypesRS.Add(complex_form_type)

    def LexiconAddComplexForm(self, entry, components, complex_form_type):
        """
        Add a complex form entry.

        Args:
            entry: ILexEntry - The complex form entry
            components: list of ILexEntry or ILexSense - The component parts
            complex_form_type: ILexEntryType - The type of complex form

        Returns:
            ILexEntryRef: The newly created entry reference

        Example:
            >>> # Create a compound "blackboard" from "black" + "board"
            >>> blackboard = project.LexEntry.Create("blackboard", "stem")
            >>> black = project.LexEntry.Find("black")
            >>> board = project.LexEntry.Find("board")
            >>> # Would need complex_form_type from project
            >>> # ref = project.LexiconAddComplexForm(blackboard, [black, board], cf_type)

        Note:
            Creates an entry reference linking the complex form to its components.
        """
        from SIL.LCModel import ILexEntryRefFactory, LexEntryRefTags

        with self._TransactionCM(f"Add complex form ({len(components)} component(s))"):
            factory = self.GetFactory(ILexEntryRefFactory)
            entry_ref = factory.Create()
            entry.EntryRefsOS.Add(entry_ref)

            # RefType MUST be set explicitly. A freshly created
            # ILexEntryRef leaves it at 0 == krtVariant, so omitting this
            # filed the components under a VARIANT reference and the
            # entry was never a complex form at all -- which is why
            # LexEntry.GetComplexFormComponents(), which filters on
            # krtComplexForm, could not see them. Matches
            # LexEntryOperations.AddComplexFormComponent, the sibling
            # entry point, which sets both of these. (issue #272)
            entry_ref.RefType = LexEntryRefTags.krtComplexForm
            entry_ref.HideMinorEntry = 0  # Show the complex form

            # Add components
            for component in components:
                entry_ref.ComponentLexemesRS.Add(component)

            # Set complex form type
            if complex_form_type:
                entry_ref.ComplexEntryTypesRS.Add(complex_form_type)

            return entry_ref

    # --- Lexical Relations ---

    def GetLexicalRelationTypes(self):
        """
        Returns an iterator over `LexRefType` objects, which define a
        type of lexical relation, such as Part-Whole.

        Each `LexRefType` has:
            - `MembersOC`: containing zero or more `LexReference` objects.
            - `MappingType`: an enumeration defining the type of lexical relation.

        `LexReference` objects have:
            - `TargetsRS`: the `LexSense` or `LexEntry` objects in the relation.

        For example::

            for lrt in project.GetLexicalRelationTypes():
                if (lrt.MembersOC.Count > 0):
                    for lr in lrt.MembersOC:
                        for target in lr.TargetsRS:
                            if target.ClassName == "LexEntry":
                                # LexEntry
                            else:
                                # LexSense

        .. note::
           This method delegates to :meth:`LexReferenceOperations.GetAllTypes`.
        """
        return self.LexReferences.GetAllTypes()

    # --- Publications ---

    def GetPublications(self):
        """
        Returns a list of the names of the publications defined in the
        project.

        .. note::
           This method delegates to :meth:`PublicationOperations.GetAll`.
        """
        return [self.Publications.GetName(pub) for pub in self.Publications.GetAll()]

    def PublicationType(self, publicationName):
        """
        Returns the `PublicationType` object (a `CmPossibility`) for the
        given publication name. (A list of publication names can be
        found using `GetPublications()`.)

        .. note::
           This method delegates to :meth:`PublicationOperations.Find`.
        """
        return self.Publications.Find(publicationName)

    # --- Texts ---

    def TextsNumberOfTexts(self):
        """
        Returns the total number of texts in the project.

        Note: This method delegates to TextOperations.GetAll() for single source of truth.
        """

        return sum(1 for _ in self.Texts.GetAll())

    def TextsGetAll(self, supplyName=True, supplyText=True):
        """
        A generator that returns all the texts in the project as
        tuples of (`name`, `text`) where:

            - `name` is the best vernacular or analysis name.
            - `text` is a string with newlines separating paragraphs.

        Passing `supplyName`/`Text` = `False` returns only the texts or names.

        Note: This method now delegates to TextOperations.GetAll() for retrieving texts.
        """

        if not supplyText:
            for t in self.Texts.GetAll():
                yield ITsString(t.Name.BestVernacularAnalysisAlternative).Text
        else:
            for t in self.Texts.GetAll():
                content = []
                if t.ContentsOA:
                    for p in t.ContentsOA.ParagraphsOS:
                        if para := ITsString(IStTxtPara(p).Contents).Text:
                            content.append(para)

                if supplyName:
                    name = ITsString(t.Name.BestVernacularAnalysisAlternative).Text
                    yield name, "\n".join(content)
                else:
                    yield "\n".join(content)


# ============================================================================
# Operation-namespace naming aliases (issue #200)
# ============================================================================
# Deprecated singular/plural aliases for the operation-namespace accessors are
# generated from a single table in the SIL-free ._op_aliases module and
# attached here. Each alias forwards to the canonical accessor and emits a
# DeprecationWarning. Keeping the table and generator SIL-free lets them be
# unit-tested without FieldWorks (tests/test_flexproject_aliases.py).
from ._op_aliases import (  # noqa: E402
    OP_NAMESPACE_ALIASES as _OP_NAMESPACE_ALIASES,
    install_op_namespace_aliases as _install_op_namespace_aliases,
)

FLExProject._OP_NAMESPACE_ALIASES = _OP_NAMESPACE_ALIASES
_install_op_namespace_aliases(FLExProject)
