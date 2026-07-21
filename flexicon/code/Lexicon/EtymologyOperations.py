#
#   EtymologyOperations.py
#
#   Class: EtymologyOperations
#          Etymology tracking operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import FLEx LCM types
from SIL.LCModel import (
    ILexEtymology,
    ILexEtymologyFactory,
    ILexEntry,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import string utilities
from ..Shared.string_utils import normalize_text


class EtymologyOperations(BaseOperations):
    """
    This class provides operations for managing etymological information in a
    FieldWorks project.

    Etymology tracking records the historical origin and development of lexical
    entries. Each etymology can specify the source language, etymological form,
    gloss, linguistic commentary, and bibliographic references.

    This class supports historical linguistics workflows including etymology
    documentation, loan word tracking, and diachronic analysis.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Access via FLExProject.Etymology property (if configured)
        # Or create directly:
        from flexlibs2.code.EtymologyOperations import EtymologyOperations
        etymOps = EtymologyOperations(project)

        # Get an entry
        entry = project.LexEntry.Find("computer")

        # Create an etymology
        etym = etymOps.Create(
            entry,
            source="English",
            form="compute",
            gloss="to calculate",
            ws="en"
        )

        # Set additional information
        etymOps.SetComment(etym, "Borrowed in the 1980s", "en")
        etymOps.SetBibliography(etym, "Smith 2020:145")

        # Get all etymologies
        for etym in etymOps.GetAll(entry):
            source = etymOps.GetSource(etym)
            form = etymOps.GetForm(etym)
            print(f"From {source}: {form}")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize EtymologyOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for etymologies.
        For Etymology, we reorder entry.EtymologyOS
        """
        return parent.EtymologyOS

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, entry_or_hvo=None):
        """
        Get all etymologies for a lexical entry, or all etymologies in the entire project.

        Args:
            entry_or_hvo: The ILexEntry object or HVO. If None, iterates all etymologies
                         in the entire project.

        Returns:
            EnumerableWrapper[ILexEtymology]: Each etymology object for the entry (or project).

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> # Get etymologies for specific entry
            >>> entry = project.LexEntry.Find("telephone")
            >>> for etym in etymOps.GetAll(entry):
            ...     source = etymOps.GetSource(etym)
            ...     form = etymOps.GetForm(etym)
            ...     gloss = etymOps.GetGloss(etym)
            ...     print(f"Etymology: {source} '{form}' ({gloss})")
            Etymology: Greek 'tele' (far)
            Etymology: Greek 'phone' (sound)

            >>> # Get ALL etymologies in entire project
            >>> for etym in etymOps.GetAll():
            ...     source = etymOps.GetSource(etym)
            ...     print(f"Etymology source: {source}")

        Notes:
            - When entry_or_hvo is provided:
              - Returns etymologies in database order
              - Returns empty generator if entry has no etymologies
              - Etymologies can be reordered using Reorder()
              - Each etymology represents one source or stage in word history
            - When entry_or_hvo is None:
              - Iterates ALL entries in the project
              - For each entry, yields all etymologies
              - Useful for project-wide etymology operations

        See Also:
            Create, Delete, Reorder
        """
        if entry_or_hvo is None:
            # Iterate ALL etymologies in entire project
            for entry in self.project.lexDB.Entries:
                for etymology in entry.EtymologyOS:
                    yield etymology
        else:
            # Iterate etymologies for specific entry
            entry = self.__GetEntryObject(entry_or_hvo)

            for etymology in entry.EtymologyOS:
                yield etymology

    @OperationsMethod
    def Create(self, entry_or_hvo, source=None, form=None, gloss=None, ws=None):
        """
        Create a new etymology for a lexical entry.

        Args:
            entry_or_hvo: The ILexEntry object or HVO.
            source (str, optional): The source language name.
            form (str, optional): The etymological form in source language.
            gloss (str, optional): The meaning in source language.
            ws: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ILexEtymology: The newly created etymology object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If entry_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etym = etymOps.Create(
            ...     entry,
            ...     source="Greek",
            ...     form="tele",
            ...     gloss="far"
            ... )
            >>> print(etymOps.GetForm(etym))
            tele

            >>> # Create minimal etymology (add details later)
            >>> etym2 = etymOps.Create(entry)
            >>> etymOps.SetSource(etym2, "Greek")
            >>> etymOps.SetForm(etym2, "phone")

        Notes:
            - All text fields are optional at creation
            - Etymology is added at the end of the entry's etymology list
            - Use Set methods to add/update information after creation
            - Multiple etymologies can track compound or complex origins
            - Default writing system is analysis WS

        See Also:
            Delete, SetSource, SetForm, SetGloss
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(entry_or_hvo, "entry_or_hvo")

        entry = self.__GetEntryObject(entry_or_hvo)
        wsHandle = self.__WSHandleAnalysis(ws)

        with self._TransactionCM("Create etymology"):
            # Create the new etymology using the factory
            factory = self.project.project.ServiceLocator.GetService(ILexEtymologyFactory)
            new_etymology = factory.Create()

            # Add to entry's etymology collection (must be done before setting properties)
            entry.EtymologyOS.Add(new_etymology)

            # Set optional fields if provided
            if source:
                mkstr = TsStringUtils.MakeString(source, wsHandle)
                new_etymology.Source.set_String(wsHandle, mkstr)

            if form:
                mkstr = TsStringUtils.MakeString(form, wsHandle)
                new_etymology.Form.set_String(wsHandle, mkstr)

            if gloss:
                mkstr = TsStringUtils.MakeString(gloss, wsHandle)
                new_etymology.Gloss.set_String(wsHandle, mkstr)

            return new_etymology

    @OperationsMethod
    def Delete(self, etymology_or_hvo):
        """
        Delete an etymology from its owning entry.

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If etymology_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if len(etymologies) > 0:
            ...     # Delete the last etymology
            ...     etymOps.Delete(etymologies[-1])

        Warning:
            - Deletion is permanent and cannot be undone
            - All etymology data (source, form, gloss, etc.) is lost
            - Consider archiving data before deletion

        Notes:
            - Removes the etymology from the owning entry's collection
            - Other etymologies in the list are automatically renumbered
            - No error if entry has no other etymologies

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)

        # Get the owning entry. etymology.Owner is typed as ICmObject
        # and does not expose EtymologyOS; cast to ILexEntry so the
        # collection is reachable (the previous hasattr check silently
        # no-opped because the typed collection lives on the concrete
        # owner, not on the base interface).
        owner = self._GetTypedOwner(etymology)
        if owner is None:
            raise FP_ParameterError("Etymology has no owning entry")
        owner.EtymologyOS.Remove(etymology)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate an etymology, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The ILexEtymology object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source etymology.
                                If False, insert at end of entry's etymology list.
            deep (bool): If True, also duplicate owned objects (if any exist).
                        If False (default), only copy simple properties and references.
                        Note: Etymology has no owned objects, so deep has no effect.

        Returns:
            ILexEtymology: The newly created duplicate etymology with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if etymologies:
            ...     # Duplicate etymology
            ...     dup = etymOps.Duplicate(etymologies[0])
            ...     print(f"Original: {etymOps.GetGuid(etymologies[0])}")
            ...     print(f"Duplicate: {etymOps.GetGuid(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321
            ...
            ...     # Verify content was copied
            ...     print(f"Source: {etymOps.GetSource(dup)}")
            ...     print(f"Form: {etymOps.GetForm(dup)}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original etymology's position
            - Simple properties copied: Source, Form, Gloss, Comment, Bibliography
            - Reference properties copied: LanguageNotesRA
            - Etymology has no owned objects, so deep parameter has no effect

        See Also:
            Create, Delete, GetGuid
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source etymology and parent. source.Owner is typed as
        # ICmObject; cast to ILexEntry so EtymologyOS is reachable.
        # Without this cast the previous `hasattr(parent, "EtymologyOS")`
        # silently returned False and the duplicate was orphaned.
        source = self.__GetEtymologyObject(item_or_hvo)
        parent = self._GetTypedOwner(source)
        if parent is None:
            raise FP_ParameterError("Etymology has no owning entry")

        with self._TransactionCM("Duplicate etymology"):
            # Create new etymology using factory (auto-generates new GUID)
            factory = self.project.project.ServiceLocator.GetService(ILexEtymologyFactory)
            duplicate = factory.Create()

            # Determine insertion position
            if insert_after:
                # Insert after source etymology
                source_index = parent.EtymologyOS.IndexOf(source)
                parent.EtymologyOS.Insert(source_index + 1, duplicate)
            else:
                # Insert at end
                parent.EtymologyOS.Add(duplicate)

            # Copy simple MultiString properties (AFTER adding to parent)
            duplicate.Source.CopyAlternatives(source.Source)
            duplicate.Form.CopyAlternatives(source.Form)
            duplicate.Gloss.CopyAlternatives(source.Gloss)
            duplicate.Comment.CopyAlternatives(source.Comment)
            duplicate.Bibliography.CopyAlternatives(source.Bibliography)

            # Copy Reference Atomic (RA) properties
            if hasattr(source, "LanguageNotesRA") and source.LanguageNotesRA:
                duplicate.LanguageNotesRA = source.LanguageNotesRA

            # Note: Etymology has no owned objects (OS collections), so deep has no effect

            return duplicate

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of an etymology for comparison.

        Args:
            item: The ILexEtymology object.

        Returns:
            dict: Dictionary mapping property names to their values.
        """
        props = {}

        # MultiString properties
        # Form - the etymological form
        form_dict = {}
        if hasattr(item, "Form"):
            for ws_def in self.project.WritingSystems.GetAll():
                from SIL.LCModel.Core.KernelInterfaces import ITsString

                text = normalize_text(ITsString(item.Form.get_String(ws_def.Handle)).Text)
                if text:
                    ws_tag = ws_def.Id
                    form_dict[ws_tag] = text
        props["Form"] = form_dict

        # Gloss - meaning of the etymological form
        gloss_dict = {}
        if hasattr(item, "Gloss"):
            for ws_def in self.project.WritingSystems.GetAll():
                from SIL.LCModel.Core.KernelInterfaces import ITsString

                text = normalize_text(ITsString(item.Gloss.get_String(ws_def.Handle)).Text)
                if text:
                    ws_tag = ws_def.Id
                    gloss_dict[ws_tag] = text
        props["Gloss"] = gloss_dict

        # Source - source language or reference
        source_dict = {}
        if hasattr(item, "Source"):
            for ws_def in self.project.WritingSystems.GetAll():
                from SIL.LCModel.Core.KernelInterfaces import ITsString

                text = normalize_text(ITsString(item.Source.get_String(ws_def.Handle)).Text)
                if text:
                    ws_tag = ws_def.Id
                    source_dict[ws_tag] = text
        props["Source"] = source_dict

        # Comment - additional notes
        comment_dict = {}
        if hasattr(item, "Comment"):
            for ws_def in self.project.WritingSystems.GetAll():
                from SIL.LCModel.Core.KernelInterfaces import ITsString

                text = normalize_text(ITsString(item.Comment.get_String(ws_def.Handle)).Text)
                if text:
                    ws_tag = ws_def.Id
                    comment_dict[ws_tag] = text
        props["Comment"] = comment_dict

        # Bibliography - bibliographic reference
        bibliography_dict = {}
        if hasattr(item, "Bibliography"):
            for ws_def in self.project.WritingSystems.GetAll():
                from SIL.LCModel.Core.KernelInterfaces import ITsString

                text = normalize_text(ITsString(item.Bibliography.get_String(ws_def.Handle)).Text)
                if text:
                    ws_tag = ws_def.Id
                    bibliography_dict[ws_tag] = text
        props["Bibliography"] = bibliography_dict

        # Reference Atomic (RA) properties
        # LanguageRA - source language (ICmPossibility from LangProject.AnalysisWSs
        # or the languages list). Serialize as GUID string.
        if hasattr(item, "LanguageRA") and item.LanguageRA:
            props["LanguageRA"] = str(item.LanguageRA.Guid)
        else:
            props["LanguageRA"] = None

        # LanguageNotesRA - language notes reference (ICmPossibility). (P2)
        # This is an atomic reference, same serialization pattern as LanguageRA.
        # [JUDGMENT CALL] The LCM field name is LanguageNotesRA on ILexEtymology;
        # this resolves against the same general possibility list as LanguageRA.
        # Verification requested: confirm LanguageNotesRA is the correct field name
        # on ILexEtymology and that its possibility list is LangProject.AnthroListOA
        # or similar (not AnalysisWSs). If the field does not exist at runtime,
        # the hasattr guard makes this a no-op.
        if hasattr(item, "LanguageNotesRA") and item.LanguageNotesRA:
            props["LanguageNotesRA"] = str(item.LanguageNotesRA.Guid)
        else:
            props["LanguageNotesRA"] = None

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """
        Apply a syncable-properties dict onto an ILexEtymology item.

        Extends the base implementation to handle atomic reference fields
        (LanguageRA, LanguageNotesRA) which are serialized as GUID strings.
        Resolution uses the generic project.Object(Guid) lookup which works
        for any LCM object whose GUID is known.

        Args:
            item: Target ILexEtymology (must already exist in target project).
            props: dict produced by GetSyncableProperties on a source etymology.
            ws_map: Optional source->target writing-system Id mapping.
            fill_gaps (bool): When True, only write fields whose current target
                value is empty/absent; passed through to BaseOperations.
                Atomic-ref fields (LanguageRA, LanguageNotesRA) are always
                applied regardless (domain has not ruled on them).
        """
        import logging as _logging
        _log = _logging.getLogger(__name__)

        self._EnsureWriteEnabled()

        _ra_fields = ("LanguageRA", "LanguageNotesRA")
        remaining_props = {}
        ra_props = {}
        for k, v in props.items():
            if k in _ra_fields:
                ra_props[k] = v
            else:
                remaining_props[k] = v

        with self._TransactionCM("Apply etymology properties"):
            # Apply plain / multistring fields via base class.
            super().ApplySyncableProperties(item, remaining_props, ws_map=ws_map, fill_gaps=fill_gaps)

            # Resolve atomic reference fields by GUID.
            for field_name, guid_str in ra_props.items():
                if not hasattr(item, field_name):
                    continue
                if not guid_str:
                    setattr(item, field_name, None)
                    continue
                try:
                    import System
                    obj = self.project.Object(System.Guid(guid_str))
                    setattr(item, field_name, obj)
                except Exception as exc:
                    _log.warning(
                        "[WARN] ApplySyncableProperties: %s GUID %s not found "
                        "in target project -- skipped (%s)",
                        field_name, guid_str, exc
                    )

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two etymologies and return their differences.

        Args:
            item1: The first ILexEtymology object.
            item2: The second ILexEtymology object.
            ops1: Optional EtymologyOperations instance for item1.
            ops2: Optional EtymologyOperations instance for item2.

        Returns:
            tuple: (is_different, differences_dict)
        """
        ops1 = ops1 or self
        ops2 = ops2 or self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}
        all_keys = set(props1.keys()) | set(props2.keys())
        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)
            if val1 != val2:
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return is_different, differences

    @OperationsMethod
    def Reorder(self, entry_or_hvo, etymology_list):
        """
        Reorder etymologies for a lexical entry.

        Args:
            entry_or_hvo: The ILexEntry object or HVO.
            etymology_list: List of ILexEtymology objects or HVOs in desired order.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If entry_or_hvo or etymology_list is None.
            FP_ParameterError: If etymology_list doesn't match entry's etymologies.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if len(etymologies) > 1:
            ...     # Reverse the order
            ...     etymOps.Reorder(entry, reversed(etymologies))
            ...     # Verify new order
            ...     for etym in etymOps.GetAll(entry):
            ...         print(etymOps.GetSource(etym))

        Notes:
            - All etymologies must be provided in the new order
            - All etymologies must belong to the specified entry
            - Useful for ordering by chronological sequence
            - Useful for ordering from ultimate to immediate source

        See Also:
            GetAll, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(entry_or_hvo, "entry_or_hvo")
        self._ValidateParam(etymology_list, "etymology_list")

        entry = self.__GetEntryObject(entry_or_hvo)

        # Convert to list if it's an iterator
        etymology_list = list(etymology_list)

        # Resolve all to objects
        etymologies = [self.__GetEtymologyObject(etym) for etym in etymology_list]

        # Verify all etymologies belong to this entry
        current_etymologies = set(entry.EtymologyOS)
        new_etymologies = set(etymologies)

        if current_etymologies != new_etymologies:
            raise FP_ParameterError("Etymology list must contain exactly the same etymologies as the entry")

        with self._TransactionCM("Reorder etymologies"):
            # Clear and re-add in new order
            entry.EtymologyOS.Clear()
            for etymology in etymologies:
                entry.EtymologyOS.Add(etymology)

    # --- Source Language Operations ---

    @OperationsMethod
    def GetSource(self, etymology_or_hvo, ws=None):
        """
        Get the source language name for an etymology.

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.
            ws: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The source language name, or empty string if not set.

        Raises:
            FP_NullParameterError: If etymology_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if etymologies:
            ...     source = etymOps.GetSource(etymologies[0])
            ...     print(f"Source language: {source}")
            Source language: Greek

            >>> # Get in specific writing system
            >>> source_fr = etymOps.GetSource(etymologies[0], "fr")

        Notes:
            - Returns empty string if source not set in specified writing system
            - Source can be a language name, language family, or proto-language
            - Examples: "Latin", "Proto-Indo-European", "French", "Unknown"
            - Can be set in multiple writing systems for multilingual display

        See Also:
            SetSource, GetForm, GetGloss
        """
        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        wsHandle = self.__WSHandleAnalysis(ws)

        source = ITsString(etymology.Source.get_String(wsHandle)).Text
        return self._NormalizeMultiString(source)

    @OperationsMethod
    def SetSource(self, etymology_or_hvo, text, ws=None):
        """
        Set the source language name for an etymology.

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.
            text (str): The source language name.
            ws: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If etymology_or_hvo or text is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if etymologies:
            ...     etymOps.SetSource(etymologies[0], "Ancient Greek")
            ...     print(etymOps.GetSource(etymologies[0]))
            Ancient Greek

            >>> # Set in multiple writing systems
            >>> etymOps.SetSource(etymologies[0], "Grec ancien", "fr")
            >>> etymOps.SetSource(etymologies[0], "Griego antiguo", "es")

        Notes:
            - Empty string is allowed (clears the source)
            - Can be set independently in multiple writing systems
            - Common formats: language name, ISO code, or proto-language
            - Be consistent within a project for analysis purposes

        See Also:
            GetSource, SetForm, SetGloss
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")
        self._ValidateParam(text, "text")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        wsHandle = self.__WSHandleAnalysis(ws)

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        etymology.Source.set_String(wsHandle, mkstr)

    # --- Form & Gloss Operations ---

    @OperationsMethod
    def GetForm(self, etymology_or_hvo, ws=None):
        """
        Get the etymological form (the form in the source language).

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.
            ws: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The etymological form, or empty string if not set.

        Raises:
            FP_NullParameterError: If etymology_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if etymologies:
            ...     form = etymOps.GetForm(etymologies[0])
            ...     source = etymOps.GetSource(etymologies[0])
            ...     print(f"{source}: {form}")
            Greek: τηλε

        Notes:
            - Returns empty string if form not set in specified writing system
            - Form should be in the orthography of the source language
            - May include phonetic transcription, reconstruction, or native script
            - For Proto-languages, use asterisk notation (e.g., "*tele")

        See Also:
            SetForm, GetSource, GetGloss
        """
        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        wsHandle = self.__WSHandleAnalysis(ws)

        form = ITsString(etymology.Form.get_String(wsHandle)).Text
        return self._NormalizeMultiString(form)

    @OperationsMethod
    def SetForm(self, etymology_or_hvo, text, ws=None):
        """
        Set the etymological form (the form in the source language).

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.
            text (str): The etymological form.
            ws: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If etymology_or_hvo or text is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etym = etymOps.Create(entry)
            >>> etymOps.SetForm(etym, "tele")
            >>> print(etymOps.GetForm(etym))
            tele

            >>> # Set reconstructed Proto-Indo-European form
            >>> etymOps.SetForm(etym, "*tele-")

        Notes:
            - Empty string is allowed (clears the form)
            - Can be set independently in multiple writing systems
            - Include diacritics, tone marks, or special characters as needed
            - For reconstructed forms, use asterisk (*) prefix by convention

        See Also:
            GetForm, SetSource, SetGloss
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")
        self._ValidateParam(text, "text")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        wsHandle = self.__WSHandleAnalysis(ws)

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        etymology.Form.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetGloss(self, etymology_or_hvo, ws=None):
        """
        Get the gloss (meaning in the source language).

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.
            ws: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The gloss text, or empty string if not set.

        Raises:
            FP_NullParameterError: If etymology_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if etymologies:
            ...     form = etymOps.GetForm(etymologies[0])
            ...     gloss = etymOps.GetGloss(etymologies[0])
            ...     print(f"'{form}' means '{gloss}'")
            'tele' means 'far, distant'

        Notes:
            - Returns empty string if gloss not set in specified writing system
            - Gloss describes the meaning in the source language
            - May differ from current meaning due to semantic shift
            - Use semicolons to separate multiple related meanings

        See Also:
            SetGloss, GetForm, GetSource
        """
        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        wsHandle = self.__WSHandleAnalysis(ws)

        gloss = ITsString(etymology.Gloss.get_String(wsHandle)).Text
        return self._NormalizeMultiString(gloss)

    @OperationsMethod
    def SetGloss(self, etymology_or_hvo, text, ws=None):
        """
        Set the gloss (meaning in the source language).

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.
            text (str): The gloss text.
            ws: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If etymology_or_hvo or text is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etym = etymOps.Create(entry)
            >>> etymOps.SetGloss(etym, "far, distant")
            >>> print(etymOps.GetGloss(etym))
            far, distant

        Notes:
            - Empty string is allowed (clears the gloss)
            - Can be set independently in multiple writing systems
            - Gloss explains the original meaning in the source language
            - Helps track semantic change from source to current language

        See Also:
            GetGloss, SetForm, SetSource
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")
        self._ValidateParam(text, "text")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        wsHandle = self.__WSHandleAnalysis(ws)

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        etymology.Gloss.set_String(wsHandle, mkstr)

    # --- Comment & Bibliography Operations ---

    @OperationsMethod
    def GetComment(self, etymology_or_hvo, ws=None):
        """
        Get the linguistic comment for an etymology.

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.
            ws: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The comment text, or empty string if not set.

        Raises:
            FP_NullParameterError: If etymology_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if etymologies:
            ...     comment = etymOps.GetComment(etymologies[0])
            ...     print(f"Note: {comment}")
            Note: Calque from Greek compound; borrowed in 19th century

        Notes:
            - Returns empty string if comment not set in specified writing system
            - Comment field allows free-form linguistic commentary
            - Use for notes on borrowing, semantic shift, sound changes, etc.
            - Can include dates, phonological rules, or comparative notes

        See Also:
            SetComment, GetBibliography
        """
        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        wsHandle = self.__WSHandleAnalysis(ws)

        comment = ITsString(etymology.Comment.get_String(wsHandle)).Text
        return self._NormalizeMultiString(comment)

    @OperationsMethod
    def SetComment(self, etymology_or_hvo, text, ws=None):
        """
        Set the linguistic comment for an etymology.

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.
            text (str): The comment text.
            ws: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If etymology_or_hvo or text is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etym = etymOps.Create(entry, source="Greek", form="tele")
            >>> etymOps.SetComment(
            ...     etym,
            ...     "Calque from Greek; borrowed in 1830s with invention of technology"
            ... )

            >>> # Add comment in multiple languages
            >>> etymOps.SetComment(
            ...     etym,
            ...     "Calque du grec; emprunté vers 1830",
            ...     "fr"
            ... )

        Notes:
            - Empty string is allowed (clears the comment)
            - Can be set independently in multiple writing systems
            - Use for documenting borrowing process, sound changes, etc.
            - Include dates, intermediate forms, or comparative evidence
            - Can be multi-line for detailed explanations

        See Also:
            GetComment, SetBibliography
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")
        self._ValidateParam(text, "text")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        wsHandle = self.__WSHandleAnalysis(ws)

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        etymology.Comment.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetBibliography(self, etymology_or_hvo):
        """
        Get the bibliographic reference for an etymology.

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.

        Returns:
            str: The bibliographic reference, or empty string if not set.

        Raises:
            FP_NullParameterError: If etymology_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if etymologies:
            ...     bib = etymOps.GetBibliography(etymologies[0])
            ...     print(f"Source: {bib}")
            Source: Smith 2020:145; Jones 2018:234

        Notes:
            - Returns empty string if bibliography not set
            - Bibliography stores academic references for the etymology
            - Can contain multiple citations separated by semicolons
            - Use standard citation format for your field
            - No specific format enforced - use consistent style

        See Also:
            SetBibliography, GetComment
        """
        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)

        # Bibliography can be stored as a string property or Unicode accessor
        # Check both possibilities
        if hasattr(etymology, "Bibliography"):
            bib = etymology.Bibliography
            if bib:
                # If it's an ITsString, extract text
                if hasattr(bib, "Text"):
                    return self._NormalizeMultiString(bib.Text)
                # If it's already a string
                elif isinstance(bib, str):
                    return bib
                # Try to cast to ITsString
                else:
                    try:
                        return self._NormalizeMultiString(ITsString(bib).Text)
                    except Exception:
                        return str(bib) if bib else ""

        return ""

    @OperationsMethod
    def SetBibliography(self, etymology_or_hvo, bibliography_text):
        """
        Set the bibliographic reference for an etymology.

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.
            bibliography_text (str): The bibliographic reference.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If etymology_or_hvo or bibliography_text is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etym = etymOps.Create(entry, source="Greek")
            >>> etymOps.SetBibliography(etym, "Smith 2020:145")
            >>> print(etymOps.GetBibliography(etym))
            Smith 2020:145

            >>> # Multiple citations
            >>> etymOps.SetBibliography(
            ...     etym,
            ...     "Smith 2020:145; Jones 2018:234; Brown 2015:89"
            ... )

        Notes:
            - Empty string is allowed (clears the bibliography)
            - Use semicolons to separate multiple citations
            - Common formats: "Author Year:Page", "Author (Year)", etc.
            - Be consistent with citation style across your project
            - Can reference etymological dictionaries, historical sources, etc.

        See Also:
            GetBibliography, SetComment
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")
        self._ValidateParam(bibliography_text, "bibliography_text")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        wsHandle = self.project.project.DefaultAnalWs

        # Bibliography might be stored as string or ITsString
        # Try to set it appropriately
        if hasattr(etymology, "Bibliography"):
            # Check if it's a MultiUnicodeAccessor
            if hasattr(etymology.Bibliography, "set_String"):
                mkstr = TsStringUtils.MakeString(bibliography_text, wsHandle)
                etymology.Bibliography.set_String(wsHandle, mkstr)
            # Otherwise treat as direct string property
            else:
                mkstr = TsStringUtils.MakeString(bibliography_text, wsHandle)
                etymology.Bibliography = mkstr

    # --- Utility Operations ---

    @OperationsMethod
    def GetOwningEntry(self, etymology_or_hvo):
        """
        Get the lexical entry that owns this etymology.

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.

        Returns:
            ILexEntry: The owning entry object.

        Raises:
            FP_NullParameterError: If etymology_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if etymologies:
            ...     owner = etymOps.GetOwningEntry(etymologies[0])
            ...     headword = project.LexEntry.GetHeadword(owner)
            ...     print(f"Entry: {headword}")
            Entry: telephone

        Notes:
            - Returns the ILexEntry that contains this etymology
            - Useful for navigation and context
            - Etymologies always have exactly one owning entry

        See Also:
            GetAll, Create
        """
        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        return ILexEntry(etymology.Owner)

    @OperationsMethod
    def GetGuid(self, etymology_or_hvo):
        """
        Get the GUID (Global Unique Identifier) of an etymology.

        Args:
            etymology_or_hvo: The ILexEtymology object or HVO.

        Returns:
            System.Guid: The GUID of the etymology.

        Raises:
            FP_NullParameterError: If etymology_or_hvo is None.

        Example:
            >>> etymOps = EtymologyOperations(project)
            >>> entry = project.LexEntry.Find("telephone")
            >>> etymologies = list(etymOps.GetAll(entry))
            >>> if etymologies:
            ...     guid = etymOps.GetGuid(etymologies[0])
            ...     print(f"Etymology GUID: {guid}")
            Etymology GUID: 12345678-1234-1234-1234-123456789abc

        Notes:
            - GUIDs are globally unique identifiers
            - Persistent across project versions
            - Use for external references and tracking
            - Same GUID across different copies of the project
            - HVO is project-specific, GUID is universal

        See Also:
            GetOwningEntry, GetAll
        """
        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        return etymology.Guid

    # --- Additional Properties ---

    @OperationsMethod
    def GetLanguage(self, etymology_or_hvo):
        """
        Get the source language of an etymology.

        Args:
            etymology_or_hvo: Either an ILexEtymology object or its HVO

        Returns:
            ICmPossibility: The language possibility object, or None

        Example:
            >>> entry = project.LexEntry.Find("loanword")
            >>> etymologies = project.Etymology.GetAll(entry)
            >>> if etymologies:
            ...     lang = project.Etymology.GetLanguage(etymologies[0])
            ...     if lang:
            ...         print(lang.Name.BestAnalysisAlternative.Text)
        """
        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        return etymology.LanguageRA

    @OperationsMethod
    def SetLanguage(self, etymology_or_hvo, language):
        """
        Set the source language of an etymology.

        Args:
            etymology_or_hvo: Either an ILexEtymology object or its HVO
            language: ICmPossibility object (language) or None

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If etymology_or_hvo is None

        Example:
            >>> entry = project.LexEntry.Find("loanword")
            >>> etymologies = project.Etymology.GetAll(entry)
            >>> if etymologies:
            ...     # Find language possibility (implementation depends on your project structure)
            ...     # language_obj = ... (get from languages list)
            ...     # project.Etymology.SetLanguage(etymologies[0], language_obj)
            ...     pass
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(etymology_or_hvo, "etymology_or_hvo")

        etymology = self.__GetEtymologyObject(etymology_or_hvo)
        etymology.LanguageRA = language

    # --- Private Helper Methods ---

    def __GetEntryObject(self, entry_or_hvo):
        """
        Resolve HVO or object to ILexEntry.

        Args:
            entry_or_hvo: Either an ILexEntry object or an HVO (int).

        Returns:
            ILexEntry: The resolved entry object.

        Raises:
            FP_ParameterError: If HVO doesn't refer to a lexical entry.
        """
        if isinstance(entry_or_hvo, int):
            obj = self.project.Object(entry_or_hvo)
            if not isinstance(obj, ILexEntry):
                raise FP_ParameterError("HVO does not refer to a lexical entry")
            return obj
        return entry_or_hvo

    def __GetEtymologyObject(self, etymology_or_hvo):
        """
        Resolve HVO or object to ILexEtymology.

        Args:
            etymology_or_hvo: Either an ILexEtymology object or an HVO (int).

        Returns:
            ILexEtymology: The resolved etymology object.

        Raises:
            FP_ParameterError: If HVO doesn't refer to an etymology.
        """
        if isinstance(etymology_or_hvo, int):
            obj = self.project.Object(etymology_or_hvo)
            if not isinstance(obj, ILexEtymology):
                raise FP_ParameterError("HVO does not refer to an etymology")
            return obj
        return etymology_or_hvo

    def __WSHandleAnalysis(self, ws):
        """
        Get writing system handle, defaulting to analysis WS.

        Args:
            ws: Optional writing system handle or identifier.

        Returns:
            int: The writing system handle.
        """
        if ws is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(ws, self.project.project.DefaultAnalWs)
