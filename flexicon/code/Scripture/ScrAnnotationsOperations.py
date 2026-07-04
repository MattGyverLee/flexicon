#
#   ScrAnnotationsOperations.py
#
#   Class: ScrAnnotationsOperations
#          Scripture book annotations operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod

# Import FLEx LCM types
from SIL.LCModel import (
    IScrBook,
    IScrBookAnnotations,
    IScrBookAnnotationsFactory,
    IScrScriptureNote,
)

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ScrAnnotationsOperations(BaseOperations):
    """
    This class provides operations for managing Scripture book annotations in a
    FieldWorks project.

    Scripture book annotations are containers for notes (translator notes,
    consultant notes, etc.) associated with a Scripture book.

    This class should be accessed via FLExProject.ScrAnnotations property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a book
        genesis = project.ScrBooks.Find(1)

        # Create annotations container
        annotations = project.ScrAnnotations.Create(genesis, "note")

        # Get annotations for a book
        annotations = project.ScrAnnotations.GetForBook(genesis)

        # Get notes in annotations
        notes = project.ScrAnnotations.GetNotes(annotations)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ScrAnnotationsOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, book_or_hvo, type="note"):
        """
        Create a new Scripture book annotations container.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO
            type (str, optional): Annotation type. Defaults to "note".
                Types: "note", "translator_note", "consultant_note"

        Returns:
            IScrBookAnnotations: The newly created annotations object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If book_or_hvo is None
            FP_ParameterError: If book doesn't exist or annotations already exist

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> annotations = project.ScrAnnotations.Create(genesis)

            >>> # Create consultant notes container
            >>> annotations = project.ScrAnnotations.Create(
            ...     genesis,
            ...     "consultant_note"
            ... )

        Notes:
            - Annotations container is created per book
            - Each book can have one annotations container
            - Container holds all notes for the book
            - Type parameter is for categorization

        See Also:
            Delete, GetForBook
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(book_or_hvo, "book_or_hvo")

        # Resolve to book object
        book = self.__ResolveBook(book_or_hvo)

        # Check if annotations already exist
        if book.FootnotesOS.Count > 0:
            raise FP_ParameterError("Book already has annotations container. Use GetForBook() instead.")

        with self._TransactionCM("Create annotations"):
            # Create the new annotations using the factory
            factory = self.project.project.ServiceLocator.GetService(IScrBookAnnotationsFactory)
            new_annotations = factory.Create()

            # Add to book's footnotes (annotations are stored in FootnotesOS)
            book.FootnotesOS.Add(new_annotations)

            return new_annotations

    @OperationsMethod
    def Delete(self, annotations_or_hvo):
        """
        Delete a Scripture book annotations container from the FLEx project.

        Args:
            annotations_or_hvo: Either an IScrBookAnnotations object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If annotations_or_hvo is None
            FP_ParameterError: If annotations doesn't exist

        Example:
            >>> annotations = project.ScrAnnotations.GetForBook(genesis)
            >>> if annotations:
            ...     project.ScrAnnotations.Delete(annotations)

        Warning:
            - This is a destructive operation
            - All notes in the container will be deleted
            - Cannot be undone

        Notes:
            - Deletion cascades to all owned notes

        See Also:
            Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(annotations_or_hvo, "annotations_or_hvo")

        # Resolve to annotations object
        annotations = self.__ResolveObject(annotations_or_hvo)

        # Delete the annotations (LCM handles removal from repository)
        annotations.Delete()

    @OperationsMethod
    def GetForBook(self, book_or_hvo):
        """
        Get the annotations container for a Scripture book.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO

        Returns:
            IScrBookAnnotations or None: The annotations object if found, None otherwise

        Raises:
            FP_NullParameterError: If book_or_hvo is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> annotations = project.ScrAnnotations.GetForBook(genesis)
            >>> if annotations:
            ...     notes = project.ScrAnnotations.GetNotes(annotations)
            ...     print(f"Book has {len(notes)} notes")

        Notes:
            - Returns None if book has no annotations container
            - Each book can have one annotations container
            - Container holds all notes for the book

        See Also:
            Create, GetNotes
        """
        self._ValidateParam(book_or_hvo, "book_or_hvo")

        # Resolve to book object
        book = self.__ResolveBook(book_or_hvo)

        # Get first annotations (typically there's only one per book)
        if book.FootnotesOS.Count > 0:
            return book.FootnotesOS[0]

        return None

    # --- Annotations Properties ---

    @OperationsMethod
    def GetNotes(self, annotations_or_hvo):
        """
        Get all notes in a Scripture book annotations container.

        Args:
            annotations_or_hvo: Either an IScrBookAnnotations object or its HVO

        Returns:
            list: List of IScrScriptureNote objects (empty list if none)

        Raises:
            FP_NullParameterError: If annotations_or_hvo is None

        Example:
            >>> annotations = project.ScrAnnotations.GetForBook(genesis)
            >>> if annotations:
            ...     notes = project.ScrAnnotations.GetNotes(annotations)
            ...     for note in notes:
            ...         text = project.ScrNotes.GetText(note)
            ...         print(f"Note: {text}")

        Notes:
            - Returns empty list if container has no notes
            - Notes are in database order
            - Use ScrNoteOperations for note-level operations

        See Also:
            GetForBook, ScrNoteOperations
        """
        self._ValidateParam(annotations_or_hvo, "annotations_or_hvo")

        annotations = self.__ResolveObject(annotations_or_hvo)
        return list(annotations.NotesOS)

    # --- Private Helper Methods ---

    def __ResolveObject(self, annotations_or_hvo):
        """
        Resolve HVO or object to IScrBookAnnotations.

        Args:
            annotations_or_hvo: Either an IScrBookAnnotations object or an HVO (int)

        Returns:
            IScrBookAnnotations: The resolved annotations object

        Raises:
            FP_ParameterError: If HVO doesn't refer to Scripture annotations
        """
        if isinstance(annotations_or_hvo, int):
            obj = self.project.Object(annotations_or_hvo)
            if not isinstance(obj, IScrBookAnnotations):
                raise FP_ParameterError("HVO does not refer to Scripture annotations")
            return obj
        return annotations_or_hvo

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
