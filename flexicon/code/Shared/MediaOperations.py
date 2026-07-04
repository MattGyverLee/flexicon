#
#   MediaOperations.py
#
#   Class: MediaOperations
#          Media file operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)

import os
import shutil

# Import FLEx LCM types
from SIL.LCModel import (
    ICmFile,
    ICmFileFactory,
    ICmFolder,
    ICmFolderFactory,
    ICmObjectRepository,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# --- Media Type Enum ---


class MediaType:
    """Media file type constants."""

    UNKNOWN = 0
    AUDIO = 1
    VIDEO = 2
    IMAGE = 3


# --- MediaOperations Class ---


class MediaOperations(BaseOperations):
    """
    Provides operations for managing media files in a FLEx project.

    Media files include audio recordings, videos, and images that can be
    attached to lexical entries, pronunciations, examples, and other objects.
    This class handles both the database references (ICmFile) and file system
    operations for project media.

    This class should be accessed via FLExProject.Media property.

    Example:
        >>> project = FLExProject()
        >>> project.OpenProject("MyProject", writeEnabled=True)
        >>> # Get all media files
        >>> for media in project.Media.GetAll():
        ...     path = project.Media.GetInternalPath(media)
        ...     print(path)
        >>> # Add a new media file
        >>> media = project.Media.Create("/path/to/audio.wav")
        >>> # Check media type
        >>> if project.Media.IsAudio(media):
        ...     print("This is an audio file")
        >>> project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize MediaOperations.

        Args:
            project: FLExProject instance
        """
        super().__init__(project)

    def __WSHandle(self, wsHandle):
        """
        Internal helper to resolve writing system handle.

        Args:
            wsHandle: Writing system handle (language tag or ID), or None for default

        Returns:
            int: Resolved writing system handle
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Retrieve all media files in the FLEx project.

        This method returns an iterator over all ICmFile objects in the
        project database, allowing iteration over the complete media inventory.

        Yields:
            ICmFile: Each media file object in the project

        Example:
            >>> for media in project.Media.GetAll():
            ...     path = project.Media.GetInternalPath(media)
            ...     label = project.Media.GetLabel(media, "en")
            ...     print(f"{label}: {path}")
            Recording1: audio/recording1.wav
            Video1: videos/intro.mp4
            Photo1: images/photo1.jpg

        Notes:
            - Returns an iterator for memory efficiency with large projects
            - Media files are returned in database order
            - Use GetInternalPath() to access the file path
            - Includes all media types (audio, video, image)

        See Also:
            Find, Create, GetMediaType
        """
        return self.project.ObjectsIn(ICmObjectRepository, ICmFile)

    @OperationsMethod
    def Create(self, file_path, label=None, wsHandle=None):
        """
        Create a new media file reference in the FLEx project.

        Args:
            file_path: The file path (internal to project or external)
            label: Optional descriptive label for the media file
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmFile: The newly created media file object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If file_path is None
            FP_ParameterError: If file_path is empty

        Example:
            >>> # Create media file reference
            >>> media = project.Media.Create("LinkedFiles/AudioVisual/audio.wav")
            >>> print(project.Media.GetInternalPath(media))
            LinkedFiles/AudioVisual/audio.wav

            >>> # Create with label
            >>> media = project.Media.Create("audio/recording.wav",
            ...                               label="Speaker 1")
            >>> print(project.Media.GetLabel(media, "en"))
            Speaker 1

        Notes:
            - Creates an ICmFile object in the database
            - The file path is stored as-is (not validated)
            - File is NOT copied to project - only reference is created
            - Use CopyToProject() to import external files
            - Label is optional and can be set later with SetLabel()

        See Also:
            Delete, CopyToProject, SetInternalPath
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(file_path, "file_path")

        if not file_path or not file_path.strip():
            raise FP_ParameterError("File path cannot be empty")

        wsHandle = self.__WSHandle(wsHandle)

        # Get the factory and create the media file
        factory = self.project.project.ServiceLocator.GetService(ICmFileFactory)
        new_media = factory.Create()

        # Set the internal path
        new_media.InternalPath = file_path.strip()

        # Set label if provided
        if label:
            mkstr = TsStringUtils.MakeString(label, wsHandle)
            new_media.Description.set_String(wsHandle, mkstr)

        return new_media

    @OperationsMethod
    def Delete(self, media_or_hvo):
        """
        Delete a media file reference from the FLEx project.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO (database ID)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> if media:
            ...     project.Media.Delete(media)

            >>> # Delete by HVO
            >>> project.Media.Delete(12345)

        Warning:
            - This is a destructive operation
            - Removes the database reference only
            - Does NOT delete the actual file from disk
            - References from other objects will be removed
            - Cannot be undone

        Notes:
            - Only removes the ICmFile object from database
            - The physical file remains in the file system
            - Use os.remove() separately if you want to delete the file
            - All references to this media from other objects are cleaned up

        See Also:
            Create, Exists
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(media_or_hvo, "media_or_hvo")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        # Delete the object (this removes all references)
        # Note: LCModel handles cascading deletion of references
        self.project.cache.DomainDataByFlid.DeleteObj(media.Hvo)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, deep=False):
        """
        Duplicate a media file reference, creating a new reference to the same file.

        This method creates a copy of the media file reference (ICmFile object) in
        the database. The duplicate points to the SAME physical file - the file
        itself is NOT duplicated on disk. Use copy_file=True to create a physical
        copy of the file.

        Args:
            item_or_hvo: Either an ICmFile object or its HVO (database ID)
            deep (bool): If True, the physical file is also copied with a new name.
                If False, only the database reference is duplicated (both references
                point to the same file).

        Returns:
            ICmFile: The newly created duplicate media file reference

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If item_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> # Shallow duplicate (reference only, same file)
            >>> media = project.Media.Find("audio.wav")
            >>> duplicate = project.Media.Duplicate(media, deep=False)
            >>> print(project.Media.GetInternalPath(duplicate))
            LinkedFiles/AudioVisual/audio.wav
            >>> print(project.Media.GetLabel(duplicate, "en"))
            Speaker 1 (copy)

            >>> # Deep duplicate (copy the physical file too)
            >>> duplicate = project.Media.Duplicate(media, deep=True)
            >>> print(project.Media.GetInternalPath(duplicate))
            LinkedFiles/AudioVisual/audio_copy.wav

        Warning:
            - With deep=False, both references point to the SAME file
            - Deleting the file affects both references
            - With deep=True, the file is physically copied (doubles disk space)
            - The duplicate will have a " (copy)" suffix in the label

        Notes:
            - Duplicated reference is added to the project database
            - New GUID is auto-generated for the duplicate
            - Internal path is copied (or modified if deep=True)
            - Label is copied with " (copy)" suffix
            - With deep=False, both references share the same physical file
            - With deep=True, a new file is created with "_copy" suffix

        See Also:
            Create, Delete, CopyToProject
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Resolve to media object
        if isinstance(item_or_hvo, int):
            source_media = self.project.Object(item_or_hvo)
            if not isinstance(source_media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            source_media = item_or_hvo

        # Get source properties
        wsHandle = self.__WSHandle(None)
        internal_path = self.GetInternalPath(source_media)
        label = self.GetLabel(source_media, wsHandle)

        # Create unique label by appending " (copy)"
        new_label = f"{label} (copy)" if label else "Media (copy)"

        # Handle deep copy (copy the physical file)
        new_path = internal_path
        if deep and internal_path:
            # Get the external path
            external_path = self.GetExternalPath(source_media)
            if os.path.exists(external_path):
                # Create new filename with "_copy" suffix
                dir_name = os.path.dirname(internal_path)
                file_name = os.path.basename(internal_path)
                name_base, ext = os.path.splitext(file_name)
                new_file_name = f"{name_base}_copy{ext}"
                new_path = os.path.join(dir_name, new_file_name)

                # Ensure uniqueness
                counter = 1
                while True:
                    new_external_path = os.path.join(os.path.dirname(external_path), os.path.basename(new_path))
                    if not os.path.exists(new_external_path):
                        break
                    new_file_name = f"{name_base}_copy{counter}{ext}"
                    new_path = os.path.join(dir_name, new_file_name)
                    counter += 1

                # Copy the file
                try:
                    shutil.copy2(external_path, new_external_path)
                except Exception as e:
                    logger.warning(f"Failed to copy physical file: {e}")
                    # Continue with shallow copy if file copy fails
                    new_path = internal_path

        # Create the new media reference
        new_media = self.Create(new_path, label=new_label, wsHandle=wsHandle)

        # Copy full Description MultiString (all writing systems)
        # Create() only sets a single-WS label; CopyAlternatives preserves all WS
        if hasattr(source_media, "Description") and source_media.Description:
            new_media.Description.CopyAlternatives(source_media.Description)

        return new_media

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a media file.

        Args:
            item: The ICmFile object.

        Returns:
            dict: Dictionary of syncable properties with their values.

        Example:
            >>> props = project.Media.GetSyncableProperties(media)
            >>> print(props['InternalPath'])
            'LinkedFiles/AudioVisual/audio.wav'
            >>> print(props['Description'])
            {'en': 'Speaker 1 recording'}

        Notes:
            - InternalPath is a string property
            - Description is a MultiString property (dict with WS keys)
            - Does NOT include file content or metadata
        """
        props = {}

        # String property - InternalPath
        if hasattr(item, "InternalPath") and item.InternalPath:
            props["InternalPath"] = item.InternalPath

        # MultiString property - Description
        if hasattr(item, "Description") and item.Description:
            props["Description"] = self.project.GetMultiStringDict(item.Description)

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two media files for differences.

        Args:
            item1: First media object (from project 1)
            item2: Second media object (from project 2)
            ops1: Optional MediaOperations instance for project 1 (defaults to self)
            ops2: Optional MediaOperations instance for project 2 (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
                - is_different (bool): True if media files differ, False if identical
                - differences_dict (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> is_diff, diffs = ops1.CompareTo(media1, media2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} != {val2}")

        Notes:
            - Compares InternalPath and Description
            - MultiStrings are compared across all writing systems
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
    def Find(self, filename):
        """
        Find a media file by its filename (internal path).

        Args:
            filename: The filename or path to search for (case-sensitive)

        Returns:
            ICmFile or None: The media file object if found, None otherwise

        Raises:
            FP_NullParameterError: If filename is None

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> if media:
            ...     print(f"Found: {project.Media.GetInternalPath(media)}")
            Found: LinkedFiles/AudioVisual/audio.wav

            >>> # Search with full path
            >>> media = project.Media.Find("LinkedFiles/AudioVisual/audio.wav")

        Notes:
            - Returns first match only
            - Search is case-sensitive
            - Searches InternalPath field
            - Can search by filename or full path
            - Returns None if not found (doesn't raise exception)
            - Matches exact path or ending path component

        See Also:
            Exists, GetAll, GetInternalPath
        """
        self._ValidateParam(filename, "filename")

        if not filename or not filename.strip():
            return None

        filename = filename.strip()

        # Search through all media files
        for media in self.GetAll():
            internal_path = media.InternalPath or ""
            # Match exact path or filename at end of path
            if internal_path == filename or internal_path.endswith(os.sep + filename):
                return media

        return None

    @OperationsMethod
    def Exists(self, filename):
        """
        Check if a media file exists in the FLEx project.

        Args:
            filename: The filename or path to check

        Returns:
            bool: True if the media file exists, False otherwise

        Example:
            >>> if project.Media.Exists("audio.wav"):
            ...     media = project.Media.Find("audio.wav")
            ... else:
            ...     media = project.Media.Create("audio.wav")

        Notes:
            - Search is case-sensitive
            - Returns False for empty or whitespace-only filenames
            - Use Find() to get the actual media object

        See Also:
            Find, Create
        """
        if not filename or not filename.strip():
            return False

        return self.Find(filename) is not None

    # --- File Properties ---

    @OperationsMethod
    def GetInternalPath(self, media_or_hvo):
        """
        Get the internal path of a media file.

        The internal path is the file location relative to the project's
        LinkedFiles directory or an absolute path.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            str: The internal path (empty string if not set)

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> path = project.Media.GetInternalPath(media)
            >>> print(path)
            LinkedFiles/AudioVisual/audio.wav

        Notes:
            - Returns empty string if path not set
            - Path may be relative or absolute
            - Use GetExternalPath() to resolve to full system path
            - Path uses forward slashes on all platforms

        See Also:
            SetInternalPath, GetExternalPath
        """
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        return media.InternalPath or ""

    @OperationsMethod
    def GetExternalPath(self, media_or_hvo):
        """
        Get the external (absolute) path of a media file.

        This resolves the internal path to an absolute file system path,
        relative to the project's LinkedFiles directory if needed.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            str: The absolute file path (may not exist on disk)

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> path = project.Media.GetExternalPath(media)
            >>> print(path)
            C:/Users/Me/Documents/FieldWorks/Projects/MyProject/LinkedFiles/AudioVisual/audio.wav

            >>> # Check if file exists on disk
            >>> import os
            >>> if os.path.exists(path):
            ...     print("File exists")

        Notes:
            - Returns absolute path, resolved from internal path
            - If internal path is absolute, returns it as-is
            - If relative, resolves relative to project LinkedFiles directory
            - Does NOT verify that file exists on disk
            - Use IsValid() to check if file exists

        See Also:
            GetInternalPath, IsValid
        """
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        internal_path = media.InternalPath or ""

        # If already absolute, return as-is
        if os.path.isabs(internal_path):
            return internal_path

        # Otherwise, resolve relative to project LinkedFiles directory
        # Note: This assumes project has a LinkedFiles directory
        # In actual FLEx, this would use the project's LinkedFilesRootDir
        if hasattr(self.project.project, "LinkedFilesRootDir"):
            linked_files_dir = self.project.project.LinkedFilesRootDir
            return os.path.join(linked_files_dir, internal_path)

        # Fallback: return internal path if we can't resolve
        return internal_path

    @OperationsMethod
    def SetInternalPath(self, media_or_hvo, path):
        """
        Set the internal path of a media file.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO
            path: The new internal path to set

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If media_or_hvo or path is None
            FP_ParameterError: If path is empty or media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> project.Media.SetInternalPath(media,
            ...                                "LinkedFiles/AudioVisual/new_audio.wav")
            >>> print(project.Media.GetInternalPath(media))
            LinkedFiles/AudioVisual/new_audio.wav

        Notes:
            - Updates the internal path reference
            - Does NOT move or rename the actual file
            - Path can be relative or absolute
            - Use forward slashes for cross-platform compatibility

        See Also:
            GetInternalPath, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(media_or_hvo, "media_or_hvo")
        self._ValidateParam(path, "path")

        if not path or not path.strip():
            raise FP_ParameterError("Path cannot be empty")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        media.InternalPath = path.strip()

    @OperationsMethod
    def RenameMediaFile(self, media_or_hvo, new_filename):
        """
        Rename a media file on disk and update the database reference.

        This is an atomic operation that:
        1. Validates parameters and checks write permissions
        2. Gets current internal and external paths
        3. Constructs new paths with new filename
        4. Renames the physical file in LinkedFiles directory
        5. Updates the InternalPath in the database
        6. Handles filename conflicts (adds suffix if needed)

        Args:
            media_or_hvo: Either an ICmFile object or its HVO (database ID)
            new_filename: New filename (without path, just filename.ext)

        Returns:
            str: The actual new internal path (may differ if conflict occurred)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If media_or_hvo or new_filename is None
            FP_ParameterError: If media doesn't exist, filename is invalid,
                or contains path separators
            OSError: If file doesn't exist or rename operation fails

        Example:
            >>> # Rename an audio file
            >>> media = project.Media.Find("LinkedFiles/AudioVisual/old_name.wav")
            >>> new_path = project.Media.RenameMediaFile(media, "new_name.wav")
            >>> print(new_path)
            LinkedFiles/AudioVisual/new_name.wav

            >>> # Handles conflicts automatically
            >>> media2 = project.Media.Find("LinkedFiles/AudioVisual/temp.wav")
            >>> new_path = project.Media.RenameMediaFile(media2, "new_name.wav")
            >>> print(new_path)
            LinkedFiles/AudioVisual/new_name_1.wav

            >>> # Rename by HVO
            >>> new_path = project.Media.RenameMediaFile(12345, "recording.wav")

        Warning:
            - Renames the physical file on disk
            - This is a destructive operation
            - If new filename already exists, adds _1, _2, etc. suffix
            - Cannot be undone

        Notes:
            - Preserves the subdirectory (AudioVisual, Pictures, etc.)
            - Only changes the filename, not the directory path
            - Handles filename conflicts by adding _1, _2, etc.
            - Updates InternalPath in database automatically
            - Old file must exist on disk
            - New filename cannot contain path separators (/ or \\)
            - Validates that new_filename is just a filename, not a path

        See Also:
            SetInternalPath, CopyToProject, GetExternalPath, GetInternalPath
        """
        # Check write permissions
        self._EnsureWriteEnabled()

        # Validate parameters
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        self._ValidateParam(new_filename, "new_filename")

        if not new_filename or not new_filename.strip():
            raise FP_ParameterError("New filename cannot be empty")

        new_filename = new_filename.strip()

        # Validate that new_filename is just a filename, not a path
        if os.sep in new_filename or "/" in new_filename or "\\" in new_filename:
            raise FP_ParameterError(f"New filename cannot contain path separators: {new_filename}")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        # Get current paths
        old_internal_path = self.GetInternalPath(media)
        if not old_internal_path:
            raise FP_ParameterError("Media file has no internal path set")

        old_external_path = self.GetExternalPath(media)

        # Check if old file exists
        if not os.path.exists(old_external_path):
            logger.error(f"File not found: {old_external_path}")
            raise FP_ParameterError(f"File not found: {old_external_path}")

        # Construct new path (preserve directory)
        dir_name = os.path.dirname(old_internal_path)
        new_internal_path = os.path.join(dir_name, new_filename)

        # Get the external directory path for constructing new external path
        old_external_dir = os.path.dirname(old_external_path)
        new_external_path = os.path.join(old_external_dir, new_filename)

        # Handle conflicts - check if target file already exists
        if os.path.exists(new_external_path):
            base, ext = os.path.splitext(new_filename)
            counter = 1
            while True:
                new_filename_conflict = f"{base}_{counter}{ext}"
                new_internal_path = os.path.join(dir_name, new_filename_conflict)
                new_external_path = os.path.join(old_external_dir, new_filename_conflict)
                if not os.path.exists(new_external_path):
                    break
                counter += 1

            logger.warning(f"File {new_filename} already exists, using {new_filename_conflict}")

        # Rename the physical file
        try:
            os.rename(old_external_path, new_external_path)
            logger.info(f"Renamed media file: {old_external_path} -> {new_external_path}")
        except OSError as e:
            logger.error(f"Failed to rename file: {e}")
            raise

        # Update database reference
        try:
            self.SetInternalPath(media, new_internal_path)
            logger.info(f"Updated internal path: {old_internal_path} -> {new_internal_path}")
        except Exception as e:
            # If database update fails, try to roll back the file rename
            logger.error(f"Failed to update database, attempting rollback: {e}")
            try:
                os.rename(new_external_path, old_external_path)
                logger.info(f"Rolled back file rename")
            except OSError as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
            raise

        return new_internal_path

    @OperationsMethod
    def GetLabel(self, media_or_hvo, wsHandle=None):
        """
        Get the label/description of a media file.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The label text (empty string if not set)

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> label = project.Media.GetLabel(media, "en")
            >>> print(label)
            Speaker 1 pronunciation

            >>> # Get in specific writing system
            >>> label_fr = project.Media.GetLabel(media, "fr")

        Notes:
            - Returns empty string if label not set
            - Returns empty string if label not set in specified writing system
            - Labels are multi-string (can have different text per WS)
            - Default writing system is analysis WS

        See Also:
            SetLabel
        """
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        wsHandle = self.__WSHandle(wsHandle)

        # Get the label/description string
        if hasattr(media, "Description"):
            label = ITsString(media.Description.get_String(wsHandle)).Text
            return label or ""
        return ""

    @OperationsMethod
    def SetLabel(self, media_or_hvo, text, wsHandle=None):
        """
        Set the label/description of a media file.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO
            text: The label text to set
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If media_or_hvo or text is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> project.Media.SetLabel(media, "Speaker 1 pronunciation", "en")
            >>> print(project.Media.GetLabel(media, "en"))
            Speaker 1 pronunciation

            >>> # Set in multiple writing systems
            >>> project.Media.SetLabel(media, "Pronunciation locuteur 1", "fr")

        Notes:
            - Text can be empty string to clear the label
            - Label is stored in the specified writing system
            - Does not affect other writing systems
            - Labels help identify media files in the UI

        See Also:
            GetLabel
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(media_or_hvo, "media_or_hvo")
        self._ValidateParam(text, "text")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        wsHandle = self.__WSHandle(wsHandle)

        # Set the label/description string
        if hasattr(media, "Description"):
            mkstr = TsStringUtils.MakeString(text, wsHandle)
            media.Description.set_String(wsHandle, mkstr)

    # --- Media Type Detection ---

    @OperationsMethod
    def GetMediaType(self, media_or_hvo):
        """
        Get the media type (audio/video/image) based on file extension.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            int: Media type constant (MediaType.AUDIO, VIDEO, IMAGE, or UNKNOWN)

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> media_type = project.Media.GetMediaType(media)
            >>> if media_type == MediaType.AUDIO:
            ...     print("This is an audio file")
            This is an audio file

            >>> # Check type name
            >>> type_names = {MediaType.AUDIO: "Audio",
            ...               MediaType.VIDEO: "Video",
            ...               MediaType.IMAGE: "Image",
            ...               MediaType.UNKNOWN: "Unknown"}
            >>> print(type_names[media_type])
            Audio

        Notes:
            - Detection is based on file extension only
            - Audio extensions: .wav, .mp3, .ogg, .wma, .m4a, .flac
            - Video extensions: .mp4, .avi, .mov, .wmv, .mpg, .mpeg
            - Image extensions: .jpg, .jpeg, .png, .gif, .bmp, .tif, .tiff
            - Returns MediaType.UNKNOWN for unrecognized extensions
            - Does not verify actual file format

        See Also:
            IsAudio, IsVideo, IsImage
        """
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        internal_path = media.InternalPath or ""
        if not internal_path:
            return MediaType.UNKNOWN

        # Get file extension
        _, ext = os.path.splitext(internal_path.lower())

        # Define media type by extension
        audio_exts = {".wav", ".mp3", ".ogg", ".wma", ".m4a", ".flac", ".aac", ".opus"}
        video_exts = {".mp4", ".avi", ".mov", ".wmv", ".mpg", ".mpeg", ".mkv", ".webm"}
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".svg"}

        if ext in audio_exts:
            return MediaType.AUDIO
        elif ext in video_exts:
            return MediaType.VIDEO
        elif ext in image_exts:
            return MediaType.IMAGE
        else:
            return MediaType.UNKNOWN

    @OperationsMethod
    def IsAudio(self, media_or_hvo):
        """
        Check if a media file is an audio file.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            bool: True if the file is audio, False otherwise

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> if project.Media.IsAudio(media):
            ...     print("This is an audio file")
            This is an audio file

            >>> # Process all audio files
            >>> for media in project.Media.GetAll():
            ...     if project.Media.IsAudio(media):
            ...         # Process audio file
            ...         pass

        Notes:
            - Detection is based on file extension
            - Audio extensions: .wav, .mp3, .ogg, .wma, .m4a, .flac, .aac, .opus
            - Does not verify actual file format

        See Also:
            GetMediaType, IsVideo, IsImage
        """
        return self.GetMediaType(media_or_hvo) == MediaType.AUDIO

    @OperationsMethod
    def IsVideo(self, media_or_hvo):
        """
        Check if a media file is a video file.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            bool: True if the file is video, False otherwise

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("intro.mp4")
            >>> if project.Media.IsVideo(media):
            ...     print("This is a video file")
            This is a video file

            >>> # Count video files
            >>> video_count = sum(1 for m in project.Media.GetAll()
            ...                   if project.Media.IsVideo(m))
            >>> print(f"Total videos: {video_count}")

        Notes:
            - Detection is based on file extension
            - Video extensions: .mp4, .avi, .mov, .wmv, .mpg, .mpeg, .mkv, .webm
            - Does not verify actual file format

        See Also:
            GetMediaType, IsAudio, IsImage
        """
        return self.GetMediaType(media_or_hvo) == MediaType.VIDEO

    @OperationsMethod
    def IsImage(self, media_or_hvo):
        """
        Check if a media file is an image file.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            bool: True if the file is image, False otherwise

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("photo.jpg")
            >>> if project.Media.IsImage(media):
            ...     print("This is an image file")
            This is an image file

            >>> # Get all image files
            >>> images = [m for m in project.Media.GetAll()
            ...           if project.Media.IsImage(m)]

        Notes:
            - Detection is based on file extension
            - Image extensions: .jpg, .jpeg, .png, .gif, .bmp, .tif, .tiff, .svg
            - Does not verify actual file format

        See Also:
            GetMediaType, IsAudio, IsVideo
        """
        return self.GetMediaType(media_or_hvo) == MediaType.IMAGE

    # --- Usage Tracking ---

    @OperationsMethod
    def GetOwners(self, media_or_hvo):
        """
        Get all objects that reference this media file.

        Returns objects (entries, pronunciations, examples, etc.) that
        have this media file attached.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            list: List of objects referencing this media file (empty if none)

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> owners = project.Media.GetOwners(media)
            >>> for owner in owners:
            ...     print(f"Owner: {owner.ClassName} (HVO: {owner.Hvo})")
            Owner: LexPronunciation (HVO: 12345)
            Owner: LexExampleSentence (HVO: 67890)

        Notes:
            - Returns all objects with references to this media
            - Common owner types: LexPronunciation, LexExampleSentence, etc.
            - Empty list if media is not used anywhere
            - Owners can be of various types
            - Use owner.ClassName to determine type

        See Also:
            GetOwnerCount
        """
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        # Get all incoming references
        # ICmFile objects track their owners via the Owner property
        owners = []
        if hasattr(media, "Owner") and media.Owner:
            owners.append(media.Owner)

        return owners

    @OperationsMethod
    def GetOwnerCount(self, media_or_hvo):
        """
        Get the count of objects referencing this media file.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            int: Number of objects using this media file

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> count = project.Media.GetOwnerCount(media)
            >>> print(f"Used by {count} objects")
            Used by 3 objects

            >>> # Check if media is orphaned
            >>> if project.Media.GetOwnerCount(media) == 0:
            ...     print("This media file is not used anywhere")

        Notes:
            - Returns 0 if media is not used anywhere
            - More efficient than len(GetOwners()) for large projects
            - Useful for finding orphaned media files

        See Also:
            GetOwners
        """
        return len(self.GetOwners(media_or_hvo))

    # --- Utility Methods ---

    @OperationsMethod
    def CopyToProject(self, external_path, internal_subdir="AudioVisual", label=None, wsHandle=None):
        """
        Copy an external file into the project's LinkedFiles directory
        and create a media reference.

        Args:
            external_path: Path to the external file to import
            internal_subdir: Subdirectory within LinkedFiles (default: "AudioVisual")
            label: Optional descriptive label for the media file
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmFile: The created media file object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If external_path is None
            FP_ParameterError: If external_path is empty or file doesn't exist

        Example:
            >>> # Import an external audio file
            >>> media = project.Media.CopyToProject(
            ...     "/home/user/recordings/audio.wav",
            ...     internal_subdir="AudioVisual",
            ...     label="Speaker 1"
            ... )
            >>> print(project.Media.GetInternalPath(media))
            LinkedFiles/AudioVisual/audio.wav

            >>> # Import an image
            >>> photo = project.Media.CopyToProject(
            ...     "/home/user/photos/item.jpg",
            ...     internal_subdir="Pictures"
            ... )

        Notes:
            - Copies the file to project's LinkedFiles directory
            - Creates the subdirectory if it doesn't exist
            - Preserves the original filename
            - If file already exists in destination, appends number
            - Creates ICmFile reference with relative path
            - Returns None if LinkedFilesRootDir not available

        See Also:
            Create, SetInternalPath
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(external_path, "external_path")

        if not external_path or not external_path.strip():
            raise FP_ParameterError("External path cannot be empty")

        external_path = external_path.strip()

        if not os.path.exists(external_path):
            raise FP_ParameterError(f"File not found: {external_path}")

        # Get LinkedFiles directory
        if not hasattr(self.project.project, "LinkedFilesRootDir"):
            # If LinkedFilesRootDir not available, create reference only
            logger.warning("LinkedFilesRootDir not available, creating reference without copying")
            return self.Create(external_path, label, wsHandle)

        linked_files_dir = self.project.project.LinkedFilesRootDir
        target_dir = os.path.join(linked_files_dir, internal_subdir)

        # Create target directory if it doesn't exist
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # Get filename and create target path
        filename = os.path.basename(external_path)
        target_path = os.path.join(target_dir, filename)

        # If file exists, append number
        if os.path.exists(target_path):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(target_dir, f"{base}_{counter}{ext}")):
                counter += 1
            filename = f"{base}_{counter}{ext}"
            target_path = os.path.join(target_dir, filename)

        # Copy the file
        shutil.copy2(external_path, target_path)

        # Create internal path (relative to LinkedFiles)
        internal_path = os.path.join("LinkedFiles", internal_subdir, filename)

        # Create media reference
        return self.Create(internal_path, label, wsHandle)

    @OperationsMethod
    def IsValid(self, media_or_hvo):
        """
        Check if a media file's referenced file exists on disk.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            bool: True if the file exists on disk, False otherwise

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> if project.Media.IsValid(media):
            ...     print("File exists on disk")
            ... else:
            ...     print("File is missing!")

            >>> # Find all missing media files
            >>> for media in project.Media.GetAll():
            ...     if not project.Media.IsValid(media):
            ...         path = project.Media.GetInternalPath(media)
            ...         print(f"Missing: {path}")

        Notes:
            - Checks if the actual file exists on the file system
            - Uses GetExternalPath() to resolve full path
            - Returns False if path cannot be resolved
            - Returns False if path is empty
            - Useful for finding broken media references

        See Also:
            GetExternalPath, GetInternalPath
        """
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        try:
            external_path = self.GetExternalPath(media_or_hvo)
            if not external_path:
                return False
            return os.path.exists(external_path)
        except (OSError, FP_ParameterError, FP_NullParameterError):
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking media file existence: {e}")
            return False

    @OperationsMethod
    def GetGuid(self, media_or_hvo):
        """
        Get the GUID (Globally Unique Identifier) of a media file.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            System.Guid: The media file's GUID

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> guid = project.Media.GetGuid(media)
            >>> print(guid)
            a1b2c3d4-e5f6-7890-abcd-ef1234567890

            >>> # Get as string
            >>> guid_str = str(guid)
            >>> print(guid_str)
            a1b2c3d4-e5f6-7890-abcd-ef1234567890

            >>> # Use GUID to retrieve media later
            >>> media2 = project.Object(guid)
            >>> print(project.Media.GetInternalPath(media2))
            audio.wav

        Notes:
            - GUIDs are unique across all FLEx projects
            - GUIDs are persistent (don't change)
            - Useful for linking media across projects
            - Can be used with FLExProject.Object() to retrieve media

        See Also:
            FLExProject.Object
        """
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        # Resolve to media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
            if not isinstance(media, ICmFile):
                raise FP_ParameterError("HVO does not refer to a media file")
        else:
            media = media_or_hvo

        return media.Guid

    @OperationsMethod
    def GetHvo(self, media):
        """
        Get the HVO (database ID) of a media file.

        Args:
            media: An ICmFile object

        Returns:
            int: The media file's HVO

        Raises:
            FP_NullParameterError: If media is None

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> hvo = project.Media.GetHvo(media)
            >>> print(hvo)
            12345

            >>> # Use HVO to retrieve media later
            >>> media2 = project.Object(hvo)
            >>> print(project.Media.GetInternalPath(media2))
            audio.wav

        Notes:
            - HVOs are database IDs (integers)
            - HVOs are unique within a project
            - HVOs may change if database is rebuilt
            - Prefer GUIDs for persistent references

        See Also:
            GetGuid, FLExProject.Object
        """
        self._ValidateParam(media, "media")

        return media.Hvo

    @OperationsMethod
    def GetFileSize(self, media_or_hvo):
        """
        Get the file size of a media file in bytes.

        Args:
            media_or_hvo: Either an ICmFile object or its HVO

        Returns:
            int: File size in bytes, or -1 if file doesn't exist

        Raises:
            FP_NullParameterError: If media_or_hvo is None
            FP_ParameterError: If media doesn't exist

        Example:
            >>> media = project.Media.Find("audio.wav")
            >>> size = project.Media.GetFileSize(media)
            >>> print(f"File size: {size / 1024:.2f} KB")
            File size: 1234.56 KB

            >>> # Get size in human-readable format
            >>> if size > 1024 * 1024:
            ...     print(f"{size / (1024 * 1024):.2f} MB")
            ... elif size > 1024:
            ...     print(f"{size / 1024:.2f} KB")
            ... else:
            ...     print(f"{size} bytes")

        Notes:
            - Returns -1 if file doesn't exist on disk
            - Uses GetExternalPath() to resolve file location
            - Size is in bytes
            - Returns actual file size from file system

        See Also:
            IsValid, GetExternalPath
        """
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        try:
            external_path = self.GetExternalPath(media_or_hvo)
            if not external_path or not os.path.exists(external_path):
                return -1
            return os.path.getsize(external_path)
        except (OSError, FP_ParameterError, FP_NullParameterError):
            return -1
        except Exception as e:
            logger.warning(f"Unexpected error getting media file size: {e}")
            return -1

    @OperationsMethod
    def GetAllByType(self, media_type):
        """
        Get all media files of a specific type.

        Args:
            media_type: Media type constant (MediaType.AUDIO, VIDEO, IMAGE)

        Yields:
            ICmFile: Each media file of the specified type

        Raises:
            FP_ParameterError: If media_type is invalid

        Example:
            >>> # Get all audio files
            >>> for media in project.Media.GetAllByType(MediaType.AUDIO):
            ...     path = project.Media.GetInternalPath(media)
            ...     print(f"Audio: {path}")
            Audio: audio1.wav
            Audio: audio2.mp3

            >>> # Count videos
            >>> video_count = sum(1 for _ in project.Media.GetAllByType(MediaType.VIDEO))
            >>> print(f"Total videos: {video_count}")

        Notes:
            - Returns an iterator for memory efficiency
            - Valid types: MediaType.AUDIO, VIDEO, IMAGE, UNKNOWN
            - Uses GetMediaType() for detection
            - Detection is based on file extension

        See Also:
            GetAll, GetMediaType, IsAudio, IsVideo, IsImage
        """
        if media_type not in (MediaType.AUDIO, MediaType.VIDEO, MediaType.IMAGE, MediaType.UNKNOWN):
            raise FP_ParameterError(
                f"Invalid media type: {media_type}. " f"Use MediaType.AUDIO, VIDEO, IMAGE, or UNKNOWN"
            )

        for media in self.GetAll():
            if self.GetMediaType(media) == media_type:
                yield media

    @OperationsMethod
    def GetOrphanedMedia(self):
        """
        Get all media files that are not referenced by any object.

        Yields:
            ICmFile: Each orphaned media file

        Example:
            >>> # Find orphaned media files
            >>> orphaned = list(project.Media.GetOrphanedMedia())
            >>> print(f"Found {len(orphaned)} orphaned media files")
            Found 5 orphaned media files

            >>> # Delete orphaned media
            >>> for media in project.Media.GetOrphanedMedia():
            ...     path = project.Media.GetInternalPath(media)
            ...     print(f"Deleting orphaned: {path}")
            ...     project.Media.Delete(media)

        Notes:
            - Returns an iterator for memory efficiency
            - Orphaned media has no owners (GetOwnerCount() == 0)
            - Useful for cleaning up unused media
            - Consider backing up before deleting orphaned media

        See Also:
            GetOwnerCount, GetOwners, Delete
        """
        for media in self.GetAll():
            if self.GetOwnerCount(media) == 0:
                yield media
