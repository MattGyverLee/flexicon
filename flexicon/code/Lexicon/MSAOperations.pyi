#
#   MSAOperations.pyi
#
#   Type stubs for MSAOperations
#

from typing import Any
from ..BaseOperations import BaseOperations
from .msa_collection import MSACollection

class MSAOperations(BaseOperations[Any]):
    """
    Read, creation and attach operations for morphosyntactic analyses (MSAs).

    MSAs are owned per-entry rather than being top-level enumerable, so
    GetAll takes the owning entry (or None to sweep the project) and
    returns an MSACollection of MorphosyntaxAnalysis wrappers. Creation and
    attachment go through the Create*/Set* helpers below. The rest of the
    common Operations surface is inherited from BaseOperations.

    This class is write-capable: everything below GetAll mutates the
    project and requires a write-enabled FLExProject.
    """

    def __init__(self, project: Any) -> None: ...

    # Read every MSA owned by an entry (or, with None, by the project).
    # Not @wrap_enumerable-decorated: MSACollection already supplies
    # __len__/__getitem__/__iter__, so the decorator would be a no-op.
    def GetAll(self, entry_or_hvo: Any = None) -> MSACollection: ...

    # Create + attach a new MSA to a sense (returns the new LCM MSA object).
    def CreateStem(self, sense: Any, pos: Any) -> Any: ...
    def CreateDerivAff(self, sense: Any, from_pos: Any, to_pos: Any = None) -> Any: ...
    def CreateInflAff(self, sense: Any, pos: Any, slots: Any = None) -> Any: ...
    def CreateUnclassifiedAffix(self, sense: Any, pos: Any) -> Any: ...

    # Update POS on an existing MSA in place (mutators; return None).
    def SetStemMsaPos(self, sense: Any, pos: Any) -> None: ...
    def SetDerivAffMsaPos(self, sense: Any, from_pos: Any = None, to_pos: Any = None) -> None: ...
    def SetInflAffMsaSlots(self, sense: Any, slots: Any, replace: bool = True) -> None: ...

    # Convert an affix MSA to a different affix variant (returns the MSA).
    def ChangeAffixVariant(self, msa: Any, target_kind: str) -> Any: ...

    # Remove orphaned MSAs (unreferenced by senses and morph bundles).
    # Returns a RemoveOrphanedResult namedtuple; see MSAOperations.py.
    def RemoveOrphaned(self, entry: Any = None, progress: Any = None) -> Any: ...

    # Sync integration (issue #251): feature-struct capture/apply for the
    # four C1 MSA rows (MsFeaturesOA / InflFeatsOA / From+ToMsFeaturesOA).
    def GetSyncableProperties(self, item: Any) -> dict: ...
    def ApplySyncableProperties(
        self, item: Any, props: dict, ws_map: Any = None, fill_gaps: bool = False
    ) -> None: ...
