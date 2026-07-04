#
#   WfiGlossOperations.py
#
#   Class: WfiGlossOperations
#          Wordform gloss operations for FieldWorks Language Explorer projects
#          via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import clr

clr.AddReference("System")

from SIL.LCModel import (
    IWfiGloss,
    IWfiGlossFactory,
    IWfiAnalysis,
)

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key

# --- WfiGlossOperations Class ---


class WfiGlossOperations(BaseOperations):
    """
    Provides operations for managing wordform glosses (WfiGloss) in a FLEx project.

    WfiGloss objects represent glosses (meanings/translations) for wordform analyses.
    Each WfiAnalysis can have multiple glosses in different writing systems.
    Glosses provide the semantic interpretation of an analyzed wordform.

    This class should be accessed via FLExProject.WfiGlosses property.

    Example:
        >>> project = FLExProject()
        >>> project.OpenProject("MyProject", writeEnabled=True)
        >>> # Get a wordform and its first analysis
        >>> wf = project.Wordforms.Find("running")
        >>> analyses = project.Wordforms.GetAnalyses(wf)
        >>> if analyses:
        ...     analysis = analyses[0]
        ...     # Get all glosses for the analysis
        ...     for gloss in project.WfiGlosses.GetAll(analysis):
        ...         form = project.WfiGlosses.GetForm(gloss)
        ...         print(f"Gloss: {form}")
        ...     # Create a new gloss
        ...     new_gloss = project.WfiGlosses.Create(analysis, "running", "en")
        ...     # Update gloss form
        ...     project.WfiGlosses.SetForm(new_gloss, "to run", "en")
        >>> project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize WfiGlossOperations.

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
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, analysis_or_hvo):
        """
        Retrieve all glosses for a wordform analysis.

        This method returns an iterator over all IWfiGloss objects associated with
        the specified analysis, allowing iteration over all meaning glosses.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Yields:
            IWfiGloss: Each gloss object for the analysis

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     for gloss in project.WfiGlosses.GetAll(analyses[0]):
            ...         form = project.WfiGlosses.GetForm(gloss)
            ...         print(form)

        Notes:
            - Returns an iterator for memory efficiency
            - Glosses are returned in the order they were added
            - Returns empty iterator if analysis has no glosses
            - Each gloss can have forms in multiple writing systems

        See Also:
            Create, Find, GetForm
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        # Resolve to analysis object
        if isinstance(analysis_or_hvo, int):
            analysis = self.project.Object(analysis_or_hvo)
            if not isinstance(analysis, IWfiAnalysis):
                raise FP_ParameterError("HVO does not refer to a wordform analysis")
        else:
            analysis = analysis_or_hvo

        # Yield all glosses from the Meanings collection
        for gloss in analysis.MeaningsOC:
            yield gloss

    @OperationsMethod
    def Create(self, analysis_or_hvo, form, wsHandle=None):
        """
        Create a new gloss for a wordform analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO
            form: The gloss text (meaning/translation)
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            IWfiGloss: The newly created gloss object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If analysis_or_hvo or form is None
            FP_ParameterError: If form is empty or analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     gloss = project.WfiGlosses.Create(analyses[0], "to run")
            ...     print(project.WfiGlosses.GetForm(gloss))
            to run
            >>> # Create with specific writing system
            >>> gloss_fr = project.WfiGlosses.Create(analyses[0], "courir", "fr")

        Notes:
            - New gloss is added to the analysis's Meanings collection
            - The form is stored in the specified writing system
            - Duplicate glosses are allowed (no uniqueness check)
            - Gloss is added at the end of the collection

        See Also:
            Delete, SetForm, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")
        self._ValidateParam(form, "form")

        if not form or not form.strip():
            raise FP_ParameterError("Gloss form cannot be empty")

        # Resolve to analysis object
        if isinstance(analysis_or_hvo, int):
            analysis = self.project.Object(analysis_or_hvo)
            if not isinstance(analysis, IWfiAnalysis):
                raise FP_ParameterError("HVO does not refer to a wordform analysis")
        else:
            analysis = analysis_or_hvo

        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM("Create gloss"):
            # Get the factory and create the gloss
            factory = self.project.project.ServiceLocator.GetService(IWfiGlossFactory)
            new_gloss = factory.Create()

            # Add to analysis's Meanings collection (must be done before setting properties)
            analysis.MeaningsOC.Add(new_gloss)

            # Set the form
            mkstr = TsStringUtils.MakeString(form, wsHandle)
            new_gloss.Form.set_String(wsHandle, mkstr)

            return new_gloss

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a wordform gloss.

        Args:
            item: The IWfiGloss object.

        Returns:
            dict: Dictionary of syncable properties with their values.

        Example:
            >>> props = project.WfiGlosses.GetSyncableProperties(gloss)
            >>> print(props['Form'])
            {'en': 'running', 'es': 'corriendo'}

        Notes:
            - MultiString property: Form
            - Form contains gloss text in multiple writing systems
        """
        props = {}

        # MultiString property - Form
        if hasattr(item, "Form") and item.Form:
            props["Form"] = self.project.GetMultiStringDict(item.Form)

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two wordform glosses for differences.

        Args:
            item1: First gloss object (from project 1)
            item2: Second gloss object (from project 2)
            ops1: Optional WfiGlossOperations instance for project 1 (defaults to self)
            ops2: Optional WfiGlossOperations instance for project 2 (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
                - is_different (bool): True if glosses differ, False if identical
                - differences_dict (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> is_diff, diffs = ops1.CompareTo(gloss1, gloss2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} != {val2}")

        Notes:
            - Compares Form MultiString across all writing systems
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

    @OperationsMethod
    def Delete(self, gloss_or_hvo):
        """
        Delete a gloss from its owning analysis.

        Args:
            gloss_or_hvo: Either an IWfiGloss object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If gloss_or_hvo is None
            FP_ParameterError: If gloss doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     glosses = list(project.WfiGlosses.GetAll(analyses[0]))
            ...     if len(glosses) > 1:
            ...         # Delete the last gloss
            ...         project.WfiGlosses.Delete(glosses[-1])

        Warning:
            - This is a destructive operation
            - Deletion is permanent and cannot be undone
            - Consider backing up data before deletion
            - Text segments that reference this gloss may be affected

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(gloss_or_hvo, "gloss_or_hvo")

        # Resolve to gloss object
        if isinstance(gloss_or_hvo, int):
            gloss = self.project.Object(gloss_or_hvo)
            if not isinstance(gloss, IWfiGloss):
                raise FP_ParameterError("HVO does not refer to a wordform gloss")
        else:
            gloss = gloss_or_hvo

        # Get the owning analysis; MeaningsOC is declared on IWfiAnalysis so
        # cast unconditionally to surface the typed collection accessor.
        analysis = IWfiAnalysis(gloss.Owner)

        # Remove from analysis's Meanings collection
        analysis.MeaningsOC.Remove(gloss)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=False):
        """
        Duplicate a wordform gloss, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IWfiGloss object or HVO to duplicate.
            insert_after (bool): Ignored. MeaningsOC is an unordered
                ILcmOwningCollection with no Insert() method and no concept of
                positional ordering. The duplicate is always appended via Add().

        Returns:
            IWfiGloss: The newly created duplicate gloss with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     glosses = list(project.WfiGlosses.GetAll(analyses[0]))
            ...     if glosses:
            ...         # Duplicate gloss
            ...         dup = project.WfiGlosses.Duplicate(glosses[0])
            ...         print(f"Original: {project.WfiGlosses.GetGuid(glosses[0])}")
            ...         print(f"Duplicate: {project.WfiGlosses.GetGuid(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321
            ...
            ...         # Verify content was copied
            ...         print(f"Form: {project.WfiGlosses.GetForm(dup)}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - MeaningsOC is unordered; the duplicate is appended via Add()
            - Simple properties copied: Form (MultiString in all writing systems)
            - Reference properties: None (WfiGloss has no reference properties)
            - WfiGloss has no owned objects, so deep parameter has no effect

        See Also:
            Create, Delete, GetGuid
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Resolve to gloss object
        if isinstance(item_or_hvo, int):
            source = self.project.Object(item_or_hvo)
            if not isinstance(source, IWfiGloss):
                raise FP_ParameterError("HVO does not refer to a wordform gloss")
        else:
            source = item_or_hvo

        parent = self._GetObject(source.Owner.Hvo)

        with self._TransactionCM("Duplicate gloss"):
            # Create new gloss using factory (auto-generates new GUID)
            factory = self.project.project.ServiceLocator.GetService(IWfiGlossFactory)
            duplicate = factory.Create()

            # MeaningsOC is unordered; always append via Add().
            parent.MeaningsOC.Add(duplicate)

            # Copy simple MultiString properties
            duplicate.Form.CopyAlternatives(source.Form)

            # Note: WfiGloss has no owned objects (OS collections), so deep has no effect

            return duplicate

    # --- Form Management Operations ---

    @OperationsMethod
    def GetForm(self, gloss_or_hvo, wsHandle=None):
        """
        Get the gloss text form.

        Args:
            gloss_or_hvo: Either an IWfiGloss object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The gloss text (empty string if not set)

        Raises:
            FP_NullParameterError: If gloss_or_hvo is None
            FP_ParameterError: If gloss doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     for gloss in project.WfiGlosses.GetAll(analyses[0]):
            ...         form = project.WfiGlosses.GetForm(gloss)
            ...         print(form)

        Notes:
            - Returns empty string if form not set in specified writing system
            - Default writing system is the default analysis WS
            - Gloss can have different forms in multiple writing systems

        See Also:
            SetForm, GetAllForms
        """
        self._ValidateParam(gloss_or_hvo, "gloss_or_hvo")

        # Resolve to gloss object
        if isinstance(gloss_or_hvo, int):
            gloss = self.project.Object(gloss_or_hvo)
            if not isinstance(gloss, IWfiGloss):
                raise FP_ParameterError("HVO does not refer to a wordform gloss")
        else:
            gloss = gloss_or_hvo

        wsHandle = self.__WSHandle(wsHandle)

        # Get the form string
        form = ITsString(gloss.Form.get_String(wsHandle)).Text
        return form or ""

    @OperationsMethod
    def SetForm(self, gloss_or_hvo, text, wsHandle=None):
        """
        Set the gloss text form.

        Args:
            gloss_or_hvo: Either an IWfiGloss object or its HVO
            text: The new gloss text
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If gloss_or_hvo or text is None
            FP_ParameterError: If gloss doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     glosses = list(project.WfiGlosses.GetAll(analyses[0]))
            ...     if glosses:
            ...         project.WfiGlosses.SetForm(glosses[0], "to run quickly")
            ...         print(project.WfiGlosses.GetForm(glosses[0]))
            to run quickly
            >>> # Set form in multiple writing systems
            >>> project.WfiGlosses.SetForm(glosses[0], "courir", "fr")
            >>> project.WfiGlosses.SetForm(glosses[0], "correr", "es")

        Notes:
            - Empty string is allowed (clears the gloss in that writing system)
            - Gloss can be set independently in multiple writing systems
            - Use this to provide translations in different languages

        See Also:
            GetForm, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(gloss_or_hvo, "gloss_or_hvo")
        self._ValidateParam(text, "text")

        # Resolve to gloss object
        if isinstance(gloss_or_hvo, int):
            gloss = self.project.Object(gloss_or_hvo)
            if not isinstance(gloss, IWfiGloss):
                raise FP_ParameterError("HVO does not refer to a wordform gloss")
        else:
            gloss = gloss_or_hvo

        wsHandle = self.__WSHandle(wsHandle)

        # Set the form string
        mkstr = TsStringUtils.MakeString(text, wsHandle)
        gloss.Form.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetAllForms(self, gloss_or_hvo):
        """
        Get all available forms for a gloss across all writing systems.

        Args:
            gloss_or_hvo: Either an IWfiGloss object or its HVO

        Returns:
            dict: Dictionary mapping writing system handles to form text

        Raises:
            FP_NullParameterError: If gloss_or_hvo is None
            FP_ParameterError: If gloss doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     glosses = list(project.WfiGlosses.GetAll(analyses[0]))
            ...     if glosses:
            ...         forms = project.WfiGlosses.GetAllForms(glosses[0])
            ...         for ws_handle, form in forms.items():
            ...             print(f"WS {ws_handle}: {form}")

        Notes:
            - Returns only writing systems where form is set
            - Dictionary keys are writing system handles (integers)
            - Use project.GetWritingSystemName(ws) to get WS names
            - Empty forms are excluded from results

        See Also:
            GetForm, SetForm
        """
        self._ValidateParam(gloss_or_hvo, "gloss_or_hvo")

        # Resolve to gloss object
        if isinstance(gloss_or_hvo, int):
            gloss = self.project.Object(gloss_or_hvo)
            if not isinstance(gloss, IWfiGloss):
                raise FP_ParameterError("HVO does not refer to a wordform gloss")
        else:
            gloss = gloss_or_hvo

        forms = {}
        # Iterate through available writing systems
        for ws in gloss.Form.AvailableWritingSystemIds:
            form_text = ITsString(gloss.Form.get_String(ws)).Text
            if form_text:
                forms[ws] = form_text

        return forms

    # --- Utility Operations ---

    @OperationsMethod
    def GetOwningAnalysis(self, gloss_or_hvo):
        """
        Get the wordform analysis that owns this gloss.

        Args:
            gloss_or_hvo: Either an IWfiGloss object or its HVO

        Returns:
            IWfiAnalysis: The owning analysis object

        Raises:
            FP_NullParameterError: If gloss_or_hvo is None
            FP_ParameterError: If gloss doesn't exist

        Example:
            >>> # Find a gloss and get its owning analysis
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     glosses = list(project.WfiGlosses.GetAll(analyses[0]))
            ...     if glosses:
            ...         analysis = project.WfiGlosses.GetOwningAnalysis(glosses[0])
            ...         print(f"Analysis HVO: {analysis.Hvo}")

        Notes:
            - Gloss is owned by exactly one analysis
            - Use this to navigate from gloss back to analysis
            - Useful for accessing other analysis properties

        See Also:
            GetAll, GetGuid
        """
        self._ValidateParam(gloss_or_hvo, "gloss_or_hvo")

        # Resolve to gloss object
        if isinstance(gloss_or_hvo, int):
            gloss = self.project.Object(gloss_or_hvo)
            if not isinstance(gloss, IWfiGloss):
                raise FP_ParameterError("HVO does not refer to a wordform gloss")
        else:
            gloss = gloss_or_hvo

        # Cast to declared return type IWfiAnalysis. Raw gloss.Owner is typed
        # as ICmObject in LCM; pythonnet only surfaces IWfiAnalysis properties
        # (e.g. MorphBundlesOS) after the explicit interface cast.
        return IWfiAnalysis(gloss.Owner)

    @OperationsMethod
    def GetGuid(self, gloss_or_hvo):
        """
        Get the GUID (Global Unique Identifier) for a gloss.

        Args:
            gloss_or_hvo: Either an IWfiGloss object or its HVO

        Returns:
            System.Guid: The GUID of the gloss

        Raises:
            FP_NullParameterError: If gloss_or_hvo is None
            FP_ParameterError: If gloss doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     glosses = list(project.WfiGlosses.GetAll(analyses[0]))
            ...     if glosses:
            ...         guid = project.WfiGlosses.GetGuid(glosses[0])
            ...         print(f"Gloss GUID: {guid}")

        Notes:
            - GUID is unique across all projects
            - GUID remains constant even if object moves
            - Useful for cross-referencing between projects
            - HVO is project-specific, GUID is universal

        See Also:
            GetOwningAnalysis, Find
        """
        self._ValidateParam(gloss_or_hvo, "gloss_or_hvo")

        # Resolve to gloss object
        if isinstance(gloss_or_hvo, int):
            gloss = self.project.Object(gloss_or_hvo)
            if not isinstance(gloss, IWfiGloss):
                raise FP_ParameterError("HVO does not refer to a wordform gloss")
        else:
            gloss = gloss_or_hvo

        return gloss.Guid

    @OperationsMethod
    def Find(self, analysis_or_hvo, form, wsHandle=None):
        """
        Find and return a gloss by its form text.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO
            form: The gloss text to find
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            IWfiGloss or None: The gloss object if found, None otherwise

        Raises:
            FP_NullParameterError: If analysis_or_hvo or form is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     gloss = project.WfiGlosses.Find(analyses[0], "to run")
            ...     if gloss:
            ...         print(f"Found gloss: {gloss.Hvo}")
            ...     else:
            ...         print("Gloss not found")

        Notes:
            - Search is case-sensitive
            - Search is writing-system specific
            - Returns None if gloss doesn't exist
            - Returns first match if multiple glosses have same form
            - Use Exists() for simple existence check

        See Also:
            Exists, GetAll, Create
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")
        self._ValidateParam(form, "form")

        if not form or not form.strip():
            return None

        # Resolve to analysis object
        if isinstance(analysis_or_hvo, int):
            analysis = self.project.Object(analysis_or_hvo)
            if not isinstance(analysis, IWfiAnalysis):
                raise FP_ParameterError("HVO does not refer to a wordform analysis")
        else:
            analysis = analysis_or_hvo

        wsHandle = self.__WSHandle(wsHandle)

        # Search through all glosses
        target = normalize_match_key(form, casefold=False)
        for gloss in self.GetAll(analysis):
            gloss_form = ITsString(gloss.Form.get_String(wsHandle)).Text
            if normalize_match_key(gloss_form, casefold=False) == target:
                return gloss

        return None

    @OperationsMethod
    def Exists(self, analysis_or_hvo, form, wsHandle=None):
        """
        Check if a gloss with the specified form exists for an analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO
            form: The gloss text to check
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            bool: True if the gloss exists, False otherwise

        Raises:
            FP_NullParameterError: If analysis_or_hvo or form is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     if project.WfiGlosses.Exists(analyses[0], "to run"):
            ...         gloss = project.WfiGlosses.Find(analyses[0], "to run")
            ...     else:
            ...         gloss = project.WfiGlosses.Create(analyses[0], "to run")

        Notes:
            - Search is case-sensitive
            - Search is writing-system specific
            - Returns False for empty or whitespace-only forms
            - More efficient than Find() when you only need existence check

        See Also:
            Find, Create
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")
        self._ValidateParam(form, "form")

        if not form or not form.strip():
            return False

        return self.Find(analysis_or_hvo, form, wsHandle) is not None

    @OperationsMethod
    def GetCount(self, analysis_or_hvo):
        """
        Get the count of glosses for a wordform analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            int: Number of glosses

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     count = project.WfiGlosses.GetCount(analyses[0])
            ...     print(f"This analysis has {count} glosses")

        Notes:
            - More efficient than len(list(GetAll())) for counting
            - Returns 0 if analysis has no glosses
            - Each gloss may have forms in multiple writing systems

        See Also:
            GetAll, Create
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        # Resolve to analysis object
        if isinstance(analysis_or_hvo, int):
            analysis = self.project.Object(analysis_or_hvo)
            if not isinstance(analysis, IWfiAnalysis):
                raise FP_ParameterError("HVO does not refer to a wordform analysis")
        else:
            analysis = analysis_or_hvo

        return analysis.MeaningsOC.Count

    @OperationsMethod
    def GetBestForm(self, gloss_or_hvo):
        """
        Get the best available form for a gloss.

        This method attempts to find a suitable gloss form by checking writing
        systems in order of preference: default analysis WS, then any available WS.

        Args:
            gloss_or_hvo: Either an IWfiGloss object or its HVO

        Returns:
            str: The best available gloss form (empty string if none found)

        Raises:
            FP_NullParameterError: If gloss_or_hvo is None
            FP_ParameterError: If gloss doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     for gloss in project.WfiGlosses.GetAll(analyses[0]):
            ...         best = project.WfiGlosses.GetBestForm(gloss)
            ...         print(f"Best form: {best}")

        Notes:
            - Tries default analysis WS first
            - Falls back to first available WS if default not set
            - Returns empty string if no forms are set
            - Useful when you need any available form

        See Also:
            GetForm, GetAllForms
        """
        self._ValidateParam(gloss_or_hvo, "gloss_or_hvo")

        # Resolve to gloss object
        if isinstance(gloss_or_hvo, int):
            gloss = self.project.Object(gloss_or_hvo)
            if not isinstance(gloss, IWfiGloss):
                raise FP_ParameterError("HVO does not refer to a wordform gloss")
        else:
            gloss = gloss_or_hvo

        # Try default analysis WS first
        default_ws = self.project.project.DefaultAnalWs
        best_form = ITsString(gloss.Form.get_String(default_ws)).Text
        if best_form:
            return best_form

        # Try any available writing system
        for ws in gloss.Form.AvailableWritingSystemIds:
            form_text = ITsString(gloss.Form.get_String(ws)).Text
            if form_text:
                return form_text

        return ""

    @OperationsMethod
    def CopyGloss(self, gloss_or_hvo, target_analysis_or_hvo):
        """
        Copy a gloss to another analysis.

        Creates a new gloss in the target analysis with all forms from the source gloss.

        Args:
            gloss_or_hvo: Either an IWfiGloss object or its HVO (source)
            target_analysis_or_hvo: Either an IWfiAnalysis object or its HVO (target)

        Returns:
            IWfiGloss: The newly created gloss in the target analysis

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If gloss_or_hvo or target_analysis_or_hvo is None
            FP_ParameterError: If gloss or analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if len(analyses) > 1:
            ...     glosses = list(project.WfiGlosses.GetAll(analyses[0]))
            ...     if glosses:
            ...         # Copy first gloss from first analysis to second
            ...         new_gloss = project.WfiGlosses.CopyGloss(glosses[0], analyses[1])
            ...         print(f"Copied gloss: {project.WfiGlosses.GetForm(new_gloss)}")

        Notes:
            - Copies all writing system forms from source to target
            - Creates a new gloss object (not a reference)
            - Useful for sharing glosses between analyses

        See Also:
            Create, GetAllForms
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(gloss_or_hvo, "gloss_or_hvo")
        self._ValidateParam(target_analysis_or_hvo, "target_analysis_or_hvo")

        # Resolve to gloss object
        if isinstance(gloss_or_hvo, int):
            source_gloss = self.project.Object(gloss_or_hvo)
            if not isinstance(source_gloss, IWfiGloss):
                raise FP_ParameterError("HVO does not refer to a wordform gloss")
        else:
            source_gloss = gloss_or_hvo

        # Resolve to target analysis object
        if isinstance(target_analysis_or_hvo, int):
            target_analysis = self.project.Object(target_analysis_or_hvo)
            if not isinstance(target_analysis, IWfiAnalysis):
                raise FP_ParameterError("HVO does not refer to a wordform analysis")
        else:
            target_analysis = target_analysis_or_hvo

        with self._TransactionCM("Copy gloss"):
            # Create new gloss
            factory = self.project.project.ServiceLocator.GetService(IWfiGlossFactory)
            new_gloss = factory.Create()

            # Add to target analysis (must be done before setting properties)
            target_analysis.MeaningsOC.Add(new_gloss)

            # Copy all forms
            for ws in source_gloss.Form.AvailableWritingSystemIds:
                form_text = ITsString(source_gloss.Form.get_String(ws)).Text
                if form_text:
                    mkstr = TsStringUtils.MakeString(form_text, ws)
                    new_gloss.Form.set_String(ws, mkstr)

            return new_gloss

    @OperationsMethod
    def ClearForm(self, gloss_or_hvo, wsHandle=None):
        """
        Clear the form for a gloss in a specific writing system.

        Args:
            gloss_or_hvo: Either an IWfiGloss object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If gloss_or_hvo is None
            FP_ParameterError: If gloss doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.Wordforms.GetAnalyses(wf)
            >>> if analyses:
            ...     glosses = list(project.WfiGlosses.GetAll(analyses[0]))
            ...     if glosses:
            ...         # Clear the English form
            ...         project.WfiGlosses.ClearForm(glosses[0], "en")

        Notes:
            - Only clears the form in the specified writing system
            - Forms in other writing systems are not affected
            - Equivalent to SetForm(gloss, "", ws)
            - Gloss object itself is not deleted

        See Also:
            SetForm, Delete
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(gloss_or_hvo, "gloss_or_hvo")

        self.SetForm(gloss_or_hvo, "", wsHandle)
