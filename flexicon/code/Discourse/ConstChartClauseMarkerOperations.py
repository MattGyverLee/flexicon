#
#   ConstChartClauseMarkerOperations.py
#
#   Class: ConstChartClauseMarkerOperations
#          Clause marker operations for constituent charts in FieldWorks
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
    IConstChartClauseMarker,
    IConstChartClauseMarkerFactory,
    IConstChartRow,
    IConstChartWordGroup,
)

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ConstChartClauseMarkerOperations(BaseOperations):
    """
    This class provides operations for managing clause markers in constituent
    charts for discourse analysis in FieldWorks projects.

    Clause markers identify clausal relationships and dependencies within the
    discourse structure. They link word groups and mark clause boundaries.

    This class should be accessed via FLExProject.ConstChartClauseMarkers property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a row and word group
        chart = project.ConstCharts.Find("Genesis 1 Analysis")
        row = project.ConstChartRows.Find(chart, 0)
        wg = project.ConstChartWordGroups.Find(row, 0)

        # Create a clause marker
        marker = project.ConstChartClauseMarkers.Create(row, wg)

        # Get all markers in a row
        for marker in project.ConstChartClauseMarkers.GetAll(row):
            # Process clause marker
            pass

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ConstChartClauseMarkerOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @OperationsMethod
    def Create(self, row_or_hvo, word_group):
        """
        Create a new clause marker in a chart row.

        Clause markers mark clausal boundaries and dependencies in the discourse
        analysis. They associate with word groups to identify clause structure.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO
            word_group: IConstChartWordGroup object this marker refers to

        Returns:
            IConstChartClauseMarker: The newly created clause marker object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If row_or_hvo or word_group is None
            FP_ParameterError: If word_group is invalid type

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> wg = project.ConstChartWordGroups.Find(row, 0)
            >>> marker = project.ConstChartClauseMarkers.Create(row, wg)

        Notes:
            - Marker is appended to the row's clause markers collection
            - Each marker identifies a clause boundary or relationship
            - Factory.Create() automatically adds marker to repository
            - Markers can have dependent clauses attached

        See Also:
            Delete, Find, GetWordGroup, AddDependentClause
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(row_or_hvo, "row_or_hvo")
        self._ValidateParam(word_group, "word_group")

        row = self.__ResolveRow(row_or_hvo)

        # Validate word group
        if not isinstance(word_group, IConstChartWordGroup):
            raise FP_ParameterError("word_group must be an IConstChartWordGroup object")

        with self._TransactionCM("Create clause marker"):
            # Create the new clause marker using the factory
            factory = self.project.project.ServiceLocator.GetService(IConstChartClauseMarkerFactory)
            new_marker = factory.Create()

            # Add to row's clause markers collection
            # Note: In FLEx, clause markers may be stored in different collections
            # depending on the chart structure. This assumes a ClauseMarkersOS collection.
            if hasattr(row, "ClauseMarkersOS"):
                row.ClauseMarkersOS.Add(new_marker)

            # Set the word group reference
            if hasattr(new_marker, "WordGroupRA"):
                new_marker.WordGroupRA = word_group

            return new_marker

    @OperationsMethod
    def Delete(self, marker_or_hvo):
        """
        Delete a clause marker from its row.

        Args:
            marker_or_hvo: Either an IConstChartClauseMarker object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If marker_or_hvo is None

        Example:
            >>> marker = project.ConstChartClauseMarkers.Find(row, 0)
            >>> if marker:
            ...     project.ConstChartClauseMarkers.Delete(marker)

        Warning:
            - This is a destructive operation
            - Dependent clause references will be lost
            - Cannot be undone

        Notes:
            - Deletion cascades to all owned relationships
            - Remaining markers maintain their order

        See Also:
            Create, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(marker_or_hvo, "marker_or_hvo")

        # Resolve to marker object
        marker = self.__ResolveObject(marker_or_hvo)

        # Delete the marker (LCM handles removal from repository)
        marker.Delete()

    @OperationsMethod
    def Find(self, row_or_hvo, index):
        """
        Find a clause marker in a row by its index position.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO
            index (int): Zero-based index of the marker to find

        Returns:
            IConstChartClauseMarker or None: The marker if found, None otherwise

        Raises:
            FP_NullParameterError: If row_or_hvo is None

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> marker = project.ConstChartClauseMarkers.Find(row, 0)
            >>> if marker:
            ...     wg = project.ConstChartClauseMarkers.GetWordGroup(marker)
            ...     print(f"Marker references word group {wg.Hvo}")

        Notes:
            - Index is zero-based (0 = first marker)
            - Returns None if index out of range
            - More efficient than iterating GetAll()

        See Also:
            GetAll, Create
        """
        self._ValidateParam(row_or_hvo, "row_or_hvo")

        row = self.__ResolveRow(row_or_hvo)

        if hasattr(row, "ClauseMarkersOS"):
            if index < 0 or index >= row.ClauseMarkersOS.Count:
                return None
            return row.ClauseMarkersOS[index]

        return None

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, row_or_hvo):
        """
        Get all clause markers in a chart row.

        Args:
            row_or_hvo: Either an IConstChartRow object or its HVO

        Returns:
            list: List of IConstChartClauseMarker objects (empty list if none)

        Raises:
            FP_NullParameterError: If row_or_hvo is None

        Example:
            >>> row = project.ConstChartRows.Find(chart, 0)
            >>> markers = project.ConstChartClauseMarkers.GetAll(row)
            >>> for marker in markers:
            ...     wg = project.ConstChartClauseMarkers.GetWordGroup(marker)
            ...     print(f"Marker for word group {wg.Hvo}")

        Notes:
            - Returns empty list if row has no clause markers
            - Markers are in row order
            - Each marker identifies a clause boundary

        See Also:
            Find, Create
        """
        self._ValidateParam(row_or_hvo, "row_or_hvo")

        row = self.__ResolveRow(row_or_hvo)

        if hasattr(row, "ClauseMarkersOS"):
            return list(row.ClauseMarkersOS)

        return []

    # --- Marker Properties ---

    @OperationsMethod
    def GetWordGroup(self, marker_or_hvo):
        """
        Get the word group associated with a clause marker.

        Args:
            marker_or_hvo: Either an IConstChartClauseMarker object or its HVO

        Returns:
            IConstChartWordGroup or None: The word group, or None if not set

        Raises:
            FP_NullParameterError: If marker_or_hvo is None

        Example:
            >>> marker = project.ConstChartClauseMarkers.Find(row, 0)
            >>> wg = project.ConstChartClauseMarkers.GetWordGroup(marker)
            >>> if wg:
            ...     print(f"Marker references word group {wg.Hvo}")

        Notes:
            - Returns None if word group reference not set
            - Word group is from the same or related row
            - Each marker should reference a word group

        See Also:
            Create, GetDependentClauses
        """
        self._ValidateParam(marker_or_hvo, "marker_or_hvo")

        marker = self.__ResolveObject(marker_or_hvo)

        return marker.WordGroupRA if hasattr(marker, "WordGroupRA") else None

    @wrap_enumerable
    @OperationsMethod
    def GetDependentClauses(self, marker_or_hvo):
        """
        Get the dependent clauses associated with a clause marker.

        Dependent clauses show the hierarchical structure of clausal relationships
        in the discourse.

        Args:
            marker_or_hvo: Either an IConstChartClauseMarker object or its HVO

        Returns:
            list: List of dependent clause markers (empty list if none)

        Raises:
            FP_NullParameterError: If marker_or_hvo is None

        Example:
            >>> marker = project.ConstChartClauseMarkers.Find(row, 0)
            >>> dependents = project.ConstChartClauseMarkers.GetDependentClauses(marker)
            >>> print(f"Marker has {len(dependents)} dependent clauses")

        Notes:
            - Returns empty list if no dependent clauses
            - Dependent clauses form a hierarchy
            - Used to mark embedded or subordinate clauses

        See Also:
            AddDependentClause, GetWordGroup
        """
        self._ValidateParam(marker_or_hvo, "marker_or_hvo")

        marker = self.__ResolveObject(marker_or_hvo)

        if hasattr(marker, "DependentClausesRS"):
            return list(marker.DependentClausesRS)

        return []

    @OperationsMethod
    def AddDependentClause(self, marker_or_hvo, clause_marker):
        """
        Add a dependent clause to a clause marker.

        Creates a hierarchical relationship showing that one clause is dependent
        on another in the discourse structure.

        Args:
            marker_or_hvo: Either an IConstChartClauseMarker object or its HVO
            clause_marker: IConstChartClauseMarker object to add as dependent

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If marker_or_hvo or clause_marker is None
            FP_ParameterError: If clause_marker is invalid type

        Example:
            >>> # Create main clause marker
            >>> main_marker = project.ConstChartClauseMarkers.Create(row, main_wg)
            >>>
            >>> # Create dependent clause marker
            >>> dep_marker = project.ConstChartClauseMarkers.Create(row, dep_wg)
            >>>
            >>> # Add as dependent
            >>> project.ConstChartClauseMarkers.AddDependentClause(
            ...     main_marker, dep_marker)

        Notes:
            - Creates hierarchical clause structure
            - Dependent clause is subordinate to main clause
            - Multiple dependents can be added to one marker
            - Circular dependencies should be avoided

        See Also:
            GetDependentClauses, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(marker_or_hvo, "marker_or_hvo")
        self._ValidateParam(clause_marker, "clause_marker")

        if not isinstance(clause_marker, IConstChartClauseMarker):
            raise FP_ParameterError("clause_marker must be an IConstChartClauseMarker object")

        marker = self.__ResolveObject(marker_or_hvo)

        # Add to dependent clauses collection
        if hasattr(marker, "DependentClausesRS"):
            if clause_marker not in marker.DependentClausesRS:
                marker.DependentClausesRS.Add(clause_marker)

    # --- Private Helper Methods ---

    def __ResolveObject(self, marker_or_hvo):
        """
        Resolve HVO or object to IConstChartClauseMarker.

        Args:
            marker_or_hvo: Either an IConstChartClauseMarker object or an HVO (int)

        Returns:
            IConstChartClauseMarker: The resolved marker object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a clause marker
        """
        if isinstance(marker_or_hvo, int):
            obj = self.project.Object(marker_or_hvo)
            if not isinstance(obj, IConstChartClauseMarker):
                raise FP_ParameterError("HVO does not refer to a clause marker")
            return obj
        return marker_or_hvo

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
        Get the owning sequence for clause markers.

        Args:
            parent: The parent IConstChartRow object

        Returns:
            ILcmOwningSequence: The ClauseMarkersOS sequence

        Notes:
            - Required for BaseOperations reordering methods
            - Returns the ClauseMarkersOS collection from the row
        """
        if hasattr(parent, "ClauseMarkersOS"):
            return parent.ClauseMarkersOS
        raise NotImplementedError(
            "Row does not have a ClauseMarkersOS collection. "
            "Clause marker reordering may not be applicable to this row structure."
        )
