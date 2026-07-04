#
#   __init__.pyi
#
#   Type stubs for flexlibs2 module
#

from .code.FLExProject import (
    FLExProject,
    FP_ProjectError,
    FP_FileNotFoundError,
    FP_FileLockedError,
    FP_MigrationRequired,
    FP_ReadOnlyError,
    FP_NullParameterError,
    FP_ParameterError,
)

def FLExInitialize() -> None: ...
def FLExCleanup() -> None: ...

__all__ = [
    "FLExProject",
    "FLExInitialize",
    "FLExCleanup",
    "FP_ProjectError",
    "FP_FileNotFoundError",
    "FP_FileLockedError",
    "FP_MigrationRequired",
    "FP_ReadOnlyError",
    "FP_NullParameterError",
    "FP_ParameterError",
]
