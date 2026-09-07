#
#   lcm_constants.py
#
#   LCM API constants and property type definitions.
#   Centralizes constants used across the flexicon codebase.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""LCM API constants and property type definitions."""

# LibLCM property suffixes
# (from PythonicWrapper.py and BaseOperations.py)
# These suffixes indicate relationship types in LibLCM:
#   - OS: Owning Sequence (ordered collection of owned children)
#   - OC: Owning Collection (unordered collection of owned children)
#   - OA: Owning Atomic (single owned child)
#   - RS: Reference Sequence (ordered collection of references)
#   - RC: Reference Collection (unordered collection of references)
#   - RA: Reference Atomic (single reference)

OWNING_SEQUENCE_SUFFIX = "OS"        # e.g., SensesOS
OWNING_COLLECTION_SUFFIX = "OC"      # e.g., AllomorphsOC
OWNING_ATOMIC_SUFFIX = "OA"          # e.g., MorphoSyntaxAnalysisOA
REFERENCE_SEQUENCE_SUFFIX = "RS"     # e.g., SlotsRS
REFERENCE_COLLECTION_SUFFIX = "RC"   # e.g., ProdRestrictRC
REFERENCE_ATOMIC_SUFFIX = "RA"       # e.g., PartOfSpeechRA

# Suffixes in order of preference (most common first)
# Used by PythonicWrapper to resolve unqualified property names
SUFFIXES = (OWNING_SEQUENCE_SUFFIX, OWNING_COLLECTION_SUFFIX, OWNING_ATOMIC_SUFFIX,
            REFERENCE_SEQUENCE_SUFFIX, REFERENCE_COLLECTION_SUFFIX, REFERENCE_ATOMIC_SUFFIX)


class CellarPropertyType:
    """Type constants for LCM Cellar properties.

    These constants identify the type of each property in the LibLCM data model.
    Values match SIL.LCModel.Core.Cellar.CellarPropertyType in the C# API.

    Reference:
        SIL.LCModel.Core.Cellar.CellarPropertyType (from FLExLCM.py)
    """
    PropType_String = 2
    PropType_Integer = 6
    PropType_Boolean = 20
    PropType_MultiString = 13
    PropType_MultiUnicode = 14
    PropType_Time = 4
    PropType_Guid = 15
    PropType_GenDate = 16
    PropType_Binary = 17
    PropType_Float = 5
    PropType_Object = 23
    PropType_Sequence = 26
    PropType_ReferenceSequence = 27
    PropType_ReferenceAtomic = 28
    PropType_ReferenceCollection = 29


# ---------------------------------------------------------------------------
# Feature-structure (IFsFeatStruc) owner-property resolver table.
#
# FROZEN per specs/feature-structure-sync-gap/spec.md section 4, C1. This
# is the SINGLE, canonical source of truth for "which LCM ClassName owns an
# IFsFeatStruc under which atomic-owning ('OA') property, and under what
# sync-wire props key". It lives here (a pure-data constants module with no
# SIL.LCModel import, already the home of OWNING_ATOMIC_SUFFIX and friends)
# rather than as a BaseOperations module-level literal, for two reasons:
#   1. BaseOperations.py already imports from this module (see
#      OWNING_SEQUENCE_SUFFIX above), so adding one more constant import
#      costs nothing structurally and keeps BaseOperations.py from growing
#      a second kind of "constants block" alongside its actual methods.
#   2. Every future consumer of this table (T4's _ApplyFeatureStruc, T5's
#      generalized MakeFeatStruc, T6-T9's per-domain GetSyncableProperties/
#      ApplySyncableProperties) needs the SAME table without importing
#      BaseOperations itself just to reach a dict -- Operations classes
#      already import from Shared/ directly (see
#      InflectionFeatureOperations.py's Shared.string_utils /
#      Shared.catalog imports), so this keeps the dependency direction
#      consistent with the rest of the codebase.
#
# Keyed by LCM `ClassName` (the string `.ClassName` returns, e.g.
# "MoStemMsa"). Each value is a tuple of rows; a ClassName with exactly one
# row is unambiguous (a `slot=` argument, if supplied, is ignored -- not an
# error). A ClassName with more than one row is ambiguous and REQUIRES an
# explicit `slot=` naming one of the row's `slot` values -- never guessed.
#
# Each row is (slot, owning_property, props_key):
#   slot            -- None for an unambiguous (single-row) ClassName, else
#                       the string identifying this row among its siblings
#                       (e.g. "From"/"To" for MoDerivAffMsa).
#   owning_property -- the LCM atomic-owning ('OA') property name that
#                       holds the IFsFeatStruc (e.g. "MsFeaturesOA"). This
#                       is the `prop_name` returned by
#                       BaseOperations._ResolveFeatureStrucOwner.
#   props_key       -- the sync wire-format key (props[props_key] /
#                       props[props_key + "Guid"]), per the frozen naming
#                       rule: the owning_property name minus its "OA"
#                       suffix. Stored explicitly (not derived) so the
#                       table reads as the literal frozen spec table and
#                       so a future row that ever needed to break the
#                       naming rule would not require touching every
#                       consumer.
#
# Explicitly EXCLUDED (raise via BaseOperations._ResolveFeatureStrucOwner,
# not silently guessed): MoDerivStepMsa, LexEntryInflType, MoStemName,
# MoUnclassifiedAffixMsa (confirmed live to carry NO feature-struct
# property at all -- see evidence/live-cycle1-probe.md item 4), and
# PosFeatures / FsComplexFeature (IPosFeatures does not exist in this LCM
# version at all; FsComplexFeature owns DefaultOA, not a feature-struct
# property -- neither is a resolver row).
FEATURE_STRUC_OWNER_TABLE = {
    "MoStemMsa": (
        (None, "MsFeaturesOA", "MsFeatures"),
    ),
    "MoInflAffMsa": (
        (None, "InflFeatsOA", "InflFeats"),
    ),
    "MoDerivAffMsa": (
        ("From", "FromMsFeaturesOA", "FromMsFeatures"),
        ("To", "ToMsFeaturesOA", "ToMsFeatures"),
    ),
    "PartOfSpeech": (
        ("Default", "DefaultFeaturesOA", "DefaultFeatures"),
        ("InherFeatVal", "InherFeatValOA", "InherFeatVal"),
    ),
    "MoAffixAllomorph": (
        (None, "MsEnvFeaturesOA", "MsEnvFeatures"),
    ),
    "PhNCFeatures": (
        (None, "FeaturesOA", "Features"),
    ),
    "PhPhoneme": (
        (None, "FeaturesOA", "Features"),
    ),
    "WfiAnalysis": (
        (None, "MsFeaturesOA", "MsFeatures"),
    ),
}
