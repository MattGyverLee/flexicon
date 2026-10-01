#
#   exceptions.py
#
#   Module:     Flexicon exception classes
#
#   Copyright 2025
#

"""FLExProject exception hierarchy for error handling and reporting."""


class FP_ProjectError(Exception):
    """Exception raised for any problems opening the project.

    Attributes:
        - message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class FP_FileNotFoundError(FP_ProjectError):
    def __init__(self, projectName, e):
        # Normally this will be a mispelled/wrong project name...
        if projectName in str(e):
            message = "Project file not found: %s" % projectName
        # ...however, it could be an internal FLEx error.
        else:
            message = "File not found error: %s" % e
        super().__init__(message)


class FP_FileLockedError(FP_ProjectError):
    def __init__(self):
        message = (
            "This project is in use by another program. To allow shared access to this project, "
            "turn on the sharing option in the Sharing tab of the Fieldworks Project Properties dialog."
        )
        super().__init__(message)


class FP_MigrationRequired(FP_ProjectError):
    def __init__(self):
        message = "This project needs to be opened in FieldWorks in order for it to be migrated to the latest format."
        super().__init__(message)


# Runtime errors


class FP_RuntimeError(Exception):
    """Exception raised for any problems running the module.

    Attributes:
        - message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class FP_ReadOnlyError(FP_RuntimeError):
    def __init__(self):
        message = "Trying to write to the project database without changes enabled."
        super().__init__(message)


class FP_WritingSystemError(FP_RuntimeError):
    def __init__(self, writingSystemName):
        message = "Invalid Writing System for this project: %s" % writingSystemName
        super().__init__(message)


class FP_NullParameterError(FP_RuntimeError):
    def __init__(self):
        super().__init__("Null parameter.")


class FP_ParameterError(FP_RuntimeError):
    def __init__(self, msg):
        super().__init__(msg)


class FP_TransactionError(FP_RuntimeError):
    def __init__(self, message):
        super().__init__(message)


class FP_DeduplicationError(FP_RuntimeError):
    """Raised when duplicate items were detected but could not all be removed."""

    def __init__(self, item_kind, entry_hvo, found, removed, cause=None):
        message = (
            f"Deduplication of {item_kind} in entry (HVO: {entry_hvo}) found "
            f"{found} duplicate(s) but removed only {removed}"
            + (f": {cause}" if cause else ".")
        )
        super().__init__(message)


class FP_ExclusiveAccessRequiredError(FP_RuntimeError):
    """
    Raised when a writing-system or custom-field schema change would run while
    this session is attached to a project that FieldWorks has open in shared
    mode, and the peer schema guard is on (``FLExProject.SetPeerSchemaGuard``).

    From a shared-mode peer, writing-system changes crash the FieldWorks that
    holds the project, and custom-field definitions are never persisted (the
    commit log carries only object changes). The guard raises BEFORE anything
    is written, so nothing needs undoing. Idempotent calls that turn out to be
    no-ops (``WritingSystems.Ensure`` on an already-active tag) do not raise.

    Attributes:
        - operation -- the wrapper call that was refused, e.g.
          ``"WritingSystems.Ensure('qaa-x-new')"``
        - message -- explanation, including the recovery steps
    """

    def __init__(self, operation):
        self.operation = operation
        message = (
            f"{operation} needs to change the project's writing systems or "
            "custom fields, which is not safe while FieldWorks has the project "
            "open. Nothing was written by this call. Close FieldWorks, re-run, "
            "then reopen FieldWorks."
        )
        super().__init__(message)


class FP_ConflictingSaveError(FP_RuntimeError):
    """
    Raised when LCM reports that another client saved changes which cannot be
    reconciled with this session's unsaved changes.

    Raised by ``flexicon.code.headless_ui.HeadlessLcmUI.ConflictingSave()``.
    Raising is deliberate: the alternatives LCM offers are to block on a
    modal dialog or to discard the caller's unsaved work; neither is
    acceptable unattended. The caller is expected to abandon or retry the
    operation.

    Subclasses ``FP_RuntimeError`` (rather than ``FP_ProjectError``) because
    the condition is discovered mid-session, on a save that occurs after the
    project is already open and in use -- it is a runtime failure of an
    in-progress write, not a problem opening the project.
    """

    def __init__(self, message):
        super().__init__(message)
