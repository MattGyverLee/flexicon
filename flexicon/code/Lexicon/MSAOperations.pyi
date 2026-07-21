#
#   MSAOperations.pyi
#
#   Type stubs for MSAOperations
#

from typing import Any
from ..BaseOperations import BaseOperations

class MSAOperations(BaseOperations[Any]):
    """
    Creation + attach operations for morphosyntactic analyses (MSAs).

    Unlike most Operations classes, MSAOperations exposes no GetAll/Find/
    Create/Delete surface -- MSAs are owned per-entry (not top-level
    enumerable) and are created/attached through the Create*/Set* helpers
    below. The common Operations surface is inherited from BaseOperations.
    See msa_collection.MSACollection for the read/iteration side.
    """

    def __init__(self, project: Any) -> None: ...

    # Create + attach a new MSA to a sense (returns the new LCM MSA object).
    def CreateStem(self, sense: Any, pos: Any) -> Any: ...
    def CreateDerivAff(self, sense: Any, from_pos: Any, to_pos: Any = None) -> Any: ...
    def CreateInflAff(self, sense: Any, pos: Any, slots: Any = None) -> Any: ...
    def CreateUnclassifiedAffix(self, sense: Any, pos: Any) -> Any: ...

    # Update POS on an existing MSA in place (mutators; return None).
    def SetStemMsaPos(self, sense: Any, pos: Any) -> None: ...
    def SetDerivAffMsaPos(self, sense: Any, from_pos: Any = None, to_pos: Any = None) -> None: ...

    # Convert an affix MSA to a different affix variant (returns the MSA).
    def ChangeAffixVariant(self, msa: Any, target_kind: str) -> Any: ...

    # Remove orphaned MSAs (unreferenced by senses and morph bundles).
    # Returns a RemoveOrphanedResult namedtuple; see MSAOperations.py.
    def RemoveOrphaned(self, entry: Any = None, progress: Any = None) -> Any: ...
