#
#   GramCatOperations.py
#
#   Class: GramCatOperations
#          Grammatical Category operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
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
    ICmPossibility,
    ICmPossibilityFactory,
    IFsFeatStrucTypeFactory,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class GramCatOperations(BaseOperations):
    """
    This class provides operations for managing Grammatical Categories in a
    FieldWorks project.

    Grammatical categories are used to classify and describe grammatical
    properties such as person, number, gender, tense, aspect, mood, case,
    and other morphosyntactic features used in linguistic analysis.

    Usage::

        from flexlibs2 import FLExProject, GramCatOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        gramCatOps = GramCatOperations(project)

        # Get all grammatical categories
        for cat in gramCatOps.GetAll():
            print(gramCatOps.GetName(cat))

        # Create a new category
        person = gramCatOps.Create("person")

        # Create subcategories
        first = gramCatOps.Create("1st person", parent=person)
        second = gramCatOps.Create("2nd person", parent=person)
        third = gramCatOps.Create("3rd person", parent=person)

        # Navigate hierarchy
        parent = gramCatOps.GetParent(first)
        subcats = gramCatOps.GetSubcategories(person)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize GramCatOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for grammatical categories.
        For GramCat, we reorder parent.SubPossibilitiesOS
        """
        return parent.SubPossibilitiesOS

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, recursive=True, **kwargs):
        """
        Get all grammatical categories in the project.

        Args:
            recursive (bool): If True (default), yields every category in the
                hierarchy (depth-first, parents before children). If False,
                yields only top-level categories and the caller must descend
                via GetSubcategories.

        Yields:
            ICmPossibility: Each grammatical category.

        Example:
            >>> gramCatOps = GramCatOperations(project)
            >>> for cat in gramCatOps.GetAll():
            ...     print(gramCatOps.GetName(cat))   # Includes subcategories

            >>> # Top-level only
            >>> for cat in gramCatOps.GetAll(recursive=False):
            ...     print(gramCatOps.GetName(cat))

        See Also:
            GetSubcategories, Create
        """
        self._RejectLegacyKwargs(kwargs, {
            "flat": ("recursive", "semantics inverted: flat=True is now recursive=True"),
        })
        feature_system = self.project.lp.MsFeatureSystemOA
        if not feature_system:
            return

        def walk(collection):
            for cat in collection:
                yield cat
                if recursive and hasattr(cat, "SubPossibilitiesOS") and cat.SubPossibilitiesOS.Count > 0:
                    yield from walk(cat.SubPossibilitiesOS)

        yield from walk(feature_system.TypesOC)

    @OperationsMethod
    def Create(self, name, parent=None):
        """
        Create a new grammatical category.

        Args:
            name (str): The name of the category (e.g., "person", "1st person").
            parent (ICmPossibility or int, optional): Optional parent category
                for creating subcategories. Can be an ICmPossibility object or
                an HVO. Defaults to None (creates top-level category).

        Returns:
            ICmPossibility: The newly created grammatical category object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty, or if a category with this
                name already exists.

        Example:
            >>> gramCatOps = GramCatOperations(project)
            >>> # Create top-level category
            >>> person = gramCatOps.Create("person")
            >>> print(gramCatOps.GetName(person))
            person

            >>> # Create subcategories
            >>> first = gramCatOps.Create("1st person", parent=person)
            >>> second = gramCatOps.Create("2nd person", parent=person)
            >>> third = gramCatOps.Create("3rd person", parent=person)

            >>> # Create nested hierarchy
            >>> number = gramCatOps.Create("number")
            >>> singular = gramCatOps.Create("singular", parent=number)
            >>> plural = gramCatOps.Create("plural", parent=number)

        Notes:
            - If parent is None, creates a top-level category
            - If parent is provided, creates a subcategory
            - Name must be unique within the project
            - The category is created in the default analysis writing system
            - Used for linguistic feature analysis in morphology

        See Also:
            Delete, GetSubcategories, GetParent
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        # Get the writing system handle
        wsHandle = self.project.project.DefaultAnalWs

        # Dispatch the factory on the destination collection's typed
        # element. MsFeatureSystemOA.TypesOC is
        # LcmOwningCollection<IFsFeatStrucType> -- adding a bare
        # ICmPossibility there violates the typed-collection invariant
        # (the bug #163 calls out). SubPossibilitiesOS is the generic
        # ICmPossibility sequence and accepts the base factory. So:
        # top-level new categories go through IFsFeatStrucTypeFactory,
        # subcategories stay with ICmPossibilityFactory.
        # (issue #163)
        with self._TransactionCM(f"Create category '{name}'"):
            if parent:
                parent_obj = self.__ResolveObject(parent)
                factory = self.project.project.ServiceLocator.GetService(ICmPossibilityFactory)
                new_cat = factory.Create()
                parent_obj.SubPossibilitiesOS.Add(new_cat)
            else:
                feature_system = self.project.lp.MsFeatureSystemOA
                factory = self.project.project.ServiceLocator.GetService(IFsFeatStrucTypeFactory)
                new_cat = factory.Create()
                feature_system.TypesOC.Add(new_cat)

            # Set name
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_cat.Name.set_String(wsHandle, mkstr_name)

            return new_cat

    @OperationsMethod
    def Delete(self, cat_or_hvo):
        """
        Delete a grammatical category.

        Args:
            cat_or_hvo: The ICmPossibility object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If cat_or_hvo is None.
            FP_ParameterError: If the category is in use and cannot be deleted.

        Example:
            >>> gramCatOps = GramCatOperations(project)
            >>> obsolete = gramCatOps.Create("obsolete_feature")
            >>> # Later, if not needed...
            >>> gramCatOps.Delete(obsolete)

        Warning:
            - Deleting a category that is in use may raise an error from FLEx
            - Will also delete all subcategories recursively
            - Deletion is permanent and cannot be undone
            - Morphological rules or entries using this may be affected

        See Also:
            Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(cat_or_hvo, "cat_or_hvo")

        # Resolve to category object
        cat = self.__ResolveObject(cat_or_hvo)

        # Remove from the feature system TypesOC
        feature_system = self.project.lp.MsFeatureSystemOA
        feature_system.TypesOC.Remove(cat)

    @OperationsMethod
    def GetName(self, cat_or_hvo, wsHandle=None):
        """
        Get the name of a grammatical category.

        Args:
            cat_or_hvo: The ICmPossibility object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The category name, or empty string if not set.

        Raises:
            FP_NullParameterError: If cat_or_hvo is None.

        Example:
            >>> gramCatOps = GramCatOperations(project)
            >>> person = gramCatOps.Create("person")
            >>> name = gramCatOps.GetName(person)
            >>> print(name)
            person

            >>> # Get name in a specific writing system
            >>> vern_name = gramCatOps.GetName(person, project.WSHandle('en'))

            >>> # List all categories
            >>> for cat in gramCatOps.GetAll():
            ...     print(gramCatOps.GetName(cat))

        See Also:
            SetName, GetSubcategories
        """
        self._ValidateParam(cat_or_hvo, "cat_or_hvo")

        cat = self.__ResolveObject(cat_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(cat.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, cat_or_hvo, name, wsHandle=None):
        """
        Set the name of a grammatical category.

        Args:
            cat_or_hvo: The ICmPossibility object or HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If cat_or_hvo or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> gramCatOps = GramCatOperations(project)
            >>> cat = gramCatOps.Create("prson")  # typo
            >>> gramCatOps.SetName(cat, "person")  # fix it

            >>> # Set name in vernacular WS
            >>> gramCatOps.SetName(cat, "persona", project.WSHandle('es'))

        See Also:
            GetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(cat_or_hvo, "cat_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        cat = self.__ResolveObject(cat_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        cat.Name.set_String(wsHandle, mkstr)

    @wrap_enumerable
    @OperationsMethod
    def GetSubcategories(self, cat_or_hvo, recursive=True, **kwargs):
        """
        Get the subcategories of a grammatical category.

        Args:
            cat_or_hvo: The ICmPossibility object or HVO.
            recursive (bool): If True (default), returns every descendant
                (depth-first, parents before children). If False, returns
                only direct children.

        Returns:
            list: List of ICmPossibility subcategory objects (empty list if none).

        Raises:
            FP_NullParameterError: If cat_or_hvo is None.

        Example:
            >>> gramCatOps = GramCatOperations(project)
            >>> person = gramCatOps.Find("person")
            >>> for subcat in gramCatOps.GetSubcategories(person):
            ...     print(gramCatOps.GetName(subcat))     # All descendants

            >>> # Direct children only
            >>> for subcat in gramCatOps.GetSubcategories(person, recursive=False):
            ...     print(gramCatOps.GetName(subcat))

        See Also:
            GetAll, GetParent, Create
        """
        self._RejectLegacyKwargs(kwargs, {
            "flat": ("recursive", "semantics inverted: flat=True is now recursive=True"),
        })
        self._ValidateParam(cat_or_hvo, "cat_or_hvo")

        cat = self.__ResolveObject(cat_or_hvo)

        if not recursive:
            return list(cat.SubPossibilitiesOS)

        result = []
        def walk(collection):
            for child in collection:
                result.append(child)
                if hasattr(child, "SubPossibilitiesOS") and child.SubPossibilitiesOS.Count > 0:
                    walk(child.SubPossibilitiesOS)
        walk(cat.SubPossibilitiesOS)
        return result

    @OperationsMethod
    def GetParent(self, cat_or_hvo):
        """
        Get the parent category of a grammatical category.

        Args:
            cat_or_hvo: The ICmPossibility object or HVO.

        Returns:
            ICmPossibility or None: Parent category, or None if top-level.

        Raises:
            FP_NullParameterError: If cat_or_hvo is None.

        Example:
            >>> gramCatOps = GramCatOperations(project)
            >>> person = gramCatOps.Create("person")
            >>> first = gramCatOps.Create("1st person", parent=person)
            >>>
            >>> parent = gramCatOps.GetParent(first)
            >>> print(gramCatOps.GetName(parent))
            person
            >>>
            >>> # Top-level categories have no parent
            >>> print(gramCatOps.GetParent(person))
            None

            >>> # Traverse up the hierarchy
            >>> cat = first
            >>> while cat:
            ...     print(gramCatOps.GetName(cat))
            ...     cat = gramCatOps.GetParent(cat)
            1st person
            person

        Notes:
            - Returns None for top-level categories
            - Use to traverse hierarchy upward
            - Useful for determining category depth
            - Parent-child relationships define category taxonomy

        See Also:
            GetSubcategories, Create
        """
        self._ValidateParam(cat_or_hvo, "cat_or_hvo")

        cat = self.__ResolveObject(cat_or_hvo)

        # Check if this category has a parent
        # The Owner property returns the owning object
        if hasattr(cat, "Owner") and cat.Owner:
            # Check if the owner is also a possibility (not the feature system itself)
            try:
                owner = ICmPossibility(cat.Owner)
                return owner
            except (AttributeError, System.InvalidCastException) as e:
                # If owner is not a possibility, it's a top-level category
                return None

        return None

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=False):
        """
        Duplicate a grammatical category, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The ICmPossibility object or HVO to duplicate.
            insert_after (bool): For subcategories (SubPossibilitiesOS is
                ordered), controls whether the duplicate is inserted
                immediately after the source. Ignored for top-level
                categories: TypesOC is an unordered ILcmOwningCollection, so
                top-level duplicates are always appended via Add().
            deep (bool): If True, recursively duplicate all subcategories.
                        If False (default), only duplicate the category itself.

        Returns:
            ICmPossibility: The newly created duplicate category with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> gramCatOps = GramCatOperations(project)
            >>> person = gramCatOps.Create("person")
            >>> # Shallow copy (no subcategories)
            >>> person_copy = gramCatOps.Duplicate(person)
            >>> print(gramCatOps.GetName(person_copy))
            person

            >>> # Deep copy (includes all subcategories)
            >>> number = gramCatOps.Create("number")
            >>> singular = gramCatOps.Create("singular", parent=number)
            >>> plural = gramCatOps.Create("plural", parent=number)
            >>> number_copy = gramCatOps.Duplicate(number, deep=True)
            >>> orig_subs = gramCatOps.GetSubcategories(number)
            >>> copy_subs = gramCatOps.GetSubcategories(number_copy)
            >>> print(f"Original has {len(orig_subs)} subcategories")
            >>> print(f"Copy has {len(copy_subs)} subcategories")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original category's position
            - Simple properties copied: Name, Abbreviation, Description (MultiString)
            - deep=True recursively duplicates SubPossibilitiesOS hierarchy
            - Used for creating variants of grammatical feature hierarchies

        See Also:
            Create, Delete, GetSubcategories
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source category
        source = self.__ResolveObject(item_or_hvo)

        # Determine parent and insertion position. Top-level categories
        # live in feature_system.TypesOC (LcmOwningCollection<IFsFeatStrucType>);
        # subcategories live in their parent's SubPossibilitiesOS
        # (LcmOwningSequence<ICmPossibility>). Dispatch the factory on
        # the destination to satisfy each typed-collection invariant.
        # (issue #163)
        parent_is_possibility = False
        try:
            parent_cat = ICmPossibility(source.Owner)
            parent_is_possibility = True
        except Exception:
            parent_is_possibility = False

        with self._TransactionCM("Duplicate category"):
            if parent_is_possibility:
                # Source is a subcategory
                parent_cat = ICmPossibility(source.Owner)
                factory = self.project.project.ServiceLocator.GetService(ICmPossibilityFactory)
                duplicate = factory.Create()
                if insert_after:
                    source_index = parent_cat.SubPossibilitiesOS.IndexOf(source)
                    parent_cat.SubPossibilitiesOS.Insert(source_index + 1, duplicate)
                else:
                    parent_cat.SubPossibilitiesOS.Add(duplicate)
            else:
                # Source is top-level -- TypesOC requires IFsFeatStrucType.
                # TypesOC is an unordered ILcmOwningCollection; insert_after has
                # no semantic meaning here and is ignored.
                feature_system = self.project.lp.MsFeatureSystemOA
                factory = self.project.project.ServiceLocator.GetService(IFsFeatStrucTypeFactory)
                duplicate = factory.Create()
                feature_system.TypesOC.Add(duplicate)

            # Copy simple MultiString properties (AFTER adding to parent)
            duplicate.Name.CopyAlternatives(source.Name)
            duplicate.Abbreviation.CopyAlternatives(source.Abbreviation)
            duplicate.Description.CopyAlternatives(source.Description)

            # Deep copy: recursively duplicate subcategories
            if deep and source.SubPossibilitiesOS.Count > 0:
                for sub_cat in source.SubPossibilitiesOS:
                    # Recursively duplicate each subcategory
                    self.__DuplicateSubcategory(sub_cat, duplicate)

            return duplicate

    def __DuplicateSubcategory(self, source_sub, parent_duplicate):
        """
        Helper method to recursively duplicate a subcategory.

        Args:
            source_sub: The source ICmPossibility subcategory to duplicate.
            parent_duplicate: The parent ICmPossibility to add the duplicate to.

        Returns:
            ICmPossibility: The duplicated subcategory.
        """
        # Create new subcategory
        factory = self.project.project.ServiceLocator.GetService(ICmPossibilityFactory)
        sub_duplicate = factory.Create()

        # Add to parent's SubPossibilitiesOS
        parent_duplicate.SubPossibilitiesOS.Add(sub_duplicate)

        # Copy properties
        sub_duplicate.Name.CopyAlternatives(source_sub.Name)
        sub_duplicate.Abbreviation.CopyAlternatives(source_sub.Abbreviation)
        sub_duplicate.Description.CopyAlternatives(source_sub.Description)

        # Recursively duplicate nested subcategories
        if source_sub.SubPossibilitiesOS.Count > 0:
            for nested_sub in source_sub.SubPossibilitiesOS:
                self.__DuplicateSubcategory(nested_sub, sub_duplicate)

        return sub_duplicate

    # --- Private Helper Methods ---

    def __ResolveObject(self, cat_or_hvo):
        """
        Resolve HVO or object to ICmPossibility.

        Args:
            cat_or_hvo: Either an ICmPossibility object or an HVO (int).

        Returns:
            ICmPossibility: The resolved category object.
        """
        if isinstance(cat_or_hvo, int):
            return self.project.Object(cat_or_hvo)
        return cat_or_hvo

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        Args:
            item: The ICmPossibility (grammatical category) object.

        Returns:
            dict: Dictionary mapping property names to their values.
                Keys are property names, values are the property values.

        Example:
            >>> gramCatOps = GramCatOperations(project)
            >>> cat = list(gramCatOps.GetAll())[0]
            >>> props = gramCatOps.GetSyncableProperties(cat)
            >>> print(props.keys())
            dict_keys(['Name', 'Abbreviation', 'Description'])

        Notes:
            - Returns all MultiString properties (all writing systems)
            - Does not include SubPossibilitiesOS (child categories)
            - Does not include GUID or HVO
        """
        cat = self.__ResolveObject(item)

        # Get all writing systems for MultiString properties
        # Fix: ILgWritingSystemFactory does not expose a .WritingSystems
        # property; enumerate via the wrapper's WritingSystemOperations.GetAll(),
        # which returns CoreWritingSystemDefinition objects with .Id / .Handle.
        all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}

        props = {}

        # MultiString properties
        for prop_name in ["Name", "Abbreviation", "Description"]:
            prop_obj = getattr(cat, prop_name)
            ws_values = {}
            for ws_id, ws_handle in all_ws.items():
                text = ITsString(prop_obj.get_String(ws_handle)).Text
                if text:  # Only include non-empty values
                    ws_values[ws_id] = text
            if ws_values:  # Only include property if it has values
                props[prop_name] = ws_values

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """Apply syncable properties (from GetSyncableProperties) onto an item.

        Inherited from BaseOperations; declared on the concrete class so static
        API indexers see it. The base implementation handles every property
        shape this class's GetSyncableProperties emits.
        """
        return super().ApplySyncableProperties(item, props, ws_map, fill_gaps=fill_gaps)

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two grammatical categories and return detailed differences.

        Args:
            item1: First category to compare (from source project).
            item2: Second category to compare (from target project).
            ops1: Optional GramCatOperations instance for item1's project.
                 Defaults to self.
            ops2: Optional GramCatOperations instance for item2's project.
                 Defaults to self.

        Returns:
            tuple: (is_different, differences) where:
                - is_different (bool): True if items differ
                - differences (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> cat1 = project1_gramCatOps.Find("person")
            >>> cat2 = project2_gramCatOps.Find("person")
            >>> is_diff, diffs = project1_gramCatOps.CompareTo(
            ...     cat1, cat2,
            ...     ops1=project1_gramCatOps,
            ...     ops2=project2_gramCatOps
            ... )
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} -> {val2}")

        Notes:
            - Compares all MultiString properties across all writing systems
            - Returns empty dict if items are identical
            - Handles cross-project comparison via ops1/ops2
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        # Get syncable properties from both items
        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        is_different = False
        differences = {}

        # Compare each property
        all_keys = set(props1.keys()) | set(props2.keys())
        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            # For MultiString properties, compare the dictionaries
            if val1 != val2:
                is_different = True
                differences[key] = (val1, val2)

        return (is_different, differences)

    # --- Private Helper Methods ---

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to analysis WS.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)
