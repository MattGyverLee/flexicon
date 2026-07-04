#
#   DataNotebookOperations.py
#
#   Class: DataNotebookOperations
#          Research notebook record operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)

# Import FLEx LCM types
from SIL.LCModel import (
    IRnGenericRec,
    IRnGenericRecFactory,
    IRnResearchNbkRepository,
    ICmPossibility,
    ICmPossibilityRepository,
    ICmPerson,
    IText,
    ICmFile,
    ICmFileFactory,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils
from System import Guid, DateTime
import System

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import string utilities
from ..Shared.string_utils import normalize_text, normalize_match_key


class DataNotebookOperations(BaseOperations):
    """
    This class provides operations for managing research notebook records in a
    FieldWorks project.

    Research notebook records (IRnGenericRec) are used to document field research,
    observations, interviews, and other data collection activities. They support
    hierarchical organization, linking to texts and participants, media attachments,
    categorization by record type, and status tracking.

    Notebook records are essential for documenting the research process and
    maintaining a structured record of linguistic fieldwork activities.

    This class should be accessed via FLExProject.DataNotebook property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Create a new notebook record
        record = project.DataNotebook.Create(
            "Interview with Speaker A",
            "Detailed notes from interview about kinship terminology"
        )

        # Set record type
        record_types = project.DataNotebook.GetAllRecordTypes()
        if record_types:
            project.DataNotebook.SetRecordType(record, record_types[0])

        # Set date of event
        project.DataNotebook.SetDateOfEvent(record, "2024-01-15")

        # Add researchers
        researcher = project.Person.Find("John Doe")
        if researcher:
            project.DataNotebook.AddResearcher(record, researcher)

        # Link to text
        text = project.Texts.Find("Interview 1")
        if text:
            project.DataNotebook.LinkToText(record, text)

        # Add media file
        media = project.Media.Find("interview_audio.wav")
        if media:
            project.DataNotebook.AddMediaFile(record, media)

        # Set status
        project.DataNotebook.SetStatus(record, "Reviewed")

        # Create hierarchical structure
        subrecord = project.DataNotebook.CreateSubRecord(
            record,
            "Analysis Notes",
            "Follow-up analysis of terminology patterns"
        )

        # Query records
        recent = project.DataNotebook.FindByDate("2024-01-01", "2024-12-31")
        for rec in recent:
            title = project.DataNotebook.GetTitle(rec)
            date = project.DataNotebook.GetDateOfEvent(rec)
            print(f"{title} - {date}")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize DataNotebookOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """Specify which sequence to reorder for notebook records."""
        return parent.RecordsOS

    def __WSHandle(self, wsHandle):
        """
        Internal helper for writing system handles.

        Args:
            wsHandle: Writing system handle or None for default analysis WS.

        Returns:
            int: The writing system handle to use.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    def __ValidatedRecordHvo(self, record_or_hvo):
        """
        Internal function to validate and convert record_or_hvo to HVO.

        Args:
            record_or_hvo: Either an IRnGenericRec object or its HVO (integer).

        Returns:
            int: The HVO of the notebook record.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
        """
        self._ValidateParam(record_or_hvo, "record_or_hvo")

        try:
            hvo = record_or_hvo.Hvo
        except AttributeError:
            hvo = record_or_hvo

        return hvo

    def __GetRecordObject(self, record_or_hvo):
        """
        Internal function to get IRnGenericRec object from record_or_hvo.

        Args:
            record_or_hvo: Either an IRnGenericRec object or its HVO (integer).

        Returns:
            IRnGenericRec: The notebook record object.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the object doesn't exist or isn't valid.
        """
        hvo = self.__ValidatedRecordHvo(record_or_hvo)

        try:
            obj = self.project.project.GetObject(hvo)
            return IRnGenericRec(obj)
        except (
            TypeError,
            System.InvalidCastException,
            AttributeError,
            KeyError,
            System.Collections.Generic.KeyNotFoundException,
        ) as e:
            raise FP_ParameterError(f"Invalid notebook record object or HVO: {record_or_hvo} - {e}")

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all research notebook records in the project.

        Returns all top-level notebook records. Use GetSubRecords() to navigate
        the hierarchical structure of records and their sub-records.

        Yields:
            IRnGenericRec: Each notebook record object.

        Example:
            >>> for record in project.DataNotebook.GetAll():
            ...     title = project.DataNotebook.GetTitle(record)
            ...     date = project.DataNotebook.GetDateCreated(record)
            ...     status = project.DataNotebook.GetStatus(record)
            ...     print(f"{title} - {date} - {status}")
            Interview with Speaker A - 2024-01-15 - Reviewed
            Field Observation Notes - 2024-01-20 - Draft
            Elicitation Session 3 - 2024-02-01 - Approved

        Notes:
            - Returns an iterator for memory efficiency
            - Returns only top-level records (not sub-records)
            - Records are returned in database order
            - Use GetSubRecords() to access hierarchical sub-records
            - Each record can have title, content, type, dates, and links

        See Also:
            Create, Find, GetSubRecords, FindByDate
        """
        repos = self.project.project.ServiceLocator.GetService(IRnResearchNbkRepository)
        for record in repos.AllInstances():
            # Only yield top-level records (those without an owner that's also a record)
            try:
                owner = record.Owner
                if not isinstance(owner, IRnGenericRec):
                    yield record
            except (AttributeError, System.NullReferenceException) as e:
                yield record

    @OperationsMethod
    def Create(self, title, content=None, wsHandle=None):
        """
        Create a new research notebook record.

        Creates a top-level notebook record with the specified title and optional
        content. Use CreateSubRecord() to create hierarchical sub-records.

        Args:
            title (str): The title/heading of the notebook record.
            content (str, optional): The main content/body text of the record.
                Defaults to None (empty content).
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            IRnGenericRec: The newly created notebook record object.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If title is None.
            FP_ParameterError: If title is empty.

        Example:
            >>> # Create a basic record
            >>> record = project.DataNotebook.Create(
            ...     "Interview with Speaker A",
            ...     "Notes from interview about kinship terms"
            ... )
            >>> print(project.DataNotebook.GetTitle(record))
            Interview with Speaker A

            >>> # Create with specific writing system
            >>> record = project.DataNotebook.Create(
            ...     "Entrevista con Hablante A",
            ...     content="Notas sobre terminología de parentesco",
            ...     wsHandle=project.WSHandle('es')
            ... )

            >>> # Create and configure
            >>> record = project.DataNotebook.Create("Field Observation")
            >>> project.DataNotebook.SetDateOfEvent(record, "2024-01-15")
            >>> project.DataNotebook.SetStatus(record, "Draft")

        Notes:
            - Title is required, content is optional
            - Created records have no type, researchers, or links by default
            - Use Set* methods to configure additional properties
            - DateCreated and DateModified are set automatically
            - GUID is assigned automatically
            - Default status depends on project configuration

        See Also:
            CreateSubRecord, SetTitle, SetContent, SetRecordType
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(title, "title")

        if not title.strip():
            raise FP_ParameterError("Title cannot be empty")

        wsHandle = self.__WSHandle(wsHandle)

        # Get the research notebook repository
        repos = self.project.project.ServiceLocator.GetService(IRnResearchNbkRepository)
        factory = self.project.project.ServiceLocator.GetService(IRnGenericRecFactory)

        # Create the record in the RecordsOC collection
        with self._TransactionCM(f"Create notebook record '{title}'"):

            record = factory.Create()
            repos.RecordsOC.Add(record)

            # Set title
            mkstr = TsStringUtils.MakeString(title, wsHandle)
            record.Title.set_String(wsHandle, mkstr)

            # Set content if provided
            if content:
                mkstr = TsStringUtils.MakeString(content, wsHandle)
                record.Text.set_String(wsHandle, mkstr)

            return record

    @OperationsMethod
    def Delete(self, record_or_hvo):
        """
        Delete a notebook record from the project.

        Deletes the specified notebook record and all its sub-records. This
        operation also removes all links to texts, researchers, participants,
        and media files.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> # Delete by object
            >>> record = project.DataNotebook.Find("Old Interview Notes")
            >>> if record:
            ...     project.DataNotebook.Delete(record)
            ...     print("Record deleted")

            >>> # Delete by HVO
            >>> project.DataNotebook.Delete(12345)

            >>> # Delete with confirmation
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> if record:
            ...     title = project.DataNotebook.GetTitle(record)
            ...     # Confirm deletion
            ...     if confirm_delete(title):
            ...         project.DataNotebook.Delete(record)

        Notes:
            - Deletes the record and all sub-records recursively
            - Removes all links but doesn't delete linked objects
            - Cannot be undone through API (uses FieldWorks undo system)
            - Linked texts, researchers, and media files are not deleted
            - Custom field data is also deleted

        See Also:
            Create, GetSubRecords
        """
        self._EnsureWriteEnabled()

        record = self.__GetRecordObject(record_or_hvo)

        # Get the repository and remove the record
        repos = self.project.project.ServiceLocator.GetService(IRnResearchNbkRepository)

        with self._TransactionCM("Delete notebook record"):

            # SubRecordsOS lives on IRnGenericRec (the parent record's concrete
            # interface), not on the base ICmObject that pythonnet returns from
            # .Owner. The prior hasattr(owner, "SubRecordsOS") was therefore
            # always False on a real sub-record -- execution fell through to
            # repos.RecordsOC.Remove(record), which removes from the top-level
            # records collection (where the sub-record never lived). Sub-record
            # deletes either silently no-op'd or removed the wrong row.
            # Route through _GetTypedOwner to recover IRnGenericRec before
            # checking the slot. (issue #133, same class as #98/#116)
            parent = self._GetTypedOwner(record)
            if parent is not None and hasattr(parent, "SubRecordsOS"):
                parent.SubRecordsOS.Remove(record)
            else:
                repos.RecordsOC.Remove(record)

    @OperationsMethod
    def Exists(self, title, wsHandle=None):
        """
        Check if a notebook record with the given title exists.

        Args:
            title (str): The title to search for (case-sensitive).
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            bool: True if a record with this title exists, False otherwise.

        Raises:
            FP_NullParameterError: If title is None.

        Example:
            >>> # Check before creating
            >>> if not project.DataNotebook.Exists("Interview 1"):
            ...     record = project.DataNotebook.Create("Interview 1")
            ... else:
            ...     print("Record already exists")
            Record already exists

            >>> # Check multiple writing systems
            >>> exists_en = project.DataNotebook.Exists("Interview", "en")
            >>> exists_es = project.DataNotebook.Exists("Entrevista", "es")

        Notes:
            - Search is case-sensitive
            - Searches in the specified writing system only
            - Returns True if at least one record matches
            - Does not search content, only titles

        See Also:
            Find, Create
        """
        self._ValidateParam(title, "title")

        return self.Find(title, wsHandle) is not None

    @OperationsMethod
    def Find(self, title, wsHandle=None):
        """
        Find a notebook record by its title.

        Searches for the first record that exactly matches the given title
        in the specified writing system.

        Args:
            title (str): The title to search for (case-sensitive).
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            IRnGenericRec: The matching notebook record object, or None if not found.

        Raises:
            FP_NullParameterError: If title is None.

        Example:
            >>> # Find and display record
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> if record:
            ...     content = project.DataNotebook.GetContent(record)
            ...     date = project.DataNotebook.GetDateOfEvent(record)
            ...     print(f"{content} - {date}")
            ... else:
            ...     print("Record not found")

            >>> # Find in specific writing system
            >>> record = project.DataNotebook.Find(
            ...     "Entrevista 1",
            ...     wsHandle=project.WSHandle('es')
            ... )

            >>> # Find and update
            >>> record = project.DataNotebook.Find("Old Title")
            >>> if record:
            ...     project.DataNotebook.SetTitle(record, "New Title")

        Notes:
            - Search is case-sensitive and exact match only
            - Returns first match if multiple records have same title
            - Returns None if no match found
            - Searches only in specified writing system
            - Use FindBy* methods for more complex queries

        See Also:
            Exists, FindByDate, FindByResearcher, FindByType
        """
        self._ValidateParam(title, "title")

        wsHandle = self.__WSHandle(wsHandle)

        target = normalize_match_key(title, casefold=False)
        for record in self.GetAll():
            record_title = ITsString(record.Title.get_String(wsHandle)).Text
            if normalize_match_key(record_title, casefold=False) == target:
                return record

        return None

    # --- Property Operations: Title ---

    @OperationsMethod
    def GetTitle(self, record_or_hvo, wsHandle=None):
        """
        Get the title of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The title text, or empty string if not set.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> title = project.DataNotebook.GetTitle(record)
            >>> print(title)
            Interview 1

            >>> # Get title in multiple languages
            >>> title_en = project.DataNotebook.GetTitle(record, "en")
            >>> title_es = project.DataNotebook.GetTitle(record, "es")
            >>> print(f"EN: {title_en}, ES: {title_es}")
            EN: Interview 1, ES: Entrevista 1

        Notes:
            - Returns empty string if title not set in specified WS
            - Titles are multi-lingual (can be set in multiple writing systems)
            - Use SetTitle() to modify

        See Also:
            SetTitle, GetContent
        """
        record = self.__GetRecordObject(record_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        try:
            text = ITsString(record.Title.get_String(wsHandle)).Text
            return normalize_text(text) or ""
        except (AttributeError, TypeError) as e:
            logger.debug(f"Could not get record title: {e}")
            return ""

    @OperationsMethod
    def SetTitle(self, record_or_hvo, title, wsHandle=None):
        """
        Set the title of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            title (str): The new title text.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or title is None.
            FP_ParameterError: If the record doesn't exist or title is empty.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> project.DataNotebook.SetTitle(record, "Interview with Speaker A")
            >>> print(project.DataNotebook.GetTitle(record))
            Interview with Speaker A

            >>> # Set in multiple languages
            >>> project.DataNotebook.SetTitle(record, "Interview 1", "en")
            >>> project.DataNotebook.SetTitle(record, "Entrevista 1", "es")

        Notes:
            - Title must not be empty
            - Titles support multiple writing systems
            - Previous title value is overwritten

        See Also:
            GetTitle, SetContent
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(title, "title")

        if not title.strip():
            raise FP_ParameterError("Title cannot be empty")

        record = self.__GetRecordObject(record_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(title, wsHandle)

        record.Title.set_String(wsHandle, mkstr)

    # --- Property Operations: Content ---

    @OperationsMethod
    def GetContent(self, record_or_hvo, wsHandle=None):
        """
        Get the content/body text of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The content text, or empty string if not set.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> content = project.DataNotebook.GetContent(record)
            >>> print(content)
            Detailed notes from interview about kinship terminology.
            Speaker provided examples of terms for siblings and cousins.

            >>> # Get content with specific length limit
            >>> content = project.DataNotebook.GetContent(record)
            >>> summary = content[:100] + "..." if len(content) > 100 else content
            >>> print(summary)

        Notes:
            - Returns empty string if content not set
            - Content can be lengthy (multiple paragraphs)
            - Content is multi-lingual
            - May contain structured text markup

        See Also:
            SetContent, GetTitle
        """
        record = self.__GetRecordObject(record_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        try:
            text = ITsString(record.Text.get_String(wsHandle)).Text
            return normalize_text(text) or ""
        except (AttributeError, TypeError) as e:
            logger.debug(f"Could not get record content: {e}")
            return ""

    @OperationsMethod
    def SetContent(self, record_or_hvo, content, wsHandle=None):
        """
        Set the content/body text of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            content (str): The new content text.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or content is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> project.DataNotebook.SetContent(
            ...     record,
            ...     "Detailed notes from interview about kinship terminology. "
            ...     "Speaker provided examples of terms for siblings and cousins."
            ... )

            >>> # Update content incrementally
            >>> existing = project.DataNotebook.GetContent(record)
            >>> new_content = existing + "\\n\\nAdditional observations..."
            >>> project.DataNotebook.SetContent(record, new_content)

            >>> # Set in multiple languages
            >>> project.DataNotebook.SetContent(record, "English notes", "en")
            >>> project.DataNotebook.SetContent(record, "Notas en español", "es")

        Notes:
            - Content can be empty string
            - Previous content is completely replaced
            - Supports multiple writing systems
            - No length limit on content

        See Also:
            GetContent, SetTitle
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(content, "content")

        record = self.__GetRecordObject(record_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(content, wsHandle)

        record.Text.set_String(wsHandle, mkstr)

    # --- Record Type Operations ---

    @OperationsMethod
    def GetRecordType(self, record_or_hvo):
        """
        Get the type/category of a notebook record.

        Record types categorize notebook records (e.g., "Interview", "Observation",
        "Elicitation Session", "Literature Notes"). Types are defined as
        possibilities in the project's notebook record type list.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            ICmPossibility: The record type object, or None if not set.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> rec_type = project.DataNotebook.GetRecordType(record)
            >>> if rec_type:
            ...     type_name = ITsString(
            ...         rec_type.Name.get_String(project.project.DefaultAnalWs)
            ...     ).Text
            ...     print(f"Type: {type_name}")
            ... else:
            ...     print("No type set")
            Type: Interview

        Notes:
            - Returns None if no type has been set
            - Types are ICmPossibility objects
            - Use GetAllRecordTypes() to see available types
            - Types can be hierarchical (with subtypes)

        See Also:
            SetRecordType, GetAllRecordTypes
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "Type") and record.Type:
            return record.Type

        return None

    @OperationsMethod
    def SetRecordType(self, record_or_hvo, record_type):
        """
        Set the type/category of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            record_type: The type to set (ICmPossibility object from record types list).

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or record_type is None.
            FP_ParameterError: If the record or type doesn't exist.

        Example:
            >>> # Set record type
            >>> record = project.DataNotebook.Find("Field Notes 1")
            >>> types = project.DataNotebook.GetAllRecordTypes()
            >>> interview_type = next(
            ...     (t for t in types if "Interview" in str(t.Name)), None
            ... )
            >>> if interview_type:
            ...     project.DataNotebook.SetRecordType(record, interview_type)

            >>> # Find type by name and set
            >>> record = project.DataNotebook.Create("New Observation")
            >>> obs_type = project.DataNotebook.FindRecordTypeByName("Observation")
            >>> if obs_type:
            ...     project.DataNotebook.SetRecordType(record, obs_type)

        Notes:
            - record_type must be from the project's record types list
            - Previous type is replaced
            - Can be set to None to remove type

        See Also:
            GetRecordType, GetAllRecordTypes, FindRecordTypeByName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(record_type, "record_type")

        record = self.__GetRecordObject(record_or_hvo)

        record.Type = record_type

    @OperationsMethod
    def GetAllRecordTypes(self):
        """
        Get all available notebook record types in the project.

        Returns all record type possibilities that can be assigned to notebook
        records. These types are used to categorize different kinds of research
        activities and observations.

        Returns:
            list: List of ICmPossibility objects representing record types.

        Example:
            >>> # List all record types
            >>> for rec_type in project.DataNotebook.GetAllRecordTypes():
            ...     name = ITsString(
            ...         rec_type.Name.get_String(project.project.DefaultAnalWs)
            ...     ).Text
            ...     print(f"Type: {name}")
            Type: Interview
            Type: Observation
            Type: Elicitation Session
            Type: Literature Notes
            Type: Methodology

            >>> # Find specific type
            >>> types = project.DataNotebook.GetAllRecordTypes()
            >>> interview = next((t for t in types if "Interview" in str(t.Name)), None)

        Notes:
            - Returns empty list if no types are defined
            - Types are ICmPossibility objects
            - Types can be hierarchical
            - Use SetRecordType() to assign a type to a record

        See Also:
            GetRecordType, SetRecordType, FindRecordTypeByName
        """
        # Get the record types list from the project
        if hasattr(self.project.lp, "RecTypesOA"):
            rec_types_list = self.project.lp.RecTypesOA
            if rec_types_list is not None:
                return list(rec_types_list.PossibilitiesOS)

        return []

    @OperationsMethod
    def FindRecordTypeByName(self, type_name, wsHandle=None):
        """
        Find a record type by its name.

        Args:
            type_name (str): The name of the record type to find.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmPossibility: The matching record type, or None if not found.

        Raises:
            FP_NullParameterError: If type_name is None.

        Example:
            >>> # Find and set record type
            >>> record = project.DataNotebook.Create("Interview Notes")
            >>> interview_type = project.DataNotebook.FindRecordTypeByName("Interview")
            >>> if interview_type:
            ...     project.DataNotebook.SetRecordType(record, interview_type)
            ... else:
            ...     print("Type not found")

        Notes:
            - Search is case-sensitive
            - Returns first match only
            - Returns None if not found

        See Also:
            GetAllRecordTypes, SetRecordType
        """
        self._ValidateParam(type_name, "type_name")

        wsHandle = self.__WSHandle(wsHandle)

        for rec_type in self.GetAllRecordTypes():
            name = ITsString(rec_type.Name.get_String(wsHandle)).Text
            if name == type_name:
                return rec_type

        return None

    # --- Date/Time Operations ---

    @OperationsMethod
    def GetDateCreated(self, record_or_hvo):
        """
        Get the creation date of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            DateTime: The creation date, or None if not available.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> created = project.DataNotebook.GetDateCreated(record)
            >>> if created:
            ...     print(f"Created: {created.ToString('yyyy-MM-dd HH:mm:ss')}")
            Created: 2024-01-15 14:30:00

        Notes:
            - Set automatically when record is created
            - Cannot be modified
            - Returns .NET DateTime object

        See Also:
            GetDateModified, GetDateOfEvent
        """
        record = self.__GetRecordObject(record_or_hvo)

        try:
            if hasattr(record, "DateCreated"):
                return record.DateCreated
        except (AttributeError, System.NullReferenceException) as e:
            pass

        return None

    @OperationsMethod
    def GetDateModified(self, record_or_hvo):
        """
        Get the last modification date of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            DateTime: The last modification date, or None if not available.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> modified = project.DataNotebook.GetDateModified(record)
            >>> if modified:
            ...     print(f"Modified: {modified.ToString('yyyy-MM-dd HH:mm:ss')}")
            Modified: 2024-01-20 09:15:00

        Notes:
            - Updated automatically when record is modified
            - Cannot be set manually
            - Returns .NET DateTime object

        See Also:
            GetDateCreated, GetDateOfEvent
        """
        record = self.__GetRecordObject(record_or_hvo)

        try:
            if hasattr(record, "DateModified"):
                return record.DateModified
        except (AttributeError, System.NullReferenceException) as e:
            pass

        return None

    @OperationsMethod
    def GetDateOfEvent(self, record_or_hvo):
        """
        Get the event date of a notebook record.

        The event date represents when the documented event/observation occurred,
        which may differ from the creation or modification dates of the record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            DateTime: The event date, or None if not set.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> event_date = project.DataNotebook.GetDateOfEvent(record)
            >>> if event_date:
            ...     print(f"Event: {event_date.ToString('yyyy-MM-dd')}")
            ... else:
            ...     print("Event date not set")
            Event: 2024-01-15

        Notes:
            - Can be different from creation/modification dates
            - Useful for documenting when fieldwork occurred
            - Returns None if not set

        See Also:
            SetDateOfEvent, GetDateCreated
        """
        record = self.__GetRecordObject(record_or_hvo)

        try:
            if hasattr(record, "DateOfEvent") and record.DateOfEvent:
                return record.DateOfEvent
        except (AttributeError, System.NullReferenceException) as e:
            pass

        return None

    @OperationsMethod
    def SetDateOfEvent(self, record_or_hvo, date):
        """
        Set the event date of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            date: The date to set (DateTime object or string in format "YYYY-MM-DD"
                or "YYYY-MM-DD HH:MM:SS").

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or date is None.
            FP_ParameterError: If the record doesn't exist or date format is invalid.

        Example:
            >>> # Set with DateTime object
            >>> from System import DateTime
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> project.DataNotebook.SetDateOfEvent(record, DateTime.Now)

            >>> # Set with string
            >>> project.DataNotebook.SetDateOfEvent(record, "2024-01-15")
            >>> project.DataNotebook.SetDateOfEvent(record, "2024-01-15 14:30:00")

            >>> # Set date from user input
            >>> date_str = "2024-01-15"
            >>> project.DataNotebook.SetDateOfEvent(record, date_str)

        Notes:
            - Accepts DateTime object or string format
            - String format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
            - Represents when the documented event occurred
            - Independent of creation/modification dates

        See Also:
            GetDateOfEvent, GetDateCreated
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(date, "date")

        record = self.__GetRecordObject(record_or_hvo)

        # Convert string to DateTime if needed
        if isinstance(date, str):
            try:
                date = DateTime.Parse(date)
            except (System.FormatException, ValueError, TypeError) as e:
                raise FP_ParameterError(f"Invalid date format: {date}. Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' - {e}")

        record.DateOfEvent = date

    # --- Hierarchy Operations ---

    @OperationsMethod
    def GetSubRecords(self, record_or_hvo):
        """
        Get all direct sub-records of a notebook record.

        Notebook records support hierarchical organization where records can
        contain sub-records. This method returns only direct children, not
        all descendants.

        Args:
            record_or_hvo: The parent record object (IRnGenericRec) or its HVO.

        Returns:
            list: List of IRnGenericRec objects that are sub-records.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> # Get and display sub-records
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> subs = project.DataNotebook.GetSubRecords(record)
            >>> print(f"Found {len(subs)} sub-records:")
            >>> for sub in subs:
            ...     title = project.DataNotebook.GetTitle(sub)
            ...     print(f"  - {title}")
            Found 3 sub-records:
              - Kinship Terms Section
              - Color Terms Section
              - Grammar Notes

            >>> # Recursive display of hierarchy
            >>> def show_hierarchy(rec, indent=0):
            ...     title = project.DataNotebook.GetTitle(rec)
            ...     print("  " * indent + title)
            ...     for sub in project.DataNotebook.GetSubRecords(rec):
            ...         show_hierarchy(sub, indent + 1)
            >>> show_hierarchy(record)

        Notes:
            - Returns empty list if no sub-records exist
            - Returns only direct children (not grandchildren)
            - Use recursion to traverse entire hierarchy
            - Sub-records can have their own sub-records

        See Also:
            CreateSubRecord, GetParentRecord
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "SubRecordsOS"):
            return list(record.SubRecordsOS)

        return []

    @OperationsMethod
    def CreateSubRecord(self, parent_record_or_hvo, title, content=None, wsHandle=None):
        """
        Create a new sub-record under a parent notebook record.

        Creates a child record in the hierarchical structure. Sub-records
        inherit the context of their parent but can have their own properties,
        links, and media.

        Args:
            parent_record_or_hvo: The parent record (IRnGenericRec) or its HVO.
            title (str): The title of the new sub-record.
            content (str, optional): The content of the sub-record. Defaults to None.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            IRnGenericRec: The newly created sub-record object.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If parent_record_or_hvo or title is None.
            FP_ParameterError: If parent doesn't exist or title is empty.

        Example:
            >>> # Create hierarchical structure
            >>> parent = project.DataNotebook.Create("Interview with Speaker A")
            >>> sub1 = project.DataNotebook.CreateSubRecord(
            ...     parent,
            ...     "Kinship Terminology",
            ...     "Discussion of family relationship terms"
            ... )
            >>> sub2 = project.DataNotebook.CreateSubRecord(
            ...     parent,
            ...     "Color Terms",
            ...     "Basic color terminology elicitation"
            ... )
            >>> # Create nested sub-records
            >>> subsub = project.DataNotebook.CreateSubRecord(
            ...     sub1,
            ...     "Parent Terms",
            ...     "Terms for mother and father"
            ... )

        Notes:
            - Sub-records can have their own sub-records (unlimited nesting)
            - Sub-records are independent objects with their own properties
            - Deleting parent deletes all sub-records recursively
            - Sub-records can link to different texts/researchers than parent

        See Also:
            Create, GetSubRecords, GetParentRecord
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(title, "title")

        if not title.strip():
            raise FP_ParameterError("Title cannot be empty")

        parent = self.__GetRecordObject(parent_record_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Create the sub-record
        factory = self.project.project.ServiceLocator.GetService(IRnGenericRecFactory)

        with self._TransactionCM(f"Create sub-record '{title}'"):

            subrecord = factory.Create()
            parent.SubRecordsOS.Add(subrecord)

            # Set title
            mkstr = TsStringUtils.MakeString(title, wsHandle)
            subrecord.Title.set_String(wsHandle, mkstr)

            # Set content if provided
            if content:
                mkstr = TsStringUtils.MakeString(content, wsHandle)
                subrecord.Text.set_String(wsHandle, mkstr)

            return subrecord

    @OperationsMethod
    def GetParentRecord(self, record_or_hvo):
        """
        Get the parent record of a sub-record.

        Args:
            record_or_hvo: The sub-record object (IRnGenericRec) or its HVO.

        Returns:
            IRnGenericRec: The parent record object, or None if this is a
                top-level record.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> # Navigate up the hierarchy
            >>> subrecord = project.DataNotebook.Find("Kinship Terms Section")
            >>> parent = project.DataNotebook.GetParentRecord(subrecord)
            >>> if parent:
            ...     parent_title = project.DataNotebook.GetTitle(parent)
            ...     print(f"Parent: {parent_title}")
            ... else:
            ...     print("This is a top-level record")
            Parent: Interview 1

            >>> # Get full path to root
            >>> def get_path(rec):
            ...     path = []
            ...     current = rec
            ...     while current:
            ...         path.insert(0, project.DataNotebook.GetTitle(current))
            ...         current = project.DataNotebook.GetParentRecord(current)
            ...     return " > ".join(path)
            >>> print(get_path(subrecord))
            Interview 1 > Kinship Terms Section

        Notes:
            - Returns None for top-level records
            - Parent is always an IRnGenericRec
            - Use GetSubRecords() to navigate down the hierarchy

        See Also:
            GetSubRecords, CreateSubRecord
        """
        record = self.__GetRecordObject(record_or_hvo)

        try:
            owner = record.Owner
            if isinstance(owner, IRnGenericRec):
                return IRnGenericRec(owner)
        except (AttributeError, TypeError, System.InvalidCastException) as e:
            pass

        return None

    # --- Linking Operations: Researchers ---

    @OperationsMethod
    def GetResearchers(self, record_or_hvo):
        """
        Get all researchers associated with a notebook record.

        Researchers are people (ICmPerson objects) who conducted the fieldwork
        or created the observations documented in the record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            list: List of ICmPerson objects representing researchers.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> researchers = project.DataNotebook.GetResearchers(record)
            >>> print(f"Researchers ({len(researchers)}):")
            >>> for person in researchers:
            ...     name = project.Person.GetName(person)
            ...     print(f"  - {name}")
            Researchers (2):
              - John Doe
              - Jane Smith

        Notes:
            - Returns empty list if no researchers assigned
            - Researchers are ICmPerson objects
            - Multiple researchers can be assigned to one record

        See Also:
            AddResearcher, RemoveResearcher, GetParticipants
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "Researchers") and record.Researchers:
            return list(record.Researchers)

        return []

    @OperationsMethod
    def AddResearcher(self, record_or_hvo, person):
        """
        Add a researcher to a notebook record.

        Associates a person (researcher/fieldworker) with the notebook record.
        The same researcher can be added to multiple records.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            person: The person object (ICmPerson) to add as a researcher.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or person is None.
            FP_ParameterError: If the record or person doesn't exist.

        Example:
            >>> # Add single researcher
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> researcher = project.Person.Find("John Doe")
            >>> if researcher:
            ...     project.DataNotebook.AddResearcher(record, researcher)

            >>> # Add multiple researchers
            >>> researchers = ["John Doe", "Jane Smith", "Maria Garcia"]
            >>> for name in researchers:
            ...     person = project.Person.Find(name)
            ...     if person:
            ...         project.DataNotebook.AddResearcher(record, person)

            >>> # Create and add new researcher
            >>> new_researcher = project.Person.Create("Alice Johnson")
            >>> project.DataNotebook.AddResearcher(record, new_researcher)

        Notes:
            - Adding same researcher twice has no effect (no duplicates)
            - Researchers are not deleted when removed from records
            - Use Person operations to manage person objects

        See Also:
            GetResearchers, RemoveResearcher, AddParticipant
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person, "person")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "Researchers"):
            if person not in record.Researchers:
                record.Researchers.Add(person)

    @OperationsMethod
    def RemoveResearcher(self, record_or_hvo, person):
        """
        Remove a researcher from a notebook record.

        Removes the association between a person and a notebook record. The
        person object itself is not deleted.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            person: The person object (ICmPerson) to remove.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or person is None.
            FP_ParameterError: If the record or person doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> researcher = project.Person.Find("John Doe")
            >>> project.DataNotebook.RemoveResearcher(record, researcher)

        Notes:
            - Only removes the link, doesn't delete the person
            - No error if person wasn't linked to record

        See Also:
            AddResearcher, GetResearchers
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person, "person")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "Researchers"):
            if person in record.Researchers:
                record.Researchers.Remove(person)

    # --- Linking Operations: Participants ---

    @OperationsMethod
    def GetParticipants(self, record_or_hvo):
        """
        Get all participants associated with a notebook record.

        Participants are people (ICmPerson objects) who participated in the
        recorded event (e.g., consultants, speakers, informants).

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            list: List of ICmPerson objects representing participants.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> participants = project.DataNotebook.GetParticipants(record)
            >>> print(f"Participants ({len(participants)}):")
            >>> for person in participants:
            ...     name = project.Person.GetName(person)
            ...     print(f"  - {name}")
            Participants (3):
              - Speaker A
              - Speaker B
              - Interpreter C

        Notes:
            - Returns empty list if no participants assigned
            - Participants differ from researchers (subjects vs. investigators)
            - Multiple participants can be assigned to one record

        See Also:
            AddParticipant, RemoveParticipant, GetResearchers
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "Participants") and record.Participants:
            return list(record.Participants)

        return []

    @OperationsMethod
    def AddParticipant(self, record_or_hvo, person):
        """
        Add a participant to a notebook record.

        Associates a person (consultant/speaker/informant) with the notebook
        record as a participant in the documented event.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            person: The person object (ICmPerson) to add as a participant.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or person is None.
            FP_ParameterError: If the record or person doesn't exist.

        Example:
            >>> # Add single participant
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> speaker = project.Person.Find("Speaker A")
            >>> if speaker:
            ...     project.DataNotebook.AddParticipant(record, speaker)

            >>> # Add multiple participants
            >>> participants = ["Speaker A", "Speaker B", "Interpreter C"]
            >>> for name in participants:
            ...     person = project.Person.Find(name)
            ...     if person:
            ...         project.DataNotebook.AddParticipant(record, person)

        Notes:
            - Adding same participant twice has no effect
            - Participants represent subjects/consultants
            - Use AddResearcher() for investigators/fieldworkers

        See Also:
            GetParticipants, RemoveParticipant, AddResearcher
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person, "person")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "Participants"):
            if person not in record.Participants:
                record.Participants.Add(person)

    @OperationsMethod
    def RemoveParticipant(self, record_or_hvo, person):
        """
        Remove a participant from a notebook record.

        Removes the association between a person and a notebook record. The
        person object itself is not deleted.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            person: The person object (ICmPerson) to remove.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or person is None.
            FP_ParameterError: If the record or person doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> speaker = project.Person.Find("Speaker A")
            >>> project.DataNotebook.RemoveParticipant(record, speaker)

        Notes:
            - Only removes the link, doesn't delete the person
            - No error if person wasn't linked to record

        See Also:
            AddParticipant, GetParticipants
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(person, "person")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "Participants"):
            if person in record.Participants:
                record.Participants.Remove(person)

    # --- Linking Operations: Locations ---

    @OperationsMethod
    def GetLocations(self, record_or_hvo):
        """
        Get all locations associated with a notebook record.

        Locations are places (ICmLocation objects) where the documented
        event or data collection occurred.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            list: List of ICmLocation objects representing locations.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> locations = project.DataNotebook.GetLocations(record)
            >>> print(f"Locations ({len(locations)}):")
            >>> for location in locations:
            ...     name = project.Location.GetName(location)
            ...     coords = project.Location.GetCoordinates(location)
            ...     print(f"  - {name}: {coords}")
            Locations (2):
              - Barasana Village: (-1.2345, -70.6789)
              - Papurí River Area: (1.1234, -70.5678)

        Notes:
            - Returns empty list if no locations assigned
            - Locations are ICmLocation objects
            - Multiple locations can be assigned to one record
            - Useful for tracking where fieldwork occurred

        See Also:
            AddLocation, RemoveLocation, GetResearchers
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "LocationsRC") and record.LocationsRC:
            return list(record.LocationsRC)

        return []

    @OperationsMethod
    def AddLocation(self, record_or_hvo, location):
        """
        Add a location to a notebook record.

        Associates a geographic location with the notebook record, indicating
        where the documented event or data collection took place.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            location: The location object (ICmLocation) to add.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or location is None.
            FP_ParameterError: If the record or location doesn't exist.

        Example:
            >>> # Add single location
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> location = project.Location.Find("Barasana Village")
            >>> if location:
            ...     project.DataNotebook.AddLocation(record, location)

            >>> # Add multiple locations
            >>> locations = ["Village A", "Village B", "Recording Site"]
            >>> for name in locations:
            ...     loc = project.Location.Find(name)
            ...     if loc:
            ...         project.DataNotebook.AddLocation(record, loc)

            >>> # Create and add new location
            >>> new_location = project.Location.Create("New Site", "en")
            >>> project.Location.SetCoordinates(new_location, -1.23, -70.45)
            >>> project.DataNotebook.AddLocation(record, new_location)

        Notes:
            - Adding same location twice has no effect (no duplicates)
            - Locations are not deleted when removed from records
            - Use Location operations to manage location objects
            - Useful for documenting fieldwork sites

        See Also:
            GetLocations, RemoveLocation, AddResearcher
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location, "location")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "LocationsRC"):
            if location not in record.LocationsRC:
                record.LocationsRC.Add(location)

    @OperationsMethod
    def RemoveLocation(self, record_or_hvo, location):
        """
        Remove a location from a notebook record.

        Removes the association between a location and a notebook record. The
        location object itself is not deleted.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            location: The location object (ICmLocation) to remove.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or location is None.
            FP_ParameterError: If the record or location doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> location = project.Location.Find("Old Site")
            >>> project.DataNotebook.RemoveLocation(record, location)

        Notes:
            - Only removes the link, doesn't delete the location
            - No error if location wasn't linked to record

        See Also:
            AddLocation, GetLocations
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(location, "location")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "LocationsRC"):
            if location in record.LocationsRC:
                record.LocationsRC.Remove(location)

    # --- Linking Operations: Sources ---

    @OperationsMethod
    def GetSources(self, record_or_hvo):
        """
        Get all bibliographic sources associated with a notebook record.

        Sources are references or publications (typically ICmPossibility objects
        from the project's bibliography) that are cited or related to the
        notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            list: List of source/reference objects.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> sources = project.DataNotebook.GetSources(record)
            >>> print(f"Sources ({len(sources)}):")
            >>> for source in sources:
            ...     # Display source information
            ...     print(f"  - {source}")
            Sources (2):
              - Smith 2020
              - Johnson & Garcia 2018

        Notes:
            - Returns empty list if no sources assigned
            - Sources can be bibliographic references or other citation objects
            - Multiple sources can be assigned to one record
            - Useful for documenting which publications relate to the data

        See Also:
            AddSource, RemoveSource, GetResearchers
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "SourcesRC") and record.SourcesRC:
            return list(record.SourcesRC)

        return []

    @OperationsMethod
    def AddSource(self, record_or_hvo, source):
        """
        Add a bibliographic source/reference to a notebook record.

        Associates a source or bibliographic reference with the notebook record,
        indicating which publications or materials are relevant to the documented
        data.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            source: The source/reference object to add.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or source is None.
            FP_ParameterError: If the record or source doesn't exist.

        Example:
            >>> # Add single source
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> source = project.Bibliography.Find("Smith 2020")
            >>> if source:
            ...     project.DataNotebook.AddSource(record, source)

            >>> # Add multiple sources
            >>> sources = ["Smith 2020", "Johnson & Garcia 2018"]
            >>> for name in sources:
            ...     src = project.Bibliography.Find(name)
            ...     if src:
            ...         project.DataNotebook.AddSource(record, src)

            >>> # Create and add new source
            >>> new_source = project.Bibliography.Create("Doe 2024")
            >>> project.DataNotebook.AddSource(record, new_source)

        Notes:
            - Adding same source twice has no effect (no duplicates)
            - Sources are not deleted when removed from records
            - Use Bibliography operations to manage source objects
            - Useful for tracking citations and references

        See Also:
            GetSources, RemoveSource, AddResearcher
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(source, "source")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "SourcesRC"):
            if source not in record.SourcesRC:
                record.SourcesRC.Add(source)

    @OperationsMethod
    def RemoveSource(self, record_or_hvo, source):
        """
        Remove a bibliographic source/reference from a notebook record.

        Removes the association between a source and a notebook record. The
        source object itself is not deleted.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            source: The source/reference object to remove.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or source is None.
            FP_ParameterError: If the record or source doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> source = project.Bibliography.Find("Old Reference")
            >>> project.DataNotebook.RemoveSource(record, source)

        Notes:
            - Only removes the link, doesn't delete the source
            - No error if source wasn't linked to record

        See Also:
            AddSource, GetSources
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(source, "source")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "SourcesRC"):
            if source in record.SourcesRC:
                record.SourcesRC.Remove(source)

    # --- Text Linking Operations ---

    @OperationsMethod
    def GetTexts(self, record_or_hvo):
        """
        Get all texts linked to a notebook record.

        Retrieves all IText objects that are linked to this notebook record.
        Texts might be recordings, transcriptions, or other textual data that
        the notebook record references or documents.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            list: List of IText objects linked to the record.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> texts = project.DataNotebook.GetTexts(record)
            >>> print(f"Linked texts ({len(texts)}):")
            >>> for text in texts:
            ...     title = project.Texts.GetTitle(text)
            ...     print(f"  - {title}")
            Linked texts (2):
              - Interview Recording 1
              - Interview Transcription 1

        Notes:
            - Returns empty list if no texts are linked
            - Links are bidirectional (can find records from texts)
            - Multiple texts can be linked to one record

        See Also:
            LinkToText, UnlinkFromText
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "TextsRC") and record.TextsRC:
            return list(record.TextsRC)

        return []

    @OperationsMethod
    def LinkToText(self, record_or_hvo, text):
        """
        Link a notebook record to a text.

        Creates a connection between a notebook record and a text object,
        indicating that the record documents or relates to that text.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            text: The text object (IText) to link to.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or text is None.
            FP_ParameterError: If the record or text doesn't exist.

        Example:
            >>> # Link record to text
            >>> record = project.DataNotebook.Find("Interview Notes")
            >>> text = project.Texts.Find("Interview Recording 1")
            >>> if text:
            ...     project.DataNotebook.LinkToText(record, text)

            >>> # Link to multiple texts
            >>> text_titles = ["Recording 1", "Recording 2", "Transcription 1"]
            >>> for title in text_titles:
            ...     text = project.Texts.Find(title)
            ...     if text:
            ...         project.DataNotebook.LinkToText(record, text)

        Notes:
            - Linking same text twice has no effect
            - Links are bidirectional
            - Useful for connecting field notes to recordings

        See Also:
            UnlinkFromText, GetTexts
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(text, "text")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "TextsRC"):
            if text not in record.TextsRC:
                record.TextsRC.Add(text)

    @OperationsMethod
    def UnlinkFromText(self, record_or_hvo, text):
        """
        Unlink a notebook record from a text.

        Removes the connection between a notebook record and a text object.
        The text itself is not deleted.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            text: The text object (IText) to unlink from.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or text is None.
            FP_ParameterError: If the record or text doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview Notes")
            >>> text = project.Texts.Find("Recording 1")
            >>> if text:
            ...     project.DataNotebook.UnlinkFromText(record, text)

        Notes:
            - Only removes the link, doesn't delete the text
            - No error if text wasn't linked to record

        See Also:
            LinkToText, GetTexts
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(text, "text")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "TextsRC"):
            if text in record.TextsRC:
                record.TextsRC.Remove(text)

    # --- Media File Operations ---

    @OperationsMethod
    def GetMediaFiles(self, record_or_hvo):
        """
        Get all media files attached to a notebook record.

        Retrieves all ICmFile objects (audio, video, images) that are attached
        to this notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            list: List of ICmFile objects representing media files.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> media_files = project.DataNotebook.GetMediaFiles(record)
            >>> print(f"Media files ({len(media_files)}):")
            >>> for media in media_files:
            ...     path = project.Media.GetInternalPath(media)
            ...     print(f"  - {path}")
            Media files (2):
              - audio/interview1.wav
              - images/notes_photo.jpg

        Notes:
            - Returns empty list if no media files attached
            - Media can be audio, video, or images
            - Files are ICmFile references, not file paths

        See Also:
            AddMediaFile, RemoveMediaFile
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "MediaFilesOS") and record.MediaFilesOS:
            return list(record.MediaFilesOS)

        return []

    @OperationsMethod
    def AddMediaFile(self, record_or_hvo, media_file):
        """
        Add a media file to a notebook record.

        Attaches a media file (audio, video, or image) to the notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            media_file: The media file object (ICmFile) to attach.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or media_file is None.
            FP_ParameterError: If the record or media file doesn't exist.

        Example:
            >>> # Add existing media file
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> media = project.Media.Find("interview1.wav")
            >>> if media:
            ...     project.DataNotebook.AddMediaFile(record, media)

            >>> # Create and add new media file
            >>> new_media = project.Media.Create("/path/to/recording.wav")
            >>> project.DataNotebook.AddMediaFile(record, new_media)

            >>> # Add multiple media files
            >>> media_files = ["audio.wav", "photo1.jpg", "photo2.jpg"]
            >>> for filename in media_files:
            ...     media = project.Media.Find(filename)
            ...     if media:
            ...         project.DataNotebook.AddMediaFile(record, media)

        Notes:
            - Media file must exist in project before linking
            - Adding same file twice has no effect
            - Supports audio, video, and image files

        See Also:
            RemoveMediaFile, GetMediaFiles
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(media_file, "media_file")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "MediaFilesOS"):
            if media_file not in record.MediaFilesOS:
                record.MediaFilesOS.Add(media_file)

    @OperationsMethod
    def RemoveMediaFile(self, record_or_hvo, media_file):
        """
        Remove a media file from a notebook record.

        Detaches a media file from the notebook record. The media file itself
        is not deleted from the project.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            media_file: The media file object (ICmFile) to remove.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or media_file is None.
            FP_ParameterError: If the record or media file doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> media = project.Media.Find("old_recording.wav")
            >>> if media:
            ...     project.DataNotebook.RemoveMediaFile(record, media)

        Notes:
            - Only removes the link, doesn't delete the media file
            - No error if file wasn't attached to record

        See Also:
            AddMediaFile, GetMediaFiles
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(media_file, "media_file")

        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "MediaFilesOS"):
            if media_file in record.MediaFilesOS:
                record.MediaFilesOS.Remove(media_file)

    # --- Status Operations ---

    @OperationsMethod
    def GetStatus(self, record_or_hvo):
        """
        Get the status of a notebook record.

        Status indicates the review state or workflow stage of the record
        (e.g., "Draft", "Reviewed", "Approved", "Published").

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            ICmPossibility: The status object, or None if not set.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> status = project.DataNotebook.GetStatus(record)
            >>> if status:
            ...     status_name = ITsString(
            ...         status.Name.get_String(project.project.DefaultAnalWs)
            ...     ).Text
            ...     print(f"Status: {status_name}")
            ... else:
            ...     print("No status set")
            Status: Reviewed

        Notes:
            - Returns None if no status has been set
            - Status values are ICmPossibility objects
            - Status list is project-specific

        See Also:
            SetStatus, GetAllStatuses
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "Status") and record.Status:
            return record.Status

        return None

    @OperationsMethod
    def SetStatus(self, record_or_hvo, status):
        """
        Set the status of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            status: The status to set (ICmPossibility object or status name string).

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or status is None.
            FP_ParameterError: If the record or status doesn't exist.

        Example:
            >>> # Set status by name
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> project.DataNotebook.SetStatus(record, "Reviewed")

            >>> # Set status by object
            >>> statuses = project.DataNotebook.GetAllStatuses()
            >>> approved = next((s for s in statuses if "Approved" in str(s.Name)), None)
            >>> if approved:
            ...     project.DataNotebook.SetStatus(record, approved)

            >>> # Workflow example
            >>> record = project.DataNotebook.Create("New Interview")
            >>> project.DataNotebook.SetStatus(record, "Draft")
            >>> # ... after review ...
            >>> project.DataNotebook.SetStatus(record, "Reviewed")
            >>> # ... after approval ...
            >>> project.DataNotebook.SetStatus(record, "Approved")

        Notes:
            - Status must be from project's status list
            - Can pass string (finds by name) or ICmPossibility object
            - Previous status is replaced

        See Also:
            GetStatus, GetAllStatuses
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(status, "status")

        record = self.__GetRecordObject(record_or_hvo)

        # If status is a string, find the matching possibility
        if isinstance(status, str):
            status_obj = self.FindStatusByName(status)
            if status_obj is None:
                raise FP_ParameterError(f"Status not found: {status}")
            status = status_obj

        record.Status = status

    @OperationsMethod
    def GetAllStatuses(self):
        """
        Get all available status values for notebook records.

        Returns all status possibilities that can be assigned to notebook
        records for tracking workflow and review stages.

        Returns:
            list: List of ICmPossibility objects representing status values.

        Example:
            >>> # List all statuses
            >>> for status in project.DataNotebook.GetAllStatuses():
            ...     name = ITsString(
            ...         status.Name.get_String(project.project.DefaultAnalWs)
            ...     ).Text
            ...     print(f"Status: {name}")
            Status: Draft
            Status: In Review
            Status: Reviewed
            Status: Approved
            Status: Published

        Notes:
            - Returns empty list if no statuses defined
            - Status list is project-specific
            - Typically includes workflow stages

        See Also:
            GetStatus, SetStatus, FindStatusByName
        """
        # Get the status list from the project
        if hasattr(self.project.lp, "StatusOA"):
            status_list = self.project.lp.StatusOA
            if status_list:
                return list(status_list.PossibilitiesOS)

        return []

    @OperationsMethod
    def FindStatusByName(self, status_name, wsHandle=None):
        """
        Find a status by its name.

        Args:
            status_name (str): The name of the status to find.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmPossibility: The matching status object, or None if not found.

        Raises:
            FP_NullParameterError: If status_name is None.

        Example:
            >>> # Find and set status
            >>> record = project.DataNotebook.Create("New Record")
            >>> draft_status = project.DataNotebook.FindStatusByName("Draft")
            >>> if draft_status:
            ...     project.DataNotebook.SetStatus(record, draft_status)

        Notes:
            - Search is case-sensitive
            - Returns first match only
            - Returns None if not found

        See Also:
            GetAllStatuses, SetStatus
        """
        self._ValidateParam(status_name, "status_name")

        wsHandle = self.__WSHandle(wsHandle)

        for status in self.GetAllStatuses():
            name = ITsString(status.Name.get_String(wsHandle)).Text
            if name == status_name:
                return status

        return None

    # --- Query Operations ---

    @OperationsMethod
    def FindByDate(self, start_date=None, end_date=None):
        """
        Find notebook records by date range.

        Searches for records whose DateOfEvent falls within the specified range.

        Args:
            start_date: Start date (DateTime or string "YYYY-MM-DD"). None means no start limit.
            end_date: End date (DateTime or string "YYYY-MM-DD"). None means no end limit.

        Returns:
            list: List of IRnGenericRec objects matching the date criteria.

        Example:
            >>> # Find records from specific date range
            >>> records = project.DataNotebook.FindByDate("2024-01-01", "2024-12-31")
            >>> print(f"Found {len(records)} records in 2024")
            >>> for record in records:
            ...     title = project.DataNotebook.GetTitle(record)
            ...     date = project.DataNotebook.GetDateOfEvent(record)
            ...     print(f"{title} - {date}")

            >>> # Find records after a certain date
            >>> recent = project.DataNotebook.FindByDate(start_date="2024-06-01")

            >>> # Find records before a certain date
            >>> old = project.DataNotebook.FindByDate(end_date="2023-12-31")

        Notes:
            - Searches DateOfEvent, not DateCreated/Modified
            - Records without DateOfEvent are excluded
            - Both dates are inclusive
            - Accepts DateTime objects or date strings

        See Also:
            FindByResearcher, FindByType, GetDateOfEvent
        """
        # Convert string dates to DateTime if needed
        if start_date and isinstance(start_date, str):
            start_date = DateTime.Parse(start_date)
        if end_date and isinstance(end_date, str):
            end_date = DateTime.Parse(end_date)

        results = []
        for record in self.GetAll():
            event_date = self.GetDateOfEvent(record)
            if not event_date:
                continue

            # Check if date falls within range
            if start_date and event_date < start_date:
                continue
            if end_date and event_date > end_date:
                continue

            results.append(record)

        return results

    @OperationsMethod
    def FindByResearcher(self, person):
        """
        Find all notebook records associated with a specific researcher.

        Args:
            person: The person object (ICmPerson) or person name (str) to search for.

        Returns:
            list: List of IRnGenericRec objects that have this researcher.

        Raises:
            FP_NullParameterError: If person is None.

        Example:
            >>> # Find by person object
            >>> researcher = project.Person.Find("John Doe")
            >>> if researcher:
            ...     records = project.DataNotebook.FindByResearcher(researcher)
            ...     print(f"John Doe worked on {len(records)} records")
            ...     for record in records:
            ...         title = project.DataNotebook.GetTitle(record)
            ...         print(f"  - {title}")

            >>> # Find by name
            >>> records = project.DataNotebook.FindByResearcher("Jane Smith")

        Notes:
            - Searches in Researchers collection
            - Can pass person object or name string
            - Returns empty list if no matches

        See Also:
            FindByDate, FindByType, GetResearchers
        """
        self._ValidateParam(person, "person")

        # If string provided, find the person
        if isinstance(person, str):
            person_obj = self.project.Person.Find(person)
            if person_obj is None:
                return []
            person = person_obj

        results = []
        for record in self.GetAll():
            researchers = self.GetResearchers(record)
            if person in researchers:
                results.append(record)

        return results

    @OperationsMethod
    def FindByType(self, record_type):
        """
        Find all notebook records of a specific type.

        Args:
            record_type: The record type (ICmPossibility object or type name string).

        Returns:
            list: List of IRnGenericRec objects with this type.

        Raises:
            FP_NullParameterError: If record_type is None.

        Example:
            >>> # Find by type name
            >>> interviews = project.DataNotebook.FindByType("Interview")
            >>> print(f"Found {len(interviews)} interview records")
            >>> for record in interviews:
            ...     title = project.DataNotebook.GetTitle(record)
            ...     date = project.DataNotebook.GetDateOfEvent(record)
            ...     print(f"{title} - {date}")

            >>> # Find by type object
            >>> types = project.DataNotebook.GetAllRecordTypes()
            >>> obs_type = next((t for t in types if "Observation" in str(t.Name)), None)
            >>> if obs_type:
            ...     observations = project.DataNotebook.FindByType(obs_type)

        Notes:
            - Can pass type object or name string
            - Returns empty list if no matches
            - Does not search sub-records by default

        See Also:
            FindByDate, FindByResearcher, GetRecordType
        """
        self._ValidateParam(record_type, "record_type")

        # If string provided, find the type
        if isinstance(record_type, str):
            type_obj = self.FindRecordTypeByName(record_type)
            if type_obj is None:
                return []
            record_type = type_obj

        results = []
        for record in self.GetAll():
            rec_type = self.GetRecordType(record)
            if rec_type and rec_type == record_type:
                results.append(record)

        return results

    @OperationsMethod
    def Duplicate(self, record_or_hvo, insert_after=False, deep=True):
        """
        Duplicate a notebook record, creating a new copy with a new GUID.

        Args:
            record_or_hvo: The IRnGenericRec object or HVO to duplicate.
            insert_after (bool): For sub-records (SubRecordsOS is an ordered
                sequence), controls whether the duplicate is inserted
                immediately after the source. Ignored for top-level records:
                RecordsOC is an unordered ILcmOwningCollection with no
                Insert() method, so top-level duplicates are always appended
                via Add().
            deep (bool): If True (default), also duplicate owned objects (sub-records).
                        If False, only copy simple properties and references.

        Returns:
            IRnGenericRec: The newly created duplicate record with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo is None.

        Example:
            >>> # Shallow duplicate (no sub-records)
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> dup = project.DataNotebook.Duplicate(record)
            >>> print(f"Original: {project.DataNotebook.GetGuid(record)}")
            >>> print(f"Duplicate: {project.DataNotebook.GetGuid(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321

            >>> # Deep duplicate (includes all sub-records)
            >>> deep_dup = project.DataNotebook.Duplicate(record, deep=True)
            >>> print(f"Sub-records: {len(project.DataNotebook.GetSubRecords(deep_dup))}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original record's position
            - Simple properties copied: Title, Text (content)
            - Reference properties copied: Type, Status, Confidence
            - DateTime properties copied: DateOfEvent
            - Owned objects (deep=True): SubRecordsOS
            - Collections NOT duplicated: Researchers, Participants, TextsRC, MediaFilesOS
            - DateCreated and DateModified are NOT copied (set automatically)

        See Also:
            Create, Delete, GetGuid, GetSubRecords
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(record_or_hvo, "record_or_hvo")

        # Get source record
        source = self.__GetRecordObject(record_or_hvo)

        # Determine parent (owner)
        owner = source.Owner

        # Create new record using factory (auto-generates new GUID)
        factory = self.project.project.ServiceLocator.GetService(IRnGenericRecFactory)
        duplicate = factory.Create()

        # Determine insertion position and add to parent FIRST
        if isinstance(owner, IRnGenericRec):
            # Parent is another notebook record (sub-record)
            parent_record = IRnGenericRec(owner)
            if insert_after:
                source_index = parent_record.SubRecordsOS.IndexOf(source)
                parent_record.SubRecordsOS.Insert(source_index + 1, duplicate)
            else:
                parent_record.SubRecordsOS.Add(duplicate)
        else:
            # Parent is the top-level repository. RecordsOC is an unordered
            # ILcmOwningCollection; insert_after has no semantic meaning here
            # and is ignored -- the duplicate is always appended via Add().
            repos = self.project.project.ServiceLocator.GetService(IRnResearchNbkRepository)
            repos.RecordsOC.Add(duplicate)

        # Copy simple MultiString properties
        duplicate.Title.CopyAlternatives(source.Title)
        duplicate.Text.CopyAlternatives(source.Text)

        # Copy Reference Atomic (RA) properties
        if hasattr(source, "Type") and source.Type:
            duplicate.Type = source.Type
        if hasattr(source, "Status") and source.Status:
            duplicate.Status = source.Status
        if hasattr(source, "Confidence") and source.Confidence:
            duplicate.Confidence = source.Confidence

        # Copy DateTime properties
        if hasattr(source, "DateOfEvent") and source.DateOfEvent:
            duplicate.DateOfEvent = source.DateOfEvent

        # Handle owned objects if deep=True
        if deep:
            # Duplicate sub-records into the NEW duplicate (not the original's parent)
            if hasattr(source, "SubRecordsOS"):
                for subrecord in source.SubRecordsOS:
                    self._DuplicateSubRecordInto(subrecord, duplicate, deep=True)

        return duplicate

    def _DuplicateSubRecordInto(self, source_rec, parent_dup, deep=True):
        """Duplicate a sub-record into the specified parent's SubRecordsOS."""
        factory = self.project.project.ServiceLocator.GetService(IRnGenericRecFactory)
        dup_rec = factory.Create()
        parent_dup.SubRecordsOS.Add(dup_rec)

        # Copy properties
        dup_rec.Title.CopyAlternatives(source_rec.Title)
        dup_rec.Text.CopyAlternatives(source_rec.Text)

        if hasattr(source_rec, "Type") and source_rec.Type:
            dup_rec.Type = source_rec.Type
        if hasattr(source_rec, "Status") and source_rec.Status:
            dup_rec.Status = source_rec.Status
        if hasattr(source_rec, "Confidence") and source_rec.Confidence:
            dup_rec.Confidence = source_rec.Confidence

        if hasattr(source_rec, "DateOfEvent") and source_rec.DateOfEvent:
            dup_rec.DateOfEvent = source_rec.DateOfEvent

        # Recurse into nested sub-records
        if deep and hasattr(source_rec, "SubRecordsOS"):
            for nested_rec in source_rec.SubRecordsOS:
                self._DuplicateSubRecordInto(nested_rec, dup_rec, deep=True)

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """Get syncable properties for cross-project synchronization."""
        self._ValidateParam(item, "item")

        record = self.__ResolveObject(item)
        wsHandle = self.project.project.DefaultAnalWs

        props = {}
        props["Title"] = ITsString(record.Title.get_String(wsHandle)).Text or ""
        props["Text"] = ITsString(record.Text.get_String(wsHandle)).Text or ""

        if hasattr(record, "Type") and record.Type:
            props["Type"] = str(record.Type.Guid)
        else:
            props["Type"] = None

        if hasattr(record, "Status") and record.Status:
            props["Status"] = str(record.Status.Guid)
        else:
            props["Status"] = None

        if hasattr(record, "Confidence") and record.Confidence:
            props["Confidence"] = str(record.Confidence.Guid)
        else:
            props["Confidence"] = None

        if hasattr(record, "DateOfEvent") and record.DateOfEvent:
            props["DateOfEvent"] = str(record.DateOfEvent)
        else:
            props["DateOfEvent"] = None

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """Compare two notebook records and return detailed differences."""
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
    def GetGuid(self, record_or_hvo):
        """
        Get the GUID (globally unique identifier) of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            Guid: The GUID of the record.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> guid = project.DataNotebook.GetGuid(record)
            >>> print(f"GUID: {guid}")
            GUID: 12345678-1234-1234-1234-123456789abc

        Notes:
            - GUID is assigned automatically when record is created
            - GUID is immutable and unique across all projects
            - Useful for external references and synchronization

        See Also:
            GetConfidence
        """
        record = self.__GetRecordObject(record_or_hvo)
        return record.Guid

    @OperationsMethod
    def GetConfidence(self, record_or_hvo):
        """
        Get the confidence level of a notebook record.

        Confidence indicates how certain or reliable the information in the
        record is considered to be.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.

        Returns:
            ICmPossibility: The confidence level object, or None if not set.

        Raises:
            FP_NullParameterError: If record_or_hvo is None.
            FP_ParameterError: If the record doesn't exist.

        Example:
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> confidence = project.DataNotebook.GetConfidence(record)
            >>> if confidence:
            ...     conf_name = ITsString(
            ...         confidence.Name.get_String(project.project.DefaultAnalWs)
            ...     ).Text
            ...     print(f"Confidence: {conf_name}")
            ... else:
            ...     print("No confidence level set")
            Confidence: High

        Notes:
            - Returns None if not set
            - Confidence levels are project-specific
            - Common values: High, Medium, Low, Uncertain

        See Also:
            SetConfidence, GetGuid
        """
        record = self.__GetRecordObject(record_or_hvo)

        if hasattr(record, "Confidence") and record.Confidence:
            return record.Confidence

        return None

    @OperationsMethod
    def SetConfidence(self, record_or_hvo, confidence):
        """
        Set the confidence level of a notebook record.

        Args:
            record_or_hvo: The notebook record object (IRnGenericRec) or its HVO.
            confidence: The confidence level (ICmPossibility object or name string).

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If record_or_hvo or confidence is None.
            FP_ParameterError: If the record or confidence level doesn't exist.

        Example:
            >>> # Set confidence by name
            >>> record = project.DataNotebook.Find("Interview 1")
            >>> project.DataNotebook.SetConfidence(record, "High")

            >>> # Set confidence by object
            >>> conf_levels = project.Confidence.GetAll()
            >>> high = next((c for c in conf_levels if "High" in str(c.Name)), None)
            >>> if high:
            ...     project.DataNotebook.SetConfidence(record, high)

        Notes:
            - Can pass confidence object or name string
            - Must be from project's confidence levels list
            - Previous value is replaced

        See Also:
            GetConfidence
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(confidence, "confidence")

        record = self.__GetRecordObject(record_or_hvo)

        # If confidence is a string, find the matching possibility
        if isinstance(confidence, str):
            conf_obj = self.project.Confidence.Find(confidence)
            if conf_obj is None:
                raise FP_ParameterError(f"Confidence level not found: {confidence}")
            confidence = conf_obj

        with self._TransactionCM('Set Confidence'):

            record.Confidence = confidence
