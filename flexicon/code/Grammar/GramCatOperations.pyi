#
#   GramCatOperations.pyi
#
#   Type stubs for GramCatOperations, a deprecated alias of POSOperations
#   (issue #276). Only the constructor and the Create override are declared;
#   every other member is inherited from POSOperations and must NOT be
#   re-declared here -- the previous stub advertised Find/Exists that the
#   .py never defined, so the stub promised a surface that raised
#   AttributeError at runtime.
#

from typing import Any, NoReturn, Optional

from .POSOperations import POSOperations

class GramCatOperations(POSOperations):
    """Deprecated alias of POSOperations; use project.POS (issue #276)."""

    def __init__(self, project: Any) -> None: ...
    def Create(self, name: Any, parent: Optional[Any] = None) -> NoReturn: ...
