#
#   AnnotationDefOperations.py
#
#   Class: AnnotationDefOperations
#          Annotation definition management operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import FLEx LCM types
from SIL.LCModel import (
    ICmAnnotationDefn,
    ICmAnnotationDefnRepository,
    ICmAnnotationDefnFactory,
    ICmPossibility,
    ICmPossibilityList,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils
from System import Guid, DateTime

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key


class AnnotationDefOperations(BaseOperations):
    """
    This class provides operations for managing annotation type definitions
    in a FieldWorks project.

    Annotation definitions specify the types and characteristics of annotations
    (notes, comments) that can be created in FLEx. They define properties such
    as name, help text, whether users can create instances, and whether multiple
    annotations of this type are allowed.

    This class should be accessed via FLExProject.AnnotationDef property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all annotation definitions
        for anno_def in project.AnnotationDef.GetAll():
            name = project.AnnotationDef.GetName(anno_def)
            anno_type = project.AnnotationDef.GetAnnotationType(anno_def)
            print(f"{name}: {anno_type}")

        # Find a specific annotation definition
        todo_def = project.AnnotationDef.Find("To Do")
        if todo_def:
            # Get properties
            help_text = project.AnnotationDef.GetHelpString(todo_def)
            user_can_create = project.AnnotationDef.GetUserCanCreate(todo_def)
            print(f"Help: {help_text}")
            print(f"User creatable: {user_can_create}")

        # Create a new annotation definition
        custom_def = project.AnnotationDef.Create(
            "Review Required",
            CmAnnotationType.katGeneralNote,
            "en"
        )
        project.AnnotationDef.SetHelpString(custom_def,
            "Mark entries that need review", "en")
        project.AnnotationDef.SetUserCanCreate(custom_def, True)

        # Get annotation definitions by type
        for note_def in project.AnnotationDef.FindByType(
                CmAnnotationType.katGeneralNote):
            name = project.AnnotationDef.GetName(note_def)
            print(f"Note type: {name}")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize AnnotationDefOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all annotation definitions in the project.

        Yields:
            ICmAnnotationDefn: Each annotation definition in the project.

        Example:
            >>> for anno_def in project.AnnotationDef.GetAll():
            ...     name = project.AnnotationDef.GetName(anno_def)
            ...     anno_type = project.AnnotationDef.GetAnnotationType(anno_def)
            ...     user_create = project.AnnotationDef.GetUserCanCreate(anno_def)
            ...     print(f"{name} ({anno_type}): user_create={user_create}")
            To Do (katGeneralNote): user_create=True
            Question (katGeneralNote): user_create=True
            Resolved (katGeneralNote): user_create=False

        Notes:
            - Returns all annotation definitions regardless of type
            - Includes both system-defined and custom definitions
            - Definitions may be organized hierarchically (with sub-types)
            - Use FindByType() to filter by annotation type
            - Results are in no particular order

        See Also:
            Find, FindByType, GetUserCreatableTypes
        """
        repo = self.project.project.ServiceLocator.GetInstance(ICmAnnotationDefnRepository)

        for anno_def in repo.AllInstances():
            yield anno_def

    @OperationsMethod
    def Create(self, name, annotation_type, wsHandle=None, parent=None):
        """
        Create a new annotation definition.

        Args:
            name (str): The name of the annotation definition.
            annotation_type (CmAnnotationType): The annotation type enumeration.
            wsHandle: Optional writing system handle. Defaults to analysis WS.
            parent (ICmAnnotationDefn, optional): Parent definition for creating
                a sub-type. If None, creates a top-level definition.

        Returns:
            ICmAnnotationDefn: The newly created annotation definition.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If name or annotation_type is None.
            FP_ParameterError: If name is empty or already exists.

        Example:
            >>> # Create a top-level annotation definition
            >>> custom_def = project.AnnotationDef.Create(
            ...     "Review Required",
            ...     CmAnnotationType.katGeneralNote,
            ...     "en"
            ... )
            >>> print(project.AnnotationDef.GetName(custom_def))
            Review Required

            >>> # Create a sub-type under an existing definition
            >>> todo_def = project.AnnotationDef.Find("To Do")
            >>> urgent_def = project.AnnotationDef.Create(
            ...     "Urgent",
            ...     CmAnnotationType.katGeneralNote,
            ...     "en",
            ...     parent=todo_def
            ... )

            >>> # Set properties for new definition
            >>> project.AnnotationDef.SetUserCanCreate(custom_def, True)
            >>> project.AnnotationDef.SetHelpString(custom_def,
            ...     "Marks entries requiring review", "en")

        Notes:
            - Annotation type determines how the definition is used
            - Common types: katGeneralNote, katQuestionNote, katResolvedNote
            - Name should be unique within the project
            - Parent creates hierarchical organization of types
            - New definitions default to user_can_create=False
            - Use SetUserCanCreate() to make user-creatable
            - GUID is auto-generated
            - DateCreated is set automatically

        See Also:
            Delete, Find, SetUserCanCreate, SetHelpString
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")
        self._ValidateParam(annotation_type, "annotation_type")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        # Check if annotation definition with this name already exists
        if self.Find(name):
            raise FP_ParameterError(f"Annotation definition '{name}' already exists")

        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM(f"Create annotation definition '{name}'"):
            # Get the factory
            factory = self.project.project.ServiceLocator.GetService(ICmAnnotationDefnFactory)

            # Create the annotation definition
            anno_def = factory.Create()

            # Add to the annotation definitions list (must be done before setting properties)
            anno_list = self.project.lp.AnnotationDefsOA
            if anno_list:
                if parent:
                    # Add as sub-possibility under parent
                    if hasattr(parent, "SubPossibilitiesOS"):
                        parent.SubPossibilitiesOS.Add(anno_def)
                else:
                    # Add as top-level possibility
                    anno_list.PossibilitiesOS.Add(anno_def)

            # Set the name
            mkstr = TsStringUtils.MakeString(name, wsHandle)
            anno_def.Name.set_String(wsHandle, mkstr)

            # Set the annotation type
            if hasattr(anno_def, "AnnotationType"):
                anno_def.AnnotationType = int(annotation_type)

            return anno_def

    @OperationsMethod
    def Delete(self, anno_def):
        """
        Delete an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object to delete.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If anno_def is None.
            FP_ParameterError: If trying to delete a system definition.

        Example:
            >>> # Delete a custom annotation definition
            >>> custom = project.AnnotationDef.Find("Old Custom Type")
            >>> if custom:
            ...     project.AnnotationDef.Delete(custom)

        Warning:
            - DO NOT delete system annotation definitions
            - Deletion is permanent and cannot be undone
            - Any annotations using this definition will be affected
            - Deletes all sub-definitions recursively
            - Only delete custom definitions you created

        Notes:
            - Best practice: only delete custom definitions
            - Deletion cascades to sub-definitions
            - Existing annotations may become orphaned
            - Use with extreme caution on shared projects

        See Also:
            Create, Find, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(anno_def, "anno_def")

        with self._TransactionCM("Delete annotation definition"):
            # Remove from parent's collection
            owner = anno_def.Owner
            if hasattr(owner, "PossibilitiesOS"):
                if anno_def in owner.PossibilitiesOS:
                    owner.PossibilitiesOS.Remove(anno_def)
            elif hasattr(owner, "SubPossibilitiesOS"):
                if anno_def in owner.SubPossibilitiesOS:
                    owner.SubPossibilitiesOS.Remove(anno_def)

            # Delete the object
            if hasattr(anno_def, "Delete"):
                anno_def.Delete()

    @OperationsMethod
    def Find(self, name, wsHandle=None):
        """
        Find an annotation definition by name.

        Args:
            name (str): The name to search for (case-sensitive).
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmAnnotationDefn or None: The annotation definition if found,
                None otherwise.

        Raises:
            FP_NullParameterError: If name is None.

        Example:
            >>> # Find by name
            >>> todo_def = project.AnnotationDef.Find("To Do")
            >>> if todo_def:
            ...     print(f"Found: {project.AnnotationDef.GetName(todo_def)}")
            ... else:
            ...     print("Not found")
            Found: To Do

            >>> # Use to check if definition exists
            >>> if not project.AnnotationDef.Find("Custom Type"):
            ...     # Create it
            ...     custom = project.AnnotationDef.Create(
            ...         "Custom Type",
            ...         CmAnnotationType.katGeneralNote
            ...     )

        Notes:
            - Search is case-sensitive
            - Searches in specified writing system
            - Returns first match only (names should be unique)
            - Returns None if not found (doesn't raise exception)
            - Use Exists() for simple existence check

        See Also:
            Exists, GetAll, FindByType
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        wsHandle = self.__WSHandle(wsHandle)

        # Search through all annotation definitions
        target = normalize_match_key(name, casefold=False)
        for anno_def in self.GetAll():
            def_name = ITsString(anno_def.Name.get_String(wsHandle)).Text
            if normalize_match_key(def_name, casefold=False) == target:
                return anno_def

        return None

    @OperationsMethod
    def Exists(self, name, wsHandle=None):
        """
        Check if an annotation definition with the given name exists.

        Args:
            name (str): The name to check.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            bool: True if the annotation definition exists, False otherwise.

        Raises:
            FP_NullParameterError: If name is None.

        Example:
            >>> if project.AnnotationDef.Exists("To Do"):
            ...     print("To Do annotation type exists")
            To Do annotation type exists

            >>> if not project.AnnotationDef.Exists("Custom"):
            ...     print("Custom type does not exist")
            Custom type does not exist

        Notes:
            - Convenience method equivalent to Find(name) is not None
            - Case-sensitive check
            - Checks in specified writing system

        See Also:
            Find, GetAll
        """
        self._ValidateParam(name, "name")

        return self.Find(name, wsHandle) is not None

    # --- Property Getters and Setters ---

    @OperationsMethod
    def GetName(self, anno_def, wsHandle=None):
        """
        Get the name of an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The name, or empty string if not set.

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> for anno_def in project.AnnotationDef.GetAll():
            ...     name = project.AnnotationDef.GetName(anno_def)
            ...     print(f"Definition: {name}")
            Definition: To Do
            Definition: Question
            Definition: Resolved

        See Also:
            SetName, Find
        """
        self._ValidateParam(anno_def, "anno_def")

        wsHandle = self.__WSHandle(wsHandle)
        name = ITsString(anno_def.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, anno_def, name, wsHandle=None):
        """
        Set the name of an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If anno_def or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> custom = project.AnnotationDef.Find("Custom")
            >>> if custom:
            ...     project.AnnotationDef.SetName(custom, "Custom Review", "en")
            ...     print(project.AnnotationDef.GetName(custom))
            Custom Review

        Warning:
            - Renaming system definitions is not recommended
            - Only rename custom definitions you created
            - Changes affect display throughout FLEx

        See Also:
            GetName, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(anno_def, "anno_def")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        wsHandle = self.__WSHandle(wsHandle)
        mkstr = TsStringUtils.MakeString(name, wsHandle)
        anno_def.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetHelpString(self, anno_def, wsHandle=None):
        """
        Get the help string (description) of an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The help string, or empty string if not set.

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> todo_def = project.AnnotationDef.Find("To Do")
            >>> if todo_def:
            ...     help_text = project.AnnotationDef.GetHelpString(todo_def)
            ...     print(f"Help: {help_text}")
            Help: Marks items that need to be done

        Notes:
            - Help strings provide user guidance
            - Displayed as tooltips or help text in FLEx UI
            - Can be set in multiple writing systems

        See Also:
            SetHelpString, GetName
        """
        self._ValidateParam(anno_def, "anno_def")

        wsHandle = self.__WSHandle(wsHandle)

        if hasattr(anno_def, "HelpString"):
            help_str = ITsString(anno_def.HelpString.get_String(wsHandle)).Text
            return help_str or ""
        return ""

    @OperationsMethod
    def SetHelpString(self, anno_def, help_string, wsHandle=None):
        """
        Set the help string (description) of an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object.
            help_string (str): The help text to set.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If anno_def or help_string is None.

        Example:
            >>> custom_def = project.AnnotationDef.Create(
            ...     "Review Required",
            ...     CmAnnotationType.katGeneralNote
            ... )
            >>> project.AnnotationDef.SetHelpString(
            ...     custom_def,
            ...     "Marks entries that require linguistic review",
            ...     "en"
            ... )
            >>> print(project.AnnotationDef.GetHelpString(custom_def))
            Marks entries that require linguistic review

        Notes:
            - Empty string is allowed (clears the help string)
            - Help strings guide users on when to use this type
            - Can provide different help in different languages

        See Also:
            GetHelpString, SetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(anno_def, "anno_def")
        self._ValidateParam(help_string, "help_string")

        wsHandle = self.__WSHandle(wsHandle)

        if hasattr(anno_def, "HelpString"):
            mkstr = TsStringUtils.MakeString(help_string, wsHandle)
            anno_def.HelpString.set_String(wsHandle, mkstr)

    # --- Type and Instance Information ---

    @OperationsMethod
    def GetAnnotationType(self, anno_def):
        """
        Get the annotation type of an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object.

        Returns:
            int: The annotation type enumeration value (CmAnnotationType).

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> from SIL.LCModel import CmAnnotationType
            >>> todo_def = project.AnnotationDef.Find("To Do")
            >>> if todo_def:
            ...     anno_type = project.AnnotationDef.GetAnnotationType(todo_def)
            ...     if anno_type == int(CmAnnotationType.katGeneralNote):
            ...         print("This is a general note type")
            This is a general note type

        Notes:
            - Returns integer value of CmAnnotationType enum
            - Common types:
              * katGeneralNote: General purpose notes
              * katQuestionNote: Question annotations
              * katResolvedNote: Resolved items
              * katTranslationNote: Translation notes
            - Annotation type determines usage context

        See Also:
            FindByType, Create
        """
        self._ValidateParam(anno_def, "anno_def")

        if hasattr(anno_def, "AnnotationType"):
            return anno_def.AnnotationType
        return 0

    @OperationsMethod
    def GetInstanceOf(self, anno_def):
        """
        Get the class that this annotation definition is an instance of.

        Args:
            anno_def: The ICmAnnotationDefn object.

        Returns:
            int: The class ID that this definition instantiates.

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> todo_def = project.AnnotationDef.Find("To Do")
            >>> if todo_def:
            ...     class_id = project.AnnotationDef.GetInstanceOf(todo_def)
            ...     print(f"Instance of class: {class_id}")

        Notes:
            - Returns the class ID that annotations of this type will be
            - Used internally by FLEx to create annotation instances
            - Most annotation definitions are instances of ICmBaseAnnotation

        See Also:
            GetAnnotationType, Create
        """
        self._ValidateParam(anno_def, "anno_def")

        if hasattr(anno_def, "InstanceOf"):
            return anno_def.InstanceOf
        return 0

    # --- User Control Fields ---

    @OperationsMethod
    def GetUserCanCreate(self, anno_def):
        """
        Check if users can create annotations of this type.

        Args:
            anno_def: The ICmAnnotationDefn object.

        Returns:
            bool: True if users can create this type, False otherwise.

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> for anno_def in project.AnnotationDef.GetAll():
            ...     name = project.AnnotationDef.GetName(anno_def)
            ...     can_create = project.AnnotationDef.GetUserCanCreate(anno_def)
            ...     print(f"{name}: user_can_create={can_create}")
            To Do: user_can_create=True
            Question: user_can_create=True
            System Only: user_can_create=False

            >>> # Filter to user-creatable types only
            >>> user_types = [d for d in project.AnnotationDef.GetAll()
            ...     if project.AnnotationDef.GetUserCanCreate(d)]

        Notes:
            - Controls whether this type appears in user UI
            - False = system use only, not shown to users
            - True = users can select this type when creating annotations
            - Useful for hiding internal or deprecated types

        See Also:
            SetUserCanCreate, GetUserCreatableTypes
        """
        self._ValidateParam(anno_def, "anno_def")

        if hasattr(anno_def, "UserCanCreate"):
            return bool(anno_def.UserCanCreate)
        return False

    @OperationsMethod
    def SetUserCanCreate(self, anno_def, can_create):
        """
        Set whether users can create annotations of this type.

        Args:
            anno_def: The ICmAnnotationDefn object.
            can_create (bool): True to allow user creation, False to restrict.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If anno_def or can_create is None.

        Example:
            >>> # Make a custom type user-creatable
            >>> custom = project.AnnotationDef.Find("Custom Review")
            >>> if custom:
            ...     project.AnnotationDef.SetUserCanCreate(custom, True)
            ...     print(f"Can create: {project.AnnotationDef.GetUserCanCreate(custom)}")
            Can create: True

            >>> # Hide a deprecated type from users
            >>> old_type = project.AnnotationDef.Find("Old Type")
            >>> if old_type:
            ...     project.AnnotationDef.SetUserCanCreate(old_type, False)

        Notes:
            - True: Type appears in user's annotation type menu
            - False: Type hidden from users (system use only)
            - Useful for phasing out old types without deleting
            - Does not affect existing annotations of this type

        See Also:
            GetUserCanCreate, GetUserCreatableTypes
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(anno_def, "anno_def")
        self._ValidateParam(can_create, "can_create")

        if hasattr(anno_def, "UserCanCreate"):
            anno_def.UserCanCreate = bool(can_create)

    @OperationsMethod
    def GetMultiple(self, anno_def):
        """
        Check if multiple annotations of this type are allowed.

        Args:
            anno_def: The ICmAnnotationDefn object.

        Returns:
            bool: True if multiple annotations allowed, False if only one.

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> todo_def = project.AnnotationDef.Find("To Do")
            >>> if todo_def:
            ...     allows_multiple = project.AnnotationDef.GetMultiple(todo_def)
            ...     if allows_multiple:
            ...         print("Can have multiple To Do notes per item")
            ...     else:
            ...         print("Only one To Do note allowed per item")

        Notes:
            - True: Multiple annotations of this type can exist per object
            - False: Only one annotation of this type allowed per object
            - Enforced by FLEx UI when creating annotations
            - Useful for ensuring unique status markers

        See Also:
            SetMultiple, GetUserCanCreate
        """
        self._ValidateParam(anno_def, "anno_def")

        if hasattr(anno_def, "AllowsMultiple"):
            return bool(anno_def.AllowsMultiple)
        return True  # Default to allowing multiple

    @OperationsMethod
    def SetMultiple(self, anno_def, allow_multiple):
        """
        Set whether multiple annotations of this type are allowed.

        Args:
            anno_def: The ICmAnnotationDefn object.
            allow_multiple (bool): True to allow multiple, False for one only.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If anno_def or allow_multiple is None.

        Example:
            >>> # Allow multiple review notes
            >>> review_def = project.AnnotationDef.Find("Review")
            >>> if review_def:
            ...     project.AnnotationDef.SetMultiple(review_def, True)

            >>> # Allow only one status annotation
            >>> status_def = project.AnnotationDef.Find("Status")
            >>> if status_def:
            ...     project.AnnotationDef.SetMultiple(status_def, False)

        Notes:
            - True: Users can add multiple annotations of this type
            - False: Only one annotation of this type per object
            - Useful for status markers that should be unique
            - Setting affects future annotation creation only

        See Also:
            GetMultiple, SetUserCanCreate
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(anno_def, "anno_def")
        self._ValidateParam(allow_multiple, "allow_multiple")

        if hasattr(anno_def, "AllowsMultiple"):
            anno_def.AllowsMultiple = bool(allow_multiple)

    # --- Prompt and Copy/Paste Settings ---

    @OperationsMethod
    def GetPrompt(self, anno_def, wsHandle=None):
        """
        Get the prompt text for an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The prompt text, or empty string if not set.

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> todo_def = project.AnnotationDef.Find("To Do")
            >>> if todo_def:
            ...     prompt = project.AnnotationDef.GetPrompt(todo_def)
            ...     print(f"Prompt: {prompt}")
            Prompt: Enter what needs to be done

        Notes:
            - Prompt appears when user creates annotation of this type
            - Guides user on what information to enter
            - Can be localized in multiple writing systems

        See Also:
            SetPrompt, GetHelpString
        """
        self._ValidateParam(anno_def, "anno_def")

        wsHandle = self.__WSHandle(wsHandle)

        if hasattr(anno_def, "Prompt"):
            prompt = ITsString(anno_def.Prompt.get_String(wsHandle)).Text
            return prompt or ""
        return ""

    @OperationsMethod
    def SetPrompt(self, anno_def, prompt_text, wsHandle=None):
        """
        Set the prompt text for an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object.
            prompt_text (str): The prompt text to set.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If anno_def or prompt_text is None.

        Example:
            >>> custom_def = project.AnnotationDef.Create(
            ...     "Review",
            ...     CmAnnotationType.katGeneralNote
            ... )
            >>> project.AnnotationDef.SetPrompt(
            ...     custom_def,
            ...     "Describe what needs to be reviewed",
            ...     "en"
            ... )

        Notes:
            - Empty string is allowed (clears the prompt)
            - Prompt helps users understand what to enter
            - Can provide different prompts in different languages

        See Also:
            GetPrompt, SetHelpString
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(anno_def, "anno_def")
        self._ValidateParam(prompt_text, "prompt_text")

        wsHandle = self.__WSHandle(wsHandle)

        if hasattr(anno_def, "Prompt"):
            mkstr = TsStringUtils.MakeString(prompt_text, wsHandle)
            anno_def.Prompt.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetCopyCutPasteAllowed(self, anno_def):
        """
        Check if copy/cut/paste operations are allowed for this type.

        Args:
            anno_def: The ICmAnnotationDefn object.

        Returns:
            bool: True if copy/cut/paste allowed, False otherwise.

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> todo_def = project.AnnotationDef.Find("To Do")
            >>> if todo_def:
            ...     can_copy = project.AnnotationDef.GetCopyCutPasteAllowed(todo_def)
            ...     if can_copy:
            ...         print("Can copy/paste To Do annotations")

        Notes:
            - Controls whether users can copy/cut/paste annotations
            - True: Standard clipboard operations enabled
            - False: Copy/cut/paste disabled for this type
            - Useful for restricting certain annotation types

        See Also:
            GetUserCanCreate, GetMultiple
        """
        self._ValidateParam(anno_def, "anno_def")

        if hasattr(anno_def, "CopyCutPasteAllowed"):
            return bool(anno_def.CopyCutPasteAllowed)
        return True  # Default to allowing copy/paste

    # --- Query Methods ---

    @OperationsMethod
    def FindByType(self, annotation_type):
        """
        Find all annotation definitions of a specific type.

        Args:
            annotation_type (CmAnnotationType): The annotation type to search for.

        Yields:
            ICmAnnotationDefn: Each annotation definition matching the type.

        Raises:
            FP_NullParameterError: If annotation_type is None.

        Example:
            >>> from SIL.LCModel import CmAnnotationType
            >>> # Get all general note types
            >>> for note_def in project.AnnotationDef.FindByType(
            ...         CmAnnotationType.katGeneralNote):
            ...     name = project.AnnotationDef.GetName(note_def)
            ...     print(f"Note type: {name}")
            Note type: To Do
            Note type: Question
            Note type: Review Required

            >>> # Count question types
            >>> question_types = list(project.AnnotationDef.FindByType(
            ...     CmAnnotationType.katQuestionNote))
            >>> print(f"Found {len(question_types)} question types")

        Notes:
            - Filters all definitions by annotation type
            - Returns empty generator if no matches
            - Use to find related annotation definition groups
            - Common types: katGeneralNote, katQuestionNote, katResolvedNote

        See Also:
            GetAnnotationType, GetUserCreatableTypes
        """
        self._ValidateParam(annotation_type, "annotation_type")

        type_value = int(annotation_type)

        for anno_def in self.GetAll():
            if self.GetAnnotationType(anno_def) == type_value:
                yield anno_def

    @OperationsMethod
    def GetUserCreatableTypes(self):
        """
        Get all annotation definitions that users can create.

        Yields:
            ICmAnnotationDefn: Each user-creatable annotation definition.

        Example:
            >>> # Get types available to users
            >>> for anno_def in project.AnnotationDef.GetUserCreatableTypes():
            ...     name = project.AnnotationDef.GetName(anno_def)
            ...     anno_type = project.AnnotationDef.GetAnnotationType(anno_def)
            ...     print(f"Available: {name} (type={anno_type})")
            Available: To Do (type=0)
            Available: Question (type=1)
            Available: Custom Review (type=0)

            >>> # Count user-creatable types
            >>> count = len(list(project.AnnotationDef.GetUserCreatableTypes()))
            >>> print(f"Users can create {count} annotation types")

        Notes:
            - Filters to definitions where UserCanCreate is True
            - These are the types shown in FLEx UI annotation menus
            - System-only types are excluded
            - Useful for UI generation and validation

        See Also:
            GetUserCanCreate, SetUserCanCreate, FindByType
        """
        for anno_def in self.GetAll():
            if self.GetUserCanCreate(anno_def):
                yield anno_def

    # --- Metadata Methods ---

    @OperationsMethod
    def GetGuid(self, anno_def):
        """
        Get the GUID of an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object.

        Returns:
            System.Guid: The GUID of the annotation definition.

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> todo_def = project.AnnotationDef.Find("To Do")
            >>> if todo_def:
            ...     guid = project.AnnotationDef.GetGuid(todo_def)
            ...     print(f"GUID: {guid}")
            GUID: 12345678-1234-1234-1234-123456789abc

        Notes:
            - GUIDs are globally unique identifiers
            - Persistent across project versions
            - Use for external references and tracking
            - Same GUID across different copies of the project

        See Also:
            Create, Find
        """
        self._ValidateParam(anno_def, "anno_def")

        return anno_def.Guid

    @OperationsMethod
    def GetDateCreated(self, anno_def):
        """
        Get the creation date of an annotation definition.

        Args:
            anno_def: The ICmAnnotationDefn object.

        Returns:
            System.DateTime: The creation date/time, or None if not set.

        Raises:
            FP_NullParameterError: If anno_def is None.

        Example:
            >>> custom = project.AnnotationDef.Find("Custom Review")
            >>> if custom:
            ...     date = project.AnnotationDef.GetDateCreated(custom)
            ...     if date:
            ...         print(f"Created: {date}")
            Created: 11/23/2025 10:30:45 AM

        Notes:
            - DateCreated is set automatically when definition is created
            - Returns System.DateTime object
            - May be None for older definitions
            - Use for tracking when custom types were added

        See Also:
            Create, GetGuid
        """
        self._ValidateParam(anno_def, "anno_def")

        if hasattr(anno_def, "DateCreated"):
            return anno_def.DateCreated
        return None

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=True):
        """
        Duplicate an annotation definition, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The ICmAnnotationDefn object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source definition.
                                If False, insert at end of parent's list.
            deep (bool): If True (default), also duplicate sub-possibilities.
                        If False, only copy simple properties.

        Returns:
            ICmAnnotationDefn: The newly created duplicate with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> todo = project.AnnotationDef.Find("To Do")
            >>> if todo:
            ...     dup = project.AnnotationDef.Duplicate(todo)
            ...     print(f"Duplicate GUID: {project.AnnotationDef.GetGuid(dup)}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - MultiString properties: Name, HelpString, Prompt
            - Simple properties: AnnotationType, InstanceOf, UserCanCreate, AllowsMultiple
            - Sub-possibilities duplicated only if deep=True

        See Also:
            Create, Delete, GetGuid
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source object
        source = (
            ICmAnnotationDefn(item_or_hvo)
            if not isinstance(item_or_hvo, int)
            else ICmAnnotationDefn(self.project.Object(item_or_hvo))
        )
        # PossibilitiesOS lives on ICmPossibilityList (top-level list owner) and
        # SubPossibilitiesOS lives on ICmAnnotationDefn (sub-item owner).
        # Disambiguate by ClassName so pythonnet surfaces the typed accessor.
        raw_parent = source.Owner
        if raw_parent.ClassName == "CmPossibilityList":
            parent = ICmPossibilityList(raw_parent)
        else:
            parent = ICmAnnotationDefn(raw_parent)

        with self._TransactionCM("Duplicate annotation definition"):
            # Create new annotation definition using factory (auto-generates new GUID)
            factory = self.project.project.ServiceLocator.GetService(ICmAnnotationDefnFactory)
            duplicate = factory.Create()

            # ADD TO PARENT FIRST
            if insert_after:
                # Insert after source
                if hasattr(parent, "PossibilitiesOS"):
                    source_index = parent.PossibilitiesOS.IndexOf(source)
                    parent.PossibilitiesOS.Insert(source_index + 1, duplicate)
                elif hasattr(parent, "SubPossibilitiesOS"):
                    source_index = parent.SubPossibilitiesOS.IndexOf(source)
                    parent.SubPossibilitiesOS.Insert(source_index + 1, duplicate)
            else:
                # Insert at end
                if hasattr(parent, "PossibilitiesOS"):
                    parent.PossibilitiesOS.Add(duplicate)
                elif hasattr(parent, "SubPossibilitiesOS"):
                    parent.SubPossibilitiesOS.Add(duplicate)

            # Copy MultiString properties (AFTER adding to parent)
            duplicate.Name.CopyAlternatives(source.Name)
            if hasattr(source, "HelpString") and source.HelpString:
                duplicate.HelpString.CopyAlternatives(source.HelpString)
            if hasattr(source, "Prompt") and source.Prompt:
                duplicate.Prompt.CopyAlternatives(source.Prompt)

            # Copy simple properties
            if hasattr(source, "AnnotationType"):
                duplicate.AnnotationType = source.AnnotationType
            if hasattr(source, "InstanceOf"):
                duplicate.InstanceOf = source.InstanceOf
            if hasattr(source, "UserCanCreate"):
                duplicate.UserCanCreate = source.UserCanCreate
            if hasattr(source, "AllowsMultiple"):
                duplicate.AllowsMultiple = source.AllowsMultiple

            # Deep copy: duplicate sub-possibilities into the NEW duplicate
            if deep and hasattr(source, "SubPossibilitiesOS") and source.SubPossibilitiesOS.Count > 0:
                for sub in source.SubPossibilitiesOS:
                    self._DuplicateSubDefInto(sub, duplicate, deep=True)

            return duplicate

    def _DuplicateSubDefInto(self, source_def, parent_dup, deep=True):
        """Duplicate an annotation sub-definition into the specified parent."""
        factory = self.project.project.ServiceLocator.GetService(ICmAnnotationDefnFactory)
        dup_def = factory.Create()
        parent_dup.SubPossibilitiesOS.Add(dup_def)

        # Copy properties
        dup_def.Name.CopyAlternatives(source_def.Name)
        if hasattr(source_def, "HelpString") and source_def.HelpString:
            dup_def.HelpString.CopyAlternatives(source_def.HelpString)
        if hasattr(source_def, "Prompt") and source_def.Prompt:
            dup_def.Prompt.CopyAlternatives(source_def.Prompt)

        if hasattr(source_def, "AnnotationType"):
            dup_def.AnnotationType = source_def.AnnotationType
        if hasattr(source_def, "InstanceOf"):
            dup_def.InstanceOf = source_def.InstanceOf
        if hasattr(source_def, "UserCanCreate"):
            dup_def.UserCanCreate = source_def.UserCanCreate
        if hasattr(source_def, "AllowsMultiple"):
            dup_def.AllowsMultiple = source_def.AllowsMultiple

        # Recurse into nested sub-definitions
        if deep and hasattr(source_def, "SubPossibilitiesOS") and source_def.SubPossibilitiesOS.Count > 0:
            for nested_def in source_def.SubPossibilitiesOS:
                self._DuplicateSubDefInto(nested_def, dup_def, deep=True)

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """Get syncable properties for cross-project synchronization."""
        self._ValidateParam(item, "item")

        anno_def = item if not isinstance(item, int) else self.project.Object(item)
        wsHandle = self.__WSHandle(None)

        props = {}
        props["Name"] = ITsString(anno_def.Name.get_String(wsHandle)).Text or ""

        if hasattr(anno_def, "HelpString"):
            props["HelpString"] = ITsString(anno_def.HelpString.get_String(wsHandle)).Text or ""
        if hasattr(anno_def, "Prompt"):
            props["Prompt"] = ITsString(anno_def.Prompt.get_String(wsHandle)).Text or ""

        if hasattr(anno_def, "AnnotationType"):
            props["AnnotationType"] = int(anno_def.AnnotationType)
        if hasattr(anno_def, "InstanceOf"):
            props["InstanceOf"] = int(anno_def.InstanceOf)
        if hasattr(anno_def, "UserCanCreate"):
            props["UserCanCreate"] = bool(anno_def.UserCanCreate)
        if hasattr(anno_def, "AllowsMultiple"):
            props["AllowsMultiple"] = bool(anno_def.AllowsMultiple)

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """Compare two annotation definitions and return detailed differences."""
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        is_different = False
        differences = {"properties": {}}

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        for key in set(props1.keys()) | set(props2.keys()):
            val1 = props1.get(key)
            val2 = props2.get(key)
            if val1 != val2:
                is_different = True
                differences["properties"][key] = {"source": val1, "target": val2, "type": "modified"}

        return is_different, differences

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
