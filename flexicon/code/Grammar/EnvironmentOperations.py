#
#   EnvironmentOperations.py
#
#   Class: EnvironmentOperations
#          Phonological environment operations for FieldWorks Language Explorer
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
from SIL.LCModel import IPhEnvironmentFactory, IPhEnvironment, ICmObjectRepository
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class EnvironmentOperations(BaseOperations):
    """
    This class provides operations for managing phonological environments in a
    FieldWorks project.

    Phonological environments specify the context in which phonological rules
    apply. They describe what precedes and follows a segment, using notation
    like V_V (between vowels), #_ (word-initially), _# (word-finally), etc.

    Usage::

        from flexlibs2 import FLExProject, EnvironmentOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        envOps = EnvironmentOperations(project)

        # Get all environments
        for env in envOps.GetAll():
            name = envOps.GetName(env)
            notation = envOps.GetStringRepresentation(env)
            print(f"{name}: {notation}")

        # Create a new environment
        word_initial = envOps.Create("Word Initial", "At the beginning of a word")
        envOps.SetStringRepresentation(word_initial, "#_")

        # Create more environments
        between_vowels = envOps.Create("Between Vowels")
        envOps.SetStringRepresentation(between_vowels, "V_V")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize EnvironmentOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for environments.
        For Environment, we reorder parent.EnvironmentsOA.PossibilitiesOS
        """
        return parent.EnvironmentsOA.PossibilitiesOS

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all phonological environments in the project.

        Yields:
            IPhEnvironment: Each environment object in the project's environment list.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> for env in envOps.GetAll():
            ...     name = envOps.GetName(env)
            ...     notation = envOps.GetStringRepresentation(env)
            ...     print(f"{name}: {notation}")
            Word Initial: #_
            Word Final: _#
            Between Vowels: V_V
            Before Consonant: _C

        Notes:
            - Returns environments in their defined order
            - Environments are reusable across phonological rules
            - Returns empty if no phonological data defined

        See Also:
            Create, GetName, GetStringRepresentation
        """
        phon_data = self.project.lp.PhonologicalDataOA
        if phon_data is not None:
            for env in phon_data.EnvironmentsOS:
                yield env

    @OperationsMethod
    def Create(self, name, description=None):
        """
        Create a new phonological environment.

        Args:
            name (str): The name of the environment (e.g., "Word Initial",
                "Between Vowels").
            description (str, optional): Optional description of when this
                environment applies. Defaults to None.

        Returns:
            IPhEnvironment: The newly created environment object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> word_initial = envOps.Create("Word Initial", "At word start")
            >>> envOps.SetStringRepresentation(word_initial, "#_")
            >>> print(envOps.GetName(word_initial))
            Word Initial

            >>> between_vowels = envOps.Create("Between Vowels")
            >>> envOps.SetStringRepresentation(between_vowels, "V_V")

        Notes:
            - Name should be descriptive of the phonological context
            - Use SetStringRepresentation() to set formal notation (e.g., "V_V")
            - Description is optional but helpful for documentation
            - Environment is created in the default analysis writing system

        See Also:
            Delete, GetName, SetStringRepresentation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        # Get the writing system handle
        wsHandle = self.project.project.DefaultAnalWs

        # Create the new environment using the factory
        factory = self.project.project.ServiceLocator.GetService(IPhEnvironmentFactory)

        with self._TransactionCM("Create environment"):
            new_env = factory.Create()

            # Add to the environments list (must be done before setting properties)
            phon_data = self.project.lp.PhonologicalDataOA
            phon_data.EnvironmentsOS.Add(new_env)

            # Set name
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_env.Name.set_String(wsHandle, mkstr_name)

            # Set description if provided
            if description:
                mkstr_desc = TsStringUtils.MakeString(description, wsHandle)
                new_env.Description.set_String(wsHandle, mkstr_desc)

            return new_env

    @OperationsMethod
    def Delete(self, env_or_hvo):
        """
        Delete a phonological environment.

        Args:
            env_or_hvo: The IPhEnvironment object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If env_or_hvo is None.
            FP_ParameterError: If the environment is in use and cannot be deleted.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> obsolete = envOps.Create("Obsolete Environment")
            >>> # ... realize it's not needed
            >>> envOps.Delete(obsolete)

        Warning:
            - Deleting an environment that is in use may raise an error from FLEx
            - This includes environments used in phonological rules and allomorph
              conditions
            - Deletion is permanent and cannot be undone
            - Consider checking usage before deletion

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(env_or_hvo, "env_or_hvo")

        # Resolve to environment object
        env = self.__ResolveObject(env_or_hvo)

        # Remove from the environments list
        phon_data = self.project.lp.PhonologicalDataOA
        phon_data.EnvironmentsOS.Remove(env)

    @OperationsMethod
    def GetName(self, env_or_hvo, wsHandle=None):
        """
        Get the name of a phonological environment.

        Args:
            env_or_hvo: The IPhEnvironment object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The environment name, or empty string if not set.

        Raises:
            FP_NullParameterError: If env_or_hvo is None.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> for env in envOps.GetAll():
            ...     name = envOps.GetName(env)
            ...     print(name)
            Word Initial
            Word Final
            Between Vowels

            >>> # Get name in a specific writing system
            >>> env = list(envOps.GetAll())[0]
            >>> name = envOps.GetName(env, project.WSHandle('en'))

        See Also:
            SetName, GetStringRepresentation
        """
        self._ValidateParam(env_or_hvo, "env_or_hvo")

        env = self.__ResolveObject(env_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(env.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, env_or_hvo, name, wsHandle=None):
        """
        Set the name of a phonological environment.

        Args:
            env_or_hvo: The IPhEnvironment object or HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If env_or_hvo or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> env = list(envOps.GetAll())[0]
            >>> envOps.SetName(env, "Word Initial Position")

            >>> # Use standard terminology
            >>> envOps.SetName(env, "Intervocalic")  # Better than custom names

        Notes:
            - Use clear, descriptive names
            - Standard terminology aids cross-linguistic comparison

        See Also:
            GetName, SetStringRepresentation
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(env_or_hvo, "env_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        env = self.__ResolveObject(env_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        env.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetStringRepresentation(self, env_or_hvo, wsHandle=None):
        """
        Get the string representation (notation) of a phonological environment.

        Args:
            env_or_hvo: The IPhEnvironment object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The environment's string representation (e.g., "V_V", "#_", "_#"),
                or empty string if not set.

        Raises:
            FP_NullParameterError: If env_or_hvo is None.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> for env in envOps.GetAll():
            ...     name = envOps.GetName(env)
            ...     notation = envOps.GetStringRepresentation(env)
            ...     print(f"{name:20} {notation}")
            Word Initial         #_
            Word Final           _#
            Between Vowels       V_V
            After Nasal          N_
            Before Stop          _P

            >>> # Use in rule description
            >>> env = list(envOps.GetAll())[0]
            >>> notation = envOps.GetStringRepresentation(env)
            >>> print(f"Rule applies in: {notation}")
            Rule applies in: V_V

        Notes:
            - String representation uses formal phonological notation
            - Underscore (_) marks the position of the target segment
            - # marks word boundaries
            - $ marks syllable boundaries
            - Capital letters (V, C, N, etc.) reference natural classes

        Common Environment Notation:
            #_      - Word-initial (e.g., #_at)
            _#      - Word-final (e.g., ca_#)
            V_V     - Between vowels (intervocalic)
            C_C     - Between consonants
            N_      - After nasal
            _P      - Before stop
            $._     - Syllable-initial
            _.$     - Syllable-final

        See Also:
            SetStringRepresentation, GetName
        """
        self._ValidateParam(env_or_hvo, "env_or_hvo")

        env = self.__ResolveObject(env_or_hvo)
        # Note: StringRepresentation is ITsString, not IMultiUnicode
        # so we access .Text directly (wsHandle is unused for this property)
        notation = env.StringRepresentation.Text if env.StringRepresentation else ""
        return notation or ""

    @OperationsMethod
    def SetStringRepresentation(self, env_or_hvo, notation, wsHandle=None):
        """
        Set the string representation (notation) of a phonological environment.

        Args:
            env_or_hvo: The IPhEnvironment object or HVO.
            notation (str): The environment representation (e.g., "V_V", "#_", "_#").
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If env_or_hvo or notation is None.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> # Create and define common environments
            >>> word_initial = envOps.Create("Word Initial")
            >>> envOps.SetStringRepresentation(word_initial, "#_")

            >>> word_final = envOps.Create("Word Final")
            >>> envOps.SetStringRepresentation(word_final, "_#")

            >>> between_vowels = envOps.Create("Between Vowels")
            >>> envOps.SetStringRepresentation(between_vowels, "V_V")

            >>> # Complex environment: after nasal, before stop
            >>> env = envOps.Create("Nasal-Stop Cluster")
            >>> envOps.SetStringRepresentation(env, "N_P")

        Notes:
            - Use standard phonological environment notation
            - Underscore (_) marks the target position
            - Reference natural classes using their abbreviations (V, C, N, P)
            - Can specify complex environments with multiple contexts
            - Empty string is allowed for unrestricted environment

        Notation Guide:
            _       - Target position (required)
            #       - Word boundary
            $       - Syllable boundary
            V       - Vowel (natural class)
            C       - Consonant (natural class)
            N       - Nasal (natural class)
            P       - Stop (natural class)
            |       - Disjunction (or)

        See Also:
            GetStringRepresentation, Create
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(env_or_hvo, "env_or_hvo")
        self._ValidateParam(notation, "notation")

        env = self.__ResolveObject(env_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Note: StringRepresentation is ITsString, assign directly (not set_String)
        mkstr = TsStringUtils.MakeString(notation, wsHandle)
        env.StringRepresentation = mkstr

    @OperationsMethod
    def GetLeftContextPattern(self, env_or_hvo):
        """
        Get the left context pattern of a phonological environment (READ-ONLY).

        This is a computed property that returns the left context specification
        of the environment, representing what must precede the target position.

        Args:
            env_or_hvo: The IPhEnvironment object or HVO.

        Returns:
            object or None: The left context object (IPhPhonContext) if set,
                None otherwise.

        Raises:
            FP_NullParameterError: If env_or_hvo is None.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> env = envOps.Create("After Vowel")
            >>> left_ctx = envOps.GetLeftContextPattern(env)
            >>> if left_ctx:
            ...     print(f"Has left context: {left_ctx}")
            >>> else:
            ...     print("No left context constraint")

            >>> # Check all environments for left context
            >>> for env in envOps.GetAll():
            ...     name = envOps.GetName(env)
            ...     left_ctx = envOps.GetLeftContextPattern(env)
            ...     if left_ctx:
            ...         print(f"{name} has left context")

        Notes:
            - This is a READ-ONLY property (no setter)
            - Returns the LeftContextOA object if present
            - Left context specifies what must precede the target
            - Returns None if no left context is defined
            - The returned object is typically an IPhPhonContext
            - Use this to inspect or analyze environment structure
            - Not intended for modification (use SetLeftContext for that)

        See Also:
            GetRightContextPattern, GetStringRepresentation, GetName
        """
        self._ValidateParam(env_or_hvo, "env_or_hvo")

        env = self.__ResolveObject(env_or_hvo)

        # Return the left context if it exists
        if hasattr(env, "LeftContextOA") and env.LeftContextOA:
            return env.LeftContextOA

        return None

    @OperationsMethod
    def GetRightContextPattern(self, env_or_hvo):
        """
        Get the right context pattern of a phonological environment (READ-ONLY).

        This is a computed property that returns the right context specification
        of the environment, representing what must follow the target position.

        Args:
            env_or_hvo: The IPhEnvironment object or HVO.

        Returns:
            object or None: The right context object (IPhPhonContext) if set,
                None otherwise.

        Raises:
            FP_NullParameterError: If env_or_hvo is None.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> env = envOps.Create("Before Consonant")
            >>> right_ctx = envOps.GetRightContextPattern(env)
            >>> if right_ctx:
            ...     print(f"Has right context: {right_ctx}")
            >>> else:
            ...     print("No right context constraint")

            >>> # Check all environments for right context
            >>> for env in envOps.GetAll():
            ...     name = envOps.GetName(env)
            ...     right_ctx = envOps.GetRightContextPattern(env)
            ...     if right_ctx:
            ...         print(f"{name} has right context")

        Notes:
            - This is a READ-ONLY property (no setter)
            - Returns the RightContextOA object if present
            - Right context specifies what must follow the target
            - Returns None if no right context is defined
            - The returned object is typically an IPhPhonContext
            - Use this to inspect or analyze environment structure
            - Not intended for modification (use SetRightContext for that)

        See Also:
            GetLeftContextPattern, GetStringRepresentation, GetName
        """
        self._ValidateParam(env_or_hvo, "env_or_hvo")

        env = self.__ResolveObject(env_or_hvo)

        # Return the right context if it exists
        if hasattr(env, "RightContextOA") and env.RightContextOA:
            return env.RightContextOA

        return None

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=True):
        """
        Duplicate a phonological environment, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IPhEnvironment object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source environment.
                                If False, insert at end of environments list.
            deep (bool): If True (default), deep copy owned context objects (LeftContextOA, RightContextOA).
                        If False, contexts are not copied.

        Returns:
            IPhEnvironment: The newly created duplicate environment with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> word_initial = envOps.Create("Word Initial")
            >>> envOps.SetStringRepresentation(word_initial, "#_")
            >>> # Deep copy (default - includes owned context objects)
            >>> copy = envOps.Duplicate(word_initial)
            >>> print(envOps.GetName(copy))
            Word Initial

            >>> # Shallow copy (no context objects)
            >>> between_vowels = envOps.Create("Between Vowels")
            >>> copy = envOps.Duplicate(between_vowels, deep=False)

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original environment's position
            - Simple properties copied: Name, Description, StringRepresentation (MultiString)
            - deep=True copies owned context objects (LeftContextOA, RightContextOA)
            - Contexts are complex structures with their own owned objects

        See Also:
            Create, Delete
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source environment
        source = self.__ResolveObject(item_or_hvo)

        # Create new environment using factory (auto-generates new GUID)
        factory = self.project.project.ServiceLocator.GetService(IPhEnvironmentFactory)

        with self._TransactionCM("Duplicate environment"):
            duplicate = factory.Create()

            # Add to environments list
            phon_data = self.project.lp.PhonologicalDataOA
            if insert_after:
                source_index = phon_data.EnvironmentsOS.IndexOf(source)
                phon_data.EnvironmentsOS.Insert(source_index + 1, duplicate)
            else:
                phon_data.EnvironmentsOS.Add(duplicate)

            # Copy simple MultiString properties (AFTER adding to parent)
            duplicate.Name.CopyAlternatives(source.Name)
            duplicate.Description.CopyAlternatives(source.Description)

            # Copy StringRepresentation (ITsString, not MultiString)
            if source.StringRepresentation:
                notation = source.StringRepresentation.Text
                wsHandle = self.__WSHandle(None)
                mkstr = TsStringUtils.MakeString(notation, wsHandle)
                duplicate.StringRepresentation = mkstr

            # Deep copy: owned context objects
            if deep:
                from ..lcm_casting import clone_properties

                # Copy LeftContextOA if exists
                if hasattr(source, "LeftContextOA") and source.LeftContextOA:
                    try:
                        # Create new context object of the same type
                        src_context = source.LeftContextOA
                        new_context = self.project.project.ServiceLocator.ObjectRepository.NewObject(src_context.ClassID)
                        # Deep clone all properties
                        clone_properties(src_context, new_context, self.project)
                        duplicate.LeftContextOA = new_context
                    except Exception:
                        pass

                # Copy RightContextOA if exists
                if hasattr(source, "RightContextOA") and source.RightContextOA:
                    try:
                        # Create new context object of the same type
                        src_context = source.RightContextOA
                        new_context = self.project.project.ServiceLocator.ObjectRepository.NewObject(src_context.ClassID)
                        # Deep clone all properties
                        clone_properties(src_context, new_context, self.project)
                        duplicate.RightContextOA = new_context
                    except Exception:
                        pass

            return duplicate

    # --- Private Helper Methods ---

    def __ResolveObject(self, env_or_hvo):
        """
        Resolve HVO or object to IPhEnvironment.

        Args:
            env_or_hvo: Either an IPhEnvironment object or an HVO (int).

        Returns:
            IPhEnvironment: The resolved environment object.
        """
        if isinstance(env_or_hvo, int):
            return self.project.Object(env_or_hvo)
        return env_or_hvo

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        Args:
            item: The IPhEnvironment object.

        Returns:
            dict: Dictionary mapping property names to their values.
                Keys are property names, values are the property values.

        Example:
            >>> envOps = EnvironmentOperations(project)
            >>> env = list(envOps.GetAll())[0]
            >>> props = envOps.GetSyncableProperties(env)
            >>> print(props.keys())
            dict_keys(['Name', 'Description', 'StringRepresentation'])

        Notes:
            - Returns all MultiString properties (all writing systems)
            - Does not include owned objects (LeftContextOA, RightContextOA)
            - Does not include GUID or HVO
        """
        env = self.__ResolveObject(item)

        # Get all writing systems for MultiString properties
        # Fix: ILgWritingSystemFactory does not expose a .WritingSystems
        # property; enumerate via the wrapper's WritingSystemOperations.GetAll(),
        # which returns CoreWritingSystemDefinition objects with .Id / .Handle.
        all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}

        props = {}

        # MultiString properties
        for prop_name in ["Name", "Description", "StringRepresentation"]:
            prop_obj = getattr(env, prop_name)
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
        Compare two environments and return detailed differences.

        Args:
            item1: First environment to compare (from source project).
            item2: Second environment to compare (from target project).
            ops1: Optional EnvironmentOperations instance for item1's project.
                 Defaults to self.
            ops2: Optional EnvironmentOperations instance for item2's project.
                 Defaults to self.

        Returns:
            tuple: (is_different, differences) where:
                - is_different (bool): True if items differ
                - differences (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> env1 = project1_envOps.Find("Word Initial")
            >>> env2 = project2_envOps.Find("Word Initial")
            >>> is_diff, diffs = project1_envOps.CompareTo(
            ...     env1, env2,
            ...     ops1=project1_envOps,
            ...     ops2=project2_envOps
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
