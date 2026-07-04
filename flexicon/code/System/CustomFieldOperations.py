#
#   CustomFieldOperations.py
#
#   Class: CustomFieldOperations
#          Custom field management operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import System

# Import FLEx LCM types
from SIL.LCModel import (
    ICmObjectRepository,
    ICmPossibilityRepository,
    ILexEntry,
    ILexSense,
    ILexExampleSentence,
    IMoForm,
    LexEntryTags,
    LexSenseTags,
    LexExampleSentenceTags,
    MoFormTags,
)

from SIL.LCModel.Core.Cellar import (
    CellarPropertyType,
    CellarPropertyTypeFilter,
)

from SIL.LCModel.Infrastructure import (
    IFwMetaDataCacheManaged,
)

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
    FP_TransactionError,
)

# Import FLExLCM types
from .. import FLExLCM  # Fixed: was "from ." (wrong path)
from ..BaseOperations import BaseOperations, OperationsMethod
from ..Shared.string_utils import normalize_match_key


class CustomFieldOperations(BaseOperations):
    """
    This class provides operations for managing custom fields in a
    FieldWorks project.

    Custom fields extend the FLEx data model by allowing users to add
    additional fields to various object classes (entries, senses, examples,
    etc.). These fields can store strings, integers, dates, or references
    to lists/objects.

    Field Types:
        - String: Single-line text (one writing system)
        - MultiString: Multi-line text (multiple writing systems)
        - MultiUnicode: Unicode text (multiple writing systems)
        - Integer: Whole number (e.g., frequency counts)
        - GenDate: Date with flexible precision
        - ReferenceAtom: Single-select from predefined list (dropdown menu)
        - ReferenceCollection: Multi-select from predefined list (checkboxes)

    This class should be accessed via FLExProject.CustomFields property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all custom fields for entries
        entry_fields = project.CustomFields.GetAllFields("LexEntry")
        for field_id, label in entry_fields:
            print(f"Field: {label} (ID: {field_id})")

        # Create a new custom field
        field_id = project.CustomFields.CreateField(
            "LexEntry",
            "DialectVariant",
            "MultiString",
            "vernacular"
        )

        # Get and set field values
        entry = project.LexEntry.Find("run")
        project.CustomFields.SetValue(entry, "DialectVariant", "runnin'", "en")
        value = project.CustomFields.GetValue(entry, "DialectVariant", "en")
        print(value)  # "runnin'"

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize CustomFieldOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Field Definition Management ---

    @OperationsMethod
    def GetAllFields(self, owner_class):
        """
        Get all custom fields for a given class.

        Args:
            owner_class (str): The class name (e.g., "LexEntry", "LexSense",
                "LexExampleSentence", "MoForm")

        Returns:
            list: List of tuples (field_id, label) for each custom field

        Raises:
            FP_NullParameterError: If owner_class is None
            FP_ParameterError: If owner_class is invalid

        Example:
            >>> # Get all entry-level custom fields
            >>> fields = project.CustomFields.GetAllFields("LexEntry")
            >>> for field_id, label in fields:
            ...     print(f"{label}: {field_id}")
            Etymology Source: 5002
            Dialect: 5003

            >>> # Get all sense-level custom fields
            >>> sense_fields = project.CustomFields.GetAllFields("LexSense")

        Notes:
            - Returns empty list if no custom fields are defined
            - Field IDs are unique across the project
            - Labels are the display names shown in FLEx UI
            - Only returns custom fields, not built-in fields
            - Common classes: LexEntry, LexSense, LexExampleSentence, MoForm

        See Also:
            FindField, CreateField, GetFieldName
        """
        self._ValidateParam(owner_class, "owner_class")

        if not owner_class or not owner_class.strip():
            raise FP_ParameterError("Owner class cannot be empty")

        # Get the class ID
        class_id = self._GetClassID(owner_class)

        # Get custom fields from metadata cache
        mdc = IFwMetaDataCacheManaged(self.project.project.MetaDataCacheAccessor)

        custom_fields = []
        for flid in mdc.GetFields(class_id, False, int(CellarPropertyTypeFilter.All)):
            if self.project.project.GetIsCustomField(flid):
                label = mdc.GetFieldLabel(flid)
                custom_fields.append((flid, label))

        return custom_fields

    @OperationsMethod
    def CreateField(self, owner_class, name, field_type, ws_type=None):
        """
        Create a new custom field.

        Args:
            owner_class (str): The class name (e.g., "LexEntry", "LexSense")
            name (str): The field name/label
            field_type (str): Field type:
                - "String": Single-line text (one writing system)
                - "MultiString": Multi-line text (multiple writing systems)
                - "MultiUnicode": Unicode text (multiple writing systems)
                - "Integer": Whole number (e.g., frequency counts)
                - "GenDate": Date with flexible precision
                - "ReferenceAtom": Single-select from predefined list (dropdown menu)
                - "ReferenceCollection": Multi-select from predefined list (checkboxes)
            ws_type (str, optional): Writing system type for string fields -
                "vernacular", "analysis", or "all". Default is "analysis" for
                MultiString, None for String.

        Returns:
            int: The field ID of the newly created field

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If required parameters are None
            FP_ParameterError: If parameters are invalid or field already exists
            FP_TransactionError: If called while a UnitOfWork is open (always
                the case in Phase 1 transaction mode). See "Transaction Safety"
                below and docs/CUSTOM_FIELDS.md.

        Example:
            >>> # Create a vernacular multi-string field
            >>> field_id = project.CustomFields.CreateField(
            ...     "LexEntry",
            ...     "Dialect Variant",
            ...     "MultiString",
            ...     "vernacular"
            ... )

            >>> # Create an integer field
            >>> freq_field = project.CustomFields.CreateField(
            ...     "LexEntry",
            ...     "Frequency",
            ...     "Integer"
            ... )

            >>> # Create a reference to a possibility list
            >>> region_field = project.CustomFields.CreateField(
            ...     "LexSense",
            ...     "Region",
            ...     "ReferenceAtom"
            ... )

        Warning:
            - This operation modifies the project schema
            - Field creation is permanent and cannot be easily undone
            - Field names must be unique within a class
            - Use FLEx UI for complex field setup (lists, etc.)

        Transaction Safety:
            Custom field creation is a SCHEMA mutation and cannot run inside
            an open UnitOfWork. In Phase 1 transaction mode (the default),
            OpenProject() opens a non-undoable envelope that remains open
            until CloseProject(), so CreateField() will refuse with
            FP_TransactionError.

            Bypassing this guard with raw LCM (IFwMetaDataCacheManaged.
            AddCustomField) creates the field in memory only; subsequent
            SetValue calls appear to succeed but the schema does NOT persist,
            producing corrupted records on next FLEx UI open. See
            docs/CUSTOM_FIELDS.md for the recommended workflow.

        Notes:
            - MultiString supports multiple writing systems
            - String supports single writing system
            - Integer stores whole numbers
            - GenDate stores dates with various precision levels
            - ReferenceAtom stores single reference to possibility list
            - ReferenceCollection stores multiple references
            - Field appears in FLEx UI after creation
            - May require FLEx restart to fully integrate

        See Also:
            DeleteField, GetAllFields, FindField
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(owner_class, "owner_class")

        if not owner_class.strip() or not name.strip() or not field_type.strip():
            raise FP_ParameterError("Parameters cannot be empty")

        # Check if field already exists
        existing_field = self.FindField(owner_class, name)
        if existing_field is not None:
            raise FP_ParameterError(f"Custom field '{name}' already exists for {owner_class}")

        # Validate field type
        valid_types = [
            "String",
            "Integer",
            "GenDate",
            "MultiString",
            "MultiUnicode",
            "ReferenceAtom",
            "ReferenceCollection",
        ]
        if field_type not in valid_types:
            raise FP_ParameterError(f"Invalid field type '{field_type}'. " f"Valid types: {', '.join(valid_types)}")

        # Refuse if an open UnitOfWork would make the schema mutation
        # unsafe. In Phase 1 mode (the default), OpenProject() opens a
        # non-undoable envelope at BeginNonUndoableTask that remains open
        # until CloseProject(), so this check effectively always fires.
        #
        # The LCM contract forbids schema mutation inside a data UoW
        # (AddCustomField + an active task -> InvalidOperationException at
        # UndoStack.CheckNotProcessingDataChanges). Bypassing the wrapper
        # with raw IFwMetaDataCacheManaged.AddCustomField creates the field
        # in memory only; SetValue calls then write data referencing a
        # ghost field that never persists, producing project corruption on
        # next FLEx UI open (issue #21).
        #
        # Until Phase 2 transaction mode lands and a safe schema-mutation
        # path is characterized, the correct workflow is:
        #   1. Create custom fields via FLEx UI (Tools > Configure > Custom Fields)
        #   2. Then run bootstrap scripts that populate values via SetValue
        # See docs/CUSTOM_FIELDS.md.
        action_handler = self.project.project.ActionHandlerAccessor
        if getattr(action_handler, "CurrentDepth", 0) > 0:
            raise FP_TransactionError(
                "CreateField cannot run inside an open UnitOfWork. "
                "Custom field creation is a schema mutation that LCM forbids "
                "inside an active task (raises InvalidOperationException at "
                "UndoStack.CheckNotProcessingDataChanges). In Phase 1 transaction "
                "mode this UoW is opened at OpenProject() and stays open until "
                "CloseProject(), so schema mutations are not possible via the "
                "wrapper. "
                "Fix: create custom fields through the FLEx UI "
                "(Tools > Configure > Custom Fields) before running bootstrap "
                "scripts that populate values. "
                "Do NOT bypass this guard with raw "
                "IFwMetaDataCacheManaged.AddCustomField: the field is created "
                "in memory only, SetValue writes data referencing a ghost field, "
                "and the project corrupts on next FLEx UI open (issue #21). "
                "See docs/CUSTOM_FIELDS.md."
            )

        # Unreachable in Phase 1 mode; placeholder for Phase 2 work.
        raise FP_TransactionError(
            "CreateField is not yet implemented for the no-UoW path. "
            "Pending Phase 2 transaction mode (see FLExProject.UndoableOperation). "
            "Until then, create custom fields through the FLEx UI: "
            "Tools > Configure > Custom Fields. See docs/CUSTOM_FIELDS.md."
        )

    @OperationsMethod
    def DeleteField(self, field_id):
        """
        Delete a custom field from the project.

        Args:
            field_id (int): The field ID to delete

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If field_id is None
            FP_ParameterError: If field_id is invalid or is not a custom field

        Example:
            >>> field_id = project.CustomFields.FindField("LexEntry", "OldField")
            >>> if field_id:
            ...     project.CustomFields.DeleteField(field_id)

        Warning:
            - This is a destructive operation
            - All data stored in this field will be lost
            - Cannot be undone
            - Field deletion affects all objects in the project
            - Use FLEx UI for safe field management

        Notes:
            - Only custom fields can be deleted (not built-in fields)
            - Field is removed from project schema
            - Data stored in field is permanently deleted
            - Recommended to use FLEx UI: Tools > Configure > Custom Fields

        See Also:
            CreateField, GetAllFields
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(field_id, "field_id")

        # Verify it's a custom field
        if not self.project.project.GetIsCustomField(field_id):
            raise FP_ParameterError("Field ID does not refer to a custom field")

        # Note: Actual deletion of custom fields through LCM API is complex
        # and should be done through FLEx UI for safety
        raise NotImplementedError(
            "Custom field deletion must be done through FLEx UI: " "Tools > Configure > Custom Fields"
        )

    @OperationsMethod
    def FindField(self, owner_class, name):
        """
        Find a custom field by owner class and name.

        Args:
            owner_class (str): The class name (e.g., "LexEntry", "LexSense")
            name (str): The field name/label to search for (case-sensitive)

        Returns:
            int or None: The field ID if found, None otherwise

        Raises:
            FP_NullParameterError: If owner_class or name is None
            FP_ParameterError: If owner_class is invalid

        Example:
            >>> # Find entry-level custom field
            >>> field_id = project.CustomFields.FindField("LexEntry", "Etymology Source")
            >>> if field_id:
            ...     print(f"Found field: {field_id}")
            ... else:
            ...     print("Field not found")

            >>> # Find sense-level custom field
            >>> domain_field = project.CustomFields.FindField("LexSense", "Semantic Domain Notes")

        Notes:
            - Search is case-sensitive
            - Returns None if field doesn't exist (doesn't raise exception)
            - Only searches custom fields, not built-in fields
            - Field name must match exactly (including spaces, punctuation)
            - Use GetAllFields() to see all available field names

        See Also:
            GetAllFields, GetFieldName
        """
        self._ValidateParam(owner_class, "owner_class")

        if not owner_class.strip() or not name.strip():
            return None

        # Get all custom fields and search by name. NFD-normalize both
        # sides: FLEx stores Unicode in NFD, Python source is typically
        # NFC; a user looking up "Etymologie Detaillee" with NFC e-acute
        # would silently miss against NFD-stored data. (issue #125)
        target = normalize_match_key(name, casefold=False)
        fields = self.GetAllFields(owner_class)
        for field_id, label in fields:
            if normalize_match_key(label, casefold=False) == target:
                return field_id

        return None

    @OperationsMethod
    def GetFieldType(self, field_id):
        """
        Get the data type of a custom field.

        Args:
            field_id (int): The field ID

        Returns:
            CellarPropertyType: The field type enumeration value

        Raises:
            FP_NullParameterError: If field_id is None
            FP_ParameterError: If field_id is invalid

        Example:
            >>> field_id = project.CustomFields.FindField("LexEntry", "Frequency")
            >>> field_type = project.CustomFields.GetFieldType(field_id)
            >>> if field_type == CellarPropertyType.Integer:
            ...     print("This is an integer field")

            >>> # Check if field is multi-string type
            >>> if project.CustomFields.IsMultiString(field_id):
            ...     print("This field supports multiple writing systems")

        Notes:
            - Returns CellarPropertyType enumeration value
            - Common types: String, MultiString, MultiUnicode, Integer,
              GenDate, ReferenceAtom, ReferenceCollection
            - Use IsMultiString(), IsListType() helper methods for checks
            - Field type cannot be changed after creation

        See Also:
            IsMultiString, IsListType, GetFieldName
        """
        self._ValidateParam(field_id, "field_id")

        mdc = IFwMetaDataCacheManaged(self.project.project.MetaDataCacheAccessor)

        try:
            field_type = CellarPropertyType(mdc.GetFieldType(field_id))
            return field_type
        except (AttributeError, KeyError, ValueError, System.Exception):
            raise FP_ParameterError("Invalid field ID")

    @OperationsMethod
    def GetFieldName(self, field_id):
        """
        Get the name/label of a custom field.

        Args:
            field_id (int): The field ID

        Returns:
            str: The field name/label

        Raises:
            FP_NullParameterError: If field_id is None
            FP_ParameterError: If field_id is invalid

        Example:
            >>> field_id = 5002
            >>> name = project.CustomFields.GetFieldName(field_id)
            >>> print(name)
            Etymology Source

        Notes:
            - Returns the display label shown in FLEx UI
            - Name is user-defined when field is created
            - Returns empty string if field has no label (rare)

        See Also:
            SetFieldName, FindField, GetAllFields
        """
        self._ValidateParam(field_id, "field_id")

        mdc = IFwMetaDataCacheManaged(self.project.project.MetaDataCacheAccessor)

        try:
            return mdc.GetFieldLabel(field_id) or ""
        except (AttributeError, KeyError, ValueError, System.Exception):
            raise FP_ParameterError("Invalid field ID")

    @OperationsMethod
    def SetFieldName(self, field_id, name):
        """
        Set/rename the label of a custom field.

        Args:
            field_id (int): The field ID
            name (str): The new field name/label

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If field_id or name is None
            FP_ParameterError: If field_id is invalid or name is empty

        Example:
            >>> field_id = project.CustomFields.FindField("LexEntry", "OldName")
            >>> if field_id:
            ...     project.CustomFields.SetFieldName(field_id, "NewName")

        Warning:
            - Renaming fields may affect exports and scripts
            - Other users/systems may reference fields by name
            - Consider backward compatibility before renaming
            - Recommended to use FLEx UI for field management

        Notes:
            - Changes the display label in FLEx UI
            - Does not affect field ID (which remains constant)
            - Does not affect stored data
            - Name change is immediate
            - Should be unique within the class (not enforced)

        See Also:
            GetFieldName, FindField
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(field_id, "field_id")

        if not name.strip():
            raise FP_ParameterError("Field name cannot be empty")

        # Verify field exists
        try:
            self.GetFieldName(field_id)
        except (AttributeError, KeyError, ValueError, System.Exception):
            raise FP_ParameterError("Invalid field ID")

        # Note: Renaming custom fields through LCM API is not commonly supported
        raise NotImplementedError(
            "Custom field renaming must be done through FLEx UI: " "Tools > Configure > Custom Fields"
        )

    # --- Field Values (Generic) ---

    @OperationsMethod
    def GetValue(self, obj, field_name, ws=None):
        """
        Get the value of a custom field for an object.

        Args:
            obj: The object (ILexEntry, ILexSense, etc.) or HVO
            field_name (str): The custom field name
            ws (str or int, optional): Writing system (tag or handle) for
                multi-string fields. If None, returns best analysis/vernacular.

        Returns:
            Value depends on field type:
            - String/MultiString: str
            - Integer: int
            - ReferenceAtom: str (short name of referenced item)
            - ReferenceCollection: list of str

        Raises:
            FP_NullParameterError: If obj or field_name is None
            FP_ParameterError: If field not found or obj invalid

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> # Get string field value
            >>> etym = project.CustomFields.GetValue(entry, "Etymology Source")
            >>> print(etym)
            Latin currere

            >>> # Get multi-string field with specific WS
            >>> dialect = project.CustomFields.GetValue(entry, "Dialect", "en")
            >>> print(dialect)
            runnin'

            >>> # Get integer field
            >>> freq = project.CustomFields.GetValue(entry, "Frequency")
            >>> print(freq)
            42

            >>> # Get list field
            >>> regions = project.CustomFields.GetValue(sense, "Regions")
            >>> print(regions)
            ['North', 'East']

        Notes:
            - Returns empty string/0/[] if field is empty
            - For multi-string fields without ws specified, returns best alternative
            - For list fields (ReferenceCollection), returns list of short names
            - Field must exist for the object's class
            - Use GetFieldType() to determine expected return type

        See Also:
            SetValue, ClearValue, GetListValues
        """
        self._ValidateParam(obj, "obj")

        # Resolve object and get class name
        hvo = self._GetHvo(obj)
        obj = self.project.Object(hvo)
        class_name = obj.ClassName

        # Find the field
        field_id = self.FindField(class_name, field_name)
        if field_id is None:
            raise FP_ParameterError(f"Custom field '{field_name}' not found for {class_name}")

        # Get the value using existing FLExProject method
        ws_handle = None
        if ws is not None:
            ws_handle = self._GetWSHandle(ws)

        return self.project.GetCustomFieldValue(obj, field_id, ws_handle)

    @OperationsMethod
    def SetValue(self, obj, field_name, value, ws=None):
        """
        Set the value of a custom field for an object.

        Args:
            obj: The object (ILexEntry, ILexSense, etc.) or HVO
            field_name (str): The custom field name
            value: The value to set (type depends on field type)
            ws (str or int, optional): Writing system (tag or handle) for
                multi-string fields. Defaults to default analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If obj or field_name is None
            FP_ParameterError: If field not found, obj invalid, or value
                type doesn't match field type

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> # Set string field
            >>> project.CustomFields.SetValue(entry, "Etymology Source",
            ...                                "Latin currere")

            >>> # Set multi-string field with specific WS
            >>> project.CustomFields.SetValue(entry, "Dialect", "runnin'", "en")

            >>> # Set integer field
            >>> project.CustomFields.SetValue(entry, "Frequency", 42)

            >>> # For list fields, use SetListFieldSingle/Multiple
            >>> # or AddListValue/RemoveListValue

        Notes:
            - Value type must match field type (string, int, etc.)
            - For multi-string fields, ws parameter is required or uses default
            - For list fields (Reference types), use list-specific methods
            - Integer fields accept int values
            - String/MultiString fields accept str values
            - Overwrites existing value

        See Also:
            GetValue, ClearValue, AddListValue, SetListFieldSingle
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(obj, "obj")

        # Resolve object and get class name
        hvo = self._GetHvo(obj)
        obj = self.project.Object(hvo)
        class_name = obj.ClassName

        # Find the field
        field_id = self.FindField(class_name, field_name)
        if field_id is None:
            raise FP_ParameterError(f"Custom field '{field_name}' not found for {class_name}")

        # Determine field type and use appropriate setter
        field_type = self.GetFieldType(field_id)

        if field_type == CellarPropertyType.Integer:
            # Integer field
            self._ValidateParam(value, "value")
            if not isinstance(value, int):
                raise FP_ParameterError("Value must be an integer")
            self.project.LexiconSetFieldInteger(obj, field_id, value)

        elif field_type in FLExLCM.CellarAllStringTypes:
            # String or MultiString field
            if not isinstance(value, str):
                raise FP_ParameterError("Value must be a string")
            ws_handle = None
            if ws is not None:
                ws_handle = self._GetWSHandle(ws)
            self.project.LexiconSetFieldText(obj, field_id, value, ws_handle)

        else:
            raise FP_ParameterError(
                "SetValue only supports String, MultiString, and Integer fields. "
                "For list fields, use AddListValue or SetListFieldSingle/Multiple."
            )

    @OperationsMethod
    def ClearValue(self, obj, field_name, ws=None):
        """
        Clear the value of a custom field for an object.

        Args:
            obj: The object (ILexEntry, ILexSense, etc.) or HVO
            field_name (str): The custom field name
            ws (str or int, optional): Writing system for multi-string fields.
                If None, clears all writing systems.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If obj or field_name is None
            FP_ParameterError: If field not found or obj invalid

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> # Clear a field value
            >>> project.CustomFields.ClearValue(entry, "Etymology Source")

            >>> # Clear specific writing system in multi-string field
            >>> project.CustomFields.ClearValue(entry, "Dialect", "en")

        Notes:
            - For multi-string fields without ws, clears all writing systems
            - For single-string fields, ws parameter is ignored
            - Sets field to empty/null value
            - For integer fields, sets to 0
            - For list fields, removes all references

        See Also:
            SetValue, GetValue
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(obj, "obj")

        # Resolve object and get class name
        hvo = self._GetHvo(obj)
        obj = self.project.Object(hvo)
        class_name = obj.ClassName

        # Find the field
        field_id = self.FindField(class_name, field_name)
        if field_id is None:
            raise FP_ParameterError(f"Custom field '{field_name}' not found for {class_name}")

        # Get field type to determine how to clear
        mdc = IFwMetaDataCacheManaged(self.project.project.MetaDataCacheAccessor)
        field_type = CellarPropertyType(mdc.GetFieldType(field_id))

        # Handle multi-string fields with specific writing system
        if field_type in FLExLCM.CellarMultiStringTypes and ws is not None:
            # Clear only the specified writing system
            wsHandle = self.project.WSHandle(ws)
            mua = self.project.project.DomainDataByFlid.get_MultiStringProp(hvo, field_id)
            mua.set_String(wsHandle, None)
        else:
            # Clear all writing systems (or single-value field)
            self.project.LexiconClearField(obj, field_id)

    # --- List Field Operations ---

    @OperationsMethod
    def GetListValues(self, obj, field_name):
        """
        Get list values from a ReferenceCollection custom field.

        Args:
            obj: The object (ILexEntry, ILexSense, etc.) or HVO
            field_name (str): The custom field name (must be ReferenceCollection type)

        Returns:
            list: List of short names (str) of referenced items

        Raises:
            FP_NullParameterError: If obj or field_name is None
            FP_ParameterError: If field not found, obj invalid, or field
                is not a ReferenceCollection type

        Example:
            >>> sense = entry.SensesOS[0]
            >>> # Get list of regions
            >>> regions = project.CustomFields.GetListValues(sense, "Regions")
            >>> print(regions)
            ['North', 'East', 'West']

            >>> # Check if list is empty
            >>> if not project.CustomFields.GetListValues(entry, "Tags"):
            ...     print("No tags assigned")

        Notes:
            - Only works with ReferenceCollection fields (multi-select lists)
            - Returns empty list if no items are selected
            - Returns short names, not full possibility objects
            - For ReferenceAtom (single-select), use GetValue() instead
            - Order is preserved as stored in database

        See Also:
            AddListValue, RemoveListValue, GetValue
        """
        self._ValidateParam(obj, "obj")

        # Resolve object and get class name
        hvo = self._GetHvo(obj)
        obj = self.project.Object(hvo)
        class_name = obj.ClassName

        # Find the field
        field_id = self.FindField(class_name, field_name)
        if field_id is None:
            raise FP_ParameterError(f"Custom field '{field_name}' not found for {class_name}")

        # Verify it's a ReferenceCollection field
        field_type = self.GetFieldType(field_id)
        if field_type != CellarPropertyType.ReferenceCollection:
            raise FP_ParameterError(f"Field '{field_name}' is not a ReferenceCollection type")

        # Get the values
        result = self.project.GetCustomFieldValue(obj, field_id, None)
        if isinstance(result, list):
            return result
        return []

    @OperationsMethod
    def AddListValue(self, obj, field_name, value):
        """
        Add a value to a ReferenceCollection custom field.

        Args:
            obj: The object (ILexEntry, ILexSense, etc.) or HVO
            field_name (str): The custom field name (must be ReferenceCollection type)
            value (str): The value to add (short name or full name of possibility)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If obj, field_name, or value is None
            FP_ParameterError: If field not found, obj invalid, field is not
                ReferenceCollection type, or value not found in possibility list

        Example:
            >>> sense = entry.SensesOS[0]
            >>> # Add a region
            >>> project.CustomFields.AddListValue(sense, "Regions", "North")

            >>> # Add multiple values
            >>> for region in ["East", "West"]:
            ...     project.CustomFields.AddListValue(sense, "Regions", region)

        Notes:
            - Only works with ReferenceCollection fields (multi-select lists)
            - Value must exist in the field's possibility list
            - If value already exists, it's not added again (no duplicates)
            - Value is case-sensitive
            - For single-select lists (ReferenceAtom), use SetValue() instead

        See Also:
            RemoveListValue, GetListValues, SetListFieldMultiple
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(obj, "obj")

        # Resolve object and get class name
        hvo = self._GetHvo(obj)
        obj = self.project.Object(hvo)
        class_name = obj.ClassName

        # Find the field
        field_id = self.FindField(class_name, field_name)
        if field_id is None:
            raise FP_ParameterError(f"Custom field '{field_name}' not found for {class_name}")

        # Verify it's a ReferenceCollection field
        field_type = self.GetFieldType(field_id)
        if field_type != CellarPropertyType.ReferenceCollection:
            raise FP_ParameterError(f"Field '{field_name}' is not a ReferenceCollection type")

        # Get current values and add new one
        current_values = self.GetListValues(obj, field_name)
        if value not in current_values:
            current_values.append(value)
            # Set the updated list
            self.project.LexiconSetListFieldMultiple(obj, field_id, current_values)

    @OperationsMethod
    def RemoveListValue(self, obj, field_name, value):
        """
        Remove a value from a ReferenceCollection custom field.

        Args:
            obj: The object (ILexEntry, ILexSense, etc.) or HVO
            field_name (str): The custom field name (must be ReferenceCollection type)
            value (str): The value to remove (short name or full name of possibility)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If obj, field_name, or value is None
            FP_ParameterError: If field not found, obj invalid, or field is not
                ReferenceCollection type

        Example:
            >>> sense = entry.SensesOS[0]
            >>> # Remove a region
            >>> project.CustomFields.RemoveListValue(sense, "Regions", "North")

            >>> # Remove all values
            >>> for region in project.CustomFields.GetListValues(sense, "Regions"):
            ...     project.CustomFields.RemoveListValue(sense, "Regions", region)

        Notes:
            - Only works with ReferenceCollection fields (multi-select lists)
            - If value doesn't exist, operation succeeds silently (no error)
            - Value is case-sensitive
            - After removing all values, list is empty (not deleted)

        See Also:
            AddListValue, GetListValues, ClearValue
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(obj, "obj")

        # Resolve object and get class name
        hvo = self._GetHvo(obj)
        obj = self.project.Object(hvo)
        class_name = obj.ClassName

        # Find the field
        field_id = self.FindField(class_name, field_name)
        if field_id is None:
            raise FP_ParameterError(f"Custom field '{field_name}' not found for {class_name}")

        # Verify it's a ReferenceCollection field
        field_type = self.GetFieldType(field_id)
        if field_type != CellarPropertyType.ReferenceCollection:
            raise FP_ParameterError(f"Field '{field_name}' is not a ReferenceCollection type")

        # Get current values and remove the specified one
        current_values = self.GetListValues(obj, field_name)
        if value in current_values:
            current_values.remove(value)
            # Set the updated list
            if current_values:
                self.project.LexiconSetListFieldMultiple(obj, field_id, current_values)
            else:
                # Clear the field if no values remain
                self.project.LexiconClearField(obj, field_id)

    # --- Utility Methods ---

    @OperationsMethod
    def GetOwnerClass(self, field_id):
        """
        Get the owner class name for a custom field.

        Args:
            field_id (int): The field ID

        Returns:
            str: The class name (e.g., "LexEntry", "LexSense")

        Raises:
            FP_NullParameterError: If field_id is None
            FP_ParameterError: If field_id is invalid

        Example:
            >>> field_id = 5002
            >>> class_name = project.CustomFields.GetOwnerClass(field_id)
            >>> print(class_name)
            LexEntry

            >>> # Use to determine which objects can use this field
            >>> owner = project.CustomFields.GetOwnerClass(field_id)
            >>> if owner == "LexSense":
            ...     print("This field is for senses")

        Notes:
            - Returns the class that owns the field definition
            - Common classes: LexEntry, LexSense, LexExampleSentence, MoForm
            - Each field belongs to exactly one class
            - Class determines which objects can have this field

        See Also:
            GetAllFields, FindField
        """
        self._ValidateParam(field_id, "field_id")

        mdc = IFwMetaDataCacheManaged(self.project.project.MetaDataCacheAccessor)

        try:
            class_id = mdc.GetOwnClsId(field_id)
            return mdc.GetClassName(class_id)
        except (AttributeError, KeyError, ValueError, System.Exception):
            raise FP_ParameterError("Invalid field ID")

    @OperationsMethod
    def IsMultiString(self, field_id):
        """
        Check if a custom field is a multi-string type.

        Multi-string fields support multiple writing systems (e.g., entering
        the same field in English, French, Spanish).

        Args:
            field_id (int): The field ID

        Returns:
            bool: True if field is MultiString or MultiUnicode, False otherwise

        Raises:
            FP_NullParameterError: If field_id is None
            FP_ParameterError: If field_id is invalid

        Example:
            >>> field_id = project.CustomFields.FindField("LexEntry", "Dialect")
            >>> if project.CustomFields.IsMultiString(field_id):
            ...     # Need to specify writing system when getting/setting
            ...     value_en = project.CustomFields.GetValue(entry, "Dialect", "en")
            ...     value_fr = project.CustomFields.GetValue(entry, "Dialect", "fr")
            ... else:
            ...     # Single string, no WS needed
            ...     value = project.CustomFields.GetValue(entry, "Dialect")

        Notes:
            - MultiString and MultiUnicode both return True
            - Single String fields return False
            - Multi-string fields require WS parameter in GetValue/SetValue
            - Useful for determining API usage pattern

        See Also:
            IsListType, GetFieldType
        """
        self._ValidateParam(field_id, "field_id")

        field_type = self.GetFieldType(field_id)
        return field_type in FLExLCM.CellarMultiStringTypes

    @OperationsMethod
    def IsListType(self, field_id):
        """
        Check if a custom field is a list (reference) type.

        List fields reference possibility lists (e.g., selecting from
        predefined options like regions, tags, categories).

        Args:
            field_id (int): The field ID

        Returns:
            bool: True if field is ReferenceAtom or ReferenceCollection,
                False otherwise

        Raises:
            FP_NullParameterError: If field_id is None
            FP_ParameterError: If field_id is invalid

        Example:
            >>> field_id = project.CustomFields.FindField("LexSense", "Region")
            >>> if project.CustomFields.IsListType(field_id):
            ...     # Use list-specific methods
            ...     values = project.CustomFields.GetListValues(sense, "Region")
            ...     project.CustomFields.AddListValue(sense, "Region", "North")
            ... else:
            ...     # Use regular GetValue/SetValue
            ...     value = project.CustomFields.GetValue(sense, "Region")

            >>> # Check if multi-select list
            >>> field_type = project.CustomFields.GetFieldType(field_id)
            >>> if field_type == CellarPropertyType.ReferenceCollection:
            ...     print("Multi-select list")
            ... elif field_type == CellarPropertyType.ReferenceAtom:
            ...     print("Single-select list")

        Notes:
            - ReferenceAtom = single-select list (radio buttons)
            - ReferenceCollection = multi-select list (checkboxes)
            - Both return True for this method
            - List fields reference possibility lists defined in project
            - Use GetListValues/AddListValue for ReferenceCollection
            - Use GetValue/SetValue for ReferenceAtom

        See Also:
            IsMultiString, GetFieldType, GetListValues, AddListValue
        """
        self._ValidateParam(field_id, "field_id")

        field_type = self.GetFieldType(field_id)
        return field_type in (CellarPropertyType.ReferenceAtom, CellarPropertyType.ReferenceCollection)

    @OperationsMethod
    def IsStringType(self, field_id):
        """
        Check if a custom field is a string type.

        String fields store text data (single or multiple writing systems).

        Args:
            field_id (int): The field ID

        Returns:
            bool: True if field is String, MultiString, or MultiUnicode,
                False otherwise

        Raises:
            FP_NullParameterError: If field_id is None
            FP_ParameterError: If field_id is invalid

        Example:
            >>> field_id = project.CustomFields.FindField("LexEntry", "Etymology")
            >>> if project.CustomFields.IsStringType(field_id):
            ...     # Can use GetValue/SetValue with string
            ...     value = project.CustomFields.GetValue(entry, "Etymology")
            ...     project.CustomFields.SetValue(entry, "Etymology", "New value")
            ... else:
            ...     # Use type-specific methods (Integer, List, etc.)
            ...     pass

            >>> # Determine if it's single vs multi-string
            >>> if project.CustomFields.IsStringType(field_id):
            ...     if project.CustomFields.IsMultiString(field_id):
            ...         print("Multi-string field (multiple writing systems)")
            ...     else:
            ...         print("Single string field")

        Notes:
            - Returns True for String, MultiString, and MultiUnicode types
            - Returns False for Integer, GenDate, Reference types
            - String types can use GetValue/SetValue with str values
            - Use IsMultiString() to distinguish single vs multi-string
            - Useful for type checking before operations

        See Also:
            IsMultiString, IsListType, GetFieldType
        """
        self._ValidateParam(field_id, "field_id")

        field_type = self.GetFieldType(field_id)
        return field_type in FLExLCM.CellarAllStringTypes

    @OperationsMethod
    def ClearField(self, obj, field_name, ws=None):
        """
        Clear a custom field value for an object.

        This is an alias for ClearValue() provided for FlexTools compatibility.

        Args:
            obj: The object (ILexEntry, ILexSense, etc.) or HVO
            field_name (str): The custom field name
            ws (str or int, optional): Writing system for multi-string fields.
                If None, clears all writing systems.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If obj or field_name is None
            FP_ParameterError: If field not found or obj invalid

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> # Clear a field (FlexTools-style API)
            >>> project.CustomFields.ClearField(entry, "Etymology Source")

            >>> # This is equivalent to:
            >>> project.CustomFields.ClearValue(entry, "Etymology Source")

        Notes:
            - This is a convenience alias for ClearValue()
            - Provided for compatibility with FlexTools scripts
            - Both methods do exactly the same thing
            - For multi-string fields without ws, clears all writing systems
            - For integer fields, sets to 0
            - For list fields, removes all references

        See Also:
            ClearValue, SetValue, GetValue
        """
        return self.ClearValue(obj, field_name, ws)

    @OperationsMethod
    def SetListFieldSingle(self, obj, field_name, value):
        """
        Set the value of a ReferenceAtom (single-select list) custom field.

        Args:
            obj: The object (ILexEntry, ILexSense, etc.) or HVO
            field_name (str): The custom field name (must be ReferenceAtom type)
            value (str): The value to set (short name or full name of possibility)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If obj, field_name, or value is None
            FP_ParameterError: If field not found, obj invalid, field is not
                ReferenceAtom type, or value not found in possibility list

        Example:
            >>> sense = entry.SensesOS[0]
            >>> # Set a single-select field
            >>> project.CustomFields.SetListFieldSingle(sense, "Primary Region", "North")

            >>> # Change the value
            >>> project.CustomFields.SetListFieldSingle(sense, "Primary Region", "South")

        Notes:
            - Only works with ReferenceAtom fields (single-select lists)
            - Overwrites any existing value
            - Value must exist in the field's possibility list
            - Value is case-sensitive
            - For multi-select lists, use AddListValue/RemoveListValue

        See Also:
            SetListFieldMultiple, AddListValue, GetValue
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(obj, "obj")

        # Resolve object and get class name
        hvo = self._GetHvo(obj)
        obj = self.project.Object(hvo)
        class_name = obj.ClassName

        # Find the field
        field_id = self.FindField(class_name, field_name)
        if field_id is None:
            raise FP_ParameterError(f"Custom field '{field_name}' not found for {class_name}")

        # Verify it's a ReferenceAtom field
        field_type = self.GetFieldType(field_id)
        if field_type != CellarPropertyType.ReferenceAtom:
            raise FP_ParameterError(f"Field '{field_name}' is not a ReferenceAtom type")

        # Set the value
        self.project.LexiconSetListFieldSingle(obj, field_id, value)

    @OperationsMethod
    def SetListFieldMultiple(self, obj, field_name, values):
        """
        Set the values of a ReferenceCollection (multi-select list) custom field.

        Args:
            obj: The object (ILexEntry, ILexSense, etc.) or HVO
            field_name (str): The custom field name (must be ReferenceCollection type)
            values (list): List of values to set (short names or full names)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If obj, field_name, or values is None
            FP_ParameterError: If field not found, obj invalid, field is not
                ReferenceCollection type, or any value not found in possibility list

        Example:
            >>> sense = entry.SensesOS[0]
            >>> # Set multiple regions
            >>> project.CustomFields.SetListFieldMultiple(sense, "Regions",
            ...                                           ["North", "East", "West"])

            >>> # Clear all values by setting empty list
            >>> project.CustomFields.SetListFieldMultiple(sense, "Regions", [])

            >>> # Replace existing values
            >>> project.CustomFields.SetListFieldMultiple(sense, "Regions", ["South"])

        Notes:
            - Only works with ReferenceCollection fields (multi-select lists)
            - Replaces all existing values
            - Values must exist in the field's possibility list
            - Values are case-sensitive
            - Empty list clears the field
            - For adding/removing individual values, use AddListValue/RemoveListValue

        See Also:
            SetListFieldSingle, AddListValue, RemoveListValue, GetListValues
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(obj, "obj")

        # Resolve object and get class name
        hvo = self._GetHvo(obj)
        obj = self.project.Object(hvo)
        class_name = obj.ClassName

        # Find the field
        field_id = self.FindField(class_name, field_name)
        if field_id is None:
            raise FP_ParameterError(f"Custom field '{field_name}' not found for {class_name}")

        # Verify it's a ReferenceCollection field
        field_type = self.GetFieldType(field_id)
        if field_type != CellarPropertyType.ReferenceCollection:
            raise FP_ParameterError(f"Field '{field_name}' is not a ReferenceCollection type")

        # Set the values
        if not values:
            # Clear the field if empty list
            self.project.LexiconClearField(obj, field_id)
        else:
            self.project.LexiconSetListFieldMultiple(obj, field_id, values)

    # --- Private Helper Methods ---

    def _GetClassID(self, class_name):
        """
        Get the class ID for a class name.

        Args:
            class_name (str): The class name

        Returns:
            int: The class ID

        Raises:
            FP_ParameterError: If class name is invalid
        """
        # Map common class names to their kClassId constants
        class_map = {
            "LexEntry": LexEntryTags.kClassId,
            "LexSense": LexSenseTags.kClassId,
            "LexExampleSentence": LexExampleSentenceTags.kClassId,
            "MoForm": MoFormTags.kClassId,
        }

        if class_name in class_map:
            return class_map[class_name]

        # Try to get from metadata cache
        mdc = IFwMetaDataCacheManaged(self.project.project.MetaDataCacheAccessor)
        try:
            return mdc.GetClassId(class_name)
        except (AttributeError, KeyError, ValueError, System.Exception):
            raise FP_ParameterError(f"Invalid class name: {class_name}")

    def _GetHvo(self, obj):
        """
        Get HVO from object or HVO.

        Args:
            obj: Object or HVO (int)

        Returns:
            int: The HVO
        """
        if isinstance(obj, int):
            return obj
        try:
            return obj.Hvo
        except AttributeError:
            raise FP_ParameterError("Invalid object - must have Hvo attribute")

    def _GetWSHandle(self, ws):
        """
        Get writing system handle from tag or handle.

        Args:
            ws: Writing system tag (str) or handle (int)

        Returns:
            int: The writing system handle
        """
        if isinstance(ws, str):
            handle = self.project.WSHandle(ws)
            if not handle:
                raise FP_ParameterError(f"Invalid writing system: {ws}")
            return handle
        return ws

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate operation is not applicable for custom fields.

        Custom fields are metadata definitions at the project schema level and
        cannot be duplicated like data objects.

        Raises:
            NotImplementedError: Always raised - custom fields cannot be duplicated.

        Notes:
            - Use CreateField() to create a new custom field with similar properties
            - Custom fields are unique schema elements
            - Field duplication would require schema modification

        See Also:
            CreateField, DeleteField
        """
        raise NotImplementedError("Custom fields cannot be duplicated. Use CreateField() to create a new field.")

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get syncable properties - NOT IMPLEMENTED for custom fields.

        Custom fields are project schema definitions that cannot be safely synced
        between projects due to their structural nature.

        Raises:
            NotImplementedError: Custom fields are not syncable
        """
        raise NotImplementedError(
            "Custom fields cannot be synced between projects. "
            "Custom fields are schema definitions unique to each project."
        )

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare custom fields - NOT IMPLEMENTED.

        Custom fields are project schema definitions that cannot be safely synced
        between projects due to their structural nature.

        Raises:
            NotImplementedError: Custom fields are not syncable
        """
        raise NotImplementedError(
            "Custom fields cannot be compared for sync. " "Custom fields are schema definitions unique to each project."
        )
