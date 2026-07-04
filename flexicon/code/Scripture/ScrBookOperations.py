#
#   ScrBookOperations.py
#
#   Class: ScrBookOperations
#          Scripture book operations for FieldWorks Language Explorer
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
    IScrBook,
    IScrBookFactory,
    IScrBookRepository,
    IScrSection,
    IScripture,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import string utilities
from ..Shared.string_utils import normalize_match_key


class ScrBookOperations(BaseOperations):
    """
    This class provides operations for managing Scripture books in a
    FieldWorks project.

    Scripture books represent individual books of the Bible (Genesis, Matthew,
    etc.) identified by canonical numbers (1-66 for standard Protestant canon).
    Each book contains sections with headings and paragraph content.

    This class should be accessed via FLExProject.ScrBooks property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all Scripture books
        for book in project.ScrBooks.GetAll():
            title = project.ScrBooks.GetTitle(book)
            print(f"Book: {title}")

        # Create a new book (Genesis = 1)
        genesis = project.ScrBooks.Create(1, "Genesis")

        # Find book by canonical number
        matthew = project.ScrBooks.Find(40)  # Matthew = 40

        # Get sections in a book
        sections = project.ScrBooks.GetSections(genesis)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ScrBookOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all Scripture books in the project.

        This method returns an iterator over all IScrBook objects in the
        project, allowing iteration over all Scripture books.

        Yields:
            IScrBook: Each Scripture book object in the project

        Example:
            >>> for book in project.ScrBooks.GetAll():
            ...     title = project.ScrBooks.GetTitle(book)
            ...     num = project.ScrBooks.GetCanonicalNum(book)
            ...     print(f"{num}: {title}")
            1: Genesis
            2: Exodus
            40: Matthew

        Notes:
            - Returns an iterator for memory efficiency
            - Books are returned in database order (not canonical order)
            - Use GetCanonicalNum() to get the book number
            - For sorted books, sort by canonical number

        See Also:
            Find, Create, GetCanonicalNum
        """
        scripture = self.__GetScripture()
        if not scripture:
            return iter([])

        return iter(scripture.ScriptureBooksOS)

    @OperationsMethod
    def Create(self, canonical_num, title=None):
        """
        Create a new Scripture book with the specified canonical number.

        Args:
            canonical_num (int): The canonical book number (1-66 for Protestant canon)
                1=Genesis, 2=Exodus, ... 40=Matthew, 41=Mark, ... 66=Revelation
            title (str, optional): Book title. If None, uses default title for
                the canonical number.

        Returns:
            IScrBook: The newly created Scripture book object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If canonical_num is None
            FP_ParameterError: If canonical_num is invalid or book already exists

        Example:
            >>> # Create Genesis
            >>> genesis = project.ScrBooks.Create(1, "Genesis")
            >>> print(project.ScrBooks.GetTitle(genesis))
            Genesis

            >>> # Create Matthew (canonical number 40)
            >>> matthew = project.ScrBooks.Create(40, "Matthew")

            >>> # Create with default title
            >>> exodus = project.ScrBooks.Create(2)

        Notes:
            - Canonical numbers: 1-39 = OT, 40-66 = NT (Protestant canon)
            - Each canonical number can only be used once
            - Book is added to Scripture.ScriptureBooksOS
            - Book GUID is auto-generated
            - Title defaults to English name if not specified

        See Also:
            Delete, Find, GetCanonicalNum
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(canonical_num, "canonical_num")

        if not isinstance(canonical_num, int) or canonical_num < 1 or canonical_num > 66:
            raise FP_ParameterError(f"Canonical number must be an integer between 1 and 66, got {canonical_num}")

        scripture = self.__GetScripture()
        if not scripture:
            raise FP_ParameterError("Project does not have Scripture enabled")

        # Check if book already exists
        existing = self.Find(canonical_num)
        if existing:
            raise FP_ParameterError(f"Book with canonical number {canonical_num} already exists")

        with self._TransactionCM(f"Create book {canonical_num}"):
            # Create the new book using the factory
            factory = self.project.project.ServiceLocator.GetService(IScrBookFactory)
            new_book = factory.Create(scripture.ScriptureBooksOS, canonical_num)

            # Set title if provided
            if title:
                wsHandle = self.project.project.DefaultVernWs
                mkstr = TsStringUtils.MakeString(title, wsHandle)
                new_book.Title.set_String(wsHandle, mkstr)

            return new_book

    @OperationsMethod
    def Delete(self, book_or_hvo):
        """
        Delete a Scripture book from the FLEx project.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO (database ID)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If book_or_hvo is None
            FP_ParameterError: If book doesn't exist

        Example:
            >>> book = project.ScrBooks.Find(1)  # Genesis
            >>> if book:
            ...     project.ScrBooks.Delete(book)

            >>> # Delete by HVO
            >>> project.ScrBooks.Delete(12345)

        Warning:
            - This is a destructive operation
            - All sections and paragraphs will be deleted
            - Cannot be undone

        Notes:
            - Deletion cascades to all owned objects (sections, paragraphs, etc.)
            - The canonical number becomes available for reuse

        See Also:
            Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(book_or_hvo, "book_or_hvo")

        # Resolve to book object
        book = self.__ResolveObject(book_or_hvo)

        # Delete the book (LCM handles removal from repository)
        book.Delete()

    @OperationsMethod
    def Find(self, canonical_num):
        """
        Find a Scripture book by its canonical number.

        Args:
            canonical_num (int): The canonical book number (1-66)

        Returns:
            IScrBook or None: The book object if found, None otherwise

        Raises:
            FP_NullParameterError: If canonical_num is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> if genesis:
            ...     title = project.ScrBooks.GetTitle(genesis)
            ...     print(f"Found: {title}")
            Found: Genesis

            >>> # Find Matthew (canonical number 40)
            >>> matthew = project.ScrBooks.Find(40)

        Notes:
            - Returns first match only (should be unique)
            - Returns None if not found (doesn't raise exception)
            - Canonical numbers: 1-39 = OT, 40-66 = NT

        See Also:
            FindByName, GetAll, GetCanonicalNum
        """
        self._ValidateParam(canonical_num, "canonical_num")

        scripture = self.__GetScripture()
        if not scripture:
            return None

        # Search through all books
        for book in scripture.ScriptureBooksOS:
            if book.CanonicalNum == canonical_num:
                return book

        return None

    @OperationsMethod
    def FindByName(self, name):
        """
        Find a Scripture book by its title/name.

        Args:
            name (str): The book title to search for (case-insensitive)

        Returns:
            IScrBook or None: The book object if found, None otherwise

        Raises:
            FP_NullParameterError: If name is None

        Example:
            >>> genesis = project.ScrBooks.FindByName("Genesis")
            >>> if genesis:
            ...     num = project.ScrBooks.GetCanonicalNum(genesis)
            ...     print(f"Canonical number: {num}")
            Canonical number: 1

            >>> # Case-insensitive search
            >>> matthew = project.ScrBooks.FindByName("matthew")

        Notes:
            - Search is case-insensitive
            - Returns first match only
            - Returns None if not found
            - Searches in default vernacular writing system

        See Also:
            Find, GetTitle
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        scripture = self.__GetScripture()
        if not scripture:
            return None

        wsHandle = self.project.project.DefaultVernWs
        target = normalize_match_key(name, casefold=True)

        # Search through all books
        for book in scripture.ScriptureBooksOS:
            book_title = ITsString(book.Title.get_String(wsHandle)).Text
            if book_title and normalize_match_key(book_title, casefold=True) == target:
                return book

        return None

    # --- Book Properties ---

    @OperationsMethod
    def GetCanonicalNum(self, book_or_hvo):
        """
        Get the canonical number of a Scripture book.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO

        Returns:
            int: The canonical book number (1-66)

        Raises:
            FP_NullParameterError: If book_or_hvo is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> num = project.ScrBooks.GetCanonicalNum(genesis)
            >>> print(num)
            1

            >>> matthew = project.ScrBooks.FindByName("Matthew")
            >>> print(project.ScrBooks.GetCanonicalNum(matthew))
            40

        Notes:
            - Canonical numbers: 1-39 = OT, 40-66 = NT (Protestant canon)
            - Number is immutable (set at creation)

        See Also:
            Create, Find
        """
        self._ValidateParam(book_or_hvo, "book_or_hvo")

        book = self.__ResolveObject(book_or_hvo)
        return book.CanonicalNum

    @OperationsMethod
    def GetTitle(self, book_or_hvo, wsHandle=None):
        """
        Get the title of a Scripture book.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The book title (empty string if not set)

        Raises:
            FP_NullParameterError: If book_or_hvo is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> title = project.ScrBooks.GetTitle(genesis)
            >>> print(title)
            Genesis

            >>> # Get in specific writing system
            >>> title_fr = project.ScrBooks.GetTitle(genesis,
            ...                                       project.WSHandle('fr'))

        Notes:
            - Returns empty string if title not set
            - Title can be in multiple writing systems

        See Also:
            SetTitle, FindByName
        """
        self._ValidateParam(book_or_hvo, "book_or_hvo")

        book = self.__ResolveObject(book_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        title = ITsString(book.Title.get_String(wsHandle)).Text
        return title or ""

    @OperationsMethod
    def SetTitle(self, book_or_hvo, title, wsHandle=None):
        """
        Set the title of a Scripture book.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO
            title (str): The new book title
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If book_or_hvo or title is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> project.ScrBooks.SetTitle(genesis, "Genesis")

            >>> # Set in specific writing system
            >>> project.ScrBooks.SetTitle(genesis, "Genèse",
            ...                            project.WSHandle('fr'))

        Notes:
            - Title can be set in multiple writing systems
            - Empty title is allowed

        See Also:
            GetTitle, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(book_or_hvo, "book_or_hvo")
        self._ValidateParam(title, "title")

        book = self.__ResolveObject(book_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(title, wsHandle)
        book.Title.set_String(wsHandle, mkstr)

    # --- Section Management ---

    @OperationsMethod
    def GetSections(self, book_or_hvo):
        """
        Get all sections in a Scripture book.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO

        Returns:
            list: List of IScrSection objects (empty list if none)

        Raises:
            FP_NullParameterError: If book_or_hvo is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> sections = project.ScrBooks.GetSections(genesis)
            >>> for section in sections:
            ...     heading = project.ScrSections.GetHeading(section)
            ...     print(f"Section: {heading}")

        Notes:
            - Returns empty list if book has no sections
            - Sections are in database order
            - Use ScrSectionOperations for section-level operations

        See Also:
            ScrSectionOperations.GetAll
        """
        self._ValidateParam(book_or_hvo, "book_or_hvo")

        book = self.__ResolveObject(book_or_hvo)
        return list(book.SectionsOS)

    # --- Private Helper Methods ---

    def __ResolveObject(self, book_or_hvo):
        """
        Resolve HVO or object to IScrBook.

        Args:
            book_or_hvo: Either an IScrBook object or an HVO (int)

        Returns:
            IScrBook: The resolved book object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a Scripture book
        """
        if isinstance(book_or_hvo, int):
            obj = self.project.Object(book_or_hvo)
            if not isinstance(obj, IScrBook):
                raise FP_ParameterError("HVO does not refer to a Scripture book")
            return obj
        return book_or_hvo

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to vernacular WS.

        Args:
            wsHandle: Optional writing system handle

        Returns:
            int: The writing system handle
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)

    def __GetScripture(self):
        """
        Get the Scripture object from the project.

        Returns:
            IScripture or None: The Scripture object if available
        """
        if not hasattr(self.project, "lp") or not self.project.lp:
            return None

        return self.project.lp.TranslatedScriptureOA
