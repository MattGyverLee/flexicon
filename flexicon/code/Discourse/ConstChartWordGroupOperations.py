#
#   ConstChartWordGroupOperations.py
#
#   Class: ConstChartWordGroupOperations
#          Constituent chart word group operations for discourse analysis in FieldWorks
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
    IConstChartWordGroup,
    IConstChartWordGroupFactory,
    IConstChartRow,
    IAnalysis,
    ISegment,
)

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ConstChartWordGroupOperations(BaseOperations):
    """
    This class provides operations for managing word groups in constituent chart rows
    for discourse analysis in FieldWorks projects.

    Word groups represent segments of text being analyzed in a discourse chart. Each
    word group references a range of segments (words/morphemes) from the analyzed text.

    This class should be accessed via FLExProject.ConstChartWordGroups property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a row
        chart = project.ConstCharts.Find("Genesis 1 Analysis")
        row = project.ConstChartRows.Find(chart, 0)

        # Create a word group (referencing text segments)
        wg = project.ConstChartWordGroups.Create(row, begin_segment, end_segment)

        # Get all word groups in a row
        for wg in project.ConstChartWordGroups.GetAll(row):
            # Process word group
            pass

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ConstChartWordGroupOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, row_or_hvo, begin_segment, end_segment):
        """
        Create a new word group in a chart row.

        Word groups represent a range of text segments being analyzed. The
        begin and end segments define the span of text this word group covers.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO
            begin_segment: ISegment object marking the start of the range
            end_segment: ISegment object marking the end of the range (inclusive)

        Returns:
            IConstChartWordGroup: The newly created word group object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If any parameter is None
            FP_ParameterError: If segments are invalid

        Example:
            >>> # Get segments from a text
            >>> text = project.Texts.Find("Genesis 1")
            >>> para = text.ContentsOA.ParagraphsOS[0]
            >>> segments = list(para.SegmentsOS)
            >>>
            >>> # Create word group spanning first 3 words
            >>> wg = project.ConstChartWordGroups.Create(
            ...     row,
            ...     segments[0],  # Begin
            ...     segments[2]   # End
            ... )

        Notes:
            - Word group is appended to the row's cells collection
            - Segments must be from the analyzed text
            - Begin segment must come before or equal to end segment
            - Factory.Create() automatically adds word group to repository
            - Word groups can have moved text markers and clause markers

        See Also:
            Delete, Find, GetBeginSegment, GetEndSegment
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(row_or_hvo, "row_or_hvo")
        self._ValidateParam(begin_segment, "begin_segment")
        self._ValidateParam(end_segment, "end_segment")

        row = self.__ResolveRow(row_or_hvo)

        # Validate segments
        if not isinstance(begin_segment, ISegment):
            raise FP_ParameterError("begin_segment must be an ISegment object")
        if not isinstance(end_segment, ISegment):
            raise FP_ParameterError("end_segment must be an ISegment object")

        with self._TransactionCM("Create word group"):
            # Create the new word group using the factory
            factory = self.project.project.ServiceLocator.GetService(IConstChartWordGroupFactory)
            new_word_group = factory.Create()

            # Add to row's cells collection
            row.CellsOS.Add(new_word_group)

            # Set the segment references
            new_word_group.BeginSegmentRA = begin_segment
            new_word_group.EndSegmentRA = end_segment

            return new_word_group

    @OperationsMethod
    def Delete(self, group_or_hvo):
        """
        Delete a word group from its chart row.

        Args:
            group_or_hvo: Either an IConstChartWordGroup object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If group_or_hvo is None

        Example:
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> if wg:
            ...     project.ConstChartWordGroups.Delete(wg)

        Warning:
            - This is a destructive operation
            - All moved text markers and clause markers will be deleted
            - Cannot be undone

        Notes:
            - Deletion cascades to all owned objects
            - Remaining word groups maintain their order

        See Also:
            Create, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(group_or_hvo, "group_or_hvo")

        # Resolve to word group object
        group = self.__ResolveObject(group_or_hvo)

        # Delete the word group (LCM handles removal from repository)
        group.Delete()

    @OperationsMethod
    def Find(self, row_or_hvo, index):
        """
        Find a word group in a row by its index position.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO
            index (int): Zero-based index of the word group to find

        Returns:
            IConstChartWordGroup or None: The word group object if found, None otherwise

        Raises:
            FP_NullParameterError: If row_or_hvo is None

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> wg = project.ConstChartWordGroups.Find(row, 0)  # First word group
            >>> if wg:
            ...     begin = project.ConstChartWordGroups.GetBeginSegment(wg)
            ...     print(f"Word group starts at segment {begin.Hvo}")

        Notes:
            - Index is zero-based (0 = first word group)
            - Returns None if index out of range
            - More efficient than iterating GetAll()

        See Also:
            GetAll, Create
        """
        self._ValidateParam(row_or_hvo, "row_or_hvo")

        row = self.__ResolveRow(row_or_hvo)

        if index < 0 or index >= row.CellsOS.Count:
            return None

        return row.CellsOS[index]

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, row_or_hvo):
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
            >>> word_groups = project.ConstChartWordGroups.GetAll(row)
            >>> for i, wg in enumerate(word_groups):
            ...     print(f"Word group {i}")

        Notes:
            - Returns empty list if row has no word groups
            - Word groups are in row order
            - Each word group references a text segment range

        See Also:
            Find, Create
        """
        self._ValidateParam(row_or_hvo, "row_or_hvo")

        row = self.__ResolveRow(row_or_hvo)

        return list(row.CellsOS)

    # --- Word Group Properties ---

    @OperationsMethod
    def GetBeginSegment(self, group_or_hvo):
        """
        Get the beginning segment of a word group.

        Args:
            group_or_hvo: Either an IConstChartWordGroup object or its HVO

        Returns:
            ISegment or None: The beginning segment, or None if not set

        Raises:
            FP_NullParameterError: If group_or_hvo is None

        Example:
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> begin_seg = project.ConstChartWordGroups.GetBeginSegment(wg)
            >>> if begin_seg:
            ...     print(f"Starts at segment {begin_seg.Hvo}")

        Notes:
            - Returns None if segment reference not set
            - Segment is from the analyzed text
            - Begin segment must be before or equal to end segment

        See Also:
            SetBeginSegment, GetEndSegment
        """
        self._ValidateParam(group_or_hvo, "group_or_hvo")

        group = self.__ResolveObject(group_or_hvo)

        return group.BeginSegmentRA if hasattr(group, "BeginSegmentRA") else None

    @OperationsMethod
    def SetBeginSegment(self, group_or_hvo, segment):
        """
        Set the beginning segment of a word group.

        Args:
            group_or_hvo: Either an IConstChartWordGroup object or its HVO
            segment: ISegment object to set as beginning (can be None to clear)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If group_or_hvo is None
            FP_ParameterError: If segment is invalid type

        Example:
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> new_segment = segments[5]
            >>> project.ConstChartWordGroups.SetBeginSegment(wg, new_segment)

        Notes:
            - Segment can be None to clear reference
            - Segment must be from the analyzed text
            - Should be before or equal to end segment

        See Also:
            GetBeginSegment, SetEndSegment
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(group_or_hvo, "group_or_hvo")

        if segment is not None and not isinstance(segment, ISegment):
            raise FP_ParameterError("segment must be an ISegment object or None")

        group = self.__ResolveObject(group_or_hvo)

        group.BeginSegmentRA = segment

    @OperationsMethod
    def GetEndSegment(self, group_or_hvo):
        """
        Get the ending segment of a word group.

        Args:
            group_or_hvo: Either an IConstChartWordGroup object or its HVO

        Returns:
            ISegment or None: The ending segment, or None if not set

        Raises:
            FP_NullParameterError: If group_or_hvo is None

        Example:
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> end_seg = project.ConstChartWordGroups.GetEndSegment(wg)
            >>> if end_seg:
            ...     print(f"Ends at segment {end_seg.Hvo}")

        Notes:
            - Returns None if segment reference not set
            - Segment is from the analyzed text
            - End segment must be after or equal to begin segment

        See Also:
            SetEndSegment, GetBeginSegment
        """
        self._ValidateParam(group_or_hvo, "group_or_hvo")

        group = self.__ResolveObject(group_or_hvo)

        return group.EndSegmentRA if hasattr(group, "EndSegmentRA") else None

    @OperationsMethod
    def SetEndSegment(self, group_or_hvo, segment):
        """
        Set the ending segment of a word group.

        Args:
            group_or_hvo: Either an IConstChartWordGroup object or its HVO
            segment: ISegment object to set as ending (can be None to clear)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If group_or_hvo is None
            FP_ParameterError: If segment is invalid type

        Example:
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> new_segment = segments[10]
            >>> project.ConstChartWordGroups.SetEndSegment(wg, new_segment)

        Notes:
            - Segment can be None to clear reference
            - Segment must be from the analyzed text
            - Should be after or equal to begin segment

        See Also:
            GetEndSegment, SetBeginSegment
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(group_or_hvo, "group_or_hvo")

        if segment is not None and not isinstance(segment, ISegment):
            raise FP_ParameterError("segment must be an ISegment object or None")

        group = self.__ResolveObject(group_or_hvo)

        group.EndSegmentRA = segment

    @OperationsMethod
    def GetColumn(self, group_or_hvo):
        """
        Get the column position of a word group in the chart.

        Args:
            group_or_hvo: Either an IConstChartWordGroup object or its HVO

        Returns:
            ICmPossibility or None: The column object, or None if not set

        Raises:
            FP_NullParameterError: If group_or_hvo is None

        Example:
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> column = project.ConstChartWordGroups.GetColumn(wg)
            >>> if column:
            ...     col_name = ITsString(column.Name.BestAnalysisAlternative).Text
            ...     print(f"Column: {col_name}")

        Notes:
            - Returns None if column not set
            - Column is from the chart template
            - Column defines position in discourse structure

        See Also:
            SetColumn
        """
        self._ValidateParam(group_or_hvo, "group_or_hvo")

        group = self.__ResolveObject(group_or_hvo)

        return group.ColumnRA if hasattr(group, "ColumnRA") else None

    @OperationsMethod
    def SetColumn(self, group_or_hvo, column):
        """
        Set the column position of a word group in the chart.

        Args:
            group_or_hvo: Either an IConstChartWordGroup object or its HVO
            column: ICmPossibility column object (can be None to clear)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If group_or_hvo is None

        Example:
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> # Get column from template
            >>> template = project.ConstCharts.GetTemplate(chart)
            >>> column = template.SubPossibilitiesOS[0]  # First column
            >>> project.ConstChartWordGroups.SetColumn(wg, column)

        Notes:
            - Column can be None to clear
            - Column should be from chart template
            - Column defines position in discourse structure

        See Also:
            GetColumn
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(group_or_hvo, "group_or_hvo")

        group = self.__ResolveObject(group_or_hvo)

        group.ColumnRA = column

    # --- Private Helper Methods ---

    def __ResolveObject(self, group_or_hvo):
        """
        Resolve HVO or object to IConstChartWordGroup.

        Args:
            group_or_hvo: Either an IConstChartWordGroup object or an HVO (int)

        Returns:
            IConstChartWordGroup: The resolved word group object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a word group
        """
        if isinstance(group_or_hvo, int):
            obj = self.project.Object(group_or_hvo)
            if not isinstance(obj, IConstChartWordGroup):
                raise FP_ParameterError("HVO does not refer to a word group")
            return obj
        return group_or_hvo

    def __ResolveRow(self, row_or_hvo):
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

    # --- Reordering Support ---

    def _GetSequence(self, parent):
        """
        Get the owning sequence for word groups.

        Args:
            parent: The parent IConstChartRow object

        Returns:
            ILcmOwningSequence: The CellsOS sequence

        Notes:
            - Required for BaseOperations reordering methods
            - Returns the CellsOS collection from the row
        """
        return parent.CellsOS
