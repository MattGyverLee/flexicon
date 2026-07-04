#
#   PublicationOperations.py
#
#   Class: PublicationOperations
#          Publication and publishing workflow operations for FieldWorks Language
#          Explorer projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import FLEx LCM types
from SIL.LCModel import (
    ICmPossibility,
    ICmPossibilityFactory,
    ICmPossibilityRepository,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils
from System import DateTime

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
    FP_NullParameterError,
)
from ..BaseOperations import OperationsMethod, wrap_enumerable
from .possibility_item_base import PossibilityItemOperations


class PublicationOperations(PossibilityItemOperations):
    """
    This class provides operations for managing publications and publishing
    workflows in a FieldWorks project.

    Publications in FLEx define output formats for dictionary and text publishing.
    They specify page layouts, formatting options, divisions (e.g., main entries,
    minor entries), header/footer settings, and default publication types. These
    are used when exporting dictionaries or texts to various formats.

    Inherited CRUD Operations (from PossibilityItemOperations):
    - GetAll() - Get all publications (NOTE: override handles flat parameter)
    - Create() - Create a new publication
    - Delete() - Delete a publication
    - Duplicate() - Clone a publication
    - Find() - Find by name
    - Exists() - Check existence
    - GetName() / SetName() - Get/set name
    - GetDescription() / SetDescription() - Get/set description
    - GetGuid() - Get GUID
    - CompareTo() - Compare by name

    Domain-Specific Methods (PublicationOperations):
    - GetPageLayout() - Get page layout description
    - SetPageLayout() - Set page layout description
    - GetIsDefault() - Check if default publication
    - SetIsDefault() - Set default publication
    - GetPageHeight() - Get page height
    - SetPageHeight() - Set page height
    - GetPageWidth() - Get page width
    - SetPageWidth() - Set page width
    - GetDivisions() - Get publication divisions
    - AddDivision() - Add a division
    - GetHeaderFooter() - Get header/footer configuration
    - GetIsLandscape() - Check landscape orientation
    - GetSubPublications() - Get sub-publications
    - GetParent() - Get parent publication
    - GetDateCreated() - Get creation date
    - GetDateModified() - Get modification date

    This class should be accessed via FLExProject.Publications property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all publications
        for pub in project.Publications.GetAll():
            name = project.Publications.GetName(pub)
            is_default = project.Publications.GetIsDefault(pub)
            print(f"{name} (Default: {is_default})")

        # Create a new publication
        pub = project.Publications.Create("Web Dictionary")

        # Set page layout and formatting
        project.Publications.SetPageWidth(pub, 8.5)
        project.Publications.SetPageHeight(pub, 11.0)
        project.Publications.SetDescription(pub,
            "Dictionary layout for web publication")

        # Set as default publication
        project.Publications.SetIsDefault(pub, True)

        # Find a publication by name
        main_pub = project.Publications.Find("Main Dictionary")
        if main_pub:
            width = project.Publications.GetPageWidth(main_pub)
            height = project.Publications.GetPageHeight(main_pub)
            print(f"Page size: {width} x {height} inches")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize PublicationOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _get_item_class_name(self):
        """Get the item class name for error messages."""
        return "Publication"

    def _get_list_object(self):
        """Get the publications list container."""
        return self.project.lexDB.PublicationTypesOA

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, recursive=True, **kwargs):
        """
        Get all publications in the project.

        Args:
            recursive (bool): If True (default), returns every publication in
                the hierarchy (depth-first, parents before children). If
                False, returns only top-level publications and the caller
                must descend via GetSubPublications.

        Returns:
            list: List of ICmPossibility objects representing publications.

        Example:
            >>> for pub in project.Publications.GetAll():
            ...     print(project.Publications.GetName(pub))   # Includes variants at any depth

            >>> # Top-level only
            >>> for pub in project.Publications.GetAll(recursive=False):
            ...     print(project.Publications.GetName(pub))

        See Also:
            Find, GetSubPublications
        """
        self._RejectLegacyKwargs(kwargs, {
            "flat": ("recursive", "semantics inverted: flat=True is now recursive=True"),
        })
        list_obj = self._get_list_object()
        if not list_obj:
            return []

        if not recursive:
            return list(list_obj.PossibilitiesOS)

        all_pubs = []
        def walk(collection):
            for pub in collection:
                all_pubs.append(pub)
                if hasattr(pub, "SubPossibilitiesOS") and pub.SubPossibilitiesOS.Count > 0:
                    walk(pub.SubPossibilitiesOS)
        walk(list_obj.PossibilitiesOS)
        return all_pubs

    # --- Publishing Properties ---

    @OperationsMethod
    def GetPageLayout(self, publication_or_hvo, wsHandle=None):
        """
        Get the page layout description for a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: Page layout description, or empty string if not set.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> layout = project.Publications.GetPageLayout(pub)
            >>> print(layout)
            Two-column layout with headers and footers

        Notes:
            - Returns empty string if page layout not set
            - Layout description is free-form text
            - Can describe columns, margins, orientation, etc.
            - Different from page dimensions (width/height)

        See Also:
            SetPageLayout, GetPageWidth, GetPageHeight
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)
        wsHandle = self._PossibilityItemOperations__WSHandle(wsHandle)

        # Use Abbreviation field for page layout description
        if hasattr(publication, "Abbreviation"):
            layout = ITsString(publication.Abbreviation.get_String(wsHandle)).Text
            return layout or ""

        return ""

    @OperationsMethod
    def SetPageLayout(self, publication_or_hvo, layout, wsHandle=None):
        """
        Set the page layout description for a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.
            layout (str): Page layout description.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If publication_or_hvo or layout is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> project.Publications.SetPageLayout(pub,
            ...     "Two-column layout with running headers")

            >>> # Clear layout description
            >>> project.Publications.SetPageLayout(pub, "")

        Notes:
            - Empty string is allowed (clears the layout description)
            - Layout description is stored in the specified writing system
            - Use to describe columns, margins, orientation, etc.
            - Actual page dimensions set with SetPageWidth/SetPageHeight

        See Also:
            GetPageLayout, SetPageWidth, SetPageHeight
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(publication_or_hvo, "publication_or_hvo")
        self._ValidateParam(layout, "layout")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)
        wsHandle = self._PossibilityItemOperations__WSHandle(wsHandle)

        if hasattr(publication, "Abbreviation"):
            with self._TransactionCM("Set publication page layout"):
                mkstr = TsStringUtils.MakeString(layout, wsHandle)
                publication.Abbreviation.set_String(wsHandle, mkstr)

                # Update modification date
                publication.DateModified = DateTime.Now

    @OperationsMethod
    def GetIsDefault(self, publication_or_hvo):
        """
        Check if a publication is the default publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.

        Returns:
            bool: True if this is the default publication, False otherwise.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> for pub in project.Publications.GetAll():
            ...     name = project.Publications.GetName(pub)
            ...     is_default = project.Publications.GetIsDefault(pub)
            ...     default_marker = " [DEFAULT]" if is_default else ""
            ...     print(f"{name}{default_marker}")
            Main Dictionary [DEFAULT]
            Root-based Dictionary
            Thematic Dictionary

            >>> # Find the default publication
            >>> default_pub = None
            >>> for pub in project.Publications.GetAll():
            ...     if project.Publications.GetIsDefault(pub):
            ...         default_pub = pub
            ...         break

        Notes:
            - Only one publication can be the default
            - Default publication is used when no specific publication is selected
            - Returns False if publication is not default
            - If no default is set, all publications return False

        See Also:
            SetIsDefault, Find
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        # Check if this publication is the default
        # Default is typically the first publication or marked by IsDefault property
        pub_list = self.project.lexDB.PublicationTypesOA
        if pub_list and pub_list.PossibilitiesOS.Count > 0:
            # The default publication is typically the first one
            default_pub = pub_list.PossibilitiesOS[0]
            return publication.Hvo == default_pub.Hvo

        return False

    @OperationsMethod
    def SetIsDefault(self, publication_or_hvo, is_default):
        """
        Set whether a publication is the default publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.
            is_default (bool): True to make this the default, False otherwise.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If publication_or_hvo or is_default is None.

        Example:
            >>> # Set a publication as default
            >>> pub = project.Publications.Find("Web Dictionary")
            >>> project.Publications.SetIsDefault(pub, True)

            >>> # Remove default status (sets first publication as default)
            >>> project.Publications.SetIsDefault(pub, False)

        Notes:
            - Only one publication can be default at a time
            - Setting a publication as default makes it the first in the list
            - If is_default is False, publication is moved from first position
            - Default publication is used when no specific publication is selected

        See Also:
            GetIsDefault, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(publication_or_hvo, "publication_or_hvo")
        self._ValidateParam(is_default, "is_default")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        pub_list = self.project.lexDB.PublicationTypesOA
        if not pub_list:
            return

        # To make a publication default, move it to the first position
        with self._TransactionCM("Set default publication"):
            if is_default:
                # Remove from current position
                if publication in pub_list.PossibilitiesOS:
                    pub_list.PossibilitiesOS.Remove(publication)
                # Insert at first position
                pub_list.PossibilitiesOS.Insert(0, publication)
            else:
                # If removing default status, move to end
                if publication in pub_list.PossibilitiesOS:
                    current_index = pub_list.PossibilitiesOS.IndexOf(publication)
                    if current_index == 0:  # Is currently default
                        pub_list.PossibilitiesOS.Remove(publication)
                        pub_list.PossibilitiesOS.Add(publication)

    # --- Formatting Properties ---

    @OperationsMethod
    def GetPageHeight(self, publication_or_hvo):
        """
        Get the page height for a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.

        Returns:
            float or None: Page height in inches, or None if not set.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> height = project.Publications.GetPageHeight(pub)
            >>> if height:
            ...     print(f"Page height: {height} inches")
            Page height: 11.0 inches

            >>> # Get both dimensions
            >>> width = project.Publications.GetPageWidth(pub)
            >>> height = project.Publications.GetPageHeight(pub)
            >>> if width and height:
            ...     print(f"Page size: {width}\" x {height}\"")

        Notes:
            - Returns None if page height is not set
            - Height is in inches (standard US measurement)
            - Common sizes: 11.0 (Letter), 11.69 (A4), 14.0 (Legal)
            - Use with GetPageWidth() to get full page dimensions

        See Also:
            SetPageHeight, GetPageWidth
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        # Store in SortKey2 field (encoded as integer, divide by 1000 for inches)
        if hasattr(publication, "SortKey2") and publication.SortKey2 != 0:
            return float(publication.SortKey2) / 1000.0

        return None

    @OperationsMethod
    def SetPageHeight(self, publication_or_hvo, height):
        """
        Set the page height for a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.
            height (float): Page height in inches.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If publication_or_hvo or height is None.
            FP_ParameterError: If height is not positive.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> # Set letter-size height
            >>> project.Publications.SetPageHeight(pub, 11.0)

            >>> # Set A4 height
            >>> project.Publications.SetPageHeight(pub, 11.69)

            >>> # Set legal-size height
            >>> project.Publications.SetPageHeight(pub, 14.0)

        Notes:
            - Height must be positive
            - Height is stored in inches
            - Common heights: 11.0 (Letter), 11.69 (A4), 14.0 (Legal)
            - Set both width and height for complete page dimensions

        See Also:
            GetPageHeight, SetPageWidth
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(publication_or_hvo, "publication_or_hvo")
        self._ValidateParam(height, "height")

        try:
            h = float(height)
        except (TypeError, ValueError):
            raise FP_ParameterError("Height must be numeric")

        if h <= 0:
            raise FP_ParameterError("Height must be positive")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        # Store in SortKey2 field (multiply by 1000 to store as integer)
        if hasattr(publication, "SortKey2"):
            with self._TransactionCM("Set publication page height"):
                publication.SortKey2 = int(h * 1000)

                # Update modification date
                publication.DateModified = DateTime.Now

    @OperationsMethod
    def GetPageWidth(self, publication_or_hvo):
        """
        Get the page width for a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.

        Returns:
            float or None: Page width in inches, or None if not set.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> width = project.Publications.GetPageWidth(pub)
            >>> if width:
            ...     print(f"Page width: {width} inches")
            Page width: 8.5 inches

            >>> # Check if dimensions are set
            >>> width = project.Publications.GetPageWidth(pub)
            >>> height = project.Publications.GetPageHeight(pub)
            >>> if width and height:
            ...     aspect = width / height
            ...     print(f"Aspect ratio: {aspect:.2f}")

        Notes:
            - Returns None if page width is not set
            - Width is in inches (standard US measurement)
            - Common sizes: 8.5 (Letter/Legal), 8.27 (A4)
            - Use with GetPageHeight() to get full page dimensions

        See Also:
            SetPageWidth, GetPageHeight
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        # Store in SortKey field (encoded as integer, divide by 1000 for inches)
        if hasattr(publication, "SortKey") and publication.SortKey != 0:
            return float(publication.SortKey) / 1000.0

        return None

    @OperationsMethod
    def SetPageWidth(self, publication_or_hvo, width):
        """
        Set the page width for a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.
            width (float): Page width in inches.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If publication_or_hvo or width is None.
            FP_ParameterError: If width is not positive.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> # Set letter-size width
            >>> project.Publications.SetPageWidth(pub, 8.5)

            >>> # Set A4 width
            >>> project.Publications.SetPageWidth(pub, 8.27)

            >>> # Set custom width
            >>> project.Publications.SetPageWidth(pub, 7.0)

        Notes:
            - Width must be positive
            - Width is stored in inches
            - Common widths: 8.5 (Letter/Legal), 8.27 (A4)
            - Set both width and height for complete page dimensions

        See Also:
            GetPageWidth, SetPageHeight
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(publication_or_hvo, "publication_or_hvo")
        self._ValidateParam(width, "width")

        try:
            w = float(width)
        except (TypeError, ValueError):
            raise FP_ParameterError("Width must be numeric")

        if w <= 0:
            raise FP_ParameterError("Width must be positive")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        # Store in SortKey field (multiply by 1000 to store as integer)
        if hasattr(publication, "SortKey"):
            with self._TransactionCM("Set publication page width"):
                publication.SortKey = int(w * 1000)

                # Update modification date
                publication.DateModified = DateTime.Now

    # --- Divisions and Structure ---

    @OperationsMethod
    def GetDivisions(self, publication_or_hvo):
        """
        Get the publication divisions (e.g., main entries, minor entries).

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.

        Returns:
            list: List of ICmPossibility objects representing divisions.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> divisions = project.Publications.GetDivisions(pub)
            >>> for div in divisions:
            ...     name = ITsString(div.Name.BestAnalysisAlternative).Text
            ...     print(f"Division: {name}")
            Division: Main Entries
            Division: Minor Entries
            Division: Back Matter

        Notes:
            - Returns empty list if no divisions
            - Divisions organize content into sections
            - Common divisions: Main Entries, Minor Entries, Subentries
            - Divisions are represented as sub-possibilities

        See Also:
            AddDivision, GetSubPublications
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        # Divisions are stored as sub-possibilities
        if hasattr(publication, "SubPossibilitiesOS"):
            return list(publication.SubPossibilitiesOS)

        return []

    @OperationsMethod
    def AddDivision(self, publication_or_hvo, division_name, wsHandle=None):
        """
        Add a division to a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.
            division_name (str): Name of the division (e.g., "Main Entries").
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmPossibility: The newly created division object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If publication_or_hvo or division_name is None.
            FP_ParameterError: If division_name is empty.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> # Add standard divisions
            >>> main = project.Publications.AddDivision(pub, "Main Entries")
            >>> minor = project.Publications.AddDivision(pub, "Minor Entries")
            >>> back = project.Publications.AddDivision(pub, "Back Matter")

            >>> # Verify divisions were added
            >>> divisions = project.Publications.GetDivisions(pub)
            >>> print(f"Publication has {len(divisions)} divisions")

        Notes:
            - Division name should be descriptive
            - Common divisions: Main Entries, Minor Entries, Subentries
            - Divisions organize publication content
            - Multiple divisions can be added to one publication

        See Also:
            GetDivisions, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(publication_or_hvo, "publication_or_hvo")
        self._ValidateParam(division_name, "division_name")

        if not division_name or not division_name.strip():
            raise FP_ParameterError("Division name cannot be empty")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)
        wsHandle = self._PossibilityItemOperations__WSHandle(wsHandle)

        # Create the new division using the factory
        factory = self.project.project.ServiceLocator.GetService(ICmPossibilityFactory)

        with self._TransactionCM(f"Add division {division_name!r}"):
            new_division = factory.Create()

            # Add to publication's sub-possibilities (must be done before setting properties)
            if hasattr(publication, "SubPossibilitiesOS"):
                publication.SubPossibilitiesOS.Add(new_division)

            # Set name
            mkstr_name = TsStringUtils.MakeString(division_name, wsHandle)
            new_division.Name.set_String(wsHandle, mkstr_name)

            # Set creation date
            new_division.DateCreated = DateTime.Now

            return new_division

    @OperationsMethod
    def GetHeaderFooter(self, publication_or_hvo, wsHandle=None):
        """
        Get the header/footer configuration for a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: Header/footer configuration text, or empty string if not set.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> header = project.Publications.GetHeaderFooter(pub)
            >>> print(header)
            Header: Dictionary title | Page number
            Footer: Copyright notice

        Notes:
            - Returns empty string if header/footer not set
            - Can describe header and footer content
            - Free-form text description
            - Actual header/footer rendering depends on export format

        See Also:
            GetPageLayout, GetDescription
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)
        wsHandle = self._PossibilityItemOperations__WSHandle(wsHandle)

        # Use Comment field for header/footer information
        if hasattr(publication, "Comment"):
            header = ITsString(publication.Comment.get_String(wsHandle)).Text
            return header or ""

        return ""

    @OperationsMethod
    def GetIsLandscape(self, publication_or_hvo):
        """
        Check if publication uses landscape orientation.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.

        Returns:
            bool: True if landscape orientation, False if portrait or not set.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> is_landscape = project.Publications.GetIsLandscape(pub)
            >>> if is_landscape:
            ...     print("Landscape orientation")
            ... else:
            ...     print("Portrait orientation")
            Portrait orientation

            >>> # Check orientation and page dimensions
            >>> width = project.Publications.GetPageWidth(pub)
            >>> height = project.Publications.GetPageHeight(pub)
            >>> is_landscape = project.Publications.GetIsLandscape(pub)
            >>> orientation = "Landscape" if is_landscape else "Portrait"
            >>> print(f"{orientation}: {width}\" x {height}\"")
            Portrait: 8.5" x 11.0"

        Notes:
            - READ-ONLY property - cannot be set directly
            - Orientation is typically inferred from page width vs. height
            - True indicates landscape (width > height)
            - False indicates portrait (height >= width)
            - Returns False if orientation not set or if dimensions are equal
            - Used when exporting dictionaries or texts

        See Also:
            GetPageWidth, GetPageHeight, GetPageLayout
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        # Check for IsLandscape property
        if hasattr(publication, "IsLandscape"):
            return bool(publication.IsLandscape)

        return False

    # --- Hierarchical Operations ---

    @OperationsMethod
    def GetSubPublications(self, publication_or_hvo, recursive=True):
        """
        Get the sub-publications of a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.
            recursive (bool): If True (default), returns every descendant
                sub-publication (depth-first, parents before children). If
                False, returns only direct children.

        Returns:
            list: List of ICmPossibility sub-publication objects.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> for sub in project.Publications.GetSubPublications(pub):
            ...     print(project.Publications.GetName(sub))   # All descendants

            >>> # Direct children only
            >>> for sub in project.Publications.GetSubPublications(pub, recursive=False):
            ...     print(project.Publications.GetName(sub))

        See Also:
            GetParent, GetDivisions
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        if not hasattr(publication, "SubPossibilitiesOS"):
            return []

        if not recursive:
            return list(publication.SubPossibilitiesOS)

        result = []
        def walk(collection):
            for child in collection:
                result.append(child)
                if hasattr(child, "SubPossibilitiesOS") and child.SubPossibilitiesOS.Count > 0:
                    walk(child.SubPossibilitiesOS)
        walk(publication.SubPossibilitiesOS)
        return result

    @OperationsMethod
    def GetParent(self, publication_or_hvo):
        """
        Get the parent publication of a sub-publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.

        Returns:
            ICmPossibility or None: The parent publication, or None if top-level.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Web Dictionary Variant")
            >>> parent = project.Publications.GetParent(pub)
            >>> if parent:
            ...     parent_name = project.Publications.GetName(parent)
            ...     print(f"Parent: {parent_name}")

        Notes:
            - Returns None for top-level publications
            - Parent is determined by ownership hierarchy
            - Use for building breadcrumb navigation

        See Also:
            GetSubPublications
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)
        owner = publication.Owner

        # Check if owner is a publication (sub-publication) or the list (top-level)
        if owner and hasattr(owner, "ClassName"):
            if owner.ClassName == "CmPossibility":
                return ICmPossibility(owner)

        return None

    # --- Metadata Operations ---

    @OperationsMethod
    def GetDateCreated(self, publication_or_hvo):
        """
        Get the creation date of a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.

        Returns:
            System.DateTime or None: The creation date/time, or None if not set.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> date = project.Publications.GetDateCreated(pub)
            >>> if date:
            ...     print(f"Created: {date}")
            Created: 11/23/2025 10:30:45 AM

            >>> # Sort publications by creation date
            >>> pubs = project.Publications.GetAll()
            >>> sorted_pubs = sorted(pubs,
            ...     key=lambda p: project.Publications.GetDateCreated(p) or DateTime.MinValue)

        Notes:
            - DateCreated is set automatically when publication is created
            - Returns System.DateTime object
            - Can be None for publications without creation date
            - Use for tracking when publications were added to project

        See Also:
            GetDateModified, Create
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        if hasattr(publication, "DateCreated"):
            return publication.DateCreated

        return None

    @OperationsMethod
    def GetDateModified(self, publication_or_hvo):
        """
        Get the last modification date of a publication.

        Args:
            publication_or_hvo: Either an ICmPossibility publication object or its HVO.

        Returns:
            System.DateTime or None: The modification date/time, or None if not set.

        Raises:
            FP_NullParameterError: If publication_or_hvo is None.

        Example:
            >>> pub = project.Publications.Find("Main Dictionary")
            >>> modified = project.Publications.GetDateModified(pub)
            >>> if modified:
            ...     print(f"Last modified: {modified}")
            Last modified: 11/23/2025 2:15:30 PM

            >>> # Find recently modified publications
            >>> from System import DateTime
            >>> one_week_ago = DateTime.Now.AddDays(-7)
            >>> pubs = project.Publications.GetAll()
            >>> recent = [p for p in pubs
            ...     if project.Publications.GetDateModified(p) and
            ...        project.Publications.GetDateModified(p) > one_week_ago]

        Notes:
            - DateModified is updated when properties change
            - Returns System.DateTime object
            - May be None if publication has never been modified
            - Useful for tracking publication updates

        See Also:
            GetDateCreated, SetName, SetDescription
        """
        self._ValidateParam(publication_or_hvo, "publication_or_hvo")

        publication = self._PossibilityItemOperations__ResolveObject(publication_or_hvo)

        if hasattr(publication, "DateModified"):
            return publication.DateModified

        return None
