#
#   WritingSystemOperations.py
#
#   Class: WritingSystemOperations
#          Writing system management operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import FLEx LCM types
from SIL.LCModel import SpecialWritingSystemCodes
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils
from SIL.WritingSystems import WritingSystemDefinition  # Fixed: was IWritingSystemDefinition

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
    FP_WritingSystemError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable


class WritingSystemOperations(BaseOperations):
    """
    This class provides operations for managing writing systems in a
    FieldWorks project.

    Writing systems define how text is displayed, including language,
    script, font settings, and directionality (left-to-right or right-to-left).

    This class should be accessed via FLExProject.WritingSystems property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all writing systems
        for ws in project.WritingSystems.GetAll():
            name = project.WritingSystems.GetDisplayName(ws)
            tag = project.WritingSystems.GetLanguageTag(ws)
            print(f"{name} ({tag})")

        # Get vernacular and analysis writing systems
        vern_wss = project.WritingSystems.GetVernacular()
        anal_wss = project.WritingSystems.GetAnalysis()

        # Configure a writing system
        ws = list(vern_wss)[0]
        project.WritingSystems.SetFontName(ws, "Charis SIL")
        project.WritingSystems.SetFontSize(ws, 12)
        project.WritingSystems.SetRightToLeft(ws, False)

        # Check and set defaults
        default_vern = project.WritingSystems.GetDefaultVernacular()
        default_anal = project.WritingSystems.GetDefaultAnalysis()

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize WritingSystemOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all active writing systems in the project.

        Returns all writing systems that are currently active (both vernacular
        and analysis) in the project.

        Yields:
            IWritingSystemDefinition: Each writing system object

        Example:
            >>> for ws in project.WritingSystems.GetAll():
            ...     name = project.WritingSystems.GetDisplayName(ws)
            ...     tag = project.WritingSystems.GetLanguageTag(ws)
            ...     font = project.WritingSystems.GetFontName(ws)
            ...     print(f"{name} ({tag}): {font}")
            English (en): Calibri
            French (fr): Arial
            Vernacular (qaa-x-kal): Charis SIL

        Notes:
            - Returns only writing systems that are active in the project
            - Includes both vernacular and analysis writing systems
            - Use GetVernacular() or GetAnalysis() to filter by type

        See Also:
            GetVernacular, GetAnalysis, Exists
        """
        vern_ws_set = self._GetAllVernacularWSTags()
        anal_ws_set = self._GetAllAnalysisWSTags()
        active_tags = vern_ws_set | anal_ws_set

        for ws in self.project.project.ServiceLocator.WritingSystems.AllWritingSystems:
            if ws.Id in active_tags:
                yield ws

    @OperationsMethod
    def GetVernacular(self):
        """
        Get all vernacular writing systems.

        Vernacular writing systems are those used for the language(s) being
        studied or documented.

        Yields:
            IWritingSystemDefinition: Each vernacular writing system

        Example:
            >>> for ws in project.WritingSystems.GetVernacular():
            ...     name = project.WritingSystems.GetDisplayName(ws)
            ...     tag = project.WritingSystems.GetLanguageTag(ws)
            ...     print(f"Vernacular: {name} ({tag})")
            Vernacular: Kalaba (qaa-x-kal)
            Vernacular: Kalaba-IPA (qaa-x-kal-fonipa)

        Notes:
            - Vernacular writing systems are for the object language
            - These are the primary languages of the lexicon entries
            - Most projects have 1-3 vernacular writing systems

        See Also:
            GetAnalysis, GetDefaultVernacular, SetDefaultVernacular
        """
        vern_ws_set = self._GetAllVernacularWSTags()

        for ws in self.project.project.ServiceLocator.WritingSystems.AllWritingSystems:
            if ws.Id in vern_ws_set:
                yield ws

    @OperationsMethod
    def GetAnalysis(self):
        """
        Get all analysis writing systems.

        Analysis writing systems are those used for linguistic analysis,
        glosses, and translations (typically major languages like English,
        French, Spanish, etc.).

        Yields:
            IWritingSystemDefinition: Each analysis writing system

        Example:
            >>> for ws in project.WritingSystems.GetAnalysis():
            ...     name = project.WritingSystems.GetDisplayName(ws)
            ...     tag = project.WritingSystems.GetLanguageTag(ws)
            ...     print(f"Analysis: {name} ({tag})")
            Analysis: English (en)
            Analysis: French (fr)
            Analysis: Spanish (es)

        Notes:
            - Analysis writing systems are for metadata languages
            - Used for glosses, definitions, and translations
            - Most projects have 1-3 analysis writing systems

        See Also:
            GetVernacular, GetDefaultAnalysis, SetDefaultAnalysis
        """
        anal_ws_set = self._GetAllAnalysisWSTags()

        for ws in self.project.project.ServiceLocator.WritingSystems.AllWritingSystems:
            if ws.Id in anal_ws_set:
                yield ws

    @OperationsMethod
    def Create(self, language_tag, name, is_vernacular=True):
        """
        Create a new writing system in the project.

        Args:
            language_tag (str): Language tag (e.g., "en", "fr", "qaa-x-kal")
            name (str): Display name for the writing system
            is_vernacular (bool): True for vernacular, False for analysis.
                Defaults to True.

        Returns:
            IWritingSystemDefinition: The newly created writing system

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If language_tag or name is None
            FP_ParameterError: If language_tag is empty or already exists

        Example:
            >>> # Create a vernacular writing system
            >>> ws = project.WritingSystems.Create("qaa-x-kal", "Kalaba")
            >>> print(project.WritingSystems.GetDisplayName(ws))
            Kalaba

            >>> # Create an analysis writing system
            >>> ws = project.WritingSystems.Create("es", "Spanish", is_vernacular=False)
            >>> project.WritingSystems.SetFontName(ws, "Arial")
            >>> project.WritingSystems.SetFontSize(ws, 12)

            >>> # Create IPA writing system
            >>> ws = project.WritingSystems.Create("qaa-x-kal-fonipa", "Kalaba IPA")
            >>> project.WritingSystems.SetFontName(ws, "Charis SIL")

        Notes:
            - Language tags should follow BCP 47 standard
            - Use "qaa-x-" prefix for undocumented languages
            - The writing system is automatically added to vernacular or
              analysis list based on is_vernacular parameter
            - Default font settings may be inherited from system defaults

        See Also:
            Delete, Exists, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(language_tag, "language_tag")
        self._ValidateParam(name, "name")

        if not language_tag or not language_tag.strip():
            raise FP_ParameterError("Language tag cannot be empty")

        # Check if writing system already exists
        if self.Exists(language_tag):
            raise FP_ParameterError(f"Writing system '{language_tag}' already exists")

        ws_manager = self.project.project.ServiceLocator.WritingSystemManager

        with self._TransactionCM(f"Create writing system '{language_tag}'"):
            # Create + register the WS with the manager. Set() stores it in the
            # repository, assigns a runtime Handle, and persists the .ldml
            # backing file on Save. Without Set(), Create() returns a detached
            # object -- adding the tag to CurXxxWss would yield an orphan
            # reference and the next OpenProject would hit a modal
            # "Unable to create writing system: <tag>" dialog from liblcm.
            ws = ws_manager.Create(language_tag)
            ws.Abbreviation = language_tag
            try:
                ws.DisplayLabel = name
            except Exception:
                pass
            ws_manager.Set(ws)

            # AddToCurrent* updates BOTH the full XxxWss list AND the current
            # list via the proper change-notification path. Raw assignment to
            # CurXxxWss (the previous implementation) bypassed the WS-list
            # collection bookkeeping and left the full list out of sync.
            if is_vernacular:
                self.project.lp.AddToCurrentVernacularWritingSystems(ws)
            else:
                self.project.lp.AddToCurrentAnalysisWritingSystems(ws)

            return ws

    @OperationsMethod
    def Delete(self, ws_handle_or_tag):
        """
        Remove a writing system from the project.

        Args:
            ws_handle_or_tag: Either a writing system handle (int) or
                language tag (str)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws_handle_or_tag is None
            FP_WritingSystemError: If writing system not found
            FP_ParameterError: If trying to delete the default WS

        Example:
            >>> # Delete by language tag
            >>> if project.WritingSystems.Exists("qaa-x-old"):
            ...     project.WritingSystems.Delete("qaa-x-old")

            >>> # Delete by handle
            >>> ws = list(project.WritingSystems.GetVernacular())[2]
            ...     handle = ws.Handle
            ...     project.WritingSystems.Delete(handle)

        Notes:
            - Cannot delete default vernacular or analysis writing systems
            - Should check that no data uses this writing system before deleting
            - This operation cannot be undone
            - Writing system is removed from both the store and active lists

        See Also:
            Create, Exists
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ws_handle_or_tag, "ws_handle_or_tag")

        # Get the writing system object
        if isinstance(ws_handle_or_tag, str):
            language_tag = ws_handle_or_tag
            ws = self._GetWSByTag(language_tag)
            if not ws:
                raise FP_WritingSystemError(language_tag)
        else:
            ws = self._GetWSByHandle(ws_handle_or_tag)
            if not ws:
                raise FP_WritingSystemError(str(ws_handle_or_tag))
            language_tag = ws.Id

        # Check if it's a default writing system
        default_vern = self.project.lp.DefaultVernacularWritingSystem
        default_anal = self.project.lp.DefaultAnalysisWritingSystem

        if ws.Handle == default_vern.Handle:
            raise FP_ParameterError("Cannot delete the default vernacular writing system")
        if ws.Handle == default_anal.Handle:
            raise FP_ParameterError("Cannot delete the default analysis writing system")

        with self._TransactionCM(f"Delete writing system '{language_tag}'"):
            # Removal contract from IWritingSystemContainer: "first remove from
            # AnalysisWritingSystems [the full list], then from
            # CurrentAnalysisWritingSystems [the current list]." Same for
            # vernacular. Going through the collections (rather than
            # rewriting the CurXxxWss space-delimited string) keeps the full
            # list and current list in sync.
            for full_list, current_list in (
                (self.project.lp.VernacularWritingSystems, self.project.lp.CurrentVernacularWritingSystems),
                (self.project.lp.AnalysisWritingSystems, self.project.lp.CurrentAnalysisWritingSystems),
            ):
                if full_list.Contains(ws):
                    full_list.Remove(ws)
                if current_list.Contains(ws):
                    current_list.Remove(ws)

    # --- Configuration Methods ---

    @OperationsMethod
    def GetFontName(self, ws):
        """
        Get the default font name for a writing system.

        Args:
            ws: IWritingSystemDefinition object or language tag (str)

        Returns:
            str: Font name (e.g., "Charis SIL", "Arial")

        Raises:
            FP_NullParameterError: If ws is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> ws = list(project.WritingSystems.GetVernacular())[0]
            >>> font = project.WritingSystems.GetFontName(ws)
            >>> print(f"Font: {font}")
            Font: Charis SIL

            >>> # By language tag
            >>> font = project.WritingSystems.GetFontName("en")
            >>> print(font)
            Calibri

        See Also:
            SetFontName, GetFontSize
        """
        ws_obj = self._ResolveWS(ws)
        if not ws_obj:
            raise FP_WritingSystemError(str(ws))

        # Get default font name
        if hasattr(ws_obj, "DefaultFontName") and ws_obj.DefaultFontName:
            return ws_obj.DefaultFontName
        elif hasattr(ws_obj, "DefaultFont") and ws_obj.DefaultFont:
            return ws_obj.DefaultFont
        else:
            return ""

    @OperationsMethod
    def SetFontName(self, ws, font_name):
        """
        Set the default font name for a writing system.

        Args:
            ws: IWritingSystemDefinition object or language tag (str)
            font_name (str): Font name (e.g., "Charis SIL", "Arial")

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws or font_name is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> ws = list(project.WritingSystems.GetVernacular())[0]
            >>> project.WritingSystems.SetFontName(ws, "Charis SIL")

            >>> # Set by language tag
            >>> project.WritingSystems.SetFontName("en", "Calibri")

            >>> # Set IPA font
            >>> project.WritingSystems.SetFontName("qaa-x-kal-fonipa", "Doulos SIL")

        Notes:
            - Font must be installed on the system
            - Changes affect all text displayed in this writing system
            - Recommended fonts for IPA: Charis SIL, Doulos SIL

        See Also:
            GetFontName, SetFontSize
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(font_name, "font_name")

        ws_obj = self._ResolveWS(ws)
        if not ws_obj:
            raise FP_WritingSystemError(str(ws))

        # Set default font name
        if hasattr(ws_obj, "DefaultFontName"):
            ws_obj.DefaultFontName = font_name
        elif hasattr(ws_obj, "DefaultFont"):
            ws_obj.DefaultFont = font_name

    @OperationsMethod
    def GetFontSize(self, ws):
        """
        Get the default font size for a writing system.

        Args:
            ws: IWritingSystemDefinition object or language tag (str)

        Returns:
            float: Font size in points (e.g., 12.0)

        Raises:
            FP_NullParameterError: If ws is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> ws = list(project.WritingSystems.GetVernacular())[0]
            >>> size = project.WritingSystems.GetFontSize(ws)
            >>> print(f"Font size: {size} pt")
            Font size: 12.0 pt

        See Also:
            SetFontSize, GetFontName
        """
        ws_obj = self._ResolveWS(ws)
        if not ws_obj:
            raise FP_WritingSystemError(str(ws))

        # Get default font size
        if hasattr(ws_obj, "DefaultFontSize") and ws_obj.DefaultFontSize:
            return float(ws_obj.DefaultFontSize)
        else:
            return 12.0  # Default size

    @OperationsMethod
    def SetFontSize(self, ws, size):
        """
        Set the default font size for a writing system.

        Args:
            ws: IWritingSystemDefinition object or language tag (str)
            size (float or int): Font size in points (e.g., 12, 14.5)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws or size is None
            FP_WritingSystemError: If writing system not found
            FP_ParameterError: If size is not positive

        Example:
            >>> ws = list(project.WritingSystems.GetVernacular())[0]
            >>> project.WritingSystems.SetFontSize(ws, 14)

            >>> # Set by language tag
            >>> project.WritingSystems.SetFontSize("en", 12)

            >>> # Larger size for better readability
            >>> project.WritingSystems.SetFontSize("qaa-x-kal", 16)

        Notes:
            - Size should typically be between 8 and 72 points
            - Common sizes: 10, 12, 14, 16
            - Changes affect all text displayed in this writing system

        See Also:
            GetFontSize, SetFontName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(size, "size")

        if size <= 0:
            raise FP_ParameterError("Font size must be positive")

        ws_obj = self._ResolveWS(ws)
        if not ws_obj:
            raise FP_WritingSystemError(str(ws))

        # Set default font size
        if hasattr(ws_obj, "DefaultFontSize"):
            ws_obj.DefaultFontSize = float(size)

    @OperationsMethod
    def GetRightToLeft(self, ws):
        """
        Get the right-to-left directionality setting for a writing system.

        Args:
            ws: IWritingSystemDefinition object or language tag (str)

        Returns:
            bool: True if right-to-left, False if left-to-right

        Raises:
            FP_NullParameterError: If ws is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> ws = list(project.WritingSystems.GetVernacular())[0]
            >>> rtl = project.WritingSystems.GetRightToLeft(ws)
            >>> print(f"RTL: {rtl}")
            RTL: False

            >>> # Check Arabic
            >>> if project.WritingSystems.Exists("ar"):
            ...     rtl = project.WritingSystems.GetRightToLeft("ar")
            ...     print(f"Arabic is RTL: {rtl}")
            Arabic is RTL: True

        Notes:
            - RTL languages include Arabic, Hebrew, Persian, Urdu
            - Most languages are left-to-right (LTR)

        See Also:
            SetRightToLeft
        """
        ws_obj = self._ResolveWS(ws)
        if not ws_obj:
            raise FP_WritingSystemError(str(ws))

        # Get RTL setting
        if hasattr(ws_obj, "RightToLeftScript"):
            return bool(ws_obj.RightToLeftScript)
        elif hasattr(ws_obj, "RightToLeft"):
            return bool(ws_obj.RightToLeft)
        else:
            return False  # Default to LTR

    @OperationsMethod
    def SetRightToLeft(self, ws, is_rtl):
        """
        Set the right-to-left directionality for a writing system.

        Args:
            ws: IWritingSystemDefinition object or language tag (str)
            is_rtl (bool): True for right-to-left, False for left-to-right

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws or is_rtl is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> # Set Arabic to RTL
            >>> if project.WritingSystems.Exists("ar"):
            ...     project.WritingSystems.SetRightToLeft("ar", True)

            >>> # Set English to LTR
            >>> project.WritingSystems.SetRightToLeft("en", False)

        Notes:
            - RTL languages: Arabic, Hebrew, Persian, Urdu, etc.
            - This affects text rendering direction in the UI
            - Most languages should be LTR (False)

        See Also:
            GetRightToLeft
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(is_rtl, "is_rtl")

        ws_obj = self._ResolveWS(ws)
        if not ws_obj:
            raise FP_WritingSystemError(str(ws))

        # Set RTL setting
        if hasattr(ws_obj, "RightToLeftScript"):
            ws_obj.RightToLeftScript = bool(is_rtl)
        elif hasattr(ws_obj, "RightToLeft"):
            ws_obj.RightToLeft = bool(is_rtl)

    # --- Default Settings ---

    @OperationsMethod
    def SetDefaultVernacular(self, ws):
        """
        Set the default vernacular writing system.

        Args:
            ws: IWritingSystemDefinition object or language tag (str)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws is None
            FP_WritingSystemError: If writing system not found
            FP_ParameterError: If ws is not a vernacular writing system

        Example:
            >>> # Set by object
            >>> ws = list(project.WritingSystems.GetVernacular())[0]
            >>> project.WritingSystems.SetDefaultVernacular(ws)

            >>> # Set by language tag
            >>> project.WritingSystems.SetDefaultVernacular("qaa-x-kal")

        Notes:
            - The writing system must be in the vernacular list
            - This is the primary writing system for lexical entries
            - Used as fallback when no specific WS is specified

        See Also:
            GetDefaultVernacular, SetDefaultAnalysis
        """
        self._EnsureWriteEnabled()

        ws_obj = self._ResolveWS(ws)
        if not ws_obj:
            raise FP_WritingSystemError(str(ws))

        # Verify it's a vernacular WS
        vern_tags = self._GetAllVernacularWSTags()
        if ws_obj.Id not in vern_tags:
            raise FP_ParameterError(f"Writing system '{ws_obj.Id}' is not a vernacular writing system")

        # Set as default
        self.project.lp.DefaultVernacularWritingSystem = ws_obj

    @OperationsMethod
    def SetDefaultAnalysis(self, ws):
        """
        Set the default analysis writing system.

        Args:
            ws: IWritingSystemDefinition object or language tag (str)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ws is None
            FP_WritingSystemError: If writing system not found
            FP_ParameterError: If ws is not an analysis writing system

        Example:
            >>> # Set by object
            >>> ws = list(project.WritingSystems.GetAnalysis())[0]
            >>> project.WritingSystems.SetDefaultAnalysis(ws)

            >>> # Set by language tag
            >>> project.WritingSystems.SetDefaultAnalysis("en")

        Notes:
            - The writing system must be in the analysis list
            - This is the primary writing system for glosses and definitions
            - Used as fallback when no specific WS is specified

        See Also:
            GetDefaultAnalysis, SetDefaultVernacular
        """
        self._EnsureWriteEnabled()

        ws_obj = self._ResolveWS(ws)
        if not ws_obj:
            raise FP_WritingSystemError(str(ws))

        # Verify it's an analysis WS
        anal_tags = self._GetAllAnalysisWSTags()
        if ws_obj.Id not in anal_tags:
            raise FP_ParameterError(f"Writing system '{ws_obj.Id}' is not an analysis writing system")

        # Set as default
        self.project.lp.DefaultAnalysisWritingSystem = ws_obj

    @OperationsMethod
    def GetDefaultVernacular(self):
        """
        Get the default vernacular writing system.

        Returns:
            IWritingSystemDefinition: The default vernacular writing system

        Example:
            >>> ws = project.WritingSystems.GetDefaultVernacular()
            >>> name = project.WritingSystems.GetDisplayName(ws)
            >>> tag = project.WritingSystems.GetLanguageTag(ws)
            >>> print(f"Default vernacular: {name} ({tag})")
            Default vernacular: Kalaba (qaa-x-kal)

        Notes:
            - This is the primary vernacular writing system
            - Used as default for lexical entries
            - Every project must have a default vernacular WS

        See Also:
            SetDefaultVernacular, GetDefaultAnalysis
        """
        return self.project.lp.DefaultVernacularWritingSystem

    @OperationsMethod
    def GetDefaultAnalysis(self):
        """
        Get the default analysis writing system.

        Returns:
            IWritingSystemDefinition: The default analysis writing system

        Example:
            >>> ws = project.WritingSystems.GetDefaultAnalysis()
            >>> name = project.WritingSystems.GetDisplayName(ws)
            >>> tag = project.WritingSystems.GetLanguageTag(ws)
            >>> print(f"Default analysis: {name} ({tag})")
            Default analysis: English (en)

        Notes:
            - This is the primary analysis writing system
            - Used as default for glosses and definitions
            - Every project must have a default analysis WS

        See Also:
            SetDefaultAnalysis, GetDefaultVernacular
        """
        return self.project.lp.DefaultAnalysisWritingSystem

    # --- Utility Methods ---

    @OperationsMethod
    def GetDisplayName(self, ws):
        """
        Get the display name (UI label) for a writing system.

        Args:
            ws: IWritingSystemDefinition object or language tag (str)

        Returns:
            str: Display name (e.g., "English", "Kalaba")

        Raises:
            FP_NullParameterError: If ws is None
            FP_WritingSystemError: If writing system not found

        Example:
            >>> ws = list(project.WritingSystems.GetAll())[0]
            >>> name = project.WritingSystems.GetDisplayName(ws)
            >>> print(name)
            English

            >>> # By language tag
            >>> name = project.WritingSystems.GetDisplayName("en")
            >>> print(name)
            English

        See Also:
            GetLanguageTag, GetAll
        """
        ws_obj = self._ResolveWS(ws)
        if not ws_obj:
            raise FP_WritingSystemError(str(ws))

        return ws_obj.DisplayLabel or ws_obj.Id

    @OperationsMethod
    def GetLanguageTag(self, ws):
        """
        Get the language tag (BCP 47 identifier) for a writing system.

        Args:
            ws: IWritingSystemDefinition object

        Returns:
            str: Language tag (e.g., "en", "fr", "qaa-x-kal")

        Raises:
            FP_NullParameterError: If ws is None

        Example:
            >>> ws = list(project.WritingSystems.GetVernacular())[0]
            >>> tag = project.WritingSystems.GetLanguageTag(ws)
            >>> print(tag)
            qaa-x-kal

        Notes:
            - Returns BCP 47 language tag
            - Format: language[-script][-region][-variant][-extension]
            - Examples: "en", "en-US", "qaa-x-kal", "zh-Hans"

        See Also:
            GetDisplayName, Exists
        """
        self._ValidateParam(ws, "ws")

        return ws.Id

    @OperationsMethod
    def Exists(self, language_tag):
        """
        Check if a writing system with the given language tag exists and is active.

        Args:
            language_tag (str): Language tag to check (e.g., "en", "qaa-x-kal")

        Returns:
            bool: True if writing system exists and is active, False otherwise

        Raises:
            FP_NullParameterError: If language_tag is None

        Example:
            >>> if project.WritingSystems.Exists("en"):
            ...     print("English writing system is active")
            English writing system is active

            >>> if not project.WritingSystems.Exists("ar"):
            ...     print("Arabic writing system not found")
            Arabic writing system not found

        Notes:
            - Only checks active (vernacular or analysis) writing systems
            - Comparison is case-insensitive
            - Handles both '-' and '_' in tags

        See Also:
            GetAll, Create, Delete
        """
        self._ValidateParam(language_tag, "language_tag")

        return self._GetWSByTag(language_tag) is not None

    @OperationsMethod
    def GetBestString(self, string_obj):
        """
        Extract the best analysis or vernacular string from a MultiString or
        MultiUnicode object.

        This method intelligently selects the most appropriate string alternative
        from a multi-writing-system text object, preferring analysis writing
        systems first, then falling back to vernacular writing systems.

        Args:
            string_obj: IMultiUnicode or IMultiString object containing text in
                multiple writing systems

        Returns:
            str: The best available string, or empty string if no valid text found

        Raises:
            FP_NullParameterError: If string_obj is None
            FP_ParameterError: If string_obj is not IMultiUnicode or IMultiString

        Example:
            >>> # Get the best string from a lexeme form
            >>> entry = project.LexEntries.GetEntry("test")
            >>> best_text = project.WritingSystems.GetBestString(entry.LexemeFormOA.Form)
            >>> print(best_text)
            test

            >>> # Get best gloss from a sense
            >>> sense = entry.SensesOS[0]
            >>> best_gloss = project.WritingSystems.GetBestString(sense.Gloss)
            >>> print(best_gloss)
            a sample word

        Notes:
            - Prefers analysis writing systems over vernacular
            - Returns empty string for "***" (FLEx's null string marker)
            - Useful for extracting displayable text from multi-WS fields
            - This is a convenience method for common text extraction patterns

        See Also:
            GetAll, GetAnalysis, GetVernacular
        """
        self._ValidateParam(string_obj, "string_obj")

        # Import types locally to avoid circular imports
        from SIL.LCModel.Core.KernelInterfaces import IMultiUnicode, IMultiString

        if not isinstance(string_obj, (IMultiUnicode, IMultiString)):
            raise FP_ParameterError("GetBestString: string_obj must be IMultiUnicode or IMultiString")

        # Get the best alternative (analysis preferred, then vernacular)
        s = string_obj.BestAnalysisVernacularAlternative.Text

        # Return empty string for FLEx's null marker "***"
        return "" if s == "***" else s

    # --- Private Helper Methods ---

    def _GetAllVernacularWSTags(self):
        """
        Get set of all vernacular writing system tags.

        Returns:
            set: Set of vernacular WS language tags
        """
        return set(self.project.lp.CurVernWss.split())

    def _GetAllAnalysisWSTags(self):
        """
        Get set of all analysis writing system tags.

        Returns:
            set: Set of analysis WS language tags
        """
        return set(self.project.lp.CurAnalysisWss.split())

    def _NormalizeLangTag(self, language_tag):
        """
        Normalize language tag for comparison (lowercase, underscores to hyphens).

        Args:
            language_tag (str): Language tag to normalize

        Returns:
            str: Normalized tag
        """
        return language_tag.replace("_", "-").lower()

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

    def _ResolveWS(self, ws):
        """
        Resolve a writing system parameter to a WS object.

        Args:
            ws: Either IWritingSystemDefinition object or language tag (str)

        Returns:
            IWritingSystemDefinition or None: Writing system object or None
        """
        self._ValidateParam(ws, "ws")

        if isinstance(ws, str):
            return self._GetWSByTag(ws)
        else:
            # Already a writing system object
            return ws

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate operation is not applicable for writing systems.

        Writing systems are project-level configuration objects with unique
        identifiers and cannot be duplicated in the traditional sense.

        Raises:
            NotImplementedError: Always raised - writing systems cannot be duplicated.

        Notes:
            - Use Create() to create a new writing system with similar properties
            - Writing systems have unique language tags (BCP 47)
            - Each writing system must have a unique identifier
            - Duplication would create ambiguity in the WS system

        See Also:
            Create, Delete, GetAll
        """
        raise NotImplementedError("Writing systems cannot be duplicated. Use Create() to create a new writing system.")

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get syncable properties - NOT IMPLEMENTED for writing systems.

        Writing systems are linguistic configuration unique to each project and
        should not be synced between projects.

        Raises:
            NotImplementedError: Writing systems are not syncable
        """
        raise NotImplementedError(
            "Writing systems cannot be synced between projects. "
            "Writing systems are linguistic configuration unique to each project."
        )

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare writing systems - NOT IMPLEMENTED.

        Writing systems are linguistic configuration unique to each project and
        should not be synced between projects.

        Raises:
            NotImplementedError: Writing systems are not syncable
        """
        raise NotImplementedError(
            "Writing systems cannot be compared for sync. "
            "Writing systems are linguistic configuration unique to each project."
        )
