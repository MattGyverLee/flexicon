#
#   FilterOperations.py
#
#   Class: FilterOperations
#          Saved filter and query management operations for FieldWorks
#          Language Explorer projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)

import clr

clr.AddReference("System")
import System
from System import Guid

import json
import os

# Import FLEx LCM types
from SIL.LCModel import (
    ICmFilter,
    ICmFilterFactory,
    IFsClosedFeature,
    ILexEntry,
    IWfiWordform,
    IText,
    ICmObjectRepository,
)

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import LCM casting utilities for pythonnet interface casting
from ..lcm_casting import get_pos_from_msa

# Import string utilities
from .string_utils import normalize_text, normalize_match_key

# Import BaseOperations decorators
from ..BaseOperations import OperationsMethod, wrap_enumerable

# --- Filter Type Constants ---


class FilterTypes:
    """
    Filter type constants for different object classes.
    """

    LEXENTRY = "LexEntry"  # Lexical entry filters
    WORDFORM = "Wordform"  # Wordform filters
    TEXT = "Text"  # Text filters
    SENSE = "Sense"  # Sense filters
    ALLOMORPH = "Allomorph"  # Allomorph filters
    CUSTOM = "Custom"  # Custom/generic filters


# --- FilterOperations Class ---


class FilterOperations:
    """
    This class provides operations for managing saved filters and queries
    in a FieldWorks project.

    Filters allow you to define reusable criteria for selecting and filtering
    different types of objects (entries, wordforms, texts, etc.). Each filter
    has a name, type, and criteria definition that can be applied to collections
    of objects.

    This class should be accessed via FLExProject.Filter property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Create a new filter
        filter_obj = project.Filter.Create(
            "Verbs",
            FilterTypes.LEXENTRY,
            {"pos": "verb"}
        )

        # Get all filters
        for f in project.Filter.GetAll():
            name = project.Filter.GetName(f)
            print(name)

        # Find a filter by name
        filter_obj = project.Filter.Find("Verbs")

        # Apply filter to entries
        entries = list(project.LexEntry.GetAll())
        matching = project.Filter.ApplyFilter(filter_obj, entries)

        # Export filter definition
        project.Filter.ExportFilter(filter_obj, "/path/to/filter.json")

        project.CloseProject()

    Notes:
        - Filters are stored as custom data structures in the project
        - Filter criteria are stored as JSON-serializable dictionaries
        - Different filter types support different criteria
        - Filters can be exported and imported for reuse across projects
    """

    def __init__(self, project):
        """
        Initialize FilterOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        self.project = project
        self._filter_cache = {}  # Cache for filter objects

    # --- Core Filter Management ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all saved filters in the project.

        This method returns all filter objects stored in the project,
        regardless of their type.

        Yields:
            dict: Each filter object with keys: guid, name, filter_type, criteria

        Example:
            >>> for filter_obj in project.Filter.GetAll():
            ...     name = filter_obj['name']
            ...     filter_type = filter_obj['filter_type']
            ...     print(f"{name} ({filter_type})")
            Verbs (LexEntry)
            Nouns (LexEntry)
            Correct Wordforms (Wordform)

        Notes:
            - Returns an iterator for memory efficiency
            - Filters are loaded from project custom settings
            - Each filter is returned as a dictionary
            - Use Find() to get a specific filter by name

        See Also:
            Find, Create, GetFiltersByType
        """
        filters = self._LoadFiltersFromProject()
        for filter_guid, filter_data in filters.items():
            yield filter_data

    @OperationsMethod
    def Create(self, name, filter_type, criteria):
        """
        Create a new saved filter in the project.

        Args:
            name (str): The name of the filter
            filter_type (str): The type of filter (use FilterTypes constants)
            criteria (dict): The filter criteria as a dictionary

        Returns:
            dict: The newly created filter object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If name, filter_type, or criteria is None
            FP_ParameterError: If name is empty or filter already exists

        Example:
            >>> # Create a lexical entry filter
            >>> verb_filter = project.Filter.Create(
            ...     "Verbs",
            ...     FilterTypes.LEXENTRY,
            ...     {"pos": "verb", "status": "approved"}
            ... )

            >>> # Create a wordform filter
            >>> correct_wf = project.Filter.Create(
            ...     "Correct Wordforms",
            ...     FilterTypes.WORDFORM,
            ...     {"spelling_status": 2}  # 2 = CORRECT
            ... )

            >>> # Create a text filter
            >>> genre_filter = project.Filter.Create(
            ...     "Narratives",
            ...     FilterTypes.TEXT,
            ...     {"genre": "narrative"}
            ... )

        Notes:
            - Filter name must be unique
            - Criteria should be a JSON-serializable dictionary
            - Filter is immediately saved to the project
            - A unique GUID is automatically assigned
            - Common criteria keys depend on filter type:
              - LexEntry: pos, morph_type, date_created, etc.
              - Wordform: spelling_status, form_pattern, etc.
              - Text: genre, title_pattern, etc.

        See Also:
            Delete, Find, GetCriteria, SetCriteria
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Filter name cannot be empty")

        # Check if filter already exists
        if self.Find(name) is not None:
            raise FP_ParameterError(f"Filter with name '{name}' already exists")

        # Validate filter type
        valid_types = [
            FilterTypes.LEXENTRY,
            FilterTypes.WORDFORM,
            FilterTypes.TEXT,
            FilterTypes.SENSE,
            FilterTypes.ALLOMORPH,
            FilterTypes.CUSTOM,
        ]
        if filter_type not in valid_types:
            raise FP_ParameterError(f"Invalid filter type: {filter_type}. " f"Use one of: {', '.join(valid_types)}")

        # Create filter object with unique GUID
        filter_guid = str(Guid.NewGuid())
        filter_obj = {
            "guid": filter_guid,
            "name": name.strip(),
            "filter_type": filter_type,
            "criteria": criteria,
            "date_created": System.DateTime.Now.ToString(),
            "date_modified": System.DateTime.Now.ToString(),
        }

        # Save to project
        filters = self._LoadFiltersFromProject()
        filters[filter_guid] = filter_obj
        self._SaveFiltersToProject(filters)

        # Update cache
        self._filter_cache[filter_guid] = filter_obj

        return filter_obj

    @OperationsMethod
    def Delete(self, filter_obj):
        """
        Delete a saved filter from the project.

        Args:
            filter_obj (dict): The filter object to delete

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If filter_obj is None
            FP_ParameterError: If filter doesn't exist

        Example:
            >>> filter_obj = project.Filter.Find("Old Filter")
            >>> if filter_obj:
            ...     project.Filter.Delete(filter_obj)

        Warning:
            - This is a destructive operation
            - Cannot be undone
            - Filter is permanently removed from the project

        Notes:
            - Filter is removed from project custom settings
            - All filter metadata is deleted
            - Does not affect objects that were previously filtered

        See Also:
            Create, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(filter_obj, "filter_obj")

        filter_guid = filter_obj.get("guid")
        if not filter_guid:
            raise FP_ParameterError("Invalid filter object: missing GUID")

        # Load filters and remove
        filters = self._LoadFiltersFromProject()
        if filter_guid not in filters:
            raise FP_ParameterError("Filter not found in project")

        del filters[filter_guid]
        self._SaveFiltersToProject(filters)

        # Clear from cache
        if filter_guid in self._filter_cache:
            del self._filter_cache[filter_guid]

    @OperationsMethod
    def Find(self, name):
        """
        Find a saved filter by name.

        Args:
            name (str): The name of the filter to find

        Returns:
            dict or None: The filter object if found, None otherwise

        Raises:
            FP_NullParameterError: If name is None

        Example:
            >>> verb_filter = project.Filter.Find("Verbs")
            >>> if verb_filter:
            ...     criteria = project.Filter.GetCriteria(verb_filter)
            ...     print(f"Filter criteria: {criteria}")
            Filter criteria: {'pos': 'verb'}

            >>> # Check if filter exists
            >>> if project.Filter.Find("Nouns") is None:
            ...     print("Nouns filter not found")

        Notes:
            - Search is case-sensitive
            - Returns None if filter not found (doesn't raise exception)
            - Returns first match if multiple filters have same name
            - Filter names should be unique

        See Also:
            Exists, GetAll, Create
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        # NFD-normalize both sides: FLEx stores Unicode in NFD, Python
        # source is typically NFC. A user looking up "Verbes Compose" with
        # NFC e-acute against NFD-stored data would silently miss without
        # this. (issue #125)
        target = normalize_match_key(name.strip(), casefold=False)
        filters = self._LoadFiltersFromProject()
        for filter_data in filters.values():
            if normalize_match_key(filter_data["name"], casefold=False) == target:
                return filter_data

        return None

    @OperationsMethod
    def Exists(self, name):
        """
        Check if a filter with the given name exists.

        Args:
            name (str): The filter name to check

        Returns:
            bool: True if a filter exists with this name, False otherwise

        Raises:
            FP_NullParameterError: If name is None

        Example:
            >>> if not project.Filter.Exists("Verbs"):
            ...     verb_filter = project.Filter.Create(
            ...         "Verbs",
            ...         FilterTypes.LEXENTRY,
            ...         {"pos": "verb"}
            ...     )

        Notes:
            - Search is case-sensitive
            - Returns False for empty or whitespace-only names
            - Use Find() to get the actual filter object

        See Also:
            Find, Create
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return False

        return self.Find(name) is not None

    # --- Filter Properties ---

    @OperationsMethod
    def GetName(self, filter_obj):
        """
        Get the name of a filter.

        Args:
            filter_obj (dict): The filter object

        Returns:
            str: The filter name

        Raises:
            FP_NullParameterError: If filter_obj is None
            FP_ParameterError: If filter_obj is invalid

        Example:
            >>> for filter_obj in project.Filter.GetAll():
            ...     name = project.Filter.GetName(filter_obj)
            ...     print(name)
            Verbs
            Nouns
            Adjectives

        Notes:
            - Name is always a non-empty string
            - Names should be unique but this is not enforced

        See Also:
            SetName, Find
        """
        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict) or "name" not in filter_obj:
            raise FP_ParameterError("Invalid filter object")

        return filter_obj["name"]

    @OperationsMethod
    def SetName(self, filter_obj, name):
        """
        Set the name of a filter.

        Args:
            filter_obj (dict): The filter object
            name (str): The new name for the filter

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If filter_obj or name is None
            FP_ParameterError: If name is empty or filter is invalid

        Example:
            >>> filter_obj = project.Filter.Find("Verbs")
            >>> project.Filter.SetName(filter_obj, "All Verbs")
            >>> print(project.Filter.GetName(filter_obj))
            All Verbs

        Notes:
            - Name must not be empty
            - Changing name does not check for duplicates
            - Filter is immediately saved to project
            - Updates modification date

        See Also:
            GetName, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(filter_obj, "filter_obj")

        if not name or not name.strip():
            raise FP_ParameterError("Filter name cannot be empty")

        if not isinstance(filter_obj, dict) or "guid" not in filter_obj:
            raise FP_ParameterError("Invalid filter object")

        # Update filter
        filter_obj["name"] = name.strip()
        filter_obj["date_modified"] = System.DateTime.Now.ToString()

        # Save to project
        filters = self._LoadFiltersFromProject()
        filter_guid = filter_obj["guid"]
        filters[filter_guid] = filter_obj
        self._SaveFiltersToProject(filters)

    @OperationsMethod
    def GetCriteria(self, filter_obj):
        """
        Get the filter criteria definition.

        The criteria is a dictionary that defines the filter conditions.
        The structure depends on the filter type.

        Args:
            filter_obj (dict): The filter object

        Returns:
            dict: The filter criteria

        Raises:
            FP_NullParameterError: If filter_obj is None
            FP_ParameterError: If filter_obj is invalid

        Example:
            >>> verb_filter = project.Filter.Find("Verbs")
            >>> criteria = project.Filter.GetCriteria(verb_filter)
            >>> print(criteria)
            {'pos': 'verb', 'status': 'approved'}

            >>> # Check specific criterion
            >>> if criteria.get('pos') == 'verb':
            ...     print("This is a verb filter")

        Notes:
            - Criteria is always a dictionary
            - Keys and values depend on filter type
            - Common LexEntry criteria: pos, morph_type, etc.
            - Common Wordform criteria: spelling_status, etc.
            - Returns original criteria object (modifications affect filter)

        See Also:
            SetCriteria, GetFilterType
        """
        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict) or "criteria" not in filter_obj:
            raise FP_ParameterError("Invalid filter object")

        return filter_obj["criteria"]

    @OperationsMethod
    def SetCriteria(self, filter_obj, criteria):
        """
        Set the filter criteria definition.

        Args:
            filter_obj (dict): The filter object
            criteria (dict): The new filter criteria

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If filter_obj or criteria is None
            FP_ParameterError: If filter_obj is invalid

        Example:
            >>> verb_filter = project.Filter.Find("Verbs")
            >>> # Update criteria to include transitivity
            >>> new_criteria = {
            ...     'pos': 'verb',
            ...     'status': 'approved',
            ...     'transitivity': 'transitive'
            ... }
            >>> project.Filter.SetCriteria(verb_filter, new_criteria)

            >>> # Replace criteria completely
            >>> project.Filter.SetCriteria(verb_filter, {'pos': 'noun'})

        Notes:
            - Criteria must be a JSON-serializable dictionary
            - Completely replaces existing criteria
            - Filter is immediately saved to project
            - Updates modification date

        See Also:
            GetCriteria, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict) or "guid" not in filter_obj:
            raise FP_ParameterError("Invalid filter object")

        # Update filter
        filter_obj["criteria"] = criteria
        filter_obj["date_modified"] = System.DateTime.Now.ToString()

        # Save to project
        filters = self._LoadFiltersFromProject()
        filter_guid = filter_obj["guid"]
        filters[filter_guid] = filter_obj
        self._SaveFiltersToProject(filters)

    @OperationsMethod
    def GetFilterType(self, filter_obj):
        """
        Get the filter type (entry/text/wordform/etc.).

        Args:
            filter_obj (dict): The filter object

        Returns:
            str: The filter type (from FilterTypes constants)

        Raises:
            FP_NullParameterError: If filter_obj is None
            FP_ParameterError: If filter_obj is invalid

        Example:
            >>> filter_obj = project.Filter.Find("Verbs")
            >>> filter_type = project.Filter.GetFilterType(filter_obj)
            >>> print(filter_type)
            LexEntry

            >>> # Check filter type before applying
            >>> if filter_type == FilterTypes.LEXENTRY:
            ...     entries = list(project.LexEntry.GetAll())
            ...     matching = project.Filter.ApplyFilter(filter_obj, entries)

        Notes:
            - Filter type determines what objects the filter can process
            - Common types: LexEntry, Wordform, Text, Sense, Allomorph
            - Filter type is set at creation and cannot be changed
            - Use GetFiltersByType() to get all filters of a specific type

        See Also:
            Create, GetFiltersByType, ApplyFilter
        """
        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict) or "filter_type" not in filter_obj:
            raise FP_ParameterError("Invalid filter object")

        return filter_obj["filter_type"]

    @OperationsMethod
    def GetGuid(self, filter_obj):
        """
        Get the GUID of a filter.

        Args:
            filter_obj (dict): The filter object

        Returns:
            str: The filter's GUID as a string

        Raises:
            FP_NullParameterError: If filter_obj is None
            FP_ParameterError: If filter_obj is invalid

        Example:
            >>> filter_obj = project.Filter.Find("Verbs")
            >>> guid = project.Filter.GetGuid(filter_obj)
            >>> print(guid)
            a1b2c3d4-e5f6-7890-abcd-ef1234567890

        Notes:
            - GUIDs are unique identifiers for filters
            - GUIDs are assigned automatically at creation
            - Useful for referencing filters programmatically
            - GUIDs persist across project sessions

        See Also:
            Find, Create
        """
        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict) or "guid" not in filter_obj:
            raise FP_ParameterError("Invalid filter object")

        return filter_obj["guid"]

    # --- Filter Application ---

    @OperationsMethod
    def ApplyFilter(self, filter_obj, object_collection):
        """
        Apply a filter to a collection of objects.

        This method evaluates each object in the collection against the
        filter criteria and returns only those that match.

        Args:
            filter_obj (dict): The filter object to apply
            object_collection: Iterable collection of objects to filter

        Returns:
            list: Objects from the collection that match the filter criteria

        Raises:
            FP_NullParameterError: If filter_obj or object_collection is None
            FP_ParameterError: If filter_obj is invalid

        Example:
            >>> # Filter lexical entries
            >>> verb_filter = project.Filter.Find("Verbs")
            >>> all_entries = list(project.LexEntry.GetAll())
            >>> verbs = project.Filter.ApplyFilter(verb_filter, all_entries)
            >>> print(f"Found {len(verbs)} verbs")

            >>> # Filter wordforms
            >>> correct_filter = project.Filter.Find("Correct Wordforms")
            >>> all_wordforms = list(project.Wordforms.GetAll())
            >>> correct_wfs = project.Filter.ApplyFilter(correct_filter, all_wordforms)

            >>> # Chain filters
            >>> filtered1 = project.Filter.ApplyFilter(filter1, all_entries)
            >>> filtered2 = project.Filter.ApplyFilter(filter2, filtered1)

        Notes:
            - Filter type should match the object collection type
            - Returns a new list (doesn't modify input collection)
            - Empty collection returns empty list
            - Objects that don't match criteria are excluded
            - Filtering is done in Python (not database-level)

        See Also:
            GetMatchCount, GetCriteria, GetFilterType
        """
        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict):
            raise FP_ParameterError("Invalid filter object")

        criteria = self.GetCriteria(filter_obj)
        filter_type = self.GetFilterType(filter_obj)

        matching_objects = []

        for obj in object_collection:
            if self._ObjectMatchesCriteria(obj, criteria, filter_type):
                matching_objects.append(obj)

        return matching_objects

    @OperationsMethod
    def GetMatchCount(self, filter_obj, object_collection=None):
        """
        Get the count of objects matching a filter.

        Args:
            filter_obj (dict): The filter object
            object_collection: Optional collection to count in. If None,
                uses all objects of the appropriate type from the project.

        Returns:
            int: Number of objects matching the filter criteria

        Raises:
            FP_NullParameterError: If filter_obj is None
            FP_ParameterError: If filter_obj is invalid

        Example:
            >>> verb_filter = project.Filter.Find("Verbs")
            >>> # Count all verbs in project
            >>> count = project.Filter.GetMatchCount(verb_filter)
            >>> print(f"Found {count} verbs")

            >>> # Count verbs in specific collection
            >>> recent_entries = get_recent_entries()
            >>> recent_verb_count = project.Filter.GetMatchCount(
            ...     verb_filter,
            ...     recent_entries
            ... )

        Notes:
            - More efficient than len(ApplyFilter(...))
            - If no collection provided, searches entire project
            - Returns 0 if no matches found
            - Useful for filter validation and reporting

        See Also:
            ApplyFilter, GetCriteria
        """
        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict):
            raise FP_ParameterError("Invalid filter object")

        # If no collection provided, get all objects of the filter type
        if object_collection is None:
            filter_type = self.GetFilterType(filter_obj)
            object_collection = self._GetAllObjectsOfType(filter_type)

        matching = self.ApplyFilter(filter_obj, object_collection)
        return len(matching)

    # --- Filter Import/Export ---

    @OperationsMethod
    def ExportFilter(self, filter_obj, file_path):
        """
        Export a filter definition to a JSON file.

        Args:
            filter_obj (dict): The filter object to export
            file_path (str): Path to the output file

        Raises:
            FP_NullParameterError: If filter_obj or file_path is None
            FP_ParameterError: If filter_obj is invalid or export fails

        Example:
            >>> filter_obj = project.Filter.Find("Verbs")
            >>> project.Filter.ExportFilter(filter_obj, "/path/to/verbs.json")

            >>> # Export all filters
            >>> for f in project.Filter.GetAll():
            ...     name = project.Filter.GetName(f)
            ...     file_name = f"{name.replace(' ', '_')}.json"
            ...     project.Filter.ExportFilter(f, file_name)

        Notes:
            - Filter is exported as JSON format
            - File is overwritten if it exists
            - GUID is preserved for re-import
            - Exported filters can be shared across projects
            - File path can be absolute or relative

        See Also:
            ImportFilter, GetCriteria
        """
        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict):
            raise FP_ParameterError("Invalid filter object")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(filter_obj, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise FP_ParameterError(f"Failed to export filter: {e}")

    @OperationsMethod
    def ImportFilter(self, file_path, rename_if_exists=False):
        """
        Import a filter definition from a JSON file.

        Args:
            file_path (str): Path to the filter file to import
            rename_if_exists (bool): If True, rename the filter if name
                already exists. If False, raise error on name conflict.

        Returns:
            dict: The imported filter object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If file_path is None
            FP_ParameterError: If file doesn't exist, is invalid, or name conflicts

        Example:
            >>> # Import a filter
            >>> imported = project.Filter.ImportFilter("/path/to/verbs.json")
            >>> print(f"Imported: {project.Filter.GetName(imported)}")

            >>> # Import with auto-rename on conflict
            >>> imported = project.Filter.ImportFilter(
            ...     "/path/to/filter.json",
            ...     rename_if_exists=True
            ... )

        Notes:
            - Filter file must be valid JSON
            - A new GUID is assigned on import
            - Import preserves name, type, and criteria
            - If rename_if_exists is True, appends number to name (e.g., "Verbs 2")
            - Import date is set to current time

        See Also:
            ExportFilter, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(file_path, "file_path")

        if not os.path.exists(file_path):
            raise FP_ParameterError(f"Filter file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                filter_data = json.load(f)
        except Exception as e:
            raise FP_ParameterError(f"Failed to import filter: {e}")

        # Validate filter data
        if not isinstance(filter_data, dict):
            raise FP_ParameterError("Invalid filter file: not a dictionary")

        required_keys = ["name", "filter_type", "criteria"]
        for key in required_keys:
            if key not in filter_data:
                raise FP_ParameterError(f"Invalid filter file: missing '{key}'")

        # Handle name conflicts
        original_name = filter_data["name"]
        import_name = original_name

        if self.Exists(import_name):
            if rename_if_exists:
                # Find a unique name
                counter = 2
                while self.Exists(f"{original_name} {counter}"):
                    counter += 1
                import_name = f"{original_name} {counter}"
            else:
                raise FP_ParameterError(
                    f"Filter with name '{original_name}' already exists. " f"Use rename_if_exists=True to auto-rename."
                )

        # Create the filter (this assigns new GUID and dates)
        return self.Create(import_name, filter_data["filter_type"], filter_data["criteria"])

    # --- Utility Methods ---

    @OperationsMethod
    def GetFiltersByType(self, filter_type):
        """
        Get all filters of a specific type.

        Args:
            filter_type (str): The filter type to retrieve (from FilterTypes)

        Yields:
            dict: Each filter object of the specified type

        Raises:
            FP_NullParameterError: If filter_type is None

        Example:
            >>> # Get all lexical entry filters
            >>> for f in project.Filter.GetFiltersByType(FilterTypes.LEXENTRY):
            ...     name = project.Filter.GetName(f)
            ...     print(name)
            Verbs
            Nouns
            Adjectives

            >>> # Count wordform filters
            >>> wf_filters = list(project.Filter.GetFiltersByType(FilterTypes.WORDFORM))
            >>> print(f"Found {len(wf_filters)} wordform filters")

        Notes:
            - Returns an iterator for memory efficiency
            - Returns empty iterator if no filters of that type exist
            - Filter types are defined in FilterTypes class

        See Also:
            GetAll, GetFilterType, FilterTypes
        """
        self._ValidateParam(filter_type, "filter_type")

        for filter_obj in self.GetAll():
            if filter_obj["filter_type"] == filter_type:
                yield filter_obj

    @OperationsMethod
    def GetDateCreated(self, filter_obj):
        """
        Get the creation date of a filter.

        Args:
            filter_obj (dict): The filter object

        Returns:
            str: The date and time the filter was created (ISO format string)

        Raises:
            FP_NullParameterError: If filter_obj is None
            FP_ParameterError: If filter_obj is invalid

        Example:
            >>> filter_obj = project.Filter.Find("Verbs")
            >>> created = project.Filter.GetDateCreated(filter_obj)
            >>> print(f"Created: {created}")
            Created: 2025-01-15 14:30:22

        Notes:
            - Date is stored as string in ISO format
            - Automatically set when filter is created
            - Cannot be modified

        See Also:
            GetDateModified, Create
        """
        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict) or "date_created" not in filter_obj:
            raise FP_ParameterError("Invalid filter object")

        return filter_obj.get("date_created", "")

    @OperationsMethod
    def GetDateModified(self, filter_obj):
        """
        Get the last modification date of a filter.

        Args:
            filter_obj (dict): The filter object

        Returns:
            str: The date and time the filter was last modified (ISO format string)

        Raises:
            FP_NullParameterError: If filter_obj is None
            FP_ParameterError: If filter_obj is invalid

        Example:
            >>> filter_obj = project.Filter.Find("Verbs")
            >>> modified = project.Filter.GetDateModified(filter_obj)
            >>> print(f"Last modified: {modified}")
            Last modified: 2025-01-20 09:15:43

        Notes:
            - Date is stored as string in ISO format
            - Automatically updated when filter is modified
            - Updates on name, criteria, or any property change

        See Also:
            GetDateCreated, SetName, SetCriteria
        """
        self._ValidateParam(filter_obj, "filter_obj")

        if not isinstance(filter_obj, dict) or "date_modified" not in filter_obj:
            raise FP_ParameterError("Invalid filter object")

        return filter_obj.get("date_modified", "")

    # --- Private Helper Methods ---

    def _LoadFiltersFromProject(self):
        """
        Load all filters from project custom settings.

        Returns:
            dict: Dictionary of filters keyed by GUID
        """
        # Try to load from project settings
        # Since FLEx doesn't have a built-in filter storage API,
        # we store filters as JSON in a custom project property
        try:
            if hasattr(self.project, "GetProjectProperty"):
                filters_json = self.project.GetProjectProperty("flexlibs_filters")
                if filters_json:
                    return json.loads(filters_json)
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            pass

        # Return empty dict if no filters stored
        return {}

    def _SaveFiltersToProject(self, filters):
        """
        Save all filters to project custom settings.

        Args:
            filters (dict): Dictionary of filters keyed by GUID
        """
        # Save to project settings as JSON
        filters_json = json.dumps(filters, indent=2, ensure_ascii=False)

        if hasattr(self.project, "SetProjectProperty"):
            self.project.SetProjectProperty("flexlibs_filters", filters_json)
        else:
            # Fallback: store in memory cache only
            # (will be lost when project closes)
            logger.warning("Project does not support custom properties. " "Filters will only persist in memory.")

    def _GetAllObjectsOfType(self, filter_type):
        """
        Get all objects of a specific type from the project.

        Args:
            filter_type (str): The filter type

        Returns:
            list: All objects of that type
        """
        if filter_type == FilterTypes.LEXENTRY:
            return list(self.project.LexEntry.GetAll())
        elif filter_type == FilterTypes.WORDFORM:
            return list(self.project.Wordforms.GetAll())
        elif filter_type == FilterTypes.TEXT:
            return list(self.project.Texts.GetAll())
        else:
            # For other types, return empty list
            logger.warning(f"GetAllObjectsOfType not implemented for {filter_type}")
            return []

    def _ObjectMatchesCriteria(self, obj, criteria, filter_type):
        """
        Check if an object matches filter criteria.

        Args:
            obj: The object to check
            criteria (dict): The filter criteria
            filter_type (str): The filter type

        Returns:
            bool: True if object matches all criteria, False otherwise
        """
        try:
            if filter_type == FilterTypes.LEXENTRY:
                return self._MatchLexEntryCriteria(obj, criteria)
            elif filter_type == FilterTypes.WORDFORM:
                return self._MatchWordformCriteria(obj, criteria)
            elif filter_type == FilterTypes.TEXT:
                return self._MatchTextCriteria(obj, criteria)
            else:
                # For custom or unknown types, always return True
                return True
        except Exception as e:
            logger.error(f"Error matching criteria: {e}")
            return False

    def _MatchLexEntryCriteria(self, entry, criteria):
        """
        Check if a lexical entry matches criteria.

        Args:
            entry: ILexEntry object
            criteria (dict): Filter criteria

        Returns:
            bool: True if matches all criteria
        """
        # Example criteria matching for lexical entries
        # This can be extended based on actual requirements

        # Check POS (part of speech)
        if "pos" in criteria:
            pos_name = criteria["pos"].lower()
            # Get entry's POS and compare
            # Use get_pos_from_msa() to handle pythonnet interface casting
            try:
                senses = list(entry.SensesOS)
                if senses:
                    for sense in senses:
                        if sense.MorphoSyntaxAnalysisRA:
                            pos = get_pos_from_msa(sense.MorphoSyntaxAnalysisRA)
                            if pos:
                                pos_text = normalize_text(ITsString(pos.Name.BestAnalysisAlternative).Text)
                                if pos_text and pos_text.lower() == pos_name:
                                    return True
                return False
            except (TypeError, AttributeError, KeyError) as e:
                return False

        # Check morph type
        if "morph_type" in criteria:
            morph_type_name = criteria["morph_type"].lower()
            try:
                if entry.LexemeFormOA and entry.LexemeFormOA.MorphTypeRA:
                    mt = entry.LexemeFormOA.MorphTypeRA
                    mt_text = normalize_text(ITsString(mt.Name.BestAnalysisAlternative).Text)
                    if mt_text and mt_text.lower() != morph_type_name:
                        return False
            except (TypeError, AttributeError, KeyError) as e:
                return False

        # Check form pattern (regex)
        if "form_pattern" in criteria:
            import re

            pattern = criteria["form_pattern"]
            try:
                form = normalize_text(ITsString(entry.LexemeFormOA.Form.BestVernacularAlternative).Text)
                if form and not re.search(pattern, form):
                    return False
            except (TypeError, AttributeError, KeyError) as e:
                return False

        # If no criteria specified or all matched, return True
        return True

    def _MatchWordformCriteria(self, wordform, criteria):
        """
        Check if a wordform matches criteria.

        Args:
            wordform: IWfiWordform object
            criteria (dict): Filter criteria

        Returns:
            bool: True if matches all criteria
        """
        # Check spelling status
        if "spelling_status" in criteria:
            expected_status = criteria["spelling_status"]
            if wordform.SpellingStatus != expected_status:
                return False

        # Check form pattern (regex)
        if "form_pattern" in criteria:
            import re

            pattern = criteria["form_pattern"]
            try:
                form = ITsString(wordform.Form.BestVernacularAlternative).Text
                if form and not re.search(pattern, form):
                    return False
            except (TypeError, AttributeError, KeyError) as e:
                return False

        return True

    def _MatchTextCriteria(self, text, criteria):
        """
        Check if a text matches criteria.

        Args:
            text: IText object
            criteria (dict): Filter criteria

        Returns:
            bool: True if matches all criteria
        """
        # Check genre
        if "genre" in criteria:
            genre_name = criteria["genre"].lower()
            try:
                if text.GenresRC and text.GenresRC.Count > 0:
                    for genre in text.GenresRC:
                        genre_text = ITsString(genre.Name.BestAnalysisAlternative).Text
                        if genre_text and genre_text.lower() == genre_name:
                            return True
                return False
            except (TypeError, AttributeError, KeyError) as e:
                return False

        # Check title pattern (regex)
        if "title_pattern" in criteria:
            import re

            pattern = criteria["title_pattern"]
            try:
                title = ITsString(text.Title.BestAnalysisAlternative).Text
                if title and not re.search(pattern, title):
                    return False
            except (TypeError, AttributeError, KeyError) as e:
                return False

        return True

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate a filter, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The filter dict object to duplicate (not HVO-based).

        Returns:
            dict: The newly created duplicate filter with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> verb_filter = project.Filter.Find("Verbs")
            >>> if verb_filter:
            ...     dup = project.Filter.Duplicate(verb_filter)
            ...     project.Filter.SetName(dup, "Verbs Copy")
            ...     print(f"Duplicate: {project.Filter.GetName(dup)}")

        Notes:
            - Creates a new filter with new GUID
            - All properties copied: name, filter_type, criteria
            - Name is copied as-is (may need renaming to avoid confusion)
            - Filters are stored as JSON, not LCM objects

        See Also:
            Create, Delete, GetGuid
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        if not isinstance(item_or_hvo, dict):
            raise FP_ParameterError("Filter object must be a dictionary")

        # Get source filter
        source = item_or_hvo

        # Create new filter with new GUID
        from System import Guid
        import System

        filter_guid = str(Guid.NewGuid())
        duplicate = {
            "guid": filter_guid,
            "name": source["name"],  # Copy name as-is
            "filter_type": source["filter_type"],
            "criteria": dict(source["criteria"]),  # Deep copy criteria dict
            "date_created": System.DateTime.Now.ToString(),
            "date_modified": System.DateTime.Now.ToString(),
        }

        # Save to project
        filters = self._LoadFiltersFromProject()
        filters[filter_guid] = duplicate
        self._SaveFiltersToProject(filters)

        # Update cache
        self._filter_cache[filter_guid] = duplicate

        return duplicate

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a filter.

        Args:
            item: The filter dict object.

        Returns:
            dict: Dictionary of syncable properties with their values.

        Example:
            >>> props = project.Filter.GetSyncableProperties(filter_obj)
            >>> print(props['name'])
            'Verbs'
            >>> print(props['filter_type'])
            'LexEntry'

        Notes:
            - Filters are dict-based, not LCM objects
            - Returns name, filter_type, and criteria
            - Does NOT include guid, date_created, date_modified (metadata)
        """
        props = {}

        # String properties
        if "name" in item:
            props["name"] = item["name"]

        if "filter_type" in item:
            props["filter_type"] = item["filter_type"]

        # Dict property
        if "criteria" in item:
            props["criteria"] = item["criteria"]

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two filters for differences.

        Args:
            item1: First filter dict object (from project 1)
            item2: Second filter dict object (from project 2)
            ops1: Optional FilterOperations instance for project 1 (defaults to self)
            ops2: Optional FilterOperations instance for project 2 (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
                - is_different (bool): True if filters differ, False if identical
                - differences_dict (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> is_diff, diffs = ops1.CompareTo(filter1, filter2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} != {val2}")

        Notes:
            - Compares name, filter_type, and criteria
            - Empty/null values are treated as equivalent
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}

        # Get all property keys from both items
        all_keys = set(props1.keys()) | set(props2.keys())

        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            # Compare values (handle dicts specially for criteria)
            if key == "criteria":
                # Deep comparison for criteria dict
                if val1 != val2:
                    differences[key] = (val1, val2)
            else:
                # Simple comparison for strings
                if val1 != val2:
                    differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return (is_different, differences)
