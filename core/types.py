"""
Core Type Definitions

This module provides common type definitions, type aliases, and protocols
used across all flexlibs modules.

Author: FlexTools Development Team
Date: 2025-11-22
"""

from typing import Any, Union, Optional, Protocol, TypeVar, runtime_checkable


# Type aliases for FLEx objects (to be replaced with actual imports when integrated)

# Phase 1: Text & Interlinear types
IText = Any
IStText = Any
IStTxtPara = Any
ISegment = Any
IAnalysis = Any
IWfiWordform = Any
IWfiAnalysis = Any
IWfiGloss = Any
IWfiMorphBundle = Any
ICmMedia = Any
ICmFile = Any
INote = Any
ICmBaseAnnotation = Any
ICmTranslation = Any

# Phase 2: Grammar & Morphology types
IPartOfSpeech = Any  # Parts of speech
ICmPossibility = Any  # Generic possibility list item (used for many things)
ICmPossibilityList = Any  # Lists in FLEx
IPhPhoneme = Any  # Phonemes
IPhCode = Any  # Phoneme codes/representations
IPhNaturalClass = Any  # Natural classes of phonemes
IPhEnvironment = Any  # Phonological environments
IMoForm = Any  # Morphological forms (allomorphs)
IMoMorphType = Any  # Types of morphs (prefix, suffix, etc.)
IMoMorphRule = Any  # Morphological rules
IMoStratum = Any  # Morphological strata
IMoInflClass = Any  # Inflection classes
IMoInflAffixSlot = Any  # Affix slots for templates
IFsFeatStruc = Any  # Feature structures
IFsFeatureDefn = Any  # Feature definitions
IFsSymFeatVal = Any  # Symbolic feature values
ILexEntry = Any  # Lexicon entries
ILexSense = Any  # Lexical senses
IMoMorphSynAnalysis = Any  # Morphosyntactic analysis (MSA)


# Generic type variable for objects or HVOs
ObjectOrHVO = TypeVar("ObjectOrHVO", bound=Union[Any, int])


# Writing system handle type - can be string (language tag) or int (ID)
WritingSystemHandle = Union[str, int]


# HVO type alias for clarity
HVO = int


class FlexObject(Protocol):
    """
    Protocol for FLEx objects.

    All FLEx objects have an HVO (Handle to Virtual Object) property
    that uniquely identifies them in the database.
    """

    @property
    def Hvo(self) -> int:
        """The object's HVO (database ID)."""
        ...


@runtime_checkable
class FlexProject(Protocol):
    """
    Protocol for FLEx Project objects.

    Defines the minimal interface needed for project-level operations.
    """

    def GetObject(self, hvo: int) -> Any:
        """Get an object by its HVO."""
        ...

    @property
    def DefaultVernacularWs(self) -> int:
        """Default vernacular writing system handle."""
        ...

    @property
    def DefaultAnalysisWs(self) -> int:
        """Default analysis writing system handle."""
        ...


# Common return types - Phase 1
OptionalText = Optional[IText]
OptionalParagraph = Optional[IStTxtPara]
OptionalSegment = Optional[ISegment]
OptionalWordform = Optional[IWfiWordform]
OptionalAnalysis = Optional[IWfiAnalysis]

# Common return types - Phase 2
OptionalPOS = Optional[IPartOfSpeech]
OptionalPhoneme = Optional[IPhPhoneme]
OptionalNaturalClass = Optional[IPhNaturalClass]
OptionalAllomorph = Optional[IMoForm]


__all__ = [
    # Phase 1 Type aliases
    "IText",
    "IStText",
    "IStTxtPara",
    "ISegment",
    "IAnalysis",
    "IWfiWordform",
    "IWfiAnalysis",
    "IWfiGloss",
    "IWfiMorphBundle",
    "ICmMedia",
    "ICmFile",
    "INote",
    "ICmBaseAnnotation",
    "ICmTranslation",
    # Phase 2 Type aliases
    "IPartOfSpeech",
    "ICmPossibility",
    "ICmPossibilityList",
    "IPhPhoneme",
    "IPhCode",
    "IPhNaturalClass",
    "IPhEnvironment",
    "IMoForm",
    "IMoMorphType",
    "IMoMorphRule",
    "IMoStratum",
    "IMoInflClass",
    "IMoInflAffixSlot",
    "IFsFeatStruc",
    "IFsFeatureDefn",
    "IFsSymFeatVal",
    "ILexEntry",
    "ILexSense",
    "IMoMorphSynAnalysis",
    # Generic types
    "ObjectOrHVO",
    "WritingSystemHandle",
    "HVO",
    # Protocols
    "FlexObject",
    "FlexProject",
    # Phase 1 Optional types
    "OptionalText",
    "OptionalParagraph",
    "OptionalSegment",
    "OptionalWordform",
    "OptionalAnalysis",
    # Phase 2 Optional types
    "OptionalPOS",
    "OptionalPhoneme",
    "OptionalNaturalClass",
    "OptionalAllomorph",
]
