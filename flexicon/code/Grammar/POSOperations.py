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
from ..Shared.arg_checks import require_lcm_object
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import FLEx LCM types
from SIL.LCModel import (
    ILexEntryRepository,
    IMoInflAffixSlot,
    IMoInflAffixSlotFactory,
    IPartOfSpeech,
    IPartOfSpeechFactory,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_NullParameterError,  # noqa: F401  -- raised by _ValidateParam
    FP_ParameterError,
    FP_ReadOnlyError,  # noqa: F401  -- raised by _EnsureWriteEnabled
)

# Import LCM casting utilities for pythonnet interface casting
from ..lcm_casting import cast_to_concrete, get_pos_from_msa

# Import string utilities
from ..Shared.string_utils import normalize_match_key, normalize_text

# Import the AffixSlot wrapper (issue #542 read-side pair for CreateAffixSlot)
from .affix_slot import AffixSlot

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

        from flexicon import FLExProject, POSOperations

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
    def Create(self, name, abbreviation, catalogSourceId=None, parent=None):
        """
        Create a new part of speech.

        This is the canonical creation path for both top-level categories
        and subcategories; AddSubcategory delegates to it.

        Args:
            name (str): The name of the POS (e.g., "Noun", "Verb").
            abbreviation (str): Short abbreviation (e.g., "N", "V").
            catalogSourceId (str, optional): Optional catalog identifier for
                linguistic databases (e.g., "GOLD:Noun"). Defaults to None.
            parent: Optional parent IPartOfSpeech object or HVO. If None
                (default), creates a top-level category; if given, creates
                a subcategory of that parent. Defaults to None.

        Returns:
            IPartOfSpeech: The newly created POS object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name or abbreviation is None.
            FP_ParameterError: If name or abbreviation is empty, or if a
                top-level POS with this name already exists.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Create("Noun", "N")
            >>> print(posOps.GetName(noun))
            Noun

            >>> proper_noun = posOps.Create("Proper Noun", "PN", "GOLD:Noun")
            >>> print(posOps.GetAbbreviation(proper_noun))
            PN

            >>> # A subcategory is just a Create with a parent
            >>> proper = posOps.Create("Proper Noun", "PN", parent=noun)

        Notes:
            - Top-level names must be unique within the project (the
              pre-existing Exists check); subcategory names are not
              uniqueness-checked, preserving AddSubcategory's behaviour.
            - Abbreviations don't need to be unique but should be distinct
            - CatalogSourceId links to linguistic ontologies (e.g., GOLD)
            - The POS is created in the default analysis writing system

        See Also:
            AddSubcategory, Delete, Exists, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")
        self._ValidateParam(abbreviation, "abbreviation")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")
        if not abbreviation or not abbreviation.strip():
            raise FP_ParameterError("Abbreviation cannot be empty")

        parent_pos = None
        if parent is not None:
            self._ValidateParam(parent, "parent")
            parent_pos = self.__ResolveObject(parent)

        label = f"Add subcategory '{name}'" if parent_pos is not None else f"Create part of speech '{name}'"

        # If the caller supplied a "GOLD:..." catalog id, defer to the
        # catalog path so the POS gets the canonical GUID and any extra
        # WS data the catalog provides. We then overlay the user's
        # name/abbreviation on top so explicit args still win.
        if catalogSourceId and catalogSourceId.upper().startswith("GOLD:"):
            wsHandle = self.project.project.DefaultAnalWs
            with self._TransactionCM(label):
                new_pos = self.CreateFromCatalog(catalogSourceId, parent=parent_pos)
                # Overlay user-supplied name and abbreviation in the
                # analysis WS (catalog values stay in other WSes).
                mkstr_name = TsStringUtils.MakeString(name, wsHandle)
                new_pos.Name.set_String(wsHandle, mkstr_name)
                mkstr_abbr = TsStringUtils.MakeString(abbreviation, wsHandle)
                new_pos.Abbreviation.set_String(wsHandle, mkstr_abbr)
                return new_pos

        # Check if POS already exists (top-level creates only, preserving
        # AddSubcategory's no-uniqueness-check behaviour for children).
        if parent_pos is None and self.Exists(name):
            raise FP_ParameterError(f"Part of Speech '{name}' already exists")

        # Get the writing system handle
        wsHandle = self.project.project.DefaultAnalWs

        # Create the new POS using the factory
        factory = self.project.project.ServiceLocator.GetService(IPartOfSpeechFactory)
        with self._TransactionCM(label):
            new_pos = factory.Create()

            # Attach to the parent subcategory list or the top-level POS
            # list (must be done before setting properties)
            if parent_pos is not None:
                parent_pos.SubPossibilitiesOS.Add(new_pos)
            else:
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

        with self._TransactionCM("Delete part of speech"):
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

        with self._TransactionCM(f"Set part of speech name '{name}'"):
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

        with self._TransactionCM(f"Set part of speech abbreviation '{abbr}'"):
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
    def GetParent(self, pos_or_hvo):
        """
        Get the parent category of a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.

        Returns:
            IPartOfSpeech: The owning part of speech, or None if this POS
            is top-level (owned by the PartsOfSpeechOA possibility list
            rather than by another category).

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> noun = posOps.Find("Noun")
            >>> proper = posOps.AddSubcategory(noun, "Proper Noun", "PN")
            >>> posOps.GetName(posOps.GetParent(proper))
            'Noun'

            >>> # Walk the hierarchy upward to the root
            >>> cat = proper
            >>> while cat is not None:
            ...     print(posOps.GetName(cat))
            ...     cat = posOps.GetParent(cat)
            Proper Noun
            Noun

        Notes:
            - Returns None for top-level categories: their Owner is the
              ICmPossibilityList at ``lp.PartsOfSpeechOA``, which is not a
              possibility and therefore not a parent category.
            - The owner is discriminated by ``ClassName`` rather than by
              attempting a CLR cast and catching the failure, matching
              ``__ResolveObject``'s ClassName-gated shape (contract C2).
              An owner that is a POS is routed back through
              ``__ResolveObject`` so the returned object is cast to
              ``IPartOfSpeech`` and exposes subtype-only members --
              ``Owner`` alone hands back a bare ``ICmObject``.
            - This is the inverse of GetSubcategories: for any subcategory
              ``s`` of ``p``, ``GetParent(s) is p``.

        See Also:
            GetSubcategories, AddSubcategory, GetAll
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)

        owner = getattr(pos, "Owner", None)
        if owner is None:
            return None

        # Top-level POSs are owned by the PartsOfSpeechOA possibility list
        # ("CmPossibilityList"); only a subcategory is owned by another
        # "PartOfSpeech". Anything else (an owner with no ClassName at all,
        # e.g. a non-LCM stand-in) is treated as "no parent category"
        # rather than raising.
        if getattr(owner, "ClassName", None) != "PartOfSpeech":
            return None

        return self.__ResolveObject(owner)

    @OperationsMethod
    def AddSubcategory(self, pos_or_hvo, name, abbreviation, catalogSourceId=None):
        """
        Add a subcategory to a part of speech.

        Thin wrapper over Create with parent=pos_or_hvo; all creation
        logic (including the "GOLD:..." catalog path) lives on Create.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO to add subcategory to.
            name (str): The name of the subcategory.
            abbreviation (str): Short abbreviation for the subcategory.
            catalogSourceId (str, optional): Optional catalog identifier for
                linguistic databases (e.g., "GOLD:Noun"). Defaults to None.

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

            >>> proper_noun = posOps.AddSubcategory(noun, "Proper Noun", "PN", "GOLD:Noun")

        Notes:
            - Equivalent to ``Create(name, abbreviation,
              catalogSourceId=catalogSourceId, parent=pos_or_hvo)``.
            - If the catalog GUID already exists, the existing item is
              returned with name/abbreviation overlaid, not re-parented
              (same idempotency as CreateFromCatalog).

        See Also:
            Create, RemoveSubcategory, GetSubcategories
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        # Bracketed per D5 (the scanner cannot see through same-class
        # delegation): joins Create's inner transaction via nesting
        # (B1) rather than opening a separate undo unit. House pattern:
        # Shared/FilterOperations.ImportFilter, Shared/MediaOperations.
        with self._TransactionCM(f"Add subcategory '{name}'"):
            return self.Create(
                name,
                abbreviation,
                catalogSourceId=catalogSourceId,
                parent=pos_or_hvo,
            )

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
        with self._TransactionCM("Remove subcategory"):
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
    def GetInflectionClasses(self, pos_or_hvo, recursive=False):
        """
        Get all inflection classes associated with a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.
            recursive (bool): If False (default), returns only the inflection
                classes directly owned by the POS. If True, also walks each
                class's ``IMoInflClass.SubclassesOC`` depth-first, so nested
                subclass hierarchies are included. Cycle-guarded.

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

            >>> # Include nested subclasses as well
            >>> all_classes = posOps.GetInflectionClasses(verb, recursive=True)

        Notes:
            - Inflection classes define morphological paradigms
            - Each POS can have multiple inflection classes
            - Returns empty list if no inflection classes are defined
            - Used for morphological analysis and generation
            - Use ``project.InflectionFeatures.InflectionClassGetName`` /
              ``InflectionClassGetAbbreviation`` to read each class's
              Name/Abbreviation multistrings

        See Also:
            GetAffixSlots, GetStemNames
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)

        # IPartOfSpeech has InflectionClassesOC
        top_level = list(pos.InflectionClassesOC)
        if not recursive:
            return top_level
        return self.__CollectInflectionClassesRecursive(top_level)

    def __CollectInflectionClassesRecursive(self, classes):
        """Depth-first walk of ``IMoInflClass.SubclassesOC``.

        Cycle-guarded on HVO so a pathological subclass loop cannot
        recurse forever. Parent classes are yielded before their
        subclasses (pre-order).
        """
        result = []
        seen = set()

        def _visit(ic):
            hvo = getattr(ic, "Hvo", None)
            if hvo is not None:
                hvo = int(hvo)
                if hvo in seen:
                    return
                seen.add(hvo)
            result.append(ic)
            subclasses = getattr(ic, "SubclassesOC", None) or []
            for sub in subclasses:
                _visit(sub)

        for ic in classes:
            _visit(ic)
        return result

    @wrap_enumerable
    @OperationsMethod
    def GetStemNames(self, pos_or_hvo):
        """
        Get all stem names owned by a part of speech.

        Stem names (``IMoStemName``) are the catalog of named stem
        variants a POS defines (e.g. "root", "stem 1", "stem 2"); stem
        allomorphs point at one via ``IMoStemAllomorph.StemNameRA`` (see
        ``AllomorphOperations.GetStemName`` / ``SetStemName``).

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.

        Returns:
            list: List of IMoStemName objects (empty list if none).

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> verb = posOps.Find("Verb")
            >>> for stem_name in posOps.GetStemNames(verb):
            ...     print(posOps.GetStemNameText(stem_name))
            root
            stem 1

        Notes:
            - Returns the raw IMoStemName objects, not text: use
              GetStemNameText / GetStemNameAbbreviation to read their
              multistrings, GetStemNameRegionCount for their regions
            - Returns empty list if the POS defines no stem names

        See Also:
            GetInflectionClasses, GetStemNameText, GetStemNameRegionCount
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)

        # IPartOfSpeech has StemNamesOC
        return list(pos.StemNamesOC)

    @OperationsMethod
    def GetStemNameText(self, stem_name_or_hvo, wsHandle=None):
        """
        Get the name text of a stem name (``IMoStemName.Name`` multistring).

        Args:
            stem_name_or_hvo: The IMoStemName object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The stem name text, or empty string if not set. Never
            ``"***"`` -- the FLEx empty-multistring placeholder is
            normalized to ``""``.

        Raises:
            FP_NullParameterError: If stem_name_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> verb = posOps.Find("Verb")
            >>> stem_names = posOps.GetStemNames(verb)
            >>> if stem_names:
            ...     print(posOps.GetStemNameText(stem_names[0]))
            root

        See Also:
            GetStemNames, GetStemNameAbbreviation, GetStemNameRegionCount
        """
        self._ValidateParam(stem_name_or_hvo, "stem_name_or_hvo")

        stem_name = self.__ResolveStemName(stem_name_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name_ms = getattr(stem_name, "Name", None)
        if name_ms is None:
            return ""
        text = ITsString(name_ms.get_String(wsHandle)).Text
        # _NormalizeMultiString turns "***" into "" but leaves None alone;
        # this method promises a str, so coerce the None-on-unset case too.
        return self._NormalizeMultiString(text) or ""

    @OperationsMethod
    def GetStemNameAbbreviation(self, stem_name_or_hvo, wsHandle=None):
        """
        Get the abbreviation of a stem name (``IMoStemName.Abbreviation``
        multistring).

        Args:
            stem_name_or_hvo: The IMoStemName object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The stem name abbreviation, or empty string if not set.
            Never ``"***"``.

        Raises:
            FP_NullParameterError: If stem_name_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> verb = posOps.Find("Verb")
            >>> stem_names = posOps.GetStemNames(verb)
            >>> if stem_names:
            ...     print(posOps.GetStemNameAbbreviation(stem_names[0]))

        See Also:
            GetStemNames, GetStemNameText, GetStemNameRegionCount
        """
        self._ValidateParam(stem_name_or_hvo, "stem_name_or_hvo")

        stem_name = self.__ResolveStemName(stem_name_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        abbr_ms = getattr(stem_name, "Abbreviation", None)
        if abbr_ms is None:
            return ""
        text = ITsString(abbr_ms.get_String(wsHandle)).Text
        return self._NormalizeMultiString(text) or ""

    @OperationsMethod
    def GetStemNameRegionCount(self, stem_name_or_hvo):
        """
        Get the number of regions on a stem name (``IMoStemName.RegionsOC``).

        Args:
            stem_name_or_hvo: The IMoStemName object or HVO.

        Returns:
            int: The region count, or 0 when the collection is absent.

        Raises:
            FP_NullParameterError: If stem_name_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> verb = posOps.Find("Verb")
            >>> for stem_name in posOps.GetStemNames(verb):
            ...     print(posOps.GetStemNameText(stem_name),
            ...           posOps.GetStemNameRegionCount(stem_name))
            root 0

        See Also:
            GetStemNames, GetStemNameText
        """
        self._ValidateParam(stem_name_or_hvo, "stem_name_or_hvo")

        stem_name = self.__ResolveStemName(stem_name_or_hvo)

        regions = getattr(stem_name, "RegionsOC", None)
        return regions.Count if regions else 0

    def __ResolveStemName(self, stem_name_or_hvo):
        """Resolve HVO or object to an IMoStemName.

        ``cast_to_concrete`` is total -- an unrecognized ``ClassName``
        (or a non-LCM input) yields the original object unchanged, so
        this resolver never raises on a miss, mirroring
        ``__ResolveObject``'s shape. Read methods guard member access
        with ``getattr`` instead.
        """
        if isinstance(stem_name_or_hvo, int):
            obj = self.project.Object(stem_name_or_hvo)
        else:
            require_lcm_object(stem_name_or_hvo, "IMoStemName")
            obj = self._UnwrapLcmObject(stem_name_or_hvo)

        return cast_to_concrete(obj)

    @wrap_enumerable
    @OperationsMethod
    def GetAffixSlots(self, pos_or_hvo):
        """
        Get all affix slots associated with a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.

        Returns:
            list: List of AffixSlot wrapper objects (empty list if none).
            Each wrapper exposes ``.name`` (str), ``.optional`` (bool), and
            ``.affixes`` (the IMoInflAffMsa objects filling the slot), and
            still proxies raw LCM member access (``.Name``, ``.Optional``,
            ``.Hvo``) through to the underlying IMoInflAffixSlot for
            backward compatibility with existing callers.

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> posOps = POSOperations(project)
            >>> verb = posOps.Find("Verb")
            >>> slots = posOps.GetAffixSlots(verb)
            >>> for slot in slots:
            ...     print(slot.name)
            Tense
            Aspect
            Mood

        Notes:
            - Affix slots define positions for affixes in morphological templates
            - Each POS can have multiple affix slots
            - Returns empty list if no affix slots are defined
            - Used for morphological parsing and generation

        See Also:
            GetInflectionClasses, CreateAffixSlot, GetSlotName, IsSlotOptional,
            GetAffixesInSlot
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)

        # IPartOfSpeech has AffixSlotsOC
        return [AffixSlot(slot) for slot in pos.AffixSlotsOC]

    @OperationsMethod
    def CreateAffixSlot(self, pos, name, optional=False):
        """
        Create an inflectional affix slot owned by a part of speech.

        Access via FLExProject as ``project.POS.CreateAffixSlot``. The new
        slot is attached to ``IPartOfSpeech.AffixSlotsOC`` before its Name
        or Optional is written. Place it on a template with
        ``project.MorphRules.AddSlotToTemplate``.

        Args:
            pos: The IPartOfSpeech object or HVO that will own the slot.
            name (str): Slot name, written in the analysis writing system.
            optional (bool): Whether the slot may be left empty. Defaults
                to False. A new FLEx affix slot is obligatory; pass True
                to create an optional slot.

        Returns:
            AffixSlot: A wrapper around the newly created IMoInflAffixSlot,
            exposing ``.name`` (str), ``.optional`` (bool), and ``.affixes``,
            while still proxying raw LCM member access (``.Name``,
            ``.Optional``, ``.Hvo``) through to the underlying
            IMoInflAffixSlot for backward compatibility. Pass it directly
            to ``MorphRules.AddSlotToTemplate`` or
            ``MSA.SetInflAffMsaSlots``; both unwrap it automatically.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If pos or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> verb = project.POS.Find("Verb")
            >>> slot = project.POS.CreateAffixSlot(verb, "PossConcord", optional=False)
            >>> slot.name
            'PossConcord'

        See Also:
            GetAffixSlots
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(pos, "pos")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        pos = self.__ResolveObject(pos)
        wsHandle = self.project.project.DefaultAnalWs

        factory = self.project.project.ServiceLocator.GetService(IMoInflAffixSlotFactory)

        with self._TransactionCM(f"Create affix slot '{name}'"):
            slot = factory.Create()

            # Attach before property writes (Phase 2 ownership rule).
            pos.AffixSlotsOC.Add(slot)

            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            slot.Name.set_String(wsHandle, mkstr_name)
            # Boolean property is Optional (clr reflection, SIL.LCModel 11).
            slot.Optional = optional

            return AffixSlot(slot)

    @OperationsMethod
    def GetSlotName(self, slot_or_hvo, wsHandle=None):
        """
        Get the name of an inflectional affix slot.

        Read-side pair for ``CreateAffixSlot`` (issue #542).
        ``IMoInflAffixSlot.Name`` is an ``IMultiUnicode``, not a string;
        this method reads it and returns plain text.

        Args:
            slot_or_hvo: The IMoInflAffixSlot object, its HVO, or an
                AffixSlot wrapper (from ``GetAffixSlots`` or
                ``AffixTemplate.prefix_slots``/etc.).
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The slot name, or empty string if not set (FLEx's
            ``***`` null marker is normalized to empty).

        Raises:
            FP_NullParameterError: If slot_or_hvo is None.
            FP_ParameterError: If slot_or_hvo does not resolve to an
                IMoInflAffixSlot.

        Example:
            >>> posOps = POSOperations(project)
            >>> verb = posOps.Find("Verb")
            >>> slot = posOps.CreateAffixSlot(verb, "Tense")
            >>> posOps.GetSlotName(slot)
            'Tense'

        See Also:
            SetSlotName, IsSlotOptional, GetAffixesInSlot
        """
        self._ValidateParam(slot_or_hvo, "slot_or_hvo")

        slot = self.__ResolveSlot(slot_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(slot.Name.get_String(wsHandle)).Text
        return normalize_text(name)

    @OperationsMethod
    def SetSlotName(self, slot_or_hvo, name, wsHandle=None):
        """
        Set the name of an inflectional affix slot.

        Args:
            slot_or_hvo: The IMoInflAffixSlot object, its HVO, or an
                AffixSlot wrapper.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If slot_or_hvo or name is None.
            FP_ParameterError: If name is empty, or slot_or_hvo does not
                resolve to an IMoInflAffixSlot.

        Example:
            >>> posOps = POSOperations(project)
            >>> slot = posOps.CreateAffixSlot(verb, "Tense")
            >>> posOps.SetSlotName(slot, "Aspect")

        See Also:
            GetSlotName, IsSlotOptional, SetSlotOptional
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(slot_or_hvo, "slot_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        slot = self.__ResolveSlot(slot_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)

        with self._TransactionCM(f"Set affix slot name '{name}'"):
            slot.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def IsSlotOptional(self, slot_or_hvo):
        """
        Check whether an inflectional affix slot may be left empty.

        Args:
            slot_or_hvo: The IMoInflAffixSlot object, its HVO, or an
                AffixSlot wrapper.

        Returns:
            bool: True if the slot is optional, False if obligatory
            (FLEx's default for a newly-created slot).

        Raises:
            FP_NullParameterError: If slot_or_hvo is None.
            FP_ParameterError: If slot_or_hvo does not resolve to an
                IMoInflAffixSlot.

        Example:
            >>> posOps = POSOperations(project)
            >>> slot = posOps.CreateAffixSlot(verb, "PossConcord", optional=True)
            >>> posOps.IsSlotOptional(slot)
            True

        See Also:
            SetSlotOptional, GetSlotName
        """
        self._ValidateParam(slot_or_hvo, "slot_or_hvo")

        slot = self.__ResolveSlot(slot_or_hvo)
        return bool(slot.Optional)

    @OperationsMethod
    def SetSlotOptional(self, slot_or_hvo, optional):
        """
        Set whether an inflectional affix slot may be left empty.

        Args:
            slot_or_hvo: The IMoInflAffixSlot object, its HVO, or an
                AffixSlot wrapper.
            optional (bool): True to make the slot optional, False to make
                it obligatory.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If slot_or_hvo is None.
            FP_ParameterError: If slot_or_hvo does not resolve to an
                IMoInflAffixSlot.

        Example:
            >>> posOps = POSOperations(project)
            >>> slot = posOps.CreateAffixSlot(verb, "PossConcord")
            >>> posOps.SetSlotOptional(slot, True)

        See Also:
            IsSlotOptional, SetSlotName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(slot_or_hvo, "slot_or_hvo")

        slot = self.__ResolveSlot(slot_or_hvo)

        with self._TransactionCM(f"Set affix slot optional={bool(optional)}"):
            slot.Optional = bool(optional)

    @wrap_enumerable
    @OperationsMethod
    def GetAffixesInSlot(self, slot_or_hvo):
        """
        Get the inflectional-affix MSAs that fill an affix slot.

        Args:
            slot_or_hvo: The IMoInflAffixSlot object, its HVO, or an
                AffixSlot wrapper.

        Returns:
            list: IMoInflAffMsa objects whose SlotsRC contains this slot
            (empty list if none).

        Raises:
            FP_NullParameterError: If slot_or_hvo is None.
            FP_ParameterError: If slot_or_hvo does not resolve to an
                IMoInflAffixSlot.

        Example:
            >>> posOps = POSOperations(project)
            >>> slot = posOps.CreateAffixSlot(verb, "Tense")
            >>> project.MSA.SetInflAffMsaSlots(sense, [slot])
            >>> affixes = posOps.GetAffixesInSlot(slot)
            >>> len(affixes)
            1

        Notes:
            - Read via ``IMoInflAffixSlot.Affixes``, the direct
              back-reference to every ``IMoInflAffMsa`` whose ``SlotsRC``
              contains this slot (confirmed by live reflection: returns
              ``IEnumerable<IMoInflAffMsa>``). This is the single most
              direct LCM path -- it is the exact inverse of
              ``MSAOperations.GetInflAffMsaSlots`` (issue #543), which
              reads ``IMoInflAffMsa.SlotsRC`` from the MSA side. No
              repository scan or entry walk is needed.

        See Also:
            GetAffixSlots, MSA.GetInflAffMsaSlots, MSA.SetInflAffMsaSlots
        """
        self._ValidateParam(slot_or_hvo, "slot_or_hvo")

        slot = self.__ResolveSlot(slot_or_hvo)

        affixes = getattr(slot, "Affixes", None)
        if affixes is None:
            return []
        return list(affixes)

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
        # Create new subcategory. Reached only from inside Duplicate's
        # bracket, so this transaction joins that one (nesting-aware per B1).
        # Stated anyway so the site is grep-auditable per D5.
        factory = self.project.project.ServiceLocator.GetService(IPartOfSpeechFactory)

        with self._TransactionCM("Duplicate subcategory"):
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
            # Reached from inside the mixin's "Create ... from catalog"
            # bracket (catalog_backed.py), so this joins that transaction
            # rather than opening its own (nesting-aware per B1). Stated
            # anyway so the site is grep-auditable per D5.
            with self._TransactionCM("Create part of speech from catalog"):
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
        # Both branches mutate, so the owner-shape guard sits inside the
        # bracket. Joins the mixin's catalog bracket per B1.
        with self._TransactionCM("Attach part of speech from catalog"):
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
            IPartOfSpeech: The resolved POS object, cast to the concrete
            ``IPartOfSpeech`` interface when its ``ClassName`` is
            ``"PartOfSpeech"`` (contract C2). ``self.project.Object(hvo)``
            returns a bare ``ICmObject``; without this cast, a caller
            reaching this method via an HVO (rather than an already-typed
            object from, e.g., ``GetAll()``, which already casts via
            ``IPartOfSpeech(raw)``) would silently lose access to every
            subtype-only member -- including the four PRE-EXISTING
            ``GetSyncableProperties`` fields (``Name``/``Abbreviation``/
            ``Description``/``CatalogSourceId``), not just the two new
            feature-struct properties T7 adds (see evidence/live-T7.md,
            prediction P1).

            Any ``ClassName`` other than ``"PartOfSpeech"`` (or a non-LCM
            input with no ``ClassName`` at all, e.g. a GUID ``str`` --
            OUT of scope for this method, folded into T12) is returned
            UNCHANGED -- this method never raises on a miss, mirroring
            ``MSAOperations.__GetMsaObject``'s ClassName-discriminated,
            never-raising shape.
        """
        if isinstance(pos_or_hvo, int):
            obj = self.project.Object(pos_or_hvo)
        else:
            require_lcm_object(pos_or_hvo, "IPartOfSpeech")
            obj = self._UnwrapLcmObject(pos_or_hvo)

        if getattr(obj, "ClassName", None) == "PartOfSpeech":
            return IPartOfSpeech(obj)
        return obj

    def __ResolveSlot(self, slot_or_hvo):
        """
        Resolve HVO, raw LCM object, or AffixSlot wrapper to IMoInflAffixSlot.

        Unlike ``__ResolveObject`` (which never raises on a ClassName
        miss -- deliberately, per its own docstring), this resolver
        *really casts*: it performs an actual pythonnet interface cast to
        ``IMoInflAffixSlot`` and raises ``FP_ParameterError`` when the cast
        fails, rather than silently handing back an object that is missing
        the members every slot reader/writer method here needs (``Name``,
        ``Optional``, ``Affixes``). The 4.10.0 live gate (commit
        9218b3c) found resolvers "that never cast" across the #455-#508
        series; this method exists specifically to not repeat that shape.

        Args:
            slot_or_hvo: An ``IMoInflAffixSlot`` object, its HVO (int), or
                an ``AffixSlot`` wrapper (unwrapped via
                ``_UnwrapLcmObject`` before casting).

        Returns:
            IMoInflAffixSlot: The resolved, cast slot object.

        Raises:
            FP_ParameterError: If the resolved object cannot be cast to
                IMoInflAffixSlot (wrong type, or a stale/invalid HVO).
        """
        if isinstance(slot_or_hvo, int):
            obj = self.project.Object(slot_or_hvo)
        else:
            obj = self._UnwrapLcmObject(slot_or_hvo)

        try:
            return IMoInflAffixSlot(obj)
        except Exception:
            raise FP_ParameterError(
                "slot_or_hvo must be an IMoInflAffixSlot, its HVO, or an "
                f"AffixSlot wrapper; got {obj!r}"
            )

    # ========== SYNC INTEGRATION METHODS ==========
    #
    # Closes issue #252 (spec feature-structure-sync-gap, task T7):
    # PartOfSpeech has TWO feature-struct-owning properties --
    # DefaultFeaturesOA (slot="Default") and InherFeatValOA
    # (slot="InherFeatVal"), the frozen C1 "PartOfSpeech" row in
    # FEATURE_STRUC_OWNER_TABLE (Shared/lcm_constants.py) -- neither of
    # which was ever captured or applied, so a synced POS carried correct
    # Name/Abbreviation/Description/CatalogSourceId but a permanently null
    # feature structure. Shape mirrors MSAOperations' #251 fix
    # (:841-1158), but T7 additionally fixes an independent C2 hole in
    # __ResolveObject itself: unlike GetAll() (which already casts every
    # POS via `IPartOfSpeech(raw)`), a POS reached through this method via
    # a bare HVO was returned as an uncast `ICmObject`, silently dropping
    # even the four PRE-EXISTING scalar/multistring properties on that
    # entry path (evidence/live-T7.md, prediction P1). Both are fixed
    # together since __ResolveObject is the single choke point both
    # methods route through.

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        Args:
            item: The IPartOfSpeech object, or its HVO (int) -- resolved
                and cast via ``__ResolveObject`` (contract C2).

        Returns:
            dict: Dictionary mapping property names to their values.
                Keys are property names, values are the property values.
                In addition to the pre-existing scalar/multistring keys,
                emits (per the frozen C1 "PartOfSpeech" table row, when
                the owning property is non-None -- C6 presence, not
                truthiness):

                - ``DefaultFeatures`` / ``DefaultFeaturesGuid`` --
                  ``DefaultFeaturesOA`` (C4 recursive-dict spec / str
                  GUID).
                - ``InherFeatVal`` / ``InherFeatValGuid`` --
                  ``InherFeatValOA``.

                An owning property that is present but genuinely empty
                (an ``IFsFeatStruc`` with zero ``FeatureSpecsOC`` entries)
                still emits BOTH its keys -- ``_GetFeatureStruc`` never
                returns ``None`` for a non-None struct (C4). A NULL owning
                property omits both keys entirely.

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
            - Feature-struct capture (``DefaultFeatures``/``InherFeatVal``)
              is entirely ``.ClassName``-driven, delegating to
              ``BaseOperations._ResolveFeatureStrucOwner``/
              ``_GetFeatureStruc`` (C1/C4) -- zero ``hasattr`` probes on
              either feature-struct property. The two ``hasattr`` calls
              below (on ``Name``/``Abbreviation``/``Description`` and
              ``CatalogSourceId``) are PRE-EXISTING and deliberately kept
              (lead ruling 3): once ``__ResolveObject`` casts, they are
              redundant but harmless, and removing them is out of this
              task's scope.
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

        # Feature-struct properties (C1 "PartOfSpeech" table row, T7/#252).
        # slot= is REQUIRED here (unlike MoStemMsa's single-row None) --
        # PartOfSpeech has two rows in FEATURE_STRUC_OWNER_TABLE.
        self.__CaptureFeatureStrucProp(props, pos, "Default", "DefaultFeatures")
        self.__CaptureFeatureStrucProp(props, pos, "InherFeatVal", "InherFeatVal")

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """
        Apply syncable properties (from GetSyncableProperties) onto a POS.

        Handles the two C1 "PartOfSpeech" feature-struct key-pairs
        (``DefaultFeatures``/``DefaultFeaturesGuid``,
        ``InherFeatVal``/``InherFeatValGuid``) directly; everything else in
        ``props`` (the pre-existing multi-WS Name/Abbreviation/Description
        + plain-string CatalogSourceId shape) is delegated to
        ``BaseOperations.ApplySyncableProperties`` unchanged.

        Args:
            item: Target POS (already created + owned + GUID-assigned by
                the caller), or its HVO (int) -- resolved and cast via
                ``__ResolveObject`` (C2).
            props: dict produced by GetSyncableProperties (or built by a
                caller following the same shape).
            ws_map: Optional source->target writing-system Id mapping.
                Unused by the feature-struct branches (which resolve by
                GUID, not writing system); passed through to the base
                loop.
            fill_gaps: Passed through to the base loop. Has no additional
                effect on the feature-struct branches, which are always
                purely additive/idempotent by GUID.

        Raises:
            FP_ParameterError: If ``item`` is None, ``props`` is not a
                dict, or (C7) a ``<Name>``/``<Name>Guid`` spec references a
                feature, value, or feature-structure-type GUID that does
                not exist in the target project -- naming the unresolved
                GUID and instructing the caller to sync the feature system
                first.

        Notes:
            - The two feature-struct keys are POPPED out of ``props``
              (via a filtered copy) BEFORE calling ``super()`` (C6):
              ``BaseOperations._apply_props_loop`` dispatches on
              ``isinstance(value, dict)`` and would otherwise route a C4
              dict into the multi-writing-system multistring path and
              silently drop it.
            - Gates on KEY PRESENCE, never truthiness (C6): a present-but-
              empty feature structure (``<Name>Guid`` set, ``<Name>``
              absent/``{}``) is a real, empty-but-attached
              ``IFsFeatStruc`` on the source and must still create/attach
              an empty struct on the target.
        """
        if item is None:
            raise FP_ParameterError("ApplySyncableProperties: item is None")
        if not isinstance(props, dict):
            raise FP_ParameterError(
                f"ApplySyncableProperties: props must be a dict, got "
                f"{type(props).__name__}"
            )

        pos = self.__ResolveObject(item)

        # Pop the two feature-struct key-pairs out of props BEFORE calling
        # super() (C6) -- BaseOperations._apply_props_loop dispatches a
        # dict value into the multistring path and would drop a C4 dict
        # silently at that layer instead of raising.
        base_props = {
            k: v for k, v in props.items() if k not in self.__FEATURE_STRUC_KEYS
        }
        super().ApplySyncableProperties(pos, base_props, ws_map, fill_gaps=fill_gaps)

        self.__ApplyFeatureStrucProp(pos, "Default", "DefaultFeatures", props)
        self.__ApplyFeatureStrucProp(pos, "InherFeatVal", "InherFeatVal", props)

    # ------------------------------------------------------------------
    # Feature-struct sync internals (T7/#252)
    # ------------------------------------------------------------------

    # The four props keys handled directly by ApplySyncableProperties's
    # feature-struct branches -- must be excluded from the base-loop
    # pass-through (C6). Kept as one tuple so the pop-filter and any
    # future audit share a single source of truth.
    __FEATURE_STRUC_KEYS = (
        "DefaultFeatures", "DefaultFeaturesGuid",
        "InherFeatVal", "InherFeatValGuid",
    )

    def __CaptureFeatureStrucProp(self, props, pos, slot, key):
        """
        Capture one C1 "PartOfSpeech" feature-struct row into ``props``,
        in place.

        Args:
            props: The dict being built by GetSyncableProperties;
                mutated in place.
            pos: The POS object (already resolved via ``__ResolveObject``).
            slot: ``"Default"`` | ``"InherFeatVal"`` -- REQUIRED (unlike
                MoStemMsa's single-row ``None``, PartOfSpeech has TWO rows
                in ``FEATURE_STRUC_OWNER_TABLE``) -- passed straight
                through to ``_ResolveFeatureStrucOwner`` (C1).
            key: The props key stem (e.g. ``"DefaultFeatures"``) -- the C1
                table's props-key column. ``f"{key}Guid"`` is the sibling
                GUID key.

        Notes:
            - Delegates the owner/property resolution entirely to
              ``BaseOperations._ResolveFeatureStrucOwner`` -- no
              ``hasattr`` probe, no local cast.
            - Only emits keys when the owning property is non-None (a
              present-but-empty struct still emits both keys, since
              ``_GetFeatureStruc`` never returns ``None`` for a non-None
              struct -- C4). A null owning property emits neither key,
              which is the PRESENCE gate C6 requires on the apply side.
        """
        concrete_owner, prop_name = self._ResolveFeatureStrucOwner(pos, slot=slot)
        struct = getattr(concrete_owner, prop_name)
        if struct is not None:
            props[key] = self._GetFeatureStruc(struct)
            props[f"{key}Guid"] = str(struct.Guid)

    def __ApplyFeatureStrucProp(self, pos, slot, key, props):
        """
        Apply one C1 "PartOfSpeech" feature-struct row from ``props`` onto
        ``pos``, if present.

        Args:
            pos: The POS object (already resolved via ``__ResolveObject``).
            slot: ``"Default"`` | ``"InherFeatVal"``.
            key: The props key stem (e.g. ``"DefaultFeatures"``).
            props: The ORIGINAL (unfiltered) props dict passed to
                ``ApplySyncableProperties`` -- read-only here.

        Notes:
            - Gates on KEY PRESENCE, never truthiness (C6):
              ``if key in props or guid_key in props`` -- a present-but-
              empty source struct carries ``<Name>Guid`` with ``<Name>``
              absent (or ``{}``), and must still create/attach an empty
              target struct, not be skipped as "source has none".
            - ``on_unresolved="raise"`` unconditionally (C7): an
              unresolvable feature/value/type GUID must never be
              silently dropped for a POS sync.
        """
        guid_key = f"{key}Guid"
        if key in props or guid_key in props:
            concrete_owner, prop_name = self._ResolveFeatureStrucOwner(
                pos, slot=slot
            )
            spec = props.get(key) or {}
            struct_guid = props.get(guid_key)
            self._ApplyFeatureStruc(
                concrete_owner,
                prop_name,
                spec,
                struct_guid=struct_guid,
                on_unresolved="raise",
                label=f"PartOfSpeech ({prop_name})",
            )

    def __ReadPOSFeatureStrucSpec(self, pos, slot):
        """Return a C4 feature-struct dict for one PartOfSpeech slot, or None."""
        concrete_owner, prop_name = self._ResolveFeatureStrucOwner(pos, slot=slot)
        struct = getattr(concrete_owner, prop_name)
        if struct is None:
            return None
        return self._GetFeatureStruc(struct)

    def __WritePOSFeatureStrucSpec(self, pos, slot, spec, struct_guid=None):
        """Apply a C4 feature-struct dict onto one PartOfSpeech slot."""
        if spec is None:
            raise FP_ParameterError("spec cannot be None; pass {} to clear entries")
        if not isinstance(spec, dict):
            raise FP_ParameterError(
                f"spec must be a dict (C4 feature-struct shape), got {type(spec).__name__}"
            )

        concrete_owner, prop_name = self._ResolveFeatureStrucOwner(pos, slot=slot)
        self._ApplyFeatureStruc(
            concrete_owner,
            prop_name,
            spec,
            struct_guid=struct_guid,
            on_unresolved="raise",
            label=f"PartOfSpeech ({prop_name})",
        )

    @OperationsMethod
    def GetDefaultFeatures(self, pos_or_hvo):
        """
        Read ``DefaultFeaturesOA`` as a C4 feature-structure dict.

        Args:
            pos_or_hvo: ``IPartOfSpeech`` or HVO.

        Returns:
            dict or None: Recursive feature-structure spec (same shape as
            ``GetSyncableProperties()['DefaultFeatures']`` when present),
            or ``None`` when ``DefaultFeaturesOA`` is unset.

        Example:
            >>> noun = project.POS.Find("Noun")
            >>> spec = project.POS.GetDefaultFeatures(noun)
            >>> if spec:
            ...     print(spec.get("specs", {}))
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")
        pos = self.__ResolveObject(pos_or_hvo)
        return self.__ReadPOSFeatureStrucSpec(pos, "Default")

    @OperationsMethod
    def SetDefaultFeatures(self, pos_or_hvo, spec, struct_guid=None):
        """
        Replace ``DefaultFeaturesOA`` from a C4 feature-structure dict.

        Args:
            pos_or_hvo: ``IPartOfSpeech`` or HVO.
            spec (dict): C4 recursive dict (see ``BaseOperations._GetFeatureStruc``).
            struct_guid (str, optional): Preserve or assign struct GUID.

        Raises:
            FP_ReadOnlyError: When the project is not write-enabled.
            FP_ParameterError: On malformed ``spec`` or unresolved feature GUIDs.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")
        pos = self.__ResolveObject(pos_or_hvo)

        with self._TransactionCM("Set POS DefaultFeatures"):
            self.__WritePOSFeatureStrucSpec(pos, "Default", spec, struct_guid=struct_guid)

    @OperationsMethod
    def GetInherFeatVal(self, pos_or_hvo):
        """
        Read ``InherFeatValOA`` as a C4 feature-structure dict.

        Args:
            pos_or_hvo: ``IPartOfSpeech`` or HVO.

        Returns:
            dict or None: Same shape as ``GetSyncableProperties()['InherFeatVal']``
            when present, or ``None`` when ``InherFeatValOA`` is unset.
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")
        pos = self.__ResolveObject(pos_or_hvo)
        return self.__ReadPOSFeatureStrucSpec(pos, "InherFeatVal")

    @OperationsMethod
    def SetInherFeatVal(self, pos_or_hvo, spec, struct_guid=None):
        """
        Replace ``InherFeatValOA`` from a C4 feature-structure dict.

        Args:
            pos_or_hvo: ``IPartOfSpeech`` or HVO.
            spec (dict): C4 recursive dict.
            struct_guid (str, optional): Preserve or assign struct GUID.

        Raises:
            FP_ReadOnlyError: When the project is not write-enabled.
            FP_ParameterError: On malformed ``spec`` or unresolved feature GUIDs.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")
        pos = self.__ResolveObject(pos_or_hvo)

        with self._TransactionCM("Set POS InherFeatVal"):
            self.__WritePOSFeatureStrucSpec(
                pos, "InherFeatVal", spec, struct_guid=struct_guid
            )

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
