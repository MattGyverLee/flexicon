#
#   ConstChartRowOperations.py
#
#   Class: ConstChartRowOperations
#          Constituent chart row operations for discourse analysis in FieldWorks
#          Language Explorer projects via SIL Language and Culture Model (LCM) API.
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
    IConstChartRow,
    IConstChartRowFactory,
    IDsConstChart,
    IConstChartWordGroup,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ConstChartRowOperations(BaseOperations):
    """
    This class provides operations for managing constituent chart rows in a
    FieldWorks project for discourse analysis.

    Chart rows represent segments or units of analyzed text within a constituent
    chart. Each row can contain word groups, labels, and notes describing the
    discourse structure.

    This class should be accessed via FLExProject.ConstChartRows property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a chart
        chart = project.ConstCharts.Find("Genesis 1 Analysis")

        # Create a new row
        row = project.ConstChartRows.Create(chart, label="Verse 1")

        # Get all rows in a chart
        for row in project.ConstChartRows.GetAll(chart):
            label = project.ConstChartRows.GetLabel(row)
            print(f"Row: {label}")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ConstChartRowOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, chart_or_hvo, label="", notes=""):
        """
        Create a new row in a constituent chart.

        Args:
            chart_or_hvo: Either an IDsConstChart object or its HVO
            label (str, optional): Label for the row (e.g., "Verse 1", "Line 3")
            notes (str, optional): Notes describing the row

        Returns:
            IConstChartRow: The newly created row object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If chart_or_hvo is None

        Example:
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> row = project.ConstChartRows.Create(chart, label="Verse 1")
            >>> print(project.ConstChartRows.GetLabel(row))
            Verse 1

            >>> # Create with label and notes
            >>> row = project.ConstChartRows.Create(chart,
            ...     label="Verse 2",
            ...     notes="Complex sentence structure")

        Notes:
            - Row is appended to the end of the chart's row list
            - Label and notes are optional
            - Label and notes use default analysis writing system
            - Factory.Create() automatically adds row to repository
            - Row starts with no word groups - add using ConstChartWordGroups

        See Also:
            Delete, Find, GetAll, SetLabel, SetNotes
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        chart = self.__ResolveChart(chart_or_hvo)
        wsHandle = self.__WSHandleAnalysis()

        with self._TransactionCM("Create chart row"):
            # Create the new row using the factory
            factory = self.project.project.ServiceLocator.GetService(IConstChartRowFactory)
            new_row = factory.Create()

            # Add to chart's rows collection
            chart.RowsOS.Add(new_row)

            # Set label if provided
            if label:
                mkstr = TsStringUtils.MakeString(label, wsHandle)
                new_row.Label.set_String(wsHandle, mkstr)

            # Set notes if provided
            if notes:
                mkstr = TsStringUtils.MakeString(notes, wsHandle)
                new_row.Notes.set_String(wsHandle, mkstr)

            return new_row

    @OperationsMethod
    def Delete(self, row_or_hvo):
        """
        Delete a row from its constituent chart.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO (database ID)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If row_or_hvo is None

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> if row:
            ...     project.ConstChartRows.Delete(row)

            >>> # Delete by HVO
            >>> project.ConstChartRows.Delete(12345)

        Warning:
            - This is a destructive operation
            - All word groups and markers in the row will be deleted
            - Cannot be undone
            - Row will be removed from the chart

        Notes:
            - Deletion cascades to all owned objects (word groups, markers, etc.)
            - Remaining rows maintain their order

        See Also:
            Create, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(row_or_hvo, "row_or_hvo")

        # Resolve to row object
        row = self.__ResolveObject(row_or_hvo)

        # Delete the row (LCM handles removal from repository)
        row.Delete()

    @OperationsMethod
    def Find(self, chart_or_hvo, index):
        """
        Find a row in a chart by its index position.

        Args:
            chart_or_hvo: Either an IDsConstChart object or its HVO
            index (int): Zero-based index of the row to find

        Returns:
            IConstChartRow or None: The row object if found, None otherwise

        Raises:
            FP_NullParameterError: If chart_or_hvo is None

        Example:
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> row = project.ConstChartRows.Find(chart, 0)  # First row
            >>> if row:
            ...     label = project.ConstChartRows.GetLabel(row)
            ...     print(f"First row: {label}")

        Notes:
            - Index is zero-based (0 = first row)
            - Returns None if index out of range (doesn't raise exception)
            - More efficient than iterating GetAll()

        See Also:
            GetAll, Create
        """
        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        chart = self.__ResolveChart(chart_or_hvo)

        if index < 0 or index >= chart.RowsOS.Count:
            return None

        return chart.RowsOS[index]

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, chart_or_hvo):
        """
        Get all rows in a constituent chart.

        Args:
            chart_or_hvo: Either an IDsConstChart object or its HVO

        Returns:
            list: List of IConstChartRow objects (empty list if none)

        Raises:
            FP_NullParameterError: If chart_or_hvo is None

        Example:
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> rows = project.ConstChartRows.GetAll(chart)
            >>> for i, row in enumerate(rows):
            ...     label = project.ConstChartRows.GetLabel(row)
            ...     print(f"Row {i}: {label}")
            Row 0: Verse 1
            Row 1: Verse 2
            Row 2: Verse 3

        Notes:
            - Returns empty list if chart has no rows
            - Rows are in chart order
            - Each row can contain word groups for analysis
            - Equivalent to chart.RowsOS but returns Python list

        See Also:
            Find, Create
        """
        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        chart = self.__ResolveChart(chart_or_hvo)

        return list(chart.RowsOS)

    # --- Row Properties ---

    @OperationsMethod
    def GetLabel(self, row_or_hvo, ws=None):
        """
        Get the label of a chart row.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO
            ws: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The row label (empty string if not set)

        Raises:
            FP_NullParameterError: If row_or_hvo is None

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> label = project.ConstChartRows.GetLabel(row)
            >>> print(label)
            Verse 1

        Notes:
            - Returns empty string if label not set
            - Uses default analysis writing system unless specified

        See Also:
            SetLabel, GetNotes
        """
        self._ValidateParam(row_or_hvo, "row_or_hvo")

        row = self.__ResolveObject(row_or_hvo)
        wsHandle = self.__WSHandle(ws)

        return ITsString(row.Label.get_String(wsHandle)).Text or ""

    @OperationsMethod
    def SetLabel(self, row_or_hvo, text, ws=None):
        """
        Set the label of a chart row.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO
            text (str): The new label text
            ws: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If row_or_hvo or text is None

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> project.ConstChartRows.SetLabel(row, "Verse 1a")
            >>> print(project.ConstChartRows.GetLabel(row))
            Verse 1a

        Notes:
            - Label can be empty to clear
            - Uses default analysis writing system unless specified
            - Changes are immediately persisted

        See Also:
            GetLabel, SetNotes
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(row_or_hvo, "row_or_hvo")
        self._ValidateParam(text, "text")

        row = self.__ResolveObject(row_or_hvo)
        wsHandle = self.__WSHandle(ws)

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        row.Label.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetNotes(self, row_or_hvo, ws=None):
        """
        Get the notes of a chart row.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO
            ws: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The row notes (empty string if not set)

        Raises:
            FP_NullParameterError: If row_or_hvo is None

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> notes = project.ConstChartRows.GetNotes(row)
            >>> print(notes)
            Complex sentence with embedded clause

        Notes:
            - Returns empty string if notes not set
            - Uses default analysis writing system unless specified
            - Notes can contain detailed analysis information

        See Also:
            SetNotes, GetLabel
        """
        self._ValidateParam(row_or_hvo, "row_or_hvo")

        row = self.__ResolveObject(row_or_hvo)
        wsHandle = self.__WSHandle(ws)

        return ITsString(row.Notes.get_String(wsHandle)).Text or ""

    @OperationsMethod
    def SetNotes(self, row_or_hvo, text, ws=None):
        """
        Set the notes of a chart row.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO
            text (str): The new notes text
            ws: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If row_or_hvo or text is None

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> project.ConstChartRows.SetNotes(row,
            ...     "Subject-predicate structure with modifier")

        Notes:
            - Notes can be empty to clear
            - Uses default analysis writing system unless specified
            - Notes are for analyst commentary and observations

        See Also:
            GetNotes, SetLabel
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(row_or_hvo, "row_or_hvo")
        self._ValidateParam(text, "text")

        row = self.__ResolveObject(row_or_hvo)
        wsHandle = self.__WSHandle(ws)

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        row.Notes.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetWordGroups(self, row_or_hvo):
        """
        Get all word groups in a chart row.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO

        Returns:
            list: List of IConstChartWordGroup objects (empty list if none)

        Raises:
            FP_NullParameterError: If row_or_hvo is None

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> word_groups = project.ConstChartRows.GetWordGroups(row)
            >>> for wg in word_groups:
            ...     # Process word group
            ...     pass

        Notes:
            - Returns empty list if row has no word groups
            - Word groups are in database order
            - Word groups represent segments of text being analyzed
            - Use ConstChartWordGroups operations to manipulate word groups

        See Also:
            ConstChartWordGroupOperations, Create
        """
        self._ValidateParam(row_or_hvo, "row_or_hvo")

        row = self.__ResolveObject(row_or_hvo)

        return list(row.CellsOS)

    @OperationsMethod
    def MoveTo(self, row_or_hvo, chart_or_hvo, index):
        """
        Move a row to a specific position in a chart.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO
            chart_or_hvo: Target chart (can be same or different chart)
            index (int): Target index position (zero-based)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If row_or_hvo or chart_or_hvo is None
            FP_ParameterError: If index is out of range

        Example:
            >>> # Move row to beginning of same chart
            >>> row = project.ConstChartRows.Find(chart, 5)
            >>> project.ConstChartRows.MoveTo(row, chart, 0)

            >>> # Move row to different chart
            >>> other_chart = project.ConstCharts.Find("Other Analysis")
            >>> project.ConstChartRows.MoveTo(row, other_chart, 0)

        Notes:
            - Can move to same or different chart
            - Index must be valid for target chart
            - Other rows shift to accommodate
            - All word groups move with the row

        Warning:
            - Moving between charts may break discourse structure
            - Ensure the move is linguistically appropriate

        See Also:
            MoveUp, MoveDown, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(row_or_hvo, "row_or_hvo")
        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        row = self.__ResolveObject(row_or_hvo)
        target_chart = self.__ResolveChart(chart_or_hvo)

        # Validate index
        if index < 0 or index > target_chart.RowsOS.Count:
            raise FP_ParameterError(f"Index {index} out of range [0, {target_chart.RowsOS.Count}]")

        # Get source chart. row.Owner is typed as ICmObject and does
        # not expose RowsOS; cast to IDsConstChart so the typed
        # collection is reachable for both the same-chart reorder path
        # and the cross-chart Remove/Insert path.
        source_chart = self._GetTypedOwner(row)
        if source_chart is None:
            raise FP_ParameterError("Row has no owning chart")

        with self._TransactionCM(f"Move row to index {index}"):
            # If moving within same chart, use reordering
            if source_chart == target_chart:
                current_index = -1
                for i in range(source_chart.RowsOS.Count):
                    if source_chart.RowsOS[i] == row:
                        current_index = i
                        break

                if current_index != -1 and current_index != index:
                    if current_index < index:
                        # Moving forward - use index + 1
                        source_chart.RowsOS.MoveTo(current_index, current_index, source_chart.RowsOS, index + 1)
                    else:
                        # Moving backward - use index directly
                        source_chart.RowsOS.MoveTo(current_index, current_index, source_chart.RowsOS, index)
            else:
                # Moving to different chart - remove from source and add to target
                source_chart.RowsOS.Remove(row)
                target_chart.RowsOS.Insert(index, row)

    # --- Private Helper Methods ---

    def __ResolveObject(self, row_or_hvo):
        """
        Resolve HVO or object to IConstChartRow.

        Args:
            row_or_hvo: Either an IConstChartRow object or an HVO (int)

        Returns:
            IConstChartRow: The resolved row object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a chart row
        """
        if isinstance(row_or_hvo, int):
            obj = self.project.Object(row_or_hvo)
            if not isinstance(obj, IConstChartRow):
                raise FP_ParameterError("HVO does not refer to a chart row")
            return obj
        return row_or_hvo

    def __ResolveChart(self, chart_or_hvo):
        """
        Resolve HVO or object to IDsConstChart.

        Args:
            chart_or_hvo: Either an IDsConstChart object or an HVO (int)

        Returns:
            IDsConstChart: The resolved chart object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a constituent chart
        """
        if isinstance(chart_or_hvo, int):
            obj = self.project.Object(chart_or_hvo)
            if not isinstance(obj, IDsConstChart):
                raise FP_ParameterError("HVO does not refer to a constituent chart")
            return obj
        return chart_or_hvo

    def __WSHandle(self, ws):
        """
        Get writing system handle, defaulting to analysis WS.

        Args:
            ws: Optional writing system handle

        Returns:
            int: The writing system handle
        """
        if ws is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(ws, self.project.project.DefaultAnalWs)

    def __WSHandleAnalysis(self):
        """
        Get writing system handle for analysis writing system.

        Returns:
            int: The analysis writing system handle
        """
        return self.project.project.DefaultAnalWs

    # --- Reordering Support ---

    def _GetSequence(self, parent):
        """
        Get the owning sequence for word groups in a row.

        Args:
            parent: The parent IConstChartRow object

        Returns:
            ILcmOwningSequence: The CellsOS sequence

        Notes:
            - Required for BaseOperations reordering methods
            - Returns the CellsOS collection from the row
        """
        return parent.CellsOS
