#
#   ConstChartMarkerOperations.py
#
#   Class: ConstChartMarkerOperations
#          Constituent-chart marker (CmPossibility) operations for
#          FieldWorks Language Explorer projects via SIL Language and
#          Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key

from SIL.LCModel import (
    ICmPossibility,
    ICmPossibilityFactory,
    ICmPossibilityList,
    ICmPossibilityListFactory,
    IDsDiscourseData,
    IDsDiscourseDataFactory,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

from ..FLExProject import (
    FP_ParameterError,
)


class ConstChartMarkerOperations(BaseOperations):
    """
    Operations for managing the project-wide constituent-chart marker
    vocabulary (``LangProject.DiscourseDataOA.ChartMarkersOA``).

    Markers are ``ICmPossibility`` items that categorise content in
    discourse charts (Topic, Focus, Tail, etc.). They live in a single
    project-wide CmPossibilityList shared across every chart in the
    project, and can be organised hierarchically -- a "Topic" marker
    may have "Sentence Topic" and "Contrastive Topic" children.

    Note: This is distinct from ``IConstChartTag``, which is the
    per-cell annotation that references a marker. See
    ``ConstChartCellTagOperations`` for that surface.

    Access via ``FLExProject.ConstChartMarkers``::

        for m in project.ConstChartMarkers.GetAll():
            print(project.ConstChartMarkers.GetName(m))

        topic = project.ConstChartMarkers.Create("Topic")
        project.ConstChartMarkers.SetDescription(
            topic, "Marks the sentence topic"
        )
    """

    def __init__(self, project):
        super().__init__(project)

    # --- Core CRUD Operations ------------------------------------------

    @OperationsMethod
    def Create(self, name):
        """
        Create a new top-level chart marker in the project-wide
        ChartMarkersOA possibility list.

        If ``DiscourseDataOA`` or ``DiscourseDataOA.ChartMarkersOA``
        is not yet initialised on the project, they are created on
        demand. This matches the FLEx UI behaviour where opening the
        discourse charting tool initialises both lazily.

        Args:
            name (str): The marker's name. Stored in the default
                analysis writing system.

        Returns:
            ICmPossibility: The newly created marker.

        Raises:
            FP_ReadOnlyError: If the project is not writeEnabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> topic = project.ConstChartMarkers.Create("Topic")
            >>> project.ConstChartMarkers.Find("Topic").Hvo == topic.Hvo
            True
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(name, "name")
        if not name or not name.strip():
            raise FP_ParameterError("Marker name cannot be empty")

        markers = self.__GetOrCreateChartMarkers()
        ws_handle = self.__WSHandle(None)

        with self._TransactionCM(f"Create chart marker '{name}'"):
            factory = self.project.project.ServiceLocator.GetService(
                ICmPossibilityFactory
            )
            new_marker = factory.Create()
            # Attach to the owning sequence BEFORE the property write so
            # the LCM property setter never runs against an orphan object.
            markers.Add(new_marker)
            new_marker.Name.set_String(
                ws_handle, TsStringUtils.MakeString(name, ws_handle)
            )
            return new_marker

    @OperationsMethod
    def Delete(self, marker_or_hvo):
        """
        Delete a chart marker.

        Args:
            marker_or_hvo: Either an ``ICmPossibility`` object or its HVO.

        Raises:
            FP_ReadOnlyError: If the project is not writeEnabled.
            FP_NullParameterError: If marker_or_hvo is None.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(marker_or_hvo, "marker_or_hvo")
        marker = self.__ResolveMarker(marker_or_hvo)
        marker.Delete()

    @OperationsMethod
    def Find(self, name, wsHandle=None):
        """
        Find a marker by name anywhere in the marker hierarchy.

        Walks both the top-level ``PossibilitiesOS`` and every
        nested ``SubPossibilitiesOS`` so hierarchical markers
        (e.g. "Topic > Contrastive Topic") are reachable.

        Args:
            name (str): The marker name to search for. Compared via
                NFD-normalised, case-insensitive match against each
                marker's Name in the chosen WS.
            wsHandle: Optional writing system handle. Defaults to the
                analysis WS.

        Returns:
            ICmPossibility or None: First match in depth-first order,
            or None when no marker has that name (or the marker list
            is not yet initialised).
        """
        self._ValidateParam(name, "name")
        if not name or not name.strip():
            return None
        ws_handle = self.__WSHandle(wsHandle)
        target = normalize_match_key(name, casefold=True)

        for marker in self.__WalkMarkers(self.__GetChartMarkers()):
            marker_name = ITsString(marker.Name.get_String(ws_handle)).Text
            if (
                marker_name
                and normalize_match_key(marker_name, casefold=True) == target
            ):
                return marker
        return None

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Iterate every marker in the project, hierarchy included.

        Returns markers in depth-first order: a top-level marker is
        yielded before its sub-markers, then its sub-markers'
        sub-markers, and so on.

        Returns:
            list[ICmPossibility]: All markers, or an empty list when
            the marker list is not yet initialised.
        """
        return list(self.__WalkMarkers(self.__GetChartMarkers()))

    # --- Marker Properties ---------------------------------------------

    @OperationsMethod
    def GetName(self, marker_or_hvo):
        """Return the marker's name in the default analysis WS (or "")."""
        self._ValidateParam(marker_or_hvo, "marker_or_hvo")
        marker = self.__ResolveMarker(marker_or_hvo)
        ws_handle = self.__WSHandle(None)
        return ITsString(marker.Name.get_String(ws_handle)).Text or ""

    @OperationsMethod
    def SetName(self, marker_or_hvo, name):
        """Set the marker's name in the default analysis WS."""
        self._EnsureWriteEnabled()
        self._ValidateParam(marker_or_hvo, "marker_or_hvo")
        self._ValidateParam(name, "name")
        if not name or not name.strip():
            raise FP_ParameterError("Marker name cannot be empty")

        marker = self.__ResolveMarker(marker_or_hvo)
        ws_handle = self.__WSHandle(None)
        marker.Name.set_String(
            ws_handle, TsStringUtils.MakeString(name, ws_handle)
        )

    @OperationsMethod
    def GetDescription(self, marker_or_hvo, wsHandle=None):
        """Return the marker's description (or "" if not set)."""
        self._ValidateParam(marker_or_hvo, "marker_or_hvo")
        marker = self.__ResolveMarker(marker_or_hvo)
        ws_handle = self.__WSHandle(wsHandle)
        return ITsString(marker.Description.get_String(ws_handle)).Text or ""

    @OperationsMethod
    def SetDescription(self, marker_or_hvo, text, wsHandle=None):
        """Set the marker's description (default WS: analysis)."""
        self._EnsureWriteEnabled()
        self._ValidateParam(marker_or_hvo, "marker_or_hvo")
        self._ValidateParam(text, "text")
        marker = self.__ResolveMarker(marker_or_hvo)
        ws_handle = self.__WSHandle(wsHandle)
        marker.Description.set_String(
            ws_handle, TsStringUtils.MakeString(text, ws_handle)
        )

    # --- Reordering Support --------------------------------------------

    def _GetSequence(self, parent):
        """
        Reorder operations are intentionally disabled on this class.

        BaseOperations' MoveUp / MoveDown / Reorder rely on
        ``_GetSequence(parent)`` to know which collection to reorder.
        Returning the project-wide ``ChartMarkersOA.PossibilitiesOS``
        would let a caller silently re-order a list every other user
        of the project shares. Raise instead so the caller has to
        manipulate the LCM list directly when project-wide reordering
        is genuinely intended.
        """
        raise NotImplementedError(
            "ConstChartMarkerOperations does not support inherited "
            "MoveUp / MoveDown / Reorder: the ChartMarkers list is "
            "project-wide, and reordering it from a single workflow "
            "would mutate state every chart in the project shares. "
            "If project-wide reordering is intended, manipulate "
            "project.lp.DiscourseDataOA.ChartMarkersOA.PossibilitiesOS "
            "directly."
        )

    # --- Private Helpers -----------------------------------------------

    def __ResolveMarker(self, marker_or_hvo):
        if isinstance(marker_or_hvo, int):
            obj = self.project.Object(marker_or_hvo)
            if not isinstance(obj, ICmPossibility):
                raise FP_ParameterError(
                    "HVO does not refer to a CmPossibility marker"
                )
            return obj
        return marker_or_hvo

    def __WSHandle(self, ws):
        if ws is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(
            ws, self.project.project.DefaultAnalWs
        )

    def __GetChartMarkers(self):
        """Read-only access; returns the top-level sequence or None."""
        discourse = self.project.lp.DiscourseDataOA
        if discourse is None:
            return None
        markers_list = discourse.ChartMarkersOA
        if markers_list is None:
            return None
        return markers_list.PossibilitiesOS

    def __GetOrCreateChartMarkers(self):
        """
        Resolve the top-level marker sequence, creating
        DiscourseDataOA and/or ChartMarkersOA on demand.

        Both atomic-owning slots are initialised lazily by FLEx --
        ``DiscourseDataOA`` when the user first opens the discourse
        charting UI, ``ChartMarkersOA`` when the user adds the first
        marker. Wrapper callers shouldn't have to know that ordering;
        Create handles it here.
        """
        sl = self.project.project.ServiceLocator
        lp = self.project.lp

        if lp.DiscourseDataOA is None:
            dd_factory = sl.GetService(IDsDiscourseDataFactory)
            lp.DiscourseDataOA = dd_factory.Create()
        discourse = lp.DiscourseDataOA

        if discourse.ChartMarkersOA is None:
            list_factory = sl.GetService(ICmPossibilityListFactory)
            discourse.ChartMarkersOA = list_factory.Create()

        return discourse.ChartMarkersOA.PossibilitiesOS

    @staticmethod
    def __WalkMarkers(top_sequence):
        """Depth-first walk over a possibility hierarchy, or empty."""
        if top_sequence is None:
            return
        stack = list(top_sequence)
        while stack:
            marker = stack.pop(0)
            yield marker
            subs = getattr(marker, "SubPossibilitiesOS", None)
            if subs is not None and subs.Count > 0:
                stack[0:0] = list(subs)
