#
#   FLExProject.py
#
#   Class: FLExProject
#            Fieldworks Language Explorer project access functions 
#            via SIL Language and Culture Model (LCM) API.
#
#
#   Platform: Python.NET
#             (ITsString doesn't work in IRONPython)
#             FieldWorks Version 9
#
#   Copyright Craig Farrow, 2008 - 2024
#

import logging
logger = logging.getLogger(__name__)

# Initialise low-level FLEx data access
from . import FLExInit
from . import FLExLCM

from subprocess import Popen, DETACHED_PROCESS
from .. import FWExecutable

import clr
clr.AddReference("System")
import System

from SIL.LCModel import (
    ICmObjectRepository,
    ILexEntryRepository, ILexEntry, LexEntryTags,
                         ILexSense, LexSenseTags,
    IWfiWordformRepository, WfiWordformTags,
                            WfiGlossTags,
    IWfiAnalysisRepository, IWfiAnalysis, WfiAnalysisTags,
                            WfiMorphBundleTags,
    LexExampleSentenceTags,
    MoFormTags,
    ILexRefTypeRepository,
    ICmPossibilityRepository,
    ICmPossibilityList,
    ICmSemanticDomain,
    TextTags,
    ITextRepository,
    IStTxtPara,
    ISegmentRepository,
    IReversalIndex, IReversalIndexEntry, ReversalIndexEntryTags,
    IMoMorphType,
    SpecialWritingSystemCodes,
    LcmInvalidClassException,
    LcmInvalidFieldException,
    LcmFileLockedException,
    LcmDataMigrationForbiddenException,
    IUndoStackManager,
    )

from SIL.LCModel.Core.Cellar import (
    CellarPropertyType, 
    CellarPropertyTypeFilter,
    )
    
from SIL.LCModel.Infrastructure import (
    IFwMetaDataCacheManaged,
    )

from SIL.LCModel.Core.KernelInterfaces import ITsString, ITsStrBldr
from SIL.LCModel.Core.Text import TsStringUtils
from SIL.LCModel.Utils import WorkerThreadException, ReflectionHelper
from SIL.FieldWorks.Common.FwUtils import (
    StartupException,
    FwAppArgs,
    )


#--- Exceptions ------------------------------------------------------

class FP_ProjectError(Exception):
    """Exception raised for any problems opening the project.

    Attributes:
        - message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

class FP_FileNotFoundError(FP_ProjectError):
    def __init__(self, projectName, e):
        # Normally this will be a mispelled/wrong project name...
        if projectName in str(e):
            FP_ProjectError.__init__(self,
                "Project file not found: %s" % projectName)
        # ...however, it could be an internal FLEx error.
        else:
            FP_ProjectError.__init__(self,
                "File not found error: %s" % e)

class FP_FileLockedError(FP_ProjectError):
    def __init__(self):
        FP_ProjectError.__init__(self,
            "This project is in use by another program. To allow shared access to this project, turn on the sharing option in the Sharing tab of the Fieldworks Project Properties dialog.")
            
class FP_MigrationRequired(FP_ProjectError):
    def __init__(self):
        FP_ProjectError.__init__(self,
            "This project needs to be opened in FieldWorks in order for it to be migrated to the latest format.")

#-----------------------------------------------------            

class FP_RuntimeError(Exception):
    """Exception raised for any problems running the module.

    Attributes:
        - message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

class FP_ReadOnlyError(FP_RuntimeError):
    def __init__(self):
        FP_RuntimeError.__init__(self,
            "Trying to write to the project database without changes enabled.")
            
class FP_WritingSystemError(FP_RuntimeError):
    def __init__(self, writingSystemName):
        FP_RuntimeError.__init__(self,
            "Invalid Writing System for this project: %s" % writingSystemName)

class FP_NullParameterError(FP_RuntimeError):
    def __init__(self):
        FP_RuntimeError.__init__(self,
            "Null parameter.")

class FP_ParameterError(FP_RuntimeError):
    def __init__(self, msg):
        FP_RuntimeError.__init__(self, msg)
        
#-----------------------------------------------------------

def AllProjectNames():
    """
    Returns a list of FieldWorks projects that are in the default location.
    """
    
    return FLExLCM.GetListOfProjects()

#-----------------------------------------------------------

def OpenProjectInFW(projectName):
    
    Popen([FWExecutable, '-db', projectName],
          creationflags=DETACHED_PROCESS)

#-----------------------------------------------------------
   
