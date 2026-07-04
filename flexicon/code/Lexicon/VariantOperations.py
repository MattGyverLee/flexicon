#
#   VariantOperations.py
#
#   Class: VariantOperations
#          Variant form operations for FieldWorks Language Explorer
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
    ILexEntry,
    ILexEntryRef,
    ILexEntryRefFactory,
    ILexEntryType,
    ILexEntryTypeRepository,
    IVariantComponentLexeme,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import string utilities
from ..Shared.string_utils import normalize_match_key


class VariantOperations(BaseOperations):
    """
    This class provides operations for managing variant forms in a FieldWorks project.

    Variant forms represent alternative forms of lexical entries, including:
    - Spelling variants (e.g., "color" vs. "colour")
    - Dialectal variants (e.g., regional pronunciations)
    - Irregularly inflected forms (e.g., "went" as past tense of "go")
    - Free variants (e.g., "among" vs. "amongst")

    Variants are linked through ILexEntryRef objects which can connect entries
    as variants of each other or as components of complex forms.

    This class should be accessed via FLExProject.Variants property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all variant types
        for vtype in project.Variants.GetAllTypes():
            name = project.Variants.GetTypeName(vtype)
            print(f"Variant type: {name}")

        # Find a specific variant type
        spelling_type = project.Variants.FindType("Spelling Variant")

        # Create a variant
        entry = project.LexEntry.Find("color")
        variant = project.Variants.Create(entry, "colour", spelling_type)

        # Get all variants for an entry
        for var in project.Variants.GetAll(entry):
            form = project.Variants.GetForm(var)
            vtype = project.Variants.GetType(var)
            print(f"Variant: {form} ({vtype})")

        # For irregularly inflected forms
        go_entry = project.LexEntry.Find("go")
        went_entry = project.LexEntry.Find("went")
        irregular_type = project.Variants.FindType("Irregularly Inflected Form")

        # Create variant with component
        variant_ref = project.Variants.Create(went_entry, "went", irregular_type)
        project.Variants.AddComponentLexeme(variant_ref, go_entry)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize VariantOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for variants.

        A LexEntryRef with RefType=0 is owned by the variant entry via
        EntryRefsOS (that is where Create appends to). The previous
        implementation pointed at ``VariantEntryBackRefsOS`` -- a virtual
        property that does not exist on ILexEntry (the analogous
        back-reference is the read-only ``VariantEntryRefs`` virtual list
        on the COMPONENT entry, not the variant entry, and it is not
        reorderable). MoveUp/MoveDown must operate on the owning sequence.
        """
        return parent.EntryRefsOS

    # --- Variant Type Management ---

    @OperationsMethod
    def GetAllTypes(self):
        """
        Get all variant entry types defined in the project.

        Variant types define the nature of the relationship between entries,
        such as spelling variants, dialectal variants, irregularly inflected
        forms, etc.

        Yields:
            ILexEntryType: Each variant type defined in the project.

        Example:
            >>> for vtype in project.Variants.GetAllTypes():
            ...     name = project.Variants.GetTypeName(vtype)
            ...     desc = project.Variants.GetTypeDescription(vtype)
            ...     print(f"{name}: {desc}")
            Spelling Variant: A variant spelling of the same word
            Dialectal Variant: A form used in a particular dialect
            Irregularly Inflected Form: An irregular inflection of a lexeme

        Notes:
            - Returns both built-in and custom variant types
            - Types are hierarchical - may include subtypes
            - Empty if no variant types are defined (unusual)
            - Types control how variants are displayed and linked

        See Also:
            FindType, GetTypeName, GetTypeDescription
        """
        if self.project.lp.LexDbOA.VariantEntryTypesOA is None:
            return

        for vtype in self.project.lp.LexDbOA.VariantEntryTypesOA.PossibilitiesOS:
            yield vtype
            # Also yield any subtypes
            if vtype.SubPossibilitiesOS.Count > 0:
                for subtype in vtype.SubPossibilitiesOS:
                    yield subtype

    @OperationsMethod
    def FindType(self, name):
        """
        Find a variant type by name.

        Args:
            name (str): The name of the variant type to find (case-insensitive).
                Common types: "Spelling Variant", "Dialectal Variant",
                "Irregularly Inflected Form", "Free Variant", etc.

        Returns:
            ILexEntryType or None: The variant type if found, None otherwise.

        Raises:
            FP_NullParameterError: If name is None.

        Example:
            >>> spelling_type = project.Variants.FindType("Spelling Variant")
            >>> if spelling_type:
            ...     print(f"Found: {project.Variants.GetTypeName(spelling_type)}")
            Found: Spelling Variant

            >>> # Case-insensitive search
            >>> dialectal = project.Variants.FindType("dialectal variant")
            >>> irregular = project.Variants.FindType("Irregularly Inflected Form")

        Notes:
            - Search is case-insensitive
            - Returns first match found
            - Searches both types and subtypes
            - Returns None if not found (doesn't raise exception)
            - Common built-in types:
              - Spelling Variant
              - Dialectal Variant
              - Free Variant
              - Irregularly Inflected Form

        See Also:
            GetAllTypes, GetTypeName
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        target = normalize_match_key(name, casefold=True)
        wsHandle = self.project.project.DefaultAnalWs

        for vtype in self.GetAllTypes():
            type_name = ITsString(vtype.Name.get_String(wsHandle)).Text
            if type_name and normalize_match_key(type_name, casefold=True) == target:
                return vtype

        return None

    @OperationsMethod
    def GetTypeName(self, variant_type, wsHandle=None):
        """
        Get the name of a variant type.

        Args:
            variant_type: The ILexEntryType object.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The variant type name (empty string if not set).

        Raises:
            FP_NullParameterError: If variant_type is None.

        Example:
            >>> for vtype in project.Variants.GetAllTypes():
            ...     name = project.Variants.GetTypeName(vtype)
            ...     print(f"Type: {name}")
            Type: Spelling Variant
            Type: Dialectal Variant
            Type: Irregularly Inflected Form

            >>> # Get in specific writing system
            >>> name_fr = project.Variants.GetTypeName(vtype, project.WSHandle('fr'))

        Notes:
            - Returns empty string if name not set in specified writing system
            - Variant types are typically defined in analysis writing systems
            - Type names are localizable (can differ per writing system)

        See Also:
            GetTypeDescription, FindType
        """
        self._ValidateParam(variant_type, "variant_type")

        wsHandle = self.__WSHandleAnalysis(wsHandle)

        name = ITsString(variant_type.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def GetTypeDescription(self, variant_type, wsHandle=None):
        """
        Get the description of a variant type.

        Args:
            variant_type: The ILexEntryType object.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The variant type description (empty string if not set).

        Raises:
            FP_NullParameterError: If variant_type is None.

        Example:
            >>> spelling_type = project.Variants.FindType("Spelling Variant")
            >>> if spelling_type:
            ...     desc = project.Variants.GetTypeDescription(spelling_type)
            ...     print(desc)
            A variant spelling of the same word

        Notes:
            - Returns empty string if description not set
            - Description is a MultiString field (can vary by writing system)
            - Not all variant types have descriptions
            - Useful for documenting custom variant types

        See Also:
            GetTypeName, FindType
        """
        self._ValidateParam(variant_type, "variant_type")

        wsHandle = self.__WSHandleAnalysis(wsHandle)

        desc = ITsString(variant_type.Description.get_String(wsHandle)).Text
        return desc or ""

    # --- Variant Management ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, entry_or_hvo=None):
        """
        Get all variant references for a lexical entry, or all variants in the entire project.

        This returns the entry references that define this entry as a variant
        of other entries, or other entries as variants of this one.

        Args:
            entry_or_hvo: The ILexEntry object or HVO. If None, iterates all variant
                         references in the entire project.

        Yields:
            ILexEntryRef: Each variant reference associated with the entry (or project).

        Example:
            >>> # Get variant references for specific entry
            >>> entry = project.LexEntry.Find("colour")
            >>> for variant_ref in project.Variants.GetAll(entry):
            ...     vtype = project.Variants.GetType(variant_ref)
            ...     type_name = project.Variants.GetTypeName(vtype)
            ...     print(f"Variant type: {type_name}")
            Variant type: Spelling Variant

            >>> # Get ALL variant references in entire project
            >>> for variant_ref in project.Variants.GetAll():
            ...     form = project.Variants.GetForm(variant_ref)
            ...     print(f"Variant form: {form}")

        Notes:
            - When entry_or_hvo is provided:
              - Returns empty generator if entry has no variants
              - Each ILexEntryRef represents one variant relationship
              - For complex entries, may return multiple references
              - Variant references are bidirectional in some cases
            - When entry_or_hvo is None:
              - Iterates ALL entries in the project
              - For each entry, yields all variant-type references
              - Useful for project-wide variant operations

        See Also:
            Create, GetVariantCount, GetType
        """
        if entry_or_hvo is None:
            # Iterate ALL variant references in entire project
            for entry in self.project.lexDB.Entries:
                for entry_ref in entry.EntryRefsOS:
                    # Check if this is a variant type reference
                    if entry_ref.RefType == 0:  # Variant type
                        yield entry_ref
        else:
            # Iterate variant references for specific entry
            entry = self.__GetEntryObject(entry_or_hvo)

            for entry_ref in entry.EntryRefsOS:
                # Check if this is a variant type reference
                if entry_ref.RefType == 0:  # Variant type
                    yield entry_ref

    @OperationsMethod
    def Create(self, entry_or_hvo, variant_form, variant_type, wsHandle=None):
        """
        Create a variant relationship for an entry.

        This creates an ILexEntryRef object that defines the entry as a variant
        of another form. The variant_form can be set as the lexeme form of the
        entry itself, or you can create a separate entry for the variant.

        Args:
            entry_or_hvo: The ILexEntry object or HVO (the variant entry).
            variant_form (str): The variant form text (for display/reference).
            variant_type: The ILexEntryType object defining the variant type.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            ILexEntryRef: The newly created variant reference object.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If entry_or_hvo, variant_form, or variant_type is None.
            FP_ParameterError: If variant_form is empty.

        Example:
            >>> # Create spelling variant
            >>> colour_entry = project.LexEntry.Find("colour")
            >>> if not colour_entry:
            ...     colour_entry = project.LexEntry.Create("colour")
            >>> spelling_type = project.Variants.FindType("Spelling Variant")
            >>> variant = project.Variants.Create(colour_entry, "colour", spelling_type)

            >>> # Create irregularly inflected form
            >>> went_entry = project.LexEntry.Find("went")
            >>> irregular_type = project.Variants.FindType("Irregularly Inflected Form")
            >>> variant_ref = project.Variants.Create(went_entry, "went", irregular_type)
            >>> # Then add the base form as a component
            >>> go_entry = project.LexEntry.Find("go")
            >>> project.Variants.AddComponentLexeme(variant_ref, go_entry)

        Notes:
            - Creates an ILexEntryRef with RefType = 0 (Variant)
            - The variant_type determines how the variant is classified
            - For irregularly inflected forms, add ComponentLexemes afterward
            - The variant_form is typically the same as the entry's lexeme form
            - Multiple variant references can exist for one entry

        See Also:
            Delete, GetType, SetType, AddComponentLexeme
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(entry_or_hvo, "entry_or_hvo")
        self._ValidateParam(variant_form, "variant_form")
        self._ValidateParam(variant_type, "variant_type")

        if not variant_form or not variant_form.strip():
            raise FP_ParameterError("Variant form cannot be empty")

        entry = self.__GetEntryObject(entry_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Create the entry reference, then attach it to the owning entry
        # BEFORE touching any of its reference-sequence properties.
        # LexEntryRef.VariantEntryTypesRS returns null until the ref is
        # owned, so accessing it before EntryRefsOS.Add raises a
        # System.NullReferenceException from native LCM (#165).
        with self._TransactionCM("Create variant"):
            factory = self.project.project.ServiceLocator.GetService(ILexEntryRefFactory)
            entry_ref = factory.Create()
            entry.EntryRefsOS.Add(entry_ref)

            # Set as variant type (RefType = 0) and add the variant type
            entry_ref.RefType = 0
            entry_ref.VariantEntryTypesRS.Add(variant_type)

            # The variant form itself is typically the entry's lexeme form.
            # We don't set a separate form on the ILexEntryRef; instead make
            # sure the entry's lexeme form matches the requested variant_form.
            if entry.LexemeFormOA:
                current_form = ITsString(entry.LexemeFormOA.Form.get_String(wsHandle)).Text
                if not current_form or current_form != variant_form:
                    mkstr = TsStringUtils.MakeString(variant_form, wsHandle)
                    entry.LexemeFormOA.Form.set_String(wsHandle, mkstr)

            return entry_ref

    @OperationsMethod
    def Delete(self, variant_or_hvo):
        """
        Delete a variant reference.

        This removes the variant relationship but does not delete the entry itself.

        Args:
            variant_or_hvo: The ILexEntryRef object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If variant_or_hvo is None.

        Example:
            >>> entry = project.LexEntry.Find("colour")
            >>> for variant in project.Variants.GetAll(entry):
            ...     # Delete the variant reference
            ...     project.Variants.Delete(variant)

        Warning:
            - Deletes the variant relationship, not the entry
            - To delete the variant entry itself, use project.LexEntry.Delete()
            - Deletion is permanent and cannot be undone
            - Component lexeme links are also removed

        Notes:
            - Removes the ILexEntryRef from the entry's EntryRefsOS collection
            - The owning entry remains unchanged
            - Any component lexemes are automatically dereferenced

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(variant_or_hvo, "variant_or_hvo")

        variant = self.__GetVariantObject(variant_or_hvo)

        # Get the owning entry. variant.Owner is typed as ICmObject and
        # does not expose EntryRefsOS; cast to ILexEntry so the typed
        # collection is reachable (the previous hasattr check silently
        # no-opped).
        owner = self._GetTypedOwner(variant)
        if owner is None:
            raise FP_ParameterError("Variant ref has no owning entry")
        owner.EntryRefsOS.Remove(variant)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate a variant reference, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The ILexEntryRef object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source variant.
                                If False, insert at end of parent's entry refs list.
            deep (bool): Reserved for future use (variants have no owned objects to duplicate).

        Returns:
            ILexEntryRef: The newly created duplicate variant reference with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> entry = project.LexEntry.Find("colour")
            >>> variants = list(project.Variants.GetAll(entry))
            >>> if variants:
            ...     # Duplicate the variant reference
            ...     dup = project.Variants.Duplicate(variants[0])
            ...     print(f"Original: {variants[0].Guid}")
            ...     print(f"Duplicate: {dup.Guid}")
            ...     vtype = project.Variants.GetType(dup)
            ...     print(f"Type: {project.Variants.GetTypeName(vtype)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321
            Type: Spelling Variant

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original variant's position/priority
            - Simple properties copied: RefType, HideMinorEntry, ShowComplexFormsIn
            - Reference Sequence (RS) properties copied: VariantEntryTypesRS, ComponentLexemesRS
            - The duplicate shares the same form as the source (both owned by same entry)
            - Variants have no owned objects, so deep parameter has no effect
            - LiftResidue is not copied (import-specific data)

        See Also:
            Create, Delete, GetType
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source variant and parent. source.Owner is typed as
        # ICmObject; cast to ILexEntry so EntryRefsOS is reachable.
        # Without this cast the previous `hasattr(parent, "EntryRefsOS")`
        # silently returned False and the duplicate was orphaned.
        source = self.__GetVariantObject(item_or_hvo)
        parent = self._GetTypedOwner(source)
        if parent is None:
            raise FP_ParameterError("Variant ref has no owning entry")

        # Create new variant reference using factory (auto-generates new GUID)
        with self._TransactionCM("Duplicate variant"):
            factory = self.project.project.ServiceLocator.GetService(ILexEntryRefFactory)
            duplicate = factory.Create()

            # Determine insertion position
            if insert_after:
                # Insert after source variant
                source_index = parent.EntryRefsOS.IndexOf(source)
                parent.EntryRefsOS.Insert(source_index + 1, duplicate)
            else:
                # Insert at end
                parent.EntryRefsOS.Add(duplicate)

            # Copy simple properties
            duplicate.RefType = source.RefType

            if hasattr(source, "HideMinorEntry"):
                duplicate.HideMinorEntry = source.HideMinorEntry

            if hasattr(source, "ShowComplexFormsIn"):
                duplicate.ShowComplexFormsIn = source.ShowComplexFormsIn

            # Copy Reference Sequence (RS) properties
            # Copy variant entry types
            for vtype in source.VariantEntryTypesRS:
                duplicate.VariantEntryTypesRS.Add(vtype)

            # Copy component lexemes (for irregularly inflected forms)
            for component in source.ComponentLexemesRS:
                duplicate.ComponentLexemesRS.Add(component)

            # Copy complex entry types (if applicable)
            if hasattr(source, "ComplexEntryTypesRS"):
                for ctype in source.ComplexEntryTypesRS:
                    duplicate.ComplexEntryTypesRS.Add(ctype)

            # Copy primary lexemes (if applicable)
            if hasattr(source, "PrimaryLexemesRS"):
                for plex in source.PrimaryLexemesRS:
                    duplicate.PrimaryLexemesRS.Add(plex)

            return duplicate

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a variant reference for comparison.

        Args:
            item: The ILexEntryRef object.

        Returns:
            dict: Dictionary mapping property names to their values.
        """
        props = {}

        # Atomic properties
        # RefType - type of reference (0 = Variant, 1 = Complex Form)
        if hasattr(item, "RefType"):
            props["RefType"] = item.RefType

        # HideMinorEntry - whether to hide minor entry
        if hasattr(item, "HideMinorEntry"):
            props["HideMinorEntry"] = item.HideMinorEntry

        # ShowComplexFormsIn - flags for showing complex forms
        if hasattr(item, "ShowComplexFormsIn"):
            props["ShowComplexFormsIn"] = item.ShowComplexFormsIn

        # Note: The variant form itself is stored on the owning entry's LexemeFormOA
        # Note: VariantEntryTypesRS is a Reference Sequence (complex relationships) - not included as simple property
        # Note: ComponentLexemesRS is a Reference Sequence (complex relationships) - not included as simple property

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two variant references and return their differences.

        Args:
            item1: The first ILexEntryRef object.
            item2: The second ILexEntryRef object.
            ops1: Optional VariantOperations instance for item1.
            ops2: Optional VariantOperations instance for item2.

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

    @OperationsMethod
    def GetForm(self, variant_or_hvo, wsHandle=None):
        """
        Get the form of a variant.

        This returns the lexeme form of the entry that owns this variant reference.

        Args:
            variant_or_hvo: The ILexEntryRef object or HVO.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The variant form text (empty string if not set).

        Raises:
            FP_NullParameterError: If variant_or_hvo is None.

        Example:
            >>> entry = project.LexEntry.Find("colour")
            >>> for variant in project.Variants.GetAll(entry):
            ...     form = project.Variants.GetForm(variant)
            ...     print(f"Variant form: {form}")
            Variant form: colour

        Notes:
            - Returns the owning entry's lexeme form
            - Returns empty string if entry has no lexeme form
            - ILexEntryRef doesn't store form directly - it's on the entry
            - For component lexemes, use GetComponentLexemes()

        See Also:
            SetForm, GetOwningEntry
        """
        self._ValidateParam(variant_or_hvo, "variant_or_hvo")

        variant = self.__GetVariantObject(variant_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # variant.Owner is typed as ICmObject in LCM. pythonnet only surfaces
        # attributes from the static type, so hasattr(owner, "LexemeFormOA")
        # is always False without an explicit downcast. Cast to ILexEntry
        # so LexemeFormOA becomes accessible.
        owner = ILexEntry(variant.Owner)

        if owner.LexemeFormOA:
            form = ITsString(owner.LexemeFormOA.Form.get_String(wsHandle)).Text
            return form or ""

        return ""

    @OperationsMethod
    def SetForm(self, variant_or_hvo, text, wsHandle=None):
        """
        Set the form of a variant.

        This sets the lexeme form of the entry that owns this variant reference.

        Args:
            variant_or_hvo: The ILexEntryRef object or HVO.
            text (str): The new variant form text.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If variant_or_hvo or text is None.
            FP_ParameterError: If text is empty or entry has no lexeme form.

        Example:
            >>> entry = project.LexEntry.Find("colour")
            >>> for variant in project.Variants.GetAll(entry):
            ...     project.Variants.SetForm(variant, "coulour")  # Fix typo
            ...     print(project.Variants.GetForm(variant))
            coulour

        Notes:
            - Sets the owning entry's lexeme form
            - Entry must have a lexeme form object
            - Changes the headword of the variant entry
            - Affects how the entry appears in the lexicon

        See Also:
            GetForm, GetOwningEntry
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(variant_or_hvo, "variant_or_hvo")
        self._ValidateParam(text, "text")

        if not text or not text.strip():
            raise FP_ParameterError("Variant form cannot be empty")

        variant = self.__GetVariantObject(variant_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Cast variant.Owner from ICmObject to ILexEntry so LexemeFormOA
        # is reachable (see GetForm rationale).
        owner = ILexEntry(variant.Owner)

        if not owner.LexemeFormOA:
            raise FP_ParameterError("Entry has no lexeme form object")

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        owner.LexemeFormOA.Form.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetType(self, variant_or_hvo):
        """
        Get the variant type of a variant reference.

        Args:
            variant_or_hvo: The ILexEntryRef object or HVO.

        Returns:
            ILexEntryType or None: The variant type, or None if not set.

        Raises:
            FP_NullParameterError: If variant_or_hvo is None.

        Example:
            >>> entry = project.LexEntry.Find("colour")
            >>> for variant in project.Variants.GetAll(entry):
            ...     vtype = project.Variants.GetType(variant)
            ...     if vtype:
            ...         name = project.Variants.GetTypeName(vtype)
            ...         print(f"Variant type: {name}")
            Variant type: Spelling Variant

        Notes:
            - Returns None if no variant type is set (unusual)
            - A variant reference can have multiple types, this returns the first
            - Use VariantEntryTypesRS collection for all types
            - Variant type determines how the variant is classified

        See Also:
            SetType, GetTypeName, GetAllTypes
        """
        self._ValidateParam(variant_or_hvo, "variant_or_hvo")

        variant = self.__GetVariantObject(variant_or_hvo)

        if variant.VariantEntryTypesRS.Count > 0:
            return variant.VariantEntryTypesRS[0]

        return None

    @OperationsMethod
    def SetType(self, variant_or_hvo, variant_type):
        """
        Set the variant type of a variant reference.

        This replaces all existing variant types with the specified type.

        Args:
            variant_or_hvo: The ILexEntryRef object or HVO.
            variant_type: The ILexEntryType object to set.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If variant_or_hvo or variant_type is None.

        Example:
            >>> entry = project.LexEntry.Find("colour")
            >>> for variant in project.Variants.GetAll(entry):
            ...     dialectal_type = project.Variants.FindType("Dialectal Variant")
            ...     if dialectal_type:
            ...         project.Variants.SetType(variant, dialectal_type)
            ...         vtype = project.Variants.GetType(variant)
            ...         print(project.Variants.GetTypeName(vtype))
            Dialectal Variant

        Notes:
            - Clears all existing variant types
            - Sets the new type as the only type
            - To add additional types, use VariantEntryTypesRS.Add()
            - Changing type affects how variant is displayed and processed

        See Also:
            GetType, FindType, GetAllTypes
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(variant_or_hvo, "variant_or_hvo")
        self._ValidateParam(variant_type, "variant_type")

        variant = self.__GetVariantObject(variant_or_hvo)

        with self._TransactionCM("Set variant type"):
            # Clear existing types
            variant.VariantEntryTypesRS.Clear()

            # Add the new type
            variant.VariantEntryTypesRS.Add(variant_type)

    # --- Component Management (for irregularly inflected forms) ---

    @OperationsMethod
    def GetComponentLexemes(self, variant_or_hvo):
        """
        Get the component lexemes of a variant.

        Component lexemes are the base entries that make up an irregularly
        inflected form. For example, "went" has "go" as a component.

        Args:
            variant_or_hvo: The ILexEntryRef object or HVO.

        Returns:
            list: List of ILexEntry objects that are components (empty list if none).

        Raises:
            FP_NullParameterError: If variant_or_hvo is None.

        Example:
            >>> # "went" is irregular past tense of "go"
            >>> went_entry = project.LexEntry.Find("went")
            >>> for variant in project.Variants.GetAll(went_entry):
            ...     components = project.Variants.GetComponentLexemes(variant)
            ...     for comp in components:
            ...         headword = project.LexEntry.GetHeadword(comp)
            ...         print(f"Component: {headword}")
            Component: go

            >>> # "worse" might have components "bad" or "ill"
            >>> worse_entry = project.LexEntry.Find("worse")
            >>> for variant in project.Variants.GetAll(worse_entry):
            ...     for comp in project.Variants.GetComponentLexemes(variant):
            ...         print(project.LexEntry.GetHeadword(comp))
            bad

        Notes:
            - Returns empty list if no components
            - Primarily used for "Irregularly Inflected Form" variant type
            - Can have multiple components (rare but possible)
            - Components are ILexEntry objects (not ILexEntryRef)
            - Access via ComponentLexemesRS collection

        See Also:
            AddComponentLexeme, RemoveComponentLexeme, Create
        """
        self._ValidateParam(variant_or_hvo, "variant_or_hvo")

        variant = self.__GetVariantObject(variant_or_hvo)

        components = []
        for comp_lex in variant.ComponentLexemesRS:
            components.append(comp_lex)

        return components

    @OperationsMethod
    def AddComponentLexeme(self, variant_or_hvo, entry_or_hvo):
        """
        Add a component lexeme to a variant.

        This creates a link from an irregularly inflected form to its base entry.
        For example, linking "went" to "go".

        Args:
            variant_or_hvo: The ILexEntryRef object or HVO.
            entry_or_hvo: The ILexEntry object or HVO to add as a component.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If variant_or_hvo or entry_or_hvo is None.

        Example:
            >>> # Create "went" as irregular past of "go"
            >>> went_entry = project.LexEntry.Find("went")
            >>> go_entry = project.LexEntry.Find("go")
            >>>
            >>> irregular_type = project.Variants.FindType("Irregularly Inflected Form")
            >>> variant_ref = project.Variants.Create(went_entry, "went", irregular_type)
            >>>
            >>> # Add "go" as the component
            >>> project.Variants.AddComponentLexeme(variant_ref, go_entry)
            >>>
            >>> # Verify
            >>> components = project.Variants.GetComponentLexemes(variant_ref)
            >>> for comp in components:
            ...     print(project.LexEntry.GetHeadword(comp))
            go

        Notes:
            - Typically used with "Irregularly Inflected Form" variant type
            - Creates a reference from the variant to the base form
            - Multiple components can be added (e.g., for suppletion)
            - The component entry must already exist
            - Adds to ComponentLexemesRS collection

        See Also:
            GetComponentLexemes, RemoveComponentLexeme, Create
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(variant_or_hvo, "variant_or_hvo")
        self._ValidateParam(entry_or_hvo, "entry_or_hvo")

        variant = self.__GetVariantObject(variant_or_hvo)
        entry = self.__GetEntryObject(entry_or_hvo)

        # Add the entry as a component
        variant.ComponentLexemesRS.Add(entry)

    @OperationsMethod
    def RemoveComponentLexeme(self, variant_or_hvo, entry_or_hvo):
        """
        Remove a component lexeme from a variant.

        Args:
            variant_or_hvo: The ILexEntryRef object or HVO.
            entry_or_hvo: The ILexEntry object or HVO to remove.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled.
            FP_NullParameterError: If variant_or_hvo or entry_or_hvo is None.

        Example:
            >>> went_entry = project.LexEntry.Find("went")
            >>> go_entry = project.LexEntry.Find("go")
            >>>
            >>> for variant in project.Variants.GetAll(went_entry):
            ...     # Remove "go" as component
            ...     project.Variants.RemoveComponentLexeme(variant, go_entry)
            ...
            ...     # Verify removal
            ...     components = project.Variants.GetComponentLexemes(variant)
            ...     print(f"Remaining components: {len(components)}")
            Remaining components: 0

        Notes:
            - If entry not in component list, this is a no-op (no error)
            - Removes from ComponentLexemesRS collection
            - Doesn't delete the component entry itself
            - Doesn't affect the variant reference (only the component link)

        See Also:
            GetComponentLexemes, AddComponentLexeme
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(variant_or_hvo, "variant_or_hvo")
        self._ValidateParam(entry_or_hvo, "entry_or_hvo")

        variant = self.__GetVariantObject(variant_or_hvo)
        entry = self.__GetEntryObject(entry_or_hvo)

        # Remove if present
        if entry in variant.ComponentLexemesRS:
            variant.ComponentLexemesRS.Remove(entry)

    # --- Utilities ---

    @OperationsMethod
    def GetOwningEntry(self, variant_or_hvo):
        """
        Get the entry that owns a variant reference.

        Args:
            variant_or_hvo: The ILexEntryRef object or HVO.

        Returns:
            ILexEntry: The entry that owns this variant reference.

        Raises:
            FP_NullParameterError: If variant_or_hvo is None.

        Example:
            >>> # Find all variants in the lexicon and their owners
            >>> for entry in project.LexEntry.GetAll():
            ...     for variant in project.Variants.GetAll(entry):
            ...         owner = project.Variants.GetOwningEntry(variant)
            ...         owner_hw = project.LexEntry.GetHeadword(owner)
            ...         var_form = project.Variants.GetForm(variant)
            ...         vtype = project.Variants.GetType(variant)
            ...         type_name = project.Variants.GetTypeName(vtype) if vtype else "?"
            ...         print(f"{owner_hw} -> {var_form} ({type_name})")
            color -> colour (Spelling Variant)
            go -> went (Irregularly Inflected Form)

        Notes:
            - Returns the ILexEntry that contains this variant reference
            - The owner is the variant entry (e.g., "colour")
            - For irregularly inflected forms, owner is the irregular form
            - Use GetComponentLexemes() to get the base form(s)

        See Also:
            GetAll, GetComponentLexemes
        """
        self._ValidateParam(variant_or_hvo, "variant_or_hvo")

        variant = self.__GetVariantObject(variant_or_hvo)

        # Cast to declared return type ILexEntry. Raw variant.Owner is typed
        # as ICmObject in LCM; pythonnet only surfaces ILexEntry properties
        # (e.g. LexemeFormOA) after the explicit interface cast.
        return ILexEntry(variant.Owner)

    @OperationsMethod
    def GetVariantCount(self, entry_or_hvo):
        """
        Get the count of variant references for an entry.

        Args:
            entry_or_hvo: The ILexEntry object or HVO.

        Returns:
            int: The number of variant references (0 if none).

        Raises:
            FP_NullParameterError: If entry_or_hvo is None.

        Example:
            >>> entry = project.LexEntry.Find("colour")
            >>> count = project.Variants.GetVariantCount(entry)
            >>> print(f"Entry has {count} variant reference(s)")
            Entry has 1 variant reference(s)

            >>> # Check if entry has any variants
            >>> if project.Variants.GetVariantCount(entry) > 0:
            ...     print("This entry has variants")

        Notes:
            - Returns 0 if entry has no variant references
            - Only counts variant-type references (RefType = 0)
            - More efficient than len(list(GetAll(entry)))
            - An entry can have multiple variant references of different types

        See Also:
            GetAll, Create
        """
        self._ValidateParam(entry_or_hvo, "entry_or_hvo")

        entry = self.__GetEntryObject(entry_or_hvo)

        count = 0
        for entry_ref in entry.EntryRefsOS:
            if entry_ref.RefType == 0:  # Variant type
                count += 1

        return count

    # --- Private Helper Methods ---

    def __GetEntryObject(self, entry_or_hvo):
        """
        Resolve HVO or object to ILexEntry.

        Args:
            entry_or_hvo: Either an ILexEntry object or an HVO (int).

        Returns:
            ILexEntry: The resolved entry object.

        Raises:
            FP_ParameterError: If HVO doesn't refer to a lexical entry.
        """
        if isinstance(entry_or_hvo, int):
            obj = self.project.Object(entry_or_hvo)
            if not isinstance(obj, ILexEntry):
                raise FP_ParameterError("HVO does not refer to a lexical entry")
            return obj
        return entry_or_hvo

    def __GetVariantObject(self, variant_or_hvo):
        """
        Resolve HVO or object to ILexEntryRef.

        Args:
            variant_or_hvo: Either an ILexEntryRef object or an HVO (int).

        Returns:
            ILexEntryRef: The resolved variant reference object.

        Raises:
            FP_ParameterError: If HVO doesn't refer to a variant reference.
        """
        if isinstance(variant_or_hvo, int):
            obj = self.project.Object(variant_or_hvo)
            if not isinstance(obj, ILexEntryRef):
                raise FP_ParameterError("HVO does not refer to a variant reference")
            return obj
        return variant_or_hvo

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to vernacular WS.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)

    def __WSHandleAnalysis(self, wsHandle):
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
