#
#   PhonFeatureOperations.py
#
#   Class: PhonFeatureOperations
#          Phonological feature operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#          Manages the phonological feature system (PhFeatureSystemOA),
#          which owns IFsClosedFeature definitions and their IFsSymFeatVal
#          values. Also provides a helper for composing IFsFeatStruc objects
#          that attach to phonemes / natural classes.
#
#          The MGA PhonFeatsEticGlossList.xml catalog is the canonical
#          source for the standard set of phonological features and
#          their +/- values.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

# Import BaseOperations parent class and decorators
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import FLEx LCM types
from SIL.LCModel import (
    IFsClosedFeature,
    IFsClosedFeatureFactory,
    IFsSymFeatVal,
    IFsSymFeatValFactory,
    IFsFeatStruc,
    IFsFeatStrucFactory,
    IFsClosedValue,
    IFsClosedValueFactory,
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


# Canonical relative subdir for the PhonFeats catalog under FWCodeDir.
# Kept as a module constant so verification / tests can reference it.
PHON_FEATS_CATALOG_FILENAME = "PhonFeatsEticGlossList.xml"
PHON_FEATS_CATALOG_SUBDIR = "Language Explorer/MGA/GlossLists"

# Optional prefix the wrapper accepts on CatalogSourceId values. Bare
# ids ("fPAConsonantal") are what FieldWorks itself writes; "PHON:" is
# accepted as a user-facing convenience and is stripped before lookup.
CATALOG_PREFIX = "PHON"


class PhonFeatureOperations(BaseOperations, CatalogBackedMixin):
    """
    This class provides operations for managing phonological features and
    feature values in a FieldWorks project.

    Phonological features are owned by ``LangProject.PhFeatureSystemOA``
    (an ``IFsFeatureSystem``). Each feature is an ``IFsClosedFeature`` with
    one or more ``IFsSymFeatVal`` value children (typically ``+`` and ``-``
    for binary features). Phonemes and natural classes attach an
    ``IFsFeatStruc`` whose ``FeatureSpecsOC`` references (feature, value)
    pairs.

    The MGA ``PhonFeatsEticGlossList.xml`` catalog provides the canonical
    set of features and values with stable GUIDs; ``ImportCatalog`` and
    ``CreateFromCatalog`` populate the project from it.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        phonFeats = project.PhonFeatures

        # Bulk-import the standard MGA feature set.
        result = phonFeats.ImportCatalog()
        print(f"Created {result.created_count}, "
              f"skipped {result.skipped_count}")

        # Or create a specific feature with its +/- values.
        cons = phonFeats.CreateFromCatalog("fPAConsonantal")

        # Compose a feature structure for a phoneme.
        plus = next(v for v in phonFeats.GetValues(cons)
                    if phonFeats.GetAbbreviation(v) == "+")
        struct = phonFeats.MakeFeatStruc([(cons, plus)], owner=phoneme)

        project.CloseProject()
    """

    # --- CatalogBackedMixin configuration ------------------------------
    # The PhonFeats catalog ships with FW under
    # Language Explorer/MGA/GlossLists/PhonFeatsEticGlossList.xml and is
    # parsed by parse_etic_gloss_list. Unlike POS, FW writes BARE entry
    # ids (no "PHON:" prefix) to CatalogSourceId; the mixin honours that
    # with CATALOG_PREFIX_WRITE = None. Features are flat (each top-level
    # entry owns IFsSymFeatVal value children handled by
    # _handle_entry_children), so the recursive-entries flag is off.
    CATALOG_FILE = PHON_FEATS_CATALOG_FILENAME
    CATALOG_SUBDIR = PHON_FEATS_CATALOG_SUBDIR
    CATALOG_PARSER = staticmethod(parse_etic_gloss_list)
    CATALOG_PREFIX_WRITE = None
    DOMAIN_LABEL = "feature"
    _supports_recursive_entries = False

    def __init__(self, project):
        """
        Initialize PhonFeatureOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # ========================================================================
    # READ METHODS
    # ========================================================================

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all phonological features in the project.

        Returns:
            EnumerableWrapper[IFsClosedFeature]: Each feature in PhFeatureSystemOA.FeaturesOC.

        Notes:
            - ``FeaturesOC`` is typed as ``IFsFeatDefn`` in C#. Each yielded
              item is cast to ``IFsClosedFeature`` (the only concrete shape
              this catalog uses) so callers can access ``ValuesOC`` directly.
            - Returns nothing if the project has no PhFeatureSystemOA.
        """
        feature_system = self.project.lp.PhFeatureSystemOA
        if feature_system is None:
            return
        for feat in feature_system.FeaturesOC:
            yield IFsClosedFeature(feat)

    @OperationsMethod
    def GetName(self, feature_or_hvo, wsHandle=None):
        """
        Get the name of a phonological feature or value.

        Args:
            feature_or_hvo: An IFsClosedFeature, IFsSymFeatVal, or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The Name in the requested WS, or "" if not set.
        """
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")
        obj = self.__ResolveObject(feature_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)
        name = ITsString(obj.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def GetAbbreviation(self, feature_or_hvo, wsHandle=None):
        """
        Get the abbreviation of a phonological feature or value.

        For values, the abbreviation is typically ``+`` or ``-``.
        """
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")
        obj = self.__ResolveObject(feature_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)
        abbr = ITsString(obj.Abbreviation.get_String(wsHandle)).Text
        return abbr or ""

    @OperationsMethod
    def GetDescription(self, feature_or_hvo, wsHandle=None):
        """
        Get the description of a phonological feature or value.

        Returns "" if the object has no Description property.
        """
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")
        obj = self.__ResolveObject(feature_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)
        if not hasattr(obj, "Description"):
            return ""
        desc = ITsString(obj.Description.get_String(wsHandle)).Text
        return desc or ""

    @wrap_enumerable
    @OperationsMethod
    def GetValues(self, feature_or_hvo):
        """
        Get all IFsSymFeatVal values defined on a closed feature.

        Args:
            feature_or_hvo: The IFsClosedFeature object or HVO.

        Yields:
            IFsSymFeatVal: Each value (typically "+" and "-" for binary
            phonological features).
        """
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")
        feature = self.__ResolveObject(feature_or_hvo)
        # ValuesOC is typed as IFsSymFeatVal directly.
        for val in feature.ValuesOC:
            yield IFsSymFeatVal(val)

    @OperationsMethod
    def Find(self, name, wsHandle=None):
        """
        Find a phonological feature by name.

        Args:
            name (str): The name to search for. Compared via NFD-normalised
                        casefold match against each feature's Name in the
                        chosen WS.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            IFsClosedFeature or None: First match, or None.

        Notes:
            - Does NOT search value names; values are looked up via
              ``GetValues(feature)``.
            - Matches the feature-name convention used by other linguistic
              Find methods (case-insensitive, NFD-normalised).
        """
        self._ValidateParam(name, "name")
        target = normalize_match_key(name, casefold=True)
        if not target:
            return None
        wsHandle = self.__WSHandle(wsHandle)

        feature_system = self.project.lp.PhFeatureSystemOA
        if feature_system is None:
            return None

        for raw in feature_system.FeaturesOC:
            feat = IFsClosedFeature(raw)
            feat_name = ITsString(feat.Name.get_String(wsHandle)).Text
            if feat_name and normalize_match_key(feat_name, casefold=True) == target:
                return feat
        return None

    @OperationsMethod
    def Exists(self, name, wsHandle=None):
        """
        Check whether a phonological feature with the given name exists.
        """
        self._ValidateParam(name, "name")
        return self.Find(name, wsHandle=wsHandle) is not None

    # ========================================================================
    # WRITE METHODS - FEATURE
    # ========================================================================

    @OperationsMethod
    def Create(self, name, abbreviation, catalogSourceId=None, force=False):
        """
        Create a new phonological feature (IFsClosedFeature).

        Args:
            name (str): Feature name (e.g. "consonantal").
            abbreviation (str): Short abbreviation (e.g. "cons").
            catalogSourceId (str, optional): Optional catalog id. If it
                starts with the ``PHON:`` prefix (case-insensitive),
                the feature is created from the MGA catalog (canonical
                GUID + localized strings + +/- value children). When
                the canonical feature already exists in the project,
                ``CreateFromCatalog`` is idempotent by GUID and returns
                the existing object; the user-supplied name/abbreviation
                are only overlaid when the analysis-WS slots are empty
                (a fresh import). When the canonical labels already match
                the user's args, the call is a no-op. When they conflict,
                the call refuses with FP_ParameterError -- pass
                ``force=True`` to overlay anyway. Otherwise the value is
                written verbatim to ``CatalogSourceId``.
            force (bool): If True, overlay name/abbreviation onto a
                pre-existing canonical feature even when the labels
                conflict. Default False (refuse). (issue #138)

        Returns:
            IFsClosedFeature: The newly created feature.

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

        # Catalog-driven creation: defer to CreateFromCatalog for the
        # canonical GUID + values, then overlay user-supplied strings
        # ONLY when the canonical labels are empty or force=True.
        # Otherwise the canonical labels (possibly set by the FLEx UI
        # user or a prior programmatic call) would be silently
        # overwritten. (issue #138)
        if catalogSourceId and catalogSourceId.upper().startswith(CATALOG_PREFIX + ":"):
            with self._TransactionCM(f"Create phonological feature '{name}'"):
                wsHandle = self.project.project.DefaultAnalWs
                new_feat = self.CreateFromCatalog(catalogSourceId)
                self.__OverlayCanonicalLabels(
                    new_feat, name, abbreviation, wsHandle, force, catalogSourceId
                )
                return new_feat

        # Uniqueness check by name within the feature system.
        if self.Exists(name):
            raise FP_ParameterError(
                f"Phonological feature '{name}' already exists"
            )

        wsHandle = self.project.project.DefaultAnalWs

        feature_system = self.project.lp.PhFeatureSystemOA
        if feature_system is None:
            raise FP_ParameterError(
                "Project has no PhFeatureSystemOA; cannot create "
                "phonological features."
            )

        # Phase 2 ownership-ordering rule: attach to the owning collection
        # FIRST, then mutate properties. The parameterless factory create
        # returns an unowned object whose property setters will NPE until
        # it is added to FeaturesOC.
        factory = self.project.project.ServiceLocator.GetService(
            IFsClosedFeatureFactory
        )
        with self._TransactionCM(f"Create phonological feature '{name}'"):
            new_feat = factory.Create()
            feature_system.FeaturesOC.Add(new_feat)
            new_feat = IFsClosedFeature(new_feat)

            # Set name + abbreviation in default analysis WS.
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_feat.Name.set_String(wsHandle, mkstr_name)
            mkstr_abbr = TsStringUtils.MakeString(abbreviation, wsHandle)
            new_feat.Abbreviation.set_String(wsHandle, mkstr_abbr)

            # Verbatim CatalogSourceId for non-PHON: prefixes (and bare ids).
            if catalogSourceId:
                new_feat.CatalogSourceId = catalogSourceId

            return new_feat

    @OperationsMethod
    def SetName(self, feature_or_hvo, name, wsHandle=None):
        """
        Set the name of a phonological feature or value.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        obj = self.__ResolveObject(feature_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)
        mkstr = TsStringUtils.MakeString(name, wsHandle)
        obj.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def SetAbbreviation(self, feature_or_hvo, abbrev, wsHandle=None):
        """
        Set the abbreviation of a phonological feature or value.

        For values, the abbreviation is typically ``+`` or ``-``.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")
        self._ValidateParam(abbrev, "abbrev")

        if not abbrev or not str(abbrev).strip():
            raise FP_ParameterError("Abbreviation cannot be empty")

        obj = self.__ResolveObject(feature_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)
        mkstr = TsStringUtils.MakeString(abbrev, wsHandle)
        obj.Abbreviation.set_String(wsHandle, mkstr)

    @OperationsMethod
    def SetDescription(self, feature_or_hvo, description, wsHandle=None):
        """
        Set the description of a phonological feature or value.

        Raises:
            FP_ParameterError: If the object has no Description property.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")
        self._ValidateParam(description, "description")

        obj = self.__ResolveObject(feature_or_hvo)
        if not hasattr(obj, "Description"):
            raise FP_ParameterError(
                "Target object has no Description multistring property."
            )
        wsHandle = self.__WSHandle(wsHandle)
        mkstr = TsStringUtils.MakeString(description, wsHandle)
        obj.Description.set_String(wsHandle, mkstr)

    @OperationsMethod
    def Delete(self, feature_or_hvo):
        """
        Delete a phonological feature.

        Args:
            feature_or_hvo: The IFsClosedFeature, wrapper, or HVO to delete.

        Notes:
            - Per Phase 4 lesson, accepts a wrapped form and unwraps it
              before talking to the LCM collection.
            - Deletion removes the feature from PhFeatureSystemOA.FeaturesOC.
              LCM will cascade-delete its IFsSymFeatVal children and any
              references from IFsClosedValue.FeatureRA.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")

        feat = self.__Unwrap(self.__ResolveObject(feature_or_hvo))
        feature_system = self.project.lp.PhFeatureSystemOA
        if feature_system is not None:
            feature_system.FeaturesOC.Remove(feat)

    # ========================================================================
    # WRITE METHODS - VALUE (IFsSymFeatVal under a feature)
    # ========================================================================

    @OperationsMethod
    def CreateValue(self, feature_or_hvo, name, abbreviation, value_marker=None):
        """
        Create a new symbolic value (IFsSymFeatVal) under a closed feature.

        Args:
            feature_or_hvo: The IFsClosedFeature or HVO that owns the value.
            name (str): Value name (e.g. "positive", "negative").
            abbreviation (str): Short abbreviation. For standard binary
                                phonological features, conventionally
                                "+" or "-".
            value_marker (str, optional): Currently informational only --
                                accepted for API symmetry with FW UIs that
                                ask the user to choose +/-, but the abbreviation
                                itself carries the actual marker. Defaults to
                                None (no constraint).

        Returns:
            IFsSymFeatVal: The newly created value.

        Notes:
            - Applies the Phase 2 ownership-ordering rule: factory.Create()
              -> feature.ValuesOC.Add() -> set Name + Abbreviation.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")
        self._ValidateParam(name, "name")
        self._ValidateParam(abbreviation, "abbreviation")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")
        if not abbreviation or not str(abbreviation).strip():
            raise FP_ParameterError("Abbreviation cannot be empty")

        feature = self.__Unwrap(self.__ResolveObject(feature_or_hvo))
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

            # value_marker is reserved for a future strict-mode check (e.g.
            # enforce that abbreviation == value_marker when both supplied).
            # Phase 5b deliberately leaves it informational only.
            _ = value_marker

            return new_val

    @OperationsMethod
    def DeleteValue(self, value_or_hvo):
        """
        Delete a phonological feature value.

        Removes the value from its owning feature's ValuesOC.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(value_or_hvo, "value_or_hvo")

        val = self.__Unwrap(self.__ResolveObject(value_or_hvo))
        owner = val.Owner
        if owner is not None:
            # ValuesOC is declared on IFsClosedFeature; cast unconditionally so
            # pythonnet surfaces the typed collection accessor. The try/except
            # guards against the unlikely case that owner is some other type
            # (should not happen in practice, but preserves robustness).
            try:
                feat = IFsClosedFeature(owner)
                feat.ValuesOC.Remove(val)
            except Exception:
                pass

    # ========================================================================
    # COMPOSE - FsFeatStruc
    # ========================================================================

    @OperationsMethod
    def MakeFeatStruc(self, specs, owner=None):
        """
        Build an IFsFeatStruc populated with (feature, value) pairs.

        Args:
            specs (list[tuple]): A list of ``(feature, value)`` tuples.
                Each side may be an IFsClosedFeature / IFsSymFeatVal
                object, a wrapper, or an HVO. Items are added to the
                struct's ``FeatureSpecsOC`` in the order provided.

            owner: LCM object that owns the struct via its
                ``FeaturesOA`` atomic-owning property. **Required.**
                The struct is attached to ``owner.FeaturesOA`` BEFORE
                its FeatureSpecsOC is populated, because LCM property
                setters and getters both NPE on free-floating
                IFsFeatStruc objects (Phase 2 ownership rule).
                Phonemes and natural classes both use ``FeaturesOA``.

                ``owner=None`` is rejected unconditionally (issue #28).
                The previous unowned-empty mode returned a struct
                whose property accessors NPE'd inside
                ``CmObject.get_Services()``; that footgun is now gone.

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
                "unusable struct (issue #28). Pass owner=phoneme / "
                "owner=natural_class / owner=context."
            )

        # Normalize and validate specs up front, before any LCM mutation.
        normalized = []
        for i, pair in enumerate(specs):
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise FP_ParameterError(
                    f"specs[{i}] must be a (feature, value) tuple"
                )
            feat_in, val_in = pair
            feat = self.__Unwrap(self.__ResolveObject(feat_in))
            val = self.__Unwrap(self.__ResolveObject(val_in))
            normalized.append((feat, val))

        # Create the struct and attach it to its owner BEFORE any
        # FeatureSpecsOC mutation. Skipping the attach (or doing it
        # after) trips the Phase 2 NPE pattern -- LCM property setters
        # on free-floating structs raise NullReferenceException.
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

    # ========================================================================
    # SYNC INTEGRATION METHODS
    # ========================================================================
    #
    # Symmetric with the 8 Grammar Operations subclasses that support
    # property-level cross-project transfer (GramTrans). Unlike the flat
    # POS / InflectionClass cases, an IFsClosedFeature OWNS its symbolic
    # values (ValuesOC -> IFsSymFeatVal). GetSyncableProperties therefore
    # surfaces each value with its own GUID + Name/Abbreviation/Description
    # so ApplySyncableProperties can co-create them GUID-aligned; a synced
    # feature would otherwise be an empty shell and per-phoneme FeaturesOA
    # specs could not be rewired against it (issue #222).

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project sync.

        Args:
            item: The IFsClosedFeature object, wrapper, or HVO.

        Returns:
            dict: Property names mapped to values. Shapes emitted:

            - ``Name`` / ``Abbreviation`` / ``Description``:
              ``{ws_id: text}`` multistring dicts (non-empty alts only).
            - ``CatalogSourceId``: plain ``str`` provenance tag, when set.
            - ``Values``: a list of dicts, one per owned ``IFsSymFeatVal``,
              each ``{"Guid": str, "Name": {...}, "Abbreviation": {...},
              "Description": {...}}``. The per-value ``Guid`` is preserved
              so a downstream GUID-aligned create rebuilds the value on the
              target side.

        Notes:
            - Does not include the feature's own GUID/HVO (identity is
              managed by the caller / match strategy).
            - Value string reads are guarded so a single malformed alt
              never aborts the whole extraction (issue #222).
        """
        feat = IFsClosedFeature(self.__Unwrap(self.__ResolveObject(item)))
        all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}

        props = {}
        for prop_name in ("Name", "Abbreviation", "Description"):
            ws_values = self.__ReadMultiString(feat, prop_name, all_ws)
            if ws_values:
                props[prop_name] = ws_values

        # CatalogSourceId is a plain-string provenance tag; carry it so the
        # target feature keeps its catalog linkage. The base apply loop
        # handles the str shape via setattr.
        csid = getattr(feat, "CatalogSourceId", None)
        if csid:
            props["CatalogSourceId"] = str(csid)

        # Owned symbolic values. Each carries its own GUID for GUID-aligned
        # co-create on the target side.
        values = []
        for raw in feat.ValuesOC:
            val = IFsSymFeatVal(raw)
            value_dict = {"Guid": str(val.Guid)}
            for prop_name in ("Name", "Abbreviation", "Description"):
                ws_values = self.__ReadMultiString(val, prop_name, all_ws)
                if ws_values:
                    value_dict[prop_name] = ws_values
            values.append(value_dict)
        if values:
            props["Values"] = values

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """
        Apply syncable properties (from GetSyncableProperties) onto a feature.

        Handles the feature's own multistring / CatalogSourceId fields via
        the BaseOperations loop, then co-creates the owned ``Values``
        (IFsSymFeatVal) GUID-aligned so the synced feature is not left an
        empty shell (issue #222).

        Args:
            item: Target IFsClosedFeature (already created + owned +
                GUID-assigned by the caller).
            props: dict produced by GetSyncableProperties.
            ws_map: Optional source->target writing-system Id mapping.
            fill_gaps: If True, only fill empty target alts / add missing
                values; never overwrite existing target data.

        Notes:
            - Value identity is by GUID: an existing value with the same
              GUID is updated in place; a missing one is created with that
              GUID via the IFsSymFeatVal factory (Create(guid, feature),
              falling back to Create(guid)+Add).
            - Must run inside the caller's unit of work (same contract as
              the base implementation, which sets strings without opening
              its own transaction).
        """
        if item is None:
            raise FP_ParameterError("ApplySyncableProperties: item is None")
        if not isinstance(props, dict):
            raise FP_ParameterError(
                f"ApplySyncableProperties: props must be a dict, got "
                f"{type(props).__name__}"
            )

        # Resolve once so an HVO or wrapper input is handled uniformly by the
        # base loop and the value co-create below.
        feature = IFsClosedFeature(self.__Unwrap(self.__ResolveObject(item)))

        # Feature-level scalar/multistring fields via the base loop.
        values = props.get("Values")
        scalar_props = {k: v for k, v in props.items() if k != "Values"}
        super().ApplySyncableProperties(
            feature, scalar_props, ws_map, fill_gaps=fill_gaps
        )

        if values:
            self.__ApplyValues(feature, values, ws_map, fill_gaps)

    def __ApplyValues(self, item, values, ws_map, fill_gaps):
        """
        Co-create / update the IFsSymFeatVal children of a feature from a
        list of value dicts emitted by GetSyncableProperties.
        """
        feature = IFsClosedFeature(self.__Unwrap(self.__ResolveObject(item)))
        existing_by_guid = {
            str(v.Guid).lower(): IFsSymFeatVal(v) for v in feature.ValuesOC
        }

        for value_dict in values:
            if not isinstance(value_dict, dict):
                continue
            guid_str = value_dict.get("Guid")
            val = None
            if guid_str:
                val = existing_by_guid.get(guid_str.lower())
            if val is None:
                val = self.__CreateValueWithGuid(feature, guid_str)
                if guid_str:
                    existing_by_guid[guid_str.lower()] = val

            # Apply the value's own multistrings through the base loop.
            sub_props = {
                k: value_dict[k]
                for k in ("Name", "Abbreviation", "Description")
                if k in value_dict
            }
            if sub_props:
                super().ApplySyncableProperties(
                    val, sub_props, ws_map, fill_gaps=fill_gaps
                )

    def __CreateValueWithGuid(self, feature, guid_str):
        """
        Create an IFsSymFeatVal under ``feature`` preserving ``guid_str``.

        Mirrors the catalog-import value creation (Path A 2-arg factory
        overload, Path B Create(Guid)+Add). Falls back to a random-GUID
        create only if no GUID was supplied or both GUID paths fail, so a
        value is never silently dropped.
        """
        factory = self.project.project.ServiceLocator.GetService(
            IFsSymFeatValFactory
        )

        new_val = None
        if guid_str:
            guid = System.Guid(guid_str)
            # Path A: 2-arg factory overload if pythonnet exposes it.
            try:
                new_val = factory.Create(guid, feature)
            except Exception:
                new_val = None
            if new_val is None:
                # Path B: implementation-side Create(Guid) then Add().
                concrete_factory = (
                    cast_to_concrete(factory)
                    if hasattr(factory, "ClassName")
                    else factory
                )
                try:
                    new_val = concrete_factory.Create(guid)
                    feature.ValuesOC.Add(new_val)
                except Exception:
                    new_val = None

        if new_val is None:
            # Last resort: random GUID (no canonical GUID available or both
            # aligned-create paths failed). Ownership-first as elsewhere.
            new_val = factory.Create()
            feature.ValuesOC.Add(new_val)

        return IFsSymFeatVal(new_val)

    def __ReadMultiString(self, obj, prop_name, all_ws):
        """
        Read a multistring property into a ``{ws_id: text}`` dict, guarding
        each per-WS read so one malformed alt cannot abort extraction.

        Returns None when the property is absent, empty, or not a
        multistring. Feature / value Name/Abbreviation/Description are all
        IMultiUnicode, so the scalar branch is defensive only.
        """
        if not hasattr(obj, prop_name):
            return None
        prop_obj = getattr(obj, prop_name)
        if prop_obj is None:
            return None

        ws_values = {}
        if hasattr(prop_obj, "get_String"):
            for ws_id, ws_handle in all_ws.items():
                try:
                    text = ITsString(prop_obj.get_String(ws_handle)).Text
                except Exception:
                    continue
                if text:
                    ws_values[ws_id] = text
        return ws_values or None

    # ========================================================================
    # CATALOG (eticGlossList) IMPORT METHODS
    # ========================================================================
    #
    # The public API (ImportCatalog / CreateFromCatalog /
    # FixGuidsAgainstCatalog) and the catalog-walking helpers live on
    # CatalogBackedMixin (extracted in Phase 5c). The hooks below tell
    # the mixin how to talk to the PhonFeats-specific LCM types
    # (IFsClosedFeature + its IFsSymFeatVal value children).
    #
    # Phase 2 ownership-ordering lesson applies: the mixin attaches via
    # the 2-arg factory overload (feature placed into FeaturesOC at
    # creation) THEN sets the multistring properties; never sets
    # properties on a free-floating feature.

    # --- CatalogBackedMixin hooks --------------------------------------

    def _get_root_list(self):
        """Return the top-level owner (PhFeatureSystemOA)."""
        return self.project.lp.PhFeatureSystemOA

    def _get_factory(self):
        """Resolve the IFsClosedFeature factory for the mixin's Path B."""
        return self.project.project.ServiceLocator.GetService(
            IFsClosedFeatureFactory
        )

    def _factory_create_attached(self, guid, parent_obj):
        """
        Path A: try the 2-arg factory overload. For features, parent_obj
        is always None (features are flat, owned directly by
        PhFeatureSystemOA.FeaturesOC), so we always pass the feature
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
        PhFeatureSystemOA.FeaturesOC. parent_obj is ignored (always None
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
        Yield each IFsClosedFeature in PhFeatureSystemOA. Features are
        flat (no hierarchy among themselves), so this is a single-level
        walk. Value children are NOT included here -- value idempotency
        is checked per-feature in _handle_entry_children.
        """
        feature_system = self.project.lp.PhFeatureSystemOA
        if feature_system is None:
            return
        for raw in feature_system.FeaturesOC:
            yield IFsClosedFeature(raw)

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
    # parent shape). Keeping it here keeps the mixin simpler.

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

        # Per-WS strings (abbreviation is the +/- marker; term is the
        # positive/negative name).
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
                f"Phonological feature for catalog id {catalogSourceId!r} "
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

    def __ResolveObject(self, obj_or_hvo):
        """
        Resolve HVO or object to its LCM object. Wrappers are passed
        through unchanged here; use __Unwrap() to peel them off if you
        need to call LCM property setters on the result.
        """
        if isinstance(obj_or_hvo, int):
            return self.project.Object(obj_or_hvo)
        return obj_or_hvo

    def __Unwrap(self, obj):
        """
        Peel off LCMObjectWrapper-style wrappers, if any. Plain LCM
        objects pass through. Mirrors the Phase 4 wrapper-aware pattern.
        """
        # Wrapper classes expose ._obj to the underlying LCM object.
        if hasattr(obj, "_obj") and not hasattr(obj, "Hvo"):
            return obj._obj
        if hasattr(obj, "_obj") and hasattr(obj._obj, "Hvo"):
            # Both shapes: wrapper that proxies .Hvo. Prefer the inner LCM obj.
            return obj._obj
        return obj

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to analysis WS.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(
            wsHandle, self.project.project.DefaultAnalWs
        )
