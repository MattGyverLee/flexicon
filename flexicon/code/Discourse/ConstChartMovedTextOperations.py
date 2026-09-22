#
#   ConstChartMovedTextOperations.py
#
#   Class: ConstChartMovedTextOperations
#          Moved text marker operations for constituent charts in FieldWorks
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
    IConstChartMovedTextMarker,
    IConstChartMovedTextMarkerFactory,
    IConstChartRow,
    IConstChartWordGroup,
    IDsConstChart,
)

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ConstChartMovedTextOperations(BaseOperations):
    """
    This class provides operations for managing moved text markers in constituent
    charts for discourse analysis in FieldWorks projects.

    Moved text markers indicate that a word group represents text that has been
    moved from its canonical position (preposed or postposed) in the discourse
    structure.

    This class should be accessed via FLExProject.ConstChartMovedText property.

    Usage::

        from flexicon import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a word group
        chart = project.ConstCharts.Find("Genesis 1 Analysis")
        row = project.ConstChartRows.Find(chart, 0)
        wg = project.ConstChartWordGroups.Find(row, 0)

        # Mark as preposed text
        marker = project.ConstChartMovedText.Create(wg, preposed=True)

        # Check if preposed
        if project.ConstChartMovedText.IsPreposed(marker):
            print("Text is preposed")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ConstChartMovedTextOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, word_group_or_hvo, preposed=True):
        """
        Create a moved text marker for a word group.

        Marks a word group as containing moved text (either preposed or postposed
        from its canonical position in the discourse).

        Args:
            word_group_or_hvo: Either an IConstChartWordGroup object or its HVO
            preposed (bool): True if text is preposed (moved earlier), False if
                postposed (moved later). Default is True.

        Returns:
            IConstChartMovedTextMarker: The newly created marker object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If word_group_or_hvo is None

        Example:
            >>> # Mark word group as preposed
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> marker = project.ConstChartMovedText.Create(wg, preposed=True)
            >>> print(project.ConstChartMovedText.IsPreposed(marker))
            True

            >>> # Mark as postposed
            >>> marker = project.ConstChartMovedText.Create(wg, preposed=False)
            >>> print(project.ConstChartMovedText.IsPreposed(marker))
            False

        Notes:
            - Preposed text appears earlier than its canonical position
            - Postposed text appears later than its canonical position
            - Marker is inserted into row.CellsOS (the row that owns the word
              group); WordGroupRA and ColumnRA are set before Preposed to avoid
              NullReferenceException (R5, #290 model).
            - Word group can reference at most one moved text marker.

        See Also:
            Delete, Find, IsPreposed, SetPreposed
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(word_group_or_hvo, "word_group_or_hvo")

        word_group = self.__ResolveWordGroup(word_group_or_hvo)

        row = self.__RowFromWordGroup(word_group)
        if row is None:
            raise FP_ParameterError("word_group has no owning row (Owner is None)")

        with self._TransactionCM("Create moved text marker"):
            # Create the new moved text marker using the factory.
            factory = self.project.project.ServiceLocator.GetService(IConstChartMovedTextMarkerFactory)
            new_marker = factory.Create()

            # Step 1: insert into row.CellsOS BEFORE setting any property
            # setters (avoids NullReferenceException -- R5, issue #290 model).
            row.CellsOS.Add(new_marker)

            # Step 2: set WordGroupRA and ColumnRA before Preposed.
            new_marker.WordGroupRA = word_group
            if hasattr(word_group, "ColumnRA") and word_group.ColumnRA is not None:
                new_marker.ColumnRA = word_group.ColumnRA

            # Step 3: set Preposed after the above.
            # VERIFY in T3: full path with live segments needed to confirm
            # NRE is resolved (analogical basis: #290 resolution).
            new_marker.Preposed = bool(preposed)

            return new_marker

    @OperationsMethod
    def Delete(self, marker_or_hvo):
        """
        Delete a moved text marker.

        Args:
            marker_or_hvo: Either an IConstChartMovedTextMarker object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If marker_or_hvo is None

        Example:
            >>> marker = project.ConstChartMovedText.Find(wg)
            >>> if marker:
            ...     project.ConstChartMovedText.Delete(marker)

        Warning:
            - This is a destructive operation
            - Cannot be undone
            - Word group will no longer be marked as moved

        See Also:
            Create, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(marker_or_hvo, "marker_or_hvo")

        # Resolve to marker object
        marker = self.__ResolveObject(marker_or_hvo)

        with self._TransactionCM("Delete moved text marker"):
            # Delete the marker (LCM handles removal from repository)
            marker.Delete()

    @OperationsMethod
    def Find(self, word_group_or_hvo):
        """
        Find the moved text marker for a word group.

        Args:
            word_group_or_hvo: Either an IConstChartWordGroup object or its HVO

        Returns:
            IConstChartMovedTextMarker or None: The marker if exists, None otherwise

        Raises:
            FP_NullParameterError: If word_group_or_hvo is None

        Example:
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> marker = project.ConstChartMovedText.Find(wg)
            >>> if marker:
            ...     print("Word group has moved text marker")
            ...     if project.ConstChartMovedText.IsPreposed(marker):
            ...         print("Text is preposed")

        Notes:
            - Returns None if no marker in the row references this word group.
            - Navigates from the word group's owning row through row.CellsOS
              and matches on WordGroupRA (R5/#290 model -- the marker is a peer
              cell in the row, not an owned child of the word group).

        See Also:
            Create, GetAll
        """
        self._ValidateParam(word_group_or_hvo, "word_group_or_hvo")

        word_group = self.__ResolveWordGroup(word_group_or_hvo)

        row = self.__RowFromWordGroup(word_group)
        if row is None:
            return None

        for cell in row.CellsOS:
            if getattr(cell, "ClassName", None) != "ConstChartMovedTextMarker":
                if not isinstance(cell, IConstChartMovedTextMarker):
                    continue
            try:
                marker = IConstChartMovedTextMarker(cell)
            except Exception:
                marker = cell
            wgra = getattr(marker, "WordGroupRA", None)
            if wgra is None:
                continue
            if wgra.Hvo == word_group.Hvo or str(wgra.Guid) == str(word_group.Guid):
                return marker

        return None

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, chart_or_hvo):
        """
        Get all moved text markers in a constituent chart.

        Args:
            chart_or_hvo: Either an IDsConstChart object or its HVO

        Returns:
            list[IConstChartMovedTextMarker]: List of moved text markers (empty list if none)

        Raises:
            FP_NullParameterError: If chart_or_hvo is None

        Example:
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> markers = project.ConstChartMovedText.GetAll(chart)
            >>> preposed_count = sum(1 for m in markers
            ...     if project.ConstChartMovedText.IsPreposed(m))
            >>> print(f"Found {preposed_count} preposed markers")

        Notes:
            - Returns empty list if chart has no moved text markers.
            - Searches row.CellsOS directly for IConstChartMovedTextMarker
              instances (R5/#290 model -- markers are peer cells, not word
              group children).
            - Includes both preposed and postposed markers.

        See Also:
            Find, Create
        """
        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        chart = self.__ResolveChart(chart_or_hvo)

        markers = []
        # Iterate CellsOS directly; markers are peer cells in the row.
        for row in chart.RowsOS:
            for cell in row.CellsOS:
                if getattr(cell, "ClassName", None) != "ConstChartMovedTextMarker":
                    if not isinstance(cell, IConstChartMovedTextMarker):
                        continue
                try:
                    markers.append(IConstChartMovedTextMarker(cell))
                except Exception:
                    markers.append(cell)

        return markers

    # --- Marker Properties ---

    @OperationsMethod
    def IsPreposed(self, marker_or_hvo):
        """
        Check if a moved text marker indicates preposed text.

        Args:
            marker_or_hvo: Either an IConstChartMovedTextMarker object or its HVO

        Returns:
            bool: True if text is preposed, False if postposed

        Raises:
            FP_NullParameterError: If marker_or_hvo is None

        Example:
            >>> marker = project.ConstChartMovedText.Find(wg)
            >>> if marker:
            ...     if project.ConstChartMovedText.IsPreposed(marker):
            ...         print("Text moved earlier")
            ...     else:
            ...         print("Text moved later")

        Notes:
            - Preposed = text appears earlier than canonical position
            - Postposed = text appears later than canonical position
            - Returns boolean value of Preposed property

        See Also:
            SetPreposed, Create
        """
        self._ValidateParam(marker_or_hvo, "marker_or_hvo")

        marker = self.__ResolveObject(marker_or_hvo)

        return marker.Preposed

    @OperationsMethod
    def SetPreposed(self, marker_or_hvo, value):
        """
        Set whether moved text is preposed or postposed.

        Args:
            marker_or_hvo: Either an IConstChartMovedTextMarker object or its HVO
            value (bool): True for preposed, False for postposed

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If marker_or_hvo or value is None

        Example:
            >>> marker = project.ConstChartMovedText.Find(wg)
            >>> if marker:
            ...     # Change from preposed to postposed
            ...     project.ConstChartMovedText.SetPreposed(marker, False)

        Notes:
            - True = preposed (text moved earlier)
            - False = postposed (text moved later)
            - Changes are immediately persisted

        See Also:
            IsPreposed, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(marker_or_hvo, "marker_or_hvo")
        self._ValidateParam(value, "value")

        marker = self.__ResolveObject(marker_or_hvo)

        with self._TransactionCM("Set moved-text preposed flag"):
            marker.Preposed = bool(value)

    @OperationsMethod
    def GetWordGroup(self, marker_or_hvo):
        """
        Get the word group associated with a moved text marker.

        Args:
            marker_or_hvo: Either an IConstChartMovedTextMarker object or its HVO

        Returns:
            IConstChartWordGroup or None: The word group, or None if not found

        Raises:
            FP_NullParameterError: If marker_or_hvo is None

        Example:
            >>> marker = project.ConstChartMovedText.Find(wg)
            >>> if marker:
            ...     word_group = project.ConstChartMovedText.GetWordGroup(marker)
            ...     if word_group:
            ...         print(f"Marker belongs to word group {word_group.Hvo}")

        Notes:
            - Returns None if WordGroupRA is not set.
            - Navigation is via WordGroupRA (R5/#290 model): the marker's owner
              is the row (row.CellsOS), not the word group. The word group is
              reached through the WordGroupRA reference attribute.

        See Also:
            Create, Find
        """
        self._ValidateParam(marker_or_hvo, "marker_or_hvo")

        marker = self.__ResolveObject(marker_or_hvo)

        # Navigate via WordGroupRA: marker -> word group reference.
        return marker.WordGroupRA if hasattr(marker, "WordGroupRA") else None

    # --- Private Helper Methods ---

    def __RowFromWordGroup(self, word_group):
        """Cast word_group.Owner to IConstChartRow (Owner is ICmObject at runtime)."""
        row = word_group.Owner
        if row is None:
            return None
        if isinstance(row, IConstChartRow):
            return row
        try:
            return IConstChartRow(row)
        except Exception:
            return None

    def __ResolveObject(self, marker_or_hvo):
        """
        Resolve HVO or object to IConstChartMovedTextMarker.

        Args:
            marker_or_hvo: Either an IConstChartMovedTextMarker object or an HVO (int)

        Returns:
            IConstChartMovedTextMarker: The resolved marker object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a moved text marker
        """
        if isinstance(marker_or_hvo, int):
            obj = self.project.Object(marker_or_hvo)
            if getattr(obj, "ClassName", None) == "ConstChartMovedTextMarker":
                try:
                    return IConstChartMovedTextMarker(obj)
                except Exception:
                    pass
            if isinstance(obj, IConstChartMovedTextMarker):
                return obj
            raise FP_ParameterError("HVO does not refer to a moved text marker")
        if getattr(marker_or_hvo, "ClassName", None) == "ConstChartMovedTextMarker":
            try:
                return IConstChartMovedTextMarker(marker_or_hvo)
            except Exception:
                pass
        return marker_or_hvo

    def __ResolveWordGroup(self, word_group_or_hvo):
        """
        Resolve HVO or object to IConstChartWordGroup.

        Args:
            word_group_or_hvo: Either an IConstChartWordGroup object or an HVO (int)

        Returns:
            IConstChartWordGroup: The resolved word group object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a word group
        """
        if isinstance(word_group_or_hvo, int):
            obj = self.project.Object(word_group_or_hvo)
            if getattr(obj, "ClassName", None) == "ConstChartWordGroup":
                try:
                    return IConstChartWordGroup(obj)
                except Exception:
                    pass
            if isinstance(obj, IConstChartWordGroup):
                return obj
            raise FP_ParameterError("HVO does not refer to a word group")
        if getattr(word_group_or_hvo, "ClassName", None) == "ConstChartWordGroup":
            try:
                return IConstChartWordGroup(word_group_or_hvo)
            except Exception:
                pass
        return word_group_or_hvo

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
            if getattr(obj, "ClassName", None) == "DsConstChart":
                try:
                    return IDsConstChart(obj)
                except Exception:
                    pass
            if isinstance(obj, IDsConstChart):
                return obj
            raise FP_ParameterError("HVO does not refer to a constituent chart")
        if getattr(chart_or_hvo, "ClassName", None) == "DsConstChart":
            try:
                return IDsConstChart(chart_or_hvo)
            except Exception:
                pass
        return chart_or_hvo

    # --- Reordering Support ---

    def _GetSequence(self, parent):
        """
        Not applicable for moved text markers.

        Moved text markers are cells in row.CellsOS (R5/#290 model). They do
        not expose a reorderable sub-sequence of their own.

        Raises:
            NotImplementedError: Moved text markers don't use a sub-sequence.
        """
        raise NotImplementedError(
            "Moved text markers live in row.CellsOS as peer cells. "
            "Reordering methods are not applicable to this type."
        )
