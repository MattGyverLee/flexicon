#
#   ScrTxtParaOperations.py
#
#   Class: ScrTxtParaOperations
#          Scripture text paragraph operations for FieldWorks Language Explorer
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
    IScrSection,
    IScrTxtPara,
    IScrTxtParaFactory,
    IStStyle,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ScrTxtParaOperations(BaseOperations):
    """
    This class provides operations for managing Scripture text paragraphs in a
    FieldWorks project.

    Scripture paragraphs are the basic text units within sections, each with
    text content and a paragraph style (Normal, Poetry, Quote, etc.).

    This class should be accessed via FLExProject.ScrTxtParas property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a section
        genesis = project.ScrBooks.Find(1)
        section = project.ScrSections.Find(genesis, 0)

        # Create a paragraph
        para = project.ScrTxtParas.Create(
            section,
            "In the beginning God created the heavens and the earth.",
            "Normal"
        )

        # Get paragraph text
        text = project.ScrTxtParas.GetText(para)

        # Set paragraph style
        project.ScrTxtParas.SetStyleName(para, "Poetry")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ScrTxtParaOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, section_or_hvo, text, style_name="Normal"):
        """
        Create a new Scripture paragraph in a section.

        Args:
            section_or_hvo: Either an IScrSection object or its HVO
            text (str): The paragraph text content
            style_name (str, optional): Paragraph style name. Defaults to "Normal".
                Common styles: "Normal", "Poetry", "Quote", "List Item"

        Returns:
            IScrTxtPara: The newly created paragraph object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If section_or_hvo or text is None
            FP_ParameterError: If section doesn't exist or style not found

        Example:
            >>> section = project.ScrSections.Find(genesis, 0)
            >>> para = project.ScrTxtParas.Create(
            ...     section,
            ...     "In the beginning God created the heavens and the earth."
            ... )

            >>> # Create poetry paragraph
            >>> para2 = project.ScrTxtParas.Create(
            ...     section,
            ...     "The LORD is my shepherd",
            ...     "Poetry"
            ... )

        Notes:
            - Paragraph is appended to section content
            - Paragraph GUID is auto-generated
            - Default style is "Normal"
            - Text can be empty string

        See Also:
            Delete, Find, GetText, SetText
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(section_or_hvo, "section_or_hvo")
        self._ValidateParam(text, "text")

        # Resolve to section object
        section = self.__ResolveSection(section_or_hvo)

        with self._TransactionCM("Create paragraph"):
            # Ensure section has content StText
            if not section.ContentOA:
                from SIL.LCModel import IStTextFactory

                text_factory = self.project.project.ServiceLocator.GetService(IStTextFactory)
                section.ContentOA = text_factory.Create()

            # Find the style
            style = self.__FindStyle(style_name)
            if not style:
                raise FP_ParameterError(f"Paragraph style '{style_name}' not found")

            # Create the new paragraph using the factory
            factory = self.project.project.ServiceLocator.GetService(IScrTxtParaFactory)
            new_para = factory.Create()

            # Add to section content (must be done before setting properties)
            section.ContentOA.ParagraphsOS.Add(new_para)

            # Set the text (Contents is ITsString, assign directly)
            wsHandle = self.project.project.DefaultVernWs
            mkstr = TsStringUtils.MakeString(text, wsHandle)
            new_para.Contents = mkstr

            # Set the style
            new_para.StyleRules = style

            return new_para

    @OperationsMethod
    def Delete(self, para_or_hvo):
        """
        Delete a Scripture paragraph from the FLEx project.

        Args:
            para_or_hvo: Either an IScrTxtPara object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If para_or_hvo is None
            FP_ParameterError: If paragraph doesn't exist

        Example:
            >>> para = project.ScrTxtParas.Find(section, 0)
            >>> if para:
            ...     project.ScrTxtParas.Delete(para)

        Warning:
            - This is a destructive operation
            - Cannot be undone

        Notes:
            - Paragraph is removed from its parent section

        See Also:
            Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(para_or_hvo, "para_or_hvo")

        # Resolve to paragraph object
        para = self.__ResolveObject(para_or_hvo)

        # Delete the paragraph (LCM handles removal from repository)
        para.Delete()

    @OperationsMethod
    def Find(self, section_or_hvo, index):
        """
        Find a Scripture paragraph by index within a section.

        Args:
            section_or_hvo: Either an IScrSection object or its HVO
            index (int): The zero-based index of the paragraph in the section

        Returns:
            IScrTxtPara or None: The paragraph object if found, None otherwise

        Raises:
            FP_NullParameterError: If section_or_hvo or index is None

        Example:
            >>> section = project.ScrSections.Find(genesis, 0)
            >>> # Get first paragraph
            >>> para = project.ScrTxtParas.Find(section, 0)
            >>> if para:
            ...     text = project.ScrTxtParas.GetText(para)
            ...     print(f"Paragraph: {text}")

            >>> # Get third paragraph
            >>> para3 = project.ScrTxtParas.Find(section, 2)

        Notes:
            - Returns None if index out of range
            - Index is zero-based (0 = first paragraph)
            - Use GetAll() to get all paragraphs

        See Also:
            GetAll, Create
        """
        self._ValidateParam(section_or_hvo, "section_or_hvo")
        self._ValidateParam(index, "index")

        # Resolve to section object
        section = self.__ResolveSection(section_or_hvo)

        if not section.ContentOA:
            return None

        # Check if index is valid
        if index < 0 or index >= section.ContentOA.ParagraphsOS.Count:
            return None

        return section.ContentOA.ParagraphsOS[index]

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, section_or_hvo):
        """
        Get all Scripture paragraphs in a section.

        Args:
            section_or_hvo: Either an IScrSection object or its HVO

        Returns:
            list: List of IScrTxtPara objects (empty list if none)

        Raises:
            FP_NullParameterError: If section_or_hvo is None

        Example:
            >>> section = project.ScrSections.Find(genesis, 0)
            >>> paras = project.ScrTxtParas.GetAll(section)
            >>> for i, para in enumerate(paras):
            ...     text = project.ScrTxtParas.GetText(para)
            ...     print(f"{i+1}. {text}")

        Notes:
            - Returns empty list if section has no paragraphs
            - Paragraphs are in database order
            - Same as project.ScrSections.GetContent(section)

        See Also:
            Find, Create
        """
        self._ValidateParam(section_or_hvo, "section_or_hvo")

        # Resolve to section object
        section = self.__ResolveSection(section_or_hvo)

        if not section.ContentOA:
            return []

        return list(section.ContentOA.ParagraphsOS)

    # --- Paragraph Properties ---

    @OperationsMethod
    def GetText(self, para_or_hvo, wsHandle=None):
        """
        Get the text content of a Scripture paragraph.

        Args:
            para_or_hvo: Either an IScrTxtPara object or its HVO
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The paragraph text (empty string if not set)

        Raises:
            FP_NullParameterError: If para_or_hvo is None

        Example:
            >>> para = project.ScrTxtParas.Find(section, 0)
            >>> text = project.ScrTxtParas.GetText(para)
            >>> print(text)
            In the beginning God created the heavens and the earth.

            >>> # Get in specific writing system
            >>> text_fr = project.ScrTxtParas.GetText(para,
            ...                                        project.WSHandle('fr'))

        Notes:
            - Returns empty string if text not set
            - Text can be in multiple writing systems

        See Also:
            SetText, Create
        """
        self._ValidateParam(para_or_hvo, "para_or_hvo")

        para = self.__ResolveObject(para_or_hvo)
        # Note: Contents is ITsString, not IMultiUnicode
        text = para.Contents.Text if para.Contents else ""
        return text or ""

    @OperationsMethod
    def SetText(self, para_or_hvo, text, wsHandle=None):
        """
        Set the text content of a Scripture paragraph.

        Args:
            para_or_hvo: Either an IScrTxtPara object or its HVO
            text (str): The new paragraph text
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If para_or_hvo or text is None

        Example:
            >>> para = project.ScrTxtParas.Find(section, 0)
            >>> project.ScrTxtParas.SetText(
            ...     para,
            ...     "In the beginning God created the heavens and the earth."
            ... )

            >>> # Set in specific writing system
            >>> project.ScrTxtParas.SetText(
            ...     para,
            ...     "Au commencement, Dieu créa les cieux et la terre.",
            ...     project.WSHandle('fr')
            ... )

        Notes:
            - Empty text is allowed
            - Text can be set in multiple writing systems

        See Also:
            GetText, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(para_or_hvo, "para_or_hvo")
        self._ValidateParam(text, "text")

        para = self.__ResolveObject(para_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Contents is ITsString, assign directly
        mkstr = TsStringUtils.MakeString(text, wsHandle)
        para.Contents = mkstr

    @OperationsMethod
    def GetStyleName(self, para_or_hvo):
        """
        Get the style name of a Scripture paragraph.

        Args:
            para_or_hvo: Either an IScrTxtPara object or its HVO

        Returns:
            str: The paragraph style name (empty string if not set)

        Raises:
            FP_NullParameterError: If para_or_hvo is None

        Example:
            >>> para = project.ScrTxtParas.Find(section, 0)
            >>> style = project.ScrTxtParas.GetStyleName(para)
            >>> print(style)
            Normal

        Notes:
            - Returns empty string if style not set
            - Common styles: Normal, Poetry, Quote, List Item

        See Also:
            SetStyleName, Create
        """
        self._ValidateParam(para_or_hvo, "para_or_hvo")

        para = self.__ResolveObject(para_or_hvo)

        if not para.StyleRules:
            return ""

        return para.StyleRules.Name or ""

    @OperationsMethod
    def SetStyleName(self, para_or_hvo, style_name):
        """
        Set the style name of a Scripture paragraph.

        Args:
            para_or_hvo: Either an IScrTxtPara object or its HVO
            style_name (str): The paragraph style name
                Common styles: "Normal", "Poetry", "Quote", "List Item"

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If para_or_hvo or style_name is None
            FP_ParameterError: If style not found

        Example:
            >>> para = project.ScrTxtParas.Find(section, 0)
            >>> project.ScrTxtParas.SetStyleName(para, "Poetry")

            >>> # Check new style
            >>> print(project.ScrTxtParas.GetStyleName(para))
            Poetry

        Notes:
            - Style must exist in the project
            - Common styles: Normal, Poetry, Quote, List Item
            - Style affects paragraph formatting

        See Also:
            GetStyleName, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(para_or_hvo, "para_or_hvo")
        self._ValidateParam(style_name, "style_name")

        para = self.__ResolveObject(para_or_hvo)

        # Find the style
        style = self.__FindStyle(style_name)
        if not style:
            raise FP_ParameterError(f"Paragraph style '{style_name}' not found")

        para.StyleRules = style

    # --- Private Helper Methods ---

    def __ResolveObject(self, para_or_hvo):
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

    def __ResolveSection(self, section_or_hvo):
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

    def __FindStyle(self, style_name):
        """
        Find a paragraph style by name.

        Args:
            style_name (str): The style name to search for

        Returns:
            IStStyle or None: The style object if found, None otherwise
        """
        if not style_name:
            return None

        # Get the style repository
        style_sheet = self.project.lp.StylesOC
        if not style_sheet:
            return None

        # Search for the style
        for style in style_sheet:
            if style.Name == style_name:
                return style

        return None
