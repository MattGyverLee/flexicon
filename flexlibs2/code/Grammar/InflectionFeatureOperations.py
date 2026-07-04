#
#   InflectionFeatureOperations.py
#
#   Class: InflectionFeatureOperations
#          Inflection class and feature operations for FieldWorks Language
#          Explorer projects via SIL Language and Culture Model (LCM) API.
#
#          Manages inflection classes (IMoInflClass) under MorphologicalDataOA
#          and the morphosyntactic feature system (MsFeatureSystemOA), which
#          owns IFsClosedFeature definitions and their IFsSymFeatVal value
#          children. The MGA EticGlossList.xml catalog is the canonical
#          source for the standard set of inflection (morphosyntactic)
#          features and their values; ImportCatalog / CreateFromCatalog /
#          FixGuidsAgainstCatalog populate the project from it.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025-2026
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod

# Import FLEx LCM types
from SIL.LCModel import (
    IMoInflClass,
    IMoInflClassFactory,
    IFsFeatStruc,
    IFsFeatStrucFactory,
    IFsFeatDefn,  # Fixed: was IFsFeatureDefn
    IFsComplexFeature,
    IFsComplexFeatureFactory,
    IFsClosedFeature,
    IFsClosedFeatureFactory,
    IFsSymFeatVal,
    IFsSymFeatValFactory,
    IFsClosedValue,
    IFsClosedValueFactory,
    IFsFeatStrucType,
    IFsFeatStrucTypeFactory,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# .NET Guid for value-child creation (mixin handles the parent feature)
import System

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import LCM casting utilities for pythonnet interface casting
from ..lcm_casting import cast_to_concrete

# Import string utilities
from ..Shared.string_utils import normalize_match_key

# Catalog (eticGlossList) parsing helpers
from ..Shared.catalog import parse_etic_gloss_list
from ..Shared.catalog_backed import CatalogBackedMixin


# Canonical relative subdir for the MGA inflection-feature catalog under
# FWCodeDir. Kept as module constants so verification / tests can reference
# them.
INFL_FEATS_CATALOG_FILENAME = "EticGlossList.xml"
INFL_FEATS_CATALOG_SUBDIR = "Language Explorer/MGA/GlossLists"

# Optional prefix the wrapper accepts on CatalogSourceId values. Bare ids
# ("fDeg", "vPositive") are what FieldWorks itself writes (the catalog
# shares the eticGlossList shape with PhonFeats); "INFL:" is accepted as
# a user-facing convenience and is stripped before lookup.
CATALOG_PREFIX = "INFL"


class InflectionFeatureOperations(BaseOperations, CatalogBackedMixin):
    """
    This class provides operations for managing inflection classes, feature
    structures, and features in a FieldWorks project.

    Inflection classes group lexical items that inflect similarly (e.g., Latin
    noun declensions, Spanish verb conjugations). Feature structures and features
    represent grammatical properties like person, number, gender, tense, aspect,
    mood, etc.

    Usage::

        from flexlibs2 import FLExProject, InflectionFeatureOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        inflOps = InflectionFeatureOperations(project)

        # Get all inflection classes
        for ic in inflOps.InflectionClassGetAll():
            name = inflOps.InflectionClassGetName(ic)
            print(f"Inflection Class: {name}")

        # Create a new inflection class
        first_decl = inflOps.InflectionClassCreate("First Declension")

        # Work with features
        for feature in inflOps.FeatureGetAll():
            print(f"Feature: {feature}")

        project.CloseProject()
    """

    # --- CatalogBackedMixin configuration ------------------------------
    # The MGA inflection-feature catalog ships with FW under
    # Language Explorer/MGA/GlossLists/EticGlossList.xml and is parsed by
    # parse_etic_gloss_list (shared with PhonFeats since both catalogs use
    # the eticGlossList shape). FW writes BARE entry ids (no "INFL:"
    # prefix) to CatalogSourceId; the mixin honours that with
    # CATALOG_PREFIX_WRITE = None. Features are flat (each top-level
    # feature entry owns IFsSymFeatVal value children handled by
    # _handle_entry_children), so the recursive-entries flag is off.
    # The catalog also contains type="fsType"/"complex" items; the
    # parser silently skips them, so Phase 6a only imports closed
    # (symbolic) features. Complex-feature import is deferred.
    CATALOG_FILE = INFL_FEATS_CATALOG_FILENAME
    CATALOG_SUBDIR = INFL_FEATS_CATALOG_SUBDIR
    CATALOG_PARSER = staticmethod(parse_etic_gloss_list)
    CATALOG_PREFIX_WRITE = None
    DOMAIN_LABEL = "inflection feature"
    _supports_recursive_entries = False

    def __init__(self, project):
        """
        Initialize InflectionFeatureOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for inflection features.
        For InflectionFeature, we reorder parent.FeaturesOA.PossibilitiesOS
        """
        return parent.FeaturesOA.PossibilitiesOS

    # ========================================================================
    # INFLECTION CLASS OPERATIONS
    # ========================================================================

    @OperationsMethod
    def InflectionClassGetAll(self):
        """
        Get all inflection classes in the project.

        Yields:
            IMoInflClass: Each inflection class object in the project.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> for ic in inflOps.InflectionClassGetAll():
            ...     name = inflOps.InflectionClassGetName(ic)
            ...     print(f"Class: {name}")
            Class: First Declension
            Class: Second Declension
            Class: Irregular Verb
            Class: Regular Verb

        Notes:
            - Returns all inflection classes from MorphologicalDataOA
            - Classes organize lexical items by inflectional pattern
            - Each class defines how entries inflect (conjugate/decline)
            - Returns empty if no classes defined

        See Also:
            InflectionClassCreate, InflectionClassGetName
        """
        morph_data = self.project.lp.MorphologicalDataOA
        if morph_data is not None and hasattr(morph_data, "ProdRestrictOA") and morph_data.ProdRestrictOA is not None:
            # Inflection classes are stored in the ProdRestrictOA (Production Restrictions)
            infl_classes = morph_data.ProdRestrictOA
            for ic in infl_classes.PossibilitiesOS:
                yield IMoInflClass(ic)

    @OperationsMethod
    def InflectionClassCreate(self, name):
        """
        Create a new inflection class.

        Args:
            name (str): The name of the inflection class (e.g., "First Declension").

        Returns:
            IMoInflClass: The newly created inflection class object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty or if a class with this name
                already exists.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> first_decl = inflOps.InflectionClassCreate("First Declension")
            >>> print(inflOps.InflectionClassGetName(first_decl))
            First Declension

            >>> # Create Spanish verb conjugation classes
            >>> ar_verbs = inflOps.InflectionClassCreate("AR Verbs")
            >>> er_verbs = inflOps.InflectionClassCreate("ER Verbs")
            >>> ir_verbs = inflOps.InflectionClassCreate("IR Verbs")

        Notes:
            - Inflection classes group entries that inflect the same way
            - Name should describe the inflectional pattern
            - Classes can be associated with specific parts of speech
            - Used in morphological templates and paradigms
            - The class is created in the default analysis writing system

        See Also:
            InflectionClassDelete, InflectionClassGetAll, InflectionClassSetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        # Check if class already exists
        target = normalize_match_key(name, casefold=True)
        for existing_ic in self.InflectionClassGetAll():
            existing_name = self.InflectionClassGetName(existing_ic)
            if existing_name and normalize_match_key(existing_name, casefold=True) == target:
                raise FP_ParameterError(f"Inflection class '{name}' already exists")

        # Get the writing system handle
        wsHandle = self.project.project.DefaultAnalWs

        # Create the new inflection class using the factory
        factory = self.project.project.ServiceLocator.GetService(IMoInflClassFactory)

        # Pre-flight: ensure the morphological data container and production
        # restrictions list exist before creating any object.
        morph_data = self.project.lp.MorphologicalDataOA
        if morph_data is None or morph_data.ProdRestrictOA is None:
            raise FP_ParameterError(
                "Project has no morphological data / production restrictions list defined"
            )

        with self._TransactionCM(f"Create inflection class '{name}'"):
            new_ic = factory.Create()

            # Add to the inflection classes list (must be done before setting properties)
            morph_data.ProdRestrictOA.PossibilitiesOS.Add(new_ic)

            # Set name
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_ic.Name.set_String(wsHandle, mkstr_name)

            return new_ic

    @OperationsMethod
    def InflectionClassDelete(self, ic_or_hvo):
        """
        Delete an inflection class.

        Args:
            ic_or_hvo: The IMoInflClass object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If ic_or_hvo is None.
            FP_ParameterError: If the class is in use and cannot be deleted.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> # Find and delete an obsolete class
            >>> for ic in inflOps.InflectionClassGetAll():
            ...     if inflOps.InflectionClassGetName(ic) == "Obsolete":
            ...         inflOps.InflectionClassDelete(ic)
            ...         break

        Warning:
            - Deleting a class that is in use may raise an error from FLEx
            - Entries using this class should be updated first
            - Deletion is permanent and cannot be undone
            - Check for references before deletion

        See Also:
            InflectionClassCreate, InflectionClassGetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ic_or_hvo, "ic_or_hvo")

        # Resolve to inflection class object
        ic = self.__ResolveInflectionClass(ic_or_hvo)

        # Remove from the inflection classes list
        morph_data = self.project.lp.MorphologicalDataOA
        if morph_data.ProdRestrictOA:
            morph_data.ProdRestrictOA.PossibilitiesOS.Remove(ic)

    @OperationsMethod
    def InflectionClassGetName(self, ic_or_hvo, wsHandle=None):
        """
        Get the name of an inflection class.

        Args:
            ic_or_hvo: The IMoInflClass object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The inflection class name, or empty string if not set.

        Raises:
            FP_NullParameterError: If ic_or_hvo is None.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> for ic in inflOps.InflectionClassGetAll():
            ...     name = inflOps.InflectionClassGetName(ic)
            ...     print(f"Inflection Class: {name}")
            Inflection Class: First Declension
            Inflection Class: Second Declension

        See Also:
            InflectionClassSetName, InflectionClassGetAll
        """
        self._ValidateParam(ic_or_hvo, "ic_or_hvo")

        ic = self.__ResolveInflectionClass(ic_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(ic.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def InflectionClassSetName(self, ic_or_hvo, name, wsHandle=None):
        """
        Set the name of an inflection class.

        Args:
            ic_or_hvo: The IMoInflClass object or HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If ic_or_hvo or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> ic = inflOps.InflectionClassCreate("1st Decl")
            >>> inflOps.InflectionClassSetName(ic, "First Declension")
            >>> print(inflOps.InflectionClassGetName(ic))
            First Declension

        See Also:
            InflectionClassGetName, InflectionClassCreate
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(ic_or_hvo, "ic_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        ic = self.__ResolveInflectionClass(ic_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        ic.Name.set_String(wsHandle, mkstr)

    # ========================================================================
    # FEATURE STRUCTURE OPERATIONS
    # ========================================================================

    @OperationsMethod
    def FeatureStructureGetAll(self):
        """
        Get all feature structures in the project.

        Yields nothing in the current implementation.

        ``IFsFeatStruc`` objects are not stored in a central
        project-level collection; they are owned by various LCM
        objects (morphemes, MSAs, allomorphs, entries, etc.) and
        attached as ``FeatureStructureRA`` or in domain-specific
        owning collections. Walking them requires iterating each
        owning surface in turn, not enumerating ``MsFeatureSystemOA``.

        The previous implementation guarded the inner loop with
        ``hasattr(feature, "FeaturesOS")`` against IFsFeatDefn variants
        that do not expose that property; the check was always False
        at runtime and the body was always-empty. Removed in (#140).

        Yields:
            IFsFeatStruc: Empty generator (placeholder for a future
            cross-surface walk implementation).

        See Also:
            FeatureStructureCreate, FeatureGetAll
        """
        # Empty generator: see docstring. Returning empty rather than
        # raising preserves the historic "calls succeed and yield []"
        # contract for any caller that loops over the result.
        return
        yield  # pragma: no cover -- makes this a generator

    @OperationsMethod
    def FeatureStructureCreate(self):
        """
        Create a new feature structure.

        Returns:
            IFsFeatStruc: The newly created feature structure object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> fs = inflOps.FeatureStructureCreate()
            >>> print(f"Created feature structure: {fs.Hvo}")

        Notes:
            - Feature structures organize related grammatical features
            - After creation, features must be added separately
            - Structures can represent complex feature combinations
            - Used to specify morphosyntactic properties
            - The structure is created as an empty container

        See Also:
            FeatureStructureDelete, FeatureGetAll
        """
        self._EnsureWriteEnabled()

        # Create the new feature structure using the factory
        factory = self.project.project.ServiceLocator.GetService(IFsFeatStrucFactory)
        new_fs = factory.Create()

        return new_fs

    @OperationsMethod
    def FeatureStructureDelete(self, fs_or_hvo):
        """
        Delete a feature structure.

        Args:
            fs_or_hvo: The IFsFeatStruc object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If fs_or_hvo is None.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> fs = inflOps.FeatureStructureCreate()
            >>> inflOps.FeatureStructureDelete(fs)

        Warning:
            - Cannot delete if referenced by entries, morphemes, or rules
            - Check dependencies before deletion
            - Deletion is permanent and cannot be undone

        See Also:
            FeatureStructureCreate, FeatureStructureGetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(fs_or_hvo, "fs_or_hvo")

        # Resolve to feature structure object
        fs = self.__ResolveFeatureStructure(fs_or_hvo)

        # Feature structures are held in the parent's FeaturesOA slot
        # (e.g. IPosFeatures.FeaturesOA, IFsComplexFeature.FeaturesOA).
        # pythonnet narrows fs.Owner to the base ICmObject interface,
        # which does NOT expose FeaturesOA -- so the prior hasattr(owner,
        # "FeaturesOA") was always False and Delete silently did nothing.
        # Route through _GetTypedOwner to recover the concrete interface
        # before checking the slot. (issue #133, same class as #98/#116)
        parent = self._GetTypedOwner(fs)
        if parent is not None and hasattr(parent, "FeaturesOA") and parent.FeaturesOA == fs:
            parent.FeaturesOA = None

    # ========================================================================
    # FEATURE OPERATIONS
    # ========================================================================

    @OperationsMethod
    def FeatureGetAll(self):
        """
        Get all feature definitions in the project.

        Yields:
            IFsFeatureDefn: Each feature definition object in the project.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> for feature in inflOps.FeatureGetAll():
            ...     print(f"Feature: {feature}")

        Notes:
            - Feature definitions describe grammatical categories
            - Each feature has a name and set of possible values
            - Examples: person (1st/2nd/3rd), number (sg/pl), tense, aspect, mood
            - Used to build feature structures for morphosyntactic analysis
            - Returns empty if no feature system defined

        See Also:
            FeatureCreate, FeatureGetValues
        """
        feature_system = self.project.lp.MsFeatureSystemOA
        if feature_system:
            for feature in feature_system.FeaturesOC:
                yield feature

    @OperationsMethod
    def Find(self, name, wsHandle=None):
        """
        Find an inflection feature by name.

        Args:
            name (str): The name to search for. Compared via NFD-normalised
                        casefold match against each feature's Name in the
                        chosen WS.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            IFsFeatDefn or None: First match, or None.

        Notes:
            - Mirrors PhonFeatureOperations.Find. Searches both closed and
              complex features in MsFeatureSystemOA.FeaturesOC.
            - Does NOT search value names; values are looked up via
              ``FeatureGetValues(feature)``.
        """
        self._ValidateParam(name, "name")
        target = normalize_match_key(name, casefold=True)
        if not target:
            return None
        wsHandle = self.__WSHandle(wsHandle)

        feature_system = self.project.lp.MsFeatureSystemOA
        if feature_system is None:
            return None

        for raw in feature_system.FeaturesOC:
            feat = IFsFeatDefn(raw)
            feat_name = ITsString(feat.Name.get_String(wsHandle)).Text
            if feat_name and normalize_match_key(feat_name, casefold=True) == target:
                return feat
        return None

    @OperationsMethod
    def Exists(self, name, wsHandle=None):
        """
        Check whether an inflection feature with the given name exists.

        Args:
            name (str): Name to look up.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            bool: True if the feature exists, False otherwise.
        """
        self._ValidateParam(name, "name")
        return self.Find(name, wsHandle=wsHandle) is not None

    @OperationsMethod
    def TypeFind(self, name, wsHandle=None):
        """
        Find an inflection feature-struct type by name.

        IFsFeatStrucType objects live in ``MsFeatureSystemOA.TypesOC``
        and group related IFsClosedFeatures into FsFeatStruc shapes
        (e.g. "tCommonAgr" for Bantu agreement features). Used by
        catalog-aligned advanced workflows where multiple closed
        features share a structural type.

        Args:
            name (str): The type's name. Compared via NFD-normalised
                casefold match against each type's Name in the chosen WS.
            wsHandle: Optional writing system handle. Defaults to
                analysis WS.

        Returns:
            IFsFeatStrucType or None: First match, or None when no
            type with that name exists or when the feature system is
            not initialised.
        """
        self._ValidateParam(name, "name")
        target = normalize_match_key(name, casefold=True)
        if not target:
            return None
        wsHandle = self.__WSHandle(wsHandle)

        feature_system = self.project.lp.MsFeatureSystemOA
        if feature_system is None:
            return None

        for raw in feature_system.TypesOC:
            type_obj = IFsFeatStrucType(raw)
            type_name = ITsString(type_obj.Name.get_String(wsHandle)).Text
            if type_name and normalize_match_key(type_name, casefold=True) == target:
                return type_obj
        return None

    @OperationsMethod
    def TypeCreate(self, name, abbreviation):
        """
        Create a new IFsFeatStrucType under ``MsFeatureSystemOA.TypesOC``.

        Use this to introduce a structural grouping for inflection
        features that will share a FsFeatStruc shape -- for example,
        Bantu's "tCommonAgr" type, which groups person, number, and
        noun-class features.

        The new type is attached to ``MsFeatureSystemOA.TypesOC``
        BEFORE its Name and Abbreviation multistrings are written
        (Phase 2 ownership rule), so the property setters never hit
        an orphan LCM object.

        A fresh random GUID is generated. To create a catalog-aligned
        type with a canonical GUID, use the bulk ImportCatalog path
        instead -- the EticGlossList parser handles fsType entries
        as part of the full feature-system import.

        Args:
            name (str): The type's display name (analysis WS),
                e.g. "tCommonAgr". Cannot be empty.
            abbreviation (str): Short label written to the analysis-WS
                Abbreviation alternative. Cannot be empty.

        Returns:
            IFsFeatStrucType: The newly created type.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name or abbreviation is None.
            FP_ParameterError: If name or abbreviation is empty, if a
                type with the same name already exists, or if
                MsFeatureSystemOA is not initialised on the project.

        Example:
            >>> infl = project.InflectionFeatures
            >>> agr_type = infl.TypeCreate("tCommonAgr", "Agr")
            >>> assert infl.TypeFind("tCommonAgr") is not None
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(name, "name")
        self._ValidateParam(abbreviation, "abbreviation")

        if not name or not name.strip():
            raise FP_ParameterError("Type name cannot be empty")
        if not abbreviation or not abbreviation.strip():
            raise FP_ParameterError("Type abbreviation cannot be empty")

        existing = self.TypeFind(name)
        if existing is not None:
            raise FP_ParameterError(
                f"Inflection feature-struct type '{name}' already exists"
            )

        feature_system = self.project.lp.MsFeatureSystemOA
        if feature_system is None:
            raise FP_ParameterError(
                "Project has no MsFeatureSystemOA; cannot create "
                "feature-struct type. Open the project in FieldWorks "
                "once to initialise the feature system."
            )

        # The interface IFsFeatStrucTypeFactory declares a 2-arg
        # Create(Guid, IFsFeatureSystem) overload, but the concrete
        # SIL.LCModel.DomainImpl.FsFeatStrucTypeFactory only exposes
        # Create() and Create(Guid) -- the 2-arg form is an interface
        # default/extension that pythonnet's overload resolver
        # cannot bind. Path B is therefore the only viable path:
        # create the type with an explicit GUID, then attach to
        # MsFeatureSystemOA.TypesOC BEFORE the multistring writes so
        # the Phase 2 ownership rule still holds.
        factory = self.project.project.ServiceLocator.GetService(
            IFsFeatStrucTypeFactory
        )
        new_guid = System.Guid.NewGuid()

        with self._TransactionCM(f"Create feature-struct type '{name}'"):
            new_type = factory.Create(new_guid)
            feature_system.TypesOC.Add(new_type)

            ws_handle = self.__WSHandle(None)
            new_type.Name.set_String(
                ws_handle, TsStringUtils.MakeString(name, ws_handle)
            )
            new_type.Abbreviation.set_String(
                ws_handle, TsStringUtils.MakeString(abbreviation, ws_handle)
            )

            return new_type

    @OperationsMethod
    def Create(self, name, abbreviation, type="closed", catalogSourceId=None, force=False):
        """
        Create a new inflection feature (IFsClosedFeature or IFsComplexFeature).

        Mirrors PhonFeatureOperations.Create so the API surface is symmetric
        across the two feature systems. The legacy FeatureCreate(name, type)
        method is preserved as a back-compat shim.

        Args:
            name (str): Feature name (e.g. "person", "number").
            abbreviation (str): Short abbreviation (e.g. "pers", "num").
            type (str): "closed" (default) for IFsClosedFeature, "complex"
                for IFsComplexFeature.
            catalogSourceId (str, optional): Optional catalog id. If it starts
                with the ``INFL:`` prefix (case-insensitive), the feature is
                created from the MGA EticGlossList.xml catalog (canonical
                GUID + localized strings + value children). When the
                canonical feature already exists in the project,
                ``CreateFromCatalog`` is idempotent by GUID and returns the
                existing object; the user-supplied name/abbreviation are
                only overlaid when the analysis-WS slots are empty (a
                fresh import). When the canonical labels already match
                the user's args, the call is a no-op. When they conflict
                (e.g. the FLEx UI user localized the labels), the call
                refuses with FP_ParameterError -- pass ``force=True`` to
                overlay anyway. Otherwise the value is written verbatim
                to ``CatalogSourceId``.
            force (bool): If True, overlay name/abbreviation onto a
                pre-existing canonical feature even when the labels
                conflict. Default False (refuse). (issue #138)

        Returns:
            IFsFeatDefn: The newly created feature.

        Raises:
            FP_ReadOnlyError, FP_NullParameterError, FP_ParameterError:
                Per BaseOperations validation rules. FP_ParameterError is
                also raised when the catalog returns an existing feature
                with canonical labels that conflict with the user's args
                and ``force=False``.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(name, "name")
        self._ValidateParam(abbreviation, "abbreviation")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")
        if not abbreviation or not abbreviation.strip():
            raise FP_ParameterError("Abbreviation cannot be empty")

        # Catalog-driven creation: defer to CreateFromCatalog (inherited from
        # CatalogBackedMixin) for the canonical GUID + values, then overlay
        # ONLY if the canonical labels are empty or force=True. Otherwise
        # the canonical labels (possibly set by the FLEx UI user or a prior
        # programmatic call) would be silently overwritten. (issue #138)
        if catalogSourceId and catalogSourceId.upper().startswith(CATALOG_PREFIX + ":"):
            wsHandle = self.project.project.DefaultAnalWs
            with self._TransactionCM(f"Create inflection feature '{name}'"):
                new_feat = self.CreateFromCatalog(catalogSourceId)
                self.__OverlayCanonicalLabels(
                    new_feat, name, abbreviation, wsHandle, force, catalogSourceId
                )
                return new_feat

        # Uniqueness by name.
        if self.Exists(name):
            raise FP_ParameterError(f"Inflection feature '{name}' already exists")

        wsHandle = self.project.project.DefaultAnalWs

        feature_system = self.project.lp.MsFeatureSystemOA
        if feature_system is None:
            raise FP_ParameterError(
                "Project has no MsFeatureSystemOA; cannot create "
                "inflection features."
            )

        # Phase 2 ownership-ordering rule: attach to the owning collection
        # FIRST, then mutate properties.
        type_normalized = (type or "closed").strip().lower()

        with self._TransactionCM(f"Create inflection feature '{name}'"):
            if type_normalized == "complex":
                factory = self.project.project.ServiceLocator.GetService(
                    IFsComplexFeatureFactory
                )
                new_feat = factory.Create()
                feature_system.FeaturesOC.Add(new_feat)
                new_feat = IFsComplexFeature(new_feat)
            else:
                factory = self.project.project.ServiceLocator.GetService(
                    IFsClosedFeatureFactory
                )
                new_feat = factory.Create()
                feature_system.FeaturesOC.Add(new_feat)
                new_feat = IFsClosedFeature(new_feat)

            # Set name + abbreviation in default analysis WS.
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_feat.Name.set_String(wsHandle, mkstr_name)
            mkstr_abbr = TsStringUtils.MakeString(abbreviation, wsHandle)
            new_feat.Abbreviation.set_String(wsHandle, mkstr_abbr)

            # Verbatim CatalogSourceId for non-INFL: prefixes (and bare ids).
            if catalogSourceId:
                new_feat.CatalogSourceId = catalogSourceId

            return new_feat

    @OperationsMethod
    def CreateValue(self, feature_or_hvo, name, abbreviation, value_marker=None):
        """
        Create a new symbolic value (IFsSymFeatVal) under a closed inflection
        feature.

        Args:
            feature_or_hvo: The IFsClosedFeature or HVO that owns the value.
            name (str): Value name (e.g. "first", "second", "third" for person).
            abbreviation (str): Short abbreviation (e.g. "1", "2", "3").
            value_marker (str, optional): Currently informational only -- the
                abbreviation itself carries the marker.

        Returns:
            IFsSymFeatVal: The newly created value.

        Notes:
            - Applies the Phase 2 ownership-ordering rule: factory.Create()
              -> feature.ValuesOC.Add() -> set Name + Abbreviation.
            - Mirrors PhonFeatureOperations.CreateValue.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")
        self._ValidateParam(name, "name")
        self._ValidateParam(abbreviation, "abbreviation")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")
        if not abbreviation or not str(abbreviation).strip():
            raise FP_ParameterError("Abbreviation cannot be empty")

        feature = self.__ResolveFeature(feature_or_hvo)
        # Cast to IFsClosedFeature so ValuesOC is accessible. IFsComplexFeature
        # has no ValuesOC -- value creation only makes sense on closed features.
        try:
            feature = IFsClosedFeature(feature)
        except Exception:
            raise FP_ParameterError(
                "CreateValue requires an IFsClosedFeature; complex features "
                "do not have a ValuesOC collection."
            )
        wsHandle = self.project.project.DefaultAnalWs

        factory = self.project.project.ServiceLocator.GetService(
            IFsSymFeatValFactory
        )

        with self._TransactionCM(f"Create feature value '{name}'"):
            new_val = factory.Create()
            # Ownership-first: attach to feature.ValuesOC before mutating strings.
            feature.ValuesOC.Add(new_val)
            new_val = IFsSymFeatVal(new_val)

            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_val.Name.set_String(wsHandle, mkstr_name)
            mkstr_abbr = TsStringUtils.MakeString(abbreviation, wsHandle)
            new_val.Abbreviation.set_String(wsHandle, mkstr_abbr)

            _ = value_marker  # reserved for future strict-mode check
            return new_val

    @OperationsMethod
    def CreateClosedFeatureWithValues(
        self, name, abbreviation, values, catalogSourceId=None
    ):
        """
        One-shot convenience: create a closed feature plus its symbolic
        values in a single call.

        Wraps Create(...) and CreateValue(...) so the very common pattern
        of "define a gender feature with masculine/feminine/neuter values"
        doesn't require interleaving wrapper calls.

        Args:
            name (str): Feature name (e.g. "gender").
            abbreviation (str): Feature abbreviation (e.g. "gen").
            values (sequence): Iterable of ``(value_name, value_abbreviation)``
                tuples. Order is preserved.
            catalogSourceId (str, optional): Optional catalog id forwarded
                to Create(). When the "INFL:" prefix is used, value
                children are populated from the catalog and these
                ``values`` overlay/append to them.

        Returns:
            tuple[IFsClosedFeature, list[IFsSymFeatVal]]: The new feature
            and the list of newly created value objects (in the order
            they were declared in ``values``).

        Raises:
            FP_ParameterError: If values is not iterable or contains
                malformed tuples.

        Example:
            >>> feature, vals = project.Features.CreateClosedFeatureWithValues(
            ...     name="gender", abbreviation="gen",
            ...     values=[("masculine", "m"), ("feminine", "f"), ("neuter", "n")],
            ... )
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(values, "values")

        # Validate the value tuples up front so a malformed list doesn't
        # leave a half-populated feature behind.
        normalized = []
        for i, pair in enumerate(values):
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise FP_ParameterError(
                    f"values[{i}] must be a (name, abbreviation) tuple"
                )
            vname, vabbr = pair
            if not vname or not str(vname).strip():
                raise FP_ParameterError(f"values[{i}] name cannot be empty")
            if not vabbr or not str(vabbr).strip():
                raise FP_ParameterError(
                    f"values[{i}] abbreviation cannot be empty"
                )
            normalized.append((str(vname), str(vabbr)))

        with self._TransactionCM(f"Create closed feature '{name}' with values"):
            feature = self.Create(
                name=name,
                abbreviation=abbreviation,
                type="closed",
                catalogSourceId=catalogSourceId,
            )
            # Roll the feature back if any CreateValue fails mid-loop, so a
            # downstream LCM exception (WS issue, GUID collision, etc.)
            # doesn't leave a partially-populated feature behind. Up-front
            # tuple-shape validation above already covers the cheap-fail
            # cases; this guards the LCM-call slice. (issue #127)
            created_values = []
            try:
                for vname, vabbr in normalized:
                    created_values.append(self.CreateValue(feature, vname, vabbr))
            except Exception:
                try:
                    self.FeatureDelete(feature)
                except Exception:
                    # Best-effort rollback; if FeatureDelete also fails
                    # (read-only transaction, weird LCM state), let the
                    # original exception propagate -- it carries the real
                    # failure.
                    pass
                raise

            return feature, created_values

    @OperationsMethod
    def MakeFeatStruc(self, specs, owner=None):
        """
        Build an IFsFeatStruc populated with (feature, value) pairs.

        Mirrors PhonFeatureOperations.MakeFeatStruc; produces inflection
        feature structures suitable for attaching to MSAs and inflection
        templates.

        Args:
            specs (list[tuple]): A list of ``(feature, value)`` tuples.
                Each side may be an IFsClosedFeature / IFsSymFeatVal
                object, a wrapper, or an HVO. Items are added to the
                struct's ``FeatureSpecsOC`` in the order provided.

            owner: LCM object that owns the struct via its
                ``FeaturesOA`` atomic-owning property. **Required.**
                The struct is attached BEFORE its FeatureSpecsOC is
                populated (Phase 2 ownership rule -- LCM property
                accessors NPE on free-floating IFsFeatStruc objects).

                ``owner=None`` is rejected unconditionally (issue #28,
                matching PhonFeatureOperations.MakeFeatStruc).
                Inflection-feature structs typically attach to MSAs,
                inflection templates, or syntactic contexts.

        Returns:
            IFsFeatStruc: The populated feature structure, attached to
            ``owner.FeaturesOA``.

        Raises:
            FP_ParameterError: If ``owner`` is None, if a spec tuple
                is malformed, or if ``owner`` has no FeaturesOA
                property.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(specs, "specs")

        if owner is None:
            raise FP_ParameterError(
                "MakeFeatStruc requires an owner. LCM property "
                "accessors NPE on free-floating IFsFeatStruc objects, "
                "so the previous unowned-empty mode produced an "
                "unusable struct (issue #28). Pass owner=msa / "
                "owner=template / owner=context."
            )

        # Normalize and validate specs up front, before any LCM mutation.
        normalized = []
        for i, pair in enumerate(specs):
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise FP_ParameterError(
                    f"specs[{i}] must be a (feature, value) tuple"
                )
            feat_in, val_in = pair
            feat = self.__Unwrap(self.__ResolveFeature(feat_in) if not isinstance(feat_in, int) else self.project.Object(feat_in))
            val = self.__Unwrap(val_in if not isinstance(val_in, int) else self.project.Object(val_in))
            normalized.append((feat, val))

        # Attach owner FIRST so subsequent FeatureSpecsOC mutations
        # don't trip the Phase 2 NPE pattern.
        owner_unwrapped = self.__Unwrap(owner)
        if not hasattr(owner_unwrapped, "FeaturesOA"):
            raise FP_ParameterError(
                "owner has no FeaturesOA property; cannot attach FsFeatStruc."
            )

        factory = self.project.project.ServiceLocator.GetService(
            IFsFeatStrucFactory
        )

        with self._TransactionCM("Make feature structure"):
            struct = factory.Create()
            owner_unwrapped.FeaturesOA = struct
            # Re-fetch via the owning property to hold the LCM view of the
            # now-owned struct.
            struct = IFsFeatStruc(owner_unwrapped.FeaturesOA)

            # Populate FeatureSpecsOC. Each spec is an IFsClosedValue with
            # FeatureRA -> feature and ValueRA -> value.
            cv_factory = self.project.project.ServiceLocator.GetService(
                IFsClosedValueFactory
            )
            for feat, val in normalized:
                closed_value = cv_factory.Create()
                struct.FeatureSpecsOC.Add(closed_value)
                cv = IFsClosedValue(closed_value)
                cv.FeatureRA = feat
                cv.ValueRA = val

            return struct

    @OperationsMethod
    def FeatureCreate(self, name, type):
        """
        Create a new feature definition.

        Args:
            name (str): The name of the feature (e.g., "person", "number", "tense").
            type (str): The type of feature (e.g., "complex" for structured features).

        Returns:
            IFsFeatureDefn: The newly created feature definition object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name or type is None.
            FP_ParameterError: If name or type is empty, or if a feature with
                this name already exists.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> person = inflOps.FeatureCreate("person", "complex")
            >>> number = inflOps.FeatureCreate("number", "complex")
            >>> tense = inflOps.FeatureCreate("tense", "complex")

        Notes:
            - Features define grammatical categories
            - Values must be added separately after creation
            - Features can be shared across multiple parts of speech
            - The 'complex' type is used for features with multiple values
            - Feature is created in the default analysis writing system

        See Also:
            FeatureDelete, FeatureGetAll, FeatureGetValues
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")
        self._ValidateParam(type, "type")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")
        if not type or not type.strip():
            raise FP_ParameterError("Type cannot be empty")

        # Check if feature already exists
        wsHandle = self.project.project.DefaultAnalWs
        target = normalize_match_key(name, casefold=True)
        for existing_feature in self.FeatureGetAll():
            existing_name = ITsString(existing_feature.Name.get_String(wsHandle)).Text
            if existing_name and normalize_match_key(existing_name, casefold=True) == target:
                raise FP_ParameterError(f"Feature '{name}' already exists")

        # Create the new feature using the factory
        # Using complex feature factory as it's the most common type
        factory = self.project.project.ServiceLocator.GetService(IFsComplexFeatureFactory)

        with self._TransactionCM(f"Create feature '{name}'"):
            new_feature = factory.Create()

            # Add to the feature system (must be done before setting properties)
            feature_system = self.project.lp.MsFeatureSystemOA
            if feature_system:
                feature_system.FeaturesOC.Add(new_feature)

            # Set name
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_feature.Name.set_String(wsHandle, mkstr_name)

            return new_feature

    @OperationsMethod
    def FeatureDelete(self, feature_or_hvo):
        """
        Delete a feature definition.

        Args:
            feature_or_hvo: The IFsFeatureDefn object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If feature_or_hvo is None.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> # Find and delete a test feature
            >>> for feature in inflOps.FeatureGetAll():
            ...     ws = project.project.DefaultAnalWs
            ...     name = ITsString(feature.Name.get_String(ws)).Text
            ...     if name == "test_feature":
            ...         inflOps.FeatureDelete(feature)
            ...         break

        Warning:
            - Cannot delete if used in feature structures
            - Cannot delete if referenced by entries or morphemes
            - Check dependencies before deletion
            - Deletion is permanent and cannot be undone

        See Also:
            FeatureCreate, FeatureGetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(feature_or_hvo, "feature_or_hvo")

        # Resolve to feature object
        feature = self.__ResolveFeature(feature_or_hvo)

        # Remove from the feature system
        feature_system = self.project.lp.MsFeatureSystemOA
        if feature_system:
            feature_system.FeaturesOC.Remove(feature)

    @OperationsMethod
    def FeatureGetValues(self, feature_or_hvo):
        """
        Get all possible values for a feature.

        Args:
            feature_or_hvo: The IFsFeatureDefn object or HVO.

        Returns:
            list: List of feature value objects (empty list if none).

        Raises:
            FP_NullParameterError: If feature_or_hvo is None.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> person = inflOps.FeatureCreate("person", "complex")
            >>> # After adding values 1st, 2nd, 3rd...
            >>> values = inflOps.FeatureGetValues(person)
            >>> print(f"Person has {len(values)} values")

        Notes:
            - Returns symbolic values (named choices)
            - Empty list if no values defined yet
            - Values represent the possible settings for this feature
            - Example: person feature has values [1st, 2nd, 3rd]
            - Example: number feature has values [singular, plural]
            - The type and structure of values depends on the feature type

        See Also:
            FeatureCreate, FeatureGetAll
        """
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")

        feature = self.__ResolveFeature(feature_or_hvo)

        # IFsClosedFeature has the symbolic ValuesOC; IFsComplexFeature
        # has no children of its own at this surface (sub-features live
        # on its TypeRA.FeaturesRS, a separate read shape). The previous
        # hasattr(feature, "FeaturesOS") fallback was always False at
        # runtime -- no IFsFeatDefn variant exposes FeaturesOS. Removed
        # in (#140); a IFsComplexFeature traversal would belong in a
        # separate method with an explicit isinstance check.
        if hasattr(feature, "ValuesOC"):
            return list(feature.ValuesOC)
        return []

    @OperationsMethod
    def GetFeatures(self, feature_system_or_hvo):
        """
        Get all features in the feature system (READ-ONLY).

        Args:
            feature_system_or_hvo: The feature system object or HVO.

        Returns:
            list: List of feature definition objects (IFsFeatDefn).

        Raises:
            FP_NullParameterError: If feature_system_or_hvo is None.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> # Get the feature system
            >>> feature_system = project.lp.MsFeatureSystemOA
            >>> if feature_system:
            ...     features = inflOps.GetFeatures(feature_system)
            ...     print(f"Feature system has {len(features)} features")
            ...     for feature in features:
            ...         wsHandle = project.project.DefaultAnalWs
            ...         name = ITsString(feature.Name.get_String(wsHandle)).Text
            ...         print(f"  - {name}")
            Feature system has 3 features
              - person
              - number
              - tense

        Notes:
            - READ-ONLY property - returns the collection
            - Access via feature_system.FeaturesOC (IFsFeatureSystem owns
              feature definitions as an owning collection, not sequence)
            - Returns empty list if no features defined
            - Features represent grammatical categories
            - Each feature can have multiple values

        See Also:
            GetFeatureConstraints, FeatureGetAll, FeatureCreate
        """
        self._ValidateParam(feature_system_or_hvo, "feature_system_or_hvo")

        # Resolve to feature system object
        if isinstance(feature_system_or_hvo, int):
            feature_system = self.project.Object(feature_system_or_hvo)
        else:
            feature_system = feature_system_or_hvo

        # Return features collection if it exists
        if hasattr(feature_system, "FeaturesOC"):
            return list(feature_system.FeaturesOC)

        return []

    @OperationsMethod
    def GetFeatureConstraints(self, feature_system_or_hvo):
        """
        Get all feature constraints in the feature system (READ-ONLY).

        Args:
            feature_system_or_hvo: The feature system object or HVO.

        Returns:
            list: List of feature constraint objects.

        Raises:
            FP_NullParameterError: If feature_system_or_hvo is None.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> # Get the feature system
            >>> feature_system = project.lp.MsFeatureSystemOA
            >>> if feature_system:
            ...     constraints = inflOps.GetFeatureConstraints(feature_system)
            ...     print(f"Feature system has {len(constraints)} constraints")
            ...     for constraint in constraints:
            ...         print(f"  - Constraint HVO: {constraint.Hvo}")

        Notes:
            - READ-ONLY property - returns the collection
            - Access via feature_system.FeatureConstraints
            - Returns empty list if no constraints defined
            - Constraints restrict valid feature combinations
            - Used for modeling co-occurrence restrictions
            - Example: agreement constraints between features

        See Also:
            GetFeatures, FeatureGetAll
        """
        self._ValidateParam(feature_system_or_hvo, "feature_system_or_hvo")

        # Resolve to feature system object
        if isinstance(feature_system_or_hvo, int):
            feature_system = self.project.Object(feature_system_or_hvo)
        else:
            feature_system = feature_system_or_hvo

        # Return feature constraints collection if it exists
        if hasattr(feature_system, "FeatureConstraintsOC"):
            return list(feature_system.FeatureConstraintsOC)

        return []

    @OperationsMethod
    def GetTypes(self, feature_system_or_hvo):
        """
        Get the feature types collection from a feature system (READ-ONLY).

        This is a getter-only method that returns the collection of feature types
        defined in the morphosyntactic feature system. Feature types categorize
        features into groups (e.g., inflectional features, agreement features).

        Args:
            feature_system_or_hvo: The IFsFeatureSystem object or HVO, or None to
                use the project's default feature system.

        Returns:
            list: List of feature type objects (IFsFeatDefn) from the TypesOC
                collection, or empty list if none defined.

        Raises:
            FP_NullParameterError: If feature_system_or_hvo is explicitly None
                and no default feature system exists.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> # Get types from default feature system
            >>> types = inflOps.GetTypes(None)
            >>> for ftype in types:
            ...     print(f"Feature type: {ftype}")

            >>> # Get types from specific feature system
            >>> fs = project.lp.MsFeatureSystemOA
            >>> types = inflOps.GetTypes(fs)
            >>> print(f"Found {len(types)} feature types")

            >>> # Iterate and display type names
            >>> for ftype in types:
            ...     ws = project.project.DefaultAnalWs
            ...     name = ITsString(ftype.Name.get_String(ws)).Text
            ...     print(f"Type: {name}")

        Notes:
            - This is a READ-ONLY property (no setter provided)
            - Returns the TypesOC collection from the feature system
            - TypesOC contains feature type definitions
            - Returns empty list if feature system has no types
            - Feature types organize and categorize features
            - If feature_system_or_hvo is None, uses MsFeatureSystemOA
            - Common feature types include inflectional, derivational, agreement

        See Also:
            FeatureGetAll, FeatureCreate, FeatureStructureGetAll
        """
        # Get the feature system
        if feature_system_or_hvo is None:
            feature_system = self.project.lp.MsFeatureSystemOA
            self._ValidateParam(feature_system, "feature_system")
        else:
            feature_system = self.__ResolveFeatureSystem(feature_system_or_hvo)

        # Return the types collection if it exists
        if hasattr(feature_system, "TypesOC"):
            return list(feature_system.TypesOC)

        return []

    # ========================================================================
    # CATALOG (eticGlossList) IMPORT METHODS
    # ========================================================================
    #
    # The public API (ImportCatalog / CreateFromCatalog /
    # FixGuidsAgainstCatalog) and the catalog-walking helpers live on
    # CatalogBackedMixin (extracted in Phase 5c). The hooks below tell
    # the mixin how to talk to the InflFeats-specific LCM types
    # (IFsClosedFeature + its IFsSymFeatVal value children) under
    # MsFeatureSystemOA.
    #
    # Phase 2 ownership-ordering lesson applies: the mixin attaches via
    # the 2-arg factory overload (feature placed into FeaturesOC at
    # creation) THEN sets the multistring properties; never sets
    # properties on a free-floating feature.
    #
    # Phase 6a MVP scope: closed features only (type="feature" + nested
    # type="value"). The catalog also has type="fsType" and type="complex"
    # items; parse_etic_gloss_list silently skips them at parse time, so
    # they never reach these hooks. fsType/complex import is deferred.

    # --- CatalogBackedMixin hooks --------------------------------------

    def _get_root_list(self):
        """Return the top-level owner (MsFeatureSystemOA)."""
        return self.project.lp.MsFeatureSystemOA

    def _get_factory(self):
        """Resolve the IFsClosedFeature factory for the mixin's Path B."""
        return self.project.project.ServiceLocator.GetService(
            IFsClosedFeatureFactory
        )

    def _factory_create_attached(self, guid, parent_obj):
        """
        Path A: try the 2-arg factory overload. For inflection features,
        parent_obj is always None (features are flat, owned directly by
        MsFeatureSystemOA.FeaturesOC), so we always pass the feature
        system as the second arg.

        Pythonnet may not expose the 2-arg overload on the interface
        variable; returning None lets the mixin fall back to Path B.
        """
        factory = self._get_factory()
        feature_system = self._get_root_list()
        try:
            return factory.Create(guid, feature_system)
        except Exception:
            return None

    def _path_b_attach(self, new_obj, parent_obj):
        """
        Path B fallback: attach a free-floating feature to
        MsFeatureSystemOA.FeaturesOC. parent_obj is ignored (always None
        for top-level features).
        """
        self._get_root_list().FeaturesOC.Add(new_obj)

    def _cast_to_domain(self, raw):
        """Return the IFsClosedFeature view of a raw LCM feature object."""
        return IFsClosedFeature(raw)

    def _set_localized(self, obj, term, abbrev, def_, missing_ws_seen, warnings):
        """Per-WS multistring writes for Name/Abbreviation/Description."""
        self._set_multistring(obj.Name, term, missing_ws_seen, warnings)
        self._set_multistring(obj.Abbreviation, abbrev, missing_ws_seen, warnings)
        if hasattr(obj, "Description"):
            self._set_multistring(obj.Description, def_, missing_ws_seen, warnings)

    def _walk_existing(self):
        """
        Yield each IFsClosedFeature in MsFeatureSystemOA. Features are
        flat (no hierarchy among themselves), so this is a single-level
        walk. Value children are NOT included here -- value idempotency
        is checked per-feature in _handle_entry_children.

        FeaturesOC may also contain IFsComplexFeature items (FW's stock
        projects ship complex morphosyntactic features pre-installed).
        Those are not catalog candidates here, so we filter by
        ClassName and yield only the closed features.
        """
        feature_system = self.project.lp.MsFeatureSystemOA
        if feature_system is None:
            return
        for raw in feature_system.FeaturesOC:
            if raw.ClassName == "FsClosedFeature":
                yield IFsClosedFeature(raw)
            # else: complex/other feature types live alongside but
            # aren't part of this catalog domain; skip silently.

    def _handle_entry_children(self, entry, created_feature, missing_ws_seen, warnings, result):
        """
        Create IFsSymFeatVal items for each value child of `entry` under
        `created_feature.ValuesOC`. Idempotency is checked per-feature
        against the existing value GUIDs on the feature.

        ``result`` is a CatalogImportResult when called from
        ImportCatalog, or None when called from CreateFromCatalog /
        FixGuidsAgainstCatalog (we still create missing values; we just
        don't accumulate counts).
        """
        existing_value_guids = {
            str(v.Guid).lower() for v in created_feature.ValuesOC
        }
        for value_entry in entry.children:
            v_guid = value_entry.guid.lower() if value_entry.guid else ""
            if v_guid and v_guid in existing_value_guids:
                if result is not None:
                    result.skipped_count += 1
                continue
            self._CreateValueFromEntry(
                value_entry, created_feature, missing_ws_seen, warnings
            )
            if result is not None:
                result.created_count += 1
                if v_guid:
                    result.created_guids.append(v_guid)
            if v_guid:
                # Track within this pass so a duplicate entry (e.g.
                # badly-formed catalog) won't re-create.
                existing_value_guids.add(v_guid)

    # --- Value-child creation ------------------------------------------
    #
    # The mixin handles feature-level creation. Value (IFsSymFeatVal)
    # creation stays local because IFsSymFeatVal doesn't fit the same
    # _create_from_entry contract (no CatalogSourceId field; different
    # parent shape). Mirrors the PhonFeats implementation.

    def _CreateValueFromEntry(
        self, value_entry, parent_feature, missing_ws_seen, warnings
    ):
        """
        Internal: instantiate one IFsSymFeatVal under `parent_feature`
        from a value-typed CatalogEntry. Applies the canonical GUID and
        per-WS strings.

        Applies the Phase 2 ownership-ordering rule: attach first (via
        the 2-arg factory overload, or fall back to Create+Add), then
        mutate properties.
        """
        factory = self.project.project.ServiceLocator.GetService(
            IFsSymFeatValFactory
        )
        guid = System.Guid(value_entry.guid)

        new_val = None
        # Path A: 2-arg factory overload if pythonnet exposes it.
        try:
            new_val = factory.Create(guid, parent_feature)
        except Exception:
            new_val = None

        if new_val is None:
            # Path B: implementation-side Create(Guid) followed by Add().
            concrete_factory = (
                cast_to_concrete(factory)
                if hasattr(factory, "ClassName")
                else factory
            )
            try:
                new_val = concrete_factory.Create(guid)
            except Exception as e:
                # No safe fallback: parameterless Create() would generate
                # a random GUID. Match the mixin's Path-A+B-failure
                # discipline (Phase 5a).
                raise FP_ParameterError(
                    f"Could not create feature value '{value_entry.id}' "
                    f"with canonical GUID {value_entry.guid} via either "
                    f"Create(Guid, parent) or Create(Guid) factory "
                    f"overloads."
                ) from e
            parent_feature.ValuesOC.Add(new_val)

        new_val = IFsSymFeatVal(new_val)

        # Per-WS strings (abbreviation is the short value marker; term is
        # the value name).
        self._set_multistring(
            new_val.Name, value_entry.term, missing_ws_seen, warnings
        )
        self._set_multistring(
            new_val.Abbreviation, value_entry.abbrev, missing_ws_seen, warnings
        )
        if hasattr(new_val, "Description"):
            self._set_multistring(
                new_val.Description, value_entry.def_, missing_ws_seen, warnings
            )

        # IFsSymFeatVal does not have a CatalogSourceId field in stock
        # LCM, so we don't try to set one. Value-level catalog provenance
        # is recoverable indirectly via the parent feature's
        # CatalogSourceId and the value's canonical GUID.

        return new_val

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def __ResolveInflectionClass(self, ic_or_hvo):
        """
        Resolve HVO or object to IMoInflClass.

        Args:
            ic_or_hvo: Either an IMoInflClass object or an HVO (int).

        Returns:
            IMoInflClass: The resolved inflection class object.
        """
        if isinstance(ic_or_hvo, int):
            return self.project.Object(ic_or_hvo)
        return ic_or_hvo

    def __ResolveFeatureStructure(self, fs_or_hvo):
        """
        Resolve HVO or object to IFsFeatStruc.

        Args:
            fs_or_hvo: Either an IFsFeatStruc object or an HVO (int).

        Returns:
            IFsFeatStruc: The resolved feature structure object.
        """
        if isinstance(fs_or_hvo, int):
            return self.project.Object(fs_or_hvo)
        return fs_or_hvo

    def __ResolveFeature(self, feature_or_hvo):
        """
        Resolve HVO or object to IFsFeatureDefn.

        Args:
            feature_or_hvo: Either an IFsFeatureDefn object or an HVO (int).

        Returns:
            IFsFeatureDefn: The resolved feature definition object.
        """
        if isinstance(feature_or_hvo, int):
            return self.project.Object(feature_or_hvo)
        return feature_or_hvo

    def __ResolveFeatureSystem(self, fs_or_hvo):
        """
        Resolve HVO or object to IFsFeatureSystem.

        Args:
            fs_or_hvo: Either an IFsFeatureSystem object or an HVO (int).

        Returns:
            IFsFeatureSystem: The resolved feature system object.
        """
        if isinstance(fs_or_hvo, int):
            return self.project.Object(fs_or_hvo)
        return fs_or_hvo

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        This method works with inflection classes (IMoInflClass). For features and
        feature structures, use separate sync methods if needed.

        Args:
            item: The IMoInflClass (inflection class) object.

        Returns:
            dict: Dictionary mapping property names to their values.
                Keys are property names, values are the property values.

        Example:
            >>> inflOps = InflectionFeatureOperations(project)
            >>> ic = list(inflOps.InflectionClassGetAll())[0]
            >>> props = inflOps.GetSyncableProperties(ic)
            >>> print(props.keys())
            dict_keys(['Name', 'Abbreviation', 'Description'])

        Notes:
            - Returns all MultiString properties (all writing systems)
            - This implementation focuses on inflection classes
            - Does not include GUID or HVO
        """
        ic = self.__ResolveInflectionClass(item)

        # Get all writing systems for MultiString properties
        # Fix: ILgWritingSystemFactory does not expose a .WritingSystems
        # property; enumerate via the wrapper's WritingSystemOperations.GetAll(),
        # which returns CoreWritingSystemDefinition objects with .Id / .Handle.
        all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}

        props = {}

        # MultiString properties
        for prop_name in ["Name", "Abbreviation", "Description"]:
            if hasattr(ic, prop_name):
                prop_obj = getattr(ic, prop_name)
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
        Compare two inflection classes and return detailed differences.

        Args:
            item1: First inflection class to compare (from source project).
            item2: Second inflection class to compare (from target project).
            ops1: Optional InflectionFeatureOperations instance for item1's project.
                 Defaults to self.
            ops2: Optional InflectionFeatureOperations instance for item2's project.
                 Defaults to self.

        Returns:
            tuple: (is_different, differences) where:
                - is_different (bool): True if items differ
                - differences (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> ic1 = project1_inflOps.InflectionClassFind("First Declension")
            >>> ic2 = project2_inflOps.InflectionClassFind("First Declension")
            >>> is_diff, diffs = project1_inflOps.CompareTo(
            ...     ic1, ic2,
            ...     ops1=project1_inflOps,
            ...     ops2=project2_inflOps
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

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def __OverlayCanonicalLabels(self, feat, name, abbreviation, wsHandle, force, catalogSourceId):
        """
        Overlay user-supplied name + abbreviation onto a feature returned
        by CreateFromCatalog -- but only when it is safe to do so.

        CreateFromCatalog is idempotent by canonical GUID: if the feature
        already exists in the project (a prior import or a FLEx UI user
        having created it), the existing object is returned. Blindly
        writing user-supplied name/abbreviation onto it would silently
        clobber whatever canonical labels were already there.

        Policy:
        - Slots empty -> overlay (newly imported feature, no conflict).
        - Slots match args -> idempotent no-op.
        - Slots differ and force=False -> refuse with a clear pointer.
        - Slots differ and force=True -> overlay (caller opted in).

        (issue #138)
        """
        existing_name = ITsString(feat.Name.get_String(wsHandle)).Text or ""
        existing_abbr = ITsString(feat.Abbreviation.get_String(wsHandle)).Text or ""

        if not force and (existing_name or existing_abbr):
            if existing_name == name and existing_abbr == abbreviation:
                # Already labeled exactly as requested; idempotent.
                return
            raise FP_ParameterError(
                f"Inflection feature for catalog id {catalogSourceId!r} "
                f"already exists with canonical labels "
                f"Name={existing_name!r} Abbreviation={existing_abbr!r}. "
                f"Refusing to overwrite with Name={name!r} "
                f"Abbreviation={abbreviation!r}. Pass force=True to "
                f"overlay anyway."
            )

        mkstr_name = TsStringUtils.MakeString(name, wsHandle)
        feat.Name.set_String(wsHandle, mkstr_name)
        mkstr_abbr = TsStringUtils.MakeString(abbreviation, wsHandle)
        feat.Abbreviation.set_String(wsHandle, mkstr_abbr)

    def __Unwrap(self, obj):
        """
        Peel off LCMObjectWrapper-style wrappers, if any. Plain LCM
        objects pass through unchanged. Mirrors PhonFeatureOperations.__Unwrap
        so that wrapper objects can be passed as feature/value/owner
        arguments to MakeFeatStruc (issue #120).
        """
        if hasattr(obj, "_obj") and not hasattr(obj, "Hvo"):
            return obj._obj
        if hasattr(obj, "_obj") and hasattr(obj._obj, "Hvo"):
            return obj._obj
        return obj

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
