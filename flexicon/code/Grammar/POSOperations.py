#
#   POSOperations.py
#
#   Class: POSOperations
#          Parts of Speech operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import BaseOperations parent class and decorators
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import FLEx LCM types
from SIL.LCModel import IPartOfSpeechFactory, IPartOfSpeech, ILexEntryRepository
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import LCM casting utilities for pythonnet interface casting
from ..lcm_casting import get_pos_from_msa

# Import string utilities
from ..Shared.string_utils import normalize_match_key

# Catalog (GOLDEtic) parsing helpers
from ..Shared.catalog import parse_etic_catalog
from ..Shared.catalog_backed import CatalogBackedMixin


class POSOperations(BaseOperations, CatalogBackedMixin):
    """
    This class provides operations for managing Parts of Speech in a
    FieldWorks project.

    Parts of Speech are fundamental grammatical categories used in linguistic
    analysis (e.g., Noun, Verb, Adjective, etc.).

    Usage::

        from flexlibs2 import FLExProject, POSOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        posOps = POSOperations(project)

        # Get all parts of speech
        for pos in posOps.GetAll():
            print(posOps.GetName(pos), posOps.GetAbbreviation(pos))

        # Create a new POS
        noun = posOps.Create("Noun", "N")

        # Find and update
        verb = posOps.Find("Verb")
        if verb:
            posOps.SetAbbreviation(verb, "V")

        project.CloseProject()
    """

    # --- CatalogBackedMixin configuration ------------------------------
    # The GOLDEtic catalog ships with FW under Templates/GOLDEtic.xml and
    # is parsed by parse_etic_catalog. POSs are written with a
    # "GOLD:<id>" CatalogSourceId so FixGuidsAgainstCatalog can find them
    # later. POSs are hierarchical (SubPossibilitiesOS), so the mixin's
    # recursive-entries flag is on.
    CATALOG_FILE = "GOLDEtic.xml"
    CATALOG_SUBDIR = "Templates"
    CATALOG_PARSER = staticmethod(parse_etic_catalog)
    CATALOG_PREFIX_WRITE = "GOLD"
    DOMAIN_LABEL = "POS"
    _supports_recursive_entries = True

    def __init__(self, project):
        """
        Initialize POSOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for POS.
        For POS, we reorder parent.SubPossibilitiesOS
        """
        return parent.SubPossibilitiesOS

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, recursive=True, **kwargs):
        """
        Get all parts of speech in the project.

        Can be called two ways:
            POSOperations.GetAll(project)         # Class-level, no instantiation
            POSOperations(project).GetAll()       # Instance-level, traditional

        Args:
            recursive (bool): If True (default), yields every POS in the
                hierarchy (depth-first, parents before children). If False,
                yields only top-level POSs and the caller must descend via
                GetSubcategories.

        Returns:
            EnumerableWrapper[IPartOfSpeech]: Each part of speech object.

        Example:
            >>> posOps = POSOperations(project)
            >>> for pos in posOps.GetAll():
            ...     print(posOps.GetName(pos))      # Includes Proper Noun, Common Noun, etc.

            >>> # Top-level only
            >>> for pos in posOps.GetAll(recursive=False):
            ...     print(posOps.GetName(pos))

        See Also:
            GetSubcategories, Find
        """
        self._RejectLegacyKwargs(kwargs, {
            "flat": ("recursive", "semantics inverted: flat=True is now recursive=True"),
        })
        pos_list = self.project.lp.PartsOfSpeechOA
        if pos_list is None:
            return

        def walk(collection):
            for raw in collection:
                pos = IPartOfSpeech(raw)
                yield pos
                if recursive and pos.SubPossibilitiesOS.Count > 0:
                    yield from walk(pos.SubPossibilitiesOS)

        yield from walk(pos_list.PossibilitiesOS)

    @OperationsMethod
    def Create(self, name, abbreviation, catalogSourceId=None):
        """
        Create a new part of speech.

        Args:
            name (str): The name of the POS (e.g., "Noun", "Verb").
            abbreviation (str): Short abbreviation (e.g., "N", "V").
            catalogSourceId (str, optional): Optional catalog identifier for
                linguistic databases (e.g., "GOLD:Noun"). Defaults to None.

        Returns:
            IPartOfSpeech: The newly created POS object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name or abbreviation is None.
            FP_ParameterError: If name or abbreviation is empty, or if a POS
                with this name already exists.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Create("Noun", "N")
            >>> print(posOps.GetName(noun))
            Noun

            >>> proper_noun = posOps.Create("Proper Noun", "PN", "GOLD:Noun")
            >>> print(posOps.GetAbbreviation(proper_noun))
            PN

        Notes:
            - Name must be unique within the project
            - Abbreviations don't need to be unique but should be distinct
            - CatalogSourceId links to linguistic ontologies (e.g., GOLD)
            - The POS is created in the default analysis writing system

        See Also:
            Delete, Exists, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")
        self._ValidateParam(abbreviation, "abbreviation")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")
        if not abbreviation or not abbreviation.strip():
            raise FP_ParameterError("Abbreviation cannot be empty")

        # If the caller supplied a "GOLD:..." catalog id, defer to the
        # catalog path so the POS gets the canonical GUID and any extra
        # WS data the catalog provides. We then overlay the user's
        # name/abbreviation on top so explicit args still win.
        if catalogSourceId and catalogSourceId.upper().startswith("GOLD:"):
            wsHandle = self.project.project.DefaultAnalWs
            with self._TransactionCM(f"Create part of speech '{name}'"):
                new_pos = self.CreateFromCatalog(catalogSourceId)
                # Overlay user-supplied name and abbreviation in the
                # analysis WS (catalog values stay in other WSes).
                mkstr_name = TsStringUtils.MakeString(name, wsHandle)
                new_pos.Name.set_String(wsHandle, mkstr_name)
                mkstr_abbr = TsStringUtils.MakeString(abbreviation, wsHandle)
                new_pos.Abbreviation.set_String(wsHandle, mkstr_abbr)
                return new_pos

        # Check if POS already exists
        if self.Exists(name):
            raise FP_ParameterError(f"Part of Speech '{name}' already exists")

        # Get the writing system handle
        wsHandle = self.project.project.DefaultAnalWs

        # Create the new POS using the factory
        factory = self.project.project.ServiceLocator.GetService(IPartOfSpeechFactory)
        with self._TransactionCM(f"Create part of speech '{name}'"):
            new_pos = factory.Create()

            # Add to the POS list (must be done before setting properties)
            pos_list = self.project.lp.PartsOfSpeechOA
            pos_list.PossibilitiesOS.Add(new_pos)

            # Set name and abbreviation
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_pos.Name.set_String(wsHandle, mkstr_name)

            mkstr_abbr = TsStringUtils.MakeString(abbreviation, wsHandle)
            new_pos.Abbreviation.set_String(wsHandle, mkstr_abbr)

            # Set catalog source ID if provided
            if catalogSourceId:
                new_pos.CatalogSourceId = catalogSourceId

            return new_pos

    @OperationsMethod
    def Delete(self, pos_or_hvo):
        """
        Delete a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If pos_or_hvo is None.
            FP_ParameterError: If the POS is in use and cannot be deleted.

        Example:
            >>> posOps = POSOperations(project)
            >>> obsolete = posOps.Find("Obsolete")
            >>> if obsolete:
            ...     posOps.Delete(obsolete)

        Warning:
            - Deleting a POS that is in use may raise an error from FLEx
            - Will also delete all subcategories recursively
            - Deletion is permanent and cannot be undone
            - Lexical entries using this POS should be updated first

        See Also:
            Create, Exists, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        # Resolve to POS object
        pos = self.__ResolveObject(pos_or_hvo)

        # Remove from the POS list
        pos_list = self.project.lp.PartsOfSpeechOA
        pos_list.PossibilitiesOS.Remove(pos)

    @OperationsMethod
    def Exists(self, name):
        """
        Check if a part of speech with the given name exists.

        Args:
            name (str): The name to search for (case-insensitive).

        Returns:
            bool: True if POS exists, False otherwise.

        Raises:
            FP_NullParameterError: If name is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> if not posOps.Exists("Noun"):
            ...     posOps.Create("Noun", "N")

        Notes:
            - Comparison is case-insensitive
            - Searches recursively through all POS including subcategories
            - Use Find() to get the actual object

        See Also:
            Find, Create
        """
        self._ValidateParam(name, "name")

        return self.Find(name) is not None

    @OperationsMethod
    def Find(self, name):
        """
        Find a part of speech by name.

        Args:
            name (str): The name to search for (case-insensitive).

        Returns:
            IPartOfSpeech or None: The POS object if found, None otherwise.

        Raises:
            FP_NullParameterError: If name is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> if noun:
            ...     abbr = posOps.GetAbbreviation(noun)
            ...     print(f"Found: {abbr}")
            Found: N

        Notes:
            - Returns first match only
            - Search is case-insensitive
            - Searches recursively through all POS including subcategories
            - Returns None if not found (doesn't raise exception)

        See Also:
            Exists, GetName
        """
        self._ValidateParam(name, "name")

        target = normalize_match_key(name, casefold=True)
        wsHandle = self.project.project.DefaultAnalWs

        # Search recursively through POS hierarchy
        def search_pos_list(pos_collection):
            for pos in pos_collection:
                pos_name = ITsString(pos.Name.get_String(wsHandle)).Text
                if normalize_match_key(pos_name, casefold=True) == target:
                    return pos
                # Search subcategories
                if pos.SubPossibilitiesOS.Count > 0:
                    found = search_pos_list(pos.SubPossibilitiesOS)
                    if found:
                        return found
            return None

        pos_list = self.project.lp.PartsOfSpeechOA
        if pos_list is None:
            return None

        found = search_pos_list(pos_list.PossibilitiesOS)
        # search_pos_list walks Possibilities/SubPossibilities collections
        # which are typed ICmPossibility; cast the result so callers can
        # access IPartOfSpeech-specific properties.
        return IPartOfSpeech(found) if found is not None else None

    @OperationsMethod
    def GetName(self, pos_or_hvo, wsHandle=None):
        """
        Get the name of a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The POS name, or empty string if not set.

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> name = posOps.GetName(noun)
            >>> print(name)
            Noun

            >>> # Get name in a specific writing system
            >>> vern_name = posOps.GetName(noun, project.WSHandle('en'))

        See Also:
            SetName, GetAbbreviation
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(pos.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, pos_or_hvo, name, wsHandle=None):
        """
        Set the name of a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If pos_or_hvo or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> posOps = POSOperations(project)
            >>> typo = posOps.Find("Nown")  # typo
            >>> if typo:
            ...     posOps.SetName(typo, "Noun")  # fix it

        See Also:
            GetName, SetAbbreviation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(pos_or_hvo, "pos_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        pos = self.__ResolveObject(pos_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        pos.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetAbbreviation(self, pos_or_hvo, wsHandle=None):
        """
        Get the abbreviation of a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The POS abbreviation, or empty string if not set.

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> abbr = posOps.GetAbbreviation(noun)
            >>> print(abbr)
            N

        See Also:
            SetAbbreviation, GetName
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        abbr = ITsString(pos.Abbreviation.get_String(wsHandle)).Text
        return abbr or ""

    @OperationsMethod
    def SetAbbreviation(self, pos_or_hvo, abbr, wsHandle=None):
        """
        Set the abbreviation of a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.
            abbr (str): The new abbreviation.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If pos_or_hvo or abbr is None.
            FP_ParameterError: If abbr is empty.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> posOps.SetAbbreviation(noun, "N")

        See Also:
            GetAbbreviation, SetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(pos_or_hvo, "pos_or_hvo")
        self._ValidateParam(abbr, "abbr")

        if not abbr or not abbr.strip():
            raise FP_ParameterError("Abbreviation cannot be empty")

        pos = self.__ResolveObject(pos_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(abbr, wsHandle)
        pos.Abbreviation.set_String(wsHandle, mkstr)

    @wrap_enumerable
    @OperationsMethod
    def GetSubcategories(self, pos_or_hvo, recursive=True, **kwargs):
        """
        Get the subcategories of a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.
            recursive (bool): If True (default), returns every descendant
                (depth-first, parents before children). If False, returns only
                direct children.

        Returns:
            list: List of IPartOfSpeech subcategory objects (empty list if none).

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> for subcat in posOps.GetSubcategories(noun):
            ...     print(posOps.GetName(subcat))       # All descendants

            >>> # Direct children only
            >>> for subcat in posOps.GetSubcategories(noun, recursive=False):
            ...     print(posOps.GetName(subcat))

        See Also:
            GetAll, Find
        """
        self._RejectLegacyKwargs(kwargs, {
            "flat": ("recursive", "semantics inverted: flat=True is now recursive=True"),
        })
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)

        # SubPossibilitiesOS is typed ICmPossibility in C#; cast each child to
        # IPartOfSpeech so callers can access POS-specific properties.
        if not recursive:
            return [IPartOfSpeech(p) for p in pos.SubPossibilitiesOS]

        result = []
        def walk(collection):
            for raw in collection:
                child = IPartOfSpeech(raw)
                result.append(child)
                if child.SubPossibilitiesOS.Count > 0:
                    walk(child.SubPossibilitiesOS)
        walk(pos.SubPossibilitiesOS)
        return result

    @OperationsMethod
    def AddSubcategory(self, pos_or_hvo, name, abbreviation):
        """
        Add a subcategory to a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO to add subcategory to.
            name (str): The name of the subcategory.
            abbreviation (str): Short abbreviation for the subcategory.

        Returns:
            IPartOfSpeech: The newly created subcategory object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If pos_or_hvo, name, or abbreviation is None.
            FP_ParameterError: If name or abbreviation is empty.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> proper_noun = posOps.AddSubcategory(noun, "Proper Noun", "PN")
            >>> print(posOps.GetName(proper_noun))
            Proper Noun

        Notes:
            - The subcategory is created as a child of the parent POS
            - Subcategories inherit the parent's properties where applicable
            - Can be nested to create multi-level POS hierarchies
            - Uses default analysis writing system

        See Also:
            RemoveSubcategory, GetSubcategories, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(pos_or_hvo, "pos_or_hvo")
        self._ValidateParam(name, "name")
        self._ValidateParam(abbreviation, "abbreviation")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")
        if not abbreviation or not abbreviation.strip():
            raise FP_ParameterError("Abbreviation cannot be empty")

        pos = self.__ResolveObject(pos_or_hvo)
        wsHandle = self.project.project.DefaultAnalWs

        # Create the subcategory using the factory
        factory = self.project.project.ServiceLocator.GetService(IPartOfSpeechFactory)
        with self._TransactionCM(f"Add subcategory '{name}'"):
            subcat = factory.Create()

            # Add to parent's SubPossibilitiesOS (must be done before setting properties)
            pos.SubPossibilitiesOS.Add(subcat)

            # Set name and abbreviation
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            subcat.Name.set_String(wsHandle, mkstr_name)

            mkstr_abbr = TsStringUtils.MakeString(abbreviation, wsHandle)
            subcat.Abbreviation.set_String(wsHandle, mkstr_abbr)

            return subcat

    @OperationsMethod
    def RemoveSubcategory(self, pos_or_hvo, subcat_or_hvo):
        """
        Remove a subcategory from a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO (parent).
            subcat_or_hvo: The subcategory IPartOfSpeech object or HVO to remove.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If pos_or_hvo or subcat_or_hvo is None.
            FP_ParameterError: If the subcategory is in use and cannot be deleted.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> subcats = posOps.GetSubcategories(noun)
            >>> for subcat in subcats:
            ...     if posOps.GetName(subcat) == "Obsolete Subcategory":
            ...         posOps.RemoveSubcategory(noun, subcat)

        Warning:
            - Removing a subcategory that is in use may raise an error from FLEx
            - Will also delete all nested subcategories recursively
            - Removal is permanent and cannot be undone
            - Lexical entries using this subcategory should be updated first

        See Also:
            AddSubcategory, GetSubcategories, Delete
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(pos_or_hvo, "pos_or_hvo")
        self._ValidateParam(subcat_or_hvo, "subcat_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)
        subcat = self.__ResolveObject(subcat_or_hvo)

        # Remove from parent's SubPossibilitiesOS
        pos.SubPossibilitiesOS.Remove(subcat)

    @OperationsMethod
    def GetCatalogSourceId(self, pos_or_hvo):
        """
        Get the catalog source ID of a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.

        Returns:
            str: The catalog source ID, or empty string if not set.

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> catalog_id = posOps.GetCatalogSourceId(noun)
            >>> print(catalog_id)
            GOLD:Noun

        Notes:
            - Catalog source IDs link POS to linguistic ontologies (e.g., GOLD)
            - Returns empty string if no catalog ID is set
            - Used for cross-linguistic standardization and data sharing

        See Also:
            Create
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)

        return pos.CatalogSourceId or ""

    @wrap_enumerable
    @OperationsMethod
    def GetInflectionClasses(self, pos_or_hvo):
        """
        Get all inflection classes associated with a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.

        Returns:
            list: List of inflection class objects (empty list if none).

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> verb = posOps.Find("Verb")
            >>> classes = posOps.GetInflectionClasses(verb)
            >>> for infl_class in classes:
            ...     print(infl_class.Name)
            Regular Verb
            Irregular Verb
            Modal Verb

        Notes:
            - Inflection classes define morphological paradigms
            - Each POS can have multiple inflection classes
            - Returns empty list if no inflection classes are defined
            - Used for morphological analysis and generation

        See Also:
            GetAffixSlots
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)

        # IPartOfSpeech has InflectionClassesOC
        return list(pos.InflectionClassesOC)

    @wrap_enumerable
    @OperationsMethod
    def GetAffixSlots(self, pos_or_hvo):
        """
        Get all affix slots associated with a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.

        Returns:
            list: List of affix slot objects (empty list if none).

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> verb = posOps.Find("Verb")
            >>> slots = posOps.GetAffixSlots(verb)
            >>> for slot in slots:
            ...     print(slot.Name)
            Tense
            Aspect
            Mood

        Notes:
            - Affix slots define positions for affixes in morphological templates
            - Each POS can have multiple affix slots
            - Returns empty list if no affix slots are defined
            - Used for morphological parsing and generation

        See Also:
            GetInflectionClasses
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)

        # IPartOfSpeech has AffixSlotsOC
        return list(pos.AffixSlotsOC)

    @OperationsMethod
    def GetEntryCount(self, pos_or_hvo, recursive=False):
        """
        Count the number of lexical entries using this part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.
            recursive (bool): If False (default), counts only entries
                tagged with this POS exactly -- matches what FLEx's UI
                shows in the Categories tool, Lexicon Browse view, and
                Tools > Statistics (every count column in FLEx is
                direct-only). If True, rolls up entries tagged with
                this POS OR any descendant POS (e.g., counting "Noun"
                also picks up "Proper Noun", "Common Noun", etc.).

        Returns:
            int: The count of entries using this POS (direct-only by
            default; including descendants when ``recursive=True``).

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> count = posOps.GetEntryCount(noun)
            >>> print(f"There are {count} entries tagged exactly Noun")

            >>> # Roll-up: include Proper Noun, Common Noun, etc.
            >>> rollup = posOps.GetEntryCount(noun, recursive=True)

        Notes:
            Counting queries default to ``recursive=False`` (FLEx UI
            parity). Collection queries elsewhere in this codebase
            (e.g. ``GetSubcategories``) default to ``recursive=True``;
            the asymmetry is intentional -- counts answer "what does
            the user see in FLEx?" while collections answer "what's
            in the subtree?"

        See Also:
            Delete, GetSubcategories
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)

        # Build the set of POS HVOs to match. With recursive=True this expands
        # to include every descendant POS, so callers don't miss entries that
        # are tagged with a subcategory of the requested POS.
        match_hvos = {pos.Hvo}
        if recursive:
            match_hvos.update(d.Hvo for d in self.GetSubcategories(pos, recursive=True))

        count = 0
        entry_repo = self.project.project.ServiceLocator.GetService(ILexEntryRepository)
        for entry in entry_repo.AllInstances():
            for msa in entry.MorphoSyntaxAnalysesOC:
                msa_pos = get_pos_from_msa(msa)
                if msa_pos and msa_pos.Hvo in match_hvos:
                    count += 1
                    break  # Count each entry only once

        return count

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=False):
        """
        Duplicate a part of speech, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IPartOfSpeech object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source POS.
                                If False, insert at end of parent's possibilities list.
            deep (bool): If True, recursively duplicate all subcategories.
                        If False (default), only duplicate the POS itself.

        Returns:
            IPartOfSpeech: The newly created duplicate POS with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> # Shallow copy (no subcategories)
            >>> noun_copy = posOps.Duplicate(noun)
            >>> print(posOps.GetName(noun_copy))
            Noun

            >>> # Deep copy (includes all subcategories)
            >>> verb = posOps.Find("Verb")
            >>> verb_copy = posOps.Duplicate(verb, deep=True)
            >>> orig_subs = posOps.GetSubcategories(verb)
            >>> copy_subs = posOps.GetSubcategories(verb_copy)
            >>> print(f"Original has {len(orig_subs)} subcategories")
            >>> print(f"Copy has {len(copy_subs)} subcategories")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original POS's position
            - Simple properties copied: Name, Abbreviation, Description (MultiString)
            - String property copied: CatalogSourceId
            - deep=True recursively duplicates SubPossibilitiesOS hierarchy
            - Inflection classes and affix slots are NOT copied (references)
            - Use after copying to create variants of existing categories

        See Also:
            Create, Delete, GetSubcategories
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source POS and parent
        source = self.__ResolveObject(item_or_hvo)

        # Create new POS using factory (auto-generates new GUID)
        factory = self.project.project.ServiceLocator.GetService(IPartOfSpeechFactory)
        with self._TransactionCM("Duplicate POS"):
            duplicate = factory.Create()

            # Determine parent and insertion position
            # Check if source is a subcategory or top-level
            parent_is_possibility = False
            try:
                parent_pos = IPartOfSpeech(source.Owner)
                parent_is_possibility = True
            except Exception:
                parent_is_possibility = False

            if parent_is_possibility:
                # Source is a subcategory
                parent_pos = IPartOfSpeech(source.Owner)
                if insert_after:
                    source_index = parent_pos.SubPossibilitiesOS.IndexOf(source)
                    parent_pos.SubPossibilitiesOS.Insert(source_index + 1, duplicate)
                else:
                    parent_pos.SubPossibilitiesOS.Add(duplicate)
            else:
                # Source is top-level
                pos_list = self.project.lp.PartsOfSpeechOA
                if insert_after:
                    source_index = pos_list.PossibilitiesOS.IndexOf(source)
                    pos_list.PossibilitiesOS.Insert(source_index + 1, duplicate)
                else:
                    pos_list.PossibilitiesOS.Add(duplicate)

            # Copy simple MultiString properties (AFTER adding to parent)
            duplicate.Name.CopyAlternatives(source.Name)
            duplicate.Abbreviation.CopyAlternatives(source.Abbreviation)
            duplicate.Description.CopyAlternatives(source.Description)

            # Copy string property
            if source.CatalogSourceId:
                duplicate.CatalogSourceId = source.CatalogSourceId

            # Deep copy: recursively duplicate subcategories
            if deep and source.SubPossibilitiesOS.Count > 0:
                for sub_pos in source.SubPossibilitiesOS:
                    # Recursively duplicate each subcategory
                    self.__DuplicateSubcategory(sub_pos, duplicate)

            return duplicate

    def __DuplicateSubcategory(self, source_sub, parent_duplicate):
        """
        Helper method to recursively duplicate a subcategory.

        Args:
            source_sub: The source IPartOfSpeech subcategory to duplicate.
            parent_duplicate: The parent IPartOfSpeech to add the duplicate to.

        Returns:
            IPartOfSpeech: The duplicated subcategory.
        """
        # Create new subcategory
        factory = self.project.project.ServiceLocator.GetService(IPartOfSpeechFactory)
        sub_duplicate = factory.Create()

        # Add to parent's SubPossibilitiesOS
        parent_duplicate.SubPossibilitiesOS.Add(sub_duplicate)

        # Copy properties
        sub_duplicate.Name.CopyAlternatives(source_sub.Name)
        sub_duplicate.Abbreviation.CopyAlternatives(source_sub.Abbreviation)
        sub_duplicate.Description.CopyAlternatives(source_sub.Description)

        if source_sub.CatalogSourceId:
            sub_duplicate.CatalogSourceId = source_sub.CatalogSourceId

        # Recursively duplicate nested subcategories
        if source_sub.SubPossibilitiesOS.Count > 0:
            for nested_sub in source_sub.SubPossibilitiesOS:
                self.__DuplicateSubcategory(nested_sub, sub_duplicate)

        return sub_duplicate

    # ========== CATALOG (GOLDEtic) IMPORT METHODS ==========
    #
    # The public API (ImportCatalog / CreateFromCatalog /
    # FixGuidsAgainstCatalog) and the catalog-walking helpers live on
    # CatalogBackedMixin (extracted in Phase 5c). The hooks below tell
    # the mixin how to talk to the POS-specific LCM types.
    #
    # The canonical FW pipeline for POS catalog import lives in
    # SIL.FieldWorks.LexText.Controls.MasterCategory; we reimplement here
    # via the mixin so we don't have to pull in the GUI-side
    # LexTextControls.dll dependency.
    #
    # Phase 2 ownership-ordering lesson applies: the mixin attaches via
    # the 2-arg factory overload (POS placed into its owning list at
    # creation) THEN sets the multistring properties; never sets
    # properties on a free-floating POS.

    # --- CatalogBackedMixin hooks --------------------------------------

    def _get_root_list(self):
        """Return the top-level owner (PartsOfSpeechOA)."""
        return self.project.lp.PartsOfSpeechOA

    def _get_factory(self):
        """Resolve the IPartOfSpeech factory for the mixin's Path B."""
        return self.project.project.ServiceLocator.GetService(IPartOfSpeechFactory)

    def _factory_create_attached(self, guid, parent_obj):
        """
        Path A: try the 2-arg factory overload that creates and attaches
        in one step. parent_obj is either an IPartOfSpeech (subcategory
        case) or None (top-level; we pass the PartsOfSpeechOA list).
        Returns the new LCM object on success, or None to let the mixin
        fall back to Path B.

        Per issue #14, pythonnet may not expose the 2-arg overload on
        the interface variable -- it's an explicit interface impl. So we
        try and let the mixin handle Path B on AttributeError /
        MissingMethodException.
        """
        factory = self._get_factory()
        try:
            if parent_obj is not None:
                return factory.Create(guid, parent_obj)
            return factory.Create(guid, self._get_root_list())
        except Exception:
            return None

    def _path_b_attach(self, new_obj, parent_obj):
        """
        Path B fallback: attach a just-created free-floating POS to the
        right owner. parent_obj is the IPartOfSpeech parent for a
        subcategory, or None for a top-level POS (in which case we
        attach to the PartsOfSpeechOA list).
        """
        if parent_obj is not None:
            parent_obj.SubPossibilitiesOS.Add(new_obj)
        else:
            self._get_root_list().PossibilitiesOS.Add(new_obj)

    def _cast_to_domain(self, raw):
        """Return the IPartOfSpeech view of a raw LCM POS object."""
        return IPartOfSpeech(raw)

    def _set_localized(self, obj, term, abbrev, def_, missing_ws_seen, warnings):
        """Per-WS multistring writes for Name/Abbreviation/Description."""
        self._set_multistring(obj.Name, term, missing_ws_seen, warnings)
        self._set_multistring(obj.Abbreviation, abbrev, missing_ws_seen, warnings)
        self._set_multistring(obj.Description, def_, missing_ws_seen, warnings)

    def _walk_existing(self):
        """
        Yield (IPartOfSpeech, parent_or_None) for every POS in the
        project, walking SubPossibilitiesOS recursively. parent is None
        for top-level POSs. Format matches the mixin's expectation of
        either a 2-tuple or a bare object.
        """
        pos_list = self.project.lp.PartsOfSpeechOA
        if pos_list is None:
            return

        def _walk(collection, parent):
            for raw in collection:
                pos = IPartOfSpeech(raw)
                yield pos, parent
                if pos.SubPossibilitiesOS.Count > 0:
                    yield from _walk(pos.SubPossibilitiesOS, pos)

        yield from _walk(pos_list.PossibilitiesOS, None)

    def _handle_entry_children(self, entry, created_obj, missing_ws_seen, warnings, result):
        """
        POS uses _supports_recursive_entries=True so the mixin recurses
        on entry.children itself; this hook is a no-op.
        """
        pass

    # --- Private Helper Methods ---

    def __ResolveObject(self, pos_or_hvo):
        """
        Resolve HVO or object to IPartOfSpeech.

        Args:
            pos_or_hvo: Either an IPartOfSpeech object or an HVO (int).

        Returns:
            IPartOfSpeech: The resolved POS object.
        """
        if isinstance(pos_or_hvo, int):
            return self.project.Object(pos_or_hvo)
        return pos_or_hvo

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        Args:
            item: The IPartOfSpeech object.

        Returns:
            dict: Dictionary mapping property names to their values.
                Keys are property names, values are the property values.

        Example:
            >>> posOps = POSOperations(project)
            >>> pos = list(posOps.GetAll())[0]
            >>> props = posOps.GetSyncableProperties(pos)
            >>> print(props.keys())
            dict_keys(['Name', 'Abbreviation', 'Description', 'CatalogSourceId'])

        Notes:
            - Returns all MultiString properties (all writing systems)
            - Returns CatalogSourceId string property
            - Does not include SubPossibilitiesOS (subcategories)
            - Does not include InflectionClassesOC or AffixSlotsOC
            - Does not include GUID or HVO of the POS itself
        """
        pos = self.__ResolveObject(item)

        # Get all writing systems for MultiString properties
        # Fix: ILgWritingSystemFactory does not expose a .WritingSystems
        # property; enumerate via the wrapper's WritingSystemOperations.GetAll(),
        # which returns CoreWritingSystemDefinition objects with .Id / .Handle.
        all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}

        props = {}

        # MultiString properties
        for prop_name in ["Name", "Abbreviation", "Description"]:
            if hasattr(pos, prop_name):
                prop_obj = getattr(pos, prop_name)
                ws_values = {}
                for ws_id, ws_handle in all_ws.items():
                    text = ITsString(prop_obj.get_String(ws_handle)).Text
                    if text:  # Only include non-empty values
                        ws_values[ws_id] = text
                if ws_values:  # Only include property if it has values
                    props[prop_name] = ws_values

        # String properties
        if hasattr(pos, "CatalogSourceId") and pos.CatalogSourceId:
            props["CatalogSourceId"] = pos.CatalogSourceId

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """Apply syncable properties (from GetSyncableProperties) onto a POS.

        Inherited from BaseOperations; declared here so static API indexers
        (e.g. the FLExToolsMCP validator) see it on the concrete class. The
        BaseOperations implementation handles every property shape that
        POSOperations.GetSyncableProperties emits (multi-WS Name/Abbreviation/
        Description + plain-string CatalogSourceId), so no per-class
        customisation is needed.
        """
        return super().ApplySyncableProperties(item, props, ws_map, fill_gaps=fill_gaps)

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two parts of speech and return detailed differences.

        Args:
            item1: First POS to compare (from source project).
            item2: Second POS to compare (from target project).
            ops1: Optional POSOperations instance for item1's project.
                 Defaults to self.
            ops2: Optional POSOperations instance for item2's project.
                 Defaults to self.

        Returns:
            tuple: (is_different, differences) where:
                - is_different (bool): True if items differ
                - differences (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> pos1 = project1_posOps.Find("Noun")
            >>> pos2 = project2_posOps.Find("Noun")
            >>> is_diff, diffs = project1_posOps.CompareTo(
            ...     pos1, pos2,
            ...     ops1=project1_posOps,
            ...     ops2=project2_posOps
            ... )
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} -> {val2}")

        Notes:
            - Compares all MultiString properties across all writing systems
            - Compares string properties
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
