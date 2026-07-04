#
#   ScrDraftOperations.py
#
#   Class: ScrDraftOperations
#          Scripture draft/version operations for FieldWorks Language Explorer
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
    IScrDraft,
    IScrDraftFactory,
    IScripture,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ScrDraftOperations(BaseOperations):
    """
    This class provides operations for managing Scripture drafts/versions in a
    FieldWorks project.

    Scripture drafts are saved versions of the Scripture text, allowing tracking
    of different translation drafts, consultant checks, or archived versions.

    This class should be accessed via FLExProject.ScrDrafts property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all drafts
        for draft in project.ScrDrafts.GetAll():
            desc = project.ScrDrafts.GetDescription(draft)
            print(f"Draft: {desc}")

        # Create a new draft
        draft = project.ScrDrafts.Create("First Draft - January 2025", "saved_version")

        # Find draft by description
        draft = project.ScrDrafts.Find("First Draft")

        # Get books in draft
        books = project.ScrDrafts.GetBooks(draft)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ScrDraftOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all Scripture drafts in the project.

        This method returns an iterator over all IScrDraft objects in the
        project, allowing iteration over all saved Scripture versions.

        Yields:
            IScrDraft: Each Scripture draft object in the project

        Example:
            >>> for draft in project.ScrDrafts.GetAll():
            ...     desc = project.ScrDrafts.GetDescription(draft)
            ...     print(f"Draft: {desc}")
            Draft: First Draft - January 2025
            Draft: Consultant Check - February 2025
            Draft: Final Version - March 2025

        Notes:
            - Returns an iterator for memory efficiency
            - Drafts are returned in database order
            - Use GetDescription() to get the draft description

        See Also:
            Find, Create, GetDescription
        """
        scripture = self.__GetScripture()
        if not scripture:
            return iter([])

        return iter(scripture.ArchivedDraftsOC)

    @OperationsMethod
    def Create(self, description, type="saved_version"):
        """
        Create a new Scripture draft/version.

        Args:
            description (str): Description of the draft (e.g., "First Draft - Jan 2025")
            type (str, optional): Draft type. Defaults to "saved_version".
                Types: "saved_version", "consultant_check", "back_translation"

        Returns:
            IScrDraft: The newly created draft object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If description is None
            FP_ParameterError: If description is empty or Scripture not enabled

        Example:
            >>> # Create a saved version
            >>> draft = project.ScrDrafts.Create("First Draft - January 2025")

            >>> # Create a consultant check draft
            >>> check = project.ScrDrafts.Create(
            ...     "Consultant Review - February 2025",
            ...     "consultant_check"
            ... )

        Notes:
            - Draft is added to Scripture.ArchivedDraftsOC
            - Draft GUID is auto-generated
            - Description should be descriptive and unique
            - Type parameter is for categorization (not strictly enforced)

        See Also:
            Delete, Find, GetDescription
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(description, "description")

        if not description or not description.strip():
            raise FP_ParameterError("Description cannot be empty")

        scripture = self.__GetScripture()
        if not scripture:
            raise FP_ParameterError("Project does not have Scripture enabled")

        with self._TransactionCM("Create draft"):
            # Create the new draft using the factory
            factory = self.project.project.ServiceLocator.GetService(IScrDraftFactory)
            new_draft = factory.Create()

            # Add to Scripture's archived drafts
            scripture.ArchivedDraftsOC.Add(new_draft)

            # Set description
            wsHandle = self.project.project.DefaultAnalWs
            mkstr = TsStringUtils.MakeString(description, wsHandle)
            new_draft.Description.set_String(wsHandle, mkstr)

            # Set type (stored as a string property for reference)
            # Note: IScrDraft doesn't have a Type property in the schema,
            # so this is stored in the description or as metadata
            # For now, we just use description

            return new_draft

    @OperationsMethod
    def Delete(self, draft_or_hvo):
        """
        Delete a Scripture draft from the FLEx project.

        Args:
            draft_or_hvo: Either an IScrDraft object or its HVO (database ID)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If draft_or_hvo is None
            FP_ParameterError: If draft doesn't exist

        Example:
            >>> draft = project.ScrDrafts.Find("Old Draft")
            >>> if draft:
            ...     project.ScrDrafts.Delete(draft)

            >>> # Delete by HVO
            >>> project.ScrDrafts.Delete(12345)

        Warning:
            - This is a destructive operation
            - All books and content in the draft will be deleted
            - Cannot be undone

        Notes:
            - Deletion cascades to all owned objects
            - Does not affect the current Scripture text

        See Also:
            Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(draft_or_hvo, "draft_or_hvo")

        # Resolve to draft object
        draft = self.__ResolveObject(draft_or_hvo)

        # Delete the draft (LCM handles removal from repository)
        draft.Delete()

    @OperationsMethod
    def Find(self, description):
        """
        Find a Scripture draft by its description.

        Args:
            description (str): The draft description to search for (case-insensitive)

        Returns:
            IScrDraft or None: The draft object if found, None otherwise

        Raises:
            FP_NullParameterError: If description is None

        Example:
            >>> draft = project.ScrDrafts.Find("First Draft")
            >>> if draft:
            ...     desc = project.ScrDrafts.GetDescription(draft)
            ...     print(f"Found: {desc}")
            Found: First Draft - January 2025

            >>> # Case-insensitive search
            >>> draft = project.ScrDrafts.Find("first draft")

        Notes:
            - Search is case-insensitive
            - Returns first match only
            - Returns None if not found
            - Partial match searches entire description

        See Also:
            GetAll, GetDescription
        """
        self._ValidateParam(description, "description")

        if not description or not description.strip():
            return None

        scripture = self.__GetScripture()
        if not scripture:
            return None

        wsHandle = self.project.project.DefaultAnalWs
        target = normalize_match_key(description, casefold=True)

        # Search through all drafts
        for draft in scripture.ArchivedDraftsOC:
            draft_desc = ITsString(draft.Description.get_String(wsHandle)).Text
            if target and target in normalize_match_key(draft_desc, casefold=True):
                return draft

        return None

    # --- Draft Properties ---

    @OperationsMethod
    def GetDescription(self, draft_or_hvo):
        """
        Get the description of a Scripture draft.

        Args:
            draft_or_hvo: Either an IScrDraft object or its HVO

        Returns:
            str: The draft description (empty string if not set)

        Raises:
            FP_NullParameterError: If draft_or_hvo is None

        Example:
            >>> draft = project.ScrDrafts.Find("First Draft")
            >>> desc = project.ScrDrafts.GetDescription(draft)
            >>> print(desc)
            First Draft - January 2025

        Notes:
            - Returns empty string if description not set
            - Description is in analysis writing system

        See Also:
            SetDescription, Create
        """
        self._ValidateParam(draft_or_hvo, "draft_or_hvo")

        draft = self.__ResolveObject(draft_or_hvo)
        wsHandle = self.project.project.DefaultAnalWs

        desc = ITsString(draft.Description.get_String(wsHandle)).Text
        return desc or ""

    @OperationsMethod
    def SetDescription(self, draft_or_hvo, text):
        """
        Set the description of a Scripture draft.

        Args:
            draft_or_hvo: Either an IScrDraft object or its HVO
            text (str): The new draft description

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If draft_or_hvo or text is None

        Example:
            >>> draft = project.ScrDrafts.Find("First Draft")
            >>> project.ScrDrafts.SetDescription(
            ...     draft,
            ...     "First Draft - Revised January 2025"
            ... )

        Notes:
            - Description is in analysis writing system
            - Empty description is allowed but not recommended

        See Also:
            GetDescription, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(draft_or_hvo, "draft_or_hvo")
        self._ValidateParam(text, "text")

        draft = self.__ResolveObject(draft_or_hvo)
        wsHandle = self.project.project.DefaultAnalWs

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        draft.Description.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetBooks(self, draft_or_hvo):
        """
        Get all books in a Scripture draft.

        Args:
            draft_or_hvo: Either an IScrDraft object or its HVO

        Returns:
            list: List of IScrBook objects (empty list if none)

        Raises:
            FP_NullParameterError: If draft_or_hvo is None

        Example:
            >>> draft = project.ScrDrafts.Find("First Draft")
            >>> books = project.ScrDrafts.GetBooks(draft)
            >>> for book in books:
            ...     title = project.ScrBooks.GetTitle(book)
            ...     print(f"Book: {title}")

        Notes:
            - Returns empty list if draft has no books
            - Books are in database order (not canonical order)
            - Books in drafts are separate from current Scripture books

        See Also:
            GetDescription
        """
        self._ValidateParam(draft_or_hvo, "draft_or_hvo")

        draft = self.__ResolveObject(draft_or_hvo)
        return list(draft.BooksOS)

    # --- Private Helper Methods ---

    def __ResolveObject(self, draft_or_hvo):
        """
        Resolve HVO or object to IScrDraft.

        Args:
            draft_or_hvo: Either an IScrDraft object or an HVO (int)

        Returns:
            IScrDraft: The resolved draft object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a Scripture draft
        """
        if isinstance(draft_or_hvo, int):
            obj = self.project.Object(draft_or_hvo)
            if not isinstance(obj, IScrDraft):
                raise FP_ParameterError("HVO does not refer to a Scripture draft")
            return obj
        return draft_or_hvo

    def __GetScripture(self):
        """
        Get the Scripture object from the project.

        Returns:
            IScripture or None: The Scripture object if available
        """
        if not hasattr(self.project, "lp") or not self.project.lp:
            return None

        return self.project.lp.TranslatedScriptureOA
