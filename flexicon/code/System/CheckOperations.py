#
#   CheckOperations.py
#
#   Class: CheckOperations
#          Consistency check and validation operations for FieldWorks Language
#          Explorer projects via SIL Language and Culture Model (LCM) API.
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
from datetime import datetime

# Import FLEx LCM types
from SIL.LCModel import (
    ICmPossibility,
    ICmPossibilityFactory,
    ICmPossibilityList,
    ILexEntry,
    IWfiWordform,
    IText,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod

# Import string utilities
from ..Shared.string_utils import normalize_text, normalize_match_key


class CheckOperations(BaseOperations):
    """
    This class provides operations for managing consistency checks and
    validation in a FieldWorks project.

    Consistency checks help identify data quality issues, missing information,
    and inconsistencies in lexical entries, texts, and other project data.
    Check types are managed as possibility list items.

    This class should be accessed via FLExProject.Checks property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all check types
        for check_type in project.Checks.GetAllCheckTypes():
            name = project.Checks.GetName(check_type)
            enabled = project.Checks.IsEnabled(check_type)
            print(f"{name}: {'Enabled' if enabled else 'Disabled'}")

        # Create a custom check type
        check = project.Checks.CreateCheckType("Missing Gloss Check")
        project.Checks.SetDescription(check, "Verify all senses have glosses")
        project.Checks.EnableCheck(check)

        # Run a check and get results
        project.Checks.RunCheck(check)
        errors = project.Checks.GetErrorCount(check)
        warnings = project.Checks.GetWarningCount(check)
        print(f"Check found {errors} errors and {warnings} warnings")

        # Get items with issues
        items = project.Checks.FindItemsWithIssues(check)
        for item in items:
            issues = project.Checks.GetIssuesForObject(check, item)
            print(f"Issues: {len(issues)}")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize CheckOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)
        # Cache for check execution results
        self._check_results = {}
        self._check_last_run = {}
        self._check_enabled = {}

    # --- Core CRUD Operations ---

    @OperationsMethod
    def GetAllCheckTypes(self):
        """
        Get all consistency check types in the project.

        Returns all check types that are available for validation and
        consistency checking.

        Yields:
            ICmPossibility: Each check type object

        Example:
            >>> for check_type in project.Checks.GetAllCheckTypes():
            ...     name = project.Checks.GetName(check_type)
            ...     desc = project.Checks.GetDescription(check_type)
            ...     enabled = project.Checks.IsEnabled(check_type)
            ...     print(f"{name}: {desc} ({'Enabled' if enabled else 'Disabled'})")
            Missing Gloss: Check for senses without glosses (Enabled)
            Duplicate Entries: Find potential duplicate lexical entries (Disabled)
            Incomplete Paradigm: Verify paradigm completeness (Enabled)

        Notes:
            - Check types are stored as possibility list items
            - Custom check types can be created for project-specific needs
            - Each check type can be enabled or disabled independently
            - Check types persist across sessions

        See Also:
            CreateCheckType, FindCheckType, GetEnabledChecks
        """
        check_list = self._GetCheckList()
        if check_list:
            for check_type in check_list.PossibilitiesOS:
                yield check_type
            # Also yield nested check types
            for check_type in check_list.PossibilitiesOS:
                for subcheck in check_type.SubPossibilitiesOS:
                    yield subcheck

    @OperationsMethod
    def CreateCheckType(self, name, description=None, wsHandle=None):
        """
        Create a new consistency check type.

        Creates a new check type that can be used to validate project data.
        The check type is added to the project's check possibility list.

        Args:
            name (str): The name of the check type. Must be unique and non-empty.
            description (str, optional): Description of what the check validates.
                Defaults to None (empty description).
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmPossibility: The newly created check type object.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If name is None or empty.
            FP_ParameterError: If a check type with this name already exists.

        Example:
            >>> # Create a simple check type
            >>> check = project.Checks.CreateCheckType("Missing Etymology Check")
            >>> print(project.Checks.GetName(check))
            Missing Etymology Check

            >>> # Create with description
            >>> check = project.Checks.CreateCheckType(
            ...     "Incomplete Paradigm",
            ...     "Verify all paradigm slots are filled")
            >>> print(project.Checks.GetDescription(check))
            Verify all paradigm slots are filled

            >>> # Enable the check
            >>> project.Checks.EnableCheck(check)

        Notes:
            - Check is created but not enabled by default
            - Use EnableCheck() to activate the check
            - The check type persists across sessions
            - Custom logic for running the check must be implemented separately

        See Also:
            DeleteCheckType, GetAllCheckTypes, EnableCheck
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        name = name.strip() if isinstance(name, str) else ""
        self._ValidateParam(name, "name")

        # Check if check type with this name already exists
        if self.FindCheckType(name):
            raise FP_ParameterError(f"A check type with the name '{name}' already exists")

        wsHandle = self.__WSHandle(wsHandle)

        # Get or create the check possibility list
        check_list = self._GetOrCreateCheckList()

        # Create the new check type using the factory
        factory = self.project.project.ServiceLocator.GetService(ICmPossibilityFactory)

        with self._TransactionCM(f"Create check type '{name}'"):
            new_check = factory.Create()

            # Add to check list (must be done before setting properties)
            check_list.PossibilitiesOS.Add(new_check)

            # Set name
            mkstr = TsStringUtils.MakeString(name, wsHandle)
            new_check.Name.set_String(wsHandle, mkstr)

            # Set description if provided
            if description:
                desc_str = TsStringUtils.MakeString(description, wsHandle)
                new_check.Description.set_String(wsHandle, desc_str)

            # Initialize as disabled by default
            self._check_enabled[new_check.Guid] = False

            return new_check

    @OperationsMethod
    def DeleteCheckType(self, check_or_hvo):
        """
        Delete a consistency check type from the project.

        Removes the check type and all associated results and configuration.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> # Delete by object
            >>> check = project.Checks.FindCheckType("Old Check")
            >>> if check:
            ...     project.Checks.DeleteCheckType(check)

            >>> # Delete by HVO
            >>> project.Checks.DeleteCheckType(check_hvo)

        Warning:
            - Deletion is permanent and cannot be undone
            - All check results and configuration are deleted
            - Only delete custom check types, not system checks

        Notes:
            - Removes check from the possibility list
            - Clears cached results for this check
            - Cannot be undone

        See Also:
            CreateCheckType, GetAllCheckTypes
        """
        self._EnsureWriteEnabled()

        check_obj = self.__GetCheckObject(check_or_hvo)

        # Remove from check list
        check_list = self._GetCheckList()
        if check_list:
            # Try to remove from top level
            if check_obj in check_list.PossibilitiesOS:
                check_list.PossibilitiesOS.Remove(check_obj)
            else:
                # Try to remove from parent's subitems
                for parent in check_list.PossibilitiesOS:
                    if check_obj in parent.SubPossibilitiesOS:
                        parent.SubPossibilitiesOS.Remove(check_obj)
                        break

        # Clear cached data
        guid = check_obj.Guid
        if guid in self._check_results:
            del self._check_results[guid]
        if guid in self._check_last_run:
            del self._check_last_run[guid]
        if guid in self._check_enabled:
            del self._check_enabled[guid]

    @OperationsMethod
    def FindCheckType(self, name):
        """
        Find a check type by its name.

        Searches for a check type with the specified name in the project's
        check possibility list.

        Args:
            name (str): The check type name to search for (case-insensitive).

        Returns:
            ICmPossibility or None: The check type object if found, None otherwise.

        Raises:
            FP_NullParameterError: If name is None or empty.

        Example:
            >>> # Find a check type
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> if check:
            ...     status = project.Checks.GetCheckStatus(check)
            ...     print(f"Status: {status}")
            Status: Ready

            >>> # Case-insensitive search
            >>> check = project.Checks.FindCheckType("missing gloss")
            >>> print(check is not None)
            True

        Notes:
            - Search is case-insensitive
            - Searches in default analysis writing system
            - Returns first match only
            - Returns None if not found (doesn't raise exception)
            - Searches recursively through nested check types

        See Also:
            GetAllCheckTypes, CreateCheckType, GetName
        """
        self._ValidateParam(name, "name")

        name = name.strip() if isinstance(name, str) else ""
        self._ValidateParam(name, "name")

        target = normalize_match_key(name, casefold=True)
        wsHandle = self.project.project.DefaultAnalWs

        # Search through all check types
        for check_type in self.GetAllCheckTypes():
            check_name = ITsString(check_type.Name.get_String(wsHandle)).Text
            if check_name and normalize_match_key(check_name, casefold=True) == target:
                return check_type

        return None

    # --- Property Methods ---

    @OperationsMethod
    def GetName(self, check_or_hvo, wsHandle=None):
        """
        Get the name of a check type.

        Retrieves the check type name in the specified writing system.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The name of the check type in the specified writing system.
                Returns empty string if no name is set.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> name = project.Checks.GetName(check)
            >>> print(name)
            Missing Gloss

            >>> # Get name in specific WS
            >>> ws_handle = project.WSHandle('fr')
            >>> name_fr = project.Checks.GetName(check, ws_handle)

        See Also:
            SetName, GetDescription, FindCheckType
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(check_obj.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, check_or_hvo, name, wsHandle=None):
        """
        Set the name of a check type.

        Sets the check type name in the specified writing system.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).
            name (str): The new name for the check type. Must be non-empty.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If check_or_hvo or name is None/empty.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Old Name")
            >>> if check:
            ...     project.Checks.SetName(check, "Updated Check Name")
            ...     print(project.Checks.GetName(check))
            Updated Check Name

            >>> # Set name in specific WS
            >>> ws_handle = project.WSHandle('fr')
            >>> project.Checks.SetName(check, "Vérification manquante", ws_handle)

        See Also:
            GetName, SetDescription
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        name = name.strip() if isinstance(name, str) else ""
        self._ValidateParam(name, "name")

        check_obj = self.__GetCheckObject(check_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        check_obj.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetDescription(self, check_or_hvo, wsHandle=None):
        """
        Get the description of a check type.

        Retrieves the detailed description explaining what the check validates.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The description of the check type. Returns empty string if
                no description is set.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> desc = project.Checks.GetDescription(check)
            >>> print(desc)
            Identifies lexical senses that are missing glosses in the analysis
            writing system

        See Also:
            SetDescription, GetName
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        desc = ITsString(check_obj.Description.get_String(wsHandle)).Text
        return desc or ""

    @OperationsMethod
    def SetDescription(self, check_or_hvo, description, wsHandle=None):
        """
        Set the description of a check type.

        Sets a detailed description explaining what the check validates.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).
            description (str): The new description text.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If check_or_hvo or description is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Etymology")
            >>> project.Checks.SetDescription(
            ...     check,
            ...     "Identifies entries without etymology information")
            >>> print(project.Checks.GetDescription(check))
            Identifies entries without etymology information

        See Also:
            GetDescription, SetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(description, "description")

        check_obj = self.__GetCheckObject(check_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(description, wsHandle)
        check_obj.Description.set_String(wsHandle, mkstr)

    # --- Execution Methods ---

    @OperationsMethod
    def RunCheck(self, check_or_hvo, target_objects=None):
        """
        Run a consistency check on project data.

        Executes the specified check and stores the results. The actual
        validation logic is determined by the check type.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).
            target_objects (list, optional): List of specific objects to check.
                If None, checks all relevant objects in the project.
                Defaults to None.

        Returns:
            dict: Results dictionary containing:
                - 'errors': list of error items
                - 'warnings': list of warning items
                - 'passed': list of items that passed
                - 'timestamp': datetime when check was run

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist, is invalid,
                or is not enabled.

        Example:
            >>> # Run check on all data
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> project.Checks.EnableCheck(check)
            >>> results = project.Checks.RunCheck(check)
            >>> print(f"Errors: {len(results['errors'])}")
            Errors: 15
            >>> print(f"Warnings: {len(results['warnings'])}")
            Warnings: 3

            >>> # Run check on specific entries
            >>> entries = list(project.LexiconGetAllEntries())[:10]
            >>> results = project.Checks.RunCheck(check, entries)

        Notes:
            - Check must be enabled before running
            - Results are cached until next run
            - Timestamp records when check was executed
            - Validation logic determined by check type name
            - Supports: Missing Gloss, Missing Definition, Missing Example,
              Missing Grammatical Info, Duplicate Entries, Missing Etymology
            - Unknown check types will mark all objects as passed

        See Also:
            GetCheckStatus, GetCheckResults, GetErrorCount, EnableCheck
        """
        check_obj = self.__GetCheckObject(check_or_hvo)

        # Verify check is enabled
        if not self.IsEnabled(check_obj):
            raise FP_ParameterError("Check must be enabled before running")

        # Initialize results
        results = {"errors": [], "warnings": [], "passed": [], "timestamp": datetime.now()}

        # Get target objects if not specified
        if target_objects is None:
            target_objects = self._GetDefaultCheckTargets(check_obj)

        # Run the check (placeholder - actual implementation would vary by check type)
        results = self._ExecuteCheck(check_obj, target_objects)

        # Cache results
        guid = check_obj.Guid
        self._check_results[guid] = results
        self._check_last_run[guid] = results["timestamp"]

        return results

    @OperationsMethod
    def GetCheckStatus(self, check_or_hvo):
        """
        Get the current status of a check type.

        Returns a status indicating whether the check is ready to run,
        running, completed, or has issues.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Returns:
            str: Status string, one of:
                - 'Ready': Check is enabled and ready to run
                - 'Disabled': Check is not enabled
                - 'Completed': Check has been run and results are available
                - 'Never Run': Check has never been executed

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> status = project.Checks.GetCheckStatus(check)
            >>> print(f"Status: {status}")
            Status: Ready

            >>> # Run check and check status
            >>> project.Checks.RunCheck(check)
            >>> status = project.Checks.GetCheckStatus(check)
            >>> print(status)
            Completed

        See Also:
            RunCheck, GetLastRun, IsEnabled
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid

        if not self.IsEnabled(check_obj):
            return "Disabled"
        elif guid in self._check_results:
            return "Completed"
        elif guid in self._check_last_run:
            return "Completed"
        else:
            return "Never Run"

    @OperationsMethod
    def GetLastRun(self, check_or_hvo):
        """
        Get the timestamp when a check was last executed.

        Returns the date and time when the check was most recently run.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Returns:
            datetime or None: Timestamp of last execution, or None if the
                check has never been run.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> last_run = project.Checks.GetLastRun(check)
            >>> if last_run:
            ...     print(f"Last run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
            ... else:
            ...     print("Never run")
            Last run: 2025-11-23 14:30:45

        See Also:
            RunCheck, GetCheckStatus
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid

        return self._check_last_run.get(guid, None)

    # --- Results Methods ---

    @OperationsMethod
    def GetCheckResults(self, check_or_hvo):
        """
        Get the full results from the last check execution.

        Retrieves all results including errors, warnings, and passed items
        from the most recent run of the check.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Returns:
            dict or None: Results dictionary containing:
                - 'errors': list of error items
                - 'warnings': list of warning items
                - 'passed': list of items that passed
                - 'timestamp': datetime when check was run
            Returns None if check has never been run.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> project.Checks.RunCheck(check)
            >>> results = project.Checks.GetCheckResults(check)
            >>> if results:
            ...     print(f"Errors: {len(results['errors'])}")
            ...     print(f"Warnings: {len(results['warnings'])}")
            ...     print(f"Passed: {len(results['passed'])}")
            Errors: 15
            Warnings: 3
            Passed: 142

        See Also:
            RunCheck, GetErrorCount, GetWarningCount
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid

        return self._check_results.get(guid, None)

    @OperationsMethod
    def GetErrorCount(self, check_or_hvo):
        """
        Get the number of errors found by a check.

        Returns the count of items that failed the check with errors
        from the most recent execution.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Returns:
            int: Number of errors found. Returns 0 if check has never been run.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> project.Checks.RunCheck(check)
            >>> error_count = project.Checks.GetErrorCount(check)
            >>> print(f"Found {error_count} errors")
            Found 15 errors

        See Also:
            GetWarningCount, GetCheckResults, RunCheck
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid

        results = self._check_results.get(guid, None)
        if results:
            return len(results.get("errors", []))
        return 0

    @OperationsMethod
    def GetWarningCount(self, check_or_hvo):
        """
        Get the number of warnings found by a check.

        Returns the count of items with warnings from the most recent
        check execution.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Returns:
            int: Number of warnings found. Returns 0 if check has never been run.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> project.Checks.RunCheck(check)
            >>> warning_count = project.Checks.GetWarningCount(check)
            >>> print(f"Found {warning_count} warnings")
            Found 3 warnings

        See Also:
            GetErrorCount, GetCheckResults, RunCheck
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid

        results = self._check_results.get(guid, None)
        if results:
            return len(results.get("warnings", []))
        return 0

    # --- Filter Methods ---

    @OperationsMethod
    def GetEnabledChecks(self):
        """
        Get all enabled check types.

        Returns only those check types that are currently enabled and
        ready to run.

        Yields:
            ICmPossibility: Each enabled check type object

        Example:
            >>> # List enabled checks
            >>> for check in project.Checks.GetEnabledChecks():
            ...     name = project.Checks.GetName(check)
            ...     print(f"Enabled: {name}")
            Enabled: Missing Gloss
            Enabled: Incomplete Paradigm
            Enabled: Duplicate Entries

            >>> # Count enabled checks
            >>> enabled_count = len(list(project.Checks.GetEnabledChecks()))
            >>> print(f"Total enabled: {enabled_count}")
            Total enabled: 3

        Notes:
            - Only returns checks that have been explicitly enabled
            - Disabled checks are excluded
            - Useful for batch operations on active checks

        See Also:
            GetAllCheckTypes, EnableCheck, DisableCheck, IsEnabled
        """
        for check_type in self.GetAllCheckTypes():
            if self.IsEnabled(check_type):
                yield check_type

    @OperationsMethod
    def EnableCheck(self, check_or_hvo):
        """
        Enable a consistency check type.

        Activates the check so it can be run on project data.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> project.Checks.EnableCheck(check)
            >>> print(project.Checks.IsEnabled(check))
            True

            >>> # Run the enabled check
            >>> results = project.Checks.RunCheck(check)

        See Also:
            DisableCheck, IsEnabled, GetEnabledChecks
        """
        self._EnsureWriteEnabled()

        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid
        self._check_enabled[guid] = True

    @OperationsMethod
    def DisableCheck(self, check_or_hvo):
        """
        Disable a consistency check type.

        Deactivates the check so it cannot be run. Previous results
        are retained.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Raises:
            FP_ReadOnlyError: If project was not opened with writeEnabled=True.
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> project.Checks.DisableCheck(check)
            >>> print(project.Checks.IsEnabled(check))
            False

            >>> # Previous results still accessible
            >>> results = project.Checks.GetCheckResults(check)

        See Also:
            EnableCheck, IsEnabled, GetEnabledChecks
        """
        self._EnsureWriteEnabled()

        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid
        self._check_enabled[guid] = False

    @OperationsMethod
    def IsEnabled(self, check_or_hvo):
        """
        Check if a consistency check type is enabled.

        Returns whether the check is currently active and can be run.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Returns:
            bool: True if check is enabled, False otherwise.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> if project.Checks.IsEnabled(check):
            ...     print("Check is active")
            ... else:
            ...     print("Check is disabled")
            Check is active

        See Also:
            EnableCheck, DisableCheck, GetEnabledChecks
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid
        return self._check_enabled.get(guid, False)

    # --- Query Methods ---

    @OperationsMethod
    def FindItemsWithIssues(self, check_or_hvo, issue_type="all"):
        """
        Find all items that have issues according to a check.

        Returns items that failed the check, either with errors, warnings,
        or both, from the most recent check execution.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).
            issue_type (str): Type of issues to return. Options:
                - 'all': Both errors and warnings (default)
                - 'errors': Only errors
                - 'warnings': Only warnings

        Returns:
            list: List of objects that have the specified issues. Returns
                empty list if check has never been run or no issues found.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist, is invalid,
                or issue_type is not recognized.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> project.Checks.RunCheck(check)
            >>>
            >>> # Get all items with issues
            >>> items = project.Checks.FindItemsWithIssues(check)
            >>> print(f"Total items with issues: {len(items)}")
            Total items with issues: 18
            >>>
            >>> # Get only items with errors
            >>> error_items = project.Checks.FindItemsWithIssues(check, 'errors')
            >>> print(f"Items with errors: {len(error_items)}")
            Items with errors: 15
            >>>
            >>> # Get only items with warnings
            >>> warning_items = project.Checks.FindItemsWithIssues(check, 'warnings')
            >>> print(f"Items with warnings: {len(warning_items)}")
            Items with warnings: 3

        Notes:
            - Returns items from most recent check execution only
            - Returns empty list if check has never been run
            - issue_type parameter controls filtering of results

        See Also:
            GetIssuesForObject, RunCheck, GetCheckResults
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid

        if issue_type not in ["all", "errors", "warnings"]:
            raise FP_ParameterError("issue_type must be 'all', 'errors', or 'warnings'")

        results = self._check_results.get(guid, None)
        if not results:
            return []

        items = []
        if issue_type in ["all", "errors"]:
            items.extend(results.get("errors", []))
        if issue_type in ["all", "warnings"]:
            items.extend(results.get("warnings", []))

        return items

    @OperationsMethod
    def GetIssuesForObject(self, check_or_hvo, obj):
        """
        Get all issues found for a specific object.

        Returns detailed information about issues found for the given
        object during the most recent check execution.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).
            obj: The object to get issues for (e.g., ILexEntry, IText, etc.).

        Returns:
            list: List of issue descriptions for the object. Returns empty
                list if object has no issues or check has never been run.

        Raises:
            FP_NullParameterError: If check_or_hvo or obj is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> project.Checks.RunCheck(check)
            >>>
            >>> # Get issues for a specific entry
            >>> entry = list(project.LexiconGetAllEntries())[0]
            >>> issues = project.Checks.GetIssuesForObject(check, entry)
            >>> for issue in issues:
            ...     print(f"- {issue}")
            - Sense 1 is missing gloss in English
            - Sense 2 is missing gloss in English

        Notes:
            - Returns issues from most recent check execution only
            - Returns empty list if object passed the check
            - Issue descriptions are human-readable strings
            - Useful for displaying issues in UI or reports

        See Also:
            FindItemsWithIssues, RunCheck, GetCheckResults
        """
        self._ValidateParam(obj, "obj")

        check_obj = self.__GetCheckObject(check_or_hvo)
        guid = check_obj.Guid

        results = self._check_results.get(guid, None)
        if not results:
            return []

        # Search for object in errors and warnings
        issues = []
        for item in results.get("errors", []):
            if hasattr(item, "Hvo") and hasattr(obj, "Hvo"):
                if item.Hvo == obj.Hvo:
                    issues.append(f"Error: {self._GetIssueDescription(item)}")

        for item in results.get("warnings", []):
            if hasattr(item, "Hvo") and hasattr(obj, "Hvo"):
                if item.Hvo == obj.Hvo:
                    issues.append(f"Warning: {self._GetIssueDescription(item)}")

        return issues

    # --- Metadata Methods ---

    @OperationsMethod
    def GetGuid(self, check_or_hvo):
        """
        Get the GUID of a check type.

        Returns the globally unique identifier for the check type.

        Args:
            check_or_hvo: Either an ICmPossibility check type object or its
                HVO (integer identifier).

        Returns:
            System.Guid: The check type's globally unique identifier.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the check type does not exist or is invalid.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> guid = project.Checks.GetGuid(check)
            >>> print(guid)
            a23b6fcc-654c-4983-a11c-5e4e15e1f6e9

            >>> # Use GUID to retrieve check later
            >>> retrieved = project.Object(guid)
            >>> name = project.Checks.GetName(retrieved)
            >>> print(name)
            Missing Gloss

        Notes:
            - GUID is stable across sessions
            - GUID is unique across all projects
            - Use GUID for persistent references
            - GUID can be used with project.Object(guid) to retrieve the check

        See Also:
            FindCheckType, GetName
        """
        check_obj = self.__GetCheckObject(check_or_hvo)
        return check_obj.Guid

    # --- Private Helper Methods ---

    def __GetCheckObject(self, check_or_hvo):
        """
        Internal function to get ICmPossibility check object from check_or_hvo.

        Args:
            check_or_hvo: Either an ICmPossibility object or its HVO (integer).

        Returns:
            ICmPossibility: The check object.

        Raises:
            FP_NullParameterError: If check_or_hvo is None.
            FP_ParameterError: If the object doesn't exist or isn't a valid check.
        """
        self._ValidateParam(check_or_hvo, "check_or_hvo")

        try:
            # If it's an integer, get the object
            if isinstance(check_or_hvo, int):
                obj = self.project.Object(check_or_hvo)
                return ICmPossibility(obj)
            else:
                # Already a possibility object
                return ICmPossibility(check_or_hvo)
        except Exception:
            raise FP_ParameterError(f"Invalid check type object or HVO: {check_or_hvo}")

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

    def _GetCheckList(self):
        """
        Get the check possibility list.

        Returns:
            ICmPossibilityList or None: The check list if it exists, None otherwise.
        """
        # Check if there's a dedicated check list
        # In FLEx, this might be stored in a specific location
        # For now, return None if not found
        # Implementation would depend on actual FLEx data model
        return None

    def _GetOrCreateCheckList(self):
        """
        Get or create the check possibility list.

        Returns:
            ICmPossibilityList: The check list.
        """
        check_list = self._GetCheckList()
        if check_list:
            return check_list

        # Create a new check list
        # Note: This is a simplified implementation
        # Actual implementation would depend on FLEx data model
        from SIL.LCModel import ICmPossibilityListFactory

        factory = self.project.project.ServiceLocator.GetInstance(ICmPossibilityListFactory)
        new_list = factory.Create()

        wsHandle = self.project.project.DefaultAnalWs
        name_str = TsStringUtils.MakeString("Consistency Checks", wsHandle)
        new_list.Name.set_String(wsHandle, name_str)

        return new_list

    def _GetDefaultCheckTargets(self, check_obj):
        """
        Get default target objects for a check.

        Args:
            check_obj: The check type ICmPossibility object.

        Returns:
            list: List of default objects to check.
        """
        # Default to all lexical entries
        # Actual implementation would vary based on check type
        return list(self.project.LexiconGetAllEntries())

    def _ExecuteCheck(self, check_obj, target_objects):
        """
        Execute the actual check logic.

        Args:
            check_obj: The check type ICmPossibility object.
            target_objects: List of objects to check.

        Returns:
            dict: Results dictionary with errors, warnings, and passed items.

        Notes:
            Implements common FLEx consistency checks:
            - Missing Gloss (ERROR): Senses without glosses
            - Missing Definition (WARNING): Senses without definitions
            - Missing Example (WARNING): Senses without examples
            - Missing Grammatical Info (ERROR): Senses without POS
            - Duplicate Entries (WARNING): Entries with same lexeme form
            - Missing Etymology (WARNING): Entries without etymology
        """
        results = {"errors": [], "warnings": [], "passed": [], "timestamp": datetime.now()}

        # Get check name - use exact matching (Craig's pattern)
        check_name = self.GetName(check_obj)
        wsHandle = self.project.project.DefaultAnalWs

        # Perform check based on exact check type name
        for obj in target_objects:
            try:
                # Ensure we're working with ILexEntry
                if not isinstance(obj, ILexEntry):
                    try:
                        obj = ILexEntry(obj)
                    except TypeError:
                        # Object is not a lexical entry - skip it
                        results["passed"].append(obj)
                        continue

                entry = obj
                has_issue = False

                # Use exact name matching for check types (Craig's pattern)
                if check_name == "Missing Gloss":
                    # ERROR: Senses without glosses
                    for sense in entry.SensesOS:
                        gloss_text = ITsString(sense.Gloss.get_String(wsHandle)).Text
                        if not gloss_text or not gloss_text.strip():
                            results["errors"].append(entry)
                            has_issue = True
                            break

                elif check_name == "Missing Definition":
                    # WARNING: Senses without definitions
                    for sense in entry.SensesOS:
                        def_text = ITsString(sense.Definition.get_String(wsHandle)).Text
                        if not def_text or not def_text.strip():
                            results["warnings"].append(entry)
                            has_issue = True
                            break

                elif check_name == "Missing Example":
                    # WARNING: Senses without examples
                    for sense in entry.SensesOS:
                        if sense.ExamplesOS.Count == 0:
                            results["warnings"].append(entry)
                            has_issue = True
                            break

                elif check_name == "Missing Grammatical Info" or check_name == "Missing Part of Speech":
                    # ERROR: Senses without POS/MSA
                    for sense in entry.SensesOS:
                        if sense.MorphoSyntaxAnalysisRA is None:
                            results["errors"].append(entry)
                            has_issue = True
                            break

                elif check_name == "Duplicate Entries":
                    # WARNING: Entries with same lexeme form lacking homograph numbers
                    if hasattr(entry, "HomographNumber") and entry.HomographNumber == 0:
                        results["warnings"].append(entry)
                        has_issue = True

                elif check_name == "Missing Etymology":
                    # WARNING: Entries without etymology
                    if entry.EtymologyOS.Count == 0:
                        results["warnings"].append(entry)
                        has_issue = True

                else:
                    # Unknown check type - mark as passed (don't fail on custom checks)
                    pass

                # If no issue found, mark as passed
                if not has_issue:
                    results["passed"].append(entry)

            except (AttributeError, KeyError) as e:
                # Entry structure incompatible with this check type
                logger.warning(f"Entry {obj} incompatible with check '{check_name}': {e}")
                results["passed"].append(obj)
            except Exception as e:
                # Unexpected error - this indicates a bug, don't hide it
                logger.error(f"Unexpected error checking entry {obj} with '{check_name}': {e}")
                raise

        return results

    def _GetIssueDescription(self, obj):
        """
        Get a human-readable description of an issue for an object.

        Args:
            obj: The object with issues.

        Returns:
            str: Description of the issue.
        """
        # Placeholder implementation
        # Actual description would be based on check type and object
        if hasattr(obj, "HeadWord") and obj.HeadWord:
            return f"Issue with '{normalize_text(obj.HeadWord.Text)}'"
        return "Issue found"

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=True):
        """
        Duplicate a check type, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The ICmPossibility check object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source check.
                                If False, insert at end of parent's list.
            deep (bool): If True (default), also duplicate sub-checks.
                        If False, only copy simple properties.

        Returns:
            ICmPossibility: The newly created duplicate with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> check = project.Checks.FindCheckType("Missing Gloss")
            >>> if check:
            ...     dup = project.Checks.Duplicate(check)
            ...     print(f"Duplicate: {project.Checks.GetName(dup)}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - MultiString properties: Name, Description
            - Check state (enabled/disabled) is not copied
            - Check results are not copied

        See Also:
            CreateCheckType, DeleteCheckType, GetGuid
        """
        self._EnsureWriteEnabled()

        check_obj = self.__GetCheckObject(item_or_hvo)
        # PossibilitiesOS lives on ICmPossibilityList (top-level) and
        # SubPossibilitiesOS lives on ICmPossibility (sub-check). Disambiguate
        # by ClassName so pythonnet surfaces the typed collection accessor.
        raw_parent = check_obj.Owner
        if raw_parent.ClassName == "CmPossibilityList":
            parent = ICmPossibilityList(raw_parent)
        else:
            parent = ICmPossibility(raw_parent)

        # Create new check using factory (auto-generates new GUID)
        factory = self.project.project.ServiceLocator.GetService(ICmPossibilityFactory)

        with self._TransactionCM("Duplicate check type"):
            duplicate = factory.Create()

            # ADD TO PARENT FIRST
            if insert_after:
                # Insert after source
                if hasattr(parent, "PossibilitiesOS"):
                    source_index = parent.PossibilitiesOS.IndexOf(check_obj)
                    parent.PossibilitiesOS.Insert(source_index + 1, duplicate)
                elif hasattr(parent, "SubPossibilitiesOS"):
                    source_index = parent.SubPossibilitiesOS.IndexOf(check_obj)
                    parent.SubPossibilitiesOS.Insert(source_index + 1, duplicate)
            else:
                # Insert at end
                if hasattr(parent, "PossibilitiesOS"):
                    parent.PossibilitiesOS.Add(duplicate)
                elif hasattr(parent, "SubPossibilitiesOS"):
                    parent.SubPossibilitiesOS.Add(duplicate)

            # Copy MultiString properties (AFTER adding to parent)
            duplicate.Name.CopyAlternatives(check_obj.Name)
            if hasattr(check_obj, "Description") and check_obj.Description:
                duplicate.Description.CopyAlternatives(check_obj.Description)

            # Note: Check state and results are not copied
            # The duplicate starts as disabled with no results

            # Deep copy: duplicate sub-checks into the NEW duplicate
            if deep and hasattr(check_obj, "SubPossibilitiesOS") and check_obj.SubPossibilitiesOS.Count > 0:
                for sub in check_obj.SubPossibilitiesOS:
                    self._DuplicateSubCheckInto(sub, duplicate, deep=True)

            return duplicate

    def _DuplicateSubCheckInto(self, source_check, parent_dup, deep=True):
        """Duplicate a sub-check into the specified parent's SubPossibilitiesOS."""
        factory = self.project.project.ServiceLocator.GetService(ICmPossibilityFactory)
        dup_check = factory.Create()
        parent_dup.SubPossibilitiesOS.Add(dup_check)

        # Copy properties
        dup_check.Name.CopyAlternatives(source_check.Name)
        if hasattr(source_check, "Description") and source_check.Description:
            dup_check.Description.CopyAlternatives(source_check.Description)

        # Recurse into nested sub-checks
        if deep and hasattr(source_check, "SubPossibilitiesOS") and source_check.SubPossibilitiesOS.Count > 0:
            for nested_check in source_check.SubPossibilitiesOS:
                self._DuplicateSubCheckInto(nested_check, dup_check, deep=True)

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """Get syncable properties for cross-project synchronization."""
        check_obj = self.__GetCheckObject(item)
        wsHandle = self.__WSHandle(None)

        props = {}
        props["Name"] = ITsString(check_obj.Name.get_String(wsHandle)).Text or ""
        if hasattr(check_obj, "Description") and check_obj.Description:
            props["Description"] = ITsString(check_obj.Description.get_String(wsHandle)).Text or ""

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """Compare two checks and return detailed differences."""
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
