#
#   ConstChartOperations.py
#
#   Class: ConstChartOperations
#          Constituent chart operations for discourse analysis in FieldWorks
#          Language Explorer projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key

# Import FLEx LCM types
from SIL.LCModel import (
    IDsConstChart,
    IDsConstChartFactory,
    IDsConstChartRepository,
    IDsDiscourseData,
    IConstChartRow,
    ICmPossibility,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class ConstChartOperations(BaseOperations):
    """
    This class provides operations for managing constituent charts in a
    FieldWorks project for discourse analysis.

    Constituent charts are used to analyze the structure of texts, showing
    how clauses, phrases, and other discourse elements are organized. Each
    chart contains rows that represent segments of the analyzed text.

    This class should be accessed via FLExProject.ConstCharts property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Create a new constituent chart
        chart = project.ConstCharts.Create("Genesis 1 Analysis")

        # Get all charts
        for chart in project.ConstCharts.GetAll():
            name = project.ConstCharts.GetName(chart)
            print(f"Chart: {name}")

        # Find a specific chart
        chart = project.ConstCharts.Find("Genesis 1 Analysis")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ConstChartOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all constituent charts in the project.

        This method returns an iterator over all IDsConstChart objects in the
        project database, allowing iteration over all discourse analysis charts.

        Yields:
            IDsConstChart: Each constituent chart object in the project

        Example:
            >>> for chart in project.ConstCharts.GetAll():
            ...     name = project.ConstCharts.GetName(chart)
            ...     row_count = chart.RowsOS.Count
            ...     print(f"{name} ({row_count} rows)")
            Genesis 1 Analysis (45 rows)
            Mark 1 Analysis (32 rows)

        Notes:
            - Returns an iterator for memory efficiency
            - Charts are returned in database order
            - Each chart can contain multiple rows for analysis
            - Use GetName() to access the chart name

        See Also:
            Find, Create, GetName
        """
        # Get the DsDiscourse object that contains all charts
        discourse = self.project.lp.DiscourseDataOA
        if discourse is not None and hasattr(discourse, "ChartsOC"):
            for chart in discourse.ChartsOC:
                if isinstance(chart, IDsConstChart):
                    yield chart

    @OperationsMethod
    def Create(self, name, template=None):
        """
        Create a new constituent chart for discourse analysis.

        Args:
            name (str): The name of the chart (e.g., "Genesis 1 Analysis")
            template (ICmPossibility, optional): Chart template to use. If None,
                creates a chart without a template.

        Returns:
            IDsConstChart: The newly created chart object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If name is None
            FP_ParameterError: If name is empty

        Example:
            >>> # Create a simple chart
            >>> chart = project.ConstCharts.Create("Matthew 5 Analysis")
            >>> print(project.ConstCharts.GetName(chart))
            Matthew 5 Analysis

            >>> # Create chart with template
            >>> template = project.ConstCharts.GetTemplate(existing_chart)
            >>> chart = project.ConstCharts.Create("New Analysis", template)

        Notes:
            - The chart is added to the discourse data container
            - Charts are used for constituent analysis of texts
            - Template defines default columns and structure
            - Factory.Create() automatically adds chart to repository
            - Chart starts with no rows - add rows using ConstChartRows

        See Also:
            Delete, Find, GetName, SetTemplate
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Chart name cannot be empty")

        # Get or create the DsDiscourse container
        discourse = self.__GetOrCreateDiscourse()

        with self._TransactionCM(f"Create chart '{name}'"):
            # Create the new chart using the factory
            factory = self.project.project.ServiceLocator.GetService(IDsConstChartFactory)
            new_chart = factory.Create()

            # Add to discourse charts collection
            discourse.ChartsOC.Add(new_chart)

            # Set the name
            wsHandle = self.__WSHandleAnalysis()
            mkstr = TsStringUtils.MakeString(name, wsHandle)
            new_chart.Name.set_String(wsHandle, mkstr)

            # Set template if provided
            if template:
                new_chart.TemplateRA = template

            return new_chart

    @OperationsMethod
    def Delete(self, chart_or_hvo):
        """
        Delete a constituent chart from the project.

        Args:
            chart_or_hvo: Either an IDsConstChart object or its HVO (database ID)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If chart_or_hvo is None
            FP_ParameterError: If chart doesn't exist

        Example:
            >>> chart = project.ConstCharts.Find("Old Analysis")
            >>> if chart:
            ...     project.ConstCharts.Delete(chart)

            >>> # Delete by HVO
            >>> project.ConstCharts.Delete(12345)

        Warning:
            - This is a destructive operation
            - All rows, word groups, and markers will be deleted
            - Cannot be undone
            - Chart will be removed from discourse data

        Notes:
            - Deletion cascades to all owned objects (rows, word groups, etc.)
            - Cross-references are automatically cleaned up

        See Also:
            Create, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        # Resolve to chart object
        chart = self.__ResolveObject(chart_or_hvo)

        # Delete the chart (LCM handles removal from repository)
        chart.Delete()

    @OperationsMethod
    def Find(self, name):
        """
        Find a constituent chart by its name.

        Args:
            name (str): The chart name to search for

        Returns:
            IDsConstChart or None: The chart object if found, None otherwise

        Raises:
            FP_NullParameterError: If name is None

        Example:
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> if chart:
            ...     name = project.ConstCharts.GetName(chart)
            ...     print(f"Found: {name}")
            Found: Genesis 1 Analysis

        Notes:
            - Returns first match only
            - Search is case-sensitive
            - Searches in default analysis writing system
            - Returns None if not found (doesn't raise exception)

        See Also:
            FindByHvo, GetAll, GetName
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        wsHandle = self.__WSHandleAnalysis()

        # Search through all charts
        target = normalize_match_key(name, casefold=False)
        for chart in self.GetAll():
            chart_name = ITsString(chart.Name.get_String(wsHandle)).Text
            if normalize_match_key(chart_name, casefold=False) == target:
                return chart

        return None

    @OperationsMethod
    def FindByHvo(self, hvo):
        """
        Find a constituent chart by its HVO (database ID).

        Args:
            hvo (int): The HVO to search for

        Returns:
            IDsConstChart or None: The chart object if found, None otherwise

        Raises:
            FP_NullParameterError: If hvo is None

        Example:
            >>> chart = project.ConstCharts.FindByHvo(12345)
            >>> if chart:
            ...     print("Chart found")

        Notes:
            - HVOs are unique within a project
            - Returns None if not found or if object is not a chart
            - More efficient than searching by name

        See Also:
            Find, GetAll
        """
        self._ValidateParam(hvo, "hvo")

        try:
            obj = self.project.Object(hvo)
            if isinstance(obj, IDsConstChart):
                return obj
        except Exception:
            pass

        return None

    # --- Chart Properties ---

    @OperationsMethod
    def GetName(self, chart_or_hvo):
        """
        Get the name of a constituent chart.

        Args:
            chart_or_hvo: Either an IDsConstChart object or its HVO

        Returns:
            str: The chart name (empty string if not set)

        Raises:
            FP_NullParameterError: If chart_or_hvo is None

        Example:
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> name = project.ConstCharts.GetName(chart)
            >>> print(name)
            Genesis 1 Analysis

        Notes:
            - Returns empty string if name not set
            - Uses default analysis writing system

        See Also:
            SetName, Find
        """
        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        chart = self.__ResolveObject(chart_or_hvo)
        wsHandle = self.__WSHandleAnalysis()

        return ITsString(chart.Name.get_String(wsHandle)).Text or ""

    @OperationsMethod
    def SetName(self, chart_or_hvo, name):
        """
        Set the name of a constituent chart.

        Args:
            chart_or_hvo: Either an IDsConstChart object or its HVO
            name (str): The new chart name

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If chart_or_hvo or name is None
            FP_ParameterError: If name is empty

        Example:
            >>> chart = project.ConstCharts.Find("Old Name")
            >>> project.ConstCharts.SetName(chart, "New Name")
            >>> print(project.ConstCharts.GetName(chart))
            New Name

        Notes:
            - Name is stored in default analysis writing system
            - Changes are immediately persisted

        See Also:
            GetName, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(chart_or_hvo, "chart_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Chart name cannot be empty")

        chart = self.__ResolveObject(chart_or_hvo)
        wsHandle = self.__WSHandleAnalysis()

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        chart.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetTemplate(self, chart_or_hvo):
        """
        Get the template associated with a constituent chart.

        Args:
            chart_or_hvo: Either an IDsConstChart object or its HVO

        Returns:
            ICmPossibility or None: The template object, or None if not set

        Raises:
            FP_NullParameterError: If chart_or_hvo is None

        Example:
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> template = project.ConstCharts.GetTemplate(chart)
            >>> if template:
            ...     print("Chart has template")

        Notes:
            - Template defines column structure and defaults
            - Returns None if no template assigned
            - Template is a CmPossibility object

        See Also:
            SetTemplate, Create
        """
        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        chart = self.__ResolveObject(chart_or_hvo)

        return chart.TemplateRA if hasattr(chart, "TemplateRA") else None

    @OperationsMethod
    def SetTemplate(self, chart_or_hvo, template):
        """
        Set the template for a constituent chart.

        Args:
            chart_or_hvo: Either an IDsConstChart object or its HVO
            template: ICmPossibility template object (can be None to clear)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If chart_or_hvo is None

        Example:
            >>> chart = project.ConstCharts.Find("Genesis 1 Analysis")
            >>> template = project.ConstCharts.GetTemplate(other_chart)
            >>> project.ConstCharts.SetTemplate(chart, template)

            >>> # Clear template
            >>> project.ConstCharts.SetTemplate(chart, None)

        Notes:
            - Template can be None to clear
            - Template defines column structure
            - Changes affect chart display in FLEx

        See Also:
            GetTemplate, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        chart = self.__ResolveObject(chart_or_hvo)

        chart.TemplateRA = template

    @wrap_enumerable
    @OperationsMethod
    def GetRows(self, chart_or_hvo):
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
            >>> rows = project.ConstCharts.GetRows(chart)
            >>> for row in rows:
            ...     label = project.ConstChartRows.GetLabel(row)
            ...     print(f"Row: {label}")

        Notes:
            - Returns empty list if chart has no rows
            - Rows are in database order
            - Each row represents a segment of analyzed text
            - Use ConstChartRows operations to manipulate rows

        See Also:
            ConstChartRowOperations, Create
        """
        self._ValidateParam(chart_or_hvo, "chart_or_hvo")

        chart = self.__ResolveObject(chart_or_hvo)

        return list(chart.RowsOS)

    # --- Private Helper Methods ---

    def __ResolveObject(self, chart_or_hvo):
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

    def __WSHandleAnalysis(self):
        """
        Get writing system handle for analysis writing system.

        Returns:
            int: The analysis writing system handle
        """
        return self.project.project.DefaultAnalWs

    def __GetOrCreateDiscourse(self):
        """
        Get or create the DsDiscourseData container for charts.

        Returns:
            IDsDiscourseData: The discourse data container

        Notes:
            - Creates DsDiscourseData if it doesn't exist
            - DsDiscourseData is the container for all discourse analysis data
        """
        discourse = self.project.lp.DiscourseDataOA

        if discourse is None:
            # Create DsDiscourseData container
            from SIL.LCModel import IDsDiscourseDataFactory

            factory = self.project.project.ServiceLocator.GetService(IDsDiscourseDataFactory)
            discourse = factory.Create()
            self.project.lp.DiscourseDataOA = discourse

        return discourse

    # --- Reordering Support ---

    def _GetSequence(self, parent):
        """
        Get the owning sequence for chart rows.

        Args:
            parent: The parent IDsConstChart object

        Returns:
            ILcmOwningSequence: The RowsOS sequence

        Notes:
            - Required for BaseOperations reordering methods
            - Returns the RowsOS collection from the chart
        """
        return parent.RowsOS
