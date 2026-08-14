#
#   exceptions.py
#
#   Module:     FlexLibs2 exception classes
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
