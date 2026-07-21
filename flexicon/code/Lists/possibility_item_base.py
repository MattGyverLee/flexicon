#
#   possibility_item_base.py
#
#   Class: PossibilityItemOperations
#          Base class for operations on specialized possibility list items
#          (Publications, Confidence Levels, Translation Types, Agents, Overlays)
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import FLEx LCM types
from SIL.LCModel import ICmPossibilityFactory
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import FP_ParameterError, FP_NullParameterError
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key


class PossibilityItemOperations(BaseOperations):
    """
    Base class for operations on specialized possibility list items.

    Provides unified CRUD operations for possibility-based items like Publications,
    Confidence Levels, Translation Types, Agents, and Overlays. Each subclass
    specializes the base class by:

    1. Accessing the appropriate list object (e.g., ConfidenceLevelsOA)
    2. Specifying the item class name (e.g., 'Confidence', 'Publication')
    3. Providing domain-specific methods (e.g., GetPageWidth, IsVisible)

    Shared Operations (inherited by all subclasses):
    - GetAll() - Get all items (basic implementation, may be overridden)
    - Create() - Create new item with validation
    - Delete() - Delete item from list
    - Duplicate() - Clone item with new GUID
    - Find() - Find item by name
    - Exists() - Check if item exists by name
    - GetName() / SetName() - Get/set item name
    - GetDescription() / SetDescription() - Get/set item description
    - GetSyncableProperties() - Return dict of syncable properties
    - CompareTo() - Compare two items
    - GetGuid() - Get GUID

    Subclasses must implement:
    - __init__() - Call super().__init__(project)
    - _GetSequence() - Return parent.SubPossibilitiesOS (for reordering)
    - _get_item_class_name() - Return item class name string
    - _get_list_object() - Return the list container object

    Example subclass structure::

        class ConfidenceOperations(PossibilityItemOperations):
            def _get_item_class_name(self):
                return "Confidence"

            def _get_list_object(self):
                return self.project.lp.ConfidenceLevelsOA

            # Domain-specific methods
            def GetAnalysesWithConfidence(self, level):
                ...
    """

    def _GetSequence(self, parent):
        """Specify which sequence to reorder for item sub-possibilities.

        Returns:
            The SubPossibilitiesOS sequence for reordering operations.
        """
        return parent.SubPossibilitiesOS

    def _get_item_class_name(self):
        """Get the item class name for error messages and type checking.

        Must be overridden by subclass.

        Returns:
            str: Item class name (e.g., 'Confidence', 'Publication')
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _get_item_class_name()"
        )

    def _get_list_object(self):
        """Get the list container object for this item type.

        Must be overridden by subclass to return the appropriate list object
        (e.g., self.project.lp.ConfidenceLevelsOA).

        Returns:
            The ICmPossibilityList object containing items
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _get_list_object()"
        )

    # ========== SHARED HELPER METHODS ==========

    def __WSHandle(self, wsHandle):
        """Resolve writing system handle to default if None.

        Args:
            wsHandle: Writing system handle or None.

        Returns:
            int: Resolved writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return wsHandle

    def __ResolveObject(self, obj_or_hvo):
        """Resolve either an object or HVO to the object.

        Args:
            obj_or_hvo: Either an ICmPossibility object or its HVO (int).

        Returns:
            The resolved ICmPossibility object.

        Raises:
            FP_ParameterError: If HVO doesn't refer to valid object.
        """
        if isinstance(obj_or_hvo, int):
            obj = self.project.Object(obj_or_hvo)
            if obj is None:
                raise FP_ParameterError(
                    f"HVO {obj_or_hvo} does not refer to a valid {self._get_item_class_name()}"
                )
            return obj
        return obj_or_hvo

    # ========== CORE CRUD OPERATIONS ==========

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """Get all items in the list.

        Returns:
            list[ICmPossibility]: All items in the list.

        Notes:
            - Returns flat list of all items
            - Returns empty list if no items exist
            - Subclasses may override for specialized behavior
        """
        list_obj = self._get_list_object()
        if not list_obj:
            return []
        return list(list_obj.PossibilitiesOS)

    @OperationsMethod
    def Create(self, name, wsHandle=None):
        """Create a new item.

        Args:
            name (str): The name of the new item.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmPossibility: The newly created item object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty or list doesn't exist.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError(f"{self._get_item_class_name()} name cannot be empty")

        # Get the list object
        list_obj = self._get_list_object()
        if not list_obj:
            raise FP_ParameterError(
                f"{self._get_item_class_name()} list not found in project"
            )

        wsHandle = self.__WSHandle(wsHandle)

        # Create the new item using the factory
        factory = self.project.project.ServiceLocator.GetService(ICmPossibilityFactory)

        with self._TransactionCM(f"Create {self._get_item_class_name()} {name!r}"):
            new_item = factory.Create()

            # Add to list (must be done before setting properties)
            list_obj.PossibilitiesOS.Add(new_item)

            # Set name
            mkstr = TsStringUtils.MakeString(name, wsHandle)
            new_item.Name.set_String(wsHandle, mkstr)

            return new_item

    @OperationsMethod
    def Delete(self, item_or_hvo):
        """Delete an item from the list.

        Args:
            item_or_hvo: Either an ICmPossibility object or its HVO.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        item = self.__ResolveObject(item_or_hvo)

        # Remove from list
        list_obj = self._get_list_object()
        if list_obj and item in list_obj.PossibilitiesOS:
            list_obj.PossibilitiesOS.Remove(item)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """Duplicate an item, creating a new copy with a new GUID.

        Args:
            item_or_hvo: Either an ICmPossibility object or its HVO to duplicate.
            insert_after (bool): If True (default), insert after the source item.
                                If False, insert at end of list.

        Returns:
            ICmPossibility: The newly created duplicate item with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source item
        source = self.__ResolveObject(item_or_hvo)

        # Get the list object
        list_obj = self._get_list_object()
        if not list_obj:
            raise FP_ParameterError(
                f"{self._get_item_class_name()} list not found in project"
            )

        # Create new item using factory (auto-generates new GUID)
        factory = self.project.project.ServiceLocator.GetService(ICmPossibilityFactory)

        with self._TransactionCM(f"Duplicate {self._get_item_class_name()}"):
            duplicate = factory.Create()

            # ADD TO PARENT FIRST before copying properties (CRITICAL)
            if insert_after:
                # Insert after source item
                source_index = list_obj.PossibilitiesOS.IndexOf(source)
                list_obj.PossibilitiesOS.Insert(source_index + 1, duplicate)
            else:
                # Insert at end
                list_obj.PossibilitiesOS.Add(duplicate)

            # Copy MultiString properties using CopyAlternatives
            duplicate.Name.CopyAlternatives(source.Name)
            duplicate.Description.CopyAlternatives(source.Description)

            return duplicate

    @OperationsMethod
    def Find(self, name):
        """Find an item by name (case-insensitive).

        Args:
            name (str): The name to search for.

        Returns:
            ICmPossibility: The matching item, or None if not found.
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        target = normalize_match_key(name.strip(), casefold=True)
        wsHandle = self.project.project.DefaultAnalWs

        for item in self.GetAll():
            item_name = ITsString(item.Name.get_String(wsHandle)).Text
            if normalize_match_key(item_name, casefold=True) == target:
                return item

        return None

    @OperationsMethod
    def Exists(self, name):
        """Check if an item exists by name.

        Args:
            name (str): The name to check for.

        Returns:
            bool: True if an item with that name exists.
        """
        self._ValidateParam(name, "name")
        return self.Find(name) is not None

    @OperationsMethod
    def GetName(self, item_or_hvo, wsHandle=None):
        """Get the name of an item in specified writing system.

        Args:
            item_or_hvo: Either an ICmPossibility object or its HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The item name, or empty string if not set.
        """
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        item = self.__ResolveObject(item_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name_str = item.Name.get_String(wsHandle)
        if name_str:
            return ITsString(name_str).Text or ""
        return ""

    @OperationsMethod
    def SetName(self, item_or_hvo, name, wsHandle=None):
        """Set the name of an item in specified writing system.

        Args:
            item_or_hvo: Either an ICmPossibility object or its HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo or name is None.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(item_or_hvo, "item_or_hvo")
        self._ValidateParam(name, "name")

        item = self.__ResolveObject(item_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name or "", wsHandle)
        item.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetDescription(self, item_or_hvo, wsHandle=None):
        """Get the description of an item in specified writing system.

        Args:
            item_or_hvo: Either an ICmPossibility object or its HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The item description, or empty string if not set.
        """
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        item = self.__ResolveObject(item_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        desc_str = item.Description.get_String(wsHandle)
        if desc_str:
            return ITsString(desc_str).Text or ""
        return ""

    @OperationsMethod
    def SetDescription(self, item_or_hvo, description, wsHandle=None):
        """Set the description of an item in specified writing system.

        Args:
            item_or_hvo: Either an ICmPossibility object or its HVO.
            description (str): The new description.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        item = self.__ResolveObject(item_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(description or "", wsHandle)
        item.Description.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetGuid(self, item_or_hvo):
        """Get the GUID of an item.

        Args:
            item_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            str: The item GUID.
        """
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        item = self.__ResolveObject(item_or_hvo)
        return str(item.Guid)

    @OperationsMethod
    def CompareTo(self, item1_or_hvo, item2_or_hvo):
        """Compare two items by name.

        Args:
            item1_or_hvo: First item or HVO.
            item2_or_hvo: Second item or HVO.

        Returns:
            int: -1 if item1 < item2, 0 if equal, 1 if item1 > item2 (by name)
        """
        self._ValidateParam(item1_or_hvo, "item1_or_hvo")
        self._ValidateParam(item2_or_hvo, "item2_or_hvo")

        item1 = self.__ResolveObject(item1_or_hvo)
        item2 = self.__ResolveObject(item2_or_hvo)

        wsHandle = self.project.project.DefaultAnalWs
        name1 = ITsString(item1.Name.get_String(wsHandle)).Text or ""
        name2 = ITsString(item2.Name.get_String(wsHandle)).Text or ""

        if name1 < name2:
            return -1
        elif name1 > name2:
            return 1
        return 0

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item_or_hvo):
        """Get syncable properties for cross-project synchronization.

        Returns basic syncable properties common to all possibility items.
        Subclasses may override to add domain-specific properties.

        Args:
            item_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            dict: Dictionary of syncable properties
                - Name (dict of WS -> text)
                - Description (dict of WS -> text)
                - Guid
        """
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        item = self.__ResolveObject(item_or_hvo)

        props = {}
        props["Guid"] = str(item.Guid)

        # Collect all writing system alternatives for Name
        name_alts = {}
        for ws in self.project.WritingSystems.GetAll():
            wsHandle = ws.Handle
            name_str = item.Name.get_String(wsHandle)
            if name_str:
                name_alts[str(wsHandle)] = ITsString(name_str).Text or ""

        if name_alts:
            props["Name"] = name_alts

        # Collect all writing system alternatives for Description
        desc_alts = {}
        for ws in self.project.WritingSystems.GetAll():
            wsHandle = ws.Handle
            desc_str = item.Description.get_String(wsHandle)
            if desc_str:
                desc_alts[str(wsHandle)] = ITsString(desc_str).Text or ""

        if desc_alts:
            props["Description"] = desc_alts

        return props
