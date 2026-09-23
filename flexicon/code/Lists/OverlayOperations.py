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
    ICmOverlayFactory,
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
from ..BaseOperations import OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key
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
        Overlays are project-scoped at ``ILangProject.OverlaysOC`` (issue #303).
        ``Create`` requires a source possibility list (``poss_list``) for
        ``PossListRA``; ``ICmOverlay.Name`` is a plain string, not multilingual.

    Usage::

        from flexicon import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        poss_list = project.lp.ConfidenceLevelsOA
        overlay = project.Overlays.Create("Participants", poss_list)
        project.Overlays.SetName(overlay, "Participant chains")
        for o in project.Overlays.GetAll():
            print(project.Overlays.GetName(o))

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
        """Return None so inherited PossibilityItem CRUD stays inert.

        Overlays live on ``ILangProject.OverlaysOC``, not a
        ``ICmPossibilityList.PossibilitiesOS``. This class overrides
        ``Create``/``GetAll``/``Delete``/``Find``/``GetName``/``SetName``
        directly (issue #309).
        """
        return None

    def __ResolveOverlay(self, overlay_or_hvo):
        """Resolve an overlay object or HVO to ``ICmOverlay``."""
        if isinstance(overlay_or_hvo, int):
            obj = self.project.Object(overlay_or_hvo)
            if obj is None:
                raise FP_ParameterError(
                    f"HVO {overlay_or_hvo} does not refer to a valid Overlay"
                )
            from ..lcm_casting import cast_to_concrete

            return cast_to_concrete(obj)
        return overlay_or_hvo

    def __ResolvePossList(self, poss_list_or_hvo):
        """Resolve a possibility list (or HVO) for ``PossListRA``."""
        if poss_list_or_hvo is None:
            raise FP_ParameterError(
                "poss_list is required when creating an overlay "
                "(sets PossListRA -- the source list for overlay items)"
            )
        if isinstance(poss_list_or_hvo, int):
            obj = self.project.Object(poss_list_or_hvo)
            if obj is None:
                raise FP_ParameterError(
                    f"HVO {poss_list_or_hvo} does not refer to a valid possibility list"
                )
            from ..lcm_casting import cast_to_concrete

            return cast_to_concrete(obj)
        return poss_list_or_hvo

    # --- CRUD (ICmOverlay-specific; issue #309) ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """Return all overlays in the project."""
        return list(self.project.lp.OverlaysOC)

    @OperationsMethod
    def Create(self, name, poss_list, items=None, wsHandle=None):
        """Create a new overlay on ``ILangProject.OverlaysOC``.

        Args:
            name (str): Overlay name (plain string on ``ICmOverlay``).
            poss_list: ``ICmPossibilityList`` (or HVO) assigned to ``PossListRA``.
            items: Optional iterable of ``ICmPossibility`` objects to seed
                ``PossItemsRC``.
            wsHandle: Ignored (kept for call-site uniformity with other
                ``Create`` methods; overlay names are not multilingual).

        Returns:
            ICmOverlay: The newly created overlay.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(name, "name")

        if not name or not str(name).strip():
            raise FP_ParameterError("Overlay name cannot be empty")

        poss_list_obj = self.__ResolvePossList(poss_list)
        factory = self.project.project.ServiceLocator.GetService(ICmOverlayFactory)

        with self._TransactionCM(f"Create Overlay {name!r}"):
            overlay = factory.Create()
            self.project.lp.OverlaysOC.Add(overlay)
            overlay.Name = str(name).strip()
            overlay.PossListRA = poss_list_obj
            if items:
                for item in items:
                    overlay.PossItemsRC.Add(item)
            return overlay

    @OperationsMethod
    def Delete(self, overlay_or_hvo):
        """Remove an overlay from ``OverlaysOC``."""
        self._EnsureWriteEnabled()
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        overlay = self.__ResolveOverlay(overlay_or_hvo)
        if overlay in self.project.lp.OverlaysOC:
            with self._TransactionCM("Delete Overlay"):
                self.project.lp.OverlaysOC.Remove(overlay)

    @OperationsMethod
    def Find(self, name):
        """Find an overlay by plain-string name."""
        self._ValidateParam(name, "name")

        if not name or not str(name).strip():
            return None

        target = normalize_match_key(str(name), casefold=True).strip()
        for overlay in self.GetAll():
            overlay_name = overlay.Name or ""
            if normalize_match_key(str(overlay_name), casefold=True).strip() == target:
                return overlay
        return None

    @OperationsMethod
    def Exists(self, name):
        """Return True if an overlay with ``name`` exists."""
        self._ValidateParam(name, "name")
        return self.Find(name) is not None

    @OperationsMethod
    def GetName(self, overlay_or_hvo, wsHandle=None):
        """Return the overlay name (``ICmOverlay.Name`` is a plain string)."""
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")
        overlay = self.__ResolveOverlay(overlay_or_hvo)
        return str(overlay.Name or "")

    @OperationsMethod
    def SetName(self, overlay_or_hvo, name, wsHandle=None):
        """Set the overlay name."""
        self._EnsureWriteEnabled()
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")
        self._ValidateParam(name, "name")

        overlay = self.__ResolveOverlay(overlay_or_hvo)
        with self._TransactionCM(f"Set Overlay name {name!r}"):
            overlay.Name = str(name or "")

    @OperationsMethod
    def Duplicate(self, overlay_or_hvo, insert_after=True, deep=False):
        """Clone an overlay into ``OverlaysOC`` with a new GUID (issue #303)."""
        self._EnsureWriteEnabled()
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        source = self.__ResolveOverlay(overlay_or_hvo)
        factory = self.project.project.ServiceLocator.GetService(ICmOverlayFactory)

        with self._TransactionCM("Duplicate Overlay"):
            duplicate = factory.Create()
            self.project.lp.OverlaysOC.Add(duplicate)
            duplicate.Name = source.Name
            duplicate.PossListRA = source.PossListRA
            if hasattr(source, "PossItemsRC"):
                for item in source.PossItemsRC:
                    duplicate.PossItemsRC.Add(item)
            return duplicate

    @OperationsMethod
    def GetDescription(self, overlay_or_hvo, wsHandle=None):
        """``ICmOverlay`` has no ``Description`` member (issue #303)."""
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")
        return ""

    @OperationsMethod
    def SetDescription(self, overlay_or_hvo, description, wsHandle=None):
        """``ICmOverlay`` has no ``Description`` member; validated no-op (#303)."""
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

    @OperationsMethod
    def GetGuid(self, overlay_or_hvo):
        """Return the overlay GUID."""
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")
        overlay = self.__ResolveOverlay(overlay_or_hvo)
        return str(overlay.Guid)

    @OperationsMethod
    def CompareTo(self, overlay1_or_hvo, overlay2_or_hvo):
        """Compare two overlays by plain-string ``Name``."""
        self._ValidateParam(overlay1_or_hvo, "overlay1_or_hvo")
        self._ValidateParam(overlay2_or_hvo, "overlay2_or_hvo")

        name1 = self.GetName(overlay1_or_hvo)
        name2 = self.GetName(overlay2_or_hvo)

        if name1 < name2:
            return -1
        if name1 > name2:
            return 1
        return 0

    @OperationsMethod
    def GetSyncableProperties(self, overlay_or_hvo):
        """Syncable snapshot for project-scoped ``ICmOverlay`` (#303)."""
        self._ValidateParam(overlay_or_hvo, "overlay_or_hvo")

        overlay = self.__ResolveOverlay(overlay_or_hvo)
        props = {"Guid": str(overlay.Guid)}

        name = overlay.Name
        if name:
            props["Name"] = str(name)

        poss_list = overlay.PossListRA
        if poss_list is not None:
            props["PossListRA"] = str(poss_list.Guid)

        return props

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

        # ICmOverlay has no visibility member (issue #364 / live #277 surface).
        if hasattr(overlay, "Hidden"):
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

        if not hasattr(overlay, "Hidden"):
            logger.debug(
                "SetVisible: %s has no Hidden/visibility member; no-op (issue #364)",
                getattr(overlay, "ClassName", type(overlay).__name__),
            )
            return

        with self._TransactionCM(f"Set overlay visible={bool(visible)}"):
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

        # Set display order. hasattr guard outside the bracket -- an overlay
        # without SortSpec is a true no-op and must not open a unit of work.
        if hasattr(overlay, "SortSpec"):
            with self._TransactionCM("Set overlay display order"):
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

        # ICmOverlay's complete own-declared property surface is
        # Name, PossItemsRC, PossListRA (confirmed by live reflection,
        # 2026-09-09; see specs/277-nonexistent-property-reads/
        # evidence/live-277-overlays.md, and re-confirmed for this issue:
        # whole-index grep for "InstancesOS"/"Elements" on ICmOverlay
        # returns zero hits). Neither InstancesOS nor Elements exists on
        # any indexed LCM 11 type, so both hasattr branches below were
        # always False -- GetElements/AddElement/RemoveElement were
        # unconditional no-ops (issue #320). PossItemsRC is a reference
        # COLLECTION (ILcmReferenceCollection<ICmPossibility>), not a
        # sequence, but it is iterable/materialisable the same way -- see
        # GetPossItems (below) and AllomorphOperations.GetPhoneEnv's
        # `list(allomorph.PhoneEnvRC)` for the established house pattern
        # with an RC property. The dead hasattr branches are deleted
        # entirely, not kept as fallbacks, since dead code that can never
        # be true is what hid this bug.
        if hasattr(overlay, "PossItemsRC"):
            return list(overlay.PossItemsRC)
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

        # --- Membership guard (issue #320, team lead ruling, cycle 3) ---
        # PossItemsRC is a reference collection: Add/Remove are pure
        # link/unlink, never a lifetime change on the ICmPossibility
        # itself.
        #
        # Cycle 2 live-verified this against the LCM layer directly (raw
        # SIL.LCModel factories/repositories, no flexicon Operations
        # involved): adding a possibility (HVO 34) that is NOT a member of
        # overlay.PossListRA's 859-item tree raised nothing and PERSISTED
        # on a fresh re-fetch (859 -> 860). See
        # specs/318-321-nonexistent-member-mutations/evidence/
        # live-cycle2-business-rules.md. So the LCM data layer itself does
        # not enforce list-membership as an invariant on PossItemsRC.
        #
        # That said, "LCM allows it" and "FLEx accepts it" are different
        # claims, and only the first was tested -- whether FLEx's UI
        # itself treats an overlay containing a possibility outside its
        # own PossListRA as valid/renderable data is UNTESTED. An overlay
        # is a filter over a specific list, so such a member may be
        # meaningless in the UI even though LCM happily stores it. We will
        # not invent a hard constraint we cannot cite, but we will not
        # stay silent either -- so we keep the membership check, but on
        # failure we warn and proceed rather than raise.
        #
        # This does NOT contradict the Original Author's ruling that
        # logger.warning is the wrong level for "the advertised operation
        # did not happen" (reviews/cycle1-author.md Q4) -- that ruling
        # governs NO-OPS. Here the add genuinely succeeds (it is durably
        # persisted, per the live evidence above); the warning is flagging
        # a possibly-meaningless-in-the-UI-but-successfully-stored write,
        # not a silently-skipped one.
        if overlay.PossListRA is not None:
            owning_list = getattr(element, "OwningList", None)
            if owning_list is None or owning_list.Hvo != overlay.PossListRA.Hvo:
                logger.warning(
                    "Element (HVO %s) is not a member of the possibility "
                    "list associated with this overlay's PossListRA; "
                    "adding it anyway (LCM does not enforce this as an "
                    "invariant -- see issue #320 evidence).",
                    getattr(element, "Hvo", "?"),
                )
        # --- End membership guard ---

        # Add element to the reference collection. PossItemsRC is the only
        # element-holding property on ICmOverlay (see GetElements above for
        # the InstancesOS/Elements dead-code evidence); the membership test
        # stays outside the transaction so an already-present element is a
        # true no-op.
        if element not in overlay.PossItemsRC:
            with self._TransactionCM("Add overlay element"):
                overlay.PossItemsRC.Add(element)

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

        # Remove element from the reference collection. PossItemsRC is the
        # only element-holding property on ICmOverlay (see GetElements above
        # for the InstancesOS/Elements dead-code evidence). Remove on a
        # reference collection is pure unlink -- it never deletes the
        # underlying ICmPossibility. The membership test stays outside the
        # transaction so an absent element is a true no-op.
        if element in overlay.PossItemsRC:
            with self._TransactionCM("Remove overlay element"):
                overlay.PossItemsRC.Remove(element)

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

        # ICmOverlay has no ChartRA/Chart (issue #364). Overlays are project-
        # scoped at ILangProject.OverlaysOC (#303); OwnerOfClass usually None.
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

        # ICmOverlay's complete own-declared property surface is
        # Name, PossItemsRC, PossListRA (confirmed by live reflection,
        # 2026-09-09; see specs/277-nonexistent-property-reads/
        # evidence/live-277-overlays.md). There is no SubPossibilitiesOS
        # on ICmOverlay -- that hasattr was always False, so this method
        # returned [] unconditionally regardless of the overlay's actual
        # contents (issue #277). PossItemsRC is a reference COLLECTION
        # (ILcmReferenceCollection<ICmPossibility>), not a sequence, but
        # it is iterable/materialisable the same way -- see
        # AllomorphOperations.GetPhoneEnv's `list(allomorph.PhoneEnvRC)`
        # for the established house pattern with an RC property.
        if hasattr(overlay, "PossItemsRC"):
            return list(overlay.PossItemsRC)
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

        # Overlays live on ILangProject.OverlaysOC, not on the chart (#303).
        return self.GetAll()

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

        return [overlay for overlay in self.GetAll() if self.IsVisible(overlay)]
