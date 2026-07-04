#
#   lcm_constants.py
#
#   LCM API constants and property type definitions.
#   Centralizes constants used across the flexlibs2 codebase.
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
