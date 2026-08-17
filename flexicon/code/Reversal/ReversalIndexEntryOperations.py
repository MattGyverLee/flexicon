#
#   ReversalIndexEntryOperations.py
#
#   Class: ReversalIndexEntryOperations
#          Reversal index entry operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key

# Import FLEx LCM types
from SIL.LCModel import (
    IReversalIndex,
    IReversalIndexEntry,
    IReversalIndexEntryFactory,
    ILexSense,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ReversalIndexEntryOperations(BaseOperations):
    """
    This class provides operations for managing reversal index entries in a FieldWorks project.

    Reversal index entries are the individual entries within a reversal index. Each entry
    has a form (the reverse headword) and links to one or more lexical senses. Entries can
    be organized hierarchically with subentries.

    Reversal entries enable users to look up words in the analysis language and find
    corresponding vernacular entries.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get reversal index
        en_ws = project.WSHandle('en')
        idx = project.ReversalIndexes.FindByWritingSystem(en_ws)

        # Create reversal entry
        entry = project.ReversalEntries.Create(idx, "run")

        # Link to lexical sense
        lex_entry = list(project.LexiconAllEntries())[0]
        sense = list(lex_entry.SensesOS)[0]
        project.ReversalEntries.AddSense(entry, sense)

        # Get all entries
        for rev_entry in project.ReversalEntries.GetAll(idx):
            form = project.ReversalEntries.GetForm(rev_entry)
            print(f"Reversal: {form}")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ReversalIndexEntryOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for reversal entries.
        For ReversalIndexEntry, we reorder parent.SubentriesOS
        """
        return parent.SubentriesOS

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, index_or_hvo):
        """
        Get all reversal entries in a reversal index.

        Args:
            index_or_hvo: Either an IReversalIndex object or its HVO

        Returns:
            EnumerableWrapper[IReversalIndexEntry]: Each reversal entry in the index

        Raises:
            FP_NullParameterError: If index_or_hvo is None

        Example:
            >>> idx = project.ReversalIndexes.Find("English")
            >>> for entry in project.ReversalEntries.GetAll(idx):
            ...     form = project.ReversalEntries.GetForm(entry)
            ...     sense_count = len(list(project.ReversalEntries.GetSenses(entry)))
            ...     print(f"{form}: {sense_count} senses")
            run: 3 senses
            walk: 2 senses

        Notes:
            - Returns top-level entries only (not subentries)
            - Use GetSubentries() to access hierarchical subentries
            - Returns empty iterator if index has no entries
            - Entries are in database order

        See Also:
            Create, GetSubentries, FindByHvo
        """
        self._ValidateParam(index_or_hvo, "index_or_hvo")

        index = self.__GetIndexObject(index_or_hvo)

        for entry in index.EntriesOC:
            yield entry

    @OperationsMethod
    def Create(self, index_or_hvo, form, sense=None, wsHandle=None, guid=None):
        """
        Create a new reversal index entry.

        Args:
            index_or_hvo: Either an IReversalIndex object or its HVO
            form (str): The reversal form (headword in analysis language)
            sense: Optional ILexSense object to link to. Must already be
                an ILexSense resolved in the TARGET project -- SensesRS
                is a reference, not an owning relationship, and a
                reference cannot span two LcmCache instances. Resolve
                the correct target-project sense yourself before calling.
            wsHandle: Optional writing system handle. Defaults to index's WS.
            guid (optional): GUID to assign to the new entry, as a
                ``System.Guid`` or string. Use this when REPRODUCING an
                entry from another project so it keeps its original
                identity. Transport-only: like WordformOperations.Create,
                this method performs NO deduplication -- neither by guid
                nor by form -- so callers must call Find() first if they
                need to avoid duplicates. None (the default) mints a
                fresh GUID.

        Returns:
            IReversalIndexEntry: The newly created reversal entry

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If index_or_hvo or form is None
            FP_ParameterError: If form is empty, or guid was supplied but
                is not a valid GUID.

        Example:
            >>> idx = project.ReversalIndexes.Find("English")
            >>> entry = project.ReversalEntries.Create(idx, "run")
            >>> print(project.ReversalEntries.GetForm(entry))
            run

            >>> # Create with linked sense
            >>> lex_entry = project.LexEntry.Find("hlauka")
            >>> sense = list(lex_entry.SensesOS)[0]
            >>> entry = project.ReversalEntries.Create(idx, "run", sense)

        Notes:
            - Entry is added to the reversal index
            - If sense provided, it's automatically linked
            - Form is stored in the index's writing system
            - Entry can link to multiple senses via AddSense()
            - This method ALWAYS adds the new entry to
              ``index.EntriesOC`` (top-level). There is no path here to
              create directly into a parent entry's ``SubentriesOS``, so
              a reproduced SUBentry from another project will land
              top-level and must be re-parented by the caller afterward.
            - If the requested guid is already present in the project,
              creation falls back to a fresh identity and logs a
              warning; it does not raise.

        See Also:
            Delete, Find, AddSense
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(index_or_hvo, "index_or_hvo")
        self._ValidateParam(form, "form")

        if not form or not form.strip():
            raise FP_ParameterError("Reversal entry form cannot be empty")

        index = self.__GetIndexObject(index_or_hvo)

        # Get writing system from index if not provided
        if wsHandle is None:
            ws_str = index.WritingSystem
            wsHandle = self.project.WSHandle(ws_str)

        with self._TransactionCM(f"Create reversal entry '{form}'"):
            # Create the reversal entry using factory
            factory = self.project.project.ServiceLocator.GetService(IReversalIndexEntryFactory)
            new_entry = self._CreateWithGuid(factory, guid, "IReversalIndexEntry")

            # Add to index's entries collection
            index.EntriesOC.Add(new_entry)

            # Set the reversal form
            mkstr = TsStringUtils.MakeString(form, wsHandle)
            new_entry.ReversalForm.set_String(wsHandle, mkstr)

            # Link to sense if provided
            if sense:
                new_entry.SensesRS.Add(sense)

            return new_entry

    @OperationsMethod
    def Delete(self, entry_or_hvo):
        """
        Delete a reversal index entry.

        Args:
            entry_or_hvo: Either an IReversalIndexEntry object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If entry_or_hvo is None

        Example:
            >>> entry = project.ReversalEntries.Find(idx, "obsolete")
            >>> if entry:
            ...     project.ReversalEntries.Delete(entry)

        Warning:
            - This is a destructive operation
            - All subentries will be deleted
            - Links to lexical senses will be removed
            - Cannot be undone

        Notes:
            - Deletion cascades to all subentries
            - Links from lexical senses are automatically cleaned up

        See Also:
            Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(entry_or_hvo, "entry_or_hvo")

        entry = self.__ResolveObject(entry_or_hvo)

        with self._TransactionCM("Delete reversal entry"):
            # Delete the entry (LCM handles removal from collections)
            entry.Delete()

    @OperationsMethod
    def Find(self, index_or_hvo, form, wsHandle=None):
        """
        Find a reversal entry by its form.

        Args:
            index_or_hvo: Either an IReversalIndex object or its HVO
            form (str): The reversal form to search for
            wsHandle: Optional writing system handle. Defaults to index's WS.

        Returns:
            IReversalIndexEntry or None: The entry object if found, None otherwise

        Raises:
            FP_NullParameterError: If index_or_hvo or form is None

        Example:
            >>> idx = project.ReversalIndexes.Find("English")
            >>> entry = project.ReversalEntries.Find(idx, "run")
            >>> if entry:
            ...     senses = list(project.ReversalEntries.GetSenses(entry))
            ...     print(f"Found 'run' with {len(senses)} senses")
            Found 'run' with 3 senses

        Notes:
            - Returns first match only
            - Search is case-sensitive
            - Searches top-level entries only (not subentries)
            - Returns None if not found

        See Also:
            FindByHvo, Create, GetAll
        """
        self._ValidateParam(index_or_hvo, "index_or_hvo")
        self._ValidateParam(form, "form")

        if not form or not form.strip():
            return None

        index = self.__GetIndexObject(index_or_hvo)

        # Get writing system from index if not provided
        if wsHandle is None:
            ws_str = index.WritingSystem
            wsHandle = self.project.WSHandle(ws_str)

        # Search through all entries
        target = normalize_match_key(form, casefold=False)
        for entry in self.GetAll(index):
            entry_form = ITsString(entry.ReversalForm.get_String(wsHandle)).Text
            if normalize_match_key(entry_form, casefold=False) == target:
                return entry

        return None

    @OperationsMethod
    def FindByHvo(self, hvo):
        """
        Find a reversal entry by its HVO (database ID).

        Args:
            hvo (int): The HVO of the reversal entry

        Returns:
            IReversalIndexEntry or None: The entry object if found, None otherwise

        Raises:
            FP_NullParameterError: If hvo is None

        Example:
            >>> entry = project.ReversalEntries.FindByHvo(12345)
            >>> if entry:
            ...     form = project.ReversalEntries.GetForm(entry)
            ...     print(f"Found entry: {form}")

        Notes:
            - Direct HVO lookup is faster than searching by form
            - Returns None if HVO doesn't exist or isn't a reversal entry
            - HVO is the internal database identifier

        See Also:
            Find, GetAll
        """
        self._ValidateParam(hvo, "hvo")

        try:
            obj = self.project.Object(hvo)
            if isinstance(obj, IReversalIndexEntry):
                return obj
        except Exception:
            pass

        return None

    # --- Property Access ---

    @OperationsMethod
    def GetForm(self, entry_or_hvo, wsHandle=None):
        """
        Get the reversal form of a reversal entry.

        Args:
            entry_or_hvo: Either an IReversalIndexEntry object or its HVO
            wsHandle: Optional writing system handle. Defaults to entry's index WS.

        Returns:
            str: The reversal form text (empty string if not set)

        Raises:
            FP_NullParameterError: If entry_or_hvo is None

        Example:
            >>> entry = project.ReversalEntries.Find(idx, "run")
            >>> form = project.ReversalEntries.GetForm(entry)
            >>> print(form)
            run

        See Also:
            SetForm, Find
        """
        self._ValidateParam(entry_or_hvo, "entry_or_hvo")

        entry = self.__ResolveObject(entry_or_hvo)

        # Use entry's index writing system if not provided
        if wsHandle is None:
            wsHandle = self.__GetEntryWS(entry)

        form = ITsString(entry.ReversalForm.get_String(wsHandle)).Text
        return form or ""

    @OperationsMethod
    def SetForm(self, entry_or_hvo, text, wsHandle=None):
        """
        Set the reversal form of a reversal entry.

        Args:
            entry_or_hvo: Either an IReversalIndexEntry object or its HVO
            text (str): The new reversal form text
            wsHandle: Optional writing system handle. Defaults to entry's index WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If entry_or_hvo or text is None
            FP_ParameterError: If text is empty

        Example:
            >>> entry = project.ReversalEntries.Find(idx, "run")
            >>> project.ReversalEntries.SetForm(entry, "running")
            >>> print(project.ReversalEntries.GetForm(entry))
            running

        See Also:
            GetForm
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(entry_or_hvo, "entry_or_hvo")
        self._ValidateParam(text, "text")

        if not text or not text.strip():
            raise FP_ParameterError("Reversal entry form cannot be empty")

        entry = self.__ResolveObject(entry_or_hvo)

        # Use entry's index writing system if not provided
        if wsHandle is None:
            wsHandle = self.__GetEntryWS(entry)

        with self._TransactionCM(f"Set reversal form '{text}'"):
            mkstr = TsStringUtils.MakeString(text, wsHandle)
            entry.ReversalForm.set_String(wsHandle, mkstr)

    # --- Sense Linking ---

    @OperationsMethod
    def GetSenses(self, entry_or_hvo):
        """
        Get all lexical senses linked to this reversal entry.

        Args:
            entry_or_hvo: Either an IReversalIndexEntry object or its HVO

        Returns:
            list: List of ILexSense objects

        Raises:
            FP_NullParameterError: If entry_or_hvo is None

        Example:
            >>> entry = project.ReversalEntries.Find(idx, "run")
            >>> senses = project.ReversalEntries.GetSenses(entry)
            >>> for sense in senses:
            ...     gloss = project.Senses.GetGloss(sense)
            ...     print(f"Linked sense: {gloss}")
            Linked sense: to move rapidly
            Linked sense: to flow
            Linked sense: to operate

        Notes:
            - Returns empty list if no senses linked
            - One reversal entry can link to multiple senses
            - Links are bidirectional (sense also knows about reversal entry)

        See Also:
            AddSense, RemoveSense
        """
        self._ValidateParam(entry_or_hvo, "entry_or_hvo")

        entry = self.__ResolveObject(entry_or_hvo)

        return list(entry.SensesRS)

    @OperationsMethod
    def AddSense(self, entry_or_hvo, sense):
        """
        Link a lexical sense to this reversal entry.

        Args:
            entry_or_hvo: Either an IReversalIndexEntry object or its HVO
            sense: ILexSense object to link

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If entry_or_hvo or sense is None

        Example:
            >>> entry = project.ReversalEntries.Find(idx, "run")
            >>> lex_entry = project.LexEntry.Find("hlauka")
            >>> sense = list(lex_entry.SensesOS)[0]
            >>> project.ReversalEntries.AddSense(entry, sense)

        Notes:
            - Multiple senses can be linked to one reversal entry
            - Duplicate links are automatically prevented
            - Link is bidirectional

        See Also:
            RemoveSense, GetSenses
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(entry_or_hvo, "entry_or_hvo")
        self._ValidateParam(sense, "sense")

        entry = self.__ResolveObject(entry_or_hvo)

        # Add sense if not already linked. The membership test stays OUTSIDE
        # the transaction so an already-linked sense is a true no-op and does
        # not open an empty undo task.
        if sense not in entry.SensesRS:
            with self._TransactionCM("Link sense to reversal entry"):
                entry.SensesRS.Add(sense)

    @OperationsMethod
    def RemoveSense(self, entry_or_hvo, sense):
        """
        Unlink a lexical sense from this reversal entry.

        Args:
            entry_or_hvo: Either an IReversalIndexEntry object or its HVO
            sense: ILexSense object to unlink

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If entry_or_hvo or sense is None

        Example:
            >>> entry = project.ReversalEntries.Find(idx, "run")
            >>> sense = list(project.ReversalEntries.GetSenses(entry))[0]
            >>> project.ReversalEntries.RemoveSense(entry, sense)

        Notes:
            - Safe to call even if sense not linked
            - Doesn't delete the sense, only removes the link
            - Link removal is bidirectional

        See Also:
            AddSense, GetSenses
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(entry_or_hvo, "entry_or_hvo")
        self._ValidateParam(sense, "sense")

        entry = self.__ResolveObject(entry_or_hvo)

        # Remove sense if linked. The membership test stays OUTSIDE the
        # transaction so an unlinked sense is a true no-op and does not open
        # an empty undo task.
        if sense in entry.SensesRS:
            with self._TransactionCM("Unlink sense from reversal entry"):
                entry.SensesRS.Remove(sense)

    # --- Hierarchical Structure ---

    @OperationsMethod
    def GetSubentries(self, entry_or_hvo):
        """
        Get all subentries of a reversal entry.

        Args:
            entry_or_hvo: Either an IReversalIndexEntry object or its HVO

        Returns:
            list: List of IReversalIndexEntry objects (subentries)

        Raises:
            FP_NullParameterError: If entry_or_hvo is None

        Example:
            >>> entry = project.ReversalEntries.Find(idx, "run")
            >>> subentries = project.ReversalEntries.GetSubentries(entry)
            >>> for sub in subentries:
            ...     form = project.ReversalEntries.GetForm(sub)
            ...     print(f"Subentry: {form}")
            Subentry: run away
            Subentry: run out

        Notes:
            - Returns empty list if no subentries
            - Subentries enable hierarchical organization
            - Common for phrasal verbs, compounds, etc.
            - Use _GetSequence() for reordering subentries

        See Also:
            Create, GetAll
        """
        self._ValidateParam(entry_or_hvo, "entry_or_hvo")

        entry = self.__ResolveObject(entry_or_hvo)

        return list(entry.SubentriesOS)

    # --- Private Helper Methods ---

    def __ResolveObject(self, entry_or_hvo):
        """
        Resolve HVO or object to IReversalIndexEntry.

        Args:
            entry_or_hvo: Either an IReversalIndexEntry object or an HVO (int)

        Returns:
            IReversalIndexEntry: The resolved entry object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a reversal entry
        """
        if isinstance(entry_or_hvo, int):
            obj = self.project.Object(entry_or_hvo)
            if not isinstance(obj, IReversalIndexEntry):
                raise FP_ParameterError("HVO does not refer to a reversal index entry")
            return obj
        return entry_or_hvo

    def __GetIndexObject(self, index_or_hvo):
        """
        Resolve HVO or object to IReversalIndex.

        Args:
            index_or_hvo: Either an IReversalIndex object or an HVO (int)

        Returns:
            IReversalIndex: The resolved index object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a reversal index
        """
        if isinstance(index_or_hvo, int):
            obj = self.project.Object(index_or_hvo)
            if not isinstance(obj, IReversalIndex):
                raise FP_ParameterError("HVO does not refer to a reversal index")
            return obj
        return index_or_hvo

    def __GetEntryWS(self, entry):
        """
        Get the writing system handle for a reversal entry.

        Args:
            entry: IReversalIndexEntry object

        Returns:
            int: Writing system handle from the entry's parent index
        """
        # Get the owning reversal index
        index = entry.ReversalIndex
        if index is None:
            raise FP_ParameterError(
                f"ReversalIndex is None for entry '{entry.Hvo}' -- "
                "entry may be orphaned or cascade-deleted."
            )
        ws_str = index.WritingSystem
        return self.project.WSHandle(ws_str)
