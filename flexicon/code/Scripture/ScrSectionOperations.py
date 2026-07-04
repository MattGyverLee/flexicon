#
#   ScrSectionOperations.py
#
#   Class: ScrSectionOperations
#          Scripture section operations for FieldWorks Language Explorer
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
    IScrSection,
    IScrSectionFactory,
    IScrTxtPara,
    IStText,
    IStTextFactory,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ScrSectionOperations(BaseOperations):
    """
    This class provides operations for managing Scripture sections in a
    FieldWorks project.

    Scripture sections are subdivisions of books, each with a heading and
    content paragraphs. Sections organize Scripture text into logical units.

    This class should be accessed via FLExProject.ScrSections property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a book
        genesis = project.ScrBooks.Find(1)

        # Create a section
        section = project.ScrSections.Create(genesis, "Creation", "In the beginning...")

        # Get all sections in a book
        sections = project.ScrSections.GetAll(genesis)

        # Get section heading and content
        heading = project.ScrSections.GetHeading(section)
        paras = project.ScrSections.GetContent(section)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ScrSectionOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, book_or_hvo, heading="", content=""):
        """
        Create a new Scripture section with heading and/or content.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO
            heading (str, optional): Section heading text
            content (str, optional): Initial paragraph content text

        Returns:
            IScrSection: The newly created section object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If book_or_hvo is None
            FP_ParameterError: If book doesn't exist

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> section = project.ScrSections.Create(
            ...     genesis,
            ...     "The Creation",
            ...     "In the beginning God created the heavens and the earth."
            ... )

            >>> # Create section with heading only
            >>> section2 = project.ScrSections.Create(genesis, "The Fall")

            >>> # Create empty section
            >>> section3 = project.ScrSections.Create(genesis)

        Notes:
            - Section is appended to the book's sections
            - Section GUID is auto-generated
            - Heading and content can be empty strings
            - Content creates a single paragraph if provided

        See Also:
            Delete, Find, GetHeading, SetHeading
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(book_or_hvo, "book_or_hvo")

        # Resolve to book object
        book = self.__ResolveBook(book_or_hvo)

        # Create the new section using the factory
        factory = self.project.project.ServiceLocator.GetService(IScrSectionFactory)
        new_section = factory.CreateScrSection(
            book,
            book.SectionsOS.Count,  # Append to end
            heading or "",
            content or "",
            True,  # Is intro section = False (main content)
        )

        return new_section

    @OperationsMethod
    def Delete(self, section_or_hvo):
        """
        Delete a Scripture section from the FLEx project.

        Args:
            section_or_hvo: Either an IScrSection object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If section_or_hvo is None
            FP_ParameterError: If section doesn't exist

        Example:
            >>> section = project.ScrSections.Find(genesis, 0)
            >>> if section:
            ...     project.ScrSections.Delete(section)

        Warning:
            - This is a destructive operation
            - All paragraphs and content will be deleted
            - Cannot be undone

        Notes:
            - Deletion cascades to all owned objects (paragraphs, etc.)

        See Also:
            Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(section_or_hvo, "section_or_hvo")

        # Resolve to section object
        section = self.__ResolveObject(section_or_hvo)

        # Delete the section (LCM handles removal from repository)
        section.Delete()

    @OperationsMethod
    def Find(self, book_or_hvo, index):
        """
        Find a Scripture section by index within a book.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO
            index (int): The zero-based index of the section in the book

        Returns:
            IScrSection or None: The section object if found, None otherwise

        Raises:
            FP_NullParameterError: If book_or_hvo or index is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> # Get first section
            >>> section = project.ScrSections.Find(genesis, 0)
            >>> if section:
            ...     heading = project.ScrSections.GetHeading(section)
            ...     print(f"Section: {heading}")

            >>> # Get third section
            >>> section3 = project.ScrSections.Find(genesis, 2)

        Notes:
            - Returns None if index out of range
            - Index is zero-based (0 = first section)
            - Use GetAll() to get all sections

        See Also:
            GetAll, Create
        """
        self._ValidateParam(book_or_hvo, "book_or_hvo")
        self._ValidateParam(index, "index")

        # Resolve to book object
        book = self.__ResolveBook(book_or_hvo)

        # Check if index is valid
        if index < 0 or index >= book.SectionsOS.Count:
            return None

        return book.SectionsOS[index]

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, book_or_hvo):
        """
        Get all Scripture sections in a book.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO

        Returns:
            list: List of IScrSection objects (empty list if none)

        Raises:
            FP_NullParameterError: If book_or_hvo is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> sections = project.ScrSections.GetAll(genesis)
            >>> for i, section in enumerate(sections):
            ...     heading = project.ScrSections.GetHeading(section)
            ...     print(f"{i+1}. {heading}")
            1. The Creation
            2. The Fall
            3. Cain and Abel

        Notes:
            - Returns empty list if book has no sections
            - Sections are in database order
            - Same as project.ScrBooks.GetSections(book)

        See Also:
            Find, Create
        """
        self._ValidateParam(book_or_hvo, "book_or_hvo")

        # Resolve to book object
        book = self.__ResolveBook(book_or_hvo)

        return list(book.SectionsOS)

    # --- Section Properties ---

    @OperationsMethod
    def GetHeading(self, section_or_hvo, wsHandle=None):
        """
        Get the heading of a Scripture section.

        Args:
            section_or_hvo: Either an IScrSection object or its HVO
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The section heading (empty string if not set)

        Raises:
            FP_NullParameterError: If section_or_hvo is None

        Example:
            >>> section = project.ScrSections.Find(genesis, 0)
            >>> heading = project.ScrSections.GetHeading(section)
            >>> print(heading)
            The Creation

            >>> # Get in specific writing system
            >>> heading_fr = project.ScrSections.GetHeading(section,
            ...                                              project.WSHandle('fr'))

        Notes:
            - Returns empty string if heading not set
            - Heading can be in multiple writing systems

        See Also:
            SetHeading, Create
        """
        self._ValidateParam(section_or_hvo, "section_or_hvo")

        section = self.__ResolveObject(section_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        if not section.HeadingOA:
            return ""

        # Get the heading text from the first paragraph
        if section.HeadingOA.ParagraphsOS.Count == 0:
            return ""

        para = section.HeadingOA.ParagraphsOS[0]
        # Note: Contents is ITsString, not IMultiUnicode
        text = para.Contents.Text if para.Contents else ""
        return text or ""

    @OperationsMethod
    def SetHeading(self, section_or_hvo, text, wsHandle=None):
        """
        Set the heading of a Scripture section.

        Args:
            section_or_hvo: Either an IScrSection object or its HVO
            text (str): The new heading text
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If section_or_hvo or text is None

        Example:
            >>> section = project.ScrSections.Find(genesis, 0)
            >>> project.ScrSections.SetHeading(section, "The Creation Story")

            >>> # Set in specific writing system
            >>> project.ScrSections.SetHeading(section, "La Création",
            ...                                 project.WSHandle('fr'))

        Notes:
            - Creates heading StText if it doesn't exist
            - Creates heading paragraph if it doesn't exist
            - Empty text is allowed

        See Also:
            GetHeading, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(section_or_hvo, "section_or_hvo")
        self._ValidateParam(text, "text")

        section = self.__ResolveObject(section_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM("Set section heading"):
            # Ensure HeadingOA exists
            if not section.HeadingOA:
                text_factory = self.project.project.ServiceLocator.GetService(IStTextFactory)
                section.HeadingOA = text_factory.Create()

            # Ensure heading has at least one paragraph
            if section.HeadingOA.ParagraphsOS.Count == 0:
                from SIL.LCModel import IStTxtParaFactory

                para_factory = self.project.project.ServiceLocator.GetService(IStTxtParaFactory)
                para = para_factory.Create()
                section.HeadingOA.ParagraphsOS.Add(para)

            # Set the heading text (Contents is ITsString, assign directly)
            para = section.HeadingOA.ParagraphsOS[0]
            mkstr = TsStringUtils.MakeString(text, wsHandle)
            para.Contents = mkstr

    @OperationsMethod
    def GetContent(self, section_or_hvo):
        """
        Get all content paragraphs in a Scripture section.

        Args:
            section_or_hvo: Either an IScrSection object or its HVO

        Returns:
            list: List of IScrTxtPara objects (empty list if none)

        Raises:
            FP_NullParameterError: If section_or_hvo is None

        Example:
            >>> section = project.ScrSections.Find(genesis, 0)
            >>> paras = project.ScrSections.GetContent(section)
            >>> for para in paras:
            ...     text = project.ScrTxtParas.GetText(para)
            ...     print(f"Paragraph: {text}")

        Notes:
            - Returns empty list if section has no content
            - Paragraphs are in database order
            - Use ScrTxtParaOperations for paragraph-level operations

        See Also:
            ScrTxtParaOperations.GetAll
        """
        self._ValidateParam(section_or_hvo, "section_or_hvo")

        section = self.__ResolveObject(section_or_hvo)

        if not section.ContentOA:
            return []

        return list(section.ContentOA.ParagraphsOS)

    @OperationsMethod
    def MoveTo(self, section_or_hvo, target_book_or_hvo, index):
        """
        Move a section to a different position or book.

        Args:
            section_or_hvo: Either an IScrSection object or its HVO
            target_book_or_hvo: Either an IScrBook object or its HVO (destination)
            index (int): The zero-based index position in the target book

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If any parameter is None
            FP_ParameterError: If index is out of range

        Example:
            >>> section = project.ScrSections.Find(genesis, 2)
            >>> # Move to first position in same book
            >>> project.ScrSections.MoveTo(section, genesis, 0)

            >>> # Move to different book
            >>> exodus = project.ScrBooks.Find(2)
            >>> project.ScrSections.MoveTo(section, exodus, 0)

        Notes:
            - Can move within same book or to different book
            - Index is zero-based
            - Other sections shift position automatically

        See Also:
            Create, Delete
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(section_or_hvo, "section_or_hvo")
        self._ValidateParam(target_book_or_hvo, "target_book_or_hvo")
        self._ValidateParam(index, "index")

        section = self.__ResolveObject(section_or_hvo)
        target_book = self.__ResolveBook(target_book_or_hvo)

        if index < 0 or index > target_book.SectionsOS.Count:
            raise FP_ParameterError(f"Index {index} out of range (0-{target_book.SectionsOS.Count})")

        # Get current owner
        current_book = section.Owner

        # If moving within same book, adjust for removal
        if current_book == target_book:
            current_index = target_book.SectionsOS.IndexOf(section)
            if current_index < index:
                index -= 1

        with self._TransactionCM("Move section"):
            # Remove from current location
            if current_book:
                current_book.SectionsOS.Remove(section)

            # Insert at new location
            target_book.SectionsOS.Insert(index, section)

    # --- Private Helper Methods ---

    def __ResolveObject(self, section_or_hvo):
        """
        Resolve HVO or object to IScrSection.

        Args:
            section_or_hvo: Either an IScrSection object or an HVO (int)

        Returns:
            IScrSection: The resolved section object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a Scripture section
        """
        if isinstance(section_or_hvo, int):
            obj = self.project.Object(section_or_hvo)
            if not isinstance(obj, IScrSection):
                raise FP_ParameterError("HVO does not refer to a Scripture section")
            return obj
        return section_or_hvo

    def __ResolveBook(self, book_or_hvo):
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
