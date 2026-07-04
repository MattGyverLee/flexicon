#
#   ConstChartCellTagOperations.py
#
#   Class: ConstChartCellTagOperations
#          Per-cell tag (IConstChartTag) operations for constituent
#          charts in FieldWorks Language Explorer projects via SIL
#          Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

from SIL.LCModel import (
    IConstChartTag,
    IConstChartTagFactory,
    IConstChartRow,
    ICmPossibility,
)

from ..FLExProject import (
    FP_ParameterError,
)


class ConstChartCellTagOperations(BaseOperations):
    """
    Operations for managing per-cell chart tags (``IConstChartTag``)
    -- the annotation surface in a constituent chart.

    Each chart row owns a sequence of cell-parts; a ``IConstChartTag``
    is one cell-part subtype. Each tag is positioned in a column
    (``ColumnRA``) and references a marker from the project-wide
    vocabulary (``TagRA``). The vocabulary itself is managed by
    ``ConstChartMarkerOperations``.

    Typical workflow::

        row    = list(chart.RowsOS)[0]
        col    = list(template.ColumnsOS)[1]
        topic  = project.ConstChartMarkers.Find("Topic")

        tag = project.ConstChartCellTags.Create(row, col, topic)
        assert project.ConstChartCellTags.GetMarker(tag) is topic

    Access via ``FLExProject.ConstChartCellTags``.
    """

    def __init__(self, project):
        super().__init__(project)

    # --- Core CRUD Operations ------------------------------------------

    @OperationsMethod
    def Create(self, row_or_hvo, column, marker, index=None):
        """
        Add a new IConstChartTag cell-part to ``row.CellsOS``.

        Args:
            row_or_hvo: The ``IConstChartRow`` (or HVO) that will own
                the new cell-part.
            column: The ``ICmPossibility`` representing the column
                this tag occupies. Stored as ``ColumnRA``.
            marker: The ``ICmPossibility`` from the project's
                ChartMarkers vocabulary. Stored as ``TagRA``.
            index (int, optional): Position to insert at within
                ``row.CellsOS``. When None (default) the tag is
                appended at the end.

        Returns:
            IConstChartTag: The newly created cell-part.

        Raises:
            FP_ReadOnlyError: If the project is not writeEnabled.
            FP_NullParameterError: If any of row_or_hvo / column /
                marker is None.
            FP_ParameterError: If index is out of range.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(row_or_hvo, "row_or_hvo")
        self._ValidateParam(column, "column")
        self._ValidateParam(marker, "marker")

        row = self.__ResolveRow(row_or_hvo)
        cell_count = row.CellsOS.Count
        if index is None:
            index = cell_count
        if index < 0 or index > cell_count:
            raise FP_ParameterError(
                f"index {index} out of range for CellsOS of size {cell_count}"
            )

        factory = self.project.project.ServiceLocator.GetService(
            IConstChartTagFactory
        )
        return factory.Create(row, index, column, marker)

    @OperationsMethod
    def Delete(self, tag_or_hvo):
        """
        Delete a cell-tag from its owning row.

        Args:
            tag_or_hvo: ``IConstChartTag`` or its HVO.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(tag_or_hvo, "tag_or_hvo")
        tag = self.__ResolveTag(tag_or_hvo)
        tag.Delete()

    @OperationsMethod
    def Find(self, row_or_hvo, column):
        """
        Find the first cell-tag in ``row`` positioned in ``column``.

        Args:
            row_or_hvo: ``IConstChartRow`` or HVO.
            column: ``ICmPossibility`` representing the column.

        Returns:
            IConstChartTag or None: First matching tag, or None when
            the row has no tag in that column.
        """
        self._ValidateParam(row_or_hvo, "row_or_hvo")
        self._ValidateParam(column, "column")
        row = self.__ResolveRow(row_or_hvo)
        column_hvo = column.Hvo
        for cell in row.CellsOS:
            if not isinstance(cell, IConstChartTag):
                continue
            if cell.ColumnRA is not None and cell.ColumnRA.Hvo == column_hvo:
                return cell
        return None

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, row_or_hvo):
        """
        Iterate every IConstChartTag in ``row.CellsOS`` (other
        cell-part subtypes are filtered out).

        Args:
            row_or_hvo: ``IConstChartRow`` or HVO.

        Returns:
            list[IConstChartTag]: Tags in CellsOS order.
        """
        self._ValidateParam(row_or_hvo, "row_or_hvo")
        row = self.__ResolveRow(row_or_hvo)
        return [c for c in row.CellsOS if isinstance(c, IConstChartTag)]

    # --- Tag Properties ------------------------------------------------

    @OperationsMethod
    def GetMarker(self, tag_or_hvo):
        """Return ``tag.TagRA`` -- the referenced marker (or None)."""
        self._ValidateParam(tag_or_hvo, "tag_or_hvo")
        tag = self.__ResolveTag(tag_or_hvo)
        return tag.TagRA

    @OperationsMethod
    def SetMarker(self, tag_or_hvo, marker):
        """Set ``tag.TagRA`` to a marker from the project vocabulary."""
        self._EnsureWriteEnabled()
        self._ValidateParam(tag_or_hvo, "tag_or_hvo")
        self._ValidateParam(marker, "marker")
        tag = self.__ResolveTag(tag_or_hvo)
        tag.TagRA = marker

    @OperationsMethod
    def GetColumn(self, tag_or_hvo):
        """Return ``tag.ColumnRA`` -- the column the tag occupies."""
        self._ValidateParam(tag_or_hvo, "tag_or_hvo")
        tag = self.__ResolveTag(tag_or_hvo)
        return tag.ColumnRA

    # --- Private Helpers -----------------------------------------------

    def __ResolveRow(self, row_or_hvo):
        if isinstance(row_or_hvo, int):
            obj = self.project.Object(row_or_hvo)
            if not isinstance(obj, IConstChartRow):
                raise FP_ParameterError(
                    "HVO does not refer to an IConstChartRow"
                )
            return obj
        return row_or_hvo

    def __ResolveTag(self, tag_or_hvo):
        if isinstance(tag_or_hvo, int):
            obj = self.project.Object(tag_or_hvo)
            if not isinstance(obj, IConstChartTag):
                raise FP_ParameterError(
                    "HVO does not refer to an IConstChartTag"
                )
            return obj
        return tag_or_hvo
