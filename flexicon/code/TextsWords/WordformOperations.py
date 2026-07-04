#
#   WordformOperations.py
#
#   Class: WordformOperations
#          Wordform operations for FieldWorks Language Explorer projects
#          via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright Craig Farrow, 2008 - 2024
#

import logging

logger = logging.getLogger(__name__)

import clr

clr.AddReference("System")

from SIL.LCModel import (
    IWfiWordformRepository,
    IWfiWordformFactory,
    IWfiWordform,
    IWfiAnalysisFactory,
    IWfiGlossFactory,
    IWfiMorphBundleFactory,
)

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key

# --- Spelling Status Enum ---


class SpellingStatusStates:
    """Spelling status values for wordforms."""

    UNDECIDED = 0
    INCORRECT = 1
    CORRECT = 2


# --- WordformOperations Class ---


class WordformOperations(BaseOperations):
    """
    Provides operations for managing wordforms in a FLEx project.

    Wordforms represent surface forms of words as they appear in texts.
    Each wordform can have multiple analyses and a spelling status.

    This class should be accessed via FLExProject.Wordforms property.

    Example:
        >>> project = FLExProject()
        >>> project.OpenProject("MyProject")
        >>> # Get all wordforms
        >>> for wf in project.Wordforms.GetAll():
        ...     print(project.Wordforms.GetForm(wf))
        >>> # Create a new wordform
        >>> wf = project.Wordforms.Create("running")
        >>> # Set spelling status
        >>> project.Wordforms.SetSpellingStatus(wf, SpellingStatusStates.CORRECT)

    Known Limitations:
        - Deep copy of wordform analyses (deep=True in Duplicate) is not yet
          implemented. See Duplicate() method for details and workaround.
    """

    def __init__(self, project):
        """
        Initialize WordformOperations.

        Args:
            project: FLExProject instance
        """
        super().__init__(project)

    def __WSHandle(self, wsHandle):
        """
        Internal helper to resolve writing system handle.

        Args:
            wsHandle: Writing system handle (language tag or ID), or None for default

        Returns:
            int: Resolved writing system handle
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Retrieve all wordforms in the FLEx project.

        This method returns an iterator over all IWfiWordform objects in the
        project database, allowing iteration over the complete wordform inventory.

        Yields:
            IWfiWordform: Each wordform object in the project

        Example:
            >>> for wordform in project.Wordforms.GetAll():
            ...     form = project.Wordforms.GetForm(wordform)
            ...     print(form)

        Notes:
            - Returns an iterator for memory efficiency with large projects
            - Wordforms are returned in database order (not alphabetical)
            - Use GetForm() to access the surface text

        See Also:
            Find, Create, GetForm
        """
        return self.project.ObjectsIn(IWfiWordformRepository)

    @OperationsMethod
    def Create(self, form, wsHandle=None):
        """
        Create a new wordform in the FLEx project.

        Args:
            form: The surface text form of the wordform
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            IWfiWordform: The newly created wordform object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If form is empty or None

        Example:
            >>> wf = project.Wordforms.Create("running")
            >>> print(project.Wordforms.GetForm(wf))
            running
            >>> # Create in specific writing system
            >>> wf_fr = project.Wordforms.Create("courir", "fr")

        Notes:
            - New wordforms have UNDECIDED spelling status by default
            - The form is stored in the specified writing system
            - Does not check if wordform already exists - use Find() or Exists() first

        See Also:
            Exists, Find, Delete
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(form, "form")

        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM("Create wordform"):
            # Factory.Create() owns the wordform automatically in FLEx 9 LCM
            factory = self.project.project.ServiceLocator.GetService(IWfiWordformFactory)
            new_wf = factory.Create()

            # Set the form
            mkstr = TsStringUtils.MakeString(form, wsHandle)
            new_wf.Form.set_String(wsHandle, mkstr)

            return new_wf

    @OperationsMethod
    def Delete(self, wordform_or_hvo):
        """
        Delete a wordform from the FLEx project.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO (database ID)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("obsolete")
            >>> if wf:
            ...     project.Wordforms.Delete(wf)

        Warning:
            - This is a destructive operation
            - All analyses associated with the wordform will also be deleted
            - Consider setting spelling status to INCORRECT instead of deleting

        See Also:
            Create, SetSpellingStatus
        """
        self._EnsureWriteEnabled()

        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        # LCM Delete() removes the object from the repository
        wordform.Delete()

    @OperationsMethod
    def Exists(self, form, wsHandle=None):
        """
        Check if a wordform exists in the FLEx project.

        Args:
            form: The surface text form to check
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            bool: True if the wordform exists, False otherwise

        Example:
            >>> if project.Wordforms.Exists("running"):
            ...     wf = project.Wordforms.Find("running")
            ... else:
            ...     wf = project.Wordforms.Create("running")

        Notes:
            - Search is case-sensitive
            - Search is writing-system specific
            - Returns False for empty or whitespace-only forms

        See Also:
            Find, Create
        """
        if not form or not form.strip():
            return False

        return self.Find(form, wsHandle) is not None

    @OperationsMethod
    def Find(self, form, wsHandle=None):
        """
        Find and return a wordform by its surface form.

        Args:
            form: The surface text form to find
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            IWfiWordform or None: The wordform object if found, None otherwise

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> if wf:
            ...     status = project.Wordforms.GetSpellingStatus(wf)
            ...     print(f"Spelling status: {status}")

        Notes:
            - Search is case-sensitive
            - Search is writing-system specific
            - Returns None if wordform doesn't exist
            - Use Exists() for simple existence check

        See Also:
            Exists, GetAll, Create
        """
        if not form or not form.strip():
            return None

        wsHandle = self.__WSHandle(wsHandle)

        # Search through all wordforms
        target = normalize_match_key(form, casefold=False)
        for wf in self.GetAll():
            wf_form = ITsString(wf.Form.get_String(wsHandle)).Text
            if normalize_match_key(wf_form, casefold=False) == target:
                return wf

        return None

    @OperationsMethod
    def GetForm(self, wordform_or_hvo, wsHandle=None):
        """
        Get the surface text form of a wordform.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The text form of the wordform (empty string if not set)

        Raises:
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> for wf in project.Wordforms.GetAll():
            ...     form = project.Wordforms.GetForm(wf)
            ...     print(form)

        Notes:
            - Returns empty string if form not set in specified writing system
            - Default writing system is the default vernacular WS
            - Multi-string forms may exist in multiple writing systems

        See Also:
            SetForm, Find
        """
        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        wsHandle = self.__WSHandle(wsHandle)

        # Get the form string
        form = ITsString(wordform.Form.get_String(wsHandle)).Text
        return form or ""

    @OperationsMethod
    def SetForm(self, wordform_or_hvo, form, wsHandle=None):
        """
        Set the surface text form of a wordform.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO
            form: The new text form to set
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If form is empty or None
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("runing")  # misspelled
            >>> if wf:
            ...     project.Wordforms.SetForm(wf, "running")  # correct it

        Warning:
            - Changing a wordform's text may affect text parsing
            - May create duplicate if another wordform has same form
            - Use carefully - consider creating new wordform instead

        See Also:
            GetForm, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(wordform_or_hvo, "wordform_or_hvo")
        self._ValidateParam(form, "form")

        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        wsHandle = self.__WSHandle(wsHandle)

        # Set the form string
        mkstr = TsStringUtils.MakeString(form, wsHandle)
        wordform.Form.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetSpellingStatus(self, wordform_or_hvo):
        """
        Get the spelling status of a wordform.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO

        Returns:
            int: The current spelling status (0=UNDECIDED, 1=INCORRECT, 2=CORRECT)

        Raises:
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> status = project.Wordforms.GetSpellingStatus(wf)
            >>> if status == SpellingStatusStates.UNDECIDED:
            ...     project.Wordforms.SetSpellingStatus(wf, SpellingStatusStates.CORRECT)

        Notes:
            - New wordforms default to UNDECIDED status (0)
            - Status affects spell-checking and analysis suggestions
            - CORRECT status (2) indicates approved wordforms
            - INCORRECT status (1) marks known misspellings

        See Also:
            SetSpellingStatus, SpellingStatusStates
        """
        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        return wordform.SpellingStatus

    @OperationsMethod
    def SetSpellingStatus(self, wordform_or_hvo, status):
        """
        Set the spelling status of a wordform.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO
            status: The new spelling status (0, 1, or 2 from SpellingStatusStates)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_ParameterError: If wordform doesn't exist or status is invalid

        Example:
            >>> wf = project.Wordforms.Find("colour")
            >>> project.Wordforms.SetSpellingStatus(wf, SpellingStatusStates.CORRECT)
            >>>
            >>> typo = project.Wordforms.Find("teh")
            >>> project.Wordforms.SetSpellingStatus(typo, SpellingStatusStates.INCORRECT)

        Notes:
            - Use SpellingStatusStates enum for status values:
              - UNDECIDED (0): Not yet reviewed
              - INCORRECT (1): Known misspelling
              - CORRECT (2): Approved spelling

        See Also:
            GetSpellingStatus, SpellingStatusStates
        """
        self._EnsureWriteEnabled()

        if status not in (SpellingStatusStates.UNDECIDED, SpellingStatusStates.INCORRECT, SpellingStatusStates.CORRECT):
            raise FP_ParameterError(f"Invalid spelling status: {status}. Must be 0, 1, or 2.")

        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        wordform.SpellingStatus = status

    @OperationsMethod
    def GetAnalyses(self, wordform_or_hvo):
        """
        Get all analyses associated with a wordform.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO

        Returns:
            list: List of IWfiAnalysis objects for this wordform

        Raises:
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> for analysis in analyses:
            ...     # Process each analysis
            ...     print(f"Analysis HVO: {analysis.Hvo}")

        Notes:
            - Returns empty list if wordform has no analyses
            - Analyses may be human-created or parser-generated
            - Each analysis represents a possible linguistic interpretation

        See Also:
            GetAll, Find
        """
        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        return list(wordform.AnalysesOC)

    @OperationsMethod
    def GetOccurrenceCount(self, wordform_or_hvo):
        """
        Get the count of occurrences of a wordform in texts.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO

        Returns:
            int: Number of times this wordform appears in project texts

        Raises:
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> count = project.Wordforms.GetOccurrenceCount(wf)
            >>> print(f"'running' appears {count} times in texts")

        Notes:
            - Counts segment occurrences across all texts in the project
            - Returns 0 if wordform has no occurrences
            - Each occurrence represents a token in a text segment

        See Also:
            GetOccurrences, GetAll
        """
        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        # OccurrencesInTexts is IEnumerable[ISegment] (no .Count). The sibling
        # GetOccurrences method already materializes via list() -- match it
        # by counting via the iterator. See issue #16.
        return sum(1 for _ in wordform.OccurrencesInTexts)

    @OperationsMethod
    def GetOccurrences(self, wordform_or_hvo):
        """
        Get all segment occurrences of a wordform in texts.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO

        Returns:
            list: List of segment objects where this wordform appears

        Raises:
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> occurrences = project.Wordforms.GetOccurrences(wf)
            >>> for segment in occurrences:
            ...     # Process each text segment containing this wordform
            ...     print(f"Segment HVO: {segment.Hvo}")

        Notes:
            - Returns empty list if wordform has no occurrences
            - Each segment represents a location where the wordform appears
            - Segments belong to texts (paragraphs/sentences)

        See Also:
            GetOccurrenceCount, GetAll
        """
        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        return list(wordform.OccurrencesInTexts)

    @OperationsMethod
    def GetChecksum(self, wordform_or_hvo):
        """
        Get the checksum of a wordform.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO

        Returns:
            int: The wordform's checksum value

        Raises:
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> checksum = project.Wordforms.GetChecksum(wf)
            >>> print(f"Checksum: {checksum}")

        Notes:
            - Checksum is used for data integrity and change detection
            - The checksum value changes when wordform properties are modified
            - Useful for tracking modifications and synchronization

        See Also:
            GetForm, GetSpellingStatus
        """
        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        return wordform.Checksum

    @OperationsMethod
    def GetAllWithStatus(self, status):
        """
        Retrieve all wordforms with a specific spelling status.

        Args:
            status: The spelling status to filter by (from SpellingStatusStates)

        Yields:
            IWfiWordform: Each wordform object with the specified status

        Raises:
            FP_ParameterError: If status is invalid

        Example:
            >>> # Get all correctly spelled wordforms
            >>> correct_wfs = list(project.Wordforms.GetAllWithStatus(SpellingStatusStates.CORRECT))
            >>> print(f"Found {len(correct_wfs)} approved wordforms")
            >>>
            >>> # Get all misspellings
            >>> for wf in project.Wordforms.GetAllWithStatus(SpellingStatusStates.INCORRECT):
            ...     form = project.Wordforms.GetForm(wf)
            ...     print(f"Misspelling: {form}")

        Notes:
            - Returns an iterator for memory efficiency with large projects
            - Valid status values (from SpellingStatusStates):
              - UNDECIDED (0): Not yet reviewed
              - INCORRECT (1): Known misspelling
              - CORRECT (2): Approved spelling
            - Use list() to convert to a list if needed

        See Also:
            GetAllUnapproved, GetSpellingStatus, SpellingStatusStates
        """
        if status not in (SpellingStatusStates.UNDECIDED, SpellingStatusStates.INCORRECT, SpellingStatusStates.CORRECT):
            raise FP_ParameterError(f"Invalid spelling status: {status}. Must be 0, 1, or 2.")

        for wf in self.GetAll():
            if wf.SpellingStatus == status:
                yield wf

    @OperationsMethod
    def GetAllUnapproved(self):
        """
        Retrieve all wordforms that are not approved (not CORRECT status).

        Yields:
            IWfiWordform: Each wordform object with UNDECIDED or INCORRECT status

        Example:
            >>> # Get all unapproved wordforms
            >>> for wf in project.Wordforms.GetAllUnapproved():
            ...     form = project.Wordforms.GetForm(wf)
            ...     status = project.Wordforms.GetSpellingStatus(wf)
            ...     print(f"{form}: status={status}")
            >>>
            >>> # Count unapproved wordforms
            >>> unapproved_count = sum(1 for _ in project.Wordforms.GetAllUnapproved())
            >>> print(f"Total unapproved: {unapproved_count}")

        Notes:
            - Returns an iterator for memory efficiency with large projects
            - Includes both UNDECIDED (0) and INCORRECT (1) statuses
            - Excludes only CORRECT (2) status wordforms
            - Useful for spell-checking and wordform review workflows

        See Also:
            GetAllWithStatus, ApproveSpelling, GetSpellingStatus
        """
        for wf in self.GetAll():
            if wf.SpellingStatus != SpellingStatusStates.CORRECT:
                yield wf

    @OperationsMethod
    def ApproveSpelling(self, wordform_or_hvo):
        """
        Approve the spelling of a wordform by setting status to CORRECT.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("colour")
            >>> project.Wordforms.ApproveSpelling(wf)
            >>>
            >>> # Approve multiple wordforms
            >>> for wf in project.Wordforms.GetAllWithStatus(SpellingStatusStates.UNDECIDED):
            ...     if should_approve(wf):
            ...         project.Wordforms.ApproveSpelling(wf)

        Notes:
            - This is equivalent to SetSpellingStatus(wf, SpellingStatusStates.CORRECT)
            - Approved wordforms are marked as correctly spelled
            - Affects spell-checking and analysis suggestions
            - Convenience method for common approval workflow

        See Also:
            SetSpellingStatus, GetAllUnapproved, GetSpellingStatus
        """
        self._EnsureWriteEnabled()

        # Resolve to wordform object
        if isinstance(wordform_or_hvo, int):
            wordform = self.project.Object(wordform_or_hvo)
            if not isinstance(wordform, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            wordform = wordform_or_hvo

        wordform.SpellingStatus = SpellingStatusStates.CORRECT

    @OperationsMethod
    def Duplicate(self, item_or_hvo, deep=False):
        """
        Duplicate a wordform, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IWfiWordform object or HVO to duplicate.
            deep (bool): If True, also duplicate analyses.
                        If False (default), only copy wordform properties.

        Returns:
            IWfiWordform: The newly created duplicate with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> if wf:
            ...     dup = project.Wordforms.Duplicate(wf)
            ...     # Change the form to create a variant
            ...     project.Wordforms.SetForm(dup, "runnin'")
            ...     print(f"Duplicate: {project.Wordforms.GetForm(dup)}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - MultiString property: Form
            - Simple property: SpellingStatus
            - Analyses duplicated with full nested structure when deep=True
            - Occurrences are NOT copied (they reference specific text segments)

        Analysis Deep Copy (deep=True):
            When deep=True, all analyses are duplicated with their nested structures:

            What's Copied:
                - IWfiAnalysis objects (with new GUIDs)
                - CategoryRA reference (part of speech)
                - WfiGloss objects with Form MultiString (word-level translations)
                - WfiMorphBundle objects with Form MultiString
                  (IWfiMorphBundle has no Gloss field of its own; the
                  displayed gloss comes from SenseRA.Gloss)
                - Morph bundle references: SenseRA, MsaRA, MorphRA, InflClassRA

            What's NOT Copied:
                - EvaluationsRC (approval status) - duplicates start unapproved
                - OccurrencesRS (text segment references) - tied to original contexts

            Use Cases:
                - Creating variant wordforms with full linguistic analysis
                - Duplicating analyzed forms for comparative study
                - Preserving complex analyses when creating spelling variants

            Example:
                >>> wf = project.Wordforms.Find("running")
                >>> dup = project.Wordforms.Duplicate(wf, deep=True)
                >>> len(project.Wordforms.GetAnalyses(wf)) == len(project.Wordforms.GetAnalyses(dup))
                True

        See Also:
            Create, Delete, GetAnalyses
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Resolve to wordform object
        if isinstance(item_or_hvo, int):
            source = self.project.Object(item_or_hvo)
            if not isinstance(source, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
        else:
            source = item_or_hvo

        with self._TransactionCM("Duplicate wordform"):
            # Create new wordform using factory (auto-generates new GUID)
            factory = self.project.project.ServiceLocator.GetService(IWfiWordformFactory)
            duplicate = factory.Create()

            # Copy MultiString properties
            duplicate.Form.CopyAlternatives(source.Form)

            # Copy simple properties
            duplicate.SpellingStatus = source.SpellingStatus

            # Deep copy: duplicate analyses
            if deep and hasattr(source, "AnalysesOC") and source.AnalysesOC.Count > 0:
                # Get factories (retrieve once, reuse for all objects)
                analysis_factory = self.project.project.ServiceLocator.GetService(IWfiAnalysisFactory)
                gloss_factory = self.project.project.ServiceLocator.GetService(IWfiGlossFactory)
                bundle_factory = self.project.project.ServiceLocator.GetService(IWfiMorphBundleFactory)

                # Iterate through all analyses in the source wordform
                for source_analysis in source.AnalysesOC:
                    # Create new analysis with auto-generated GUID
                    new_analysis = analysis_factory.Create()

                    # Add to duplicate wordform BEFORE copying properties (critical for MultiStrings)
                    duplicate.AnalysesOC.Add(new_analysis)

                    # Copy Reference Atomic (RA) properties
                    if hasattr(source_analysis, "CategoryRA") and source_analysis.CategoryRA:
                        new_analysis.CategoryRA = source_analysis.CategoryRA

                    # Note: We intentionally do NOT copy EvaluationsRC (approval status)
                    # New duplicate analysis should start as unapproved

                    # Deep copy glosses (MeaningsOC - owned collection)
                    if hasattr(source_analysis, "MeaningsOC"):
                        for gloss in source_analysis.MeaningsOC:
                            new_gloss = gloss_factory.Create()
                            new_analysis.MeaningsOC.Add(new_gloss)
                            # Copy MultiString form
                            new_gloss.Form.CopyAlternatives(gloss.Form)

                    # Deep copy morph bundles (MorphBundlesOS - owned sequence)
                    if hasattr(source_analysis, "MorphBundlesOS"):
                        for bundle in source_analysis.MorphBundlesOS:
                            new_bundle = bundle_factory.Create()
                            new_analysis.MorphBundlesOS.Add(new_bundle)

                            # Copy MultiString properties
                            new_bundle.Form.CopyAlternatives(bundle.Form)
                            new_bundle.Gloss.CopyAlternatives(bundle.Gloss)

                            # Copy Reference Atomic (RA) properties
                            if hasattr(bundle, "SenseRA") and bundle.SenseRA:
                                new_bundle.SenseRA = bundle.SenseRA
                            if hasattr(bundle, "MsaRA") and bundle.MsaRA:
                                new_bundle.MsaRA = bundle.MsaRA
                            if hasattr(bundle, "MorphRA") and bundle.MorphRA:
                                new_bundle.MorphRA = bundle.MorphRA
                            if hasattr(bundle, "InflClassRA") and bundle.InflClassRA:
                                new_bundle.InflClassRA = bundle.InflClassRA

                logger.info(f"Deep copied {source.AnalysesOC.Count} analyses with nested structures")

            # Note: Occurrences (OccurrencesRS) are NOT copied as they reference
            # specific text segments in the corpus

            return duplicate

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a wordform.

        Args:
            item: The IWfiWordform object.

        Returns:
            dict: Dictionary of syncable properties with their values.

        Example:
            >>> props = project.Wordforms.GetSyncableProperties(wordform)
            >>> print(props['Form'])
            {'en': 'running'}
            >>> print(props['SpellingStatus'])
            2  # CORRECT

        Notes:
            - MultiString property: Form
            - Integer property: SpellingStatus (0=UNDECIDED, 1=INCORRECT, 2=CORRECT)
            - Does NOT include owned collections (analyses) - those are children
        """
        props = {}

        # MultiString property - Form
        if hasattr(item, "Form") and item.Form:
            props["Form"] = self.project.GetMultiStringDict(item.Form)

        # Integer property - SpellingStatus
        if hasattr(item, "SpellingStatus"):
            props["SpellingStatus"] = int(item.SpellingStatus)

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two wordforms for differences.

        Args:
            item1: First wordform object (from project 1)
            item2: Second wordform object (from project 2)
            ops1: Optional WordformOperations instance for project 1 (defaults to self)
            ops2: Optional WordformOperations instance for project 2 (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
                - is_different (bool): True if wordforms differ, False if identical
                - differences_dict (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> is_diff, diffs = ops1.CompareTo(wf1, wf2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} != {val2}")

        Notes:
            - Compares Form MultiString across all writing systems
            - Compares SpellingStatus integer value
            - Empty/null values are treated as equivalent
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}

        # Get all property keys from both items
        all_keys = set(props1.keys()) | set(props2.keys())

        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            # Compare values
            if self.project._CompareValues(val1, val2):
                # Values are different
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return (is_different, differences)
