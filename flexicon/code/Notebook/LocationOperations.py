#
#   LocationOperations.py
#
#   Class: LocationOperations
#          Geographic location operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)

import math

# Import FLEx LCM types
from SIL.LCModel import (
    ICmLocation,
    ICmLocationFactory,
    ICmPossibilityRepository,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils
from System import DateTime

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key


class LocationOperations(BaseOperations):
    """
    This class provides operations for managing geographic locations in a
    FieldWorks project.

    Locations in FLEx represent geographic places where linguistic data was
    collected, where speakers live, or where languages are spoken. Locations
    support hierarchical organization (regions, subregions, cities), geographic
    coordinates, elevation data, and descriptive information.

    This class should be accessed via FLExProject.Location property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all locations
        for location in project.Location.GetAll():
            name = project.Location.GetName(location)
            coords = project.Location.GetCoordinates(location)
            print(f"{name}: {coords}")

        # Create a new location
        village = project.Location.Create("Barasana Village", "en")
        project.Location.SetCoordinates(village, -1.2345, -70.6789)
        project.Location.SetElevation(village, 150)

        # Create hierarchical locations
        region = project.Location.Create("Vaupés Region", "en")
        subregion = project.Location.CreateSublocation(
            region, "Papurí River Area", "en")

        # Find locations by coordinates
        nearby = project.Location.FindByCoordinates(-1.23, -70.67, radius_km=50)
        print(f"Found {len(nearby)} locations within 50 km")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize LocationOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, recursive=True, **kwargs):
        """
        Get all locations in the project.

        Args:
            recursive (bool): If True (default), returns every location in
                the hierarchy (depth-first, parents before children). If
                False, returns only top-level locations and the caller must
                descend via GetSublocations.

        Returns:
            list: List of ICmLocation objects.

        Example:
            >>> for location in project.Location.GetAll():
            ...     print(project.Location.GetName(location))   # Includes sublocations

            >>> # Top-level only
            >>> for location in project.Location.GetAll(recursive=False):
            ...     print(project.Location.GetName(location))

        See Also:
            Find, Create, GetSublocations
        """
        self._RejectLegacyKwargs(kwargs, {
            "flat": ("recursive", "semantics inverted: flat=True is now recursive=True"),
        })
        location_list = self.project.lp.LocationsOA
        if not location_list:
            return []

        return list(self.project.UnpackNestedPossibilityList(
            location_list.PossibilitiesOS, ICmLocation, recursive))

    @OperationsMethod
    def Create(self, name, wsHandle=None, alias=None):
        """
        Create a new top-level location.

        Args:
            name (str): The name of the new location.
            wsHandle: Optional writing system handle. Defaults to analysis WS.
            alias (str): Optional alias/abbreviation for the location.

        Returns:
            ICmLocation: The newly created location object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> # Create a simple location
            >>> village = project.Location.Create("Barasana Village", "en")
            >>> print(project.Location.GetName(village))
            Barasana Village

            >>> # Create with alias
            >>> region = project.Location.Create("Vaupés Department", "en",
            ...                                   alias="VAU")
            >>> print(project.Location.GetAlias(region))
            VAU

            >>> # Add coordinates and elevation
            >>> project.Location.SetCoordinates(village, -1.2345, -70.6789)
            >>> project.Location.SetElevation(village, 150)

        Notes:
            - Creates a top-level location (no parent region)
            - Use CreateSublocation() to create hierarchical locations
            - Name is set in specified writing system
            - Alias is optional and can be set later with SetAlias()
            - Coordinates and elevation should be set separately
            - GUID is auto-generated

        See Also:
            Delete, CreateSublocation, SetName, SetCoordinates
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        wsHandle = self.__WSHandle(wsHandle)

        # Get the locations list
        location_list = self.project.lp.LocationsOA
        if not location_list:
            raise FP_ParameterError("Locations list not found in project")

        # Create the new location using the factory
        with self._TransactionCM(f"Create location '{name}'"):
            factory = self.project.project.ServiceLocator.GetService(ICmLocationFactory)
            new_location = factory.Create()

            # Add to top-level list (must be done before setting properties)
            location_list.PossibilitiesOS.Add(new_location)

            # Set name
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_location.Name.set_String(wsHandle, mkstr_name)

            # Set alias if provided
            if alias:
                mkstr_alias = TsStringUtils.MakeString(alias, wsHandle)
                new_location.Abbreviation.set_String(wsHandle, mkstr_alias)

            # Set creation date
            new_location.DateCreated = DateTime.Now

            return new_location

    @OperationsMethod
    def Delete(self, location_or_hvo):
        """
        Delete a location from the project.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If location_or_hvo is None.

        Example:
            >>> # Delete a location
            >>> location = project.Location.Find("Old Village")
            >>> if location:
            ...     project.Location.Delete(location)

            >>> # Delete by HVO
            >>> project.Location.Delete(12345)

        Warning:
            - This is a destructive operation
            - Deletion is permanent and cannot be undone
            - Deletes all sublocations recursively
            - Any references to this location will be removed
            - Data collected at this location will lose location reference

        Notes:
            - Deletion cascades to all sublocations
            - Parent-child relationships are automatically cleaned up
            - References from other objects are removed
            - Use with caution on shared projects

        See Also:
            Create, GetSublocations
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)

        # Get the parent or top-level list
        parent = self.GetRegion(location)

        with self._TransactionCM("Delete location"):
            if parent:
                # Remove from parent's sublocations
                parent.SubPossibilitiesOS.Remove(location)
            else:
                # Remove from top-level list
                location_list = self.project.lp.LocationsOA
                if location_list:
                    location_list.PossibilitiesOS.Remove(location)

    @OperationsMethod
    def Find(self, name):
        """
        Find a location by its name.

        Args:
            name (str): The location name to search for (case-insensitive).

        Returns:
            ICmLocation or None: The location object if found, None otherwise.

        Raises:
            FP_NullParameterError: If name is None.

        Example:
            >>> # Find by name
            >>> location = project.Location.Find("Barasana Village")
            >>> if location:
            ...     coords = project.Location.GetCoordinates(location)
            ...     print(f"Found at: {coords}")
            Found at: (-1.2345, -70.6789)

            >>> # Case-insensitive search
            >>> location = project.Location.Find("barasana village")
            >>> print(location is not None)
            True

            >>> # Not found
            >>> missing = project.Location.Find("Nonexistent Place")
            >>> print(missing)
            None

        Notes:
            - Search is case-insensitive
            - Searches in default analysis writing system
            - Returns first match only
            - Returns None if not found (doesn't raise exception)
            - For multilingual searches, iterate GetAll() manually
            - Searches both top-level and nested locations

        See Also:
            Exists, GetAll, GetName
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        target = normalize_match_key(name.strip(), casefold=True)
        wsHandle = self.project.project.DefaultAnalWs

        # Search through all locations
        for location in self.GetAll():
            location_name = ITsString(location.Name.get_String(wsHandle)).Text
            if normalize_match_key(location_name, casefold=True) == target:
                return location

        return None

    @OperationsMethod
    def Exists(self, name):
        """
        Check if a location with the given name exists.

        Args:
            name (str): The location name to check.

        Returns:
            bool: True if location exists, False otherwise.

        Example:
            >>> if project.Location.Exists("Barasana Village"):
            ...     print("Village location exists")
            Village location exists

            >>> if not project.Location.Exists("Unknown Place"):
            ...     location = project.Location.Create("Unknown Place")

        Notes:
            - Search is case-insensitive
            - Returns False for empty or whitespace-only names
            - More efficient than Find() when you only need existence check
            - Use Find() if you need the actual location object

        See Also:
            Find, Create
        """
        if not name or (isinstance(name, str) and not name.strip()):
            return False

        return self.Find(name) is not None

    # --- Name and Alias Operations ---

    @OperationsMethod
    def GetName(self, location_or_hvo, wsHandle=None):
        """
        Get the name of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The location name, or empty string if not set.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> name = project.Location.GetName(location)
            >>> print(name)
            Barasana Village

            >>> # Get name in specific writing system
            >>> name_es = project.Location.GetName(location,
            ...                                     project.WSHandle('es'))
            >>> print(name_es)
            Pueblo Barasana

        Notes:
            - Returns empty string if name not set in specified writing system
            - Names can be set in multiple writing systems
            - Default writing system is the default analysis WS

        See Also:
            SetName, GetAlias
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(location.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, location_or_hvo, name, wsHandle=None):
        """
        Set the name of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If location_or_hvo or name is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Old Name")
            >>> project.Location.SetName(location, "New Name")
            >>> print(project.Location.GetName(location))
            New Name

            >>> # Set name in multiple writing systems
            >>> project.Location.SetName(location, "Village", "en")
            >>> project.Location.SetName(location, "Pueblo", "es")

        Notes:
            - Empty string is allowed (clears the name in that WS)
            - Name is stored in the specified writing system
            - Does not affect other writing systems
            - Use different writing systems for multilingual names

        See Also:
            GetName, SetAlias
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location_or_hvo, "location_or_hvo")
        self._ValidateParam(name, "name")

        location = self.__ResolveObject(location_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM(f"Set location name '{name}'"):
            mkstr = TsStringUtils.MakeString(name, wsHandle)
            location.Name.set_String(wsHandle, mkstr)

            # Update modification date
            location.DateModified = DateTime.Now

    @OperationsMethod
    def GetAlias(self, location_or_hvo, wsHandle=None):
        """
        Get the alias/abbreviation of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The location alias, or empty string if not set.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Vaupés Department")
            >>> alias = project.Location.GetAlias(location)
            >>> print(alias)
            VAU

            >>> # Common use case: display alias when available
            >>> name = project.Location.GetName(location)
            >>> alias = project.Location.GetAlias(location)
            >>> display = f"{name} ({alias})" if alias else name
            >>> print(display)
            Vaupés Department (VAU)

        Notes:
            - Returns empty string if alias not set in specified writing system
            - Aliases are typically abbreviations or short codes
            - Useful for map labels and compact displays
            - Can be multilingual (different alias per writing system)

        See Also:
            SetAlias, GetName
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        alias = ITsString(location.Abbreviation.get_String(wsHandle)).Text
        return alias or ""

    @OperationsMethod
    def SetAlias(self, location_or_hvo, alias, wsHandle=None):
        """
        Set the alias/abbreviation of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            alias (str): The new alias.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If location_or_hvo or alias is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Vaupés Department")
            >>> project.Location.SetAlias(location, "VAU")
            >>> print(project.Location.GetAlias(location))
            VAU

            >>> # Clear alias
            >>> project.Location.SetAlias(location, "")

        Notes:
            - Empty string is allowed (clears the alias)
            - Alias is stored in the specified writing system
            - Common aliases include state/province codes, airport codes, etc.
            - Keep aliases short for display purposes

        See Also:
            GetAlias, SetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location_or_hvo, "location_or_hvo")
        self._ValidateParam(alias, "alias")

        location = self.__ResolveObject(location_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM(f"Set location alias '{alias}'"):
            mkstr = TsStringUtils.MakeString(alias, wsHandle)
            location.Abbreviation.set_String(wsHandle, mkstr)

            # Update modification date
            location.DateModified = DateTime.Now

    # --- Geographic Properties ---

    @OperationsMethod
    def GetCoordinates(self, location_or_hvo):
        """
        Get the geographic coordinates (latitude, longitude) of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.

        Returns:
            tuple or None: A tuple of (latitude, longitude) as floats in decimal
                degrees, or None if coordinates are not set.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> coords = project.Location.GetCoordinates(location)
            >>> if coords:
            ...     lat, lon = coords
            ...     print(f"Latitude: {lat}, Longitude: {lon}")
            Latitude: -1.2345, Longitude: -70.6789

            >>> # Check if coordinates are set
            >>> if project.Location.GetCoordinates(location):
            ...     print("Location has coordinates")
            ... else:
            ...     print("Location coordinates not set")

        Notes:
            - Returns None if either latitude or longitude is not set
            - Latitude range: -90 (South Pole) to +90 (North Pole)
            - Longitude range: -180 (West) to +180 (East)
            - Coordinates are stored as GenDate fields in LCM
            - Use decimal degrees format (not degrees/minutes/seconds)

        See Also:
            SetCoordinates, GetElevation, FindByCoordinates
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)

        # Coordinates are stored in GenDate fields
        # Latitude in GenDate.GenDateVal1
        # Longitude in GenDate.GenDateVal2
        if hasattr(location, "DateOfEvent") and location.DateOfEvent:
            date_info = location.DateOfEvent
            if hasattr(date_info, "GenDateVal1") and hasattr(date_info, "GenDateVal2"):
                lat = date_info.GenDateVal1
                lon = date_info.GenDateVal2
                # Check if valid coordinates (both non-zero or explicitly set)
                if lat != 0 or lon != 0:
                    return (float(lat), float(lon))

        return None

    @OperationsMethod
    def SetCoordinates(self, location_or_hvo, latitude, longitude):
        """
        Set the geographic coordinates of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            latitude (float): Latitude in decimal degrees (-90 to +90).
            longitude (float): Longitude in decimal degrees (-180 to +180).

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If location_or_hvo, latitude, or longitude is None.
            FP_ParameterError: If location doesn't exist or coordinates are invalid.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> # Set coordinates (latitude, longitude in decimal degrees)
            >>> project.Location.SetCoordinates(location, -1.2345, -70.6789)
            >>> coords = project.Location.GetCoordinates(location)
            >>> print(coords)
            (-1.2345, -70.6789)

            >>> # Set coordinates for a city
            >>> bogota = project.Location.Create("Bogotá", "en")
            >>> project.Location.SetCoordinates(bogota, 4.7110, -74.0721)

        Notes:
            - Latitude must be between -90 and +90
            - Longitude must be between -180 and +180
            - Use negative values for South latitude and West longitude
            - Use decimal degrees, not degrees/minutes/seconds
            - Coordinates are stored in GenDate fields
            - Use (0, 0) to clear coordinates (though this is valid for Gulf of Guinea)

        See Also:
            GetCoordinates, SetElevation, FindByCoordinates
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location_or_hvo, "location_or_hvo")
        self._ValidateParam(latitude, "latitude")
        self._ValidateParam(longitude, "longitude")

        # Validate coordinate ranges
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError):
            raise FP_ParameterError("Latitude and longitude must be numeric")

        if lat < -90 or lat > 90:
            raise FP_ParameterError(f"Latitude must be between -90 and +90 (got {lat})")
        if lon < -180 or lon > 180:
            raise FP_ParameterError(f"Longitude must be between -180 and +180 (got {lon})")

        location = self.__ResolveObject(location_or_hvo)

        # Create or update GenDate for coordinates
        with self._TransactionCM("Set location coordinates"):
            if not hasattr(location, "DateOfEvent") or not location.DateOfEvent:
                # Need to create GenDate - this may require factory
                # For now, set directly if property exists
                if hasattr(location, "DateOfEvent"):
                    # Try to initialize the GenDate object
                    from SIL.LCModel import GenDate

                    location.DateOfEvent = GenDate()

            if hasattr(location, "DateOfEvent") and location.DateOfEvent:
                location.DateOfEvent.GenDateVal1 = int(lat * 10000)  # Store with precision
                location.DateOfEvent.GenDateVal2 = int(lon * 10000)

            # Update modification date
            location.DateModified = DateTime.Now

    @OperationsMethod
    def GetElevation(self, location_or_hvo):
        """
        Get the elevation of a location in meters above sea level.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.

        Returns:
            int or None: Elevation in meters, or None if not set.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> elevation = project.Location.GetElevation(location)
            >>> if elevation is not None:
            ...     print(f"Elevation: {elevation} meters above sea level")
            Elevation: 150 meters above sea level

            >>> # Check if elevation is set
            >>> if project.Location.GetElevation(location) is None:
            ...     print("Elevation not recorded")

        Notes:
            - Returns None if elevation is not set
            - Elevation is in meters above sea level
            - Negative values indicate below sea level
            - Stored as an integer
            - Typical range: -500 to +9000 meters for inhabited areas

        See Also:
            SetElevation, GetCoordinates
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)

        # Elevation might be stored in a numeric field
        # Check if the field exists and has a value
        if hasattr(location, "Elevation"):
            elev = location.Elevation
            if elev != 0:  # Assume 0 means not set
                return int(elev)

        return None

    @OperationsMethod
    def SetElevation(self, location_or_hvo, elevation):
        """
        Set the elevation of a location in meters above sea level.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            elevation (int): Elevation in meters above sea level.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If location_or_hvo or elevation is None.
            FP_ParameterError: If location doesn't exist or elevation is invalid.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> # Set elevation (150 meters above sea level)
            >>> project.Location.SetElevation(location, 150)
            >>> print(project.Location.GetElevation(location))
            150

            >>> # Below sea level location
            >>> dead_sea = project.Location.Create("Dead Sea Shore", "en")
            >>> project.Location.SetElevation(dead_sea, -430)

            >>> # Mountain village
            >>> mountain = project.Location.Create("Cusco", "en")
            >>> project.Location.SetElevation(mountain, 3400)

        Notes:
            - Elevation is in meters above sea level
            - Negative values for locations below sea level
            - Must be an integer (will be converted if float)
            - Use 0 to clear elevation (though this is valid for sea level)
            - Typical range: -500 to +9000 meters for inhabited areas

        See Also:
            GetElevation, SetCoordinates
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location_or_hvo, "location_or_hvo")
        self._ValidateParam(elevation, "elevation")

        # Validate elevation
        try:
            elev = int(elevation)
        except (TypeError, ValueError):
            raise FP_ParameterError("Elevation must be numeric")

        # Reasonable range check (deepest inhabited to highest)
        if elev < -500 or elev > 10000:
            logger.warning(f"Elevation {elev} is outside typical range (-500 to 10000m)")

        location = self.__ResolveObject(location_or_hvo)

        # Set elevation if field exists
        with self._TransactionCM("Set location elevation"):
            if hasattr(location, "Elevation"):
                location.Elevation = elev
            else:
                logger.warning("Elevation field not available on ICmLocation")

            # Update modification date
            location.DateModified = DateTime.Now

    # --- Description ---

    @OperationsMethod
    def GetDescription(self, location_or_hvo, wsHandle=None):
        """
        Get the description of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The location description, or empty string if not set.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> desc = project.Location.GetDescription(location)
            >>> print(desc)
            Small village on the Papurí River, accessible by boat.
            Primary language: Barasana. Population approximately 200.

        Notes:
            - Returns empty string if description not set
            - Description can be lengthy (multiple paragraphs)
            - Useful for recording location details, access info, etc.
            - Can be multilingual (different description per writing system)

        See Also:
            SetDescription, GetName
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        if hasattr(location, "Description"):
            desc = ITsString(location.Description.get_String(wsHandle)).Text
            return desc or ""

        return ""

    @OperationsMethod
    def SetDescription(self, location_or_hvo, description, wsHandle=None):
        """
        Set the description of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            description (str): The new description text.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If location_or_hvo or description is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> desc = ("Small village on the Papurí River.\\n"
            ...         "Accessible by boat from Mitú.\\n"
            ...         "Primary language: Barasana.")
            >>> project.Location.SetDescription(location, desc)

            >>> # Multilingual descriptions
            >>> project.Location.SetDescription(location, desc_en, "en")
            >>> project.Location.SetDescription(location, desc_es, "es")

        Notes:
            - Empty string is allowed (clears the description)
            - Description is stored in the specified writing system
            - Use newlines for formatting if needed
            - Good place for access info, language info, population, etc.

        See Also:
            GetDescription, SetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location_or_hvo, "location_or_hvo")
        self._ValidateParam(description, "description")

        location = self.__ResolveObject(location_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM("Set location description"):
            if hasattr(location, "Description"):
                mkstr = TsStringUtils.MakeString(description, wsHandle)
                location.Description.set_String(wsHandle, mkstr)

                # Update modification date
                location.DateModified = DateTime.Now

    # --- Hierarchical Operations ---

    @OperationsMethod
    def GetRegion(self, location_or_hvo):
        """
        Get the parent region of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.

        Returns:
            ICmLocation or None: The parent location, or None if top-level.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> # Get parent region
            >>> village = project.Location.Find("Barasana Village")
            >>> region = project.Location.GetRegion(village)
            >>> if region:
            ...     region_name = project.Location.GetName(region)
            ...     print(f"Part of: {region_name}")
            Part of: Papurí River Area

            >>> # Top-level locations have no parent
            >>> country = project.Location.Find("Colombia")
            >>> parent = project.Location.GetRegion(country)
            >>> print(parent)
            None

        Notes:
            - Returns None for top-level locations
            - Parent is determined by ownership hierarchy
            - Use for building breadcrumb navigation
            - Locations form a tree structure (country → state → city, etc.)

        See Also:
            SetRegion, GetSublocations, CreateSublocation
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)
        owner = location.Owner

        # Check if owner is a location (sublocation) or the list (top-level).
        # Cast through ICmLocation when it is, so callers can reach
        # SubPossibilitiesOS / Name / Abbreviation on the parent without
        # the AttributeError that the base ICmObject return would cause.
        # Same Owner-without-cast bug class as #97/#98/#129/#151. (issue #157)
        if owner and hasattr(owner, "ClassName"):
            if owner.ClassName == "CmLocation":
                return ICmLocation(owner)

        return None

    @OperationsMethod
    def SetRegion(self, location_or_hvo, parent_location_or_hvo):
        """
        Set the parent region of a location (move it in the hierarchy).

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO to move.
            parent_location_or_hvo: The new parent ICmLocation object or HVO,
                or None to make it top-level.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If trying to make a location its own parent,
                or creating circular hierarchy.

        Example:
            >>> # Move a location to a different region
            >>> village = project.Location.Find("Barasana Village")
            >>> new_region = project.Location.Find("Vaupés Department")
            >>> project.Location.SetRegion(village, new_region)

            >>> # Make a location top-level
            >>> project.Location.SetRegion(village, None)

        Warning:
            - Cannot make a location its own parent
            - Cannot create circular hierarchies (A → B → A)
            - Check for circular references before moving

        Notes:
            - Moves location from old parent to new parent
            - Pass None to make location top-level
            - Automatically updates old and new parent's sublocation lists
            - Use for reorganizing location hierarchies

        See Also:
            GetRegion, CreateSublocation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)

        # Resolve new parent
        new_parent = None
        if parent_location_or_hvo is not None:
            new_parent = self.__ResolveObject(parent_location_or_hvo)

            # Check for self-reference
            if new_parent == location:
                raise FP_ParameterError("Cannot make a location its own parent")

            # Check for circular reference
            current = new_parent
            while current:
                if current == location:
                    raise FP_ParameterError("Cannot create circular hierarchy")
                current = self.GetRegion(current)

        # Get current parent
        old_parent = self.GetRegion(location)

        # Remove from old parent
        with self._TransactionCM("Set location region"):
            if old_parent:
                old_parent.SubPossibilitiesOS.Remove(location)
            else:
                # Remove from top-level list
                location_list = self.project.lp.LocationsOA
                if location_list and location in location_list.PossibilitiesOS:
                    location_list.PossibilitiesOS.Remove(location)

            # Add to new parent
            if new_parent:
                new_parent.SubPossibilitiesOS.Add(location)
            else:
                # Add to top-level list
                location_list = self.project.lp.LocationsOA
                if location_list:
                    location_list.PossibilitiesOS.Add(location)

            # Update modification date
            location.DateModified = DateTime.Now

    @OperationsMethod
    def GetSublocations(self, location_or_hvo, recursive=True):
        """
        Get the sublocations of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            recursive (bool): If True (default), returns every descendant
                location (depth-first, parents before children). If False,
                returns only direct children.

        Returns:
            list: List of ICmLocation objects (empty list if none).

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> region = project.Location.Find("Vaupés Department")
            >>> for subloc in project.Location.GetSublocations(region):
            ...     print(project.Location.GetName(subloc))   # All descendants

            >>> # Direct children only
            >>> for subloc in project.Location.GetSublocations(region, recursive=False):
            ...     print(project.Location.GetName(subloc))

        See Also:
            GetRegion, CreateSublocation, SetRegion
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)

        if not hasattr(location, "SubPossibilitiesOS"):
            return []

        if not recursive:
            return [ICmLocation(child) for child in location.SubPossibilitiesOS]

        result = []
        def walk(collection):
            for raw in collection:
                child = ICmLocation(raw)
                result.append(child)
                if child.SubPossibilitiesOS.Count > 0:
                    walk(child.SubPossibilitiesOS)
        walk(location.SubPossibilitiesOS)
        return result

    @OperationsMethod
    def CreateSublocation(self, parent_location_or_hvo, name, wsHandle=None, alias=None):
        """
        Create a new sublocation under a parent location.

        Args:
            parent_location_or_hvo: The parent ICmLocation object or HVO.
            name (str): The name of the new sublocation.
            wsHandle: Optional writing system handle. Defaults to analysis WS.
            alias (str): Optional alias/abbreviation.

        Returns:
            ICmLocation: The newly created sublocation object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If parent_location_or_hvo or name is None.
            FP_ParameterError: If name is empty or parent doesn't exist.

        Example:
            >>> # Create hierarchical locations
            >>> country = project.Location.Create("Colombia", "en")
            >>> department = project.Location.CreateSublocation(
            ...     country, "Vaupés Department", "en", alias="VAU")
            >>> municipality = project.Location.CreateSublocation(
            ...     department, "Mitú", "en")

            >>> # Verify hierarchy
            >>> parent = project.Location.GetRegion(municipality)
            >>> print(project.Location.GetName(parent))
            Vaupés Department

        Notes:
            - Creates location as child of parent
            - Parent-child relationship is established automatically
            - Sublocation inherits no properties from parent (coordinates, etc.)
            - Set coordinates and other properties separately
            - Can create multi-level hierarchies (country → state → city → village)

        See Also:
            Create, SetRegion, GetSublocations
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(parent_location_or_hvo, "parent_location_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        parent = self.__ResolveObject(parent_location_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Create the new location using the factory
        factory = self.project.project.ServiceLocator.GetService(ICmLocationFactory)
        new_location = factory.Create()

        # Add to parent's sublocations (must be done before setting properties)
        parent.SubPossibilitiesOS.Add(new_location)

        # Set name
        mkstr_name = TsStringUtils.MakeString(name, wsHandle)
        new_location.Name.set_String(wsHandle, mkstr_name)

        # Set alias if provided
        if alias:
            mkstr_alias = TsStringUtils.MakeString(alias, wsHandle)
            new_location.Abbreviation.set_String(wsHandle, mkstr_alias)

        # Set creation date
        new_location.DateCreated = DateTime.Now

        return new_location

    @OperationsMethod
    def Duplicate(self, location_or_hvo, insert_after=True, deep=True):
        """
        Duplicate a location, creating a new copy with a new GUID.

        Args:
            location_or_hvo: The ICmLocation object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source location.
                                If False, insert at end of parent's sublocations list.
            deep (bool): If True (default), also duplicate owned objects (sublocations).
                        If False, only copy simple properties and references.

        Returns:
            ICmLocation: The newly created duplicate location with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If location_or_hvo is None.

        Example:
            >>> # Shallow duplicate (no sublocations)
            >>> location = project.Location.Find("Barasana Village")
            >>> dup = project.Location.Duplicate(location)
            >>> print(f"Original: {project.Location.GetGuid(location)}")
            >>> print(f"Duplicate: {project.Location.GetGuid(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321

            >>> # Deep duplicate (includes all sublocations)
            >>> region = project.Location.Find("Vaupés Department")
            >>> deep_dup = project.Location.Duplicate(region, deep=True)
            >>> print(f"Sublocations: {len(project.Location.GetSublocations(deep_dup))}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original location's position
            - Simple properties copied: Name, Abbreviation (alias), Description
            - Geographic properties copied: coordinates (latitude/longitude), elevation
            - Owned objects (deep=True): SubPossibilitiesOS (sublocations)
            - DateCreated is set to current time (not copied from source)
            - DateModified is set automatically

        See Also:
            Create, Delete, GetGuid, GetSublocations
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location_or_hvo, "location_or_hvo")

        # Get source location
        source = self.__ResolveObject(location_or_hvo)

        # Determine parent (owner)
        parent = self.GetRegion(source)

        # Create new location using factory (auto-generates new GUID)
        factory = self.project.project.ServiceLocator.GetService(ICmLocationFactory)
        duplicate = factory.Create()

        # Determine insertion position and add to parent FIRST
        if parent:
            # Parent is another location (sublocation)
            if insert_after:
                source_index = parent.SubPossibilitiesOS.IndexOf(source)
                parent.SubPossibilitiesOS.Insert(source_index + 1, duplicate)
            else:
                parent.SubPossibilitiesOS.Add(duplicate)
        else:
            # Parent is the top-level list
            location_list = self.project.lp.LocationsOA
            if location_list:
                if insert_after:
                    source_index = location_list.PossibilitiesOS.IndexOf(source)
                    location_list.PossibilitiesOS.Insert(source_index + 1, duplicate)
                else:
                    location_list.PossibilitiesOS.Add(duplicate)

        # Copy simple MultiString properties
        duplicate.Name.CopyAlternatives(source.Name)
        duplicate.Abbreviation.CopyAlternatives(source.Abbreviation)
        if hasattr(source, "Description"):
            duplicate.Description.CopyAlternatives(source.Description)

        # Copy coordinates and elevation
        coords = self.GetCoordinates(source)
        if coords:
            lat, lon = coords
            self.SetCoordinates(duplicate, lat, lon)

        if hasattr(source, "DateOfEvent") and source.DateOfEvent:
            if hasattr(duplicate, "DateOfEvent"):
                duplicate.DateOfEvent = source.DateOfEvent

        elevation = self.GetElevation(source)
        if elevation is not None:
            if hasattr(duplicate, "Elevation"):
                duplicate.Elevation = elevation

        # Set creation date
        duplicate.DateCreated = DateTime.Now

        # Handle owned objects if deep=True
        if deep:
            # Duplicate sublocations into the NEW duplicate (not the original's parent)
            if hasattr(source, "SubPossibilitiesOS"):
                for sublocation in source.SubPossibilitiesOS:
                    self._DuplicateSublocationInto(sublocation, duplicate, deep=True)

        return duplicate

    def _DuplicateSublocationInto(self, source_loc, parent_dup, deep=True):
        """Duplicate a sublocation into the specified parent's SubPossibilitiesOS."""
        factory = self.project.project.ServiceLocator.GetService(ICmLocationFactory)
        dup_loc = factory.Create()
        parent_dup.SubPossibilitiesOS.Add(dup_loc)

        # Copy properties
        dup_loc.Name.CopyAlternatives(source_loc.Name)
        dup_loc.Abbreviation.CopyAlternatives(source_loc.Abbreviation)
        if hasattr(source_loc, "Description"):
            dup_loc.Description.CopyAlternatives(source_loc.Description)

        coords = self.GetCoordinates(source_loc)
        if coords:
            lat, lon = coords
            self.SetCoordinates(dup_loc, lat, lon)

        if hasattr(source_loc, "DateOfEvent") and source_loc.DateOfEvent:
            if hasattr(dup_loc, "DateOfEvent"):
                dup_loc.DateOfEvent = source_loc.DateOfEvent

        elevation = self.GetElevation(source_loc)
        if elevation is not None:
            if hasattr(dup_loc, "Elevation"):
                dup_loc.Elevation = elevation

        dup_loc.DateCreated = DateTime.Now

        # Recurse into nested sublocations
        if deep and hasattr(source_loc, "SubPossibilitiesOS"):
            for nested_loc in source_loc.SubPossibilitiesOS:
                self._DuplicateSublocationInto(nested_loc, dup_loc, deep=True)

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get syncable properties for cross-project synchronization.

        Args:
            item: The ICmLocation object

        Returns:
            dict: Dictionary of syncable properties
        """
        self._ValidateParam(item, "item")

        location = self.__ResolveObject(item)
        wsHandle = self.project.project.DefaultAnalWs

        props = {}
        props["Name"] = ITsString(location.Name.get_String(wsHandle)).Text or ""
        props["Abbreviation"] = ITsString(location.Abbreviation.get_String(wsHandle)).Text or ""
        if hasattr(location, "Description"):
            props["Description"] = ITsString(location.Description.get_String(wsHandle)).Text or ""

        coords = self.GetCoordinates(location)
        props["Coordinates"] = coords if coords else None
        props["Elevation"] = self.GetElevation(location)

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two locations and return detailed differences.

        Args:
            item1: First location
            item2: Second location
            ops1: Operations for item1's project (defaults to self)
            ops2: Operations for item2's project (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
        """
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

    # --- Metadata Operations ---

    @OperationsMethod
    def GetGuid(self, location_or_hvo):
        """
        Get the GUID (Globally Unique Identifier) of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.

        Returns:
            System.Guid: The location's GUID.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> guid = project.Location.GetGuid(location)
            >>> print(guid)
            a1b2c3d4-e5f6-7890-abcd-ef1234567890

            >>> # Use GUID to retrieve location later
            >>> location2 = project.Object(guid)
            >>> print(project.Location.GetName(location2))
            Barasana Village

        Notes:
            - GUIDs are unique across all FLEx projects
            - GUIDs are persistent (don't change)
            - Useful for linking locations across projects
            - Can be used with FLExProject.Object() to retrieve location

        See Also:
            FLExProject.Object
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)
        return location.Guid

    @OperationsMethod
    def GetDateCreated(self, location_or_hvo):
        """
        Get the creation date of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.

        Returns:
            System.DateTime or None: The creation date/time, or None if not set.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> date = project.Location.GetDateCreated(location)
            >>> if date:
            ...     print(f"Created: {date}")
            Created: 11/23/2025 10:30:45 AM

            >>> # Sort locations by creation date
            >>> locations = project.Location.GetAll()
            >>> sorted_locs = sorted(locations,
            ...     key=lambda l: project.Location.GetDateCreated(l) or DateTime.MinValue)

        Notes:
            - DateCreated is set automatically when location is created
            - Returns System.DateTime object
            - Can be None for locations without creation date
            - Use for tracking when locations were added to project

        See Also:
            GetDateModified, Create
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)

        if hasattr(location, "DateCreated"):
            return location.DateCreated

        return None

    @OperationsMethod
    def GetDateModified(self, location_or_hvo):
        """
        Get the last modification date of a location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.

        Returns:
            System.DateTime or None: The modification date/time, or None if not set.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist.

        Example:
            >>> location = project.Location.Find("Barasana Village")
            >>> modified = project.Location.GetDateModified(location)
            >>> if modified:
            ...     print(f"Last modified: {modified}")
            Last modified: 11/23/2025 2:15:30 PM

            >>> # Find recently modified locations
            >>> from System import DateTime
            >>> one_week_ago = DateTime.Now.AddDays(-7)
            >>> locations = project.Location.GetAll()
            >>> recent = [l for l in locations
            ...     if project.Location.GetDateModified(l) and
            ...        project.Location.GetDateModified(l) > one_week_ago]

        Notes:
            - DateModified is updated when properties change
            - Returns System.DateTime object
            - May be None if location has never been modified
            - Useful for tracking location updates

        See Also:
            GetDateCreated, SetName, SetCoordinates
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)

        if hasattr(location, "DateModified"):
            return location.DateModified

        return None

    # --- Query Operations ---

    @OperationsMethod
    def FindByCoordinates(self, latitude, longitude, radius_km=10):
        """
        Find locations near the specified coordinates.

        Args:
            latitude (float): Target latitude in decimal degrees.
            longitude (float): Target longitude in decimal degrees.
            radius_km (float): Search radius in kilometers. Defaults to 10 km.

        Returns:
            list: List of (ICmLocation, distance_km) tuples sorted by distance,
                where distance_km is the distance in kilometers from the target.

        Raises:
            FP_NullParameterError: If latitude or longitude is None.
            FP_ParameterError: If coordinates or radius are invalid.

        Example:
            >>> # Find locations within 50 km of a point
            >>> nearby = project.Location.FindByCoordinates(-1.23, -70.67, radius_km=50)
            >>> for location, distance in nearby:
            ...     name = project.Location.GetName(location)
            ...     print(f"{name}: {distance:.1f} km away")
            Barasana Village: 2.3 km away
            Neighboring Village: 15.7 km away
            Mitú: 45.2 km away

            >>> # Find exact location (very small radius)
            >>> exact = project.Location.FindByCoordinates(
            ...     -1.2345, -70.6789, radius_km=0.1)

        Notes:
            - Uses Haversine formula for great-circle distance
            - Only returns locations that have coordinates set
            - Results are sorted by distance (nearest first)
            - Distance is approximate (assumes spherical Earth)
            - Radius of 0 will find only exact matches (unlikely)
            - For large radii (>1000 km), consider Earth's curvature limitations

        See Also:
            GetCoordinates, GetNearby
        """
        self._ValidateParam(latitude, "latitude")
        self._ValidateParam(longitude, "longitude")

        # Validate inputs
        try:
            lat = float(latitude)
            lon = float(longitude)
            radius = float(radius_km)
        except (TypeError, ValueError):
            raise FP_ParameterError("Coordinates and radius must be numeric")

        if lat < -90 or lat > 90:
            raise FP_ParameterError("Latitude must be between -90 and +90")
        if lon < -180 or lon > 180:
            raise FP_ParameterError("Longitude must be between -180 and +180")
        if radius < 0:
            raise FP_ParameterError("Radius must be non-negative")

        results = []

        # Search through all locations
        for location in self.GetAll():
            coords = self.GetCoordinates(location)
            if coords:
                loc_lat, loc_lon = coords
                distance = self.__HaversineDistance(lat, lon, loc_lat, loc_lon)
                if distance <= radius:
                    results.append((location, distance))

        # Sort by distance
        results.sort(key=lambda x: x[1])

        return results

    @OperationsMethod
    def GetNearby(self, location_or_hvo, radius_km=50):
        """
        Get all locations near a given location.

        Args:
            location_or_hvo: Either an ICmLocation object or its HVO.
            radius_km (float): Search radius in kilometers. Defaults to 50 km.

        Returns:
            list: List of (ICmLocation, distance_km) tuples sorted by distance,
                excluding the reference location itself.

        Raises:
            FP_NullParameterError: If location_or_hvo is None.
            FP_ParameterError: If location doesn't exist, has no coordinates,
                or radius is invalid.

        Example:
            >>> # Find locations near a village
            >>> village = project.Location.Find("Barasana Village")
            >>> nearby = project.Location.GetNearby(village, radius_km=30)
            >>> for location, distance in nearby:
            ...     name = project.Location.GetName(location)
            ...     print(f"{name}: {distance:.1f} km away")
            Neighboring Village: 15.7 km away
            Another Village: 22.3 km away

            >>> # Find all locations in the same area (larger radius)
            >>> regional = project.Location.GetNearby(village, radius_km=200)
            >>> print(f"Found {len(regional)} locations in the region")

        Notes:
            - Requires reference location to have coordinates set
            - Reference location is excluded from results
            - Results are sorted by distance (nearest first)
            - Uses Haversine formula for distance calculation
            - Only includes locations that have coordinates

        See Also:
            FindByCoordinates, GetCoordinates
        """
        self._ValidateParam(location_or_hvo, "location_or_hvo")

        location = self.__ResolveObject(location_or_hvo)

        # Get coordinates of reference location
        coords = self.GetCoordinates(location)
        if not coords:
            raise FP_ParameterError("Reference location must have coordinates set")

        lat, lon = coords

        # Find nearby locations
        nearby = self.FindByCoordinates(lat, lon, radius_km)

        # Exclude the reference location itself
        nearby = [(loc, dist) for loc, dist in nearby if loc != location]

        return nearby

    # --- Private Helper Methods ---

    def __ResolveObject(self, location_or_hvo):
        """
        Resolve HVO or object to ICmLocation.

        Args:
            location_or_hvo: Either an ICmLocation object or an HVO (int).

        Returns:
            ICmLocation: The resolved location object.

        Raises:
            FP_ParameterError: If HVO doesn't refer to a location.
        """
        if isinstance(location_or_hvo, int):
            obj = self.project.Object(location_or_hvo)
            if not isinstance(obj, ICmLocation):
                raise FP_ParameterError("HVO does not refer to a location")
            return obj
        return location_or_hvo

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

    def __HaversineDistance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great-circle distance between two points on Earth.

        Uses the Haversine formula to calculate distance in kilometers.

        Args:
            lat1, lon1: First point coordinates (decimal degrees)
            lat2, lon2: Second point coordinates (decimal degrees)

        Returns:
            float: Distance in kilometers
        """
        # Earth's radius in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c

        return distance
