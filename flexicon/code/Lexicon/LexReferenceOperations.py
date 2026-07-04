#
#   LexReferenceOperations.py
#
#   Class: LexReferenceOperations
#          Lexical reference and relation operations for FieldWorks Language
#          Explorer projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_text, normalize_match_key

# Import FLEx LCM types
from SIL.LCModel import (
    ILexReference,
    ILexReferenceFactory,
    ILexRefType,
    ILexRefTypeFactory,
    ILexRefTypeRepository,
    ILexEntry,
    ILexSense,
    LexRefTypeTags,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# --- Lexical Reference Mapping Type Constants ---


class LexRefMappingTypes:
    """
    Lexical reference mapping type constants.

    These correspond to the LexRefTypeTags.MappingTypes enum in FLEx.
    The mapping type determines how the lexical relation behaves:

    - SYMMETRIC: Bidirectional equal relations (A ↔ B)
      Example: synonym, antonym

    - ASYMMETRIC: Directional relations with forward and reverse (A → B, B ← A)
      Example: hypernym/hyponym, part/whole

    - TREE: Tree/hierarchical relations with parent-child structure
      Example: taxonomic hierarchies, part-whole hierarchies

    - SEQUENCE: Ordered sequence relations (A → B → C)
      Example: temporal sequences, procedural steps
    """

    SYMMETRIC = 1  # krtSym - Symmetric (A ↔ B)
    ASYMMETRIC = 2  # krtAsym - Asymmetric with forward/reverse (A → B, B ← A)
    TREE = 3  # krtTree - Tree/hierarchical (parent-child)
    SEQUENCE = 4  # krtSequence - Ordered sequence (A → B → C)


class LexReferenceOperations(BaseOperations):
    """
    This class provides operations for managing lexical references and
    cross-references in a FieldWorks project.

    Lexical references connect entries or senses through various types of
    relations such as synonyms, antonyms, hypernyms, part-whole relationships,
    and complex form relationships. These relations help organize the lexicon
    semantically and structurally.

    The class handles different mapping types:
    - Symmetric (e.g., synonym, antonym)
    - Asymmetric (e.g., hypernym/hyponym)
    - Tree (e.g., part-whole hierarchies)
    - Sequence (ordered relationships)

    This class should be accessed via FLExProject.LexReferences property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all relation types
        for ref_type in project.LexReferences.GetAllTypes():
            name = project.LexReferences.GetTypeName(ref_type)
            mapping = project.LexReferences.GetMappingType(ref_type)
            print(f"{name}: {mapping}")

        # Create a new relation type
        synonym_type = project.LexReferences.CreateType(
            "Synonym",
            "Symmetric",
            reverse_name=None
        )

        # Create a reference between two senses
        entry1 = project.LexEntry.Find("run")
        entry2 = project.LexEntry.Find("jog")
        if entry1 and entry2:
            sense1 = list(project.Senses.GetAll(entry1))[0]
            sense2 = list(project.Senses.GetAll(entry2))[0]
            ref = project.LexReferences.Create(synonym_type, [sense1, sense2])

        # Get all references for a sense
        for ref in project.LexReferences.GetAll(sense1):
            targets = project.LexReferences.GetTargets(ref)
            for target in targets:
                if target.ClassName == "LexSense":
                    gloss = project.Senses.GetGloss(target)
                    print(f"Related sense: {gloss}")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize LexReferenceOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Reference Type Management ---

    @OperationsMethod
    def GetAllTypes(self):
        """
        Get all lexical relation types in the project.

        This method returns an iterator over all ILexRefType objects that
        define the types of lexical relations available in the project, such
        as Synonym, Antonym, Part-Whole, etc.

        Yields:
            ILexRefType: Each lexical reference type object in the project

        Example:
            >>> for ref_type in project.LexReferences.GetAllTypes():
            ...     name = project.LexReferences.GetTypeName(ref_type)
            ...     mapping = project.LexReferences.GetMappingType(ref_type)
            ...     count = len(list(ref_type.MembersOC))
            ...     print(f"{name} ({mapping}): {count} references")
            Synonym (Symmetric): 15 references
            Antonym (Symmetric): 8 references
            Part-Whole (Tree): 22 references

        Notes:
            - Returns all defined relation types, even if unused
            - Each type defines constraints on how relations work
            - Mapping type determines reference behavior (symmetric, etc.)
            - Types can be hierarchical (with subtypes)

        See Also:
            FindType, CreateType, GetTypeName, GetMappingType
        """
        return self.project.ObjectsIn(ILexRefTypeRepository)

    @OperationsMethod
    def CreateType(self, name, mapping_type, reverse_name=None, wsHandle=None):
        """
        Create a new lexical relation type.

        Args:
            name (str): The name of the relation type (e.g., "Synonym")
            mapping_type (str): The mapping type - one of:
                - "Symmetric" - bidirectional equal relations (synonym, antonym)
                - "Asymmetric" - directional relations (hypernym/hyponym)
                - "Tree" - hierarchical part-whole relations
                - "Sequence" - ordered sequence relations
            reverse_name (str, optional): The reverse name for asymmetric
                relations (e.g., "Hyponym" when name is "Hypernym")
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ILexRefType: The newly created reference type object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If name or mapping_type is None
            FP_ParameterError: If mapping_type is invalid or name is empty

        Example:
            >>> # Create symmetric relation (synonym)
            >>> syn_type = project.LexReferences.CreateType("Synonym", "Symmetric")
            >>> print(project.LexReferences.GetTypeName(syn_type))
            Synonym

            >>> # Create asymmetric relation (hypernym/hyponym)
            >>> hyper_type = project.LexReferences.CreateType(
            ...     "Hypernym",
            ...     "Asymmetric",
            ...     reverse_name="Hyponym"
            ... )

            >>> # Create tree relation (part-whole)
            >>> part_type = project.LexReferences.CreateType(
            ...     "Part-Whole",
            ...     "Tree"
            ... )

        Notes:
            - Symmetric relations don't need reverse_name
            - Asymmetric relations should provide reverse_name
            - Tree relations create hierarchical structures
            - Sequence relations maintain order of targets
            - Type is added to project's lexical relation types list

        See Also:
            DeleteType, FindType, GetAllTypes, SetTypeName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")
        self._ValidateParam(mapping_type, "mapping_type")

        self._ValidateStringNotEmpty(name, "name")

        # Validate mapping type
        mapping_type_upper = mapping_type.upper()
        mapping_value = None

        # Map string to LcmReferenceType enumeration value
        # Using the integer values from the FLEx API
        if mapping_type_upper in ("SYMMETRIC", "SYM"):
            mapping_value = LexRefMappingTypes.SYMMETRIC
        elif mapping_type_upper in ("ASYMMETRIC", "ASYM"):
            mapping_value = LexRefMappingTypes.ASYMMETRIC
        elif mapping_type_upper == "TREE":
            mapping_value = LexRefMappingTypes.TREE
        elif mapping_type_upper in ("SEQUENCE", "SEQ"):
            mapping_value = LexRefMappingTypes.SEQUENCE
        else:
            raise FP_ParameterError(
                f"Invalid mapping type '{mapping_type}'. " f"Must be one of: Symmetric, Asymmetric, Tree, Sequence"
            )

        wsHandle = self.__WSHandleAnalysis(wsHandle)

        with self._TransactionCM(f"Create reference type '{name}'"):
            # Create the new reference type using the factory
            factory = self.project.project.ServiceLocator.GetService(ILexRefTypeFactory)
            new_ref_type = factory.Create()

            # Add to project's lexical relation types (must be done before setting properties)
            ref_types_list = self.project.lexDB.ReferencesOA
            if ref_types_list:
                ref_types_list.PossibilitiesOS.Add(new_ref_type)

            # Set the name
            mkstr = TsStringUtils.MakeString(name, wsHandle)
            new_ref_type.Name.set_String(wsHandle, mkstr)

            # Set the mapping type
            new_ref_type.MappingType = mapping_value

            # Set reverse name for asymmetric relations
            if reverse_name and mapping_value == LexRefMappingTypes.ASYMMETRIC:
                rev_mkstr = TsStringUtils.MakeString(reverse_name, wsHandle)
                new_ref_type.ReverseName.set_String(wsHandle, rev_mkstr)
            else:
                # Create the reference list if it doesn't exist
                from SIL.LCModel import ICmPossibilityListFactory

                list_factory = self.project.project.ServiceLocator.GetService(ICmPossibilityListFactory)
                new_list = list_factory.Create()
                self.project.lexDB.ReferencesOA = new_list
                new_list.PossibilitiesOS.Add(new_ref_type)

            return new_ref_type

    @OperationsMethod
    def DeleteType(self, ref_type_or_hvo):
        """
        Delete a lexical relation type.

        Args:
            ref_type_or_hvo: Either an ILexRefType object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ref_type_or_hvo is None
            FP_ParameterError: If type doesn't exist

        Example:
            >>> ref_type = project.LexReferences.FindType("Obsolete Relation")
            >>> if ref_type:
            ...     project.LexReferences.DeleteType(ref_type)

        Warning:
            - This is a destructive operation
            - All references of this type will be deleted
            - Cannot be undone
            - Use with caution

        Notes:
            - Deletion cascades to all LexReference objects of this type
            - Related entries/senses are not affected, only the references

        See Also:
            CreateType, FindType
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ref_type_or_hvo, "ref_type_or_hvo")

        ref_type = self.__ResolveRefType(ref_type_or_hvo)

        # Remove from the references list
        ref_types_list = self.project.lexDB.ReferencesOA
        if ref_types_list:
            ref_types_list.PossibilitiesOS.Remove(ref_type)

    @OperationsMethod
    def FindType(self, name, wsHandle=None):
        """
        Find a lexical relation type by name.

        Args:
            name (str): The name of the relation type to search for
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ILexRefType or None: The reference type object if found, None otherwise

        Raises:
            FP_NullParameterError: If name is None

        Example:
            >>> syn_type = project.LexReferences.FindType("Synonym")
            >>> if syn_type:
            ...     mapping = project.LexReferences.GetMappingType(syn_type)
            ...     print(f"Found: {mapping}")
            Found: Symmetric

            >>> # Search with specific writing system
            >>> type_fr = project.LexReferences.FindType(
            ...     "Synonyme",
            ...     project.WSHandle('fr')
            ... )

        Notes:
            - Search is case-sensitive
            - Search is writing-system specific
            - Returns first match only
            - Returns None if not found (doesn't raise exception)
            - Searches top-level types only (not subtypes)

        See Also:
            GetAllTypes, CreateType, GetTypeName
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        wsHandle = self.__WSHandleAnalysis(wsHandle)

        # Search through all reference types. NFD-normalize both sides:
        # FLEx stores Unicode in NFD, Python source is typically NFC; a
        # diacritic-bearing relation name would silently miss without
        # this. (issue #125)
        target = normalize_match_key(name, casefold=False)
        for ref_type in self.GetAllTypes():
            type_name = ITsString(ref_type.Name.get_String(wsHandle)).Text
            if type_name and normalize_match_key(type_name, casefold=False) == target:
                return ref_type

        return None

    @OperationsMethod
    def GetTypeName(self, ref_type_or_hvo, wsHandle=None):
        """
        Get the name of a lexical relation type.

        Args:
            ref_type_or_hvo: Either an ILexRefType object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The name of the reference type (empty string if not set)

        Raises:
            FP_NullParameterError: If ref_type_or_hvo is None

        Example:
            >>> for ref_type in project.LexReferences.GetAllTypes():
            ...     name = project.LexReferences.GetTypeName(ref_type)
            ...     print(f"Relation type: {name}")
            Relation type: Synonym
            Relation type: Antonym
            Relation type: Part-Whole

        Notes:
            - Returns empty string if name not set in specified writing system
            - Different writing systems may have different names
            - Default writing system is analysis WS

        See Also:
            SetTypeName, GetTypeReverseName
        """
        self._ValidateParam(ref_type_or_hvo, "ref_type_or_hvo")

        ref_type = self.__ResolveRefType(ref_type_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        name = ITsString(ref_type.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetTypeName(self, ref_type_or_hvo, name, wsHandle=None):
        """
        Set the name of a lexical relation type.

        Args:
            ref_type_or_hvo: Either an ILexRefType object or its HVO
            name (str): The new name for the reference type
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ref_type_or_hvo or name is None

        Example:
            >>> ref_type = project.LexReferences.FindType("Synonm")  # typo
            >>> if ref_type:
            ...     project.LexReferences.SetTypeName(ref_type, "Synonym")
            ...     print(project.LexReferences.GetTypeName(ref_type))
            Synonym

        Notes:
            - Can be set independently in multiple writing systems
            - Empty string is allowed (clears the name)
            - Changing name doesn't affect existing references

        See Also:
            GetTypeName, SetTypeReverseName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ref_type_or_hvo, "ref_type_or_hvo")
        self._ValidateParam(name, "name")

        ref_type = self.__ResolveRefType(ref_type_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        ref_type.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetTypeReverseName(self, ref_type_or_hvo, wsHandle=None):
        """
        Get the reverse name for an asymmetric relation type.

        For asymmetric relations, the reverse name is used for the opposite
        direction. For example, if the name is "Hypernym", the reverse name
        would be "Hyponym".

        Args:
            ref_type_or_hvo: Either an ILexRefType object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The reverse name (empty string if not set or not asymmetric)

        Raises:
            FP_NullParameterError: If ref_type_or_hvo is None

        Example:
            >>> hyper_type = project.LexReferences.FindType("Hypernym")
            >>> if hyper_type:
            ...     name = project.LexReferences.GetTypeName(hyper_type)
            ...     reverse = project.LexReferences.GetTypeReverseName(hyper_type)
            ...     print(f"{name} <-> {reverse}")
            Hypernym <-> Hyponym

        Notes:
            - Only meaningful for asymmetric relations
            - Returns empty string for symmetric/tree/sequence relations
            - Returns empty string if not set

        See Also:
            SetTypeReverseName, GetTypeName, GetMappingType
        """
        self._ValidateParam(ref_type_or_hvo, "ref_type_or_hvo")

        ref_type = self.__ResolveRefType(ref_type_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        # Check if this is an asymmetric relation
        if ref_type.MappingType == LexRefMappingTypes.ASYMMETRIC:
            reverse_name = ITsString(ref_type.ReverseName.get_String(wsHandle)).Text
            return reverse_name or ""
        else:
            return ""

    @OperationsMethod
    def SetTypeReverseName(self, ref_type_or_hvo, name, wsHandle=None):
        """
        Set the reverse name for an asymmetric relation type.

        Args:
            ref_type_or_hvo: Either an ILexRefType object or its HVO
            name (str): The new reverse name
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ref_type_or_hvo or name is None
            FP_ParameterError: If the relation type is not asymmetric

        Example:
            >>> hyper_type = project.LexReferences.FindType("Hypernym")
            >>> if hyper_type:
            ...     project.LexReferences.SetTypeReverseName(hyper_type, "Hyponym")

        Notes:
            - Only applicable to asymmetric relations
            - Will raise error if used on symmetric/tree/sequence relations
            - Empty string is allowed (clears the reverse name)

        See Also:
            GetTypeReverseName, SetTypeName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ref_type_or_hvo, "ref_type_or_hvo")
        self._ValidateParam(name, "name")

        ref_type = self.__ResolveRefType(ref_type_or_hvo)

        # Verify this is an asymmetric relation
        if ref_type.MappingType != LexRefMappingTypes.ASYMMETRIC:
            raise FP_ParameterError("SetTypeReverseName can only be used with asymmetric relations")

        wsHandle = self.__WSHandleAnalysis(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        ref_type.ReverseName.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetMappingType(self, ref_type_or_hvo):
        """
        Get the mapping type of a lexical relation type.

        The mapping type determines how the relation behaves:
        - Symmetric: Bidirectional equal relations (e.g., synonym)
        - Asymmetric: Directional relations with reverse (e.g., hypernym/hyponym)
        - Tree: Hierarchical parent-child relations (e.g., part-whole)
        - Sequence: Ordered sequence relations

        Args:
            ref_type_or_hvo: Either an ILexRefType object or its HVO

        Returns:
            str: The mapping type as a string - one of:
                "Symmetric", "Asymmetric", "Tree", "Sequence", or "Unknown"

        Raises:
            FP_NullParameterError: If ref_type_or_hvo is None

        Example:
            >>> for ref_type in project.LexReferences.GetAllTypes():
            ...     name = project.LexReferences.GetTypeName(ref_type)
            ...     mapping = project.LexReferences.GetMappingType(ref_type)
            ...     print(f"{name}: {mapping}")
            Synonym: Symmetric
            Antonym: Symmetric
            Hypernym: Asymmetric
            Part-Whole: Tree

        Notes:
            - Mapping type is set when the relation type is created
            - Cannot be changed after creation
            - Determines UI behavior and relation constraints in FLEx

        See Also:
            CreateType, GetTypeName
        """
        self._ValidateParam(ref_type_or_hvo, "ref_type_or_hvo")

        ref_type = self.__ResolveRefType(ref_type_or_hvo)

        # Map integer value to string name
        mapping_value = ref_type.MappingType

        if mapping_value == LexRefMappingTypes.SYMMETRIC:
            return "Symmetric"
        elif mapping_value == LexRefMappingTypes.ASYMMETRIC:
            return "Asymmetric"
        elif mapping_value == LexRefMappingTypes.TREE:
            return "Tree"
        elif mapping_value == LexRefMappingTypes.SEQUENCE:
            return "Sequence"
        else:
            return "Unknown"

    # --- Reference Management ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, sense_or_entry=None):
        """
        Get all lexical references for a sense or entry, or all references in the entire project.

        This returns all LexReference objects that include the specified
        sense or entry as one of their targets.

        Args:
            sense_or_entry: Either an ILexSense or ILexEntry object (or HVO).
                           If None, iterates all lexical references in the entire project.

        Yields:
            ILexReference: Each reference that includes this sense/entry (or project)

        Example:
            >>> # Get references for specific sense
            >>> entry = project.LexEntry.Find("run")
            >>> if entry:
            ...     senses = list(project.Senses.GetAll(entry))
            ...     if senses:
            ...         for ref in project.LexReferences.GetAll(senses[0]):
            ...             ref_type = project.LexReferences.GetType(ref)
            ...             type_name = project.LexReferences.GetTypeName(ref_type)
            ...             targets = project.LexReferences.GetTargets(ref)
            ...             print(f"{type_name}: {len(targets)} targets")
            Synonym: 3 targets
            Hypernym: 2 targets

            >>> # Get ALL lexical references in entire project
            >>> for ref in project.LexReferences.GetAll():
            ...     ref_type = project.LexReferences.GetType(ref)
            ...     type_name = project.LexReferences.GetTypeName(ref_type)
            ...     print(f"Reference type: {type_name}")

        Notes:
            - When sense_or_entry is provided:
              - Returns references where sense/entry is any of the targets
              - For entry, checks all senses of the entry
              - Returns empty generator if no references exist
            - When sense_or_entry is None:
              - Iterates ALL entries in the project
              - For each entry, iterates all senses
              - For each sense, yields all lexical references
              - Useful for project-wide reference operations

        See Also:
            Create, GetTargets, GetReferencesOfType
        """
        if sense_or_entry is None:
            # Iterate ALL lexical references in entire project
            seen_refs = set()
            for entry in self.project.lexDB.Entries:
                for sense in entry.SensesOS:
                    for ref in sense.ReferringLexReferences:
                        # Avoid duplicates across different senses
                        if ref.Hvo not in seen_refs:
                            seen_refs.add(ref.Hvo)
                            yield ref
        else:
            # Iterate references for specific sense or entry
            obj = self.__ResolveSenseOrEntry(sense_or_entry)

            # Determine if this is a sense or entry
            if hasattr(obj, "ClassName"):
                if obj.ClassName == "LexSense":
                    # Get references for this sense
                    for ref in obj.ReferringLexReferences:
                        yield ref
                elif obj.ClassName == "LexEntry":
                    # Get references for all senses of this entry
                    seen_refs = set()
                    for sense in obj.SensesOS:
                        for ref in sense.ReferringLexReferences:
                            # Avoid duplicates
                            if ref.Hvo not in seen_refs:
                                seen_refs.add(ref.Hvo)
                                yield ref

    @OperationsMethod
    def Create(self, ref_type_or_name, targets):
        """
        Create a new lexical reference linking senses or entries.

        Args:
            ref_type_or_name: Either an ILexRefType object, its HVO, or
                the name of the reference type (str)
            targets: List of ILexSense or ILexEntry objects (or HVOs) to link.
                Must contain at least 2 targets.

        Returns:
            ILexReference: The newly created reference object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If ref_type_or_name or targets is None
            FP_ParameterError: If targets has fewer than 2 items, if reference
                type not found, or if targets are invalid

        Example:
            >>> # Create synonym relation between two senses
            >>> entry1 = project.LexEntry.Find("run")
            >>> entry2 = project.LexEntry.Find("jog")
            >>> if entry1 and entry2:
            ...     sense1 = list(project.Senses.GetAll(entry1))[0]
            ...     sense2 = list(project.Senses.GetAll(entry2))[0]
            ...
            ...     # Find or create synonym type
            ...     syn_type = project.LexReferences.FindType("Synonym")
            ...     if not syn_type:
            ...         syn_type = project.LexReferences.CreateType("Synonym", "Symmetric")
            ...
            ...     # Create the reference
            ...     ref = project.LexReferences.Create(syn_type, [sense1, sense2])

            >>> # Create using type name
            >>> ref2 = project.LexReferences.Create("Antonym", [sense1, sense3])

        Notes:
            - All targets must be same type (all senses or all entries)
            - Targets are added to the reference's TargetsRS collection
            - For asymmetric relations, order matters (first is source)
            - Reference is automatically added to the relation type

        See Also:
            Delete, AddTarget, RemoveTarget, GetTargets
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ref_type_or_name, "ref_type_or_name")
        self._ValidateParam(targets, "targets")

        if not targets or len(targets) < 2:
            raise FP_ParameterError("At least 2 targets required to create a reference")

        # Resolve reference type
        if isinstance(ref_type_or_name, str):
            ref_type = self.FindType(ref_type_or_name)
            if not ref_type:
                raise FP_ParameterError(f"Reference type '{ref_type_or_name}' not found")
        else:
            ref_type = self.__ResolveRefType(ref_type_or_name)

        # Resolve all targets
        resolved_targets = []
        for target in targets:
            obj = self.__ResolveSenseOrEntry(target)
            resolved_targets.append(obj)

        # Verify all targets are the same type
        first_class = resolved_targets[0].ClassName
        if not all(t.ClassName == first_class for t in resolved_targets):
            raise FP_ParameterError("All targets must be the same type (all LexSense or all LexEntry)")

        with self._TransactionCM("Create reference"):
            # Create the new reference using the factory
            factory = self.project.project.ServiceLocator.GetService(ILexReferenceFactory)
            new_ref = factory.Create()

            # Add reference to the type's members (must be done before setting properties)
            ref_type.MembersOC.Add(new_ref)

            # Add targets to the reference
            for target in resolved_targets:
                new_ref.TargetsRS.Add(target)

            return new_ref

    @OperationsMethod
    def Delete(self, lex_ref_or_hvo):
        """
        Delete a lexical reference.

        Args:
            lex_ref_or_hvo: Either an ILexReference object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If lex_ref_or_hvo is None

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> if entry:
            ...     sense = list(project.Senses.GetAll(entry))[0]
            ...     refs = list(project.LexReferences.GetAll(sense))
            ...     if refs:
            ...         # Delete first reference
            ...         project.LexReferences.Delete(refs[0])

        Warning:
            - This is a destructive operation
            - Cannot be undone
            - The related entries/senses are not affected

        Notes:
            - Removes the reference from the type's MembersOC collection
            - Targets are not deleted, only the relationship

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(lex_ref_or_hvo, "lex_ref_or_hvo")

        lex_ref = self.__ResolveLexRef(lex_ref_or_hvo)

        # Cast owner to its concrete ILexRefType so MembersOC is reachable.
        # Raw lex_ref.Owner is typed as ICmObject and
        # hasattr(...,"MembersOC") returns False there, which is why the
        # prior implementation silently no-opped.
        owner = self._GetTypedOwner(lex_ref)
        if owner is None:
            raise FP_ParameterError("Lex reference has no owning type")
        owner.MembersOC.Remove(lex_ref)

    @OperationsMethod
    def GetTargets(self, lex_ref_or_hvo):
        """
        Get all target senses or entries in a lexical reference.

        Args:
            lex_ref_or_hvo: Either an ILexReference object or its HVO

        Returns:
            list: List of ILexSense or ILexEntry objects that are targets

        Raises:
            FP_NullParameterError: If lex_ref_or_hvo is None

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> if entry:
            ...     sense = list(project.Senses.GetAll(entry))[0]
            ...     for ref in project.LexReferences.GetAll(sense):
            ...         targets = project.LexReferences.GetTargets(ref)
            ...         for target in targets:
            ...             if target.ClassName == "LexSense":
            ...                 gloss = project.Senses.GetGloss(target)
            ...                 print(f"  -> {gloss}")
            ...             elif target.ClassName == "LexEntry":
            ...                 headword = project.LexEntry.GetHeadword(target)
            ...                 print(f"  -> {headword}")
              -> jog
              -> sprint

        Notes:
            - Returns all targets in the TargetsRS collection
            - Targets can be either LexSense or LexEntry objects
            - Order may be significant for sequence relations
            - All targets in a reference are the same type

        See Also:
            AddTarget, RemoveTarget, Create
        """
        self._ValidateParam(lex_ref_or_hvo, "lex_ref_or_hvo")

        lex_ref = self.__ResolveLexRef(lex_ref_or_hvo)

        return list(lex_ref.TargetsRS)

    @OperationsMethod
    def AddTarget(self, lex_ref_or_hvo, sense_or_entry):
        """
        Add a target sense or entry to an existing lexical reference.

        Args:
            lex_ref_or_hvo: Either an ILexReference object or its HVO
            sense_or_entry: The ILexSense or ILexEntry to add (or HVO)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If lex_ref_or_hvo or sense_or_entry is None
            FP_ParameterError: If target type doesn't match existing targets

        Example:
            >>> # Find synonym reference
            >>> entry1 = project.LexEntry.Find("run")
            >>> sense1 = list(project.Senses.GetAll(entry1))[0]
            >>> refs = list(project.LexReferences.GetAll(sense1))
            >>>
            >>> # Find synonym type reference
            >>> syn_ref = None
            >>> for ref in refs:
            ...     ref_type = project.LexReferences.GetType(ref)
            ...     if project.LexReferences.GetTypeName(ref_type) == "Synonym":
            ...         syn_ref = ref
            ...         break
            >>>
            >>> if syn_ref:
            ...     # Add another synonym
            ...     entry2 = project.LexEntry.Find("sprint")
            ...     sense2 = list(project.Senses.GetAll(entry2))[0]
            ...     project.LexReferences.AddTarget(syn_ref, sense2)

        Notes:
            - Target must be same type as existing targets (sense or entry)
            - Target can already exist in the reference (creates duplicate)
            - For symmetric relations, order doesn't matter
            - For asymmetric relations, new target is added at end

        See Also:
            RemoveTarget, GetTargets, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(lex_ref_or_hvo, "lex_ref_or_hvo")
        self._ValidateParam(sense_or_entry, "sense_or_entry")

        lex_ref = self.__ResolveLexRef(lex_ref_or_hvo)
        target = self.__ResolveSenseOrEntry(sense_or_entry)

        # Verify target type matches existing targets
        if lex_ref.TargetsRS.Count > 0:
            first_target = lex_ref.TargetsRS[0]
            if target.ClassName != first_target.ClassName:
                raise FP_ParameterError(
                    f"Target type mismatch: cannot add {target.ClassName} "
                    f"to reference with {first_target.ClassName} targets"
                )

        # Add the target
        lex_ref.TargetsRS.Add(target)

    @OperationsMethod
    def RemoveTarget(self, lex_ref_or_hvo, sense_or_entry):
        """
        Remove a target sense or entry from a lexical reference.

        Args:
            lex_ref_or_hvo: Either an ILexReference object or its HVO
            sense_or_entry: The ILexSense or ILexEntry to remove (or HVO)

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If lex_ref_or_hvo or sense_or_entry is None
            FP_ParameterError: If removing would leave fewer than 2 targets

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> sense = list(project.Senses.GetAll(entry))[0]
            >>> refs = list(project.LexReferences.GetAll(sense))
            >>> if refs:
            ...     targets = project.LexReferences.GetTargets(refs[0])
            ...     if len(targets) > 2:
            ...         # Safe to remove one
            ...         project.LexReferences.RemoveTarget(refs[0], targets[-1])

        Warning:
            - Will raise error if removal would leave < 2 targets
            - Consider using Delete() instead if removing all but one target

        Notes:
            - Target must exist in the reference
            - If target not in reference, this is a no-op (no error)
            - References must have at least 2 targets
            - If only 2 targets remain, delete the reference instead

        See Also:
            AddTarget, GetTargets, Delete
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(lex_ref_or_hvo, "lex_ref_or_hvo")
        self._ValidateParam(sense_or_entry, "sense_or_entry")

        lex_ref = self.__ResolveLexRef(lex_ref_or_hvo)
        target = self.__ResolveSenseOrEntry(sense_or_entry)

        # Verify we won't drop below 2 targets
        if lex_ref.TargetsRS.Count <= 2:
            raise FP_ParameterError(
                "Cannot remove target: reference must have at least 2 targets. "
                "Use Delete() to remove the entire reference instead."
            )

        # Remove the target if it exists
        if target in lex_ref.TargetsRS:
            lex_ref.TargetsRS.Remove(target)

    @OperationsMethod
    def GetType(self, lex_ref_or_hvo):
        """
        Get the reference type of a lexical reference.

        Args:
            lex_ref_or_hvo: Either an ILexReference object or its HVO

        Returns:
            ILexRefType: The reference type object

        Raises:
            FP_NullParameterError: If lex_ref_or_hvo is None

        Example:
            >>> entry = project.LexEntry.Find("run")
            >>> if entry:
            ...     sense = list(project.Senses.GetAll(entry))[0]
            ...     for ref in project.LexReferences.GetAll(sense):
            ...         ref_type = project.LexReferences.GetType(ref)
            ...         name = project.LexReferences.GetTypeName(ref_type)
            ...         mapping = project.LexReferences.GetMappingType(ref_type)
            ...         print(f"{name} ({mapping})")
            Synonym (Symmetric)
            Hypernym (Asymmetric)

        Notes:
            - Every reference has exactly one type
            - Type determines relationship semantics
            - Type is set when reference is created

        See Also:
            GetTypeName, GetMappingType, Create
        """
        self._ValidateParam(lex_ref_or_hvo, "lex_ref_or_hvo")

        lex_ref = self.__ResolveLexRef(lex_ref_or_hvo)

        # Cast to declared return type ILexRefType. Raw lex_ref.Owner is typed
        # as ICmObject in LCM; pythonnet only surfaces ILexRefType properties
        # (e.g. MembersOC, MappingType) after the explicit interface cast.
        # The owner of a LexReference is always a LexRefType.
        return ILexRefType(lex_ref.Owner)

    @OperationsMethod
    def GetReferencesOfType(self, ref_type_or_name):
        """
        Get all lexical references of a specific type.

        Args:
            ref_type_or_name: Either an ILexRefType object, its HVO, or
                the name of the reference type (str)

        Yields:
            ILexReference: Each reference of the specified type

        Raises:
            FP_NullParameterError: If ref_type_or_name is None
            FP_ParameterError: If reference type name not found

        Example:
            >>> # Get all synonym references
            >>> for ref in project.LexReferences.GetReferencesOfType("Synonym"):
            ...     targets = project.LexReferences.GetTargets(ref)
            ...     glosses = []
            ...     for target in targets:
            ...         if target.ClassName == "LexSense":
            ...             glosses.append(project.Senses.GetGloss(target))
            ...     print(f"Synonyms: {', '.join(glosses)}")
            Synonyms: run, jog, sprint
            Synonyms: walk, stroll, amble

        Notes:
            - Returns references in database order
            - Returns empty generator if type has no references
            - Can search by type name (string) or type object

        See Also:
            GetAll, GetType, FindType
        """
        self._ValidateParam(ref_type_or_name, "ref_type_or_name")

        # Resolve reference type
        if isinstance(ref_type_or_name, str):
            ref_type = self.FindType(ref_type_or_name)
            if not ref_type:
                raise FP_ParameterError(f"Reference type '{ref_type_or_name}' not found")
        else:
            ref_type = self.__ResolveRefType(ref_type_or_name)

        # Yield all members of this type
        for ref in ref_type.MembersOC:
            yield ref

    # --- Show Complex Forms Operations ---

    @OperationsMethod
    def ShowComplexFormsIn(self, entry, complex_entry):
        """
        Show a component entry as a subentry under a complex form entry.

        This creates a "Show Complex Forms In" relationship, making the
        component entry appear as a subentry in dictionary views of the
        complex form.

        Args:
            entry: The component entry (ILexEntry or HVO) to show as subentry
            complex_entry: The complex form entry (ILexEntry or HVO) to show it under

        Returns:
            ILexReference: The created reference object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If entry or complex_entry is None
            FP_ParameterError: If entries are invalid

        Example:
            >>> # Show "run" as a component under "running shoe"
            >>> run_entry = project.LexEntry.Find("run")
            >>> shoe_entry = project.LexEntry.Find("running shoe")
            >>> if run_entry and shoe_entry:
            ...     ref = project.LexReferences.ShowComplexFormsIn(
            ...         run_entry,
            ...         shoe_entry
            ...     )

            >>> # Show multiple components under one complex form
            >>> run_entry = project.LexEntry.Find("run")
            >>> away_entry = project.LexEntry.Find("away")
            >>> runaway_entry = project.LexEntry.Find("runaway")
            >>> if run_entry and away_entry and runaway_entry:
            ...     # This would typically be done differently, creating one
            ...     # reference with multiple targets
            ...     pass

        Notes:
            - Uses the "Complex Forms" reference type
            - Creates entry-level references (not sense-level)
            - Component entry appears as subentry in complex form
            - Useful for compounds, derivatives, idioms, etc.

        See Also:
            GetComplexFormEntries, GetComponentEntries
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(entry, "entry")
        self._ValidateParam(complex_entry, "complex_entry")

        component = self.__ResolveEntry(entry)
        complex_form = self.__ResolveEntry(complex_entry)

        # Find "Complex Forms" reference type (read-only lookup)
        complex_type = self.FindType("Complex Forms")

        with self._TransactionCM("Show complex forms in"):
            if not complex_type:
                # Create it as a tree relation
                complex_type = self.CreateType("Complex Forms", "Tree", reverse_name="Components")

            # Create reference with complex form as parent, component as child
            # In tree relations, first target is typically the parent
            ref = self.Create(complex_type, [complex_form, component])

            return ref

    @OperationsMethod
    def GetComplexFormEntries(self, entry):
        """
        Get all complex form entries that show this entry as a component.

        Returns all complex forms (compounds, derivatives, etc.) that list
        the given entry as one of their components.

        Args:
            entry: The component entry (ILexEntry or HVO)

        Returns:
            list: List of ILexEntry objects that are complex forms containing
                this entry as a component

        Raises:
            FP_NullParameterError: If entry is None

        Example:
            >>> # Find all complex forms containing "run"
            >>> run_entry = project.LexEntry.Find("run")
            >>> if run_entry:
            ...     complex_forms = project.LexReferences.GetComplexFormEntries(run_entry)
            ...     for cf in complex_forms:
            ...         headword = project.LexEntry.GetHeadword(cf)
            ...         print(f"Complex form: {headword}")
            Complex form: running shoe
            Complex form: run away
            Complex form: run-up

        Notes:
            - Returns entries from "Complex Forms" or similar reference types
            - Useful for finding derivatives and compounds
            - Returns empty list if entry is not a component of any complex form

        See Also:
            GetComponentEntries, ShowComplexFormsIn
        """
        self._ValidateParam(entry, "entry")

        component = self.__ResolveEntry(entry)

        complex_forms = []

        # Find "Complex Forms" reference type
        complex_type = self.FindType("Complex Forms")
        if not complex_type:
            return complex_forms

        # Get all references of this type
        for ref in complex_type.MembersOC:
            targets = list(ref.TargetsRS)
            # Check if our entry is in the targets
            for i, target in enumerate(targets):
                if target.Hvo == component.Hvo:
                    # For tree relations, other targets are related complex forms
                    for j, other_target in enumerate(targets):
                        if i != j and other_target.ClassName == "LexEntry":
                            if other_target not in complex_forms:
                                complex_forms.append(other_target)

        return complex_forms

    @OperationsMethod
    def GetComponentEntries(self, complex_entry):
        """
        Get all component entries that make up a complex form entry.

        Returns all component entries (roots, stems) that are shown as
        subentries under the given complex form.

        Args:
            complex_entry: The complex form entry (ILexEntry or HVO)

        Returns:
            list: List of ILexEntry objects that are components of this
                complex form

        Raises:
            FP_NullParameterError: If complex_entry is None

        Example:
            >>> # Find components of "running shoe"
            >>> shoe_entry = project.LexEntry.Find("running shoe")
            >>> if shoe_entry:
            ...     components = project.LexReferences.GetComponentEntries(shoe_entry)
            ...     for comp in components:
            ...         headword = project.LexEntry.GetHeadword(comp)
            ...         print(f"Component: {headword}")
            Component: run
            Component: shoe

        Notes:
            - Returns entries from "Complex Forms" or similar reference types
            - Useful for analyzing compound structure
            - Returns empty list if entry has no components defined

        See Also:
            GetComplexFormEntries, ShowComplexFormsIn
        """
        self._ValidateParam(complex_entry, "complex_entry")

        complex_form = self.__ResolveEntry(complex_entry)

        components = []

        # Find "Complex Forms" reference type
        complex_type = self.FindType("Complex Forms")
        if not complex_type:
            return components

        # Get all references of this type
        for ref in complex_type.MembersOC:
            targets = list(ref.TargetsRS)
            # Check if our entry is in the targets
            for i, target in enumerate(targets):
                if target.Hvo == complex_form.Hvo:
                    # For tree relations, other targets are components
                    for j, other_target in enumerate(targets):
                        if i != j and other_target.ClassName == "LexEntry":
                            if other_target not in components:
                                components.append(other_target)

        return components

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a lexical reference for comparison.

        Args:
            item: The ILexReference object.

        Returns:
            dict: Dictionary mapping property names to their values.
        """
        props = {}

        # MultiString properties
        # Name - optional name of the relationship
        name_dict = {}
        if hasattr(item, "Name"):
            for ws_def in self.project.WritingSystems.GetAll():
                from SIL.LCModel.Core.KernelInterfaces import ITsString

                text = normalize_text(ITsString(item.Name.get_String(ws_def.Handle)).Text)
                if text:
                    ws_tag = ws_def.Id
                    name_dict[ws_tag] = text
        props["Name"] = name_dict

        # Comment - additional notes
        comment_dict = {}
        if hasattr(item, "Comment"):
            for ws_def in self.project.WritingSystems.GetAll():
                from SIL.LCModel.Core.KernelInterfaces import ITsString

                text = normalize_text(ITsString(item.Comment.get_String(ws_def.Handle)).Text)
                if text:
                    ws_tag = ws_def.Id
                    comment_dict[ws_tag] = text
        props["Comment"] = comment_dict

        # Reference Atomic (RA) properties
        # ReferenceTypeRA - the type of reference relationship
        if hasattr(item, "ReferenceTypeRA") and item.ReferenceTypeRA:
            props["ReferenceTypeRA"] = str(item.ReferenceTypeRA.Guid)
        else:
            props["ReferenceTypeRA"] = None

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two lexical references and return their differences.

        Args:
            item1: The first ILexReference object.
            item2: The second ILexReference object.
            ops1: Optional LexReferenceOperations instance for item1.
            ops2: Optional LexReferenceOperations instance for item2.

        Returns:
            tuple: (is_different, differences_dict)
        """
        ops1 = ops1 or self
        ops2 = ops2 or self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}
        all_keys = set(props1.keys()) | set(props2.keys())
        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)
            if val1 != val2:
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return is_different, differences

    # --- Private Helper Methods ---

    def __ResolveRefType(self, ref_type_or_hvo):
        """
        Resolve HVO or object to ILexRefType.

        Args:
            ref_type_or_hvo: Either an ILexRefType object or an HVO (int)

        Returns:
            ILexRefType: The resolved reference type object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a reference type
        """
        if isinstance(ref_type_or_hvo, int):
            obj = self.project.Object(ref_type_or_hvo)
            # Verify it's the right type
            if not hasattr(obj, "MappingType"):
                raise FP_ParameterError("HVO does not refer to a LexRefType")
            return obj
        return ref_type_or_hvo

    def __ResolveLexRef(self, lex_ref_or_hvo):
        """
        Resolve HVO or object to ILexReference.

        Args:
            lex_ref_or_hvo: Either an ILexReference object or an HVO (int)

        Returns:
            ILexReference: The resolved reference object

        Raises:
            FP_ParameterError: If HVO doesn't refer to a lexical reference
        """
        if isinstance(lex_ref_or_hvo, int):
            obj = self.project.Object(lex_ref_or_hvo)
            # Verify it's the right type
            if not hasattr(obj, "TargetsRS"):
                raise FP_ParameterError("HVO does not refer to a LexReference")
            return obj
        return lex_ref_or_hvo

    def __ResolveSenseOrEntry(self, sense_or_entry):
        """
        Resolve HVO or object to ILexSense or ILexEntry.

        Args:
            sense_or_entry: Either an ILexSense/ILexEntry object or an HVO (int)

        Returns:
            ILexSense or ILexEntry: The resolved object

        Raises:
            FP_ParameterError: If HVO doesn't refer to sense or entry
        """
        if isinstance(sense_or_entry, int):
            obj = self.project.Object(sense_or_entry)
            if not hasattr(obj, "ClassName"):
                raise FP_ParameterError("HVO does not refer to a LexSense or LexEntry")
            if obj.ClassName not in ("LexSense", "LexEntry"):
                raise FP_ParameterError(f"Object is {obj.ClassName}, not LexSense or LexEntry")
            return obj
        return sense_or_entry

    def __ResolveEntry(self, entry_or_hvo):
        """
        Resolve HVO or object to ILexEntry.

        Args:
            entry_or_hvo: Either an ILexEntry object or an HVO (int)

        Returns:
            ILexEntry: The resolved entry object

        Raises:
            FP_ParameterError: If HVO doesn't refer to an entry
        """
        if isinstance(entry_or_hvo, int):
            obj = self.project.Object(entry_or_hvo)
            if not hasattr(obj, "ClassName") or obj.ClassName != "LexEntry":
                raise FP_ParameterError("Object is not a LexEntry")
            return obj
        return entry_or_hvo

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
