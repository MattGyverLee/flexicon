#
#   NoteOperations.py
#
#   Class: NoteOperations
#          Note and comment operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import FLEx LCM types
from SIL.LCModel import (
    IScrScriptureNote,
    IScrScriptureNoteFactory,
    ICmBaseAnnotation,
    ICmBaseAnnotationFactory,
    ICmAnnotationDefn,
    ICmPossibility,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils
from System import DateTime

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable


class NoteOperations(BaseOperations):
    """
    This class provides operations for managing notes and comments in a
    FieldWorks project.

    Notes in FLEx are annotations that can be attached to various objects
    including lexical entries, senses, texts, paragraphs, and more. Notes
    support threading (replies), categorization, metadata tracking, and
    multi-lingual content.

    This class should be accessed via FLExProject.Note property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a lexical entry
        entry = project.LexEntry.Find("run")

        # Get all notes for the entry
        for note in project.Note.GetAll(entry):
            content = project.Note.GetContent(note)
            date = project.Note.GetDateCreated(note)
            print(f"Note: {content} (created {date})")

        # Create a new note
        note = project.Note.Create(entry, "Review etymology", "en")

        # Set note type
        project.Note.SetNoteType(note, "To Do")

        # Add a reply
        reply = project.Note.AddReply(note, "Checked - looks correct", "en")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize NoteOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, owner_object):
        """
        Get all notes attached to an object.

        Args:
            owner_object: The object whose notes to retrieve. Can be an
                ILexEntry, ILexSense, IText, IStPara, or any annotatable object.

        Yields:
            ICmBaseAnnotation: Each note/annotation attached to the object.

        Raises:
            FP_NullParameterError: If owner_object is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> for note in project.Note.GetAll(entry):
            ...     content = project.Note.GetContent(note)
            ...     print(f"Note: {content}")
            Note: Check etymology source
            Note: Add example sentences

        Notes:
            - Returns notes in creation order
            - Returns empty generator if object has no notes
            - Works with any object that supports annotations
            - Includes both top-level notes and replies

        See Also:
            Create, Delete, GetReplies
        """
        self._ValidateParam(owner_object, "owner_object")

        # Get the annotation repository
        anno_repos = self.project.project.ServiceLocator.GetService(ICmBaseAnnotation).Repository

        # Find all annotations for this object
        for annotation in anno_repos.AllInstances():
            # Check if this annotation references our owner object
            if hasattr(annotation, "BeginObjectRA"):
                if annotation.BeginObjectRA == owner_object:
                    yield annotation
            # Also check for direct ownership. .Owner is on every
            # ICmObject; no hasattr guard needed. (issue #133 sweep)
            if annotation.Owner == owner_object:
                yield annotation

    @OperationsMethod
    def Create(self, owner_object, content, wsHandle=None):
        """
        Create a new note attached to an object.

        Args:
            owner_object: The object to attach the note to (entry, sense, etc.).
            content (str): The text content of the note.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmBaseAnnotation: The newly created note object.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If owner_object or content is None.
            FP_ParameterError: If content is empty.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> note = project.Note.Create(entry, "Check etymology", "en")
            >>> print(project.Note.GetContent(note))
            Check etymology

            >>> # Create with specific writing system
            >>> sense = entry.SensesOS[0]
            >>> note = project.Note.Create(sense, "À vérifier",
            ...                             project.WSHandle('fr'))

        Notes:
            - Note is immediately added to the database
            - DateCreated is set automatically to current time
            - Use SetNoteType() to assign a category
            - Use AddReply() to create threaded discussions
            - GUID is auto-generated

        See Also:
            Delete, SetContent, SetNoteType, AddReply
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(owner_object, "owner_object")
        self._ValidateParam(content, "content")

        if not content or not content.strip():
            raise FP_ParameterError("Note content cannot be empty")

        wsHandle = self.__WSHandle(wsHandle)

        # Create the annotation using the factory
        with self._TransactionCM("Create note"):
            factory = self.project.project.ServiceLocator.GetService(ICmBaseAnnotationFactory)
            note = factory.Create()

            # Add to the annotations collection (must be done before setting properties)
            if hasattr(owner_object, "AnnotationsOC"):
                owner_object.AnnotationsOC.Add(note)

            # Set the content
            mkstr = TsStringUtils.MakeString(content, wsHandle)
            note.Comment.set_String(wsHandle, mkstr)

            # Set the reference to the annotated object
            if hasattr(note, "BeginObjectRA"):
                note.BeginObjectRA = owner_object

            # Set creation date
            note.DateCreated = DateTime.Now

            return note

    @OperationsMethod
    def Delete(self, note):
        """
        Delete a note.

        Args:
            note: The ICmBaseAnnotation (note) object to delete.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If note is None.

        Example:
            >>> entry = project.LexEntry.Find("obsolete")
            >>> notes = list(project.Note.GetAll(entry))
            >>> if notes:
            ...     project.Note.Delete(notes[0])

        Warning:
            - This is a destructive operation
            - All replies to the note will also be deleted
            - Cannot be undone

        Notes:
            - Deletion cascades to all replies
            - Owner references are automatically cleaned up
            - Consider archiving important notes before deletion

        See Also:
            Create, GetReplies
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(note, "note")

        # Remove from owner's collection. note.Owner is typed as
        # ICmObject and does not expose AnnotationsOC / RepliesOS; cast
        # to the concrete owner so the typed collection is reachable
        # (the previous hasattr check silently no-opped for notes owned
        # by IRnGenericRec or by a parent note).
        with self._TransactionCM("Delete note"):
            owner = self._GetTypedOwner(note)
            if owner is not None:
                if hasattr(owner, "AnnotationsOC") and note in owner.AnnotationsOC:
                    owner.AnnotationsOC.Remove(note)
                elif hasattr(owner, "RepliesOS") and note in owner.RepliesOS:
                    owner.RepliesOS.Remove(note)

            # Delete the note object
            if hasattr(note, "Delete"):
                note.Delete()

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=True):
        """
        Duplicate a note, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The ICmBaseAnnotation (note) object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source note.
                                If False, insert at end of owner's annotation list.
            deep (bool): If True (default), also duplicate owned objects (replies).
                        If False, only copy simple properties and references.

        Returns:
            ICmBaseAnnotation: The newly created duplicate note with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> notes = list(project.Note.GetAll(entry))
            >>> if notes:
            ...     # Shallow duplicate (no replies)
            ...     dup = project.Note.Duplicate(notes[0])
            ...     print(f"Original: {project.Note.GetGuid(notes[0])}")
            ...     print(f"Duplicate: {project.Note.GetGuid(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321
            ...
            ...     # Deep duplicate (includes all replies)
            ...     deep_dup = project.Note.Duplicate(notes[0], deep=True)
            ...     print(f"Replies: {len(list(project.Note.GetReplies(deep_dup)))}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original note's position
            - Simple properties copied: Comment, Source (author), DateCreated, DateModified
            - Reference properties copied: AnnotationTypeRA, BeginObjectRA
            - Owned objects (deep=True): RepliesOS (threaded discussion)
            - DateCreated and DateModified are copied from source, not set to current time

        See Also:
            Create, Delete, GetGuid, GetReplies
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source note and parent. source.Owner is typed as ICmObject
        # and does not expose AnnotationsOC / RepliesOS; cast to the
        # concrete owner so the typed collection is reachable (the
        # previous hasattr checks silently no-opped, leaving the
        # duplicate orphaned).
        source = item_or_hvo if not isinstance(item_or_hvo, int) else self.project.Object(item_or_hvo)
        parent = self._GetTypedOwner(source)
        if parent is None:
            raise FP_ParameterError("Note has no owning record or parent note")

        # Create new note using factory (auto-generates new GUID)
        with self._TransactionCM("Duplicate note"):
            factory = self.project.project.ServiceLocator.GetService(ICmBaseAnnotationFactory)
            duplicate = factory.Create()

            # Determine insertion position
            # Notes can be in AnnotationsOC (when parent is owner object) or RepliesOS (when parent is another note)
            if insert_after:
                # Insert after source note
                if hasattr(parent, "RepliesOS"):
                    source_index = parent.RepliesOS.IndexOf(source)
                    parent.RepliesOS.Insert(source_index + 1, duplicate)
                elif hasattr(parent, "AnnotationsOC"):
                    # AnnotationsOC is unordered (OC); insert_after is a no-op, add at end
                    parent.AnnotationsOC.Add(duplicate)
            else:
                # Insert at end
                if hasattr(parent, "RepliesOS"):
                    parent.RepliesOS.Add(duplicate)
                elif hasattr(parent, "AnnotationsOC"):
                    parent.AnnotationsOC.Add(duplicate)

            # Copy simple MultiString properties
            duplicate.Comment.CopyAlternatives(source.Comment)
            duplicate.Source.CopyAlternatives(source.Source)

            # Copy Reference Atomic (RA) properties
            if hasattr(source, "AnnotationTypeRA"):
                duplicate.AnnotationTypeRA = source.AnnotationTypeRA
            if hasattr(source, "BeginObjectRA"):
                duplicate.BeginObjectRA = source.BeginObjectRA

            # Copy datetime properties
            if hasattr(source, "DateCreated"):
                duplicate.DateCreated = source.DateCreated
            if hasattr(source, "DateModified"):
                duplicate.DateModified = source.DateModified

            # Handle owned objects if deep=True
            if deep:
                # Duplicate replies into the NEW duplicate (not the original's parent)
                if hasattr(source, "RepliesOS"):
                    for reply in source.RepliesOS:
                        self._DuplicateReplyInto(reply, duplicate, deep=True)

            return duplicate

    def _DuplicateReplyInto(self, source_reply, parent_note, deep=True):
        """Duplicate a reply note into the specified parent note's RepliesOS."""
        factory = self.project.project.ServiceLocator.GetService(ICmBaseAnnotationFactory)
        dup_reply = factory.Create()
        parent_note.RepliesOS.Add(dup_reply)

        # Copy properties
        dup_reply.Comment.CopyAlternatives(source_reply.Comment)
        dup_reply.Source.CopyAlternatives(source_reply.Source)
        if hasattr(source_reply, "AnnotationTypeRA"):
            dup_reply.AnnotationTypeRA = source_reply.AnnotationTypeRA
        if hasattr(source_reply, "BeginObjectRA"):
            dup_reply.BeginObjectRA = source_reply.BeginObjectRA

        # Recurse into nested replies
        if deep and hasattr(source_reply, "RepliesOS"):
            for nested_reply in source_reply.RepliesOS:
                self._DuplicateReplyInto(nested_reply, dup_reply, deep=True)

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get syncable properties for cross-project synchronization.

        Returns all syncable properties of a note including MultiString fields
        and reference properties.

        Args:
            item: The ICmBaseAnnotation (note) object

        Returns:
            dict: Dictionary of syncable properties

        Example:
            >>> props = project.Note.GetSyncableProperties(note)
            >>> print(props)
            {'Comment': 'Check this', 'Source': 'John', 'AnnotationType': '...'}
        """
        self._ValidateParam(item, "item")

        note = item
        wsHandle = self.__WSHandle(None)

        props = {}

        # MultiString properties
        if hasattr(note, "Comment"):
            props["Comment"] = ITsString(note.Comment.get_String(wsHandle)).Text or ""
        if hasattr(note, "Source"):
            props["Source"] = ITsString(note.Source.get_String(wsHandle)).Text or ""

        # Reference Atomic (RA) property - return GUID as string
        if hasattr(note, "AnnotationTypeRA") and note.AnnotationTypeRA:
            props["AnnotationType"] = str(note.AnnotationTypeRA.Guid)
        else:
            props["AnnotationType"] = None

        if hasattr(note, "BeginObjectRA") and note.BeginObjectRA:
            props["BeginObject"] = str(note.BeginObjectRA.Guid)
        else:
            props["BeginObject"] = None

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two notes and return detailed differences.

        Args:
            item1: First note (from source project)
            item2: Second note (from target project)
            ops1: Operations instance for item1's project (defaults to self)
            ops2: Operations instance for item2's project (defaults to self)

        Returns:
            tuple: (is_different, differences_dict) where differences_dict contains
                   'properties' dict with changed property details

        Example:
            >>> is_diff, diffs = ops1.CompareTo(note1, note2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, details in diffs['properties'].items():
            ...         print(f"{prop}: {details['source']} -> {details['target']}")
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        is_different = False
        differences = {"properties": {}}

        # Get syncable properties from both items
        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        # Compare each property
        for key in set(props1.keys()) | set(props2.keys()):
            val1 = props1.get(key)
            val2 = props2.get(key)

            if val1 != val2:
                is_different = True
                differences["properties"][key] = {"source": val1, "target": val2, "type": "modified"}

        return is_different, differences

    # --- Content Operations ---

    @OperationsMethod
    def GetContent(self, note, wsHandle=None):
        """
        Get the text content of a note.

        Args:
            note: The ICmBaseAnnotation (note) object.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The note content, or empty string if not set.

        Raises:
            FP_NullParameterError: If note is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> notes = list(project.Note.GetAll(entry))
            >>> if notes:
            ...     content = project.Note.GetContent(notes[0])
            ...     print(content)
            Check etymology source

            >>> # Get in specific writing system
            >>> content_fr = project.Note.GetContent(notes[0],
            ...                                       project.WSHandle('fr'))

        Notes:
            - Returns empty string if content not set in specified WS
            - Notes can have content in multiple writing systems
            - Analysis writing system is typically used for notes

        See Also:
            SetContent, Create
        """
        self._ValidateParam(note, "note")

        wsHandle = self.__WSHandle(wsHandle)

        if hasattr(note, "Comment"):
            text = ITsString(note.Comment.get_String(wsHandle)).Text
            return text or ""
        return ""

    @OperationsMethod
    def SetContent(self, note, text, wsHandle=None):
        """
        Set the text content of a note.

        Args:
            note: The ICmBaseAnnotation (note) object.
            text (str): The new note content.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If note or text is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> notes = list(project.Note.GetAll(entry))
            >>> if notes:
            ...     project.Note.SetContent(notes[0], "Etymology verified")
            ...     print(project.Note.GetContent(notes[0]))
            Etymology verified

        Notes:
            - Empty string is allowed (clears the content)
            - DateModified is updated automatically
            - Use different writing systems for multilingual notes

        See Also:
            GetContent, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(note, "note")
        self._ValidateParam(text, "text")

        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM("Set note content"):
            if hasattr(note, "Comment"):
                mkstr = TsStringUtils.MakeString(text, wsHandle)
                note.Comment.set_String(wsHandle, mkstr)

                # Update modification date
                note.DateModified = DateTime.Now

    # --- Note Type Operations ---

    @OperationsMethod
    def GetNoteType(self, note):
        """
        Get the note type/category.

        Args:
            note: The ICmBaseAnnotation (note) object.

        Returns:
            ICmAnnotationDefn: The annotation definition (note type), or None.

        Raises:
            FP_NullParameterError: If note is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> notes = list(project.Note.GetAll(entry))
            >>> if notes:
            ...     note_type = project.Note.GetNoteType(notes[0])
            ...     if note_type:
            ...         # Get the name of the note type
            ...         ws = project.project.DefaultAnalWs
            ...         type_name = ITsString(note_type.Name.get_String(ws)).Text
            ...         print(f"Note type: {type_name}")
            Note type: To Do

        Notes:
            - Returns None if no note type is set
            - Note types are defined in the annotation definitions
            - Common types: "To Do", "Question", "Resolved", etc.

        See Also:
            SetNoteType
        """
        self._ValidateParam(note, "note")

        if hasattr(note, "AnnotationTypeRA"):
            return note.AnnotationTypeRA
        return None

    @OperationsMethod
    def SetNoteType(self, note, note_type):
        """
        Set the note type/category.

        Args:
            note: The ICmBaseAnnotation (note) object.
            note_type: Either a string name or ICmAnnotationDefn object.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If note is None.
            FP_ParameterError: If note_type string not found.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> note = project.Note.Create(entry, "Check this later")
            >>> project.Note.SetNoteType(note, "To Do")

            >>> # Using annotation definition object
            >>> anno_defn = project.Note.GetNoteType(existing_note)
            >>> if anno_defn:
            ...     project.Note.SetNoteType(new_note, anno_defn)

        Notes:
            - If string is provided, searches for matching annotation definition
            - Search is case-sensitive
            - Common types: "To Do", "Question", "Resolved"
            - Note type affects display and filtering in FLEx

        See Also:
            GetNoteType
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(note, "note")

        if not hasattr(note, "AnnotationTypeRA"):
            raise FP_ParameterError("Note does not support type assignment")

        # If string, find the annotation definition
        if isinstance(note_type, str):
            anno_defn = self.__FindAnnotationDefn(note_type)
            if not anno_defn:
                raise FP_ParameterError(f"Note type '{note_type}' not found")
            note_type = anno_defn

        note.AnnotationTypeRA = note_type

    # --- Metadata Operations ---

    @OperationsMethod
    def GetDateCreated(self, note):
        """
        Get the creation date of a note.

        Args:
            note: The ICmBaseAnnotation (note) object.

        Returns:
            System.DateTime: The creation date/time, or None if not set.

        Raises:
            FP_NullParameterError: If note is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> notes = list(project.Note.GetAll(entry))
            >>> if notes:
            ...     date = project.Note.GetDateCreated(notes[0])
            ...     print(f"Created: {date}")
            Created: 11/23/2025 10:30:45 AM

            >>> # Sort notes by creation date
            >>> sorted_notes = sorted(notes,
            ...     key=lambda n: project.Note.GetDateCreated(n) or DateTime.MinValue)

        Notes:
            - DateCreated is set automatically when note is created
            - Returns System.DateTime object
            - Can be None for notes without creation date
            - Use for sorting and filtering notes by age

        See Also:
            GetDateModified, Create
        """
        self._ValidateParam(note, "note")

        if hasattr(note, "DateCreated"):
            return note.DateCreated
        return None

    @OperationsMethod
    def GetDateModified(self, note):
        """
        Get the last modification date of a note.

        Args:
            note: The ICmBaseAnnotation (note) object.

        Returns:
            System.DateTime: The modification date/time, or None if not set.

        Raises:
            FP_NullParameterError: If note is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> notes = list(project.Note.GetAll(entry))
            >>> if notes:
            ...     modified = project.Note.GetDateModified(notes[0])
            ...     if modified:
            ...         print(f"Last modified: {modified}")
            Last modified: 11/23/2025 2:15:30 PM

            >>> # Find recently modified notes
            >>> from System import DateTime
            >>> one_week_ago = DateTime.Now.AddDays(-7)
            >>> recent = [n for n in notes
            ...     if project.Note.GetDateModified(n) and
            ...        project.Note.GetDateModified(n) > one_week_ago]

        Notes:
            - DateModified is updated when content or properties change
            - Returns System.DateTime object
            - May be None if note has never been modified
            - Useful for tracking note activity

        See Also:
            GetDateCreated, SetContent
        """
        self._ValidateParam(note, "note")

        if hasattr(note, "DateModified"):
            return note.DateModified
        return None

    @OperationsMethod
    def GetAuthor(self, note):
        """
        Get the author of a note.

        Args:
            note: The ICmBaseAnnotation (note) object.

        Returns:
            str: The author name, or empty string if not set.

        Raises:
            FP_NullParameterError: If note is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> notes = list(project.Note.GetAll(entry))
            >>> if notes:
            ...     author = project.Note.GetAuthor(notes[0])
            ...     if author:
            ...         print(f"Author: {author}")
            Author: John Smith

            >>> # Filter notes by author
            >>> john_notes = [n for n in notes
            ...     if project.Note.GetAuthor(n) == "John Smith"]

        Notes:
            - Returns empty string if author not set
            - Author is typically set from user preferences
            - Use for filtering and attribution

        See Also:
            SetAuthor
        """
        self._ValidateParam(note, "note")

        if hasattr(note, "Source"):
            ws = self.project.project.DefaultAnalWs
            text = ITsString(note.Source.get_String(ws)).Text
            return text or ""
        return ""

    @OperationsMethod
    def SetAuthor(self, note, author_name):
        """
        Set the author of a note.

        Args:
            note: The ICmBaseAnnotation (note) object.
            author_name (str): The author name to set.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If note or author_name is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> note = project.Note.Create(entry, "Review needed")
            >>> project.Note.SetAuthor(note, "John Smith")
            >>> print(project.Note.GetAuthor(note))
            John Smith

        Notes:
            - Empty string is allowed (clears the author)
            - Author is stored as a string, not a user object reference
            - Use consistent naming for better filtering

        See Also:
            GetAuthor
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(note, "note")
        self._ValidateParam(author_name, "author_name")

        if hasattr(note, "Source"):
            ws = self.project.project.DefaultAnalWs
            mkstr = TsStringUtils.MakeString(author_name, ws)
            note.Source.set_String(ws, mkstr)

    # --- Discussion/Threading Operations ---

    @OperationsMethod
    def GetReplies(self, note):
        """
        Get all reply notes (threaded discussion) for a note.

        Args:
            note: The ICmBaseAnnotation (note) object.

        Yields:
            ICmBaseAnnotation: Each reply note.

        Raises:
            FP_NullParameterError: If note is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> notes = list(project.Note.GetAll(entry))
            >>> if notes:
            ...     parent = notes[0]
            ...     print(f"Parent: {project.Note.GetContent(parent)}")
            ...     for reply in project.Note.GetReplies(parent):
            ...         content = project.Note.GetContent(reply)
            ...         author = project.Note.GetAuthor(reply)
            ...         print(f"  Reply by {author}: {content}")
            Parent: Check etymology
              Reply by Jane: Looks correct to me
              Reply by John: Agreed, verified in source

        Notes:
            - Replies are child annotations of the parent note
            - Returns empty generator if note has no replies
            - Replies can themselves have replies (nested threading)
            - Use recursively for full conversation trees

        See Also:
            AddReply, Create
        """
        self._ValidateParam(note, "note")

        if hasattr(note, "RepliesOS"):
            for reply in note.RepliesOS:
                yield reply

    @OperationsMethod
    def AddReply(self, parent_note, content, wsHandle=None):
        """
        Add a reply to an existing note (threaded discussion).

        Args:
            parent_note: The ICmBaseAnnotation (note) to reply to.
            content (str): The reply text content.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmBaseAnnotation: The newly created reply note.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If parent_note or content is None.
            FP_ParameterError: If content is empty.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> note = project.Note.Create(entry, "Is this etymology correct?")
            >>> project.Note.SetAuthor(note, "John")
            >>>
            >>> # Add a reply
            >>> reply = project.Note.AddReply(note, "Yes, verified in source")
            >>> project.Note.SetAuthor(reply, "Jane")
            >>>
            >>> # Add a nested reply
            >>> nested = project.Note.AddReply(reply, "Thanks for checking!")
            >>> project.Note.SetAuthor(nested, "John")

        Notes:
            - Reply is created as a child of the parent note
            - DateCreated is set automatically
            - Replies support all note operations (type, metadata, etc.)
            - Can create multi-level threaded discussions

        See Also:
            GetReplies, Create, SetAuthor
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(parent_note, "parent_note")
        self._ValidateParam(content, "content")

        if not content or not content.strip():
            raise FP_ParameterError("Reply content cannot be empty")

        wsHandle = self.__WSHandle(wsHandle)

        # Create the reply annotation using the factory
        with self._TransactionCM("Add reply"):
            factory = self.project.project.ServiceLocator.GetService(ICmBaseAnnotationFactory)
            reply = factory.Create()

            # Add as reply to parent note (must be done before setting properties)
            if hasattr(parent_note, "RepliesOS"):
                parent_note.RepliesOS.Add(reply)

            # Set the content
            mkstr = TsStringUtils.MakeString(content, wsHandle)
            reply.Comment.set_String(wsHandle, mkstr)

            # Set creation date
            reply.DateCreated = DateTime.Now

            return reply

    # --- Utility Operations ---

    @OperationsMethod
    def GetOwner(self, note):
        """
        Get the owner object that the note is attached to.

        Args:
            note: The ICmBaseAnnotation (note) object.

        Returns:
            object: The owner object (ILexEntry, ILexSense, etc.), or None.

        Raises:
            FP_NullParameterError: If note is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> note = project.Note.Create(entry, "Check this")
            >>> owner = project.Note.GetOwner(note)
            >>> print(owner == entry)
            True

            >>> # Get headword of entry that owns the note
            >>> if hasattr(owner, 'LexemeFormOA'):
            ...     headword = project.LexEntry.GetHeadword(owner)
            ...     print(f"Note on entry: {headword}")
            Note on entry: run

        Notes:
            - Returns the direct owner object
            - For replies, returns the parent note, not the original object
            - Use BeginObjectRA for the annotated object reference

        See Also:
            Create, GetAll
        """
        self._ValidateParam(note, "note")

        # .Owner is on every ICmObject; no hasattr guard needed. The
        # previous BeginObjectRA fallback was unreachable. (issue #133
        # sweep -- BeginObjectRA is exposed as the annotated-object
        # reference via separate accessors.)
        return note.Owner

    @OperationsMethod
    def GetGuid(self, note):
        """
        Get the GUID of a note.

        Args:
            note: The ICmBaseAnnotation (note) object.

        Returns:
            System.Guid: The GUID of the note.

        Raises:
            FP_NullParameterError: If note is None.

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> note = project.Note.Create(entry, "Important note")
            >>> guid = project.Note.GetGuid(note)
            >>> print(f"Note GUID: {guid}")
            Note GUID: 12345678-1234-1234-1234-123456789abc

        Notes:
            - GUIDs are globally unique identifiers
            - Persistent across project versions
            - Use for external references and tracking
            - Same GUID across different copies of the project

        See Also:
            GetOwner, Create
        """
        self._ValidateParam(note, "note")

        return note.Guid

    # --- Private Helper Methods ---

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to analysis WS for notes.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    def __FindAnnotationDefn(self, name):
        """
        Find an annotation definition by name.

        Args:
            name (str): The name of the annotation definition to find.

        Returns:
            ICmAnnotationDefn: The annotation definition, or None if not found.
        """
        # Get annotation definition list
        anno_defn_list = self.project.project.LangProject.AnnotationDefsOA
        if not anno_defn_list:
            return None

        ws = self.project.project.DefaultAnalWs

        # Search through possibilities
        for defn in anno_defn_list.PossibilitiesOS:
            defn_name = ITsString(defn.Name.get_String(ws)).Text
            if defn_name == name:
                return defn

        return None
