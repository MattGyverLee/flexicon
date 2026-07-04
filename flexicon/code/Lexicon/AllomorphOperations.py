#
#   AllomorphOperations.py
#
#   Class: AllomorphOperations
#          Allomorph operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import FLEx LCM types
from SIL.LCModel import (
    IMoForm,
    IMoStemAllomorphFactory,
    IMoAffixAllomorphFactory,
    ILexEntry,
    IPhEnvironment,
    MoMorphTypeTags,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import string utilities
from ..Shared.string_utils import normalize_text

# Import wrapper classes
from .allomorph import Allomorph
from .allomorph_collection import AllomorphCollection


class AllomorphOperations(BaseOperations):
    """
    This class provides operations for managing allomorphs in a FieldWorks project.

    Allomorphs are variant forms of morphemes that appear in different phonological
    or morphological contexts. For example, the English plural morpheme has
    allomorphs "-s", "-es", and "-en" (ox/oxen).

    Usage::

        from flexlibs2 import FLExProject, AllomorphOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        allomorphOps = AllomorphOperations(project)

        # Get entry
        entry = project.LexiconAllEntries()[0]

        # Get all allomorphs for an entry
        for allomorph in allomorphOps.GetAll(entry):
            form = allomorphOps.GetForm(allomorph)
            print(f"Allomorph: {form}")

        # Create a new allomorph
        morphType = project.lp.MorphTypesOA.PossibilitiesOS[0]
        allomorph = allomorphOps.Create(entry, "walk", morphType)

        # Set phonological environment
        env = project.lp.PhonologicalDataOA.EnvironmentsOS[0]
        allomorphOps.AddPhoneEnv(allomorph, env)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize AllomorphOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for allomorphs.
        For Allomorph, we reorder entry.AlternateFormsOS
        """
        return parent.AlternateFormsOS

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, entry_or_hvo=None):
        """
        Get all allomorphs for a lexical entry, or all allomorphs in the entire project.

        Returns a smart collection of wrapped allomorph objects that transparently
        handle the two concrete types (MoStemAllomorph and MoAffixAllomorph).

        Args:
            entry_or_hvo: The ILexEntry object or HVO. If None, iterates all allomorphs
                         in the entire project.

        Returns:
            AllomorphCollection: Smart collection of Allomorph wrapper objects
                showing type breakdown and supporting filtered queries.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>>
            >>> # Get all allomorphs for specific entry
            >>> allomorphs = allomorphOps.GetAll(entry)
            >>> print(allomorphs)  # Shows type breakdown
            # AllomorphCollection (8 total)
            #   MoStemAllomorph: 5 (62%)
            #   MoAffixAllomorph: 3 (38%)
            >>>
            >>> # Iterate through wrapped objects
            >>> for allomorph in allomorphs:
            ...     print(f"Form: {allomorph.form}, Type: {allomorph.class_type}")
            Form: run, Type: MoStemAllomorph
            Form: ran, Type: MoStemAllomorph
            Form: running, Type: MoStemAllomorph
            >>>
            >>> # Filter by type
            >>> stems = allomorphs.stem_allomorphs()
            >>> print(f"Found {len(stems)} stem allomorphs")
            Found 5 stem allomorphs
            >>>
            >>> # Filter by form
            >>> ing_forms = allomorphs.filter(form_contains='ing')
            >>> for allomorph in ing_forms:
            ...     print(allomorph.form)
            running
            >>>
            >>> # Chain filters
            >>> ing_stems = allomorphs.stem_allomorphs().filter(form_contains='ing')
            >>>
            >>> # Get ALL allomorphs in entire project
            >>> all_project_allomorphs = allomorphOps.GetAll()
            >>> print(f"Project has {len(all_project_allomorphs)} allomorphs")

        Notes:
            - Returns AllomorphCollection (smart collection) not raw generator
            - When entry_or_hvo is provided:
              - Returns the lexeme form first (if it exists)
              - Then returns all alternate forms
              - Order follows FLEx database order
              - Returns empty collection if entry has no allomorphs
            - When entry_or_hvo is None:
              - Iterates ALL entries in the project
              - For each entry, yields lexeme form then alternate forms
              - Useful for project-wide allomorph operations
            - AllomorphCollection shows type breakdown and supports filtering
            - Use convenience methods like stem_allomorphs() and affix_allomorphs()
            - Use filter() for form-based filtering
            - Use where() for complex custom filtering
            - Individual items are Allomorph wrapper objects with properties like
              form, environment, is_stem_allomorph, is_affix_allomorph

        See Also:
            Create, GetForm, AllomorphCollection, Allomorph
        """
        # Collect all allomorphs
        allomorphs = []

        if entry_or_hvo is None:
            # Iterate ALL allomorphs in entire project
            for entry in self.project.lexDB.Entries:
                # First add the lexeme form if it exists
                if entry.LexemeFormOA:
                    allomorphs.append(Allomorph(entry.LexemeFormOA))

                # Then add all alternate forms
                for allomorph in entry.AlternateFormsOS:
                    allomorphs.append(Allomorph(allomorph))
        else:
            # Iterate allomorphs for specific entry
            entry = self.__GetEntryObject(entry_or_hvo)

            # First add the lexeme form if it exists
            if entry.LexemeFormOA:
                allomorphs.append(Allomorph(entry.LexemeFormOA))

            # Then add all alternate forms
            for allomorph in entry.AlternateFormsOS:
                allomorphs.append(Allomorph(allomorph))

        # Return smart collection
        return AllomorphCollection(allomorphs)

    @OperationsMethod
    def Create(self, entry_or_hvo, form, morphType=None, wsHandle=None):
        """
        Create a new allomorph for a lexical entry.

        Args:
            entry_or_hvo: The ILexEntry object or HVO.
            form (str): The allomorph form (e.g., "-ing", "walk", "pre-").
            morphType (IMoMorphType | str | None): The morpheme type.  Pass an
                IMoMorphType object, a name string (e.g. 'suffix', '=enclitic',
                '-prefix'), or None to inherit from the entry's LexemeFormOA
                morph type (matching FLEx GUI behaviour).  Display markers are
                stripped automatically so UI-copied names resolve correctly.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            IMoForm: The newly created allomorph object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If entry_or_hvo or form is None.
            FP_ParameterError: If form is empty or entry has no LexemeFormOA when
                morphType is not provided.

        Example:
            >>> # Create allomorph with inherited morph type (default)
            >>> entry = project.LexEntry.Create("run")
            >>> allomorph = project.Allomorphs.Create(entry, "running")
            >>> print(project.Allomorphs.GetForm(allomorph))
            running

            >>> # Create with explicit morph type
            >>> morphType = project.lexDB.MorphTypesOA.PossibilitiesOS[0]
            >>> allomorph = project.Allomorphs.Create(entry, "ran", morphType)

            >>> # Create with specific writing system
            >>> allomorph = project.Allomorphs.Create(entry, "rʌn",
            ...                                        wsHandle=project.WSHandle('en-fonipa'))

        Notes:
            - The allomorph is added to the entry's alternate forms list
            - If the entry has no lexeme form, this becomes the lexeme form
            - Otherwise, it's added as an alternate form
            - By default, inherits morph type from entry's LexemeFormOA (matches FLEx)
            - Correct allomorph class (MoStemAllomorph vs MoAffixAllomorph) is
              automatically chosen based on morph type

        See Also:
            Delete, GetAll, SetForm
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(entry_or_hvo, "entry_or_hvo")
        self._ValidateParam(form, "form")

        self._ValidateStringNotEmpty(form, "form")

        entry = self.__GetEntryObject(entry_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Accept morph type as a string name (with or without display markers).
        if isinstance(morphType, str):
            bare = morphType.strip('-=~<>')
            morph_types = self.project.lp.LexDbOA.MorphTypesOA
            from ..Shared.string_utils import normalize_match_key, best_analysis_text
            target = normalize_match_key(bare, casefold=True)
            def _find(possibilities):
                for mt in possibilities:
                    mt_name = best_analysis_text(mt.Name)
                    if mt_name and normalize_match_key(mt_name, casefold=True) == target:
                        return mt
                    if mt.SubPossibilitiesOS.Count > 0:
                        found = _find(mt.SubPossibilitiesOS)
                        if found:
                            return found
                return None
            resolved = _find(morph_types.PossibilitiesOS) if morph_types else None
            if resolved is None:
                raise FP_ParameterError(
                    f"Morph type '{morphType}' not found. "
                    "Use project.LexEntry.GetAvailableMorphTypes() to see valid names."
                )
            morphType = resolved

        # If no morphType provided, inherit from entry's LexemeFormOA (FLEx behavior)
        if morphType is None:
            if not entry.LexemeFormOA or not entry.LexemeFormOA.MorphTypeRA:
                raise FP_ParameterError(
                    "Cannot inherit morph type: entry has no LexemeFormOA with MorphTypeRA. "
                    "Either provide morphType parameter or ensure entry has a lexeme form."
                )
            morphType = entry.LexemeFormOA.MorphTypeRA

        # Create the new allomorph using the appropriate factory based on morph type
        if self.__IsStemType(morphType):
            factory = self.project.project.ServiceLocator.GetService(IMoStemAllomorphFactory)
        else:
            factory = self.project.project.ServiceLocator.GetService(IMoAffixAllomorphFactory)

        with self._TransactionCM(f"Create allomorph '{form}'"):
            allomorph = factory.Create()

            # Add to entry (must be done before setting properties)
            # If no lexeme form, set as lexeme, else add as alternate
            if not entry.LexemeFormOA:
                entry.LexemeFormOA = allomorph
            else:
                entry.AlternateFormsOS.Add(allomorph)

            # Set form
            mkstr = TsStringUtils.MakeString(form, wsHandle)
            allomorph.Form.set_String(wsHandle, mkstr)

            # Set morph type
            allomorph.MorphTypeRA = morphType

            return allomorph

    @OperationsMethod
    def Delete(self, allomorph_or_hvo):
        """
        Delete an allomorph.

        Args:
            allomorph_or_hvo: The IMoForm object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If allomorph_or_hvo is None.
            FP_ParameterError: If the allomorph is in use or cannot be deleted.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorphs = list(allomorphOps.GetAll(entry))
            >>> if len(allomorphs) > 1:
            ...     allomorphOps.Delete(allomorphs[-1])

        Warning:
            - Deleting an allomorph that is in use in analyses may cause issues
            - If deleting the lexeme form and alternates exist, the first
              alternate becomes the new lexeme form
            - Deletion is permanent and cannot be undone
            - Consider checking usage in texts before deletion

        Notes:
            - Removes the allomorph from the entry's forms collection
            - All references to this allomorph in analyses are affected

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)

        # Get the owning entry. allomorph.Owner is typed as ICmObject and
        # does not expose LexemeFormOA / AlternateFormsOS; cast to the
        # concrete interface so the typed collections are reachable.
        owner = self._GetTypedOwner(allomorph)
        if owner is None:
            raise FP_ParameterError("Allomorph has no owning entry")

        # Check if this is the lexeme form or an alternate
        with self._TransactionCM("Delete allomorph"):
            if hasattr(owner, "LexemeFormOA") and owner.LexemeFormOA == allomorph:
                # Deleting the lexeme form
                # If there are alternates, promote the first one to lexeme
                if owner.AlternateFormsOS.Count > 0:
                    new_lexeme = owner.AlternateFormsOS[0]
                    owner.AlternateFormsOS.RemoveAt(0)
                    owner.LexemeFormOA = new_lexeme
                else:
                    # No alternates, just clear the lexeme form
                    owner.LexemeFormOA = None
            elif hasattr(owner, "AlternateFormsOS"):
                # Deleting an alternate form
                owner.AlternateFormsOS.Remove(allomorph)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate an allomorph, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IMoForm object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source allomorph.
                                If False, insert at end of parent's alternate forms list.
            deep (bool): Reserved for future use (allomorphs have no owned objects).

        Returns:
            IMoForm: The newly created duplicate allomorph with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorphs = list(allomorphOps.GetAll(entry))
            >>> if len(allomorphs) > 1:  # Don't duplicate lexeme form
            ...     # Duplicate an alternate form
            ...     dup = allomorphOps.Duplicate(allomorphs[1])
            ...     print(f"Original: {allomorphOps.GetGuid(allomorphs[1])}")
            ...     print(f"Duplicate: {allomorphOps.GetGuid(dup)}")
            ...     print(f"Form: {allomorphOps.GetForm(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321
            Form: walk

        Notes:
            - Factory.Create() automatically generates a new GUID
            - Factory type determined by source ClassName (MoStemAllomorph, MoAffixAllomorph, etc.)
            - insert_after=True preserves the original allomorph's position/priority
            - Simple properties copied: Form (MultiString)
            - Reference properties copied: MorphTypeRA, PhoneEnvRC
            - Allomorphs have no owned objects, so deep parameter has no effect
            - Only duplicates alternate forms, not lexeme forms

        See Also:
            Create, Delete, GetGuid
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source allomorph and parent. source.Owner is typed as
        # ICmObject; cast to the concrete owning entry so AlternateFormsOS
        # and LexemeFormOA are reachable and the duplicate actually gets
        # attached (raw .Owner.AlternateFormsOS would orphan the dup).
        source = self.__GetAllomorphObject(item_or_hvo)
        parent = self._GetTypedOwner(source)
        if parent is None:
            raise FP_ParameterError("Allomorph has no owning entry")

        # Determine the factory type based on the source's ClassName
        class_name = source.ClassName
        factory = None

        if class_name == "MoStemAllomorph":
            from SIL.LCModel import IMoStemAllomorphFactory

            factory = self.project.project.ServiceLocator.GetService(IMoStemAllomorphFactory)
        elif class_name == "MoAffixAllomorph":
            from SIL.LCModel import IMoAffixAllomorphFactory

            factory = self.project.project.ServiceLocator.GetService(IMoAffixAllomorphFactory)
        else:
            # Unrecognized allomorph type - raise error instead of defaulting
            raise FP_ParameterError(
                f"Unrecognized allomorph type: {class_name}. " f"Expected 'MoStemAllomorph' or 'MoAffixAllomorph'."
            )

        # Create new allomorph using factory (auto-generates new GUID)
        with self._TransactionCM("Duplicate allomorph"):
            duplicate = factory.Create()

            # Determine insertion position
            # Note: Allomorphs can be lexeme forms or alternate forms
            if hasattr(parent, "LexemeFormOA") and parent.LexemeFormOA == source:
                # Source is lexeme form - add duplicate as alternate form
                if insert_after:
                    parent.AlternateFormsOS.Insert(0, duplicate)
                else:
                    parent.AlternateFormsOS.Add(duplicate)
            elif hasattr(parent, "AlternateFormsOS"):
                # Source is alternate form
                if insert_after:
                    source_index = parent.AlternateFormsOS.IndexOf(source)
                    parent.AlternateFormsOS.Insert(source_index + 1, duplicate)
                else:
                    parent.AlternateFormsOS.Add(duplicate)

            # Copy simple MultiString properties (AFTER adding to parent)
            duplicate.Form.CopyAlternatives(source.Form)

            # Copy Reference Atomic (RA) properties
            duplicate.MorphTypeRA = source.MorphTypeRA

            # Copy Reference Collection (RC) properties
            for env in source.PhoneEnvRC:
                duplicate.PhoneEnvRC.Add(env)

            return duplicate

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of an allomorph for comparison.

        Args:
            item: The IMoForm object (allomorph).

        Returns:
            dict: Dictionary mapping property names to their values:
                - MultiString properties as dicts {ws: text}
                - Atomic properties as simple values
                - Reference Atomic (RA) properties as GUID strings
                - Does NOT include Owning Sequence (OS) properties

        Example:
            >>> allo = list(project.Allomorphs.GetAll(entry))[0]
            >>> props = project.Allomorphs.GetSyncableProperties(allo)
            >>> print(props['Form'])  # MultiString
            {'en': 'run', 'fr': 'courir'}
            >>> print(props['IsAbstract'])  # Boolean
            True
        """
        props = {}

        # MultiString properties
        # Form - the allomorph form in various writing systems
        form_dict = {}
        if hasattr(item, "Form"):
            for ws_def in self.project.WritingSystems.GetAll():
                text = normalize_text(ITsString(item.Form.get_String(ws_def.Handle)).Text)
                if text:
                    form_dict[ws_def.Id] = text
        props["Form"] = form_dict

        # Atomic properties
        # IsAbstract - whether this is an abstract form
        if hasattr(item, "IsAbstract"):
            props["IsAbstract"] = item.IsAbstract

        # Reference Atomic (RA) properties
        # MorphTypeRA - morpheme type (prefix, suffix, stem, etc.)
        if hasattr(item, "MorphTypeRA") and item.MorphTypeRA:
            props["MorphTypeRA"] = str(item.MorphTypeRA.Guid)
        else:
            props["MorphTypeRA"] = None

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two allomorphs and return their differences.

        Args:
            item1: The first IMoForm object.
            item2: The second IMoForm object.
            ops1: Optional AllomorphOperations instance for item1 (for cross-project comparison).
                 If None, uses self.
            ops2: Optional AllomorphOperations instance for item2 (for cross-project comparison).
                 If None, uses self.

        Returns:
            tuple: (is_different, differences_dict) where:
                - is_different: True if items differ, False otherwise
                - differences_dict: Maps property names to (value1, value2) tuples for differing properties

        Example:
            >>> allo1 = list(project1.Allomorphs.GetAll(entry1))[0]
            >>> allo2 = list(project2.Allomorphs.GetAll(entry2))[0]
            >>> is_diff, diffs = project1.Allomorphs.CompareTo(allo1, allo2,
            ...                                                  project1.Allomorphs,
            ...                                                  project2.Allomorphs)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} -> {val2}")
        """
        # Use provided ops or default to self
        ops1 = ops1 or self
        ops2 = ops2 or self

        # Get syncable properties from both items
        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}

        # Compare all properties
        all_keys = set(props1.keys()) | set(props2.keys())
        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            # Handle MultiString comparison (dict comparison)
            if isinstance(val1, dict) and isinstance(val2, dict):
                if val1 != val2:
                    differences[key] = (val1, val2)
            # Handle None values
            elif val1 != val2:
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return is_different, differences

    @OperationsMethod
    def GetForm(self, allomorph_or_hvo, wsHandle=None):
        """
        Get the form (text) of an allomorph.

        Args:
            allomorph_or_hvo: The IMoForm object or HVO.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The allomorph form, or empty string if not set.

        Raises:
            FP_NullParameterError: If allomorph_or_hvo is None.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorphs = list(allomorphOps.GetAll(entry))
            >>> if allomorphs:
            ...     form = allomorphOps.GetForm(allomorphs[0])
            ...     print(form)
            walk

            >>> # Get form in specific writing system
            >>> form_ipa = allomorphOps.GetForm(allomorphs[0],
            ...                                  project.WSHandle('en-fonipa'))
            >>> print(form_ipa)
            wɔk

        Notes:
            - Returns empty string if form not set in specified writing system
            - Use different writing systems for pronunciation variants

        See Also:
            SetForm, GetAll
        """
        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        form = ITsString(allomorph.Form.get_String(wsHandle)).Text
        return self._NormalizeMultiString(form)

    @OperationsMethod
    def SetForm(self, allomorph_or_hvo, form, wsHandle=None):
        """
        Set the form (text) of an allomorph.

        Args:
            allomorph_or_hvo: The IMoForm object or HVO.
            form (str): The new allomorph form.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If allomorph_or_hvo or form is None.
            FP_ParameterError: If form is empty.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorphs = list(allomorphOps.GetAll(entry))
            >>> if allomorphs:
            ...     allomorphOps.SetForm(allomorphs[0], "walked")
            ...     print(allomorphOps.GetForm(allomorphs[0]))
            walked

            >>> # Set IPA pronunciation
            >>> allomorphOps.SetForm(allomorphs[0], "wɔkt",
            ...                      project.WSHandle('en-fonipa'))

        Notes:
            - Changing the form affects all analyses using this allomorph
            - Parser may need to be rerun after form changes
            - Use different writing systems for different representations

        See Also:
            GetForm, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")
        self._ValidateParam(form, "form")

        self._ValidateStringNotEmpty(form, "form")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(form, wsHandle)
        allomorph.Form.set_String(wsHandle, mkstr)

    @OperationsMethod
    def SetFormAudio(self, allomorph_or_hvo, file_path, wsHandle=None):
        """
        Set an audio recording for an allomorph's Form field.

        This is a convenience method for working with audio writing systems.
        The audio file is embedded as a file path reference in the Form field
        for an audio writing system (e.g., en-Zxxx-x-audio).

        Args:
            allomorph_or_hvo: The IMoForm object or HVO.
            file_path: Path to audio file. This should be either:
                      - A path within LinkedFiles (e.g., "LinkedFiles/AudioVisual/audio.wav")
                      - An external path (will be copied to LinkedFiles automatically)
            wsHandle: Optional audio writing system handle. If None, uses the first
                     audio writing system found in the project.

        Returns:
            str: The internal path where the audio file was stored (relative to project).

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If allomorph_or_hvo or file_path is None.
            FP_ParameterError: If no audio writing system is available, or if the
                              wsHandle provided is not an audio writing system.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorph = list(allomorphOps.GetAll(entry))[0]
            >>>
            >>> # Set audio from external file (will be copied to LinkedFiles)
            >>> audio_path = allomorphOps.SetFormAudio(
            ...     allomorph,
            ...     "/path/to/recordings/pronunciation.wav"
            ... )
            >>> print(f"Audio stored at: {audio_path}")
            LinkedFiles/AudioVisual/pronunciation.wav

            >>> # Set audio with specific audio writing system
            >>> audio_ws = project.WSHandle('en-Zxxx-x-audio')
            >>> allomorphOps.SetFormAudio(allomorph, "/path/to/audio.wav", audio_ws)

        Notes:
            - Audio writing systems use the Zxxx script code (ISO 15924 for "no written form")
            - Tag format: {lang}-Zxxx-x-audio (e.g., "en-Zxxx-x-audio")
            - The audio WS must already exist in the project (create it in FLEx UI first)
            - If file_path is external, it will be copied to LinkedFiles/AudioVisual
            - The file path is embedded as an ORC (Object Replacement Character) reference
            - FLEx will display this as a playable audio control in the UI
            - This is different from attaching media files via MediaFilesOS

        See Also:
            GetFormAudio, SetForm, project.SetAudioPath, project.IsAudioWritingSystem
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")
        self._ValidateParam(file_path, "file_path")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)

        # Find or validate audio writing system
        if wsHandle is None:
            # Auto-detect first audio WS
            for ws_def in self.project.WritingSystems.GetAll():
                if self.project.IsAudioWritingSystem(ws_def.Handle):
                    wsHandle = ws_def.Handle
                    break

            if wsHandle is None:
                raise FP_ParameterError(
                    "No audio writing system found in project. " "Create one in FLEx first (e.g., en-Zxxx-x-audio)"
                )
        else:
            # Validate that provided WS is audio
            if not self.project.IsAudioWritingSystem(wsHandle):
                raise FP_ParameterError(
                    "The provided writing system is not an audio writing system. "
                    "Use project.IsAudioWritingSystem() to check."
                )

        # Determine if we need to copy the file to LinkedFiles
        import os

        internal_path = file_path

        # If file_path is an external file (not already in LinkedFiles)
        if os.path.isabs(file_path) or not file_path.startswith("LinkedFiles"):
            # Copy file to project using Media operations
            try:
                from ..Shared.MediaOperations import MediaOperations

                media_ops = MediaOperations(self.project)

                # Copy file to LinkedFiles/AudioVisual
                media_file = media_ops.CopyToProject(file_path, internal_subdir="AudioVisual")
                internal_path = media_ops.GetInternalPath(media_file)
            except Exception as e:
                # If Media operations fail, just use the path as-is
                logger.warning(f"Could not copy audio file to LinkedFiles: {e}")
                internal_path = file_path

        # Set audio path in Form field
        self.project.SetAudioPath(allomorph.Form, wsHandle, internal_path)

        return internal_path

    @OperationsMethod
    def GetFormAudio(self, allomorph_or_hvo, wsHandle=None):
        """
        Get the audio file path from an allomorph's Form field.

        This is a convenience method for extracting audio file references from
        audio writing system fields.

        Args:
            allomorph_or_hvo: The IMoForm object or HVO.
            wsHandle: Optional audio writing system handle. If None, uses the first
                     audio writing system found in the project.

        Returns:
            str: Path to audio file (relative to project root), or None if no audio is set.

        Raises:
            FP_NullParameterError: If allomorph_or_hvo is None.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorph = list(allomorphOps.GetAll(entry))[0]
            >>>
            >>> # Get audio file path
            >>> audio_path = allomorphOps.GetFormAudio(allomorph)
            >>> if audio_path:
            ...     print(f"Audio file: {audio_path}")
            ...     # Construct full path if needed
            ...     import os
            ...     full_path = os.path.join(
            ...         project.GetLinkedFilesDir(),
            ...         audio_path.replace("LinkedFiles/", "")
            ...     )
            ...     print(f"Full path: {full_path}")
            ... else:
            ...     print("No audio recording")
            Audio file: LinkedFiles/AudioVisual/pronunciation.wav

            >>> # Get audio with specific writing system
            >>> audio_ws = project.WSHandle('en-Zxxx-x-audio')
            >>> audio_path = allomorphOps.GetFormAudio(allomorph, audio_ws)

        Notes:
            - Returns None if no audio writing system is found in the project
            - Returns None if the specified writing system has no audio data
            - The returned path is relative to the project root
            - Use project.GetLinkedFilesDir() to construct absolute paths
            - Audio must have been set using SetFormAudio() or project.SetAudioPath()
            - This only retrieves the file path; it doesn't play the audio

        See Also:
            SetFormAudio, GetForm, project.GetAudioPath, project.IsAudioWritingSystem
        """
        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)

        # Find audio writing system if not provided
        if wsHandle is None:
            for ws_def in self.project.WritingSystems.GetAll():
                if self.project.IsAudioWritingSystem(ws_def.Handle):
                    wsHandle = ws_def.Handle
                    break

            if wsHandle is None:
                # No audio WS in project
                return None

        # Get audio path from Form field
        try:
            return self.project.GetAudioPath(allomorph.Form, wsHandle)
        except FP_ParameterError:
            # Not an audio writing system
            return None

    @OperationsMethod
    def GetMorphType(self, allomorph_or_hvo):
        """
        Get the morpheme type of an allomorph.

        Args:
            allomorph_or_hvo: The IMoForm object or HVO.

        Returns:
            IMoMorphType: The morpheme type (stem, prefix, suffix, etc.).

        Raises:
            FP_NullParameterError: If allomorph_or_hvo is None.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorphs = list(allomorphOps.GetAll(entry))
            >>> if allomorphs:
            ...     morphType = allomorphOps.GetMorphType(allomorphs[0])
            ...     # Get type name
            ...     wsHandle = project.project.DefaultAnalWs
            ...     type_name = ITsString(morphType.Name.get_String(wsHandle)).Text
            ...     print(type_name)
            stem

        Notes:
            - Morpheme types include: stem, root, bound root, prefix, suffix,
              infix, circumfix, clitic, proclitic, enclitic, simulfix, etc.
            - Type determines parsing behavior and template slots
            - Returns the IMoMorphType object which can be queried for details

        See Also:
            SetMorphType, Create
        """
        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)
        return allomorph.MorphTypeRA

    @OperationsMethod
    def SetMorphType(self, allomorph_or_hvo, morphType):
        """
        Set the morpheme type of an allomorph.

        Args:
            allomorph_or_hvo: The IMoForm object or HVO.
            morphType: The new morpheme type (IMoMorphType object).

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If allomorph_or_hvo or morphType is None.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorphs = list(allomorphOps.GetAll(entry))
            >>> if allomorphs:
            ...     # Get a different morph type
            ...     morphTypes = project.lp.MorphTypesOA.PossibilitiesOS
            ...     prefix_type = [mt for mt in morphTypes
            ...                    if "prefix" in str(mt).lower()][0]
            ...     allomorphOps.SetMorphType(allomorphs[0], prefix_type)

        Notes:
            - Changing type affects parsing and morphological analysis
            - Incompatible changes may require template updates
            - Parser should be rerun after type changes

        See Also:
            GetMorphType, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")
        self._ValidateParam(morphType, "morphType")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)
        allomorph.MorphTypeRA = morphType

    @OperationsMethod
    def GetPhoneEnv(self, allomorph_or_hvo):
        """
        Get the phonological environments for an allomorph.

        Args:
            allomorph_or_hvo: The IMoForm object or HVO.

        Returns:
            list: List of IPhEnvironment objects (empty list if none).

        Raises:
            FP_NullParameterError: If allomorph_or_hvo is None.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorphs = list(allomorphOps.GetAll(entry))
            >>> if allomorphs:
            ...     envs = allomorphOps.GetPhoneEnv(allomorphs[0])
            ...     for env in envs:
            ...         wsHandle = project.project.DefaultAnalWs
            ...         name = ITsString(env.Name.get_String(wsHandle)).Text
            ...         print(f"Environment: {name}")
            Environment: After voiceless consonant

        Notes:
            - Phonological environments define distribution of allomorphs
            - Empty list means allomorph appears in all contexts
            - Multiple environments are OR'd (any match allows allomorph)
            - Used by the parser to select appropriate allomorph

        See Also:
            AddPhoneEnv, RemovePhoneEnv
        """
        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)
        return list(allomorph.PhoneEnvRC)

    @OperationsMethod
    def AddPhoneEnv(self, allomorph_or_hvo, env_or_hvo):
        """
        Add a phonological environment to an allomorph.

        Args:
            allomorph_or_hvo: The IMoForm object or HVO.
            env_or_hvo: The IPhEnvironment object or HVO to add.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If allomorph_or_hvo or env_or_hvo is None.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorphs = list(allomorphOps.GetAll(entry))
            >>> if allomorphs and project.lp.PhonologicalDataOA:
            ...     envs = project.lp.PhonologicalDataOA.EnvironmentsOS
            ...     if envs.Count > 0:
            ...         allomorphOps.AddPhoneEnv(allomorphs[0], envs[0])

            >>> # Define that "-es" appears after sibilants
            >>> # (assuming you have created the environment)
            >>> sibilant_env = project.lp.PhonologicalDataOA.EnvironmentsOS[0]
            >>> allomorphOps.AddPhoneEnv(allomorphs[0], sibilant_env)

        Notes:
            - Multiple environments can be added (OR logic)
            - If environment already exists in the list, it's still added
              (duplicates are allowed but not recommended)
            - Environments guide parser in selecting appropriate allomorph

        See Also:
            GetPhoneEnv, RemovePhoneEnv
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")
        self._ValidateParam(env_or_hvo, "env_or_hvo")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)
        env = self.__GetEnvironmentObject(env_or_hvo)

        allomorph.PhoneEnvRC.Add(env)

    @OperationsMethod
    def RemovePhoneEnv(self, allomorph_or_hvo, env_or_hvo):
        """
        Remove a phonological environment from an allomorph.

        Args:
            allomorph_or_hvo: The IMoForm object or HVO.
            env_or_hvo: The IPhEnvironment object or HVO to remove.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If allomorph_or_hvo or env_or_hvo is None.

        Example:
            >>> allomorphOps = AllomorphOperations(project)
            >>> entry = project.LexiconAllEntries()[0]
            >>> allomorphs = list(allomorphOps.GetAll(entry))
            >>> if allomorphs:
            ...     envs = allomorphOps.GetPhoneEnv(allomorphs[0])
            ...     if envs:
            ...         # Remove the first environment
            ...         allomorphOps.RemovePhoneEnv(allomorphs[0], envs[0])

        Notes:
            - If environment not in list, this is a no-op (no error)
            - Removing all environments means allomorph appears in all contexts
            - Parser behavior changes when environments are modified

        See Also:
            GetPhoneEnv, AddPhoneEnv
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(allomorph_or_hvo, "allomorph_or_hvo")
        self._ValidateParam(env_or_hvo, "env_or_hvo")

        allomorph = self.__GetAllomorphObject(allomorph_or_hvo)
        env = self.__GetEnvironmentObject(env_or_hvo)

        # Only remove if it's actually in the collection
        if env in allomorph.PhoneEnvRC:
            allomorph.PhoneEnvRC.Remove(env)

    # --- Private Helper Methods ---

    def __GetEntryObject(self, entry_or_hvo):
        """
        Resolve HVO or object to ILexEntry.

        Args:
            entry_or_hvo: Either an ILexEntry object or an HVO (int).

        Returns:
            ILexEntry: The resolved entry object.
        """
        if isinstance(entry_or_hvo, int):
            return self.project.Object(entry_or_hvo)
        return entry_or_hvo

    def __GetAllomorphObject(self, allomorph_or_hvo):
        """
        Resolve HVO or object to IMoForm.

        Args:
            allomorph_or_hvo: Either an IMoForm object or an HVO (int).

        Returns:
            IMoForm: The resolved allomorph object.
        """
        if isinstance(allomorph_or_hvo, int):
            return self.project.Object(allomorph_or_hvo)
        return allomorph_or_hvo

    def __GetEnvironmentObject(self, env_or_hvo):
        """
        Resolve HVO or object to IPhEnvironment.

        Args:
            env_or_hvo: Either an IPhEnvironment object or an HVO (int).

        Returns:
            IPhEnvironment: The resolved environment object.
        """
        if isinstance(env_or_hvo, int):
            return self.project.Object(env_or_hvo)
        return env_or_hvo

    def __IsStemType(self, morph_type):
        """
        Determine if a morph type should use MoStemAllomorph or MoAffixAllomorph.

        Args:
            morph_type: IMoMorphType object

        Returns:
            bool: True if stem type (uses MoStemAllomorph), False if affix type

        Notes:
            Based on FLEx logic - matches LexEntryOperations.__IsStemType
        """
        if morph_type is None:
            return True  # Default to stem

        # Check GUID against known stem types
        stem_guids = {
            MoMorphTypeTags.kguidMorphStem,
            MoMorphTypeTags.kguidMorphRoot,
            MoMorphTypeTags.kguidMorphBoundRoot,
            MoMorphTypeTags.kguidMorphBoundStem,
            MoMorphTypeTags.kguidMorphClitic,
            MoMorphTypeTags.kguidMorphEnclitic,
            MoMorphTypeTags.kguidMorphProclitic,
            MoMorphTypeTags.kguidMorphParticle,
            MoMorphTypeTags.kguidMorphPhrase,
            MoMorphTypeTags.kguidMorphDiscontiguousPhrase,
        }

        return morph_type.Guid in stem_guids

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to vernacular WS for allomorph forms.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)
