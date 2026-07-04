#
#   ProjectSettingsOperations.py
#
#   Class: ProjectSettingsOperations
#          Project-level settings and configuration operations for FieldWorks
#          Language Explorer projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)

# Import FLEx LCM types
from SIL.LCModel import (
    ILangProject,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils
from SIL.WritingSystems import WritingSystemDefinition  # Fixed: was IWritingSystemDefinition

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
    FP_WritingSystemError,
)
from ..BaseOperations import BaseOperations, OperationsMethod


class ProjectSettingsOperations(BaseOperations):
    """
    This class provides operations for managing project-level settings and
    configuration in a FieldWorks project.

    Project settings include metadata (name, description), language settings
    (vernacular and analysis writing systems), interface preferences, default
    fonts, and file paths for external resources.

    This class should be accessed via FLExProject.ProjectSettings property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get project information
        name = project.ProjectSettings.GetProjectName()
        description = project.ProjectSettings.GetDescription("en")
        print(f"Project: {name}")
        print(f"Description: {description}")

        # Set project metadata
        project.ProjectSettings.SetProjectName("My Linguistic Study")
        project.ProjectSettings.SetDescription(
            "Documentation of endangered language", "en"
        )

        # Language settings
        vern_wss = project.ProjectSettings.GetVernacularWSs()
        anal_wss = project.ProjectSettings.GetAnalysisWSs()
        print(f"Vernacular WSs: {vern_wss}")
        print(f"Analysis WSs: {anal_wss}")

        # Set default writing systems
        project.ProjectSettings.SetDefaultVernacular("qaa-x-kal")
        project.ProjectSettings.SetDefaultAnalysis("en")

        # Configure default fonts
        project.ProjectSettings.SetDefaultFont("qaa-x-kal", "Charis SIL")
        project.ProjectSettings.SetDefaultFontSize("qaa-x-kal", 14)

        # External file paths
        linked_path = project.ProjectSettings.GetLinkedFilesRootDir()
        print(f"Linked files: {linked_path}")

        # Metadata
        created = project.ProjectSettings.GetDateCreated()
        modified = project.ProjectSettings.GetDateModified()
        print(f"Created: {created}")
        print(f"Last modified: {modified}")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ProjectSettingsOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Project Information ---

    @OperationsMethod
    def GetProjectName(self):
        """
        Get the project name.

        Returns:
            str: The name of the project

        Example:
            >>> name = project.ProjectSettings.GetProjectName()
            >>> print(f"Project name: {name}")
            Project name: Kalaba Documentation

        Notes:
            - Returns the display name of the project
            - This is different from the project filename
            - Empty string if no name is set

        See Also:
            SetProjectName, GetDescription
        """
        if hasattr(self.project.lp, "Name") and self.project.lp.Name:
            ts = ITsString(self.project.lp.Name)
            return ts.Text if ts else ""
        return ""

    @OperationsMethod
    def SetProjectName(self, name):
        """
        Set the project name.

        Args:
            name (str): The new project name

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If name is None
            FP_ParameterError: If name is empty

        Example:
            >>> project.ProjectSettings.SetProjectName("Kalaba Documentation")
            >>> name = project.ProjectSettings.GetProjectName()
            >>> print(name)
            Kalaba Documentation

        Notes:
            - Sets the display name of the project
            - Does not change the project filename
            - Name should be descriptive and meaningful

        See Also:
            GetProjectName, SetDescription
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Project name cannot be empty")

        # Get default analysis writing system for the name
        ws_handle = self.project.project.DefaultAnalWs
        ts = TsStringUtils.MakeString(name, ws_handle)
        self.project.lp.Name = ts

    @OperationsMethod
    def GetDescription(self, ws_handle_or_tag=None):
        """
        Get the project description in the specified writing system.

        Args:
            ws_handle_or_tag: Writing system handle (int), language tag (str),
                or None for default analysis WS

        Returns:
            str: The project description text

        Raises:
            FP_WritingSystemError: If writing system not found

        Example:
            >>> # Get in default analysis WS
            >>> desc = project.ProjectSettings.GetDescription()
            >>> print(desc)
            Documentation of endangered Kalaba language

            >>> # Get in specific writing system
            >>> desc_en = project.ProjectSettings.GetDescription("en")
            >>> desc_fr = project.ProjectSettings.GetDescription("fr")

        Notes:
            - Returns empty string if no description set
            - Description can be set in multiple writing systems
            - Useful for multilingual project documentation

        See Also:
            SetDescription, GetProjectName
        """
        ws_handle = self._ResolveWSHandle(ws_handle_or_tag)

        if hasattr(self.project.lp, "Description") and self.project.lp.Description:
            ts = ITsString(self.project.lp.Description.get_String(ws_handle))
            return ts.Text if ts else ""
        return ""

    @OperationsMethod
    def SetDescription(self, description, ws_handle_or_tag=None):
        """
        Set the project description in the specified writing system.

        Args:
            description (str): The description text
            ws_handle_or_tag: Writing system handle (int), language tag (str),
                or None for default analysis WS

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If description is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> # Set in default analysis WS
            >>> project.ProjectSettings.SetDescription(
            ...     "Documentation of endangered Kalaba language"
            ... )

            >>> # Set in multiple languages
            >>> project.ProjectSettings.SetDescription(
            ...     "Documentation of endangered Kalaba language", "en"
            ... )
            >>> project.ProjectSettings.SetDescription(
            ...     "Documentation de la langue Kalaba en danger", "fr"
            ... )

        Notes:
            - Can set different descriptions in different writing systems
            - Empty string clears the description
            - Description is used in project properties and reports

        See Also:
            GetDescription, SetProjectName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(description, "description")

        ws_handle = self._ResolveWSHandle(ws_handle_or_tag)

        # Ensure Description MultiString exists
        if not self.project.lp.Description:
            # Description should exist, but handle gracefully
            logger.warning("Description MultiString not initialized")
            return

        ts = TsStringUtils.MakeString(description, ws_handle)
        self.project.lp.Description.set_String(ws_handle, ts)

    # --- Language Settings ---

    @OperationsMethod
    def GetVernacularWSs(self):
        """
        Get the list of vernacular writing system tags.

        Returns:
            list: List of vernacular writing system language tags (e.g., ["qaa-x-kal"])

        Example:
            >>> vern_wss = project.ProjectSettings.GetVernacularWSs()
            >>> print("Vernacular writing systems:")
            >>> for ws_tag in vern_wss:
            ...     print(f"  - {ws_tag}")
            Vernacular writing systems:
              - qaa-x-kal
              - qaa-x-kal-fonipa

        Notes:
            - Returns list of language tags, not WS objects
            - These are the writing systems for the object language(s)
            - Use WritingSystems operations to get full WS details
            - Empty list if no vernacular writing systems configured

        See Also:
            GetAnalysisWSs, SetDefaultVernacular
        """
        if hasattr(self.project.lp, "CurVernWss") and self.project.lp.CurVernWss:
            return self.project.lp.CurVernWss.split()
        return []

    @OperationsMethod
    def GetAnalysisWSs(self):
        """
        Get the list of analysis writing system tags.

        Returns:
            list: List of analysis writing system language tags (e.g., ["en", "fr"])

        Example:
            >>> anal_wss = project.ProjectSettings.GetAnalysisWSs()
            >>> print("Analysis writing systems:")
            >>> for ws_tag in anal_wss:
            ...     print(f"  - {ws_tag}")
            Analysis writing systems:
              - en
              - fr
              - es

        Notes:
            - Returns list of language tags, not WS objects
            - These are the writing systems for metadata and analysis
            - Use WritingSystems operations to get full WS details
            - Empty list if no analysis writing systems configured

        See Also:
            GetVernacularWSs, SetDefaultAnalysis
        """
        if hasattr(self.project.lp, "CurAnalysisWss") and self.project.lp.CurAnalysisWss:
            return self.project.lp.CurAnalysisWss.split()
        return []

    @OperationsMethod
    def SetDefaultVernacular(self, ws_handle_or_tag):
        """
        Set the default vernacular writing system.

        Args:
            ws_handle_or_tag: Writing system handle (int) or language tag (str)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws_handle_or_tag is None
            FP_WritingSystemError: If writing system not found
            FP_ParameterError: If WS is not in vernacular list

        Example:
            >>> # Set by language tag
            >>> project.ProjectSettings.SetDefaultVernacular("qaa-x-kal")

            >>> # Verify the change
            >>> default = project.WritingSystems.GetDefaultVernacular()
            >>> tag = project.WritingSystems.GetLanguageTag(default)
            >>> print(f"Default vernacular: {tag}")
            Default vernacular: qaa-x-kal

        Notes:
            - Writing system must be in the vernacular list
            - This is the primary WS for lexical entries
            - Used as fallback when no specific WS is specified

        See Also:
            SetDefaultAnalysis, GetVernacularWSs
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ws_handle_or_tag, "ws_handle_or_tag")

        # Resolve to WS object
        ws = self._ResolveWS(ws_handle_or_tag)
        if not ws:
            raise FP_WritingSystemError(str(ws_handle_or_tag))

        # Verify it's a vernacular WS
        vern_tags = set(self.GetVernacularWSs())
        if ws.Id not in vern_tags:
            raise FP_ParameterError(f"Writing system '{ws.Id}' is not a vernacular writing system")

        # Set as default
        self.project.lp.DefaultVernacularWritingSystem = ws

    @OperationsMethod
    def SetDefaultAnalysis(self, ws_handle_or_tag):
        """
        Set the default analysis writing system.

        Args:
            ws_handle_or_tag: Writing system handle (int) or language tag (str)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws_handle_or_tag is None
            FP_WritingSystemError: If writing system not found
            FP_ParameterError: If WS is not in analysis list

        Example:
            >>> # Set by language tag
            >>> project.ProjectSettings.SetDefaultAnalysis("en")

            >>> # Verify the change
            >>> default = project.WritingSystems.GetDefaultAnalysis()
            >>> tag = project.WritingSystems.GetLanguageTag(default)
            >>> print(f"Default analysis: {tag}")
            Default analysis: en

        Notes:
            - Writing system must be in the analysis list
            - This is the primary WS for glosses and definitions
            - Used as fallback when no specific WS is specified

        See Also:
            SetDefaultVernacular, GetAnalysisWSs
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ws_handle_or_tag, "ws_handle_or_tag")

        # Resolve to WS object
        ws = self._ResolveWS(ws_handle_or_tag)
        if not ws:
            raise FP_WritingSystemError(str(ws_handle_or_tag))

        # Verify it's an analysis WS
        anal_tags = set(self.GetAnalysisWSs())
        if ws.Id not in anal_tags:
            raise FP_ParameterError(f"Writing system '{ws.Id}' is not an analysis writing system")

        # Set as default
        self.project.lp.DefaultAnalysisWritingSystem = ws

    # --- UI Settings ---

    @OperationsMethod
    def GetInterfaceLanguage(self):
        """
        Get the user interface language writing system.

        Returns:
            IWritingSystemDefinition: The UI language writing system

        Example:
            >>> ui_ws = project.ProjectSettings.GetInterfaceLanguage()
            >>> tag = project.WritingSystems.GetLanguageTag(ui_ws)
            >>> print(f"UI language: {tag}")
            UI language: en

        Notes:
            - This determines the language used in the FLEx interface
            - Typically an analysis writing system (e.g., "en", "fr", "es")
            - Falls back to default analysis WS if not specifically set

        See Also:
            SetInterfaceLanguage
        """
        # The UI language is stored in UserWs
        if hasattr(self.project.lp, "UserWs"):
            return self.project.lp.UserWs
        # Fall back to default analysis
        return self.project.lp.DefaultAnalysisWritingSystem

    @OperationsMethod
    def SetInterfaceLanguage(self, ws_handle_or_tag):
        """
        Set the user interface language writing system.

        Args:
            ws_handle_or_tag: Writing system handle (int) or language tag (str)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws_handle_or_tag is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> # Set UI to French
            >>> project.ProjectSettings.SetInterfaceLanguage("fr")

            >>> # Set UI to English
            >>> project.ProjectSettings.SetInterfaceLanguage("en")

        Notes:
            - Changes the language used in the FLEx interface
            - Should typically be an analysis writing system
            - Requires application restart to take full effect

        See Also:
            GetInterfaceLanguage
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ws_handle_or_tag, "ws_handle_or_tag")

        # Resolve to WS object
        ws = self._ResolveWS(ws_handle_or_tag)
        if not ws:
            raise FP_WritingSystemError(str(ws_handle_or_tag))

        # Set the UI language
        if hasattr(self.project.lp, "UserWs"):
            self.project.lp.UserWs = ws

    # --- Default Font Settings ---

    @OperationsMethod
    def GetDefaultFont(self, ws_handle_or_tag):
        """
        Get the default font name for a writing system.

        Args:
            ws_handle_or_tag: Writing system handle (int) or language tag (str)

        Returns:
            str: Font name (e.g., "Charis SIL", "Arial")

        Raises:
            FP_NullParameterError: If ws_handle_or_tag is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> font = project.ProjectSettings.GetDefaultFont("qaa-x-kal")
            >>> print(f"Default font: {font}")
            Default font: Charis SIL

            >>> # Get for analysis WS
            >>> font = project.ProjectSettings.GetDefaultFont("en")
            >>> print(font)
            Calibri

        Notes:
            - Returns the default font for display and editing
            - Empty string if no default font is set
            - This is a convenience wrapper around WritingSystems.GetFontName()

        See Also:
            SetDefaultFont, GetDefaultFontSize
        """
        self._ValidateParam(ws_handle_or_tag, "ws_handle_or_tag")

        ws = self._ResolveWS(ws_handle_or_tag)
        if not ws:
            raise FP_WritingSystemError(str(ws_handle_or_tag))

        # Get default font name
        if hasattr(ws, "DefaultFontName") and ws.DefaultFontName:
            return ws.DefaultFontName
        elif hasattr(ws, "DefaultFont") and ws.DefaultFont:
            return ws.DefaultFont
        return ""

    @OperationsMethod
    def SetDefaultFont(self, ws_handle_or_tag, font_name):
        """
        Set the default font name for a writing system.

        Args:
            ws_handle_or_tag: Writing system handle (int) or language tag (str)
            font_name (str): Font name (e.g., "Charis SIL", "Arial")

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws_handle_or_tag or font_name is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> # Set font for vernacular
            >>> project.ProjectSettings.SetDefaultFont("qaa-x-kal", "Charis SIL")

            >>> # Set font for IPA
            >>> project.ProjectSettings.SetDefaultFont("qaa-x-kal-fonipa", "Doulos SIL")

            >>> # Set font for analysis
            >>> project.ProjectSettings.SetDefaultFont("en", "Calibri")

        Notes:
            - Font must be installed on the system
            - Changes affect all text displayed in this writing system
            - Recommended fonts for IPA: Charis SIL, Doulos SIL
            - This is a convenience wrapper around WritingSystems.SetFontName()

        See Also:
            GetDefaultFont, SetDefaultFontSize
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ws_handle_or_tag, "ws_handle_or_tag")

        ws = self._ResolveWS(ws_handle_or_tag)
        if not ws:
            raise FP_WritingSystemError(str(ws_handle_or_tag))

        # Set default font name
        if hasattr(ws, "DefaultFontName"):
            ws.DefaultFontName = font_name
        elif hasattr(ws, "DefaultFont"):
            ws.DefaultFont = font_name

    @OperationsMethod
    def GetDefaultFontSize(self, ws_handle_or_tag):
        """
        Get the default font size for a writing system.

        Args:
            ws_handle_or_tag: Writing system handle (int) or language tag (str)

        Returns:
            float: Font size in points (e.g., 12.0)

        Raises:
            FP_NullParameterError: If ws_handle_or_tag is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> size = project.ProjectSettings.GetDefaultFontSize("qaa-x-kal")
            >>> print(f"Font size: {size} pt")
            Font size: 14.0 pt

        Notes:
            - Returns 12.0 if no default size is set
            - This is a convenience wrapper around WritingSystems.GetFontSize()

        See Also:
            SetDefaultFontSize, GetDefaultFont
        """
        self._ValidateParam(ws_handle_or_tag, "ws_handle_or_tag")

        ws = self._ResolveWS(ws_handle_or_tag)
        if not ws:
            raise FP_WritingSystemError(str(ws_handle_or_tag))

        # Get default font size
        if hasattr(ws, "DefaultFontSize") and ws.DefaultFontSize:
            return float(ws.DefaultFontSize)
        return 12.0  # Default size

    @OperationsMethod
    def SetDefaultFontSize(self, ws_handle_or_tag, size):
        """
        Set the default font size for a writing system.

        Args:
            ws_handle_or_tag: Writing system handle (int) or language tag (str)
            size (float or int): Font size in points (e.g., 12, 14.5)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws_handle_or_tag or size is None
            FP_WritingSystemError: If writing system not found
            FP_ParameterError: If size is not positive

        Example:
            >>> # Set standard size
            >>> project.ProjectSettings.SetDefaultFontSize("qaa-x-kal", 14)

            >>> # Set larger for better readability
            >>> project.ProjectSettings.SetDefaultFontSize("qaa-x-kal", 16)

            >>> # Set for analysis
            >>> project.ProjectSettings.SetDefaultFontSize("en", 12)

        Notes:
            - Size should typically be between 8 and 72 points
            - Common sizes: 10, 12, 14, 16
            - Changes affect all text displayed in this writing system
            - This is a convenience wrapper around WritingSystems.SetFontSize()

        See Also:
            GetDefaultFontSize, SetDefaultFont
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ws_handle_or_tag, "ws_handle_or_tag")

        if size <= 0:
            raise FP_ParameterError("Font size must be positive")

        ws = self._ResolveWS(ws_handle_or_tag)
        if not ws:
            raise FP_WritingSystemError(str(ws_handle_or_tag))

        # Set default font size
        if hasattr(ws, "DefaultFontSize"):
            ws.DefaultFontSize = float(size)

    # --- Advanced Settings ---

    @OperationsMethod
    def GetLinkedFilesRootDir(self):
        """
        Get the root directory for linked files (media, pictures, etc.).

        Returns:
            str: Path to the linked files root directory

        Example:
            >>> linked_path = project.ProjectSettings.GetLinkedFilesRootDir()
            >>> print(f"Linked files: {linked_path}")
            Linked files: C:\\Users\\username\\Documents\\FLEx\\Kalaba\\LinkedFiles

        Notes:
            - This is where FLEx stores media files, pictures, etc.
            - Path is typically relative to the project directory
            - Returns empty string if not set
            - Used for organizing external resources

        See Also:
            SetLinkedFilesRootDir, GetExtLinkRootDir
        """
        if hasattr(self.project.lp, "LinkedFilesRootDir") and self.project.lp.LinkedFilesRootDir:
            return self.project.lp.LinkedFilesRootDir
        return ""

    @OperationsMethod
    def SetLinkedFilesRootDir(self, path):
        """
        Set the root directory for linked files (media, pictures, etc.).

        Args:
            path (str): Path to the linked files root directory

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If path is None

        Example:
            >>> # Set absolute path
            >>> project.ProjectSettings.SetLinkedFilesRootDir(
            ...     "C:\\\\Users\\\\username\\\\Documents\\\\FLEx\\\\Kalaba\\\\LinkedFiles"
            ... )

            >>> # Set relative path
            >>> project.ProjectSettings.SetLinkedFilesRootDir("LinkedFiles")

        Notes:
            - Can be absolute or relative path
            - Relative paths are relative to the project directory
            - Directory should exist before setting
            - Used for organizing external resources like media files

        See Also:
            GetLinkedFilesRootDir, SetExtLinkRootDir
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(path, "path")

        self.project.lp.LinkedFilesRootDir = path

    @OperationsMethod
    def GetExtLinkRootDir(self):
        """
        Get the external link root directory.

        Returns:
            str: Path to the external link root directory

        Example:
            >>> ext_link_path = project.ProjectSettings.GetExtLinkRootDir()
            >>> print(f"External links: {ext_link_path}")
            External links: C:\\Users\\username\\Documents\\ExternalResources

        Notes:
            - This is for external linked resources
            - Different from LinkedFilesRootDir
            - Returns empty string if not set
            - Used for organizing external reference materials

        See Also:
            SetExtLinkRootDir, GetLinkedFilesRootDir
        """
        if hasattr(self.project.lp, "ExtLinkRootDir") and self.project.lp.ExtLinkRootDir:
            return self.project.lp.ExtLinkRootDir
        return ""

    @OperationsMethod
    def SetExtLinkRootDir(self, path):
        """
        Set the external link root directory.

        Args:
            path (str): Path to the external link root directory

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If path is None

        Example:
            >>> # Set absolute path
            >>> project.ProjectSettings.SetExtLinkRootDir(
            ...     "C:\\\\Users\\\\username\\\\Documents\\\\ExternalResources"
            ... )

            >>> # Set relative path
            >>> project.ProjectSettings.SetExtLinkRootDir("ExternalLinks")

        Notes:
            - Can be absolute or relative path
            - Relative paths are relative to the project directory
            - Directory should exist before setting
            - Used for organizing external linked resources

        See Also:
            GetExtLinkRootDir, SetLinkedFilesRootDir
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(path, "path")

        self.project.lp.ExtLinkRootDir = path

    @OperationsMethod
    def GetAnalysisWritingSystems(self):
        """
        Get the list of analysis writing system tags.

        Returns:
            list: List of analysis writing system language tags (e.g., ["en", "fr"])

        Example:
            >>> anal_wss = project.ProjectSettings.GetAnalysisWritingSystems()
            >>> print("Analysis writing systems:")
            >>> for ws_tag in anal_wss:
            ...     print(f"  - {ws_tag}")
            Analysis writing systems:
              - en
              - fr
              - es

        Notes:
            - Returns list of language tags, not WS objects
            - These are the writing systems for metadata and analysis
            - READ-ONLY: Use other methods to modify the writing system list
            - Empty list if no analysis writing systems configured
            - This is an alias for GetAnalysisWSs() for consistency

        See Also:
            GetVernacularWritingSystems, GetAnalysisWSs
        """
        if hasattr(self.project.lp, "AnalysisWss") and self.project.lp.AnalysisWss:
            return self.project.lp.AnalysisWss.split()
        return []

    @OperationsMethod
    def GetVernacularWritingSystems(self):
        """
        Get the list of vernacular writing system tags.

        Returns:
            list: List of vernacular writing system language tags (e.g., ["qaa-x-kal"])

        Example:
            >>> vern_wss = project.ProjectSettings.GetVernacularWritingSystems()
            >>> print("Vernacular writing systems:")
            >>> for ws_tag in vern_wss:
            ...     print(f"  - {ws_tag}")
            Vernacular writing systems:
              - qaa-x-kal
              - qaa-x-kal-fonipa

        Notes:
            - Returns list of language tags, not WS objects
            - These are the writing systems for the object language(s)
            - READ-ONLY: Use other methods to modify the writing system list
            - Empty list if no vernacular writing systems configured
            - This is an alias for GetVernacularWSs() for consistency

        See Also:
            GetAnalysisWritingSystems, GetVernacularWSs
        """
        if hasattr(self.project.lp, "CurVernWss") and self.project.lp.CurVernWss:
            return self.project.lp.CurVernWss.split()
        return []

    @OperationsMethod
    def GetProjectGuid(self):
        """
        Get the project GUID as a string.

        Returns:
            str: The project GUID (e.g., 'a1b2c3d4-e5f6-...'), or empty string if unavailable.

        Example:
            >>> guid = project.ProjectSettings.GetProjectGuid()
            >>> print(f"Project GUID: {guid}")
            Project GUID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

        Notes:
            - Derived from ILangProject.Guid
            - Stable identifier for this project instance
            - READ-ONLY

        See Also:
            GetProjectName
        """
        if hasattr(self.project.lp, "Guid"):
            return str(self.project.lp.Guid)
        return ""

    @OperationsMethod
    def GetProjectDescription(self, ws_handle_or_tag=None):
        """
        Get the project description in the specified writing system.

        Alias for GetDescription(). See GetDescription() for full documentation.

        Args:
            ws_handle_or_tag: Writing system handle (int), language tag (str),
                or None for default analysis WS.

        Returns:
            str: The project description text.

        See Also:
            GetDescription
        """
        return self.GetDescription(ws_handle_or_tag)

    @OperationsMethod
    def GetExternalLink(self):
        """
        Get the external (linked files) root directory path.

        Alias for GetExtLinkRootDir(). See GetExtLinkRootDir() for full documentation.

        Returns:
            str: The external link root directory path, or empty string if not set.

        See Also:
            GetExtLinkRootDir
        """
        return self.GetExtLinkRootDir()

    @OperationsMethod
    def GetAnalysisWritingSystem(self):
        """
        Get the default analysis writing system object.

        Returns:
            IWritingSystem: The default analysis writing system for this project, or None if the language project is unavailable.

        Example:
            >>> ws = project.ProjectSettings.GetAnalysisWritingSystem()
            >>> print(ws.Id)
            en

        Notes:
            - Returns the IWritingSystem object, not a string tag
            - For a list of all analysis writing system tags, use GetAnalysisWritingSystems()
            - READ-ONLY

        See Also:
            GetAnalysisWritingSystems, GetVernacularWritingSystem
        """
        if self.project.lp is None:
            return None
        return self.project.lp.DefaultAnalysisWritingSystem

    @OperationsMethod
    def GetVernacularWritingSystem(self):
        """
        Get the default vernacular writing system object.

        Returns:
            IWritingSystem: The default vernacular writing system for this project, or None if the language project is unavailable.

        Example:
            >>> ws = project.ProjectSettings.GetVernacularWritingSystem()
            >>> print(ws.Id)
            qaa-x-kal

        Notes:
            - Returns the IWritingSystem object, not a string tag
            - For a list of all vernacular writing system tags, use GetVernacularWritingSystems()
            - READ-ONLY

        See Also:
            GetVernacularWritingSystems, GetAnalysisWritingSystem
        """
        if self.project.lp is None:
            return None
        return self.project.lp.DefaultVernacularWritingSystem

    # --- Project Metadata ---

    @OperationsMethod
    def GetDateCreated(self):
        """
        Get the date the project was created.

        Returns:
            datetime: The creation date/time, or None if not available

        Example:
            >>> created = project.ProjectSettings.GetDateCreated()
            >>> if created:
            ...     print(f"Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
            Created: 2024-01-15 10:30:00

        Notes:
            - Returns .NET DateTime object
            - Can be None if creation date is not recorded
            - Read-only property

        See Also:
            GetDateModified
        """
        if hasattr(self.project.lp, "DateCreated"):
            return self.project.lp.DateCreated
        return None

    @OperationsMethod
    def GetDateModified(self):
        """
        Get the date the project was last modified.

        Returns:
            datetime: The last modification date/time, or None if not available

        Example:
            >>> modified = project.ProjectSettings.GetDateModified()
            >>> if modified:
            ...     print(f"Last modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            Last modified: 2024-03-20 15:45:30

        Notes:
            - Returns .NET DateTime object
            - Can be None if modification date is not recorded
            - Read-only property
            - Updated automatically when project is saved

        See Also:
            GetDateCreated
        """
        if hasattr(self.project.lp, "DateModified"):
            return self.project.lp.DateModified
        return None

    # --- Private Helper Methods ---

    def _ResolveWSHandle(self, ws_handle_or_tag):
        """
        Resolve a writing system parameter to a WS handle.

        Args:
            ws_handle_or_tag: Writing system handle (int), language tag (str),
                or None for default analysis WS

        Returns:
            int: Writing system handle

        Raises:
            FP_WritingSystemError: If writing system not found
        """
        if ws_handle_or_tag is None:
            return self.project.project.DefaultAnalWs

        if isinstance(ws_handle_or_tag, str):
            # Language tag - resolve to handle
            ws = self._GetWSByTag(ws_handle_or_tag)
            if not ws:
                raise FP_WritingSystemError(ws_handle_or_tag)
            return ws.Handle
        else:
            # Assume it's a handle
            return ws_handle_or_tag

    def _ResolveWS(self, ws_handle_or_tag):
        """
        Resolve a writing system parameter to a WS object.

        Args:
            ws_handle_or_tag: Writing system handle (int) or language tag (str)

        Returns:
            IWritingSystemDefinition or None: Writing system object or None
        """
        self._ValidateParam(ws_handle_or_tag, "ws_handle_or_tag")

        if isinstance(ws_handle_or_tag, str):
            return self._GetWSByTag(ws_handle_or_tag)
        else:
            # Handle - resolve to WS object
            return self._GetWSByHandle(ws_handle_or_tag)

    def _GetWSByTag(self, language_tag):
        """
        Get writing system object by language tag.

        Args:
            language_tag (str): Language tag

        Returns:
            IWritingSystemDefinition or None: Writing system or None if not found
        """
        normalized_tag = self._NormalizeLangTag(language_tag)

        for ws in self.project.project.ServiceLocator.WritingSystems.AllWritingSystems:
            if self._NormalizeLangTag(ws.Id) == normalized_tag:
                return ws
        return None

    def _GetWSByHandle(self, handle):
        """
        Get writing system object by handle.

        Args:
            handle (int): Writing system handle

        Returns:
            IWritingSystemDefinition or None: Writing system or None if not found
        """
        for ws in self.project.project.ServiceLocator.WritingSystems.AllWritingSystems:
            if ws.Handle == handle:
                return ws
        return None

    def _NormalizeLangTag(self, language_tag):
        """
        Normalize language tag for comparison (lowercase, underscores to hyphens).

        Args:
            language_tag (str): Language tag to normalize

        Returns:
            str: Normalized tag
        """
        return language_tag.replace("_", "-").lower()

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate operation is not applicable for project settings.

        Project settings are singleton configuration objects and cannot be duplicated.

        Raises:
            NotImplementedError: Always raised - project settings cannot be duplicated.

        Notes:
            - Project settings are unique per project
            - Use getter/setter methods to modify settings
            - Settings are not duplicatable data objects

        See Also:
            GetProjectName, SetProjectName
        """
        raise NotImplementedError(
            "Project settings cannot be duplicated. Project settings are singleton configuration objects."
        )

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get syncable properties - NOT IMPLEMENTED for project settings.

        Project settings are configuration data unique to each project and should
        not be synced between projects.

        Raises:
            NotImplementedError: Project settings are not syncable
        """
        raise NotImplementedError(
            "Project settings cannot be synced between projects. "
            "Settings are configuration data unique to each project."
        )

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare project settings - NOT IMPLEMENTED.

        Project settings are configuration data unique to each project and should
        not be synced between projects.

        Raises:
            NotImplementedError: Project settings are not syncable
        """
        raise NotImplementedError(
            "Project settings cannot be compared for sync. " "Settings are configuration data unique to each project."
        )
