#
#   ReversalIndexOperations.py
#
#   Class: ReversalIndexOperations
#          Reversal index operations for FieldWorks Language Explorer
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
    IReversalIndexFactory,
    IReversalIndexRepository,
    ILangProject,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ReversalIndexOperations(BaseOperations):
    """
    This class provides operations for managing reversal indexes in a FieldWorks project.

    Reversal indexes provide reverse dictionaries for analysis languages (e.g., English
    to vernacular). Each index is tied to a specific writing system and contains reversal
    entries that link back to lexical senses.

    This is a core dictionary feature with LIFT import/export capabilities (753 occurrences
    in codebase).

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Create a reversal index
        en_ws = project.WSHandle('en')
        rev_index = project.ReversalIndexes.Create("English", en_ws)

        # Get all reversal indexes
        for idx in project.ReversalIndexes.GetAll():
            name = project.ReversalIndexes.GetName(idx)
            print(f"Reversal Index: {name}")

        # Find by writing system
        idx = project.ReversalIndexes.FindByWritingSystem(en_ws)

        # Get entries
        entries = project.ReversalIndexes.GetEntries(idx)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ReversalIndexOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all reversal indexes in the project.

        Yields:
            IReversalIndex: Each reversal index object in the project

        Example:
            >>> for idx in project.ReversalIndexes.GetAll():
            ...     name = project.ReversalIndexes.GetName(idx)
            ...     ws = project.ReversalIndexes.GetWritingSystem(idx)
            ...     entry_count = len(list(project.ReversalIndexes.GetEntries(idx)))
            ...     print(f"{name} ({ws}): {entry_count} entries")
            English (en): 250 entries
            French (fr): 120 entries

        Notes:
            - Returns an iterator for memory efficiency
            - Indexes are returned in database order
            - Each index is tied to a specific analysis writing system
            - Empty project returns empty iterator

        See Also:
            Create, Find, FindByWritingSystem
        """
        return self.project.ObjectsIn(IReversalIndexRepository)

    @OperationsMethod
    def Create(self, name, writing_system):
        """
        Create a new reversal index for an analysis writing system.

        Args:
            name (str): Name for the reversal index (e.g., "English", "French")
            writing_system: Writing system handle (must be analysis WS)

        Returns:
            IReversalIndex: The newly created reversal index

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If name or writing_system is None
            FP_ParameterError: If name is empty or index already exists for WS

        Example:
            >>> # Create English reversal index
            >>> en_ws = project.WSHandle('en')
            >>> rev_index = project.ReversalIndexes.Create("English", en_ws)
            >>> print(project.ReversalIndexes.GetName(rev_index))
            English

            >>> # Create French reversal index
            >>> fr_ws = project.WSHandle('fr')
            >>> rev_index = project.ReversalIndexes.Create("French", fr_ws)

        Notes:
            - Name is stored in the default analysis writing system
            - One reversal index per writing system
            - Writing system must be an analysis writing system
            - Index is automatically added to project's reversal indexes
            - New index starts with zero entries

        See Also:
            Delete, Find, FindByWritingSystem, GetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")
        self._ValidateParam(writing_system, "writing_system")

        if not name or not name.strip():
            raise FP_ParameterError("Reversal index name cannot be empty")

        # Check if index already exists for this writing system
        existing = self.FindByWritingSystem(writing_system)
        if existing:
            raise FP_ParameterError(f"Reversal index already exists for writing system {writing_system}")

        with self._TransactionCM(f"Create reversal index '{name}'"):
            # Create the reversal index using factory
            factory = self.project.project.ServiceLocator.GetService(IReversalIndexFactory)
            new_index = factory.Create()

            # Add to language project's reversal indexes
            self.project.lp.LexDbOA.ReversalIndexesOC.Add(new_index)

            # Set the writing system
            new_index.WritingSystem = str(writing_system)

            # Set the name
            wsHandle = self.project.project.DefaultAnalWs
            mkstr = TsStringUtils.MakeString(name, wsHandle)
            new_index.Name.set_String(wsHandle, mkstr)

            return new_index

    @OperationsMethod
    def Delete(self, index_or_hvo):
        """
        Delete a reversal index from the project.

        Args:
            index_or_hvo: Either an IReversalIndex object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If index_or_hvo is None
            FP_ParameterError: If index doesn't exist

        Example:
            >>> idx = project.ReversalIndexes.Find("French")
            >>> if idx:
            ...     project.ReversalIndexes.Delete(idx)

        Warning:
            - This is a destructive operation
            - All reversal entries in the index will be deleted
            - Links to lexical senses will be removed
            - Cannot be undone

        Notes:
            - Deletion cascades to all reversal entries
            - Safe to delete unused reversal indexes

        See Also:
            Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(index_or_hvo, "index_or_hvo")

        index = self.__ResolveObject(index_or_hvo)

        # Delete the index (LCM handles removal from repository)
        index.Delete()

    @OperationsMethod
    def Find(self, name):
        """
        Find a reversal index by its name.

        Args:
            name (str): The reversal index name to search for

        Returns:
            IReversalIndex or None: The index object if found, None otherwise

        Raises:
            FP_NullParameterError: If name is None

        Example:
            >>> idx = project.ReversalIndexes.Find("English")
            >>> if idx:
            ...     entries = list(project.ReversalIndexes.GetEntries(idx))
            ...     print(f"English index has {len(entries)} entries")
            English index has 250 entries

        Notes:
            - Returns first match only
            - Search is case-sensitive
            - Returns None if not found (doesn't raise exception)

        See Also:
            FindByWritingSystem, GetAll, GetName
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        wsHandle = self.project.project.DefaultAnalWs

        # Search through all reversal indexes
        target = normalize_match_key(name, casefold=False)
        for idx in self.GetAll():
            idx_name = ITsString(idx.Name.get_String(wsHandle)).Text
            if normalize_match_key(idx_name, casefold=False) == target:
                return idx

        return None

    @OperationsMethod
    def FindByWritingSystem(self, ws):
        """
        Find a reversal index by its writing system.

        Args:
            ws: Writing system handle or string identifier

        Returns:
            IReversalIndex or None: The index object if found, None otherwise

        Raises:
            FP_NullParameterError: If ws is None

        Example:
            >>> en_ws = project.WSHandle('en')
            >>> idx = project.ReversalIndexes.FindByWritingSystem(en_ws)
            >>> if idx:
            ...     name = project.ReversalIndexes.GetName(idx)
            ...     print(f"Found reversal index: {name}")
            Found reversal index: English

            >>> # Can also use string identifier
            >>> idx = project.ReversalIndexes.FindByWritingSystem('en')

        Notes:
            - Each writing system has at most one reversal index
            - Returns None if no index exists for that writing system
            - Writing system must be an analysis writing system

        See Also:
            Find, GetWritingSystem, Create
        """
        self._ValidateParam(ws, "ws")

        # Convert to string if handle provided
        ws_str = str(ws)

        # Search through all reversal indexes
        for idx in self.GetAll():
            if idx.WritingSystem == ws_str:
                return idx

        return None

    # --- Property Access ---

    @OperationsMethod
    def GetName(self, index_or_hvo, wsHandle=None):
        """
        Get the name of a reversal index.

        Args:
            index_or_hvo: Either an IReversalIndex object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The index name (empty string if not set)

        Raises:
            FP_NullParameterError: If index_or_hvo is None

        Example:
            >>> idx = project.ReversalIndexes.FindByWritingSystem('en')
            >>> name = project.ReversalIndexes.GetName(idx)
            >>> print(name)
            English

        See Also:
            SetName, Find
        """
        self._ValidateParam(index_or_hvo, "index_or_hvo")

        index = self.__ResolveObject(index_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        name = ITsString(index.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, index_or_hvo, name, wsHandle=None):
        """
        Set the name of a reversal index.

        Args:
            index_or_hvo: Either an IReversalIndex object or its HVO
            name (str): The new index name
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If index_or_hvo or name is None
            FP_ParameterError: If name is empty

        Example:
            >>> idx = project.ReversalIndexes.FindByWritingSystem('en')
            >>> project.ReversalIndexes.SetName(idx, "English Reversal")
            >>> print(project.ReversalIndexes.GetName(idx))
            English Reversal

        See Also:
            GetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(index_or_hvo, "index_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Reversal index name cannot be empty")

        index = self.__ResolveObject(index_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        index.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetWritingSystem(self, index_or_hvo):
        """
        Get the writing system of a reversal index.

        Args:
            index_or_hvo: Either an IReversalIndex object or its HVO

        Returns:
            str: The writing system identifier (e.g., 'en', 'fr')

        Raises:
            FP_NullParameterError: If index_or_hvo is None

        Example:
            >>> idx = project.ReversalIndexes.Find("English")
            >>> ws = project.ReversalIndexes.GetWritingSystem(idx)
            >>> print(ws)
            en

        See Also:
            FindByWritingSystem
        """
        self._ValidateParam(index_or_hvo, "index_or_hvo")

        index = self.__ResolveObject(index_or_hvo)

        return index.WritingSystem or ""

    @OperationsMethod
    def GetEntries(self, index_or_hvo):
        """
        Get all reversal entries in a reversal index.

        Args:
            index_or_hvo: Either an IReversalIndex object or its HVO

        Yields:
            IReversalIndexEntry: Each reversal entry in the index

        Raises:
            FP_NullParameterError: If index_or_hvo is None

        Example:
            >>> idx = project.ReversalIndexes.Find("English")
            >>> for entry in project.ReversalIndexes.GetEntries(idx):
            ...     form = project.ReversalEntries.GetForm(entry)
            ...     senses = project.ReversalEntries.GetSenses(entry)
            ...     print(f"{form}: {len(list(senses))} senses")
            run: 3 senses
            walk: 2 senses

        Notes:
            - Returns an iterator for memory efficiency
            - Entries are in hierarchical order (top-level first)
            - Does not include subentries (use GetSubentries for those)
            - Returns empty iterator if index has no entries

        See Also:
            project.ReversalEntries.GetAll, project.ReversalEntries.Create
        """
        self._ValidateParam(index_or_hvo, "index_or_hvo")

        index = self.__ResolveObject(index_or_hvo)

        # Iterate through all entries in the index
        for entry in index.EntriesOC:
            yield entry

    @OperationsMethod
    def ExportToLIFT(self, index_or_hvo, path):
        """
        Export a reversal index to LIFT format.

        Args:
            index_or_hvo: Either an IReversalIndex object or its HVO
            path (str): File path for the exported LIFT file

        Raises:
            FP_NullParameterError: If index_or_hvo or path is None
            FP_ParameterError: If path is invalid or index has no entries

        Example:
            >>> idx = project.ReversalIndexes.Find("English")
            >>> project.ReversalIndexes.ExportToLIFT(idx, "english_reversal.lift")

        Notes:
            - LIFT (Lexicon Interchange FormaT) is an XML format
            - Exports reversal entries with their linked senses
            - Compatible with other lexicography tools
            - Not implemented in this version (placeholder for future feature)

        Warning:
            This method is a placeholder and not yet implemented.
            Use FLEx's built-in export functionality for now.

        See Also:
            GetEntries
        """
        self._ValidateParam(index_or_hvo, "index_or_hvo")
        self._ValidateParam(path, "path")

        # Placeholder for future implementation
        raise FP_ParameterError("ExportToLIFT not yet implemented. " "Use FLEx's built-in LIFT export functionality.")

    # --- Private Helper Methods ---

    def __ResolveObject(self, index_or_hvo):
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

    def __WSHandleAnalysis(self, wsHandle):
        """
        Get writing system handle, defaulting to analysis WS.

        Args:
            wsHandle: Optional writing system handle

        Returns:
            int: The writing system handle
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)
