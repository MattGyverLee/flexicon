#
#   __init__.pyi
#
#   Module: Type stubs for the flexicon package.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

version: str
CAPABILITIES: frozenset[str]

def FLExInitialize() -> None: ...
def FLExCleanup() -> None: ...

from .code.FLExGlobals import (
    FWCodeDir,
    FWProjectsDir,
    FWExecutable,
    FWShortVersion,
    FWLongVersion,
    APIHelpFile,
)

from .code.FLExProject import (
    AllProjectNames,
    OpenProjectInFW,
    FLExProject,
    FP_ConflictingSaveError,
    FP_FileLockedError,
    FP_FileNotFoundError,
    FP_MigrationRequired,
    FP_NullParameterError,
    FP_ParameterError,
    FP_ProjectError,
    FP_ReadOnlyError,
    FP_RuntimeError,
    FP_TransactionError,
    FP_WritingSystemError,
)

from .code.headless_ui import HeadlessLcmUI

# Grammar Operations
from .code.Grammar.POSOperations import (
    POSOperations,
)

from .code.Grammar.PhonemeOperations import (
    PhonemeOperations,
)

from .code.Grammar.NaturalClassOperations import (
    NaturalClassOperations,
)

from .code.Grammar.EnvironmentOperations import (
    EnvironmentOperations,
)

from .code.Grammar.MorphRuleOperations import (
    MorphRuleOperations,
)

from .code.Grammar.InflectionFeatureOperations import (
    InflectionFeatureOperations,
)

from .code.Grammar.GramCatOperations import (
    GramCatOperations,
)

from .code.Grammar.PhonologicalRuleOperations import (
    PhonologicalRuleOperations,
)

from .code.Grammar.PhonFeatureOperations import (
    PhonFeatureOperations,
)

from .code.Grammar.StratumOperations import (
    StratumOperations,
)

# Lexicon Operations
from .code.Lexicon.LexEntryOperations import (
    LexEntryOperations,
)

from .code.Lexicon.LexSenseOperations import (
    LexSenseOperations,
)

from .code.Lexicon.ExampleOperations import (
    ExampleOperations,
)

from .code.Lexicon.LexReferenceOperations import (
    LexReferenceOperations,
)

from .code.Lexicon.VariantOperations import (
    VariantOperations,
)

from .code.Lexicon.PronunciationOperations import (
    PronunciationOperations,
)

from .code.Lexicon.SemanticDomainOperations import (
    SemanticDomainOperations,
)

from .code.Lexicon.EtymologyOperations import (
    EtymologyOperations,
)

from .code.Lexicon.AllomorphOperations import (
    AllomorphOperations,
)

from .code.Lexicon.MSAOperations import (
    MSAOperations,
)

# TextsWords Operations
from .code.TextsWords.TextOperations import (
    TextOperations,
)

from .code.TextsWords.WordformOperations import (
    WordformOperations,
    SpellingStatusStates,
)

from .code.TextsWords.WfiAnalysisOperations import (
    WfiAnalysisOperations,
    ApprovalStatusTypes,
)

from .code.TextsWords.ParagraphOperations import (
    ParagraphOperations,
)

from .code.TextsWords.SegmentOperations import (
    SegmentOperations,
)

from .code.TextsWords.WfiGlossOperations import (
    WfiGlossOperations,
)

from .code.TextsWords.WfiMorphBundleOperations import (
    WfiMorphBundleOperations,
)

from .code.Shared.MediaOperations import (
    MediaOperations,
    MediaType,
)

from .code.Shared.FilterOperations import (
    FilterOperations,
)

from .code.Shared.string_utils import (
    normalize_text,
    is_empty_text,
    best_analysis_text,
    best_vernacular_text,
    best_text,
    FLEX_NULL_MARKER,
)

from .code.Shared.rule_patterns import (
    Seg,
    NC,
    Boundary,
)

from .code.TextsWords.DiscourseOperations import (
    DiscourseOperations,
)

# Notebook Operations
from .code.Notebook.NoteOperations import (
    NoteOperations,
)

from .code.Notebook.PersonOperations import (
    PersonOperations,
)

from .code.Notebook.LocationOperations import (
    LocationOperations,
)

from .code.Notebook.AnthropologyOperations import (
    AnthropologyOperations,
)

from .code.Notebook.DataNotebookOperations import (
    DataNotebookOperations,
)

# Lists Operations
from .code.Lists.PublicationOperations import (
    PublicationOperations,
)

from .code.Lists.AgentOperations import (
    AgentOperations,
)

from .code.Lists.ConfidenceOperations import (
    ConfidenceOperations,
)

from .code.Lists.OverlayOperations import (
    OverlayOperations,
)

from .code.Lists.TranslationTypeOperations import (
    TranslationTypeOperations,
)

