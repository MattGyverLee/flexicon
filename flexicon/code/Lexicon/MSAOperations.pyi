#
#   MSAOperations.pyi
#
#   Type stubs for MSAOperations
#

from typing import Any, Optional
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

    # Owning entry navigation (issue #581): climbs the ownership chain
    # to the nearest ILexEntry; None (never raises) when there is none.
    def GetOwningEntry(self, msa_or_hvo: Any) -> Optional[Any]: ...

    # Create + attach a new MSA to a sense (returns the new LCM MSA object).
    def CreateStem(self, sense: Any, pos: Any) -> Any: ...
    def CreateDerivAff(self, sense: Any, from_pos: Any, to_pos: Any = None) -> Any: ...
    def CreateInflAff(self, sense: Any, pos: Any, slots: Any = None) -> Any: ...
    def CreateUnclassifiedAffix(self, sense: Any, pos: Any) -> Any: ...

    # Update POS on an existing MSA in place (mutators; return None).
    def SetStemMsaPos(self, sense: Any, pos: Any, keep_inflection_class: bool = True) -> None: ...
    def SetDerivAffMsaPos(self, sense: Any, from_pos: Any = None, to_pos: Any = None) -> None: ...
    def SetInflAffMsaSlots(self, sense: Any, slots: Any, replace: bool = True) -> None: ...
    def GetInflAffMsaSlots(self, sense_or_msa: Any) -> list: ...

    # MSA display-name + type discrimination (issue #575). GetLongName
    # reads the LongName LCM property, normalizing "***" to "". GetMSAType
    # maps ClassName to one of "stem"/"inflectional"/"derivational"/
    # "unclassified" (raw ClassName fallback for unrecognized subtypes).
    def GetLongName(self, msa_or_hvo: Any) -> str: ...
    def GetMSAType(self, msa_or_hvo: Any) -> str: ...
    # Stem-MSA inflection-class accessors (issue #573). Get returns the
    # IMoInflClass or None (never raises on a non-stem MSA). Set validates
    # the class against the MSA's POS parent chain and raises
    # FP_ParameterError on mismatch; None clears.
    def GetInflectionClass(self, msa_or_hvo: Any) -> Any: ...
    def SetInflectionClass(self, msa_or_hvo: Any, infl_class_or_hvo_or_None: Any) -> None: ...

    # MSA exception features (issue #574). GetExceptionFeatures reads
    # ProdRestrictRC ("Exception features" in FLEx) as ICmPossibility
    # objects; Add/RemoveExceptionFeature edit the collection. Only
    # MoStemMsa / MoInflAffMsa / MoDerivAffMsa carry ProdRestrictRC.
    def GetExceptionFeatures(self, msa_or_hvo: Any) -> list: ...
    def AddExceptionFeature(self, msa_or_hvo: Any, feature_or_hvo: Any) -> None: ...
    def RemoveExceptionFeature(self, msa_or_hvo: Any, feature_or_hvo: Any) -> None: ...

    # Feature-structure getters (issue #544): reverse of
    # InflectionFeatures.MakeFeatStruc. Return a MakeFeatStruc-shaped
    # {featureGuid: valueGuid | {...}} spec, or None (no MSA / wrong
    # MSA class / null owning property) or {} (present-but-empty struct).
    def GetStemFeatures(self, sense_or_msa: Any) -> Any: ...
    def GetInflAffFeatures(self, sense_or_msa: Any) -> Any: ...
    def GetDerivFromFeatures(self, sense_or_msa: Any) -> Any: ...
    def GetDerivToFeatures(self, sense_or_msa: Any) -> Any: ...
    def GetFeatures(self, sense_or_msa: Any, slot: Any = None) -> Any: ...

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
