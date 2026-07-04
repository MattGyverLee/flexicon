#
#   FLExProject.pyi
#
#   Type stubs for FLExProject
#   Provides type hints for Pylance and IDE support
#
#   Platform: Python 3.8+
#   FieldWorks Version 9+
#
#   Copyright 2025
#

from typing import Any, Optional, Iterator, Union, List
from .Grammar.POSOperations import POSOperations
from .Grammar.PhonemeOperations import PhonemeOperations
from .Grammar.NaturalClassOperations import NaturalClassOperations
from .Grammar.EnvironmentOperations import EnvironmentOperations
from .Grammar.AllomorphOperations import AllomorphOperations
from .Grammar.MorphRuleOperations import MorphRuleOperations
from .Grammar.InflectionFeatureOperations import InflectionFeatureOperations
from .Grammar.GramCatOperations import GramCatOperations
from .Grammar.PhonologicalRuleOperations import PhonologicalRuleOperations
from .Lexicon.LexEntryOperations import LexEntryOperations
from .Lexicon.LexSenseOperations import LexSenseOperations
from .Lexicon.ExampleOperations import ExampleOperations
from .Lexicon.LexReferenceOperations import LexReferenceOperations
from .Lexicon.ReversalOperations import ReversalOperations
from .Lexicon.SemanticDomainOperations import SemanticDomainOperations
from .Lexicon.PronunciationOperations import PronunciationOperations
from .Lexicon.VariantOperations import VariantOperations
from .Lexicon.EtymologyOperations import EtymologyOperations
from .TextsWords.TextOperations import TextOperations
from .TextsWords.ParagraphOperations import ParagraphOperations
from .TextsWords.SegmentOperations import SegmentOperations
from .TextsWords.WordformOperations import WordformOperations
from .TextsWords.WfiAnalysisOperations import WfiAnalysisOperations
from .TextsWords.WfiGlossOperations import WfiGlossOperations
from .TextsWords.WfiMorphBundleOperations import WfiMorphBundleOperations
from .TextsWords.MediaOperations import MediaOperations
from .TextsWords.DiscourseOperations import DiscourseOperations
from .TextsWords.FilterOperations import FilterOperations
from .Notebook.NoteOperations import NoteOperations
from .Notebook.PersonOperations import PersonOperations
from .Notebook.LocationOperations import LocationOperations
from .Notebook.AnthropologyOperations import AnthropologyOperations
from .Notebook.DataNotebookOperations import DataNotebookOperations
from .Lists.PossibilityListOperations import PossibilityListOperations
from .Lists.PublicationOperations import PublicationOperations
from .Lists.TranslationTypeOperations import TranslationTypeOperations
from .Lists.OverlayOperations import OverlayOperations
from .Lists.ConfidenceOperations import ConfidenceOperations
from .Lists.AgentOperations import AgentOperations
from .System.WritingSystemOperations import WritingSystemOperations
from .System.CustomFieldOperations import CustomFieldOperations
from .System.ProjectSettingsOperations import ProjectSettingsOperations
from .System.AnnotationDefOperations import AnnotationDefOperations
from .System.CheckOperations import CheckOperations

# Exception classes
class FP_ProjectError(Exception):
    message: str
    def __init__(self, message: str) -> None: ...

class FP_FileNotFoundError(FP_ProjectError): ...
class FP_FileLockedError(FP_ProjectError): ...
class FP_MigrationRequired(FP_ProjectError): ...
class FP_ReadOnlyError(FP_ProjectError): ...
class FP_NullParameterError(FP_ProjectError): ...
class FP_ParameterError(FP_ProjectError): ...

class FLExProject:
    WriteEnabled: bool
    ProjectName: str
    ProjectPath: str

    # Low-level LCM API properties (for advanced use)
    project: Any  # Direct access to FdoCache
    lp: Any  # Direct access to LangProject (LcmCache.LanguageProject)
    lexDB: Any  # Direct access to LexDb (LangProject.LexDbOA)

    # Grammar operations
    @property
    def POS(self) -> POSOperations: ...
    @property
    def Phonemes(self) -> PhonemeOperations: ...
    @property
    def NaturalClasses(self) -> NaturalClassOperations: ...
    @property
    def Environments(self) -> EnvironmentOperations: ...
    @property
    def Allomorphs(self) -> AllomorphOperations: ...
    @property
    def MorphRules(self) -> MorphRuleOperations: ...
    @property
    def InflectionFeatures(self) -> InflectionFeatureOperations: ...
    @property
    def GramCat(self) -> GramCatOperations: ...
    @property
    def PhonRules(self) -> PhonologicalRuleOperations: ...

    # Lexicon operations
    @property
    def LexEntry(self) -> LexEntryOperations: ...
    @property
    def Senses(self) -> LexSenseOperations: ...
    @property
    def Examples(self) -> ExampleOperations: ...
    @property
    def LexReferences(self) -> LexReferenceOperations: ...
    @property
    def Reversal(self) -> ReversalOperations: ...
    @property
    def ReversalIndexes(self) -> ReversalOperations: ...
    @property
    def ReversalEntries(self) -> ReversalOperations: ...
    @property
    def SemanticDomains(self) -> SemanticDomainOperations: ...
    @property
    def Pronunciations(self) -> PronunciationOperations: ...
    @property
    def Variants(self) -> VariantOperations: ...
    @property
    def Etymology(self) -> EtymologyOperations: ...

    # Texts & Words operations
    @property
    def Texts(self) -> TextOperations: ...
    @property
    def Paragraphs(self) -> ParagraphOperations: ...
    @property
    def Segments(self) -> SegmentOperations: ...
    @property
    def Wordforms(self) -> WordformOperations: ...
    @property
    def WfiAnalyses(self) -> WfiAnalysisOperations: ...
    @property
    def WfiGlosses(self) -> WfiGlossOperations: ...
    @property
    def WfiMorphBundles(self) -> WfiMorphBundleOperations: ...
    @property
    def Media(self) -> MediaOperations: ...
    @property
    def Discourse(self) -> DiscourseOperations: ...
    @property
    def Filters(self) -> FilterOperations: ...

    # Notebook operations
    @property
    def Notes(self) -> NoteOperations: ...
    @property
    def Person(self) -> PersonOperations: ...
    @property
    def Location(self) -> LocationOperations: ...
    @property
    def Anthropology(self) -> AnthropologyOperations: ...
    @property
    def DataNotebook(self) -> DataNotebookOperations: ...

    # Lists operations
    @property
    def PossibilityLists(self) -> PossibilityListOperations: ...
    @property
    def Publications(self) -> PublicationOperations: ...
    @property
    def TranslationTypes(self) -> TranslationTypeOperations: ...
    @property
    def Overlays(self) -> OverlayOperations: ...
    @property
    def Confidence(self) -> ConfidenceOperations: ...
    @property
    def Agents(self) -> AgentOperations: ...

    # System operations
    @property
    def WritingSystems(self) -> WritingSystemOperations: ...
    @property
    def CustomFields(self) -> CustomFieldOperations: ...
    @property
    def ProjectSettings(self) -> ProjectSettingsOperations: ...
    @property
    def AnnotationDefs(self) -> AnnotationDefOperations: ...
    @property
    def Checks(self) -> CheckOperations: ...

    # Lifecycle methods
    def OpenProject(self, projectName: str, writeEnabled: bool = False) -> None: ...
    def CloseProject(self, save: bool = True) -> None: ...

    # Utility methods
    def GetFieldID(self, className: str, fieldName: str) -> Optional[int]: ...
    def Object(self, hvoOrGuid: Union[int, str]) -> Optional[Any]: ...
