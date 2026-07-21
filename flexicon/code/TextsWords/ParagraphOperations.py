#
#   ParagraphOperations.py
#
#   Class: ParagraphOperations
#          Paragraph CRUD operations for FieldWorks Language Explorer projects
#          via SIL Language and Culture Model (LCM) API.
#
#   Copyright Craig Farrow, 2008 - 2025
#

import clr

clr.AddReference("System")
import System

from SIL.LCModel import (
    IText,
    IStTxtPara,
    IStTxtParaFactory,
)

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable


class ParagraphOperations(BaseOperations):
    """
    Paragraph CRUD operations for managing FLEx paragraph objects.

    This class provides methods for creating, reading, updating, and deleting
    paragraphs within texts in a FieldWorks Language Explorer project.

    Usage:
        project = FLExProject()
        project.OpenProject("MyProject", writeEnabled=True)

        # Access through the Paragraphs property
        para_ops = ParagraphOperations(project)

        # Or if integrated into FLExProject:
        # text = project.Texts.Create("Genesis")
        # para = project.Paragraphs.Create(text, "In the beginning...")
    """

    def __init__(self, project):
        """
        Initialize ParagraphOperations with a FLEx project.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """Specify which sequence to reorder for paragraph segments."""
        return parent.SegmentsOS

    def __WSHandle(self, wsHandle):
        """
        Internal helper for writing system handles.

        Args:
            wsHandle: Writing system handle or None for default vernacular WS.

        Returns:
            int: The writing system handle to use.
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)

    def __GetTextObject(self, text_or_hvo):
        """
        Resolve text_or_hvo to IText object.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer).

        Returns:
            IText: The text object.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the object doesn't exist or isn't a valid text.
        """
        self._ValidateParam(text_or_hvo, "text_or_hvo")

        if isinstance(text_or_hvo, int):
            try:
                obj = self.project.Object(text_or_hvo)
                return IText(obj)
            except (AttributeError, System.InvalidCastException) as e:
                raise FP_ParameterError(f"Invalid text HVO: {text_or_hvo}") from e
        return text_or_hvo

    def __GetParagraphObject(self, para_or_hvo):
        """
        Resolve para_or_hvo to IStTxtPara object.

        Args:
            para_or_hvo: Either an IStTxtPara object or its HVO (integer).

        Returns:
            IStTxtPara: The paragraph object.

        Raises:
            FP_NullParameterError: If para_or_hvo is None.
            FP_ParameterError: If the object doesn't exist or isn't a valid paragraph.
        """
        self._ValidateParam(para_or_hvo, "para_or_hvo")

        if isinstance(para_or_hvo, int):
            try:
                obj = self.project.Object(para_or_hvo)
                return IStTxtPara(obj)
            except (AttributeError, System.InvalidCastException) as e:
                raise FP_ParameterError(f"Invalid paragraph HVO: {para_or_hvo}") from e
        return para_or_hvo

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, text_or_hvo, content, wsHandle=None):
        """
        Create a new paragraph and append it to a text.

        Creates a new paragraph with the specified content and adds it to the end
        of the text's paragraph collection. The paragraph will be created in the
        specified writing system or the default vernacular writing system.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).
            content (str): The text content for the new paragraph. Must be non-empty.
            wsHandle (int, optional): Writing system handle. If None, uses the
                default vernacular writing system. Can also be a language tag string.

        Returns:
            IStTxtPara: The newly created paragraph object.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If text_or_hvo or content is None.
            FP_ParameterError: If text has no StText contents, or content is empty.

        Example:
            >>> # Create a paragraph in a text
            >>> text = project.Texts.Create("Genesis")
            >>> para = project.Paragraphs.Create(text, "In the beginning...")
            >>> print(project.Paragraphs.GetText(para))
            In the beginning...

            >>> # Create with specific writing system
            >>> ws_handle = project.WSHandle('en')
            >>> para2 = project.Paragraphs.Create(text, "Chapter 2", ws_handle)

        See Also:
            Delete, InsertAt, GetAll, SetText
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(content, "content")

        content_str = content.strip() if isinstance(content, str) else str(content)
        if not content_str:
            raise FP_ParameterError("Content cannot be empty")

        text_obj = self.__GetTextObject(text_or_hvo)

        # Validate text has ContentsOA
        if not text_obj.ContentsOA:
            raise FP_ParameterError("Text has no StText contents")

        # Get the writing system handle
        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM("Create paragraph"):
            # Create the new paragraph using the factory
            factory = self.project.project.ServiceLocator.GetService(IStTxtParaFactory)
            para = factory.Create()

            # Add to text's paragraphs collection
            text_obj.ContentsOA.ParagraphsOS.Add(para)

            # Set the content
            mkstr = TsStringUtils.MakeString(content_str, wsHandle)
            para.Contents = mkstr

            return para

    @OperationsMethod
    def Delete(self, paragraph_or_hvo):
        """
        Delete a paragraph from its text.

        Removes the paragraph from its parent text's paragraph collection. This
        will also delete all segments and other data associated with the paragraph.

        Args:
            paragraph_or_hvo: Either an IStTxtPara object or its HVO (integer identifier).

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If paragraph_or_hvo is None.
            FP_ParameterError: If the paragraph does not exist or is invalid.

        Example:
            >>> # Delete a paragraph
            >>> para = list(project.Paragraphs.GetAll(text))[0]
            >>> project.Paragraphs.Delete(para)

            >>> # Delete by HVO
            >>> project.Paragraphs.Delete(para_hvo)

        Warning:
            - Deletion is permanent and cannot be undone
            - All segments in the paragraph will also be deleted
            - References to the paragraph from other objects may become invalid

        See Also:
            Create, GetAll, InsertAt
        """
        self._EnsureWriteEnabled()

        para_obj = self.__GetParagraphObject(paragraph_or_hvo)

        # Cast owner to its concrete IStText so ParagraphsOS is reachable.
        # Raw para.Owner is typed as ICmObject and
        # hasattr(...,"ParagraphsOS") returns False there, which is why
        # the prior implementation always fell through to the else branch
        # and spuriously raised even on perfectly valid paragraphs.
        owner = self._GetTypedOwner(para_obj)
        if owner is None:
            raise FP_ParameterError("Paragraph has no valid owner or cannot be removed")
        owner.ParagraphsOS.Remove(para_obj)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=True):
        """
        Duplicate a paragraph, creating a new paragraph with the same content.

        This method creates a copy of an existing paragraph. With deep=True (default),
        all segments are also duplicated (though segments typically need re-parsing).
        With deep=False, only the paragraph text is duplicated.

        Args:
            item_or_hvo: Either an IStTxtPara object or its HVO (integer identifier)
            insert_after (bool): If True, insert the duplicate after the original
                paragraph in the text. If False, append to the end of the text.
            deep (bool): If True (default), also duplicate all segments (though they
                may need re-parsing). If False, only duplicate the paragraph text.

        Returns:
            IStTxtPara: The newly created duplicate paragraph

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If item_or_hvo is None.
            FP_ParameterError: If the paragraph does not exist or is invalid, or
                if the paragraph has no valid owner text.

        Example:
            >>> # Deep duplicate (default: with segments, though they need re-parsing)
            >>> para = list(project.Paragraphs.GetAll(text))[0]
            >>> duplicate = project.Paragraphs.Duplicate(para, insert_after=True)  # deep=True by default
            >>> print(project.Paragraphs.GetText(duplicate))
            In the beginning...

            >>> # Shallow duplicate (paragraph text only)
            >>> duplicate = project.Paragraphs.Duplicate(para, deep=False)

        Warning:
            - The duplicate will have identical content but a new GUID
            - Segments in duplicated paragraphs will need re-parsing for analyses
            - insert_after=True inserts immediately after the original paragraph
            - deep=True duplicates segments, but they may not have valid analyses

        Notes:
            - Duplicated paragraph is added to the same text as the original
            - New GUID is auto-generated for the duplicate
            - Text content is copied in the same writing system
            - With deep=True, segments are created but analyses are not copied
            - Paragraph is inserted after original if insert_after=True

        See Also:
            Create, Delete, InsertAt, project.Segments.Duplicate
        """
        self._EnsureWriteEnabled()

        para_obj = self.__GetParagraphObject(item_or_hvo)

        # Cast owner to its concrete IStText so ParagraphsOS is reachable.
        # Raw para_obj.Owner is typed as ICmObject; hasattr(..., "ParagraphsOS")
        # returns False there, silently no-opping Duplicate.
        owner = self._GetTypedOwner(para_obj)
        if owner is None:
            raise FP_ParameterError("Paragraph has no valid owner text")

        # Get parent IText — StText.Owner is the IText container.
        # Cast via IText so ContentsOA and ParagraphsOS are accessible when
        # the result is passed to InsertAt / Create.
        parent_text = IText(owner.Owner) if owner.Owner is not None else None
        if parent_text is None:
            raise FP_ParameterError("Cannot determine parent text for paragraph")

        # Get source properties
        wsHandle = self.__WSHandle(None)
        para_text = self.GetText(para_obj, wsHandle)

        with self._TransactionCM("Duplicate paragraph"):
            # Determine insertion position
            if insert_after:
                # Find the index of the current paragraph
                para_list = list(owner.ParagraphsOS)
                try:
                    current_index = para_list.index(para_obj)
                    insert_index = current_index + 1
                except ValueError:
                    # Paragraph not found in list, append to end
                    insert_index = len(para_list)

                # Insert at position
                new_para = self.InsertAt(parent_text, insert_index, para_text, wsHandle)
            else:
                # Append to end
                new_para = self.Create(parent_text, para_text, wsHandle)

            # Deep duplication: duplicate all segments
            if deep:
                segments = self.GetSegments(para_obj)
                for segment in segments:
                    if hasattr(segment, "BaselineText"):
                        seg_text = ITsString(segment.BaselineText).Text or ""
                        if seg_text and hasattr(self.project, "Segments"):
                            # AppendSentence edits Contents first then adds the segment,
                            # matching the correct LCM idiom. It also auto-inserts a
                            # sentence terminator when the paragraph does not already
                            # end with one, so seg_text is passed as-is.
                            self.project.Segments.AppendSentence(new_para, seg_text, wsHandle)

            return new_para

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a paragraph.

        Args:
            item: The IStTxtPara object.

        Returns:
            dict: Dictionary of syncable properties with their values.

        Example:
            >>> props = project.Paragraphs.GetSyncableProperties(para)
            >>> print(props['Contents'])
            {'en': 'In the beginning...'}

        Notes:
            - Contents is a TsString property (returned as dict with WS keys)
            - Does NOT include owned sequences (segments) - those are children
        """
        props = {}

        # TsString property - Contents (paragraph text)
        if hasattr(item, "Contents") and item.Contents:
            # Convert TsString to dict with WS keys
            ws_dict = {}
            text = ITsString(item.Contents).Text
            if text:
                # Get the writing system of the TsString
                ws = item.Contents.get_WritingSystemAt(0) if item.Contents.Length > 0 else None
                if ws:
                    # Find the WritingSystemDefinition with this handle to get its ID
                    ws_def = next((w for w in self.project.WritingSystems.GetAll() if w.Handle == ws), None)
                    if ws_def:
                        ws_dict[ws_def.Id] = text
            props["Contents"] = ws_dict

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two paragraphs for differences.

        Args:
            item1: First paragraph object (from project 1)
            item2: Second paragraph object (from project 2)
            ops1: Optional ParagraphOperations instance for project 1 (defaults to self)
            ops2: Optional ParagraphOperations instance for project 2 (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
                - is_different (bool): True if paragraphs differ, False if identical
                - differences_dict (dict): Maps property names to (value1, val2) tuples

        Example:
            >>> is_diff, diffs = ops1.CompareTo(para1, para2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} != {val2}")

        Notes:
            - Compares paragraph Contents (text)
            - Empty/null values are treated as equivalent
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}

        # Get all property keys from both items
        all_keys = set(props1.keys()) | set(props2.keys())

        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            # Compare values
            if self.project._CompareValues(val1, val2):
                # Values are different
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return (is_different, differences)

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, text_or_hvo):
        """
        Get all paragraphs in a text.

        Returns an EnumerableWrapper (subscriptable, len()-able, lazily
        materialized) over all paragraph objects in the text's paragraph
        collection, in order.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).

        Returns:
            EnumerableWrapper[IStTxtPara]: Each paragraph object in the text.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> # Iterate over all paragraphs
            >>> text = project.Texts.Find("Genesis")
            >>> for para in project.Paragraphs.GetAll(text):
            ...     text = project.Paragraphs.GetText(para)
            ...     print(f"Paragraph: {text[:50]}...")

            >>> # Get as list
            >>> all_paras = list(project.Paragraphs.GetAll(text))
            >>> print(f"Total paragraphs: {len(all_paras)}")

        Notes:
            - If the text has no contents, yields nothing
            - Paragraphs are yielded in the order they appear in the text
            - Use list() to convert to a list if you need random access

        See Also:
            Create, Delete, GetSegmentCount
        """
        text_obj = self.__GetTextObject(text_or_hvo)

        # If text has no contents, return empty
        if not text_obj.ContentsOA:
            return

        # Yield each paragraph, cast to IStTxtPara to ensure SegmentsOS is accessible
        for para in text_obj.ContentsOA.ParagraphsOS:
            yield IStTxtPara(para)

    @OperationsMethod
    def GetText(self, paragraph_or_hvo, wsHandle=None):
        """
        Get the text content of a paragraph.

        Retrieves the text content in the specified writing system, or the default
        vernacular writing system if not specified.

        Args:
            paragraph_or_hvo: Either an IStTxtPara object or its HVO (integer identifier).
            wsHandle (int, optional): Writing system handle. If None, uses the
                default vernacular writing system. Can also be a language tag string.

        Returns:
            str: The text content of the paragraph. Returns empty string if no
                content is set for that writing system.

        Raises:
            FP_NullParameterError: If paragraph_or_hvo is None.
            FP_ParameterError: If the paragraph does not exist or is invalid.

        Example:
            >>> para = list(project.Paragraphs.GetAll(text))[0]
            >>>
            >>> # Get text in default vernacular WS
            >>> text = project.Paragraphs.GetText(para)
            >>> print(text)
            In the beginning...
            >>>
            >>> # Get text in specific WS
            >>> ws_handle = project.WSHandle('en')
            >>> text_en = project.Paragraphs.GetText(para, ws_handle)

        See Also:
            SetText, Create, GetSegments
        """
        para_obj = self.__GetParagraphObject(paragraph_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Get the text content
        text = para_obj.Contents.Text if para_obj.Contents else ""
        return text or ""

    @OperationsMethod
    def SetText(self, paragraph_or_hvo, content, wsHandle=None):
        """
        Set the text content of a paragraph.

        Updates the paragraph's text content in the specified writing system, or
        the default vernacular writing system if not specified.

        Args:
            paragraph_or_hvo: Either an IStTxtPara object or its HVO (integer identifier).
            content (str): The new text content for the paragraph. Must be non-empty.
            wsHandle (int, optional): Writing system handle. If None, uses the
                default vernacular writing system. Can also be a language tag string.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If paragraph_or_hvo or content is None.
            FP_ParameterError: If the paragraph does not exist, is invalid, or
                content is empty.

        Example:
            >>> para = list(project.Paragraphs.GetAll(text))[0]
            >>>
            >>> # Set text in default vernacular WS
            >>> project.Paragraphs.SetText(para, "Updated paragraph text.")
            >>>
            >>> # Set text in specific WS
            >>> ws_handle = project.WSHandle('en')
            >>> project.Paragraphs.SetText(para, "English text", ws_handle)

        Warning:
            - This will replace all existing content in the paragraph
            - Existing segments may be invalidated and need re-analysis
            - Use with caution on analyzed texts

        See Also:
            GetText, Create, InsertAt
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(content, "content")

        content_str = content.strip() if isinstance(content, str) else str(content)
        if not content_str:
            raise FP_ParameterError("Content cannot be empty")

        para_obj = self.__GetParagraphObject(paragraph_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Set the content
        mkstr = TsStringUtils.MakeString(content_str, wsHandle)
        para_obj.Contents = mkstr

    @OperationsMethod
    def GetSegments(self, paragraph_or_hvo):
        """
        Get all segments in a paragraph.

        Segments are the individual units (typically sentences) within a paragraph
        that can have their own analyses and translations.

        Args:
            paragraph_or_hvo: Either an IStTxtPara object or its HVO (integer identifier).

        Returns:
            list: A list of ISegment objects in the paragraph.

        Raises:
            FP_NullParameterError: If paragraph_or_hvo is None.
            FP_ParameterError: If the paragraph does not exist or is invalid.

        Example:
            >>> para = list(project.Paragraphs.GetAll(text))[0]
            >>> segments = project.Paragraphs.GetSegments(para)
            >>> print(f"Paragraph has {len(segments)} segments")
            Paragraph has 3 segments
            >>>
            >>> # Iterate over segments
            >>> for seg in segments:
            ...     print(seg.BaselineText.Text)

        Notes:
            - Returns empty list if the paragraph has no segments
            - Segments are created during text analysis
            - Use GetSegmentCount() for a quick count without creating a list

        See Also:
            GetSegmentCount, GetText, Create
        """
        para_obj = self.__GetParagraphObject(paragraph_or_hvo)

        # Return list of segments
        return list(para_obj.SegmentsOS)

    @OperationsMethod
    def GetSegmentCount(self, paragraph_or_hvo):
        """
        Get the number of segments in a paragraph.

        This is more efficient than calling len(GetSegments()) when you only
        need the count.

        Args:
            paragraph_or_hvo: Either an IStTxtPara object or its HVO (integer identifier).

        Returns:
            int: The number of segments in the paragraph.

        Raises:
            FP_NullParameterError: If paragraph_or_hvo is None.
            FP_ParameterError: If the paragraph does not exist or is invalid.

        Example:
            >>> para = list(project.Paragraphs.GetAll(text))[0]
            >>> count = project.Paragraphs.GetSegmentCount(para)
            >>> print(f"Paragraph has {count} segments")
            Paragraph has 3 segments

        Notes:
            - Returns 0 if the paragraph has no segments
            - More efficient than getting all segments when you only need the count
            - Segments are created during text analysis

        See Also:
            GetSegments, GetText
        """
        para_obj = self.__GetParagraphObject(paragraph_or_hvo)

        # Return segment count
        return para_obj.SegmentsOS.Count

    @OperationsMethod
    def InsertAt(self, text_or_hvo, index, content, wsHandle=None):
        """
        Insert a new paragraph at a specific position in a text.

        Creates a new paragraph with the specified content and inserts it at the
        given index in the text's paragraph collection. Existing paragraphs at
        that index and after will be shifted down.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).
            index (int): The position at which to insert the paragraph (0-based).
                Must be between 0 and the current paragraph count (inclusive).
            content (str): The text content for the new paragraph. Must be non-empty.
            wsHandle (int, optional): Writing system handle. If None, uses the
                default vernacular writing system. Can also be a language tag string.

        Returns:
            IStTxtPara: The newly created paragraph object.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If text_or_hvo or content is None.
            FP_ParameterError: If text has no StText contents, content is empty,
                or index is out of range.

        Example:
            >>> text = project.Texts.Find("Genesis")
            >>>
            >>> # Insert at beginning
            >>> para = project.Paragraphs.InsertAt(text, 0, "Title: Genesis")
            >>>
            >>> # Insert at end (equivalent to Create)
            >>> count = len(list(project.Paragraphs.GetAll(text)))
            >>> para2 = project.Paragraphs.InsertAt(text, count, "The end")
            >>>
            >>> # Insert in middle
            >>> para3 = project.Paragraphs.InsertAt(text, 5, "Chapter 3")

        Notes:
            - Index must be in range [0, current_paragraph_count]
            - Index equal to paragraph count appends to the end
            - Existing paragraphs are shifted, not replaced
            - Use Create() to always append to the end

        See Also:
            Create, Delete, GetAll
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(content, "content")

        content_str = content.strip() if isinstance(content, str) else str(content)
        if not content_str:
            raise FP_ParameterError("Content cannot be empty")

        text_obj = self.__GetTextObject(text_or_hvo)

        # Validate text has ContentsOA
        if not text_obj.ContentsOA:
            raise FP_ParameterError("Text has no StText contents")

        # Validate index range
        para_count = text_obj.ContentsOA.ParagraphsOS.Count
        if index < 0 or index > para_count:
            raise FP_ParameterError(f"Index {index} out of range (0-{para_count})")

        # Get the writing system handle
        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM(f"Insert paragraph at {index}"):
            # Create the new paragraph using the factory
            factory = self.project.project.ServiceLocator.GetService(IStTxtParaFactory)
            para = factory.Create()

            # Insert at the specified index
            text_obj.ContentsOA.ParagraphsOS.Insert(index, para)

            # Set the content
            mkstr = TsStringUtils.MakeString(content_str, wsHandle)
            para.Contents = mkstr

            return para
