#
#   ParserOperations.pyi
#
#   Type stubs for ParserOperations -- READ-ONLY access to the FieldWorks
#   morphological parser.
#
#   Hand-written, not generated. The surface is deliberately small and
#   deliberately closed: tests/test_parser_offline.py (A1.4) asserts the
#   public surface by SET EQUALITY, so an addition here without a matching
#   contract change is a failure, not a convenience.
#

from typing import Any, Iterable, Optional

from ..BaseOperations import BaseOperations

class ParserAvailability:
    """Whether this project can reach the parser, and why not if it cannot."""

    available: bool
    reason: str
    version: Optional[str]
    def __init__(self, available: bool, reason: str, version: Optional[str] = ...) -> None: ...

class ParserOperations(BaseOperations[Any]):
    """READ-ONLY parser operations. No method here records or files a result."""

    def GetAvailability(self) -> ParserAvailability: ...
    def ParseWord(self, word: str) -> Any: ...
    def ParseWordXml(self, word: str) -> Any: ...
    # analyses=None traces without restriction. An EMPTY iterable is refused
    # (FP_ParameterError): the component reads an empty restriction as
    # "admit nothing", which is the opposite of "no restriction".
    def TraceWordXml(self, word: str, analyses: Optional[Iterable[int]] = ...) -> Any: ...
    def Reload(self) -> None: ...
    def IsUpToDate(self) -> bool: ...
    def __getattr__(self, name: str) -> Any: ...
