# ----------------------------------------------------------------------------
# Name:         flexicon
# Purpose:      This package provides a Python interface to FLEx project data
#               via the Fieldworks Language and Culture Model (LCM).
#
#               flexicon began as a fork of cdfarrow/flexlibs (LGPL-2.1) and is
#               now an independent successor library with an extensively
#               reshaped, user-centric API. The legacy `flexlibs2` import name
#               is preserved as a deprecated alias (removed in v5.0.0).
#
#   Platform:   Python.NET, FieldWorks 9+
#   License:    LGPL-2.1-or-later  (see LICENSE.txt)
# ----------------------------------------------------------------------------

version = "4.3.0"

# Define exported classes, etc. at the top level of the package

from .code.FLExInit import (
    FLExInitialize,
    FLExCleanup,
)

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

# Advanced Operations (v2.0+)

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

# Pythonic Wrapper - suffix-free property access
from .code.PythonicWrapper import (
    wrap,
    unwrap,
    p,
    PythonicWrapper,
)
