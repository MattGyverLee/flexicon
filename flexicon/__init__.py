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

version = "4.9.0"

#: Capabilities this *build* of flexicon implements, probed with ``in``.
#:
#: Consumers (notably FlexToolsMCP) must probe defensively, because releases
#: at or below 4.3.0 do not define this name at all::
#:
#:     CAPS = getattr(flexicon, "CAPABILITIES", frozenset())
#:     if "per-operation-uow" in CAPS:
#:         ...          # post-Track-B surface
#:     else:
#:         ...          # 4.3.0 floor: session-envelope path
#:
#: Use the one-line ``getattr(..., frozenset())`` form, not a two-step
#: ``hasattr()`` check. See ``docs/FLEXTOOLSMCP_WRITE_CONTRACT.md`` section 3.
#:
#: IMPORTANT -- a token here means "this build implements the capability", NOT
#: "the capability is active in your session". Two of the four are
#: mode-dependent: they are active under ``undoable=True``, which is the
#: default since 4.4.0, and deliver nothing if a caller opts out with
#: ``undoable=False``:
#:
#:   ``"ui-injection"``        Always active. ``OpenProject(..., ui=...)``
#:                             accepts an ``ILcmUI``; defaults to a bare
#:                             ``HeadlessLcmUI()`` since issue #285 (a
#:                             conflicting save raises
#:                             ``FP_ConflictingSaveError`` rather than
#:                             blocking on or silently discarding through
#:                             the historical ``FwLcmUI``, which remains
#:                             reachable by passing it explicitly).
#:   ``"refresh-from-disk"``   Always active. ``FLExProject.RefreshFromDisk()``
#:                             wraps ``IUndoStackManager.Refresh()``; needed in
#:                             BOTH modes, since one foreign FLEx save otherwise
#:                             wedges auto-save for the rest of the session.
#:   ``"per-operation-uow"``   Requires ``undoable=True`` (the default). Every
#:                             LCM mutation runs inside a named, nesting-aware
#:                             unit of work. If a caller opts out with
#:                             ``undoable=False`` the atomicity unit is
#:                             the whole SESSION, not the operation.
#:   ``"transaction-rollback"``Requires ``undoable=True`` (the default). An
#:                             exception escaping
#:                             a transaction reverts that operation's mutations
#:                             via ``UndoableUnitOfWorkHelper``'s ``Rollback(0)``.
#:                             Under ``undoable=False`` there is NO rollback --
#:                             liblcm exposes no reachable rollback-to-mark API
#:                             in that mode (issue #236), and mutations applied
#:                             before a failure are still written to disk by
#:                             ``CloseProject()``.
#:
#: ``OpenProject()`` already warns once per call when ``writeEnabled=True`` is
#: combined with an explicit ``undoable=False``, so the mode dependence is
#: surfaced at the boundary where the mode is chosen as well as here.
#:
#: ``parser`` is mode-independent but MACHINE-dependent, and the distinction
#: matters more here than for the four above. The token says this build ships
#: ``project.Parser``; it says NOTHING about whether the machine reading it
#: can reach a parser, because that depends on a FieldWorks component this
#: package does not install and deliberately does not require. A consumer
#: must therefore PROBE rather than infer::
#:
#:     if "parser" in getattr(flexicon, "CAPABILITIES", frozenset()):
#:         status = project.Parser.GetAvailability()   # ask the machine
#:         if status.available:
#:             ...
#:
#: Treating the token as "a parser is available" is the one misreading that
#: turns a degrade-with-a-reason into a crash.
CAPABILITIES = frozenset({
    "ui-injection",
    "refresh-from-disk",
    "per-operation-uow",
    "transaction-rollback",
    "parser",
})

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

# HeadlessLcmUI (issue #285): the non-blocking, non-destructive ILcmUI that
# OpenProject(..., ui=None) now defaults to. Exported at the top level so a
# consumer that catches FP_ConflictingSaveError can also reach the class that
# raises it, without reaching into flexicon.code.* -- same precedent as
# cast_to_concrete (#271). Re-exported, not redefined: this is the same
# object as flexicon.code.headless_ui.HeadlessLcmUI, which keeps working.
#
# By the time this line runs, flexicon.code.FLExLCM (imported just above via
# FLExProject -> FLExLCM) has already imported flexicon.code.headless_ui at
# module level, so this import is a sys.modules cache hit, not a fresh CLR
# type emission -- see specs/285-headless-ui-default/reviews/cycle1-programmer.md.
from .code.headless_ui import HeadlessLcmUI

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
#
# Reachable only via project.X accessors before now; exporting them here
# closes issue #257's ImportError for `from flexicon import X` on these
# classes (along with MSAOperations, PhonFeatureOperations,
# StratumOperations, LocalizedListsOperations, and the ConstChart*
# Operations classes below).
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

# Parser Operations -- READ-ONLY access to the FieldWorks morphological
# parser. Importing this module never touches ParserCore.dll: the component
# probe is deferred to the first GetAvailability() call, so `import flexicon`
# still succeeds on a machine with no parser (FR-003).
from .code.Parser.ParserOperations import (
    ParserOperations,
)

# Pythonic Wrapper - suffix-free property access
from .code.PythonicWrapper import (
    wrap,
    unwrap,
    p,
    PythonicWrapper,
)

# LCM casting escape hatch -- public since #271.
#
# `cast_to_concrete` is the supported remedy for the
# `'ICmObject' object has no attribute 'X'` failure class. flexicon's own
# Operations classes cast internally, so most callers never need it; it is
# exported for direct-LCM work and for collections that stay legitimately
# polymorphic (e.g. `ComponentLexemesRS`, which legally mixes ILexEntry and
# ILexSense elements).
#
# Eager import is safe: lcm_casting imports only `logging` at module scope
# and defers every `SIL.LCModel` import into a lazy `_ensure_interfaces()`
# call made on first use, so `import flexicon` still works on a machine
# with no FieldWorks installed. The module is already loaded transitively
# by BaseOperations, so this adds no import cost.
from .code.lcm_casting import (
    cast_to_concrete,
)

# __all__ -- the explicit public surface, per constitution Principle VII's
# "Published means..." clause. This is exactly the set of module-level
# names bound above that do not start with an underscore (i.e. exactly what
# `from flexicon import *` already exposes); it intentionally does not
# narrow that set. See specs/constitution-v2-amendment/reviews/
# cycle2-all-exports.md for the derivation and candidates flagged for a
# future gated removal.
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
    "ParserOperations",
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
