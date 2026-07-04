#
#   OverlayOperations.py
#
#   Class: OverlayOperations
#          Discourse chart overlay and layer management operations for FieldWorks
#          Language Explorer projects via SIL Language and Culture Model (LCM) API.
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)

import clr

clr.AddReference("System")
import System

from SIL.LCModel import (
    IDsConstChart,
    IDsConstChartFactory,
    ICmPossibility,
    ICmPossibilityFactory,
)

try:
    from SIL.LCModel import DsConstChartTags
except ImportError:
    # Mock for testing without FieldWorks installed
    class DsConstChartTags:
        kClassId = 0

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

from ..FLExProject import (
    FP_ParameterError,
    FP_NullParameterError,
)
from ..BaseOperations import OperationsMethod
from .possibility_item_base import PossibilityItemOperations


class OverlayOperations(PossibilityItemOperations):
    """
    Discourse chart overlay and layer management operations for FLEx projects.

    This class provides methods for creating and managing overlays (layers) in
    discourse constituent charts. Overlays allow multiple levels of analysis to
    be displayed in the same chart, with each overlay representing a different
    analytical perspective or feature set.

    Overlays can be toggled on/off for visibility and have customizable display
    order. They are used to organize complex chart analyses by separating different
    aspects of discourse structure into manageable layers.

    Inherited CRUD Operations (from PossibilityItemOperations):
    - GetAll() - Get all overlays (NOTE: requires chart context, see special handling)
    - Create() - Create a new overlay
    - Delete() - Delete an overlay
    - Duplicate() - Clone an overlay
    - Find() - Find by name
    - Exists() - Check existence
    - GetName() / SetName() - Get/set name
    - GetDescription() / SetDescription() - Get/set description
    - GetGuid() - Get GUID
    - CompareTo() - Compare by name

    Domain-Specific Methods (OverlayOperations):
    - IsVisible() - Check visibility
    - SetVisible() - Set visibility
    - GetDisplayOrder() - Get display order
    - SetDisplayOrder() - Set display order
    - GetElements() - Get overlay elements
    - AddElement() - Add element to overlay
    - RemoveElement() - Remove element from overlay
    - GetChart() - Get parent chart
    - GetPossItems() - Get possibility items
    - FindByChart() - Find overlays for a chart
    - GetVisibleOverlays() - Get visible overlays for a chart

    Note:
        Overlays are specific to constituent charts (IConstChart). They provide
        a way to layer multiple analytical perspectives in a single chart view.
        GetAll() requires chart context - use FindByChart() instead for chart-specific queries.

    Usage::

        from flexlibs2 import FLExProject, DiscourseOperations, OverlayOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        discourse_ops = DiscourseOperations(project)
        overlay_ops = OverlayOperations(project)

        # Get a chart
        text = list(project.Texts.GetAll())[0]
        charts = list(discourse_ops.GetAllCharts(text))
        chart = charts[0]

        # Get overlays for the chart
        overlays = list(overlay_ops.FindByChart(chart))
        print(f"Chart has {len(overlays)} overlays")

        # Create a new overlay
        overlay = overlay_ops.Create("Participants")
        overlay_ops.SetDescription(overlay, "Track participant chains")

        # Configure visibility and display order
        overlay_ops.SetVisible(overlay, True)
        overlay_ops.SetDisplayOrder(overlay, 1)

        # Get visible overlays
        visible = list(overlay_ops.GetVisibleOverlays(chart))
        print(f"Chart has {len(visible)} visible overlays")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize OverlayOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _get_item_class_name(self):
        """Get the item class name for error messages."""
        return "Overlay"

    def _get_list_object(self):
        """Get the overlay list container.

        Note: Overlays are chart-scoped, not project-wide.
        Returns None because overlays don't have a single project list.
        Use FindByChart() to get overlays for a specific chart.
        """
        return None

    # --- Visibility Operations ---

    @OperationsMethod
    def IsVisible(self, overlay_or_hvo):
        """
        Check if an overlay is visible in its chart.

        Args:
            overlay_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            bool: True if the overlay is visible, False otherwise.

        Raises:
            FP_NullParameterError: If overlay_or_hvo is None.

        Example:
            >>> overlay = project.Overlay.Find("Participants")
            >>> if project.Overlay.IsVisible(overlay):
            ...     print("Overlay is visible")

        See Also:
            SetVisible, GetDisplayOrder
        """
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        overlay = self._PossibilityItemOperations__ResolveObject(overlay_or_hvo)

        # Overlays have a visibility flag in the model
        if hasattr(overlay, "IsVisibleRA"):
            return bool(overlay.IsVisibleRA)
        elif hasattr(overlay, "Hidden"):
            return not overlay.Hidden
        return True

    @OperationsMethod
    def SetVisible(self, overlay_or_hvo, visible):
        """
        Set the visibility of an overlay in its chart.

        Args:
            overlay_or_hvo: Either an ICmPossibility object or its HVO.
            visible (bool): True to show, False to hide.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If overlay_or_hvo is None.

        Example:
            >>> overlay = project.Overlay.Find("Participants")
            >>> project.Overlay.SetVisible(overlay, True)

        See Also:
            IsVisible, GetDisplayOrder
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        overlay = self._PossibilityItemOperations__ResolveObject(overlay_or_hvo)

        # Set visibility flag
        if hasattr(overlay, "IsVisibleRA"):
            overlay.IsVisibleRA = bool(visible)
        elif hasattr(overlay, "Hidden"):
            overlay.Hidden = not visible

    # --- Display Order Operations ---

    @OperationsMethod
    def GetDisplayOrder(self, overlay_or_hvo):
        """
        Get the display order of an overlay in its chart.

        Args:
            overlay_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            int: Display order (typically 0-based or 1-based depending on chart).

        Raises:
            FP_NullParameterError: If overlay_or_hvo is None.

        Example:
            >>> overlay = project.Overlay.Find("Participants")
            >>> order = project.Overlay.GetDisplayOrder(overlay)
            >>> print(f"Display order: {order}")
            Display order: 1

        See Also:
            SetDisplayOrder, IsVisible
        """
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        overlay = self._PossibilityItemOperations__ResolveObject(overlay_or_hvo)

        # Display order is typically in a numeric field
        if hasattr(overlay, "SortSpec"):
            return overlay.SortSpec
        return 0

    @OperationsMethod
    def SetDisplayOrder(self, overlay_or_hvo, order):
        """
        Set the display order of an overlay in its chart.

        Args:
            overlay_or_hvo: Either an ICmPossibility object or its HVO.
            order (int): Display order value.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If overlay_or_hvo is None.
            FP_ParameterError: If order is negative.

        Example:
            >>> overlay = project.Overlay.Find("Participants")
            >>> project.Overlay.SetDisplayOrder(overlay, 1)

        See Also:
            GetDisplayOrder, SetVisible
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        if order < 0:
            raise FP_ParameterError("Display order cannot be negative")

        overlay = self._PossibilityItemOperations__ResolveObject(overlay_or_hvo)

        # Set display order
        if hasattr(overlay, "SortSpec"):
            overlay.SortSpec = int(order)

    # --- Element Operations ---

    @OperationsMethod
    def GetElements(self, overlay_or_hvo):
        """
        Get all elements in an overlay.

        Args:
            overlay_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            list: List of overlay elements.

        Raises:
            FP_NullParameterError: If overlay_or_hvo is None.

        Example:
            >>> overlay = project.Overlay.Find("Participants")
            >>> elements = project.Overlay.GetElements(overlay)
            >>> print(f"Overlay has {len(elements)} elements")
            Overlay has 5 elements

        See Also:
            AddElement, RemoveElement
        """
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        overlay = self._PossibilityItemOperations__ResolveObject(overlay_or_hvo)

        # Elements are typically in a sequence
        if hasattr(overlay, "InstancesOS"):
            return list(overlay.InstancesOS)
        elif hasattr(overlay, "Elements"):
            return list(overlay.Elements)
        return []

    @OperationsMethod
    def AddElement(self, overlay_or_hvo, element):
        """
        Add an element to an overlay.

        Args:
            overlay_or_hvo: Either an ICmPossibility object or its HVO.
            element: The element to add.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If overlay_or_hvo or element is None.

        Example:
            >>> overlay = project.Overlay.Find("Participants")
            >>> # element creation code here
            >>> project.Overlay.AddElement(overlay, element)

        See Also:
            RemoveElement, GetElements
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")
        self._ValidateParam(element, "element")

        overlay = self._PossibilityItemOperations__ResolveObject(overlay_or_hvo)

        # Add element to sequence
        if hasattr(overlay, "InstancesOS"):
            if element not in overlay.InstancesOS:
                overlay.InstancesOS.Add(element)
        elif hasattr(overlay, "Elements"):
            if element not in overlay.Elements:
                overlay.Elements.Add(element)

    @OperationsMethod
    def RemoveElement(self, overlay_or_hvo, element):
        """
        Remove an element from an overlay.

        Args:
            overlay_or_hvo: Either an ICmPossibility object or its HVO.
            element: The element to remove.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If overlay_or_hvo or element is None.

        Example:
            >>> overlay = project.Overlay.Find("Participants")
            >>> elements = project.Overlay.GetElements(overlay)
            >>> if elements:
            ...     project.Overlay.RemoveElement(overlay, elements[0])

        See Also:
            AddElement, GetElements
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")
        self._ValidateParam(element, "element")

        overlay = self._PossibilityItemOperations__ResolveObject(overlay_or_hvo)

        # Remove element from sequence
        if hasattr(overlay, "InstancesOS"):
            if element in overlay.InstancesOS:
                overlay.InstancesOS.Remove(element)
        elif hasattr(overlay, "Elements"):
            if element in overlay.Elements:
                overlay.Elements.Remove(element)

    # --- Chart Association Operations ---

    @OperationsMethod
    def GetChart(self, overlay_or_hvo):
        """
        Get the chart that owns this overlay.

        Args:
            overlay_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            IDsConstChart or None: The parent chart, or None if not found.

        Raises:
            FP_NullParameterError: If overlay_or_hvo is None.

        Example:
            >>> overlay = project.Overlay.Find("Participants")
            >>> chart = project.Overlay.GetChart(overlay)
            >>> if chart:
            ...     print(f"Overlay belongs to chart: {chart.Guid}")

        Notes:
            - Overlays are scoped to charts
            - Returns None if overlay is not in any chart
            - Used internally by FindByChart()

        See Also:
            FindByChart, GetVisibleOverlays
        """
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        overlay = self._PossibilityItemOperations__ResolveObject(overlay_or_hvo)

        # Direct-reference fast path: if a future LCM version exposes ChartRA
        # or Chart as a direct property, prefer it over walking ownership.
        if hasattr(overlay, "ChartRA"):
            return overlay.ChartRA
        elif hasattr(overlay, "Chart"):
            return overlay.Chart
        # Per issue #149: ICmOverlay is owned per-chart via
        # IDsConstChart.OverlaysOC (LcmOwningCollection<ICmOverlay>), not via a
        # project-wide DsDiscourseData list.  Walk the ownership chain to find
        # the enclosing IDsConstChart ancestor.
        chart_lcm = overlay.OwnerOfClass(DsConstChartTags.kClassId)
        if chart_lcm is None:
            return None
        return IDsConstChart(chart_lcm) if IDsConstChart is not None else chart_lcm

    @OperationsMethod
    def GetPossItems(self, overlay_or_hvo):
        """
        Get the possibility items associated with an overlay.

        Args:
            overlay_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            list: List of associated possibility items.

        Raises:
            FP_NullParameterError: If overlay_or_hvo is None.

        Example:
            >>> overlay = project.Overlay.Find("Participants")
            >>> items = project.Overlay.GetPossItems(overlay)
            >>> print(f"Overlay has {len(items)} associated items")

        See Also:
            GetElements, GetChart
        """
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        overlay = self._PossibilityItemOperations__ResolveObject(overlay_or_hvo)

        # Possibility items may be stored in SubPossibilitiesOS
        if hasattr(overlay, "SubPossibilitiesOS"):
            return list(overlay.SubPossibilitiesOS)
        return []

    # --- Search Operations ---

    @OperationsMethod
    def FindByChart(self, chart):
        """
        Find all overlays for a specific chart.

        Args:
            chart: The IDsConstChart to search.

        Returns:
            list: List of ICmPossibility objects representing overlays for the chart.

        Raises:
            FP_NullParameterError: If chart is None.

        Example:
            >>> # Get all overlays for a chart
            >>> charts = project.Discourse.GetAllCharts(text)
            >>> chart = list(charts)[0]
            >>> overlays = project.Overlay.FindByChart(chart)
            >>> print(f"Chart has {len(overlays)} overlays")
            Chart has 3 overlays

            >>> # Find overlays by name for a chart
            >>> overlays = project.Overlay.FindByChart(chart)
            >>> for overlay in overlays:
            ...     name = project.Overlay.GetName(overlay)
            ...     if name == "Participants":
            ...         print(f"Found participants overlay")

        Notes:
            - Returns empty list if chart has no overlays
            - Overlays are scoped to specific charts
            - More efficient than GetAll() for chart-specific queries

        See Also:
            GetVisibleOverlays, GetChart
        """
        self._ValidateParam(chart, "chart")

        # Query the chart's overlay list
        overlays = []
        if hasattr(chart, "OverlaysOC"):
            overlays = list(chart.OverlaysOC)
        elif hasattr(chart, "Overlays"):
            overlays = list(chart.Overlays)

        return overlays

    @OperationsMethod
    def GetVisibleOverlays(self, chart):
        """
        Get all visible overlays for a chart.

        Args:
            chart: The IDsConstChart to search.

        Returns:
            list: List of visible overlay ICmPossibility objects.

        Raises:
            FP_NullParameterError: If chart is None.

        Example:
            >>> # Get only visible overlays
            >>> overlays = project.Overlay.GetVisibleOverlays(chart)
            >>> print(f"Chart has {len(overlays)} visible overlays")
            Chart has 2 visible overlays

            >>> # Hide and show overlays
            >>> all_overlays = project.Overlay.FindByChart(chart)
            >>> for overlay in all_overlays:
            ...     project.Overlay.SetVisible(overlay, False)
            >>> # Now GetVisibleOverlays returns empty list
            >>> visible = project.Overlay.GetVisibleOverlays(chart)
            >>> assert len(visible) == 0

        Notes:
            - Returns subset of FindByChart() filtered by visibility
            - Used for determining which layers to render in chart display
            - Empty list if all overlays are hidden

        See Also:
            FindByChart, IsVisible, SetVisible
        """
        self._ValidateParam(chart, "chart")

        # Get all overlays and filter by visibility
        all_overlays = self.FindByChart(chart)
        visible_overlays = []

        for overlay in all_overlays:
            if self.IsVisible(overlay):
                visible_overlays.append(overlay)

        return visible_overlays