from .code.Lists.PossibilityListOperations import (
    PossibilityListOperations,
)

from .code.Lists.LocalizedListsOperations import (
    LocalizedListsOperations,
)

# System Operations
from .code.System.WritingSystemOperations import (
    WritingSystemOperations,
)

from .code.System.ProjectSettingsOperations import (
    ProjectSettingsOperations,
)

from .code.System.AnnotationDefOperations import (
    AnnotationDefOperations,
)

from .code.System.CheckOperations import (
    CheckOperations,
)

from .code.System.CustomFieldOperations import (
    CustomFieldOperations,
)

# Reversal Operations
from .code.Reversal.ReversalIndexOperations import (
    ReversalIndexOperations,
)

from .code.Reversal.ReversalIndexEntryOperations import (
    ReversalIndexEntryOperations,
)

# Discourse (constituent chart) Operations
from .code.Discourse.ConstChartOperations import (
    ConstChartOperations,
)

from .code.Discourse.ConstChartRowOperations import (
    ConstChartRowOperations,
)

from .code.Discourse.ConstChartCellTagOperations import (
    ConstChartCellTagOperations,
)

from .code.Discourse.ConstChartMarkerOperations import (
    ConstChartMarkerOperations,
)

from .code.Discourse.ConstChartClauseMarkerOperations import (
    ConstChartClauseMarkerOperations,
)

from .code.Discourse.ConstChartWordGroupOperations import (
    ConstChartWordGroupOperations,
)

from .code.Discourse.ConstChartMovedTextOperations import (
    ConstChartMovedTextOperations,
)

# Pythonic Wrapper - suffix-free property access
from .code.PythonicWrapper import (
    wrap,
    unwrap,
    p,
    PythonicWrapper,
)

# LCM casting escape hatch -- public since #271.
from .code.lcm_casting import (
    cast_to_concrete,
)

__all__ = [
    "APIHelpFile",
    "AgentOperations",
    "AllProjectNames",
    "AllomorphOperations",
    "AnnotationDefOperations",
    "AnthropologyOperations",
    "ApprovalStatusTypes",
    "Boundary",
    "CAPABILITIES",
    "CheckOperations",
    "ConfidenceOperations",
    "ConstChartCellTagOperations",
    "ConstChartClauseMarkerOperations",
    "ConstChartMarkerOperations",
    "ConstChartMovedTextOperations",
    "ConstChartOperations",
    "ConstChartRowOperations",
    "ConstChartWordGroupOperations",
    "CustomFieldOperations",
    "DataNotebookOperations",
    "DiscourseOperations",
    "EnvironmentOperations",
    "EtymologyOperations",
    "ExampleOperations",
    "FLEX_NULL_MARKER",
    "FLExCleanup",
    "FLExInitialize",
    "FLExProject",
    "FP_ConflictingSaveError",
    "FP_FileLockedError",
    "FP_FileNotFoundError",
    "FP_MigrationRequired",
    "FP_NullParameterError",
    "FP_ParameterError",
    "FP_ProjectError",
    "FP_ReadOnlyError",
    "FP_RuntimeError",
    "FP_TransactionError",
    "FP_WritingSystemError",
    "FWCodeDir",
    "FWExecutable",
    "FWLongVersion",
    "FWProjectsDir",
    "FWShortVersion",
    "FilterOperations",
    "GramCatOperations",
    "HeadlessLcmUI",
    "InflectionFeatureOperations",
    "LexEntryOperations",
    "LexReferenceOperations",
    "LexSenseOperations",
    "LocalizedListsOperations",
    "LocationOperations",
    "MSAOperations",
    "MediaOperations",
    "MediaType",
    "MorphRuleOperations",
    "NC",
    "NaturalClassOperations",
    "NoteOperations",
    "OpenProjectInFW",
    "OverlayOperations",
    "POSOperations",
    "ParagraphOperations",
    "PersonOperations",
    "PhonFeatureOperations",
    "PhonemeOperations",
    "PhonologicalRuleOperations",
    "PossibilityListOperations",
    "ProjectSettingsOperations",
    "PronunciationOperations",
    "PublicationOperations",
    "PythonicWrapper",
    "ReversalIndexEntryOperations",
    "ReversalIndexOperations",
    "Seg",
    "SegmentOperations",
    "SemanticDomainOperations",
    "SpellingStatusStates",
    "StratumOperations",
    "TextOperations",
    "TranslationTypeOperations",
    "VariantOperations",
    "WfiAnalysisOperations",
    "WfiGlossOperations",
    "WfiMorphBundleOperations",
    "WordformOperations",
    "WritingSystemOperations",
    "best_analysis_text",
    "best_text",
    "best_vernacular_text",
    "cast_to_concrete",
    "is_empty_text",
    "normalize_text",
    "p",
    "unwrap",
    "version",
    "wrap",
]
