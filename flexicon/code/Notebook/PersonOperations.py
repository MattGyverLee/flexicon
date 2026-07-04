#
#   PersonOperations.py
#
#   Class: PersonOperations
#          Person operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import FLEx LCM types
from SIL.LCModel import (
    ICmPerson,
    ICmPersonFactory,
    ICmPersonRepository,
    ICmPossibility,
    ICmPossibilityRepository,
    ICmLocation,
    ILangProject,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key


class PersonOperations(BaseOperations):
    """
    This class provides operations for managing people (consultants, speakers,
    researchers) in a FieldWorks project.

    People are stored as ICmPerson objects and can represent consultants,
    native speakers, researchers, or any other individuals associated with
    the linguistic data collection and analysis.

    This class should be accessed via FLExProject.Person property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all people
        for person in project.Person.GetAll():
            name = project.Person.GetName(person)
            print(name)

        # Create a new person
        person = project.Person.Create("John Smith")

        # Set properties
        project.Person.SetEmail(person, "john.smith@example.com")
        project.Person.SetDateOfBirth(person, "1985-03-15")
        project.Person.SetGender(person, "Male")

        # Add contact information
        project.Person.SetPhone(person, "+1-555-123-4567")
        project.Person.SetAddress(person, "123 Main St, City, Country")

        # Add notes
        project.Person.AddNote(person, "Primary consultant for dialect study")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize PersonOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all people in the project.

        This method returns an iterator over all ICmPerson objects in the
        project database, allowing iteration over all registered people.

        Yields:
            ICmPerson: Each person object in the project

        Example:
            >>> for person in project.Person.GetAll():
            ...     name = project.Person.GetName(person)
            ...     email = project.Person.GetEmail(person)
            ...     print(f"{name}: {email}")
            John Smith: john.smith@example.com
            Maria Garcia: maria.garcia@example.com
            Ahmed Hassan: ahmed.hassan@example.com

        Notes:
            - Returns an iterator for memory efficiency
            - People are returned in database order
            - Includes all person types (consultants, researchers, speakers)
            - Use GetName() to access the display name

        See Also:
            Find, Create, GetName
        """
        return self.project.ObjectsIn(ICmPersonRepository)

    @OperationsMethod
    def Create(self, name, wsHandle=None):
        """
        Create a new person in the FLEx project.

        Args:
            name (str): The full name of the person
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            ICmPerson: The newly created person object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If name is None
            FP_ParameterError: If name is empty

        Example:
            >>> # Create a basic person
            >>> person = project.Person.Create("John Smith")
            >>> print(project.Person.GetName(person))
            John Smith

            >>> # Create with specific writing system
            >>> person = project.Person.Create("María García",
            ...                                 project.WSHandle('es'))

            >>> # Create and set additional properties
            >>> consultant = project.Person.Create("Ahmed Hassan")
            >>> project.Person.SetEmail(consultant, "ahmed@example.com")
            >>> project.Person.SetGender(consultant, "Male")

        Notes:
            - The person is added to the project's people collection
            - Only name is required; other properties can be set later
            - Person GUID is auto-generated
            - Use Set* methods to add contact information and other details

        See Also:
            Delete, Exists, Find, SetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        wsHandle = self.__WSHandle(wsHandle)

        # Create the new person using the factory
        with self._TransactionCM(f"Create person '{name}'"):
            factory = self.project.project.ServiceLocator.GetService(ICmPersonFactory)
            new_person = factory.Create()

            # Add person to the language project's people collection (must be done before setting properties)
            self.project.lp.PeopleOA.PossibilitiesOS.Add(new_person)

            # Set the name
            mkstr = TsStringUtils.MakeString(name, wsHandle)
            new_person.Name.set_String(wsHandle, mkstr)

            return new_person

    @OperationsMethod
    def Delete(self, person_or_hvo):
        """
        Delete a person from the FLEx project.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO (database ID)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo is None
            FP_ParameterError: If person doesn't exist

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> if person:
            ...     project.Person.Delete(person)

            >>> # Delete by HVO
            >>> project.Person.Delete(12345)

        Warning:
            - This is a destructive operation
            - All associated data (positions, notes, etc.) will be deleted
            - References from texts or lexical entries may become invalid
            - Cannot be undone
            - Person will be removed from all linked records

        Notes:
            - Deletion cascades to all owned objects
            - Consider archiving data before deletion
            - Use with caution in production databases

        See Also:
            Create, Exists
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")

        # Resolve to person object
        person = self.__ResolveObject(person_or_hvo)

        # Remove from people collection
        self.project.lp.PeopleOA.PossibilitiesOS.Remove(person)

    @OperationsMethod
    def Exists(self, name, wsHandle=None):
        """
        Check if a person with the given name exists.

        Args:
            name (str): The name to search for
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            bool: True if a person exists with this name, False otherwise

        Raises:
            FP_NullParameterError: If name is None

        Example:
            >>> if not project.Person.Exists("John Smith"):
            ...     person = project.Person.Create("John Smith")

            >>> # Check in specific writing system
            >>> if project.Person.Exists("María García", project.WSHandle('es')):
            ...     print("Spanish name exists")

        Notes:
            - Search is case-sensitive
            - Search is writing-system specific
            - Returns False for empty or whitespace-only names
            - Use Find() to get the actual person object

        See Also:
            Find, Create
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return False

        return self.Find(name, wsHandle) is not None

    @OperationsMethod
    def Find(self, name, wsHandle=None):
        """
        Find a person by name.

        Args:
            name (str): The name to search for
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            ICmPerson or None: The person object if found, None otherwise

        Raises:
            FP_NullParameterError: If name is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> if person:
            ...     email = project.Person.GetEmail(person)
            ...     print(f"Found: {email}")
            Found: john.smith@example.com

            >>> # Search in specific writing system
            >>> person = project.Person.Find("María García",
            ...                               project.WSHandle('es'))

        Notes:
            - Returns first match only
            - Search is case-sensitive
            - Search is writing-system specific
            - Returns None if not found (doesn't raise exception)
            - For partial name search, iterate GetAll() and filter

        See Also:
            Exists, GetAll, GetName
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        wsHandle = self.__WSHandle(wsHandle)

        # Search through all people
        target = normalize_match_key(name, casefold=False)
        for person in self.GetAll():
            person_name = ITsString(person.Name.get_String(wsHandle)).Text
            if normalize_match_key(person_name, casefold=False) == target:
                return person

        return None

    # --- Name Management ---

    @OperationsMethod
    def GetName(self, person_or_hvo, wsHandle=None):
        """
        Get the name of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The person's name (empty string if not set)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> name = project.Person.GetName(person)
            >>> print(name)
            John Smith

            >>> # Get in specific writing system
            >>> name_es = project.Person.GetName(person, project.WSHandle('es'))

        Notes:
            - Returns empty string if name not set
            - Returns empty string if not set in specified writing system
            - Name can be set in multiple writing systems

        See Also:
            SetName, Create
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(person.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, person_or_hvo, name, wsHandle=None):
        """
        Set the name of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            name (str): The new name
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or name is None
            FP_ParameterError: If name is empty

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> project.Person.SetName(person, "John Robert Smith")
            >>> print(project.Person.GetName(person))
            John Robert Smith

            >>> # Set in specific writing system
            >>> project.Person.SetName(person, "Juan Smith",
            ...                         project.WSHandle('es'))

        Notes:
            - Name should be the full name
            - Can be set in multiple writing systems
            - Empty names are not allowed

        See Also:
            GetName, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        person.Name.set_String(wsHandle, mkstr)

    # --- Gender ---

    @OperationsMethod
    def GetGender(self, person_or_hvo, wsHandle=None):
        """
        Get the gender of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The gender (empty string if not set)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> gender = project.Person.GetGender(person)
            >>> print(gender)
            Male

        Notes:
            - Returns empty string if gender not set
            - Gender is stored as a string field
            - Common values: "Male", "Female", "Other", but can be any text

        See Also:
            SetGender
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        gender = ITsString(person.Gender.get_String(wsHandle)).Text
        return gender or ""

    @OperationsMethod
    def SetGender(self, person_or_hvo, gender, wsHandle=None):
        """
        Set the gender of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            gender (str): The gender to set
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or gender is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> project.Person.SetGender(person, "Male")

            >>> # Clear gender
            >>> project.Person.SetGender(person, "")

        Notes:
            - Gender can be any text value
            - Common values: "Male", "Female", "Other"
            - Can be empty string to clear

        See Also:
            GetGender
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(gender, "gender")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        mkstr = TsStringUtils.MakeString(gender, wsHandle)
        person.Gender.set_String(wsHandle, mkstr)

    # --- Date of Birth ---

    @OperationsMethod
    def GetDateOfBirth(self, person_or_hvo):
        """
        Get the date of birth of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO

        Returns:
            str: Date of birth as string (empty if not set)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> dob = project.Person.GetDateOfBirth(person)
            >>> print(dob)
            1985-03-15

        Notes:
            - Returns empty string if date not set
            - Date format depends on how it was stored
            - Typically stored as ISO format (YYYY-MM-DD) or locale format

        See Also:
            SetDateOfBirth
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)

        # DateOfBirth is stored as a GenDate field
        if person.DateOfBirth:
            return str(person.DateOfBirth)
        return ""

    @OperationsMethod
    def SetDateOfBirth(self, person_or_hvo, date_str):
        """
        Set the date of birth of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            date_str (str): Date of birth as string (e.g., "1985-03-15")

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or date_str is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> project.Person.SetDateOfBirth(person, "1985-03-15")

            >>> # Clear date
            >>> project.Person.SetDateOfBirth(person, "")

        Notes:
            - Accepts various date formats
            - ISO format (YYYY-MM-DD) recommended
            - Can be empty string to clear
            - Invalid dates may raise FLEx internal errors

        See Also:
            GetDateOfBirth
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(date_str, "date_str")

        person = self.__ResolveObject(person_or_hvo)

        # DateOfBirth is a GenDate field - set as string
        person.DateOfBirth = date_str

    # --- Contact Information ---

    @OperationsMethod
    def GetEmail(self, person_or_hvo, wsHandle=None):
        """
        Get the email address of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: Email address (empty string if not set)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> email = project.Person.GetEmail(person)
            >>> print(email)
            john.smith@example.com

        Notes:
            - Returns empty string if email not set
            - No email validation is performed
            - Can store multiple emails as comma-separated values

        See Also:
            SetEmail, GetPhone
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        email = ITsString(person.Email.get_String(wsHandle)).Text
        return email or ""

    @OperationsMethod
    def SetEmail(self, person_or_hvo, email, wsHandle=None):
        """
        Set the email address of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            email (str): Email address to set
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or email is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> project.Person.SetEmail(person, "john.smith@example.com")

            >>> # Multiple emails
            >>> project.Person.SetEmail(person,
            ...     "john.smith@example.com, j.smith@work.org")

            >>> # Clear email
            >>> project.Person.SetEmail(person, "")

        Notes:
            - No email validation is performed
            - Can be empty string to clear
            - Multiple emails can be comma-separated

        See Also:
            GetEmail, SetPhone
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(email, "email")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        mkstr = TsStringUtils.MakeString(email, wsHandle)
        person.Email.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetPhone(self, person_or_hvo, wsHandle=None):
        """
        Get the phone number of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: Phone number (empty string if not set)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> phone = project.Person.GetPhone(person)
            >>> print(phone)
            +1-555-123-4567

        Notes:
            - Returns empty string if phone not set
            - No phone number validation or formatting is performed
            - Can store multiple numbers

        See Also:
            SetPhone, GetEmail
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        phone = ITsString(person.PlaceOfBirth.get_String(wsHandle)).Text
        return phone or ""

    @OperationsMethod
    def SetPhone(self, person_or_hvo, phone, wsHandle=None):
        """
        Set the phone number of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            phone (str): Phone number to set
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or phone is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> project.Person.SetPhone(person, "+1-555-123-4567")

            >>> # Multiple numbers
            >>> project.Person.SetPhone(person,
            ...     "Mobile: +1-555-123-4567, Office: +1-555-890-1234")

            >>> # Clear phone
            >>> project.Person.SetPhone(person, "")

        Notes:
            - No phone validation or formatting is performed
            - Can be empty string to clear
            - Multiple numbers can be listed

        See Also:
            GetPhone, SetEmail
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(phone, "phone")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        mkstr = TsStringUtils.MakeString(phone, wsHandle)
        person.PlaceOfBirth.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetAddress(self, person_or_hvo, wsHandle=None):
        """
        Get the address of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: Address (empty string if not set)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> address = project.Person.GetAddress(person)
            >>> print(address)
            123 Main St, City, Country

        Notes:
            - Returns empty string if address not set
            - No address format validation
            - Can be multi-line using newline characters

        See Also:
            SetAddress, GetResidences
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        # Use Abbreviation field for address storage
        address = ITsString(person.Abbreviation.get_String(wsHandle)).Text
        return address or ""

    @OperationsMethod
    def SetAddress(self, person_or_hvo, address, wsHandle=None):
        """
        Set the address of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            address (str): Address to set
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or address is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> project.Person.SetAddress(person,
            ...     "123 Main St\\nCity, State 12345\\nCountry")

            >>> # Clear address
            >>> project.Person.SetAddress(person, "")

        Notes:
            - Can be empty string to clear
            - No format validation
            - Use \\n for multi-line addresses

        See Also:
            GetAddress, AddResidence
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(address, "address")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        mkstr = TsStringUtils.MakeString(address, wsHandle)
        person.Abbreviation.set_String(wsHandle, mkstr)

    # --- Academic Information ---

    @OperationsMethod
    def GetEducation(self, person_or_hvo, wsHandle=None):
        """
        Get the education information of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: Education information (empty string if not set)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> education = project.Person.GetEducation(person)
            >>> print(education)
            PhD Linguistics, University of Example, 2010

        Notes:
            - Returns empty string if education not set
            - Can contain degrees, institutions, years, etc.
            - No specific format required

        See Also:
            SetEducation, GetPositions
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        education = ITsString(person.Description.get_String(wsHandle)).Text
        return education or ""

    @OperationsMethod
    def SetEducation(self, person_or_hvo, education, wsHandle=None):
        """
        Set the education information of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            education (str): Education information to set
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or education is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> project.Person.SetEducation(person,
            ...     "PhD Linguistics, University of Example, 2010\\n"
            ...     "MA Anthropology, State University, 2005")

            >>> # Clear education
            >>> project.Person.SetEducation(person, "")

        Notes:
            - Can be empty string to clear
            - Can be multi-line using \\n
            - No format validation

        See Also:
            GetEducation, AddPosition
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(education, "education")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        mkstr = TsStringUtils.MakeString(education, wsHandle)
        person.Description.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetPositions(self, person_or_hvo):
        """
        Get the positions/roles associated with a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO

        Returns:
            list: List of ICmPossibility objects representing positions
                  (empty list if none)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> positions = project.Person.GetPositions(person)
            >>> for pos in positions:
            ...     name = ITsString(pos.Name.BestAnalysisAlternative).Text
            ...     print(f"Position: {name}")
            Position: Consultant
            Position: Native Speaker

        Notes:
            - Returns empty list if no positions assigned
            - Positions are ICmPossibility objects from project lists
            - Typically from the Positions possibility list

        See Also:
            AddPosition
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)

        return list(person.PositionsRC)

    @OperationsMethod
    def AddPosition(self, person_or_hvo, position):
        """
        Add a position/role to a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            position: ICmPossibility object representing the position

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or position is None
            FP_ParameterError: If position is not a valid ICmPossibility

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> # Get position from project's positions list
            >>> positions_list = project.lp.PositionsOA
            >>> if positions_list:
            ...     consultant_pos = positions_list.PossibilitiesOS[0]
            ...     project.Person.AddPosition(person, consultant_pos)

        Notes:
            - Position must be an ICmPossibility from project lists
            - Duplicate positions are allowed
            - Use GetPositions() to verify before adding

        See Also:
            GetPositions
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(position, "position")

        person = self.__ResolveObject(person_or_hvo)

        try:
            position_poss = ICmPossibility(position)
            person.PositionsRC.Add(position_poss)
        except (AttributeError, System.InvalidCastException) as e:
            raise FP_ParameterError("position must be a valid ICmPossibility object")

    @OperationsMethod
    def Duplicate(self, person_or_hvo, insert_after=True):
        """
        Duplicate a person, creating a new copy with a new GUID.

        Args:
            person_or_hvo: The ICmPerson object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source person.
                                If False, insert at end of people collection.
            deep (bool): Reserved for future use (persons have no owned objects).
                        Currently has no effect.

        Returns:
            ICmPerson: The newly created duplicate person with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If person_or_hvo is None.

        Example:
            >>> # Duplicate a person
            >>> person = project.Person.Find("John Smith")
            >>> dup = project.Person.Duplicate(person)
            >>> print(f"Original: {project.Person.GetGuid(person)}")
            >>> print(f"Duplicate: {project.Person.GetGuid(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321

            >>> # Verify properties copied
            >>> print(project.Person.GetEmail(dup))
            john.smith@example.com

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original person's position
            - Simple properties copied: Name, Gender, Email, DateOfBirth
            - MultiString properties copied: Abbreviation (address), Description (education),
              Comment (notes), PlaceOfBirth (phone)
            - Reference collections copied: PositionsRC, PlacesOfResidenceRC, LanguagesRC
            - DateCreated and DateModified are NOT copied (set automatically)
            - deep parameter has no effect (persons have no owned objects)

        See Also:
            Create, Delete, GetGuid
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")

        # Get source person
        source = self.__ResolveObject(person_or_hvo)

        # Create new person using factory (auto-generates new GUID)
        with self._TransactionCM("Duplicate person"):
            factory = self.project.project.ServiceLocator.GetService(ICmPersonFactory)
            duplicate = factory.Create()

            # Determine insertion position and add to parent FIRST
            if insert_after:
                source_index = self.project.lp.PeopleOA.PossibilitiesOS.IndexOf(source)
                self.project.lp.PeopleOA.PossibilitiesOS.Insert(source_index + 1, duplicate)
            else:
                self.project.lp.PeopleOA.PossibilitiesOS.Add(duplicate)

            # Copy simple MultiString properties
            duplicate.Name.CopyAlternatives(source.Name)
            duplicate.Gender.CopyAlternatives(source.Gender)
            duplicate.Email.CopyAlternatives(source.Email)
            duplicate.Abbreviation.CopyAlternatives(source.Abbreviation)  # Address
            duplicate.Description.CopyAlternatives(source.Description)  # Education
            duplicate.Comment.CopyAlternatives(source.Comment)  # Notes
            duplicate.PlaceOfBirth.CopyAlternatives(source.PlaceOfBirth)  # Phone

            # Copy DateOfBirth (GenDate field)
            if hasattr(source, "DateOfBirth") and source.DateOfBirth:
                duplicate.DateOfBirth = source.DateOfBirth

            # Copy Reference Collection (RC) properties
            if hasattr(source, "PositionsRC"):
                for position in source.PositionsRC:
                    duplicate.PositionsRC.Add(position)

            if hasattr(source, "PlacesOfResidenceRC"):
                for residence in source.PlacesOfResidenceRC:
                    duplicate.PlacesOfResidenceRC.Add(residence)

            if hasattr(source, "LanguagesRC"):
                for language in source.LanguagesRC:
                    duplicate.LanguagesRC.Add(language)

            # Note: deep parameter has no effect for persons (no owned objects)

            return duplicate

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get syncable properties for cross-project synchronization.

        Returns all syncable properties of a person including MultiString fields
        and reference collections (as GUIDs).

        Args:
            item: The ICmPerson object

        Returns:
            dict: Dictionary of syncable properties

        Example:
            >>> props = project.Person.GetSyncableProperties(person)
            >>> print(props)
            {'Name': 'John Smith', 'Gender': 'Male', 'Email': 'john@...', ...}
        """
        self._ValidateParam(item, "item")

        person = self.__ResolveObject(item)
        wsHandle = self.project.project.DefaultAnalWs

        props = {}

        # MultiString properties
        props["Name"] = ITsString(person.Name.get_String(wsHandle)).Text or ""
        props["Gender"] = ITsString(person.Gender.get_String(wsHandle)).Text or ""
        props["Email"] = ITsString(person.Email.get_String(wsHandle)).Text or ""
        props["Abbreviation"] = ITsString(person.Abbreviation.get_String(wsHandle)).Text or ""  # Address
        props["Description"] = ITsString(person.Description.get_String(wsHandle)).Text or ""  # Education
        props["Comment"] = ITsString(person.Comment.get_String(wsHandle)).Text or ""  # Notes
        props["PlaceOfBirth"] = ITsString(person.PlaceOfBirth.get_String(wsHandle)).Text or ""  # Phone

        # GenDate field
        if hasattr(person, "DateOfBirth") and person.DateOfBirth:
            props["DateOfBirth"] = str(person.DateOfBirth)
        else:
            props["DateOfBirth"] = None

        # Reference Collection (RC) properties - return GUIDs as strings
        if hasattr(person, "PositionsRC"):
            props["Positions"] = [str(pos.Guid) for pos in person.PositionsRC]
        if hasattr(person, "PlacesOfResidenceRC"):
            props["PlacesOfResidence"] = [str(place.Guid) for place in person.PlacesOfResidenceRC]
        if hasattr(person, "LanguagesRC"):
            props["Languages"] = [str(lang.Guid) for lang in person.LanguagesRC]

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two persons and return detailed differences.

        Args:
            item1: First person (from source project)
            item2: Second person (from target project)
            ops1: Operations instance for item1's project (defaults to self)
            ops2: Operations instance for item2's project (defaults to self)

        Returns:
            tuple: (is_different, differences_dict) where differences_dict contains
                   'properties' dict with changed property details

        Example:
            >>> is_diff, diffs = ops1.CompareTo(person1, person2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, details in diffs['properties'].items():
            ...         print(f"{prop}: {details['source']} -> {details['target']}")
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        is_different = False
        differences = {"properties": {}}

        # Get syncable properties from both items
        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        # Compare each property
        for key in set(props1.keys()) | set(props2.keys()):
            val1 = props1.get(key)
            val2 = props2.get(key)

            # Handle list comparisons (for RC properties)
            if isinstance(val1, list) and isinstance(val2, list):
                if set(val1) != set(val2):
                    is_different = True
                    differences["properties"][key] = {"source": val1, "target": val2, "type": "modified"}
            elif val1 != val2:
                is_different = True
                differences["properties"][key] = {"source": val1, "target": val2, "type": "modified"}

        return is_different, differences

    # --- Metadata ---

    @OperationsMethod
    def GetGuid(self, person_or_hvo):
        """
        Get the GUID (Globally Unique Identifier) of a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO

        Returns:
            System.Guid: The person's GUID

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> guid = project.Person.GetGuid(person)
            >>> print(guid)
            a1b2c3d4-e5f6-7890-abcd-ef1234567890

            >>> # Use GUID to retrieve person later
            >>> person2 = project.Object(guid)
            >>> print(project.Person.GetName(person2))
            John Smith

        Notes:
            - GUIDs are unique across all FLEx projects
            - GUIDs are persistent (don't change)
            - Useful for linking people across projects
            - Can be used with FLExProject.Object() to retrieve person

        See Also:
            FLExProject.Object, FLExProject.BuildGotoURL
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)

        return person.Guid

    @OperationsMethod
    def GetDateCreated(self, person_or_hvo):
        """
        Get the creation date of a person record.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO

        Returns:
            System.DateTime: The date and time the person record was created

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> created = project.Person.GetDateCreated(person)
            >>> print(f"Created: {created}")
            Created: 2025-01-15 14:30:22

        Notes:
            - Returns System.DateTime object (not Python datetime)
            - Automatically set when person is created
            - Cannot be modified (read-only property)
            - Timezone is local to the FLEx project

        See Also:
            GetDateModified
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)

        return person.DateCreated

    @OperationsMethod
    def GetDateModified(self, person_or_hvo):
        """
        Get the last modification date of a person record.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO

        Returns:
            System.DateTime: The date and time the person record was last modified

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> modified = project.Person.GetDateModified(person)
            >>> print(f"Last modified: {modified}")
            Last modified: 2025-01-20 09:15:43

        Notes:
            - Returns System.DateTime object (not Python datetime)
            - Automatically updated when person changes
            - Cannot be modified directly (read-only property)
            - Updates on any change to person properties

        See Also:
            GetDateCreated
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)

        return person.DateModified

    # --- Relationships ---

    @OperationsMethod
    def GetResidences(self, person_or_hvo):
        """
        Get the places of residence for a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO

        Returns:
            list: List of ICmLocation objects (empty list if none)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> residences = project.Person.GetResidences(person)
            >>> for loc in residences:
            ...     name = ITsString(loc.Name.BestAnalysisAlternative).Text
            ...     print(f"Residence: {name}")
            Residence: New York, USA
            Residence: London, UK

        Notes:
            - Returns empty list if no residences assigned
            - Residences are ICmLocation objects
            - Locations may need to be created first

        See Also:
            AddResidence
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)

        return list(person.PlacesOfResidenceRC)

    @OperationsMethod
    def AddResidence(self, person_or_hvo, location):
        """
        Add a place of residence to a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            location: ICmLocation object representing the residence

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or location is None
            FP_ParameterError: If location is not a valid ICmLocation

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> # Assuming location was created elsewhere
            >>> # location = ...
            >>> # project.Person.AddResidence(person, location)

        Notes:
            - Location must be an ICmLocation object
            - Duplicate locations are allowed
            - Locations must be created before adding

        See Also:
            GetResidences
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(location, "location")

        person = self.__ResolveObject(person_or_hvo)

        try:
            location_obj = ICmLocation(location)
            person.PlacesOfResidenceRC.Add(location_obj)
        except (AttributeError, System.InvalidCastException) as e:
            raise FP_ParameterError("location must be a valid ICmLocation object")

    @OperationsMethod
    def GetLanguages(self, person_or_hvo):
        """
        Get the languages known by a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO

        Returns:
            list: List of ICmPossibility objects representing languages
                  (empty list if none)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> languages = project.Person.GetLanguages(person)
            >>> for lang in languages:
            ...     name = ITsString(lang.Name.BestAnalysisAlternative).Text
            ...     print(f"Language: {name}")
            Language: English
            Language: Spanish

        Notes:
            - Returns empty list if no languages assigned
            - Languages are ICmPossibility objects from language lists
            - Typically from the Languages possibility list

        See Also:
            AddLanguage
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)

        return list(person.LanguagesRC)

    @OperationsMethod
    def AddLanguage(self, person_or_hvo, language):
        """
        Add a language to a person's known languages.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            language: ICmPossibility object representing the language

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or language is None
            FP_ParameterError: If language is not a valid ICmPossibility

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> # Get language from project's languages list
            >>> languages_list = project.lp.LanguagesOA
            >>> if languages_list:
            ...     spanish = languages_list.PossibilitiesOS[0]
            ...     project.Person.AddLanguage(person, spanish)

        Notes:
            - Language must be an ICmPossibility from project lists
            - Duplicate languages are allowed
            - Use GetLanguages() to verify before adding

        See Also:
            GetLanguages
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(language, "language")

        person = self.__ResolveObject(person_or_hvo)

        try:
            language_poss = ICmPossibility(language)
            person.LanguagesRC.Add(language_poss)
        except (AttributeError, System.InvalidCastException) as e:
            raise FP_ParameterError("language must be a valid ICmPossibility object")

    # --- Notes ---

    @OperationsMethod
    def GetNotes(self, person_or_hvo, wsHandle=None):
        """
        Get the notes for a person.

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: Notes text (empty string if not set)

        Raises:
            FP_NullParameterError: If person_or_hvo is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> notes = project.Person.GetNotes(person)
            >>> print(notes)
            Primary consultant for dialect study. Available weekdays.

        Notes:
            - Returns empty string if no notes
            - Can be multi-line text
            - Useful for storing additional information

        See Also:
            AddNote, SetEducation
        """
        self._ValidateParam(person_or_hvo, "person_or_hvo")

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        # Use Comment field for notes
        notes = ITsString(person.Comment.get_String(wsHandle)).Text
        return notes or ""

    @OperationsMethod
    def AddNote(self, person_or_hvo, note, wsHandle=None):
        """
        Add a note to a person (appends to existing notes).

        Args:
            person_or_hvo: Either an ICmPerson object or its HVO
            note (str): Note text to add
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If person_or_hvo or note is None

        Example:
            >>> person = project.Person.Find("John Smith")
            >>> project.Person.AddNote(person, "Primary consultant")
            >>> project.Person.AddNote(person, "Available weekdays")
            >>> print(project.Person.GetNotes(person))
            Primary consultant
            Available weekdays

        Notes:
            - Appends to existing notes with newline separator
            - Use GetNotes() and SetNotes() for replacing all notes
            - Empty note text is ignored

        See Also:
            GetNotes
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person_or_hvo, "person_or_hvo")
        self._ValidateParam(note, "note")

        if not note or not note.strip():
            return  # Ignore empty notes

        person = self.__ResolveObject(person_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        # Get existing notes
        existing = ITsString(person.Comment.get_String(wsHandle)).Text or ""

        # Append new note
        if existing:
            new_notes = existing + "\n" + note
        else:
            new_notes = note

        mkstr = TsStringUtils.MakeString(new_notes, wsHandle)
        person.Comment.set_String(wsHandle, mkstr)

    # --- Private Helper Methods ---

    def __ResolveObject(self, person_or_hvo):
        """
        Resolve HVO or object to ICmPerson.

        Args:
            person_or_hvo: Either an ICmPerson object or an HVO (int)

        Returns:
            ICmPerson: The resolved person object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a person
        """
        if isinstance(person_or_hvo, int):
            obj = self.project.Object(person_or_hvo)
            if not isinstance(obj, ICmPerson):
                raise FP_ParameterError("HVO does not refer to a person")
            return obj
        return person_or_hvo

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to vernacular WS.

        Args:
            wsHandle: Optional writing system handle

        Returns:
            int: The writing system handle
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)

    def __WSHandleAnalysis(self, wsHandle):
        """
        Get writing system handle, defaulting to analysis WS.

        Args:
            wsHandle: Optional writing system handle

        Returns:
            int: The writing system handle
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)
