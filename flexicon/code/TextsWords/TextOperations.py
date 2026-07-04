#
#   TextOperations.py
#
#   Class: TextOperations
#            Text operations for FieldWorks Language Explorer projects
#            via SIL Language and Culture Model (LCM) API.
#
#   Copyright Craig Farrow, 2008 - 2024
#

import clr

clr.AddReference("System")
import System

from SIL.LCModel import (
    IText,
    ITextFactory,
    IStTextFactory,
    IStTxtParaFactory,
    ITextRepository,
    IStTxtPara,
    ICmPossibility,
    ICmMedia,
    ICmMediaFactory,
    ICmFolderFactory,
)

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key


class TextOperations(BaseOperations):
    """
    Text operations for managing FLEx Text objects.

    This class provides methods for creating, reading, updating, and deleting
    texts in a FieldWorks Language Explorer project.

    Usage:
        project = FLExProject()
        project.OpenProject("MyProject", writeEnabled=True)

        # Access through the Texts property
        text_ops = TextOperations(project)

        # Or if integrated into FLExProject:
        # new_text = project.Texts.Create("Story 1")
    """

    def __init__(self, project):
        """
        Initialize TextOperations with a FLEx project.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """Specify which sequence to reorder for text paragraphs."""
        return parent.ContentsOS

    def __WSHandle(self, wsHandle):
        """
        Internal helper for writing system handles.

        Args:
            wsHandle: Writing system handle or None for default analysis WS.

        Returns:
            int: The writing system handle to use.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    def __GetTextObject(self, text_or_hvo):
        """
        Resolve text_or_hvo to IText object.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer).

        Returns:
            IText: The text object.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the HVO doesn't refer to a text object.
        """
        self._ValidateParam(text_or_hvo, "text_or_hvo")

        if isinstance(text_or_hvo, int):
            obj = self.project.Object(text_or_hvo)
            if not isinstance(obj, IText):
                raise FP_ParameterError(f"HVO {text_or_hvo} does not refer to a text object")
            return obj
        return text_or_hvo

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, name, genre=None):
        """
        Create a new text in the project.

        Creates a new IText object with the specified name and optional genre.
        The text will have an empty StText contents object created automatically.

        Args:
            name (str): The name of the text. Must be unique and non-empty.
            genre (ICmPossibility, optional): Genre classification for the text.
                If provided, must be a valid ICmPossibility from the project's
                genre list. Defaults to None.

        Returns:
            IText: The newly created text object.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If name is None or empty.
            FP_ParameterError: If a text with this name already exists.

        Example:
            >>> # Create a simple text
            >>> text = project.Texts.Create("Genesis")
            >>> print(text.Name.BestAnalysisAlternative.Text)
            Genesis

            >>> # Create a text with genre
            >>> narrative_genre = project.lp.GenreListOA.PossibilitiesOS[0]
            >>> text = project.Texts.Create("Story 1", genre=narrative_genre)

        See Also:
            Delete, Exists, GetAll
        """
        self._EnsureWriteEnabled()
        self._ValidateStringNotEmpty(name, "text name")
        name = name.strip()

        # Check if text with this name already exists
        if self.Exists(name):
            raise FP_ParameterError(f"A text with the name '{name}' already exists.")

        with self._TransactionCM(f"Create text '{name}'"):
            # Create the text object
            text_factory = self.project.project.ServiceLocator.GetService(ITextFactory)
            new_text = text_factory.Create()

            # Add to the texts collection. In newer LCM builds ILangProject's
            # texts accessor is `Texts` (not `TextsOC` -- the latter has been
            # renamed/removed). See issue #22.
            self.project.lp.Texts.Add(new_text)

            # Set the name
            wsHandle = self.project.project.DefaultAnalWs
            name_str = TsStringUtils.MakeString(name, wsHandle)
            new_text.Name.set_String(wsHandle, name_str)

            # Create the contents (StText)
            sttext_factory = self.project.project.ServiceLocator.GetService(IStTextFactory)
            contents = sttext_factory.Create()
            new_text.ContentsOA = contents

            # Set genre if provided
            if genre is not None:
                self.SetGenre(new_text, genre)

            return new_text

    @OperationsMethod
    def Delete(self, text_or_hvo):
        """
        Delete a text from the project.

        Removes the text and all its contents (paragraphs, segments, etc.) from
        the project database.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> # Delete by object
            >>> text = project.Texts.GetAll()[0]
            >>> project.Texts.Delete(text)

            >>> # Delete by HVO
            >>> project.Texts.Delete(text_hvo)

        See Also:
            Create, Exists, GetAll
        """
        self._EnsureWriteEnabled()

        text_obj = self.__GetTextObject(text_or_hvo)

        # Remove from collection. See note in Create() about the LCM API
        # rename from TextsOC to Texts (issue #22).
        self.project.lp.Texts.Remove(text_obj)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, deep=True):
        """
        Duplicate a text, creating a new text with the same properties.

        This method creates a copy of an existing text. With deep=True (default),
        all paragraphs and their segments are recursively duplicated. With deep=False,
        only the text shell (name, genre, abbreviation) is duplicated.

        Args:
            item_or_hvo: Either an IText object or its HVO (integer identifier)
            deep (bool): If True (default), recursively duplicate all paragraphs
                and segments. If False, only duplicate the text shell (name, genre).

        Returns:
            IText: The newly created duplicate text

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If item_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> # Deep duplicate (default: with all paragraphs)
            >>> text = list(project.Texts.GetAll())[0]
            >>> duplicate = project.Texts.Duplicate(text)  # deep=True by default
            >>> print(project.Texts.GetParagraphCount(duplicate))
            10

            >>> # Shallow duplicate (text shell only, no paragraphs)
            >>> text = list(project.Texts.GetAll())[0]
            >>> duplicate = project.Texts.Duplicate(text, deep=False)
            >>> print(project.Texts.GetName(duplicate))
            Genesis (copy)
            >>> print(project.Texts.GetParagraphCount(duplicate))
            0

        Warning:
            - deep=True for Text can be slow for long texts with many paragraphs
            - The duplicate will have a " (copy)" suffix added to the name
            - The duplicate will have identical content but a new GUID
            - Media files are NOT duplicated (to avoid file duplication)
            - Segments will need re-parsing if you want analyses

        Notes:
            - Duplicated text is added to the project texts collection
            - New GUID is auto-generated for the duplicate
            - Name is copied with " (copy)" suffix to ensure uniqueness
            - Genre is copied (if set)
            - Abbreviation is copied (if set)
            - With deep=True, all paragraphs are recursively duplicated

        See Also:
            Create, Delete, project.Paragraphs.Duplicate
        """
        self._EnsureWriteEnabled()

        text_obj = self.__GetTextObject(item_or_hvo)

        # Get source properties
        wsHandle = self.__WSHandle(None)
        source_name = self.GetName(text_obj, wsHandle)
        source_genre = self.GetGenre(text_obj)

        # Create unique name by appending " (copy)"
        new_name = f"{source_name} (copy)"

        # Ensure uniqueness
        counter = 1
        while self.Exists(new_name):
            new_name = f"{source_name} (copy {counter})"
            counter += 1

        with self._TransactionCM("Duplicate text"):
            # Create the new text (sets Name and Genre via Create helper)
            new_text = self.Create(new_name, genre=source_genre)

            # Copy remaining MultiString properties (all writing systems)
            if hasattr(text_obj, "Abbreviation") and text_obj.Abbreviation:
                new_text.Abbreviation.CopyAlternatives(text_obj.Abbreviation)
            if hasattr(text_obj, "Title") and text_obj.Title:
                new_text.Title.CopyAlternatives(text_obj.Title)
            if hasattr(text_obj, "Description") and text_obj.Description:
                new_text.Description.CopyAlternatives(text_obj.Description)
            if hasattr(text_obj, "Source") and text_obj.Source:
                new_text.Source.CopyAlternatives(text_obj.Source)

            # Deep duplication: copy paragraph contents
            if deep:
                paragraphs = self.GetParagraphs(text_obj)
                for para in paragraphs:
                    if para.Contents:
                        # Copy the full TsString (preserves formatting and all WS runs)
                        para_factory = self.project.project.ServiceLocator.GetService(IStTxtParaFactory)
                        new_para = para_factory.Create()
                        new_text.ContentsOA.ParagraphsOS.Add(new_para)
                        new_para.Contents = para.Contents

            return new_text

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a text.

        Args:
            item: The IText object.

        Returns:
            dict: Dictionary of syncable properties with their values.

        Example:
            >>> props = project.Texts.GetSyncableProperties(text)
            >>> print(props['Title'])
            {'en': 'Genesis'}
            >>> print(props['Description'])
            {'en': 'First book of the Bible'}

        Notes:
            - MultiString properties: Title, Description, Source
            - DateTime properties: DateCreated, DateModified
            - Reference Collection properties: GenresRC, MediaFilesRC (GUIDs)
            - Does NOT include owned sequences (paragraphs) - those are children
        """
        props = {}

        # MultiString properties
        if hasattr(item, "Title") and item.Title:
            props["Title"] = self.project.GetMultiStringDict(item.Title)

        if hasattr(item, "Description") and item.Description:
            props["Description"] = self.project.GetMultiStringDict(item.Description)

        if hasattr(item, "Source") and item.Source:
            props["Source"] = self.project.GetMultiStringDict(item.Source)

        # DateTime properties
        if hasattr(item, "DateCreated") and item.DateCreated:
            props["DateCreated"] = str(item.DateCreated)

        if hasattr(item, "DateModified") and item.DateModified:
            props["DateModified"] = str(item.DateModified)

        # Reference Collection properties (return list of GUIDs)
        if hasattr(item, "GenresRC") and item.GenresRC:
            props["GenresRC"] = [str(g.Guid) for g in item.GenresRC]

        if hasattr(item, "MediaFilesRC") and item.MediaFilesRC:
            props["MediaFilesRC"] = [str(m.Guid) for m in item.MediaFilesRC]

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two texts for differences.

        Args:
            item1: First text object (from project 1)
            item2: Second text object (from project 2)
            ops1: Optional TextOperations instance for project 1 (defaults to self)
            ops2: Optional TextOperations instance for project 2 (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
                - is_different (bool): True if texts differ, False if identical
                - differences_dict (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> is_diff, diffs = ops1.CompareTo(text1, text2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} != {val2}")

        Notes:
            - Compares all syncable properties
            - MultiStrings are compared across all writing systems
            - Reference collections are compared by GUID
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

    @OperationsMethod
    def Exists(self, name):
        """
        Check if a text with the given name exists in the project.

        Performs a case-sensitive comparison of text names in the default
        analysis writing system.

        Args:
            name (str): The name of the text to check.

        Returns:
            bool: True if a text with the given name exists, False otherwise.

        Raises:
            FP_NullParameterError: If name is None or empty.

        Example:
            >>> if project.Texts.Exists("Genesis"):
            ...     print("Text already exists")
            ... else:
            ...     text = project.Texts.Create("Genesis")

        See Also:
            Create, GetAll, GetName
        """
        self._ValidateStringNotEmpty(name, "text name")
        name = name.strip()

        # Check all texts for matching name
        target = normalize_match_key(name, casefold=False)
        for text in self.project.ObjectsIn(ITextRepository):
            text_name = ITsString(text.Name.BestAnalysisAlternative).Text
            if normalize_match_key(text_name, casefold=False) == target:
                return True

        return False

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all texts in the project.

        Returns a generator that yields IText objects. This is a wrapper around
        the existing TextsGetAll method but returns the raw IText objects instead
        of (name, content) tuples.

        Yields:
            IText: Each text object in the project.

        Example:
            >>> # Iterate over all texts
            >>> for text in project.Texts.GetAll():
            ...     name = text.Name.BestAnalysisAlternative.Text
            ...     print(f"Text: {name}")

            >>> # Get as list
            >>> all_texts = list(project.Texts.GetAll())
            >>> print(f"Total texts: {len(all_texts)}")

        See Also:
            Create, Delete, Exists, project.TextsGetAll()
        """
        return self.project.ObjectsIn(ITextRepository)

    @OperationsMethod
    def Find(self, title, wsHandle=None):
        """Find a text by title, returning None when no match exists.

        ``IText.Name`` is the user-facing title in FieldWorks, so Find
        searches that field. Matches a single writing system at a time
        (the default analysis WS when ``wsHandle`` is omitted). Returns
        the first matching ``IText`` or None; for partial matching,
        iterate ``GetAll()`` and filter manually.
        """
        self._ValidateParam(title, "title")
        if not title or not title.strip():
            return None

        wsHandle = self.__WSHandle(wsHandle)
        target = normalize_match_key(title, casefold=False)
        for text in self.GetAll():
            current = ITsString(text.Name.get_String(wsHandle)).Text
            if normalize_match_key(current, casefold=False) == target:
                return text
        return None

    # GetTitle / SetTitle are user-facing names for the same field that
    # LCM exposes as IText.Name. Both spellings appear in the codebase's
    # public conventions (and in FieldWorks' UI), so expose them as
    # first-class methods rather than as deprecated aliases.
    def GetTitle(self, text_or_hvo, wsHandle=None):
        """Get the text's title (same field as GetName)."""
        return self.GetName(text_or_hvo, wsHandle=wsHandle)

    def SetTitle(self, text_or_hvo, title, wsHandle=None):
        """Set the text's title (same field as SetName)."""
        return self.SetName(text_or_hvo, title, wsHandle=wsHandle)

    @OperationsMethod
    def GetName(self, text_or_hvo, wsHandle=None):
        """
        Get the name of a text.

        Retrieves the text name in the specified writing system, or the default
        analysis writing system if not specified.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).
            wsHandle (int, optional): Writing system handle. If None, uses the
                default analysis writing system. Can also be a language tag string.

        Returns:
            str: The name of the text in the specified writing system. Returns
                empty string if no name is set for that writing system.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>>
            >>> # Get name in default analysis WS
            >>> name = project.Texts.GetName(text)
            >>>
            >>> # Get name in specific WS
            >>> ws_handle = project.WSHandle('en')
            >>> name_en = project.Texts.GetName(text, ws_handle)

        See Also:
            SetName, Exists
        """
        text_obj = self.__GetTextObject(text_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Get the name string
        name_str = ITsString(text_obj.Name.get_String(wsHandle)).Text
        return name_str or ""

    @OperationsMethod
    def SetName(self, text_or_hvo, name, wsHandle=None):
        """
        Set the name of a text.

        Sets the text name in the specified writing system, or the default
        analysis writing system if not specified.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).
            name (str): The new name for the text. Must be non-empty.
            wsHandle (int, optional): Writing system handle. If None, uses the
                default analysis writing system. Can also be a language tag string.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If text_or_hvo or name is None/empty.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>>
            >>> # Set name in default analysis WS
            >>> project.Texts.SetName(text, "Updated Story")
            >>>
            >>> # Set name in specific WS
            >>> ws_handle = project.WSHandle('en')
            >>> project.Texts.SetName(text, "English Title", ws_handle)

        See Also:
            GetName, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        name = name.strip()
        self._ValidateParam(name, "name")

        text_obj = self.__GetTextObject(text_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Set the name
        mkstr = TsStringUtils.MakeString(name, wsHandle)
        text_obj.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetGenre(self, text_or_hvo):
        """
        Get the genre of a text.

        Retrieves the first genre assigned to the text. In FLEx, texts can
        technically have multiple genres, but typically only one is assigned.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).

        Returns:
            ICmPossibility or None: The genre object if one is assigned, or None
                if no genre is set.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>> genre = project.Texts.GetGenre(text)
            >>> if genre:
            ...     genre_name = genre.Name.BestAnalysisAlternative.Text
            ...     print(f"Genre: {genre_name}")
            ... else:
            ...     print("No genre assigned")

        See Also:
            SetGenre, Create
        """
        text_obj = self.__GetTextObject(text_or_hvo)

        # Get the first genre (if any)
        if text_obj.GenresRC.Count > 0:
            return text_obj.GenresRC.FirstOrDefault()

        return None

    @OperationsMethod
    def SetGenre(self, text_or_hvo, genre):
        """
        Set the genre of a text.

        Clears any existing genres and sets the specified genre. If genre is None,
        all genres are cleared.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).
            genre (ICmPossibility or None): The genre to assign. Must be a valid
                ICmPossibility from the project's genre list (typically found in
                project.lp.GenreListOA.PossibilitiesOS). If None, clears all genres.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid, or if
                genre is not a valid ICmPossibility.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>>
            >>> # Set genre to first available genre
            >>> if project.lp.GenreListOA.PossibilitiesOS.Count > 0:
            ...     narrative = project.lp.GenreListOA.PossibilitiesOS[0]
            ...     project.Texts.SetGenre(text, narrative)
            >>>
            >>> # Clear genre
            >>> project.Texts.SetGenre(text, None)

        See Also:
            GetGenre, Create
        """
        self._EnsureWriteEnabled()

        text_obj = self.__GetTextObject(text_or_hvo)

        with self._TransactionCM("Set text genre"):
            # Clear existing genres
            text_obj.GenresRC.Clear()

            # Add new genre if provided
            if genre is not None:
                try:
                    # Validate it's a possibility
                    genre_poss = ICmPossibility(genre)
                    text_obj.GenresRC.Add(genre_poss)
                except (TypeError, System.InvalidCastException, AttributeError):
                    raise FP_ParameterError("genre must be a valid ICmPossibility object")

    # --- Advanced Text Content Operations ---

    @OperationsMethod
    def GetContents(self, text_or_hvo):
        """
        Get the StText contents object for a text.

        Retrieves the IStText object that contains the actual content (paragraphs,
        segments, etc.) of the text. Each IText has a ContentsOA (owned atomic)
        property that points to its StText content object.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).

        Returns:
            IStText or None: The text contents object if set, or None if the text
                has no contents.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> text = project.Texts.Find("Genesis")
            >>> contents = project.Texts.GetContents(text)
            >>> if contents:
            ...     print(f"Paragraphs: {contents.ParagraphsOS.Count}")
            ... else:
            ...     print("Text has no contents")

        See Also:
            GetParagraphs, GetParagraphCount, Create
        """
        text_obj = self.__GetTextObject(text_or_hvo)
        return text_obj.ContentsOA if text_obj.ContentsOA else None

    @OperationsMethod
    def GetParagraphs(self, text_or_hvo):
        """
        Get all paragraphs in a text.

        Retrieves a list of all paragraph objects (IStTxtPara) from the text's
        contents. If the text has no contents, returns an empty list.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).

        Returns:
            list: List of IStTxtPara objects. Returns empty list if the text has
                no contents or no paragraphs.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>> paras = project.Texts.GetParagraphs(text)
            >>> for i, para in enumerate(paras, 1):
            ...     content = para.Contents.Text
            ...     print(f"Paragraph {i}: {content}")

        See Also:
            GetContents, GetParagraphCount
        """
        text_obj = self.__GetTextObject(text_or_hvo)
        if text_obj.ContentsOA:
            # Cast each paragraph to IStTxtPara to ensure SegmentsOS is accessible
            return [IStTxtPara(para) for para in text_obj.ContentsOA.ParagraphsOS]
        return []

    @OperationsMethod
    def GetParagraphCount(self, text_or_hvo):
        """
        Get the number of paragraphs in a text.

        Counts the paragraphs in the text's contents. This is more efficient
        than getting all paragraphs and checking the length if you only need
        the count.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).

        Returns:
            int: The number of paragraphs. Returns 0 if the text has no contents.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>> count = project.Texts.GetParagraphCount(text)
            >>> print(f"Text has {count} paragraphs")

        See Also:
            GetParagraphs, GetContents
        """
        text_obj = self.__GetTextObject(text_or_hvo)
        if text_obj.ContentsOA:
            return text_obj.ContentsOA.ParagraphsOS.Count
        return 0

    @OperationsMethod
    def GetMediaFiles(self, text_or_hvo):
        """
        Get media files associated with a text.

        Retrieves all media files (audio, video, etc.) that are linked to the
        text. In FLEx, media files are stored in a CmMediaContainer object
        referenced by the text's MediaFilesOA property.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).

        Returns:
            list: List of ICmMedia objects. Returns empty list if no media
                container exists or no media files are attached.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>> media = project.Texts.GetMediaFiles(text)
            >>> for m in media:
            ...     if m.MediaFileRA:
            ...         path = m.MediaFileRA.AbsoluteInternalPath
            ...         print(f"Media file: {path}")

        See Also:
            AddMediaFile
        """
        text_obj = self.__GetTextObject(text_or_hvo)
        if text_obj.MediaFilesOA:
            return list(text_obj.MediaFilesOA.MediaFilesOC)
        return []

    @OperationsMethod
    def AddMediaFile(self, text_or_hvo, filepath, label=None):
        """
        Add a media file to a text.

        Copies the file to the project's LinkedFiles directory and creates
        a media reference linked to the text. If the text doesn't have a
        media container yet, one will be created automatically.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).
            filepath (str): Path to the external media file to import.
            label (str, optional): Descriptive label for the media file.

        Returns:
            ICmMedia: The created media object with file properly linked.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If text_or_hvo or filepath is None/empty.
            FP_ParameterError: If the text does not exist, is invalid, or file not found.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>> media = project.Texts.AddMediaFile(
            ...     text,
            ...     "/home/user/audio/genesis.mp3",
            ...     label="Genesis Recording"
            ... )
            >>> print(f"Media added: {media.Hvo}")

        Notes:
            - File is copied to project's LinkedFiles/AudioVisual directory
            - Unique filename generated if collision occurs (file_1.mp3, etc.)
            - Creates ICmMedia object with proper ICmFile reference
            - Media is automatically added to text's MediaFilesOC collection

        See Also:
            GetMediaFiles, project.Media.CopyToProject
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(filepath, "filepath")

        filepath = filepath.strip()
        self._ValidateParam(filepath, "filepath")

        text_obj = self.__GetTextObject(text_or_hvo)

        with self._TransactionCM("Add media file"):
            # Create media container if needed
            if not text_obj.MediaFilesOA:
                folder_factory = self.project.project.ServiceLocator.GetService(ICmFolderFactory)
                container = folder_factory.Create()
                text_obj.MediaFilesOA = container

            # Use MediaOperations to properly copy file and create ICmFile
            # Copy file to project and get ICmFile reference
            cm_file = self.project.Media.CopyToProject(filepath, internal_subdir="AudioVisual", label=label)

            # Create ICmMedia object
            media_factory = self.project.project.ServiceLocator.GetService(ICmMediaFactory)
            media = media_factory.Create()

            # Add to text's media collection (must be done before setting properties)
            text_obj.MediaFilesOA.MediaFilesOC.Add(media)

            # Link the ICmFile to ICmMedia
            media.MediaFileRA = cm_file

            return media

    @OperationsMethod
    def GetAbbreviation(self, text_or_hvo, wsHandle=None):
        """
        Get the abbreviation for a text.

        Retrieves the text's abbreviation in the specified writing system.
        Abbreviations are used as short identifiers for texts in FLEx's UI
        and exports.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).
            wsHandle (int, optional): Writing system handle. If None, uses the
                default analysis writing system. Can also be a language tag string.

        Returns:
            str: The abbreviation in the specified writing system. Returns empty
                string if no abbreviation is set for that writing system.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>>
            >>> # Get abbreviation in default analysis WS
            >>> abbr = project.Texts.GetAbbreviation(text)
            >>> print(f"Abbreviation: {abbr}")
            >>>
            >>> # Get abbreviation in specific WS
            >>> ws_handle = project.WSHandle('en')
            >>> abbr_en = project.Texts.GetAbbreviation(text, ws_handle)

        See Also:
            GetName, SetName
        """
        text_obj = self.__GetTextObject(text_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        abbr_str = ITsString(text_obj.Abbreviation.get_String(wsHandle)).Text
        return abbr_str or ""

    @OperationsMethod
    def GetIsTranslated(self, text_or_hvo):
        """
        Check if a text's translation is marked as complete.

        Retrieves the IsTranslated boolean property indicating whether the
        text has been fully translated or not.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).

        Returns:
            bool: True if the text is marked as translated, False otherwise.

        Raises:
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>> is_translated = project.Texts.GetIsTranslated(text)
            >>> if is_translated:
            ...     print("Text translation is complete")
            ... else:
            ...     print("Text translation is incomplete")

        Notes:
            - This is a boolean property on the IText object
            - Used to track translation workflow status
            - Independent of the actual translation content
            - Can be set manually or programmatically

        See Also:
            SetIsTranslated
        """
        text_obj = self.__GetTextObject(text_or_hvo)
        return bool(text_obj.IsTranslated)

    @OperationsMethod
    def SetIsTranslated(self, text_or_hvo, value):
        """
        Mark a text as translated or untranslated.

        Sets the IsTranslated boolean property to indicate whether the text
        has been fully translated.

        Args:
            text_or_hvo: Either an IText object or its HVO (integer identifier).
            value (bool): True to mark as translated, False to mark as untranslated.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If text_or_hvo is None.
            FP_ParameterError: If the text does not exist or is invalid, or if
                value is not a boolean.

        Example:
            >>> text = list(project.Texts.GetAll())[0]
            >>>
            >>> # Mark text as translated
            >>> project.Texts.SetIsTranslated(text, True)
            >>>
            >>> # Verify
            >>> if project.Texts.GetIsTranslated(text):
            ...     print("Text is now marked as translated")
            >>>
            >>> # Mark text as untranslated
            >>> project.Texts.SetIsTranslated(text, False)

        Notes:
            - value must be a boolean (True or False)
            - Used to track translation workflow status
            - Does not affect the actual content
            - Useful for managing translation progress

        See Also:
            GetIsTranslated
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(text_or_hvo, "text_or_hvo")

        if not isinstance(value, bool):
            raise FP_ParameterError("value must be a boolean (True or False)")

        text_obj = self.__GetTextObject(text_or_hvo)
        text_obj.IsTranslated = value
