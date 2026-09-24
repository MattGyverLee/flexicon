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

        from flexicon import FLExProject

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

        This method returns an EnumerableWrapper (subscriptable, len()-able, lazily materialized) over all IScrDraft objects in the
        project, allowing iteration over all saved Scripture versions.

        Returns:
            EnumerableWrapper[IScrDraft]: Each Scripture draft object in the project

        Example:
            >>> for draft in project.ScrDrafts.GetAll():
            ...     desc = project.ScrDrafts.GetDescription(draft)
            ...     print(f"Draft: {desc}")
            Draft: First Draft - January 2025
            Draft: Consultant Check - February 2025
            Draft: Final Version - March 2025

        Notes:
            - Returns an EnumerableWrapper (subscriptable, len()-able) for memory efficiency; the underlying LCM enumerator is only materialized into a list on first len()/index/iteration access
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
            - Type selects the LCM ScrDraftType (saved version, consultant
              check, or back translation)

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

        draft_type = self.__CoerceDraftType(type)

        with self._TransactionCM("Create draft"):
            # IScrDraftFactory exposes no no-arg Create() -- only
            # Create(description[, ...]) (live-proven TypeError; issue
            # #352 follow-up). The factory parents the new draft into
            # ArchivedDraftsOC itself, so only Add when it did not
            # (compare by HVO: proxies have no stable identity).
            factory = self.project.project.ServiceLocator.GetService(IScrDraftFactory)
            try:
                new_draft = factory.Create(description, draft_type)
            except TypeError:
                new_draft = factory.Create(description)
                new_draft.Type = draft_type

            if new_draft.Hvo not in {d.Hvo for d in scripture.ArchivedDraftsOC}:
                scripture.ArchivedDraftsOC.Add(new_draft)

            # Description is a scalar String, not a multistring
            # (live-proven: plain str; issue #352) -- assign directly,
            # same as SemanticDomain OcmCodes. The factory already set
            # it from the description argument; re-assert it so a later
            # refactor of the factory call cannot silently drop it.
            new_draft.Description = description

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

        with self._TransactionCM("Delete scripture draft"):
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

        target = normalize_match_key(description, casefold=True)

        # Search through all drafts. Description is a scalar String
        # (issue #352), so there is no writing-system dimension.
        for draft in scripture.ArchivedDraftsOC:
            draft_desc = draft.Description or ""
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
            - Description is a scalar String (no writing-system
              variants; issue #352)

        See Also:
            SetDescription, Create
        """
        self._ValidateParam(draft_or_hvo, "draft_or_hvo")

        draft = self.__ResolveObject(draft_or_hvo)

        return draft.Description or ""

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
            - Description is a scalar String (no writing-system
              variants; issue #352)
            - Empty description is allowed but not recommended

        See Also:
            GetDescription, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(draft_or_hvo, "draft_or_hvo")
        self._ValidateParam(text, "text")

        draft = self.__ResolveObject(draft_or_hvo)

        with self._TransactionCM("Set draft description"):
            draft.Description = text

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
            if getattr(obj, "ClassName", None) == "ScrDraft":
                try:
                    return IScrDraft(obj)
                except Exception:
                    pass
            if isinstance(obj, IScrDraft):
                return obj
            raise FP_ParameterError("HVO does not refer to a Scripture draft")
        if getattr(draft_or_hvo, "ClassName", None) == "ScrDraft":
            try:
                return IScrDraft(draft_or_hvo)
            except Exception:
                pass
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

    def __CoerceDraftType(self, type_label):
        """
        Map a user-facing draft-type label to ScrDraftType.

        Raises:
            FP_ParameterError: If the label is unknown or empty after strip.
        """
        if type_label is None:
            raise FP_ParameterError("Draft type cannot be None")
        key = str(type_label).strip().lower()
        if not key:
            raise FP_ParameterError("Draft type cannot be empty")
        from SIL.LCModel import ScrDraftType

        by_label = {
            "saved_version": ScrDraftType.SavedVersion,
            "consultant_check": ScrDraftType.ConsultantCheck,
            "back_translation": ScrDraftType.BackTranslation,
        }
        try:
            return by_label[key]
        except KeyError:
            allowed = ", ".join(sorted(by_label))
            raise FP_ParameterError(
                f"Unknown draft type {type_label!r}; expected one of: {allowed}"
            )
