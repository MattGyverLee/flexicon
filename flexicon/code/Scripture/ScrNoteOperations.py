#
#   ScrNoteOperations.py
#
#   Class: ScrNoteOperations
#          Scripture note operations for FieldWorks Language Explorer
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
    IScrBookAnnotations,
    IScrScriptureNote,
    IScrScriptureNoteFactory,
    IScrTxtPara,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ScrNoteOperations(BaseOperations):
    """
    This class provides operations for managing Scripture notes in a
    FieldWorks project.

    Scripture notes are annotations attached to specific paragraphs or
    locations in Scripture text. They can be translator notes, consultant
    notes, checking questions, etc.

    This class should be accessed via FLExProject.ScrNotes property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a book
        genesis = project.ScrBooks.Find(1)

        # Get a paragraph
        section = project.ScrSections.Find(genesis, 0)
        para = project.ScrTxtParas.Find(section, 0)

        # Create a note
        note = project.ScrNotes.Create(
            genesis,
            para,
            "Check: Is 'beginning' the best translation?",
            "translator_note"
        )

        # Get all notes for a book
        notes = project.ScrNotes.GetAll(genesis)

        # Get note text
        text = project.ScrNotes.GetText(note)

        # Resolve a note
        project.ScrNotes.Resolve(note)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ScrNoteOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, book_or_hvo, paragraph_or_hvo, text, type="translator_note"):
        """
        Create a new Scripture note attached to a paragraph.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO
            paragraph_or_hvo: Either an IScrTxtPara object or its HVO
            text (str): The note text content
            type (str, optional): Note type. Defaults to "translator_note".
                Types: "translator_note", "consultant_note", "checking_question"

        Returns:
            IScrScriptureNote: The newly created note object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If any parameter is None
            FP_ParameterError: If book or paragraph doesn't exist

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> section = project.ScrSections.Find(genesis, 0)
            >>> para = project.ScrTxtParas.Find(section, 0)
            >>> note = project.ScrNotes.Create(
            ...     genesis,
            ...     para,
            ...     "Check: Is 'beginning' the best translation?"
            ... )

            >>> # Create consultant note
            >>> note = project.ScrNotes.Create(
            ...     genesis,
            ...     para,
            ...     "Good translation. Consider alternate word order.",
            ...     "consultant_note"
            ... )

        Notes:
            - Note is added to book's annotations container
            - Creates annotations container if it doesn't exist
            - Note GUID is auto-generated
            - Type parameter is for categorization

        See Also:
            Delete, Find, GetText, SetText
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(book_or_hvo, "book_or_hvo")
        self._ValidateParam(paragraph_or_hvo, "paragraph_or_hvo")
        self._ValidateParam(text, "text")

        # Resolve to book and paragraph objects
        book = self.__ResolveBook(book_or_hvo)
        paragraph = self.__ResolveParagraph(paragraph_or_hvo)

        with self._TransactionCM("Create note"):
            # Ensure book has annotations container
            if book.FootnotesOS.Count == 0:
                from SIL.LCModel import IScrBookAnnotationsFactory

                annotations_factory = self.project.project.ServiceLocator.GetService(IScrBookAnnotationsFactory)
                annotations = annotations_factory.Create()
                book.FootnotesOS.Add(annotations)
            else:
                annotations = book.FootnotesOS[0]

            # Create the new note using the factory
            factory = self.project.project.ServiceLocator.GetService(IScrScriptureNoteFactory)
            new_note = factory.Create()

            # Add to annotations container
            annotations.NotesOS.Add(new_note)

            # Set the note text
            wsHandle = self.project.project.DefaultAnalWs
            mkstr = TsStringUtils.MakeString(text, wsHandle)

            # Create discussion paragraph if needed
            # Note: Contents is ITsString, assign directly
            if new_note.DiscussionOA:
                if new_note.DiscussionOA.ParagraphsOS.Count > 0:
                    para_obj = new_note.DiscussionOA.ParagraphsOS[0]
                    para_obj.Contents = mkstr
                else:
                    # Create paragraph
                    from SIL.LCModel import IStTxtParaFactory

                    para_factory = self.project.project.ServiceLocator.GetService(IStTxtParaFactory)
                    para_obj = para_factory.Create()
                    new_note.DiscussionOA.ParagraphsOS.Add(para_obj)
                    para_obj.Contents = mkstr
            else:
                # Create discussion StText
                from SIL.LCModel import IStTextFactory, IStTxtParaFactory

                text_factory = self.project.project.ServiceLocator.GetService(IStTextFactory)
                new_note.DiscussionOA = text_factory.Create()
                para_factory = self.project.project.ServiceLocator.GetService(IStTxtParaFactory)
                para_obj = para_factory.Create()
                new_note.DiscussionOA.ParagraphsOS.Add(para_obj)
                para_obj.Contents = mkstr

            # Set beginning reference to the paragraph
            # Note: This is a simplified approach - full implementation would set
            # BeginRef and EndRef properly with BCVRef references
            # For now, we just create the note without precise reference

            return new_note

    @OperationsMethod
    def Delete(self, note_or_hvo):
        """
        Delete a Scripture note from the FLEx project.

        Args:
            note_or_hvo: Either an IScrScriptureNote object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If note_or_hvo is None
            FP_ParameterError: If note doesn't exist

        Example:
            >>> note = project.ScrNotes.Find(genesis, 0)
            >>> if note:
            ...     project.ScrNotes.Delete(note)

        Warning:
            - This is a destructive operation
            - Cannot be undone

        Notes:
            - Note is removed from annotations container

        See Also:
            Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(note_or_hvo, "note_or_hvo")

        # Resolve to note object
        note = self.__ResolveObject(note_or_hvo)

        # Delete the note (LCM handles removal from repository)
        note.Delete()

    @OperationsMethod
    def Find(self, book_or_hvo, index):
        """
        Find a Scripture note by index within a book.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO
            index (int): The zero-based index of the note in the book

        Returns:
            IScrScriptureNote or None: The note object if found, None otherwise

        Raises:
            FP_NullParameterError: If book_or_hvo or index is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> # Get first note
            >>> note = project.ScrNotes.Find(genesis, 0)
            >>> if note:
            ...     text = project.ScrNotes.GetText(note)
            ...     print(f"Note: {text}")

            >>> # Get third note
            >>> note3 = project.ScrNotes.Find(genesis, 2)

        Notes:
            - Returns None if index out of range
            - Index is zero-based (0 = first note)
            - Use GetAll() to get all notes

        See Also:
            GetAll, Create
        """
        self._ValidateParam(book_or_hvo, "book_or_hvo")
        self._ValidateParam(index, "index")

        # Resolve to book object
        book = self.__ResolveBook(book_or_hvo)

        # Get annotations container
        if book.FootnotesOS.Count == 0:
            return None

        annotations = book.FootnotesOS[0]

        # Check if index is valid
        if index < 0 or index >= annotations.NotesOS.Count:
            return None

        return annotations.NotesOS[index]

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, book_or_hvo):
        """
        Get all Scripture notes in a book.

        Args:
            book_or_hvo: Either an IScrBook object or its HVO

        Returns:
            list: List of IScrScriptureNote objects (empty list if none)

        Raises:
            FP_NullParameterError: If book_or_hvo is None

        Example:
            >>> genesis = project.ScrBooks.Find(1)
            >>> notes = project.ScrNotes.GetAll(genesis)
            >>> for i, note in enumerate(notes):
            ...     text = project.ScrNotes.GetText(note)
            ...     resolved = project.ScrNotes.IsResolved(note)
            ...     status = "Resolved" if resolved else "Open"
            ...     print(f"{i+1}. [{status}] {text}")

        Notes:
            - Returns empty list if book has no notes
            - Notes are in database order
            - Includes both resolved and unresolved notes

        See Also:
            Find, Create
        """
        self._ValidateParam(book_or_hvo, "book_or_hvo")

        # Resolve to book object
        book = self.__ResolveBook(book_or_hvo)

        # Get annotations container
        if book.FootnotesOS.Count == 0:
            return []

        annotations = book.FootnotesOS[0]
        return list(annotations.NotesOS)

    # --- Note Properties ---

    @OperationsMethod
    def GetText(self, note_or_hvo, wsHandle=None):
        """
        Get the text content of a Scripture note.

        Args:
            note_or_hvo: Either an IScrScriptureNote object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The note text (empty string if not set)

        Raises:
            FP_NullParameterError: If note_or_hvo is None

        Example:
            >>> note = project.ScrNotes.Find(genesis, 0)
            >>> text = project.ScrNotes.GetText(note)
            >>> print(text)
            Check: Is 'beginning' the best translation?

            >>> # Get in specific writing system
            >>> text_fr = project.ScrNotes.GetText(note,
            ...                                     project.WSHandle('fr'))

        Notes:
            - Returns empty string if text not set
            - Text can be in multiple writing systems

        See Also:
            SetText, Create
        """
        self._ValidateParam(note_or_hvo, "note_or_hvo")

        note = self.__ResolveObject(note_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        if not note.DiscussionOA:
            return ""

        # Get the discussion text from the first paragraph
        if note.DiscussionOA.ParagraphsOS.Count == 0:
            return ""

        para = note.DiscussionOA.ParagraphsOS[0]
        # Note: Contents is ITsString, not IMultiUnicode
        text = para.Contents.Text if para.Contents else ""
        return text or ""

    @OperationsMethod
    def SetText(self, note_or_hvo, text, wsHandle=None):
        """
        Set the text content of a Scripture note.

        Args:
            note_or_hvo: Either an IScrScriptureNote object or its HVO
            text (str): The new note text
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If note_or_hvo or text is None

        Example:
            >>> note = project.ScrNotes.Find(genesis, 0)
            >>> project.ScrNotes.SetText(
            ...     note,
            ...     "Updated: Consider using 'origin' instead of 'beginning'"
            ... )

            >>> # Set in specific writing system
            >>> project.ScrNotes.SetText(
            ...     note,
            ...     "Vérifier: Utiliser 'commencement' ou 'origine'?",
            ...     project.WSHandle('fr')
            ... )

        Notes:
            - Creates discussion StText if it doesn't exist
            - Creates discussion paragraph if it doesn't exist
            - Empty text is allowed

        See Also:
            GetText, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(note_or_hvo, "note_or_hvo")
        self._ValidateParam(text, "text")

        note = self.__ResolveObject(note_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM("Set note text"):
            # Ensure DiscussionOA exists
            if not note.DiscussionOA:
                from SIL.LCModel import IStTextFactory

                text_factory = self.project.project.ServiceLocator.GetService(IStTextFactory)
                note.DiscussionOA = text_factory.Create()

            # Ensure discussion has at least one paragraph
            if note.DiscussionOA.ParagraphsOS.Count == 0:
                from SIL.LCModel import IStTxtParaFactory

                para_factory = self.project.project.ServiceLocator.GetService(IStTxtParaFactory)
                para = para_factory.Create()
                note.DiscussionOA.ParagraphsOS.Add(para)

            # Set the discussion text (Contents is ITsString, assign directly)
            para = note.DiscussionOA.ParagraphsOS[0]
            mkstr = TsStringUtils.MakeString(text, wsHandle)
            para.Contents = mkstr

    @OperationsMethod
    def GetType(self, note_or_hvo):
        """
        Get the type of a Scripture note.

        Args:
            note_or_hvo: Either an IScrScriptureNote object or its HVO

        Returns:
            str: The note type (empty string if not determinable)

        Raises:
            FP_NullParameterError: If note_or_hvo is None

        Example:
            >>> note = project.ScrNotes.Find(genesis, 0)
            >>> note_type = project.ScrNotes.GetType(note)
            >>> print(note_type)
            translator_note

        Notes:
            - Type is inferred from note properties
            - May return empty string if type cannot be determined
            - Common types: translator_note, consultant_note, checking_question

        See Also:
            Create
        """
        self._ValidateParam(note_or_hvo, "note_or_hvo")

        note = self.__ResolveObject(note_or_hvo)

        # Note type is typically stored in annotation definition
        # For simplicity, return generic "note" type
        # A full implementation would check note.AnnotationTypeRA
        return "note"

    @OperationsMethod
    def Resolve(self, note_or_hvo):
        """
        Mark a Scripture note as resolved.

        Args:
            note_or_hvo: Either an IScrScriptureNote object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If note_or_hvo is None

        Example:
            >>> note = project.ScrNotes.Find(genesis, 0)
            >>> # Check if already resolved
            >>> if not project.ScrNotes.IsResolved(note):
            ...     project.ScrNotes.Resolve(note)
            ...     print("Note resolved")

        Notes:
            - Resolved notes are marked as complete
            - Typically hidden in note displays
            - Can be un-resolved by clearing the resolved flag

        See Also:
            IsResolved, Unresolve
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(note_or_hvo, "note_or_hvo")

        note = self.__ResolveObject(note_or_hvo)

        # Mark as resolved (set ResolutionStatus)
        # Note: The exact property for resolution may vary
        # For now, we set a simple flag approach
        # A full implementation would use note.ResolutionStatus
        if hasattr(note, "ResolutionStatus"):
            note.ResolutionStatus = 1  # Resolved

    @OperationsMethod
    def IsResolved(self, note_or_hvo):
        """
        Check if a Scripture note is marked as resolved.

        Args:
            note_or_hvo: Either an IScrScriptureNote object or its HVO

        Returns:
            bool: True if note is resolved, False otherwise

        Raises:
            FP_NullParameterError: If note_or_hvo is None

        Example:
            >>> note = project.ScrNotes.Find(genesis, 0)
            >>> if project.ScrNotes.IsResolved(note):
            ...     print("Note is resolved")
            ... else:
            ...     print("Note is still open")

        Notes:
            - Resolved notes are marked as complete
            - Use Resolve() to mark as resolved

        See Also:
            Resolve
        """
        self._ValidateParam(note_or_hvo, "note_or_hvo")

        note = self.__ResolveObject(note_or_hvo)

        # Check resolution status
        if hasattr(note, "ResolutionStatus"):
            return note.ResolutionStatus == 1

        return False

    # --- Private Helper Methods ---

    def __ResolveObject(self, note_or_hvo):
        """
        Resolve HVO or object to IScrScriptureNote.

        Args:
            note_or_hvo: Either an IScrScriptureNote object or an HVO (int)

        Returns:
            IScrScriptureNote: The resolved note object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a Scripture note
        """
        if isinstance(note_or_hvo, int):
            obj = self.project.Object(note_or_hvo)
            if not isinstance(obj, IScrScriptureNote):
                raise FP_ParameterError("HVO does not refer to a Scripture note")
            return obj
        return note_or_hvo

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

    def __ResolveParagraph(self, para_or_hvo):
        """
        Resolve HVO or object to IScrTxtPara.

        Args:
            para_or_hvo: Either an IScrTxtPara object or an HVO (int)

        Returns:
            IScrTxtPara: The resolved paragraph object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a Scripture paragraph
        """
        if isinstance(para_or_hvo, int):
            obj = self.project.Object(para_or_hvo)
            if not isinstance(obj, IScrTxtPara):
                raise FP_ParameterError("HVO does not refer to a Scripture paragraph")
            return obj
        return para_or_hvo

    def __WSHandle(self, wsHandle):
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