class FLExProject (object):
    """
    This class provides convenience methods for accessing a FieldWorks 
    project by hiding some of the complexity of LCM.
    For functionality that isn't provided here, LCM data and methods
    can be used directly via `FLExProject.project`, `FLExProject.lp` and
    `FLExProject.lexDB`.
    However, for long term use, new methods should be added to this class.

    Usage::

        from SIL.LCModel.Core.KernelInterfaces import ITsString, ITsStrBldr
        from SIL.LCModel.Core.Text import TsStringUtils 

        project = FLExProject()
        try:
            project.OpenProject("my project",
                                writeEnabled = True/False)
        except:
            #"Failed to open project"
            del project
            exit(1)

        WSHandle = project.WSHandle('en')

        # Traverse the whole lexicon
        for lexEntry in project.LexiconAllEntries():
            headword = project.LexiconGetHeadword(lexEntry)

            # Use get_String() and set_String() with text fields:
            lexForm = lexEntry.LexemeFormOA                              
            lexEntryValue = ITsString(lexForm.Form.get_String(WSHandle)).Text
            newValue = convert_headword(lexEntryValue)
            mkstr = TsStringUtils.MakeString(newValue, WSHandle) 
            lexForm.Form.set_String(WSHandle, mkstr)

    """
        
    def OpenProject(self, 
                    projectName, 
                    writeEnabled = False):
        """
        Open a project. The project must be closed with `CloseProject()` to 
        save any changes, and release the lock.

        projectName:
            - Either the full path including ".fwdata" suffix, or
            - The name only, to open from the default project location.
            
        writeEnabled: 
            Enables changes to be written to the project, which will be
            saved on a call to `CloseProject()`. 
            LCM will raise an exception if changes are attempted without 
            opening the project in this mode.
            
        Note: 
            A call to `OpenProject()` may fail with a `FP_FileLockedError`
            exception if the project is open in Fieldworks (or another 
            application).
            To avoid this, project sharing can be enabled within the 
            Fieldworks Project Properties dialog. In the Sharing tab,
            turn on the option "Share project contents with programs 
            on this computer".

        """
        
        try:
            self.project = FLExLCM.OpenProject(projectName)
            
        except System.IO.FileNotFoundException as e:
            raise FP_FileNotFoundError(projectName, e)
            
        except LcmFileLockedException as e:
            raise FP_FileLockedError()
        
        except (LcmDataMigrationForbiddenException,           
                WorkerThreadException) as e:
            # Raised if the FW project needs to be migrated
            # to a later version. The user needs to open the project 
            # in FW to do the migration.
            # Jason Naylor [Dec2018] said not to do migration from an external
            # program: "We think that is something a FieldWorks user should
            # explicitly decide."
            raise FP_MigrationRequired()
            
        except StartupException as e:
            # An unknown error -- pass on the full information
            raise FP_ProjectError(e.Message)


        self.lp    = self.project.LangProject
        self.lexDB = self.lp.LexDbOA
        
        # Set up FieldWorks for making changes to the project.
        # All changes will be automatically saved when this object is
        # deleted.

        self.writeEnabled = writeEnabled
        
        if self.writeEnabled:
            try:
                # This must be called before calling any methods that change
                # the project.
                self.project.MainCacheAccessor.BeginNonUndoableTask()
            except System.InvalidOperationException:
                raise FP_ProjectError("BeginNonUndoableTask() failed.")

    def CloseProject(self):
        """
        Save any pending changes and dispose of the LCM object.
        """
        # logger.debug("Closing FLExProject object...")
        if hasattr(self, "project"):
            if self.writeEnabled:
                # logger.debug("Saving changes...")
                # This must be called to mirror the call to BeginNonUndoableTask().
                self.project.MainCacheAccessor.EndNonUndoableTask()
                # Save all changes to disk. (EndNonUndoableTask)
                usm = self.ObjectRepository(IUndoStackManager)
                usm.Save()                
                # logger.debug("Done")
            try:
                # logger.debug("Calling Dispose()...")
                self.project.Dispose()
                del self.project
                # logger.debug("Deleted project object")
                return
            except:
                # import traceback
                # logger.debug("Exception in Dispose()")
                # logger.debug("FLExProject.__del__:\n %s\n" % (traceback.format_exc()))
                raise
                pass

    # --- Advanced Operations ---

    @property
    def POS(self):
        """
        Access to Parts of Speech operations.

        Returns:
            POSOperations: Instance providing POS management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all parts of speech
            >>> for pos in project.POS.GetAll():
            ...     print(f"{project.POS.GetName(pos)} ({project.POS.GetAbbreviation(pos)})")
            >>> # Create a new POS
            >>> noun = project.POS.Create("Noun", "N")
            >>> # Find and update
            >>> verb = project.POS.Find("Verb")
            >>> if verb:
            ...     project.POS.SetAbbreviation(verb, "V")
        """
        if not hasattr(self, '_pos_ops'):
            from .POSOperations import POSOperations
            self._pos_ops = POSOperations(self)
        return self._pos_ops

    @property
    def LexEntry(self):
        """
        Access to Lexical Entry operations.

        Returns:
            LexEntryOperations: Instance providing lexical entry management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all entries
            >>> for entry in project.LexEntry.GetAll():
            ...     print(project.LexEntry.GetHeadword(entry))
            >>> # Create a new entry
            >>> entry = project.LexEntry.Create("run", "stem")
            >>> # Add a sense
            >>> sense = project.LexEntry.AddSense(entry, "to move rapidly on foot")
            >>> # Set citation form
            >>> project.LexEntry.SetCitationForm(entry, "run")
        """
        if not hasattr(self, '_lexentry_ops'):
            from .LexEntryOperations import LexEntryOperations
            self._lexentry_ops = LexEntryOperations(self)
        return self._lexentry_ops

    @property
    def Texts(self):
        """
        Access to Text operations.

        Returns:
            TextOperations: Instance providing text management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a new text
            >>> text = project.Texts.Create("Genesis")
            >>> # List all texts
            >>> for t in project.Texts.GetAll():
            ...     print(project.Texts.GetName(t))
            >>> # Update text name
            >>> project.Texts.SetName(text, "Genesis Chapter 1")
        """
        if not hasattr(self, '_text_ops'):
            from .TextOperations import TextOperations
            self._text_ops = TextOperations(self)
        return self._text_ops

    @property
    def Wordforms(self):
        """
        Access to wordform operations.

        Returns:
            WordformOperations: Instance providing wordform management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all wordforms
            >>> for wf in project.Wordforms.GetAll():
            ...     print(project.Wordforms.GetForm(wf))
            >>> # Create a new wordform
            >>> wf = project.Wordforms.Create("running")
            >>> # Set spelling status
            >>> from flexlibs import SpellingStatusStates
            >>> project.Wordforms.SetSpellingStatus(wf, SpellingStatusStates.CORRECT)
        """
        if not hasattr(self, '_wordform_ops'):
            from .WordformOperations import WordformOperations
            self._wordform_ops = WordformOperations(self)
        return self._wordform_ops

    @property
    def WfiAnalyses(self):
        """
        Access to wordform analysis operations.

        Returns:
            WfiAnalysisOperations: Instance providing wordform analysis management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get wordform and its analyses
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.WfiAnalyses.GetAll(wf)
            >>> for analysis in analyses:
            ...     glosses = project.WfiAnalyses.GetGlosses(analysis)
            ...     print(f"Analysis: {glosses}")
            >>> # Create new analysis
            >>> new_analysis = project.WfiAnalyses.Create(wf)
            >>> # Add gloss
            >>> project.WfiAnalyses.AddGloss(new_analysis, "running", "en")
            >>> # Set category
            >>> verb = project.POS.Find("Verb")
            >>> if verb:
            ...     project.WfiAnalyses.SetCategory(new_analysis, verb)
            >>> # Approve analysis
            >>> project.WfiAnalyses.ApproveAnalysis(new_analysis)
        """
        if not hasattr(self, '_wfianalysis_ops'):
            from .WfiAnalysisOperations import WfiAnalysisOperations
            self._wfianalysis_ops = WfiAnalysisOperations(self)
        return self._wfianalysis_ops

    @property
    def Paragraphs(self):
        """
        Access to paragraph operations.

        Returns:
            ParagraphOperations: Instance providing paragraph management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> text = list(project.Texts.GetAll())[0]
            >>> para = list(text.ContentsOA.ParagraphsOS)[0]
            >>> # Get translations
            >>> trans = project.Paragraphs.GetTranslations(para)
            >>> # Set translation
            >>> project.Paragraphs.SetTranslation(para, "In the beginning...", "en")
            >>> # Add note
            >>> note = project.Paragraphs.AddNote(para, "Check translation")
            >>> # Get style
            >>> style = project.Paragraphs.GetStyleName(para)
        """
        if not hasattr(self, '_paragraph_ops'):
            from .ParagraphOperations import ParagraphOperations
            self._paragraph_ops = ParagraphOperations(self)
        return self._paragraph_ops

    @property
    def Segments(self):
        """
        Access to segment operations.

        Returns:
            SegmentOperations: Instance providing segment management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all segments in a paragraph
            >>> para = project.Object(para_hvo)
            >>> for segment in project.Segments.GetAll(para):
            ...     baseline = project.Segments.GetBaselineText(segment)
            ...     print(baseline)
            >>> # Set translations
            >>> segment = list(project.Segments.GetAll(para))[0]
            >>> project.Segments.SetFreeTranslation(segment, "In the beginning...")
            >>> project.Segments.SetLiteralTranslation(segment, "In-the beginning...")
        """
        if not hasattr(self, '_segment_ops'):
            from .SegmentOperations import SegmentOperations
            self._segment_ops = SegmentOperations(self)
        return self._segment_ops

    @property
    def Phonemes(self):
        """
        Access to phoneme operations.

        Returns:
            PhonemeOperations: Instance providing phoneme management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all phonemes
            >>> for phoneme in project.Phonemes.GetAll():
            ...     repr = project.Phonemes.GetRepresentation(phoneme)
            ...     desc = project.Phonemes.GetDescription(phoneme)
            ...     print(f"{repr}: {desc}")
            >>> # Create a new phoneme
            >>> phoneme = project.Phonemes.Create("/p/")
            >>> project.Phonemes.SetDescription(phoneme, "voiceless bilabial stop")
            >>> # Add allophonic codes
            >>> project.Phonemes.AddCode(phoneme, "[p]")
            >>> project.Phonemes.AddCode(phoneme, "[pʰ]")
            >>> # Check phoneme type
            >>> if project.Phonemes.IsConsonant(phoneme):
            ...     print("Consonant phoneme")
        """
        if not hasattr(self, '_phoneme_ops'):
            from .PhonemeOperations import PhonemeOperations
            self._phoneme_ops = PhonemeOperations(self)
        return self._phoneme_ops

    @property
    def NaturalClasses(self):
        """
        Access to natural class operations.

        Returns:
            NaturalClassOperations: Instance providing natural class management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all natural classes
            >>> for nc in project.NaturalClasses.GetAll():
            ...     name = project.NaturalClasses.GetName(nc)
            ...     print(f"Natural class: {name}")
            >>> # Create a new natural class
            >>> nc = project.NaturalClasses.Create("Voiced Stops")
            >>> # Add phonemes to the class
            >>> phoneme_b = project.Phonemes.Find("/b/")
            >>> project.NaturalClasses.AddPhoneme(nc, phoneme_b)
        """
        if not hasattr(self, '_naturalclass_ops'):
            from .NaturalClassOperations import NaturalClassOperations
            self._naturalclass_ops = NaturalClassOperations(self)
        return self._naturalclass_ops

    @property
    def Environments(self):
        """
        Access to phonological environment operations.

        Returns:
            EnvironmentOperations: Instance providing environment management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all environments
            >>> for env in project.Environments.GetAll():
            ...     name = project.Environments.GetName(env)
            ...     repr = project.Environments.GetStringRepresentation(env)
            ...     print(f"{name}: {repr}")
            >>> # Create a new environment
            >>> env = project.Environments.Create("Between vowels", "V_V")
        """
        if not hasattr(self, '_environment_ops'):
            from .EnvironmentOperations import EnvironmentOperations
            self._environment_ops = EnvironmentOperations(self)
        return self._environment_ops

    @property
    def Allomorphs(self):
        """
        Access to allomorph operations.

        Returns:
            AllomorphOperations: Instance providing allomorph management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all allomorphs for an entry
            >>> entry = project.LexiconGetFirstEntry()
            >>> for allo in project.Allomorphs.GetAll(entry):
            ...     form = project.Allomorphs.GetForm(allo)
            ...     print(f"Allomorph: {form}")
            >>> # Create a new allomorph
            >>> allo = project.Allomorphs.Create(entry, "-ed")
        """
        if not hasattr(self, '_allomorph_ops'):
            from .AllomorphOperations import AllomorphOperations
            self._allomorph_ops = AllomorphOperations(self)
        return self._allomorph_ops

    @property
    def MorphRules(self):
        """
        Access to morphological rule operations.

        Returns:
            MorphRuleOperations: Instance providing morph rule management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all morphological rules
            >>> for rule in project.MorphRules.GetAll():
            ...     name = project.MorphRules.GetName(rule)
            ...     active = project.MorphRules.IsActive(rule)
            ...     print(f"{name}: {'active' if active else 'inactive'}")
            >>> # Create a new rule
            >>> rule = project.MorphRules.Create("Plural formation", "Lexical")
        """
        if not hasattr(self, '_morphrule_ops'):
            from .MorphRuleOperations import MorphRuleOperations
            self._morphrule_ops = MorphRuleOperations(self)
        return self._morphrule_ops

    @property
    def InflectionFeatures(self):
        """
        Access to inflection feature operations.

        Returns:
            InflectionFeatureOperations: Instance providing inflection feature management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all inflection classes
            >>> for ic in project.InflectionFeatures.GetAllClasses():
            ...     name = project.InflectionFeatures.GetClassName(ic)
            ...     print(f"Inflection class: {name}")
            >>> # Get all features
            >>> for feat in project.InflectionFeatures.GetAllFeatures():
            ...     name = project.InflectionFeatures.GetFeatureName(feat)
            ...     print(f"Feature: {name}")
        """
        if not hasattr(self, '_inflectionfeature_ops'):
            from .InflectionFeatureOperations import InflectionFeatureOperations
            self._inflectionfeature_ops = InflectionFeatureOperations(self)
        return self._inflectionfeature_ops

    @property
    def GramCat(self):
        """
        Access to grammatical category operations.

        Returns:
            GramCatOperations: Instance providing grammatical category management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all grammatical categories
            >>> for gc in project.GramCat.GetAll():
            ...     name = project.GramCat.GetName(gc)
            ...     print(f"Category: {name}")
            >>> # Create a new category
            >>> gc = project.GramCat.Create("Transitive")
        """
        if not hasattr(self, '_gramcat_ops'):
            from .GramCatOperations import GramCatOperations
            self._gramcat_ops = GramCatOperations(self)
        return self._gramcat_ops

    @property
    def PhonRules(self):
        """
        Access to phonological rule operations.

        Returns:
            PhonologicalRuleOperations: Instance providing phonological rule management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a phonological rule
            >>> rule = project.PhonRules.Create("Voicing Assimilation",
            ...     "Voiceless stops become voiced between vowels")
            >>> # Add input and output
            >>> phoneme_t = project.Phonemes.Find("/t/")
            >>> phoneme_d = project.Phonemes.Find("/d/")
            >>> project.PhonRules.AddInputSegment(rule, phoneme_t)
            >>> project.PhonRules.AddOutputSegment(rule, phoneme_d)
            >>> # Set context
            >>> vowels = project.NaturalClasses.Find("Vowels")
            >>> project.PhonRules.SetLeftContext(rule, vowels)
            >>> project.PhonRules.SetRightContext(rule, vowels)
        """
        if not hasattr(self, '_phonrule_ops'):
            from .PhonologicalRuleOperations import PhonologicalRuleOperations
            self._phonrule_ops = PhonologicalRuleOperations(self)
        return self._phonrule_ops

    @property
    def Senses(self):
        """
        Access to lexical sense operations.

        Returns:
            LexSenseOperations: Instance providing sense management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all senses for an entry
            >>> entry = list(project.LexiconAllEntries())[0]
            >>> for sense in project.Senses.GetAll(entry):
            ...     gloss = project.Senses.GetGloss(sense)
            ...     print(f"Sense: {gloss}")
            >>> # Create a new sense
            >>> sense = project.Senses.Create(entry, "to run", "en")
            >>> # Set definition
            >>> project.Senses.SetDefinition(sense, "To move swiftly on foot")
            >>> # Add semantic domain
            >>> domains = project.GetAllSemanticDomains(flat=True)
            >>> if domains:
            ...     project.Senses.AddSemanticDomain(sense, domains[0])
        """
        if not hasattr(self, '_sense_ops'):
            from .LexSenseOperations import LexSenseOperations
            self._sense_ops = LexSenseOperations(self)
        return self._sense_ops

    @property
    def Examples(self):
        """
        Access to example sentence operations.

        Returns:
            ExampleOperations: Instance providing example sentence management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get first entry and sense
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> # Get all examples
            >>> for example in project.Examples.GetAll(sense):
            ...     text = project.Examples.GetExample(example)
            ...     trans = project.Examples.GetTranslation(example)
            ...     print(f"{text} - {trans}")
            >>> # Create a new example
            >>> example = project.Examples.Create(sense, "The cat slept.")
            >>> project.Examples.SetTranslation(example, "Le chat a dormi.")
            >>> project.Examples.SetReference(example, "Corpus A:123")
        """
        if not hasattr(self, '_example_ops'):
            from .ExampleOperations import ExampleOperations
            self._example_ops = ExampleOperations(self)
        return self._example_ops

    @property
    def LexReferences(self):
        """
        Access to lexical reference and relation operations.

        Returns:
            LexReferenceOperations: Instance providing lexical reference management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all reference types
            >>> for ref_type in project.LexReferences.GetAllTypes():
            ...     name = project.LexReferences.GetTypeName(ref_type)
            ...     mapping = project.LexReferences.GetMappingType(ref_type)
            ...     print(f"{name}: {mapping}")
            >>> # Create a synonym relation
            >>> syn_type = project.LexReferences.FindType("Synonym")
            >>> if not syn_type:
            ...     syn_type = project.LexReferences.CreateType("Synonym", "Symmetric")
            >>> # Link two senses
            >>> entry1 = project.LexEntry.Find("run")
            >>> entry2 = project.LexEntry.Find("jog")
            >>> if entry1 and entry2:
            ...     sense1 = list(project.Senses.GetAll(entry1))[0]
            ...     sense2 = list(project.Senses.GetAll(entry2))[0]
            ...     ref = project.LexReferences.Create(syn_type, [sense1, sense2])
            >>> # Get all references for a sense
            >>> for ref in project.LexReferences.GetAll(sense1):
            ...     targets = project.LexReferences.GetTargets(ref)
            ...     print(f"Related to {len(targets)} items")
        """
        if not hasattr(self, '_lexref_ops'):
            from .LexReferenceOperations import LexReferenceOperations
            self._lexref_ops = LexReferenceOperations(self)
        return self._lexref_ops

    @property
    def Reversal(self):
        """
        Access to reversal entry operations.

        Returns:
            ReversalOperations: Instance providing reversal entry management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all reversal indexes
            >>> for index in project.Reversal.GetAllIndexes():
            ...     ws = index.WritingSystem
            ...     print(f"Reversal index: {ws}")
            >>> # Get English reversal index
            >>> en_index = project.Reversal.GetIndex("en")
            >>> if en_index:
            ...     # Get all entries
            ...     for entry in project.Reversal.GetAll(en_index):
            ...         form = project.Reversal.GetForm(entry)
            ...         print(f"Reversal: {form}")
            ...     # Create a new reversal entry
            ...     entry = project.Reversal.Create(en_index, "run", "en")
            ...     # Link to a sense
            ...     lexentry = project.LexEntry.Find("run")
            ...     if lexentry:
            ...         senses = project.LexEntry.GetSenses(lexentry)
            ...         if senses:
            ...             project.Reversal.AddSense(entry, senses[0])
        """
        if not hasattr(self, '_reversal_ops'):
            from .ReversalOperations import ReversalOperations
            self._reversal_ops = ReversalOperations(self)
        return self._reversal_ops

    @property
    def SemanticDomains(self):
        """
        Access to semantic domain operations.

        Returns:
            SemanticDomainOperations: Instance providing semantic domain management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all semantic domains
            >>> for domain in project.SemanticDomains.GetAll(flat=True):
            ...     number = project.SemanticDomains.GetNumber(domain)
            ...     name = project.SemanticDomains.GetName(domain)
            ...     print(f"{number} - {name}")
            >>> # Find a specific domain
            >>> walk_domain = project.SemanticDomains.Find("7.2.1")
            >>> if walk_domain:
            ...     desc = project.SemanticDomains.GetDescription(walk_domain)
            ...     senses = project.SemanticDomains.GetSensesInDomain(walk_domain)
            ...     print(f"Domain has {len(senses)} senses")
            >>> # Create a custom domain
            >>> custom = project.SemanticDomains.Create("Technology", "900")
        """
        if not hasattr(self, '_semantic_domain_ops'):
            from .SemanticDomainOperations import SemanticDomainOperations
            self._semantic_domain_ops = SemanticDomainOperations(self)
        return self._semantic_domain_ops

    @property
    def Pronunciations(self):
        """
        Access to pronunciation operations.

        Returns:
            PronunciationOperations: Instance providing pronunciation management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all pronunciations for an entry
            >>> entry = list(project.LexiconAllEntries())[0]
            >>> for pron in project.Pronunciations.GetAll(entry):
            ...     ipa = project.Pronunciations.GetForm(pron, "en-fonipa")
            ...     print(f"IPA: {ipa}")
            >>> # Create a new pronunciation
            >>> pron = project.Pronunciations.Create(entry, "rʌn", "en-fonipa")
            >>> # Add audio file
            >>> project.Pronunciations.AddMediaFile(pron, "/path/to/audio.wav")
            >>> # Get media files
            >>> media = project.Pronunciations.GetMediaFiles(pron)
            >>> print(f"Audio files: {len(media)}")
        """
        if not hasattr(self, '_pronunciation_ops'):
            from .PronunciationOperations import PronunciationOperations
            self._pronunciation_ops = PronunciationOperations(self)
        return self._pronunciation_ops

    @property
    def Variants(self):
        """
        Access to variant form operations.

        Returns:
            VariantOperations: Instance providing variant management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all variant types
            >>> for vtype in project.Variants.GetAllTypes():
            ...     name = project.Variants.GetTypeName(vtype)
            ...     print(f"Variant type: {name}")
            >>> # Find a specific variant type
            >>> spelling_type = project.Variants.FindType("Spelling Variant")
            >>> # Create a variant
            >>> entry = project.LexEntry.Find("color")
            >>> variant = project.Variants.Create(entry, "colour", spelling_type)
            >>> # Get all variants for an entry
            >>> for var in project.Variants.GetAll(entry):
            ...     form = project.Variants.GetForm(var)
            ...     vtype = project.Variants.GetType(var)
            ...     print(f"Variant: {form}")
            >>> # For irregularly inflected forms
            >>> go_entry = project.LexEntry.Find("go")
            >>> went_entry = project.LexEntry.Find("went")
            >>> irregular_type = project.Variants.FindType("Irregularly Inflected Form")
            >>> variant_ref = project.Variants.Create(went_entry, "went", irregular_type)
            >>> project.Variants.AddComponentLexeme(variant_ref, go_entry)
        """
        if not hasattr(self, '_variant_ops'):
            from .VariantOperations import VariantOperations
            self._variant_ops = VariantOperations(self)
        return self._variant_ops

    @property
    def Etymology(self):
        """
        Access to etymology operations.

        Returns:
            EtymologyOperations: Instance providing etymology tracking methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get an entry
            >>> entry = project.LexEntry.Find("telephone")
            >>> # Create etymology for compound word components
            >>> etym1 = project.Etymology.Create(entry, "Ancient Greek", "τηλε (tele)", "far, distant")
            >>> project.Etymology.SetComment(etym1, "Combining form from Greek τῆλε")
            >>> etym2 = project.Etymology.Create(entry, "Ancient Greek", "φωνή (phōnē)", "sound, voice")
            >>> # Query etymologies
            >>> for etym in project.Etymology.GetAll(entry):
            ...     source = project.Etymology.GetSource(etym)
            ...     form = project.Etymology.GetForm(etym)
            ...     gloss = project.Etymology.GetGloss(etym)
            ...     print(f"{source}: {form} ({gloss})")
        """
        if not hasattr(self, '_etymology_ops'):
            from .EtymologyOperations import EtymologyOperations
            self._etymology_ops = EtymologyOperations(self)
        return self._etymology_ops

    @property
    def PossibilityLists(self):
        """
        Access to generic possibility list operations.

        Returns:
            PossibilityListOperations: Instance providing possibility list management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all possibility lists in the project
            >>> for poss_list in project.PossibilityLists.GetAllLists():
            ...     name = project.PossibilityLists.GetListName(poss_list)
            ...     items = project.PossibilityLists.GetItems(poss_list, flat=True)
            ...     print(f"{name}: {len(items)} items")
            Semantic Domains: 1435 items
            Parts of Speech: 45 items
            Text Genres: 12 items
            ...
            >>> # Work with a specific list
            >>> genre_list = project.PossibilityLists.FindList("Text Genres")
            >>> if genre_list:
            ...     # Get all items
            ...     for item in project.PossibilityLists.GetItems(genre_list):
            ...         name = project.PossibilityLists.GetItemName(item)
            ...         depth = project.PossibilityLists.GetDepth(item)
            ...         print(f"{'  ' * depth}{name}")
            ...     # Create a new genre
            ...     narrative = project.PossibilityLists.CreateItem(
            ...         genre_list, "Narrative", "en")
            ...     # Create a sub-genre
            ...     folktale = project.PossibilityLists.CreateItem(
            ...         genre_list, "Folktale", "en", parent=narrative)
            ...     # Move items in hierarchy
            ...     project.PossibilityLists.MoveItem(folktale, None)  # Move to top
        """
        if not hasattr(self, '_possibilitylist_ops'):
            from .PossibilityListOperations import PossibilityListOperations
            self._possibilitylist_ops = PossibilityListOperations(self)
        return self._possibilitylist_ops

    @property
    def CustomFields(self):
        """
        Access to custom field operations.

        Returns:
            CustomFieldOperations: Instance providing custom field management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all custom fields for entries
            >>> entry_fields = project.CustomFields.GetAllFields("LexEntry")
            >>> for field_id, label in entry_fields:
            ...     print(f"Field: {label} (ID: {field_id})")
            >>> # Find a specific field
            >>> field_id = project.CustomFields.FindField("LexEntry", "Etymology Source")
            >>> # Get and set field values
            >>> entry = project.LexEntry.Find("run")
            >>> if field_id:
            ...     value = project.CustomFields.GetValue(entry, "Etymology Source")
            ...     print(f"Current value: {value}")
            ...     project.CustomFields.SetValue(entry, "Etymology Source", "Latin currere")
            >>> # Work with list fields
            >>> sense = entry.SensesOS[0]
            >>> regions = project.CustomFields.GetListValues(sense, "Regions")
            >>> project.CustomFields.AddListValue(sense, "Regions", "North")
        """
        if not hasattr(self, '_customfield_ops'):
            from .CustomFieldOperations import CustomFieldOperations
            self._customfield_ops = CustomFieldOperations(self)
        return self._customfield_ops

    @property
    def WritingSystems(self):
        """
        Access to writing system operations.

        Returns:
            WritingSystemOperations: Instance providing writing system management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all writing systems
            >>> for ws in project.WritingSystems.GetAll():
            ...     name = project.WritingSystems.GetDisplayName(ws)
            ...     tag = project.WritingSystems.GetLanguageTag(ws)
            ...     print(f"{name} ({tag})")
            >>> # Configure a writing system
            >>> ws = list(project.WritingSystems.GetVernacular())[0]
            >>> project.WritingSystems.SetFontName(ws, "Charis SIL")
            >>> project.WritingSystems.SetFontSize(ws, 14)
            >>> # Set RTL for Arabic
            >>> if project.WritingSystems.Exists("ar"):
            ...     project.WritingSystems.SetRightToLeft("ar", True)
        """
        if not hasattr(self, '_writingsystem_ops'):
            from .WritingSystemOperations import WritingSystemOperations
            self._writingsystem_ops = WritingSystemOperations(self)
        return self._writingsystem_ops

    @property
    def WfiAnalyses(self):
        """
        Access to wordform analysis operations.

        Returns:
            WfiAnalysisOperations: Instance providing wordform analysis management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all analyses for a wordform
            >>> wordform = project.Wordforms.FindOrCreate("running")
            >>> for analysis in project.WfiAnalyses.GetAll(wordform):
            ...     category = project.WfiAnalyses.GetCategory(analysis)
            ...     bundles = project.WfiAnalyses.GetMorphBundles(analysis)
            ...     print(f"Category: {category}, Morphemes: {len(bundles)}")
            >>> # Create a new analysis
            >>> analysis = project.WfiAnalyses.Create(wordform)
            >>> # Approve the analysis
            >>> project.WfiAnalyses.ApproveAnalysis(analysis)
            >>> # Get all unapproved analyses
            >>> for analysis in project.WfiAnalyses.GetUnapprovedAnalyses():
            ...     wf = project.WfiAnalyses.GetWordform(analysis)
            ...     form = project.Wordforms.GetForm(wf)
            ...     print(f"Unapproved: {form}")
        """
        if not hasattr(self, '_wfianalysis_ops'):
            from .WfiAnalysisOperations import WfiAnalysisOperations
            self._wfianalysis_ops = WfiAnalysisOperations(self)
        return self._wfianalysis_ops

    @property
    def WfiGlosses(self):
        """
        Access to wordform gloss operations.

        Returns:
            WfiGlossOperations: Instance providing wordform gloss management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get an analysis
            >>> wordform = project.Wordforms.FindOrCreate("running")
            >>> analyses = project.WfiAnalyses.GetAll(wordform)
            >>> if analyses:
            ...     analysis = analyses[0]
            ...     # Create a gloss
            ...     gloss = project.WfiGlosses.Create(analysis, "running", "en")
            ...     # Get all glosses for an analysis
            ...     for g in project.WfiGlosses.GetAll(analysis):
            ...         form = project.WfiGlosses.GetForm(g, "en")
            ...         print(f"Gloss: {form}")
        """
        if not hasattr(self, '_wfigloss_ops'):
            from .WfiGlossOperations import WfiGlossOperations
            self._wfigloss_ops = WfiGlossOperations(self)
        return self._wfigloss_ops

    @property
    def WfiMorphBundles(self):
        """
        Access to wordform morpheme bundle operations.

        Returns:
            WfiMorphBundleOperations: Instance providing morpheme bundle management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get an analysis
            >>> wordform = project.Wordforms.FindOrCreate("running")
            >>> analysis = project.WfiAnalyses.Create(wordform)
            >>> # Create morpheme bundles
            >>> run_sense = project.LexEntry.Find("run").SensesOS[0]
            >>> bundle1 = project.WfiMorphBundles.Create(analysis, run_sense, "run")
            >>> ing_sense = project.LexEntry.Find("-ing").SensesOS[0]
            >>> bundle2 = project.WfiMorphBundles.Create(analysis, ing_sense, "-ing")
            >>> # Get all bundles
            >>> for bundle in project.WfiMorphBundles.GetAll(analysis):
            ...     form = project.WfiMorphBundles.GetForm(bundle)
            ...     sense = project.WfiMorphBundles.GetSense(bundle)
            ...     print(f"Morpheme: {form}")
        """
        if not hasattr(self, '_wfimorphbundle_ops'):
            from .WfiMorphBundleOperations import WfiMorphBundleOperations
            self._wfimorphbundle_ops = WfiMorphBundleOperations(self)
        return self._wfimorphbundle_ops

    @property
    def Media(self):
        """
        Access to media file operations.

        Returns:
            MediaOperations: Instance providing media file management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all media files
            >>> for media in project.Media.GetAll():
            ...     filename = project.Media.GetFilename(media)
            ...     mtype = project.Media.GetMediaType(media)
            ...     print(f"{filename} ({mtype})")
            >>> # Add a media file
            >>> media = project.Media.Create("/path/to/audio.wav", "My Recording")
            >>> # Copy file to project
            >>> project.Media.CopyToProject(media)
            >>> # Find orphaned media
            >>> orphans = project.Media.GetOrphanedMedia()
            >>> print(f"Found {len(orphans)} orphaned files")
        """
        if not hasattr(self, '_media_ops'):
            from .MediaOperations import MediaOperations
            self._media_ops = MediaOperations(self)
        return self._media_ops

    @property
    def Notes(self):
        """
        Access to note and annotation operations.

        Returns:
            NoteOperations: Instance providing note management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a note on an entry
            >>> entry = project.LexEntry.Find("run")
            >>> note = project.Notes.Create(entry, "Check etymology", "en")
            >>> # Add a reply
            >>> reply = project.Notes.AddReply(note, "Verified - from Latin currere", "en")
            >>> # Get all notes for an object
            >>> for n in project.Notes.GetAll(entry):
            ...     content = project.Notes.GetContent(n, "en")
            ...     replies = project.Notes.GetReplies(n)
            ...     print(f"Note: {content} ({len(replies)} replies)")
        """
        if not hasattr(self, '_note_ops'):
            from .NoteOperations import NoteOperations
            self._note_ops = NoteOperations(self)
        return self._note_ops

    @property
    def Filters(self):
        """
        Access to filter and query operations.

        Returns:
            FilterOperations: Instance providing filter management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a filter for incomplete entries
            >>> filter_def = {
            ...     "name": "Incomplete Entries",
            ...     "type": "LexEntry",
            ...     "conditions": [
            ...         {"field": "SensesOS", "operator": "isEmpty"}
            ...     ]
            ... }
            >>> filter_obj = project.Filters.Create(filter_def)
            >>> # Apply the filter
            >>> results = project.Filters.ApplyFilter(filter_obj)
            >>> print(f"Found {len(results)} incomplete entries")
            >>> # Export filter
            >>> json_str = project.Filters.ExportFilter(filter_obj)
        """
        if not hasattr(self, '_filter_ops'):
            from .FilterOperations import FilterOperations
            self._filter_ops = FilterOperations(self)
        return self._filter_ops

    @property
    def Discourse(self):
        """
        Access to discourse chart operations.

        Returns:
            DiscourseOperations: Instance providing discourse chart management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get a text
            >>> text = list(project.TextCatalog())[0]
            >>> # Create a discourse chart
            >>> chart = project.Discourse.CreateChart(text, "Constituent Chart", "en")
            >>> # Add rows
            >>> row1 = project.Discourse.AddRow(chart, 0)
            >>> # Get all charts
            >>> for c in project.Discourse.GetAllCharts():
            ...     name = project.Discourse.GetChartName(c, "en")
            ...     rows = project.Discourse.GetRows(c)
            ...     print(f"Chart: {name} ({len(rows)} rows)")
        """
        if not hasattr(self, '_discourse_ops'):
            from .DiscourseOperations import DiscourseOperations
            self._discourse_ops = DiscourseOperations(self)
        return self._discourse_ops

    @property
    def Person(self):
        """
        Access to person operations for managing consultants, speakers, and researchers.

        Returns:
            PersonOperations: Instance providing person management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a person
            >>> consultant = project.Person.Create("Maria Garcia", "en")
            >>> # Set properties
            >>> project.Person.SetGender(consultant, "Female", "en")
            >>> project.Person.SetEmail(consultant, "maria@example.com", "en")
            >>> project.Person.SetEducation(consultant, "PhD Linguistics", "en")
            >>> # Add residence
            >>> location = project.Location.Find("Lima")
            >>> if location:
            ...     project.Person.AddResidence(consultant, location)
            >>> # Get all people
            >>> for person in project.Person.GetAll():
            ...     name = project.Person.GetName(person)
            ...     email = project.Person.GetEmail(person)
            ...     print(f"{name}: {email}")
        """
        if not hasattr(self, '_person_ops'):
            from .PersonOperations import PersonOperations
            self._person_ops = PersonOperations(self)
        return self._person_ops

    @property
    def Location(self):
        """
        Access to location operations for managing geographic places.

        Returns:
            LocationOperations: Instance providing location management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create a location
            >>> region = project.Location.Create("Cusco Region", "en", alias="CUS")
            >>> project.Location.SetCoordinates(region, -13.5319, -71.9675)
            >>> project.Location.SetElevation(region, 3400)
            >>> # Create sublocation
            >>> city = project.Location.CreateSublocation(region, "Cusco", "en")
            >>> project.Location.SetDescription(city, "Historic capital of Inca Empire", "en")
            >>> # Find nearby locations
            >>> nearby = project.Location.GetNearby(city, radius_km=100)
            >>> for loc in nearby:
            ...     name = project.Location.GetName(loc)
            ...     coords = project.Location.GetCoordinates(loc)
            ...     print(f"{name}: {coords}")
        """
        if not hasattr(self, '_location_ops'):
            from .LocationOperations import LocationOperations
            self._location_ops = LocationOperations(self)
        return self._location_ops

    @property
    def Anthropology(self):
        """
        Access to anthropology operations for managing cultural/ethnographic data.

        Returns:
            AnthropologyOperations: Instance providing anthropology management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create anthropology items
            >>> marriage = project.Anthropology.Create(
            ...     "Marriage Customs", "MAR", "586")
            >>> project.Anthropology.SetDescription(marriage,
            ...     "Traditional marriage practices and ceremonies", "en")
            >>> # Create subitem
            >>> wedding = project.Anthropology.CreateSubitem(
            ...     marriage, "Wedding Ceremony", "WED", "586.1")
            >>> # Link to text
            >>> text = project.Texts.Find("Wedding Story")
            >>> if text:
            ...     project.Anthropology.AddText(marriage, text)
            >>> # Query items
            >>> items = project.Anthropology.GetItemsForText(text)
            >>> for item in items:
            ...     name = project.Anthropology.GetName(item)
            ...     code = project.Anthropology.GetAnthroCode(item)
            ...     print(f"{code}: {name}")
        """
        if not hasattr(self, '_anthropology_ops'):
            from .AnthropologyOperations import AnthropologyOperations
            self._anthropology_ops = AnthropologyOperations(self)
        return self._anthropology_ops

    @property
    def ProjectSettings(self):
        """
        Access to project settings operations.

        Returns:
            ProjectSettingsOperations: Instance providing project configuration methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get project info
            >>> name = project.ProjectSettings.GetProjectName()
            >>> desc = project.ProjectSettings.GetDescription("en")
            >>> # Configure writing systems
            >>> vern_wss = project.ProjectSettings.GetVernacularWSs()
            >>> project.ProjectSettings.SetDefaultVernacular("qaa-x-spec")
            >>> # Set default font
            >>> project.ProjectSettings.SetDefaultFont("en", "Charis SIL")
            >>> project.ProjectSettings.SetDefaultFontSize("en", 14)
        """
        if not hasattr(self, '_projectsettings_ops'):
            from .ProjectSettingsOperations import ProjectSettingsOperations
            self._projectsettings_ops = ProjectSettingsOperations(self)
        return self._projectsettings_ops

    @property
    def Publications(self):
        """
        Access to publication operations.

        Returns:
            PublicationOperations: Instance providing publication management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create publication
            >>> pub = project.Publications.Create("Dictionary", "en")
            >>> project.Publications.SetPageWidth(pub, 8.5)
            >>> project.Publications.SetPageHeight(pub, 11)
            >>> # Get all publications
            >>> for p in project.Publications.GetAll():
            ...     name = project.Publications.GetName(p)
            ...     is_default = project.Publications.GetIsDefault(p)
            ...     print(f"{name} (default: {is_default})")
        """
        if not hasattr(self, '_publication_ops'):
            from .PublicationOperations import PublicationOperations
            self._publication_ops = PublicationOperations(self)
        return self._publication_ops

    @property
    def Agents(self):
        """
        Access to agent operations.

        Returns:
            AgentOperations: Instance providing agent management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create human agent
            >>> person = project.Person.Create("John Smith", "en")
            >>> agent = project.Agents.CreateHumanAgent("John Smith", person)
            >>> # Create parser agent
            >>> parser = project.Agents.CreateParserAgent("MyParser", "1.0.0")
            >>> # Query agents
            >>> for a in project.Agents.GetAll():
            ...     name = project.Agents.GetName(a)
            ...     if project.Agents.IsHuman(a):
            ...         print(f"Human: {name}")
            ...     else:
            ...         version = project.Agents.GetVersion(a)
            ...         print(f"Parser: {name} v{version}")
        """
        if not hasattr(self, '_agent_ops'):
            from .AgentOperations import AgentOperations
            self._agent_ops = AgentOperations(self)
        return self._agent_ops

    @property
    def Confidence(self):
        """
        Access to confidence level operations.

        Returns:
            ConfidenceOperations: Instance providing confidence management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all confidence levels
            >>> for level in project.Confidence.GetAll():
            ...     name = project.Confidence.GetName(level)
            ...     print(f"Confidence: {name}")
            >>> # Create custom confidence level
            >>> verified = project.Confidence.Create("Speaker Verified", "en")
            >>> project.Confidence.SetDescription(verified,
            ...     "Confirmed by native speaker", "en")
        """
        if not hasattr(self, '_confidence_ops'):
            from .ConfidenceOperations import ConfidenceOperations
            self._confidence_ops = ConfidenceOperations(self)
        return self._confidence_ops

    @property
    def Overlays(self):
        """
        Access to discourse overlay operations.

        Returns:
            OverlayOperations: Instance providing overlay management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get a chart
            >>> text = list(project.TextCatalog())[0]
            >>> chart = project.Discourse.CreateChart(text, "Chart", "en")
            >>> # Create overlay
            >>> overlay = project.Overlays.Create(chart, "Temporal", "en")
            >>> project.Overlays.SetVisible(overlay, True)
            >>> # Get visible overlays
            >>> for o in project.Overlays.GetVisibleOverlays(chart):
            ...     name = project.Overlays.GetName(o)
            ...     print(f"Overlay: {name}")
        """
        if not hasattr(self, '_overlay_ops'):
            from .OverlayOperations import OverlayOperations
            self._overlay_ops = OverlayOperations(self)
        return self._overlay_ops

    @property
    def TranslationTypes(self):
        """
        Access to translation type operations.

        Returns:
            TranslationTypeOperations: Instance providing translation type methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get predefined types
            >>> free = project.TranslationTypes.GetFreeTranslationType()
            >>> literal = project.TranslationTypes.GetLiteralTranslationType()
            >>> # Create custom type
            >>> gloss = project.TranslationTypes.Create("Interlinear Gloss", "IG", "en")
            >>> # Get all types
            >>> for t in project.TranslationTypes.GetAll():
            ...     name = project.TranslationTypes.GetName(t)
            ...     abbr = project.TranslationTypes.GetAbbreviation(t)
            ...     print(f"{name} ({abbr})")
        """
        if not hasattr(self, '_translationtype_ops'):
            from .TranslationTypeOperations import TranslationTypeOperations
            self._translationtype_ops = TranslationTypeOperations(self)
        return self._translationtype_ops

    @property
    def AnnotationDefs(self):
        """
        Access to annotation definition operations.

        Returns:
            AnnotationDefOperations: Instance providing annotation definition methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Get all annotation definitions
            >>> for defn in project.AnnotationDefs.GetAll():
            ...     name = project.AnnotationDefs.GetName(defn)
            ...     can_create = project.AnnotationDefs.GetUserCanCreate(defn)
            ...     print(f"{name} (user-creatable: {can_create})")
            >>> # Create custom annotation type
            >>> note_type = project.AnnotationDefs.Create("Field Note", "en")
            >>> project.AnnotationDefs.SetUserCanCreate(note_type, True)
        """
        if not hasattr(self, '_annotationdef_ops'):
            from .AnnotationDefOperations import AnnotationDefOperations
            self._annotationdef_ops = AnnotationDefOperations(self)
        return self._annotationdef_ops

    @property
    def Checks(self):
        """
        Access to consistency check operations.

        Returns:
            CheckOperations: Instance providing check management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create check type
            >>> check = project.Checks.CreateCheckType("Missing Gloss", "en")
            >>> project.Checks.SetDescription(check,
            ...     "Find senses without glosses", "en")
            >>> # Run check
            >>> results = project.Checks.RunCheck(check)
            >>> print(f"Errors: {results['errors']}")
            >>> print(f"Warnings: {results['warnings']}")
            >>> # Get enabled checks
            >>> for c in project.Checks.GetEnabledChecks():
            ...     name = project.Checks.GetName(c)
            ...     status = project.Checks.GetCheckStatus(c)
            ...     print(f"{name}: {status}")
        """
        if not hasattr(self, '_check_ops'):
            from .CheckOperations import CheckOperations
            self._check_ops = CheckOperations(self)
        return self._check_ops

    @property
    def DataNotebook(self):
        """
        Access to data notebook operations for research notes and observations.

        Returns:
            DataNotebookOperations: Instance providing notebook record management methods

        Example:
            >>> project = FLExProject()
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> # Create notebook record
            >>> record = project.DataNotebook.Create(
            ...     "Field Interview", "Notes from interview with speaker")
            >>> project.DataNotebook.SetDateOfEvent(record, "2024-01-15")
            >>> # Link researcher
            >>> researcher = project.Person.Find("John Smith")
            >>> project.DataNotebook.AddResearcher(record, researcher)
            >>> # Create sub-record
            >>> sub = project.DataNotebook.CreateSubRecord(
            ...     record, "Kinship Terms", "Analysis of family terms")
            >>> # Set status
            >>> project.DataNotebook.SetStatus(record, "Reviewed")
            >>> # Query records
            >>> for rec in project.DataNotebook.FindByResearcher(researcher):
            ...     title = project.DataNotebook.GetTitle(rec)
            ...     date = project.DataNotebook.GetDateOfEvent(rec)
            ...     print(f"{title} ({date})")
        """
        if not hasattr(self, '_datanotebook_ops'):
            from .DataNotebookOperations import DataNotebookOperations
            self._datanotebook_ops = DataNotebookOperations(self)
        return self._datanotebook_ops

    # --- General ---

    def ProjectName(self):
        """
        Returns the display name of the current project.
        """

        return self.project.ProjectId.UiName
            
    # --- String Utilities ---

    def BestStr(self, stringObj):
        """
        Generic string function for `MultiUnicode` and `MultiString`
        objects, returning the best analysis or vernacular string.

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        return self.WritingSystems.GetBestString(stringObj)


    # --- LCM Utilities ---
    
    def UnpackNestedPossibilityList(self, possibilityList, objClass, flat=False):
        """
        Returns a nested or flat list of a Fieldworks possibility list.
        `objClass` is the class of object to cast the `CmPossibility` elements into.
        
        Return items are objects with properties/methods:
            - `Hvo`         - ID (value not the same across projects)
            - `Guid`        - Global Unique ID (same across all projects)
            - `ToString()`  - String representation.
        """
        for i in possibilityList:
            yield objClass(i)
            if flat:
                for j in self.UnpackNestedPossibilityList(i.SubPossibilitiesOS, objClass, flat):
                    yield objClass(j)
            else:
                l = list(self.UnpackNestedPossibilityList(i.SubPossibilitiesOS, objClass, flat))
                if l: yield l
    
    # --- Global: Writing Systems ---

    def GetAllVernacularWSs(self):
        """
        Returns a set of language tags for all vernacular writing systems used
        in this project.

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        return set(self.WritingSystems.GetLanguageTag(ws) for ws in self.WritingSystems.GetVernacular())
           
           
    def GetAllAnalysisWSs(self):
        """
        Returns a set of language tags for all analysis writing systems used
        in this project.

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        return set(self.WritingSystems.GetLanguageTag(ws) for ws in self.WritingSystems.GetAnalysis())

        
    def GetWritingSystems(self):
        """
        Returns the writing systems that are active in this project as a
        list of tuples: (Name, Language-tag, Handle, IsVernacular).
        Use the Language-tag when specifying writing system to other
        functions.

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        VernWSSet = self.GetAllVernacularWSs()

        WSList = []
        for ws in self.WritingSystems.GetAll():
            name = self.WritingSystems.GetDisplayName(ws)
            tag = self.WritingSystems.GetLanguageTag(ws)
            handle = ws.Handle
            isVern = tag in VernWSSet
            WSList.append((name, tag, handle, isVern))
        return WSList

        
    def WSUIName(self, languageTagOrHandle):
        """
        Returns the UI name of the writing system for the given language tag
        or handle.
        Ignores case and '-'/'_' differences.
        Returns `None` if the language tag is not found.

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        if isinstance(languageTagOrHandle, str):
            languageTagOrHandle = self.__NormaliseLangTag(languageTagOrHandle)

        try:
            return self.__WSNameCache[languageTagOrHandle]
        except AttributeError:
            # Create a lookup table on-demand using WritingSystemOperations
            self.__WSNameCache = {}
            for ws in self.project.ServiceLocator.WritingSystems.AllWritingSystems:
                langTag = self.__NormaliseLangTag(ws.Id)
                displayName = self.WritingSystems.GetDisplayName(ws)
                self.__WSNameCache[langTag] = displayName
                self.__WSNameCache[ws.Handle] = displayName
            # Recursive:
            return self.WSUIName(languageTagOrHandle)
        except KeyError:
            return None

            
    def WSHandle(self, languageTag):
        """
        Returns the handle of the writing system for `languageTag`.
        Ignores case and '-'/'_' differences.
        Returns `None` if the language tag is not found.
        """
        
        languageTag = self.__NormaliseLangTag(languageTag)
        
        try:
            return self.__WSLCIDCache[languageTag]
        except AttributeError:
            # Create a lookup table on-demand.
            self.__WSLCIDCache = {}
            for x in self.project.ServiceLocator.WritingSystems.AllWritingSystems:
                langTag = self.__NormaliseLangTag(x.Id)
                self.__WSLCIDCache[langTag] = x.Handle
            # Recursive:
            return self.WSHandle(languageTag)
        except KeyError:
            return None
            
            
    def GetDefaultVernacularWS(self):
        """
        Returns the default vernacular writing system: (Language-tag, Name)

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        ws = self.WritingSystems.GetDefaultVernacular()
        return (self.WritingSystems.GetLanguageTag(ws),
                self.WritingSystems.GetDisplayName(ws))
    
    
    def GetDefaultAnalysisWS(self):
        """
        Returns the default analysis writing system: (Language-tag, Name)

        Note: This method now delegates to WritingSystemOperations for single source of truth.
        """
        ws = self.WritingSystems.GetDefaultAnalysis()
        return (self.WritingSystems.GetLanguageTag(ws),
                self.WritingSystems.GetDisplayName(ws))

    # --- Global: other information ---
    
    def GetDateLastModified(self):
        return self.lp.DateModified
    
    
    def GetPartsOfSpeech(self):
        """
        Returns a list of the parts of speech defined in this project.

        .. note::
           This method delegates to :meth:`POSOperations.GetAll`.
        """
        return [self.POS.GetName(pos) for pos in self.POS.GetAll()]

        
    def GetAllSemanticDomains(self, flat=False):
        """
        Returns a nested or flat list of all semantic domains defined
        in this project. The list is ordered.

        Return items are `ICmSemanticDomain` objects.

        .. note::
           This method delegates to :meth:`SemanticDomainOperations.GetAll`.
        """
        return self.SemanticDomains.GetAll(flat=flat)


    # --- Global utility functions ---
    
    def BuildGotoURL(self, objectOrGuid):
        """
        Builds a URL that can be used with `os.startfile()` to jump to the
        object in Fieldworks. This method currently supports:

            - Lexical Entries, Senses and any object within the lexicon
            - Wordforms, Analyses and Wordform Glosses
            - Reversal Entries
            - Texts
        """

        if isinstance(objectOrGuid, System.Guid):
            flexObject = self.Object(objectOrGuid)
        else:
            flexObject = objectOrGuid
            
        # Quick sanity check that we have the right thing
        try:
            flexObject.Guid
        except:
            raise FP_ParameterError("BuildGotoURL: objectOrGuid is neither System.Guid nor an object with attribute Guid")

        if flexObject.ClassID == ReversalIndexEntryTags.kClassId:
            tool = "reversalToolEditComplete"

        elif flexObject.ClassID in (WfiWordformTags.kClassId,
                                    WfiAnalysisTags.kClassId,
                                    WfiGlossTags.kClassId):
            tool = "Analyses"
            
        elif flexObject.ClassID == TextTags.kClassId:
            tool = "interlinearEdit"
            
        else:
            tool = "lexiconEdit"                # Default tool is Lexicon Edit

        # Build the URL
        linkObj = FwAppArgs(self.project.ProjectId.Handle,
                            tool,
                            flexObject.Guid)

        return str(linkObj)

    # --- Generic Repository Access ---

    def ObjectRepository(self, repository):        
        """
        Returns an object repository.
        `repository` is specified by the interface class, such as:
        
            - `ITextRepository`
            - `ILexEntryRepository`
        """

        return self.project.ServiceLocator.GetService(repository)


    def ObjectCountFor(self, repository):
        """
        Returns the number of objects in `repository`.
        `repository` is specified by the interface class, such as:
        
            - `ITextRepository`
            - `ILexEntryRepository`

        All repository names can be viewed by opening a project in
        LCMBrowser, which can be launched via the Help menu. Add "I" 
        to the front and import from `SIL.LCModel`.
        """
        
        repo = self.ObjectRepository(repository)
        return repo.Count
    
    
    def ObjectsIn(self, repository):
        """
        Returns an iterator over all the objects in `repository`.
        `repository` is specified by the interface class, such as:
        
            - `ITextRepository`
            - `ILexEntryRepository`
            
        All repository names can be viewed by opening a project in
        LCMBrowser, which can be launched via the Help menu. Add "I" 
        to the front and import from `SIL.LCModel`.
        """

        repo = self.ObjectRepository(repository)
        return iter(repo.AllInstances())


    def Object(self, hvoOrGuid):
        """
        Returns the `CmObject` for the given Hvo or guid (`str` or `System.Guid`).
        Refer to `.ClassName` to determine the LCM class.
        """
        if isinstance(hvoOrGuid, str):
            try:
                hvoOrGuid = System.Guid(hvoOrGuid)
            except System.FormatException:
                raise FP_ParameterError("Invalid parameter, hvoOrGuid")
                
        if isinstance(hvoOrGuid, (System.Guid, int)):
            return self.project.ServiceLocator.GetObject(hvoOrGuid)
        else:
            raise FP_ParameterError("hvoOrGuid must be an Hvo (int), System.Guid or str")


    # --- Lexicon ---

    def LexiconNumberOfEntries(self):
        return self.ObjectCountFor(ILexEntryRepository)
        
    def LexiconAllEntries(self):
        """
        Returns an iterator over all entries in the lexicon.

        Each entry is of type::

          SIL.LCModel.ILexEntry, which contains:
              - HomographNumber :: integer
              - HomographForm :: string
              - LexemeFormOA ::  SIL.LCModel.IMoForm
                   - Form :: SIL.LCModel.MultiUnicodeAccessor
                      - GetAlternative : Get String for given WS type
                      - SetAlternative : Set string for given WS type
              - SensesOS :: Ordered collection of SIL.LCModel.ILexSense
                  - Gloss :: SIL.LCModel.MultiUnicodeAccessor
                  - Definition :: SIL.LCModel.MultiStringAccessor
                  - SenseNumber :: string
                  - ExamplesOS :: Ordered collection of ILexExampleSentence
                      - Example :: MultiStringAccessor

        Note: This method delegates to LexEntryOperations.GetAll() for single source of truth.
        """

        return self.LexEntry.GetAll()


    def LexiconAllEntriesSorted(self):
        """
        Returns an iterator over all entries in the lexicon sorted by
        the (lower-case) headword.
        """
        entries = [(str(e.HeadWord), e) for e in self.LexiconAllEntries()]

        for h, e in sorted(entries, key=lambda x: x[0].lower()):
            yield e
        

    #  Private writing system utilities
    
    def __WSHandle(self, languageTagOrHandle, defaultWS):
        if languageTagOrHandle == None:
            handle = defaultWS
        else:
            #print "Specified ws =", languageTagOrHandle
            if isinstance(languageTagOrHandle, str):
                handle = self.WSHandle(languageTagOrHandle)
            else:
                handle = languageTagOrHandle
        if not handle:
            raise FP_WritingSystemError(languageTagOrHandle)
        return handle

    def __WSHandleVernacular(self, languageTagOrHandle):
        return self.__WSHandle(languageTagOrHandle,
                               self.project.DefaultVernWs)

    def __WSHandleAnalysis(self, languageTagOrHandle):
        return self.__WSHandle(languageTagOrHandle,
                               self.project.DefaultAnalWs)
    
    def __NormaliseLangTag(self, languageTag):
        return languageTag.replace("-", "_").lower()
    
    #  Vernacular WS fields
    
    def LexiconGetHeadword(self, entry):
        """
        Returns the headword for `entry`.

        Note: This method now delegates to LexEntryOperations for single source of truth.
        """
        return self.LexEntry.GetHeadword(entry)

        
    def LexiconGetLexemeForm(self, entry, languageTagOrHandle=None):
        """
        Returns the lexeme form for `entry` in the default vernacular WS
        or other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to LexEntryOperations for single source of truth.
        """
        return self.LexEntry.GetLexemeForm(entry, languageTagOrHandle)


    def LexiconSetLexemeForm(self, entry, form, languageTagOrHandle=None):
        """
        Set the lexeme form for `entry`:
            - `form` is the new lexeme form string.
            - `languageTagOrHandle` specifies a non-default writing system.

        Note: This method now delegates to LexEntryOperations for single source of truth.
        """
        return self.LexEntry.SetLexemeForm(entry, form, languageTagOrHandle)
            
        
    def LexiconGetCitationForm(self, entry, languageTagOrHandle=None):
        """
        Returns the citation form for `entry` in the default vernacular WS
        or other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to LexEntryOperations for single source of truth.
        """
        return self.LexEntry.GetCitationForm(entry, languageTagOrHandle)

    def LexiconGetAlternateForm(self, entry, languageTagOrHandle=None):
        """
        Returns the Alternate form for the entry in the Default Vernacular WS
        or other WS as specified by languageTagOrHandle.
        """
        WSHandle = self.__WSHandleVernacular(languageTagOrHandle)

        # MultiUnicodeAccessor
        form = ITsString(entry.AlternateFormsOS.Form.get_String(WSHandle)).Text
        return form or ""


    def LexiconGetPublishInCount(self, entry):
        """
        Returns the number of dictionaries that `entry` is configured 
        to be published in.
        """
        return entry.PublishIn.Count

        
    def LexiconGetPronunciation(self, pronunciation, languageTagOrHandle=None):
        """
        Returns the form for `pronunciation` in the default vernacular WS
        or other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to PronunciationOperations for single source of truth.
        """
        return self.Pronunciations.GetForm(pronunciation, languageTagOrHandle)

        
    def LexiconGetExample(self, example, languageTagOrHandle=None):
        """
        Returns the example text in the default vernacular WS or
        other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to ExampleOperations for single source of truth.
        """
        return self.Examples.GetExample(example, languageTagOrHandle)

        
    def LexiconSetExample(self, example, newString, languageTagOrHandle=None):
        """
        Set the default vernacular string for `example`:
            - `newString` is the new string value.
            - `languageTagOrHandle` specifies a non-default writing system.

        NOTE: using this function will lose any formatting that might
        have been present in the example string.

        Note: This method now delegates to ExampleOperations for single source of truth.
        """
        return self.Examples.SetExample(example, newString, languageTagOrHandle)

        
    def LexiconGetExampleTranslation(self, translation, languageTagOrHandle=None):
        """
        Returns the translation of an example in the default analysis WS or
        other WS as specified by `languageTagOrHandle`.

        NOTE: Analysis language translations of example sentences are
        stored as a collection (list). E.g.::

            for translation in example.TranslationsOC:
                print (project.LexiconGetExampleTranslation(translation))

        Note: This method works with translation objects (ICmTranslation) directly.
        For getting translation text from an example object, use Examples.GetTranslation().
        """
        WSHandle = self.__WSHandleAnalysis(languageTagOrHandle)

        # Translation is a MultiString
        tr = ITsString(translation.Translation.get_String(WSHandle)).Text
        return tr or ""


    def LexiconGetSenseNumber(self, sense):
        """
        Returns the sense number for the sense. (This is not available
        directly from `ILexSense`.)

        Note: This method delegates to LexSenseOperations.GetSenseNumber() for single source of truth.
        """

        return self.Senses.GetSenseNumber(sense)


    #  Analysis WS fields

    def LexiconGetSenseGloss(self, sense, languageTagOrHandle=None):
        """
        Returns the gloss for the sense in the default analysis WS or
        other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.GetGloss(sense, languageTagOrHandle)

        
    def LexiconSetSenseGloss(self, sense, gloss, languageTagOrHandle=None):
        """
        Set the default analysis gloss for `sense`:
            - `gloss` is the new gloss string.
            - `languageTagOrHandle` specifies a non-default writing system.

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.SetGloss(sense, gloss, languageTagOrHandle)
    
    
    def LexiconGetSenseDefinition(self, sense, languageTagOrHandle=None):
        """
        Returns the definition for the sense in the default analysis WS or
        other WS as specified by `languageTagOrHandle`.

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.GetDefinition(sense, languageTagOrHandle)

    
    #  Non-string types
    
    def LexiconGetSensePOS(self, sense):
        """
        Returns the part of speech abbreviation for the sense.

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.GetPartOfSpeech(sense)

            
    def LexiconGetSenseSemanticDomains(self, sense):
        """
        Returns a list of semantic domain objects belonging to the sense.
        `ToString()` and `Hvo` are available.

        Methods available for SemanticDomainsRC::

             Count
             Add(Hvo)
             Contains(Hvo)
             Remove(Hvo)
             RemoveAll()

        Note: This method now delegates to LexSenseOperations for single source of truth.
        """
        return self.Senses.GetSemanticDomains(sense)

        
    def LexiconEntryAnalysesCount(self, entry):
        """
        Returns a count of the occurrences of the entry in the text corpus.

        NOTE: This calculation can produce slightly different results to 
        that shown in FieldWorks (where the same analysis in the same text 
        segment is only counted once in some displays). See LT-13997 for 
        more details.
        """
        
        # EntryAnalysesCount is not part of the interface ILexEntry, 
        # and you can't cast to LexEntry outside the LCM assembly 
        # because LexEntry is internal.
        # Therefore we use reflection since it is a public method which 
        # any instance of ILexEntry implements.
        # (Instructions from JohnT)

        count = ReflectionHelper.GetProperty(entry, "EntryAnalysesCount")
        return count


    def LexiconSenseAnalysesCount(self, sense):
        """
        Returns a count of the occurrences of the sense in the text corpus.

        Note: This method delegates to LexSenseOperations.GetAnalysesCount() for single source of truth.
        """

        return self.Senses.GetAnalysesCount(sense)


    # --- Lexicon: field functions ---

    def GetFieldID(self, className, fieldName):
        """
        Return the `FieldID` ('flid') for the given field of an LCM class.
        `className` and `fieldName` are strings, where `fieldName` may omit 
        the type suffix (e.g. 'OS'). Both are case-sensitive.
        For example, find the `FieldID` for academic domains with::
        
            GetFieldID("LexSense", "DomainTypes")
        """

        mdc = self.project.MetaDataCacheAccessor

        if fieldName[-2:] in ("OA", "OS", "OC", "RA", "RS", "RC"):
            fieldName = fieldName[:-2]

        try:
            # True=include base classes if needed.
            flid = mdc.GetFieldId(className, fieldName, True) 
        except (LcmInvalidFieldException, 
                LcmInvalidClassException) as e:
            # "from None" avoids confusion of both exceptions being reported.
            raise FP_ParameterError(e.Message) from None
        return flid
 
 
    def __ValidatedHvo(self, senseOrEntryOrHvo, fieldID):
        """
        Internal function to check for valid parameters to lexicon functions.
        """
        if not senseOrEntryOrHvo: raise FP_NullParameterError()
        if not fieldID: raise FP_NullParameterError()

        try:
            hvo = senseOrEntryOrHvo.Hvo
        except AttributeError:
            hvo = senseOrEntryOrHvo
        
        return hvo


    def GetCustomFieldValue(self, senseOrEntryOrHvo, fieldID,
                            languageTagOrHandle=None):
        """
        Returns the field value for String, MultiString, Integer 
        and List (both single and multiple) fields.
        Raises `FP_ParameterError` for other field types.
        
        `languageTagOrHandle` only applies to MultiStrings; if `None` the
        best analysis or venacular string is returned. 
        
        Note: if the field is a vernacular WS field, then the 
        `languageTagOrHandle` must be specified.
        """

        hvo = self.__ValidatedHvo(senseOrEntryOrHvo, fieldID)

        # Adapted from XDumper.cs::GetCustomFieldValue
        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        fieldType = CellarPropertyType(mdc.GetFieldType(fieldID))

        if fieldType in FLExLCM.CellarStringTypes:
            return ITsString(self.project.DomainDataByFlid.\
                             get_StringProp(hvo, fieldID))

        elif fieldType in FLExLCM.CellarMultiStringTypes:
            mua = self.project.DomainDataByFlid.get_MultiStringProp(hvo, fieldID)
            if languageTagOrHandle:
                WSHandle = self.__WSHandle(languageTagOrHandle, None)
                return mua.get_String(WSHandle)
            else:
                return ITsString(mua.BestAnalysisVernacularAlternative)

        elif fieldType == CellarPropertyType.Integer:
            return self.project.DomainDataByFlid.get_IntProp(hvo, fieldID)

        elif fieldType == CellarPropertyType.ReferenceAtom:
            item = self.project.DomainDataByFlid.get_ObjectProp(hvo, fieldID)
            if not item:
                return ""
            poss = self.ObjectRepository(ICmPossibilityRepository).GetObject(item)
            return poss.ShortName

        elif fieldType == CellarPropertyType.ReferenceCollection:
            numItems = self.project.DomainDataByFlid.get_VecSize(hvo, fieldID)
            getPossibilityObject = self.ObjectRepository(
                                        ICmPossibilityRepository).GetObject
            items = []
            for i in range(numItems):
                item = self.project.DomainDataByFlid.get_VecItem(hvo, fieldID, i)
                poss = getPossibilityObject(item)
                items.append(poss.ShortName)
            return items

        raise FP_ParameterError("GetCustomFieldValue: field is not a supported type")


    def LexiconFieldIsStringType(self, fieldID):
        """
        Returns `True` if the given field is a simple string type suitable
        for use with `LexiconAddTagToField()`, otherwise returns `False`.

        Delegates to: CustomFields.GetFieldType()
        """
        if not fieldID: raise FP_NullParameterError()

        field_type = self.CustomFields.GetFieldType(fieldID)
        return field_type == CellarPropertyType.String


    def LexiconFieldIsMultiType(self, fieldID):
        """
        Returns `True` if the given field is a multi string type
        (MultiUnicode or MultiString)

        Delegates to: CustomFields.IsMultiString()
        """
        if not fieldID: raise FP_NullParameterError()

        return self.CustomFields.IsMultiString(fieldID)

        
    def LexiconFieldIsAnyStringType(self, fieldID):
        """
        Returns `True` if the given field is any of the string types.

        Delegates to: CustomFields.GetFieldType()
        """
        if not fieldID: raise FP_NullParameterError()

        field_type = self.CustomFields.GetFieldType(fieldID)
        return field_type in (CellarPropertyType.String,
                              CellarPropertyType.MultiString,
                              CellarPropertyType.MultiUnicode)

        
        
    def LexiconGetFieldText(self, senseOrEntryOrHvo, fieldID,
                            languageTagOrHandle=None):
        """
        Return the text value for the given entry/sense and field ID.
        Provided for use with custom fields.
        Returns the empty string if the value is null.
        `languageTagOrHandle` only applies to MultiStrings; if `None` the
        default analysis writing system is returned. 
        
        Note: if the field is a vernacular WS field, then 
        `languageTagOrHandle` must be specified.

        For normal fields, the object can be used directly with 
        `get_String()`. E.g.::
        
            lexForm = lexEntry.LexemeFormOA
            lexEntryValue = ITsString(lexForm.Form.get_String(WSHandle)).Text
        """
        
        value = self.GetCustomFieldValue(senseOrEntryOrHvo, 
                                         fieldID,
                                         languageTagOrHandle)

        # (value.Text is None if the field is empty.)
        if value and value.Text and value.Text != "***":
            return value.Text
        else:
            return ""

        
    def LexiconSetFieldText(self, senseOrEntryOrHvo, fieldID, text, 
                            languageTagOrHandle=None):
        """
        Set the text value for the given entry/sense and field ID.
        Provided for use with custom fields.

        NOTE: writes the string in one writing system only (defaults
        to the default analysis WS).

        For normal fields the object can be used directly with
        `set_String()`. E.g.::
        
            lexForm = lexEntry.LexemeFormOA
            mkstr = TsStringUtils.MakeString("text to write", WSHandle) 
            lexForm.Form.set_String(WSHandle, mkstr)
        """

        if not self.writeEnabled: raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntryOrHvo, fieldID)
        
        WSHandle = self.__WSHandleAnalysis(languageTagOrHandle)

        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        fieldType = CellarPropertyType(mdc.GetFieldType(fieldID))

        tss = TsStringUtils.MakeString(text, WSHandle)
        
        if fieldType in FLExLCM.CellarStringTypes:
            try:
                self.project.DomainDataByFlid.SetString(hvo, fieldID, tss)
            except LcmInvalidFieldException as msg:
                # This exception indicates that the project is not in write mode
                raise FP_ReadOnlyError()
        elif fieldType in FLExLCM.CellarMultiStringTypes:
            # MultiUnicodeAccessor
            mua = self.project.DomainDataByFlid.get_MultiStringProp(hvo, fieldID)
            try:
                mua.set_String(WSHandle, tss)
            except LcmInvalidFieldException as msg:
                raise FP_ReadOnlyError()        
        else:
            raise FP_ParameterError("LexiconSetFieldText: field is not a supported type")
            

    def LexiconClearField(self, senseOrEntryOrHvo, fieldID):
        """
        Clears the string field or all of the strings (writing systems)
        in a multi-string field.
        Can be used to clear out a custom field.
        """

        if not self.writeEnabled: raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntryOrHvo, fieldID)

        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        fieldType = CellarPropertyType(mdc.GetFieldType(fieldID))
        
        if fieldType in FLExLCM.CellarStringTypes:
            try:
                self.project.DomainDataByFlid.SetString(hvo, fieldID, None)
            except LcmInvalidFieldException as msg:
                # This exception indicates that the project is not in write mode
                raise FP_ReadOnlyError()
        elif fieldType in FLExLCM.CellarMultiStringTypes:
            # MultiUnicodeAccessor
            mua = self.project.DomainDataByFlid.get_MultiStringProp(hvo, fieldID)
            try:
                for ws in (self.GetAllAnalysisWSs() | self.GetAllVernacularWSs()):
                    mua.set_String(self.WSHandle(ws), None)
            except LcmInvalidFieldException as msg:
                raise FP_ReadOnlyError()        
        else:
            raise FP_ParameterError("LexiconClearField: field is not a supported type")


    def LexiconSetFieldInteger(self, senseOrEntryOrHvo, fieldID, integer):
        """
        Sets the integer value for the given entry/sense and field ID.
        Provided for use with custom fields.
        """

        if not self.writeEnabled: raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntryOrHvo, fieldID)

        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        if CellarPropertyType(mdc.GetFieldType(fieldID)) != CellarPropertyType.Integer:
            raise FP_ParameterError("LexiconSetFieldInteger: field is not Integer type")

        if self.project.DomainDataByFlid.get_IntProp(hvo, fieldID) != integer:
            try:
                self.project.DomainDataByFlid.SetInt(hvo, fieldID, integer)
            except LcmInvalidFieldException as msg:
                # This exception indicates that the project is not in write mode
                raise FP_ReadOnlyError()


    def LexiconAddTagToField(self, senseOrEntryOrHvo, fieldID, tag):
        """
        Appends the tag string to the end of the given field in the
        sense or entry inserting a semicolon between tags.
        If the tag is already in the field then it isn't added.
        """

        s = self.LexiconGetFieldText(senseOrEntryOrHvo, fieldID)
                
        if s:
            if tag in s: return
            newText = "; ".join((s, tag))
        else:
            newText = tag

        self.LexiconSetFieldText(senseOrEntryOrHvo,
                                 fieldID,
                                 newText)

        return


    # --- Lexicon: list field functions ---

    def ListFieldPossibilityList(self, senseOrEntry, fieldID):
        """
        Return the `CmPossibilityList` object for the given list field.
        Raises an exception if the field is not a list (single/Atomic
        or multiple/Collection)
        """

        if not senseOrEntry: raise FP_NullParameterError()
        if not fieldID: raise FP_NullParameterError()

        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        fieldType = CellarPropertyType(mdc.GetFieldType(fieldID))
        if fieldType not in (CellarPropertyType.ReferenceAtom, 
                             CellarPropertyType.ReferenceCollection):
            raise FP_ParameterError("ListFieldPossibilityList: field must be a List type")
        return ICmPossibilityList(senseOrEntry.ReferenceTargetOwner(fieldID))


    def ListFieldPossibilities(self, senseOrEntry, fieldID):
        """
        Returns the `PossibilitiesOS` for the given list field. This
        is a list of `CmPossibility` objects.
        Raises an exception if the field is not a list (single/Atomic
        or multiple/Collection)
        
        Note: this returns the top-level `CmPossibility` objects. Subitems 
        can be found via the `SubPossibilitiesOS` attribute. Alternatively, 
        a flat list of all possible options can be obtained with::
        
            options = project.UnpackNestedPossibilityList(possibilities,
                                                          str, 
                                                          True)
        """

        pList = self.ListFieldPossibilityList(senseOrEntry, fieldID)
        return pList.PossibilitiesOS


    def ListFieldLookup(self, senseOrEntry, fieldID, value):
        """
        Looks up the value (a string) in the `CmPossibilityList` for the
        given field.
        Returns the `CmPossibility` object, or `None` if it can't be found.
        """
        
        pList = self.ListFieldPossibilityList(senseOrEntry, fieldID)
        wsa = self.lp.DefaultAnalysisWritingSystem.Handle
        return pList.FindPossibilityByName(pList.PossibilitiesOS,
                                           value,
                                           wsa)


    def LexiconSetListFieldSingle(self, 
                                  senseOrEntry, 
                                  fieldID, 
                                  possibilityOrString):
        """
        Sets the value for a 'single' (Atomic) list field.
        `possibilityOrString` can be a `CmPossibility` object, or a string.
        A string value can be the full name or the abbreviation (case-sensitive).
        
        Use `ListFieldPossibilities()` to find the valid values for the list.
        
        Note: this function is primarily for use with custom fields, 
        since regular list field values can be assigned directly. E.g.::
             
             status_poss = project.ListFieldPossibilities(
                               sense, 
                               project.GetFieldID("LexSense", "Status"))
             sense.StatusRA = status_poss[3]    # Tentative
        """

        if not self.writeEnabled: raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntry, fieldID)
        
        if type(possibilityOrString) is str:
            possibility = self.ListFieldLookup(senseOrEntry, 
                                               fieldID, 
                                               possibilityOrString)
            if not possibility:
                raise FP_ParameterError(f"'{possibilityOrString}' not found in the Possibility list")
        else:
            try:
                if possibilityOrString.ClassName == "CmPossibility":
                    possibility = possibilityOrString
                else:
                    raise AttributeError
            except AttributeError:
                raise FP_ParameterError("possibilityOrString must be a string or CmPossibility")

        self.project.DomainDataByFlid.SetObjProp(hvo, 
                                                 fieldID, 
                                                 possibility.Hvo)


    def LexiconClearListFieldSingle(self, 
                                    senseOrEntry, 
                                    fieldID):
        """
        Clears the value for a 'single' (Atomic) list field.
        """

        if not self.writeEnabled: raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntry, fieldID)
        
        self.project.DomainDataByFlid.SetObjProp(hvo, 
                                                 fieldID, 
                                                 0)


    def LexiconSetListFieldMultiple(self, 
                                    senseOrEntry, 
                                    fieldID,
                                    listOfValues):
        """
        Sets the value(s) for a 'multiple' (Collection) list field.
        `listOfValues` can be a list of:
        
            - `CmPossibility` objects; or
            - `CmPossibility` hvos; or
            - `str` (either the full name or the abbreviation; case-sensitive).

        Use `ListFieldPossibilities()` to find the valid values for the list.
        
        Note: this function is primarily for use with custom fields, 
        since regular fields can use the `Add()`, `Remove()` and `Clear()` 
        methods of the field itself (see LcmReferenceCollection).
        """
        
        if not self.writeEnabled: raise FP_ReadOnlyError()

        hvo = self.__ValidatedHvo(senseOrEntry, fieldID)
        
        if not listOfValues:
            raise FP_ParameterError("LexiconSetListFieldMultiple: listOfValues cannot be empty or None")

        if type(listOfValues[0]) is int:
            hvoList = listOfValues
        else:
            if type(listOfValues[0]) is str:
                possibilities = [self.ListFieldLookup(senseOrEntry,
                                                      fieldID, 
                                                      s)
                                 for s in listOfValues]
                if not all(possibilities):
                    raise FP_ParameterError("LexiconSetListFieldMultiple: one or more values not valid.")
            else:
                possibilities = listOfValues

            try:
                hvoList = [p.Hvo for p in possibilities]
            except AttributeError:
                raise FP_ParameterError("LexiconSetListFieldMultiple: listOfValues is not valid.")

        # Get the count of current items in the field
        ddbf = self.project.DomainDataByFlid
        numItems = ddbf.get_VecSize(senseOrEntry.Hvo, fieldID)

        # Replace the current items with the new list
        ddbf.Replace(senseOrEntry.Hvo, fieldID,
                     0, numItems,
                     hvoList, len(hvoList))


    # --- Lexicon: Custom fields ---
    
    def __GetCustomFieldsOfType(self, classID):
        """
        Generator for finding all the custom fields belonging to the
        given class.
        Returns tuples of (flid, label)
        """

        # The MetaDataCache defines the project structure: we can
        # find the custom fields in here.
        mdc = IFwMetaDataCacheManaged(self.project.MetaDataCacheAccessor)
        
        for flid in mdc.GetFields(classID, False, int(CellarPropertyTypeFilter.All)):
            if self.project.GetIsCustomField(flid):
                yield ((flid, mdc.GetFieldLabel(flid)))

    def __FindCustomField(self, classID, fieldName):
        for flid, name in self.__GetCustomFieldsOfType(classID):
            if name == fieldName:
                return flid
        return None


    def LexiconGetEntryCustomFields(self):
        """
        Returns a list of the custom fields defined at entry level.
        Each item in the list is a tuple of (flid, label)

        Delegates to: CustomFields.GetAllFields("LexEntry")
        """
        return self.CustomFields.GetAllFields("LexEntry")


    def LexiconGetSenseCustomFields(self):
        """
        Returns a list of the custom fields defined at sense level.
        Each item in the list is a tuple of (flid, label)

        Delegates to: CustomFields.GetAllFields("LexSense")
        """
        return self.CustomFields.GetAllFields("LexSense")


    def LexiconGetExampleCustomFields(self):
        """
        Returns a list of the custom fields defined at example level.
        Each item in the list is a tuple of (flid, label)

        Delegates to: CustomFields.GetAllFields("LexExampleSentence")
        """
        return self.CustomFields.GetAllFields("LexExampleSentence")
        
        
    def LexiconGetAllomorphCustomFields(self):
        """
        Returns a list of the custom fields defined at allomorph level.
        Each item in the list is a tuple of (flid, label)

        Delegates to: CustomFields.GetAllFields("MoForm")
        """
        return self.CustomFields.GetAllFields("MoForm")
        
        
    def LexiconGetEntryCustomFieldNamed(self, fieldName):
        """
        Return the entry-level field ID given its name.

        NOTE: `fieldName` is case-sensitive.

        Delegates to: CustomFields.FindField("LexEntry", name)
        """
        return self.CustomFields.FindField("LexEntry", fieldName)


    def LexiconGetSenseCustomFieldNamed(self, fieldName):
        """
        Return the sense-level field ID given its name.

        NOTE: `fieldName` is case-sensitive.

        Delegates to: CustomFields.FindField("LexSense", name)
        """
        return self.CustomFields.FindField("LexSense", fieldName)

        
    # --- Lexical Relations ---
    
    def GetLexicalRelationTypes(self):
        """
        Returns an iterator over `LexRefType` objects, which define a
        type of lexical relation, such as Part-Whole.

        Each `LexRefType` has:
            - `MembersOC`: containing zero or more `LexReference` objects.
            - `MappingType`: an enumeration defining the type of lexical relation.

        `LexReference` objects have:
            - `TargetsRS`: the `LexSense` or `LexEntry` objects in the relation.

        For example::

            for lrt in project.GetLexicalRelationTypes():
                if (lrt.MembersOC.Count > 0):
                    for lr in lrt.MembersOC:
                        for target in lr.TargetsRS:
                            if target.ClassName == "LexEntry":
                                # LexEntry
                            else:
                                # LexSense

        .. note::
           This method delegates to :meth:`LexReferenceOperations.GetAllTypes`.
        """
        return self.LexReferences.GetAllTypes()
        
    
    # --- Publications ---
    
    def GetPublications(self):
        """
        Returns a list of the names of the publications defined in the
        project.

        .. note::
           This method delegates to :meth:`PublicationOperations.GetAll`.
        """
        return [self.Publications.GetName(pub) for pub in self.Publications.GetAll()]


    def PublicationType(self, publicationName):
        """
        Returns the `PublicationType` object (a `CmPossibility`) for the
        given publication name. (A list of publication names can be
        found using `GetPublications()`.)

        .. note::
           This method delegates to :meth:`PublicationOperations.Find`.
        """
        return self.Publications.Find(publicationName)


    # --- Reversal Indices ---

    def ReversalIndex(self, languageTag):
        """
        Returns the reversal index for `languageTag` (eg 'en').
        Returns `None` if there is no reversal index for
        that writing system.

        .. note::
           This method delegates to :meth:`ReversalOperations.GetIndex`.
        """
        return self.Reversal.GetIndex(languageTag)


    def ReversalEntries(self, languageTag):
        """
        Returns an iterator for the reversal entries for `languageTag` (eg 'en').
        Returns `None` if there is no reversal index for that writing system.

        .. note::
           This method delegates to :meth:`ReversalOperations.GetIndex` and
           :meth:`ReversalOperations.GetAll`.
        """
        ri = self.Reversal.GetIndex(languageTag)
        if ri:
            return iter(self.Reversal.GetAll(ri))
        else:
            return None


    def ReversalGetForm(self, entry, languageTagOrHandle=None):
        """
        Returns the citation form for the reversal entry in the default
        vernacular WS or other WS as specified by `languageTagOrHandle`.

        .. note::
           This method delegates to :meth:`ReversalOperations.GetForm`.
        """
        return self.Reversal.GetForm(entry, languageTagOrHandle)


    def ReversalSetForm(self, entry, form, languageTagOrHandle=None):
        """
        Sets the default analysis reversal form for the given reversal entry:
            - `form` is the new reversal form string.
            - `languageTagOrHandle` specifies a non-default writing system.

        .. note::
           This method delegates to :meth:`ReversalOperations.SetForm`.
        """
        return self.Reversal.SetForm(entry, form, languageTagOrHandle)
    
    # --- Texts ---

    def TextsNumberOfTexts(self):
        """
        Returns the total number of texts in the project.

        Note: This method delegates to TextOperations.GetAll() for single source of truth.
        """

        return sum(1 for _ in self.Texts.GetAll())


    def TextsGetAll(self, supplyName=True, supplyText=True):
        """
        A generator that returns all the texts in the project as
        tuples of (`name`, `text`) where:

            - `name` is the best vernacular or analysis name.
            - `text` is a string with newlines separating paragraphs.

        Passing `supplyName`/`Text` = `False` returns only the texts or names.

        Note: This method now delegates to TextOperations.GetAll() for retrieving texts.
        """

        if not supplyText:
            for t in self.Texts.GetAll():
                yield ITsString(t.Name.BestVernacularAnalysisAlternative).Text
        else:
            for t in self.Texts.GetAll():
                content = []
                if t.ContentsOA:
                    for p in t.ContentsOA.ParagraphsOS:
                        if para := ITsString(IStTxtPara(p).Contents).Text:
                            content.append(para)

                if supplyName:
                    name = ITsString(t.Name.BestVernacularAnalysisAlternative).Text
                    yield name, "\n".join(content)
                else:
                    yield "\n".join(content)        

