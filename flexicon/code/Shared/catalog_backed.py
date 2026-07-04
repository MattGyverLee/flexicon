#
#   catalog_backed.py
#
#   Module: CatalogBackedMixin
#
#           Shared catalog-import behaviour for Operations classes that wrap
#           LCM possibility-list / feature-system domains backed by a SIL
#           catalog XML file (GOLDEtic, PhonFeatsEticGlossList, etc.).
#
#           Extracted in Phase 5c from the duplicated bodies of
#           POSOperations (Phase 5a) and PhonFeatureOperations (Phase 5b).
#
#           See docs/CATALOG_CONVENTIONS.md for an overview of the prefix
#           policy used by each catalog when writing CatalogSourceId.
#
#           Behaviour is identical to the original per-class implementations:
#               * Idempotent ImportCatalog (skip any entry whose canonical
#                 GUID is already present in the project).
#               * CreateFromCatalog returning the existing object when its
#                 canonical GUID is already present, otherwise creating with
#                 the canonical GUID.
#               * FixGuidsAgainstCatalog walking existing items, looking up
#                 the catalog entry by CatalogSourceId, and replacing the
#                 object via MergeObject when the GUID drifted.
#
#           Subclasses customise per-domain behaviour by setting class-level
#           constants and implementing a small set of hook methods. See the
#           CatalogBackedMixin docstring below for the contract.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

# .NET Guid for catalog-driven creation. The mixin needs System.Guid to
# build the canonical-GUID argument for the factory calls; subclasses
# never need to import it themselves.
import System

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

from .catalog import (
    CatalogImportResult,
    find_catalog_entry,
    find_catalog_file,
)
from ..FLExProject import FP_ParameterError
from ..exceptions import FP_FileNotFoundError
from ..lcm_casting import cast_to_concrete


class CatalogBackedMixin:
    """
    Mixin for Operations classes that wrap LCM possibility-list /
    feature-system domains backed by a SIL catalog XML file (GOLDEtic,
    PhonFeatsEticGlossList, etc.).

    Subclasses declare class-level constants:

        CATALOG_FILE
            Filename of the catalog XML, e.g. "GOLDEtic.xml" or
            "PhonFeatsEticGlossList.xml".

        CATALOG_SUBDIR
            Relative subdirectory under FWCodeDir. Defaults to "Templates"
            in this base; subclasses override for catalogs that live
            elsewhere (e.g. "Language Explorer/MGA/GlossLists").

        CATALOG_PARSER
            Staticmethod returning ``list[CatalogEntry]`` from a file path.
            Either ``parse_etic_catalog`` or ``parse_etic_gloss_list``.

        CATALOG_PREFIX_WRITE
            Either a string (e.g. ``"GOLD"``) or ``None``.
            * String: the mixin writes ``CatalogSourceId = "{PREFIX}:{entry.id}"``.
            * None: the mixin writes ``CatalogSourceId = entry.id`` (the bare
              FW convention used by PhonFeats).

        DOMAIN_LABEL
            Short human-readable label used in error messages, e.g.
            "POS" or "feature".

    Subclasses must also set the optional class flag:

        _supports_recursive_entries (bool, default False)
            True for catalogs whose CatalogEntry tree is hierarchical and
            should produce a parallel hierarchy of LCM objects (POS:
            top-level entries become top-level POSs, nested entries
            become SubPossibilitiesOS). When True, the mixin recurses on
            entry.children calling _create_from_entry(child,
            parent_obj=created_obj).

            False for catalogs whose top-level entries own a flat list of
            children that need bespoke per-domain handling (PhonFeats:
            value children of a feature). When False, the mixin invokes
            ``_handle_entry_children(entry, created_obj, ...)`` once per
            top-level entry; the subclass is responsible for the children.

    Subclasses implement these hook methods:

        _factory_create_attached(self, guid, parent)
            Try the LCM 2-arg factory overload ``Create(Guid, parent)``.
            ``parent`` is whatever was passed to ``_create_from_entry`` -
            either the parent LCM object (subcategory case) or the
            "root list" returned by ``_get_root_list()`` (top-level case).
            Must return either the new LCM object (Path A success) or
            ``None`` (Path A failed; mixin then runs Path B).

        _path_b_attach(self, new_obj, parent_obj)
            Path B fallback: attach ``new_obj`` (just created via
            ``concrete_factory.Create(guid)``) to its owning collection.
            ``parent_obj`` matches the ``parent`` arg passed to the
            top-level _create_from_entry call; if it is None and the
            domain supports subcategories, the subclass attaches to the
            top-level collection on ``_get_root_list()``.
            * POS: ``parent_obj.SubPossibilitiesOS.Add(new_obj)`` if
                   parent_obj is a POS, else
                   ``self.project.lp.PartsOfSpeechOA.PossibilitiesOS.Add(new_obj)``.
            * PhonFeats: ``self._get_root_list().FeaturesOC.Add(new_obj)``.

        _cast_to_domain(self, raw_lcm_obj)
            Return the interface-cast view of the raw LCM object.
            * POS:        ``IPartOfSpeech(raw)``
            * PhonFeats:  ``IFsClosedFeature(raw)``

        _set_localized(self, obj, term, abbrev, def_, missing_ws_seen, warnings)
            Per-domain multistring writes. ``term``, ``abbrev`` and ``def_``
            are ``{ws_tag: text}`` dicts from the CatalogEntry. The
            subclass writes ``obj.Name`` / ``obj.Abbreviation`` /
            ``obj.Description`` (where present) using
            ``_set_multistring`` which the mixin provides.

        _walk_existing(self)
            Yield existing items for idempotency lookup. For domains
            with subcategories (POS), this walks recursively. For flat
            domains (PhonFeats), it yields top-level items.

        _get_root_list(self)
            Return the top-level owner object. POS returns
            ``self.project.lp.PartsOfSpeechOA``; PhonFeats returns
            ``self.project.lp.PhFeatureSystemOA``.

        _handle_entry_children(self, entry, created_obj, missing_ws_seen, warnings, result)
            Per-domain handling of CatalogEntry.children.
            * POS: empty (use ``_supports_recursive_entries=True`` instead).
            * PhonFeats: walk ``entry.children`` (value entries) and
              create IFsSymFeatVal items under ``created_obj.ValuesOC``,
              respecting per-feature value-GUID idempotency.
            ``result`` is the CatalogImportResult (so per-value
            created/skipped counts and created_guids can be updated).
            ``result`` is None when called from CreateFromCatalog or
            FixGuidsAgainstCatalog; subclasses must handle that.

    The mixin provides three public methods (ImportCatalog,
    CreateFromCatalog, FixGuidsAgainstCatalog) plus private helpers
    (_create_from_entry, _get_all_guids, _find_by_guid,
    _set_multistring, _flattened_catalog_count). The public methods are
    plain ``def``s on the mixin; subclasses reach them through normal
    instance dispatch (see the note below for the @OperationsMethod
    convention).

    Why a mixin and not inheritance? The shared behaviour cuts across
    Operations classes that have their own primary inheritance chain
    (BaseOperations); a mixin keeps the catalog-import surface composable
    with that chain without disturbing it.
    """

    # ---- Class-level configuration (subclasses override) ---------------

    CATALOG_FILE = None
    CATALOG_SUBDIR = "Templates"
    CATALOG_PARSER = None
    CATALOG_PREFIX_WRITE = None
    DOMAIN_LABEL = "item"

    # When True the mixin recurses into entry.children as a parallel
    # parent/child hierarchy (POS). When False the mixin delegates each
    # entry's children to _handle_entry_children (PhonFeats).
    _supports_recursive_entries = False

    # ---- Public API ----------------------------------------------------

    # Note: subclasses are expected to also decorate these on the class
    # itself if they want the @OperationsMethod metadata to apply at the
    # subclass level. The decorator on BaseOperations already wraps Class
    # methods; the mixin inherits the same convention by composition.

    def ImportCatalog(self, progress=None):
        """
        Import the configured SIL catalog into this project. Idempotent.

        Each catalog entry is matched against existing items by its
        canonical GUID. Entries whose GUID already exists are skipped.
        New entries are created with the canonical GUID + per-WS
        localized name/abbreviation/description, and a CatalogSourceId
        tag for later FixGuidsAgainstCatalog() repair.

        Args:
            progress: Optional callable accepting (count, total, name)
                      for progress reporting. May be None.

        Returns:
            CatalogImportResult: Created/skipped counts, list of created
            GUIDs, and any human-readable warnings raised during import.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FileNotFoundError: If the catalog file is not found under FWCodeDir.
            FP_ParameterError: For domain-specific preconditions (e.g. missing
                PhFeatureSystemOA on the project).
        """
        self._EnsureWriteEnabled()

        path = find_catalog_file(self.CATALOG_FILE, subdir=self.CATALOG_SUBDIR)
        entries = self._invoke_parser(path)

        # Validate that the domain root list exists before doing any work.
        # PhonFeats raises here when PhFeatureSystemOA is missing; POS's
        # PartsOfSpeechOA is always present so this is effectively a no-op
        # for POS.
        root = self._get_root_list()
        if root is None:
            raise FP_ParameterError(
                f"Project has no {self.DOMAIN_LABEL} root list; "
                f"cannot import catalog."
            )

        existing_guids = self._get_all_guids()

        result = CatalogImportResult()
        missing_ws_seen = set()

        total = self._flattened_catalog_count(entries)

        def _import_one(entry, parent_obj):
            guid_str = entry.guid.lower() if entry.guid else ""
            existing = existing_guids.get(guid_str)
            if existing is not None:
                result.skipped_count += 1
                obj = existing
            else:
                obj = self._create_from_entry(
                    entry, parent_obj, missing_ws_seen, result.warnings
                )
                result.created_count += 1
                result.created_guids.append(guid_str)
                existing_guids[guid_str] = obj

            if progress:
                try:
                    progress(
                        result.created_count + result.skipped_count,
                        total,
                        entry.id,
                    )
                except Exception:
                    # Progress callbacks must never break the import.
                    pass

            # Per-domain children handling.
            if self._supports_recursive_entries:
                # Hierarchical: recurse with `obj` as the new parent.
                for child in entry.children:
                    _import_one(child, obj)
            else:
                # Flat-with-children: delegate to subclass.
                self._handle_entry_children(
                    entry, obj, missing_ws_seen, result.warnings, result
                )
                # Update progress for the children handled.
                if progress:
                    try:
                        progress(
                            result.created_count + result.skipped_count,
                            total,
                            entry.id,
                        )
                    except Exception:
                        pass

        for top in entries:
            _import_one(top, None)

        return result

    def CreateFromCatalog(self, source_id, parent=None):
        """
        Create a single item from the configured catalog using the
        canonical GUID and all localized data available for the WSes the
        project has.

        Idempotent: if an item with the catalog's canonical GUID already
        exists in the project, that existing item is returned unchanged.

        Args:
            source_id (str): Catalog id, with or without a known catalog
                prefix (``"GOLD:"``, ``"PHON:"``). e.g. ``"GOLD:Adjective"``
                or ``"Adjective"``; ``"PHON:fPAConsonantal"`` or
                ``"fPAConsonantal"``.
            parent: Optional LCM object to attach the new item under. For
                hierarchical domains (POS), this becomes the parent POS.
                For flat domains (PhonFeats), this is ignored.

        Returns:
            The created (or pre-existing) LCM object, cast via
            _cast_to_domain.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_ParameterError: If source_id is not present in the catalog,
                               or for domain-specific preconditions.
            FileNotFoundError: If the catalog is not found under FWCodeDir.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(source_id, "source_id")

        path = find_catalog_file(self.CATALOG_FILE, subdir=self.CATALOG_SUBDIR)
        entries = self._invoke_parser(path)
        entry = find_catalog_entry(entries, source_id)
        if entry is None:
            raise FP_ParameterError(
                f"Catalog id '{source_id}' not found in {self.CATALOG_FILE}"
            )

        root = self._get_root_list()
        if root is None:
            raise FP_ParameterError(
                f"Project has no {self.DOMAIN_LABEL} root list; "
                f"cannot import catalog."
            )

        # Idempotency: if the canonical GUID is already present, return it
        # (and still create any missing children via _handle_entry_children).
        existing = self._find_by_guid(entry.guid)

        warnings = []
        missing_ws_seen = set()

        if existing is not None:
            obj = existing
        else:
            obj = self._create_from_entry(
                entry, parent, missing_ws_seen, warnings
            )

        # For flat-with-children domains, ensure value children are
        # present even when the parent feature was already there.
        if not self._supports_recursive_entries:
            self._handle_entry_children(
                entry, obj, missing_ws_seen, warnings, None
            )

        return obj

    def FixGuidsAgainstCatalog(self):
        """
        Scan items in this project; for any whose CatalogSourceId matches
        a catalog entry but whose GUID differs from the catalog's
        canonical GUID, create a replacement with the correct GUID,
        transfer references via MergeObject, and remove the old item.

        Returns:
            list[tuple]: One ``(old_name, old_guid, new_guid)`` tuple per
            item repaired. Empty list if everything is already canonical.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_ParameterError: If MergeObject fails for any candidate
                (silently removing the old item would orphan incoming
                references, so we re-raise the LCM error).
        """
        self._EnsureWriteEnabled()

        path = find_catalog_file(self.CATALOG_FILE, subdir=self.CATALOG_SUBDIR)
        entries = self._invoke_parser(path)

        root = self._get_root_list()
        if root is None:
            return []

        fixed = []
        # Collect candidates first; iterating + mutating the same
        # collection during merge would be unsafe.
        candidates = []
        for existing in self._walk_existing():
            # _walk_existing yields either (obj, parent) tuples (POS) or
            # bare objs (PhonFeats); normalise to obj.
            obj, parent_obj = self._normalise_walk_item(existing)

            cat_id = obj.CatalogSourceId or ""
            if not cat_id:
                continue
            entry = find_catalog_entry(entries, cat_id)
            if entry is None:
                continue
            current_guid = str(obj.Guid).lower()
            canonical_guid = entry.guid.lower()
            if current_guid == canonical_guid:
                continue
            candidates.append((obj, parent_obj, entry))

        for old_obj, parent_obj, entry in candidates:
            wsHandle = self.project.project.DefaultAnalWs
            old_name = ITsString(old_obj.Name.get_String(wsHandle)).Text or "(unnamed)"
            old_guid = str(old_obj.Guid).lower()

            warnings = []
            missing_ws = set()
            new_obj = self._create_from_entry(
                entry, parent_obj, missing_ws, warnings
            )

            # For flat-with-children: also recreate value children with
            # canonical GUIDs under the replacement feature.
            if not self._supports_recursive_entries:
                self._handle_entry_children(
                    entry, new_obj, missing_ws, warnings, None
                )

            try:
                old_obj.MergeObject(new_obj, True)
            except Exception as e:
                # MergeObject failure indicates a genuine LCM error
                # (transaction conflict, reference inconsistency, etc.).
                # Silently removing old_obj would orphan incoming
                # references; re-raise so the caller sees the real problem.
                raise FP_ParameterError(
                    f"Failed to merge {self.DOMAIN_LABEL} '{old_name}' into "
                    f"canonical-GUID replacement (entry '{entry.id}'): {e}"
                ) from e

            fixed.append((old_name, old_guid, entry.guid.lower()))

        return fixed

    # ---- Mixin-private helpers ----------------------------------------

    def _invoke_parser(self, path):
        """
        Invoke the configured catalog parser. CATALOG_PARSER is declared
        as a staticmethod on the subclass; accessing it via the
        descriptor protocol resolves to the underlying function so we
        can call it with a single argument.
        """
        # Class-level CATALOG_PARSER is a staticmethod descriptor; access
        # through the class to get the unwrapped callable.
        parser = type(self).CATALOG_PARSER
        return parser(path)

    def _create_from_entry(self, entry, parent_obj, missing_ws_seen, warnings):
        """
        Internal: instantiate one LCM object from a CatalogEntry, attach
        to the correct owner with the canonical GUID, then set per-WS
        Name / Abbreviation / Description and CatalogSourceId.

        Applies the Phase 2 ownership-ordering rule: attach first (via
        the 2-arg factory overload, or fall back to Create+Add), then
        mutate properties.
        """
        guid = System.Guid(entry.guid)

        # Path A: explicit 2-arg interface overload. The subclass owns
        # the factory + the choice of "parent" argument shape (root list
        # vs subcategory parent). Returns None on failure.
        new_obj = self._factory_create_attached(guid, parent_obj)

        if new_obj is None:
            # Path B: implementation-side Create(Guid) + explicit Add().
            # cast_to_concrete defends against interface-only views that
            # hide Create(Guid).
            factory = self._get_factory()
            concrete_factory = (
                cast_to_concrete(factory) if hasattr(factory, "ClassName") else factory
            )
            try:
                new_obj = concrete_factory.Create(guid)
            except Exception as e:
                # No safe fallback: parameterless Create() would generate
                # a random GUID, defeating the entire point of
                # CreateFromCatalog. Fail loudly rather than silently
                # degrade (Phase 5a discipline).
                raise FP_ParameterError(
                    f"Could not create {self.DOMAIN_LABEL} '{entry.id}' with "
                    f"canonical GUID {entry.guid} via either Create(Guid, owner) "
                    f"or Create(Guid) factory overloads. The catalog's canonical "
                    f"GUID cannot be applied in this LCM version; a manual "
                    f"factory.Create() workaround would produce a random GUID "
                    f"and is not acceptable here."
                ) from e

            self._path_b_attach(new_obj, parent_obj)

        # Cast to the domain interface so the subclass's _set_localized
        # sees the right view.
        new_obj = self._cast_to_domain(new_obj)

        # Per-WS multistring properties.
        self._set_localized(
            new_obj, entry.term, entry.abbrev, entry.def_,
            missing_ws_seen, warnings,
        )

        # CatalogSourceId tagging policy: prefixed or bare per subclass.
        if self.CATALOG_PREFIX_WRITE is None:
            new_obj.CatalogSourceId = entry.id
        else:
            new_obj.CatalogSourceId = f"{self.CATALOG_PREFIX_WRITE}:{entry.id}"

        return new_obj

    def _get_factory(self):
        """
        Resolve the LCM factory used by Path B. Subclasses override or
        rely on the default: look up the same factory the subclass
        already configures _factory_create_attached against.

        Default impl raises; subclasses MUST override.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement _get_factory() "
            f"for the Path B fallback."
        )

    def _set_multistring(self, multistring, ws_to_text, missing_ws_seen, warnings):
        """
        Apply a {ws_tag: text} dict to an LCM multistring, mapping ws_tag
        to handle via project.WSHandle(). Missing handles are skipped;
        a warning is recorded once per missing tag.

        This is the truly-identical body extracted from
        _SetPosMultiString / _SetFsMultiString. Subclasses use it from
        their _set_localized implementations.
        """
        for ws_tag, text in ws_to_text.items():
            handle = self.project.WSHandle(ws_tag)
            if handle is None:
                if ws_tag not in missing_ws_seen:
                    missing_ws_seen.add(ws_tag)
                    warnings.append(
                        f"Skipping catalog WS '{ws_tag}': "
                        "no matching writing system in project."
                    )
                continue
            tss = TsStringUtils.MakeString(text, handle)
            multistring.set_String(handle, tss)

    def _get_all_guids(self):
        """
        Build a dict mapping lowercased GUID string -> existing LCM object
        for every top-level item in the domain. For hierarchical domains
        (POS) _walk_existing recurses; for flat domains (PhonFeats) it
        yields top-level items only.
        """
        guids = {}
        for existing in self._walk_existing():
            obj, _parent = self._normalise_walk_item(existing)
            guids[str(obj.Guid).lower()] = obj
        return guids

    def _find_by_guid(self, guid_str):
        """Return the item whose GUID matches `guid_str`, or None."""
        target = guid_str.lower() if guid_str else ""
        if not target:
            return None
        for existing in self._walk_existing():
            obj, _parent = self._normalise_walk_item(existing)
            if str(obj.Guid).lower() == target:
                return obj
        return None

    def _normalise_walk_item(self, item):
        """
        _walk_existing may yield either (obj, parent) tuples (POS,
        which needs the parent to preserve hierarchy in repair) or
        bare LCM objects (PhonFeats, which is flat). Normalise to
        (obj, parent_or_None) so the rest of the mixin can be uniform.
        """
        if isinstance(item, tuple) and len(item) == 2:
            return item
        return (item, None)

    def _flattened_catalog_count(self, entries):
        """Total catalog entries across the forest, including children."""
        n = 0
        for e in entries:
            n += 1 + self._flattened_catalog_count(e.children)
        return n


class _LCMNativeCatalogImportMixin:
    """
    Mixin for Operations classes that wrap LCM possibility-list domains
    whose catalog ships as LCM-native XML (``<LangProject>...<CmPossibilityList>``
    with canonical-GUID children) rather than as an etic CatalogEntry feed.

    Subclasses delegate the heavy lifting to
    ``SIL.LCModel.Application.ApplicationServices.XmlList.ImportList(lp,
    fieldName, path, progress)`` -- LCM's native import path -- and only
    add a non-empty-list guard around it. ``XmlList.ImportList`` APPENDS
    without GUID-based deduplication, so calling it on a non-empty list
    silently duplicates the canonical hierarchy. The guard refuses by
    default and surfaces an FP_ParameterError; callers pass
    ``force=True`` to opt in.

    Extracted in Phase Q-3a from the duplicated bodies of
    SemanticDomainOperations.ImportCatalog (SemDom.xml) and
    AnthropologyOperations.ImportCatalog (OCM.xml). Both methods are
    near-identical 80-100-line wrappers around the same LCM call; the
    only variation is the catalog file, the LCM fieldName argument, the
    LangProject OA-property holding the target list, and the singular /
    plural item label used in the guard's error message.

    Subclasses declare class-level constants:

        CATALOG_FILE
            Filename of the LCM-native catalog XML, e.g. ``"SemDom.xml"``
            or ``"OCM.xml"``.

        CATALOG_SUBDIR
            Relative subdirectory under FWCodeDir. Defaults to
            ``"Templates"`` to match both existing catalogs.

        LCM_FIELD_NAME
            The second argument to
            ``XmlList.ImportList(lp, fieldName, path, progress)`` -- LCM's
            internal name for the LangProject possibility list this
            catalog feeds. E.g. ``"SemanticDomainList"`` or ``"AnthroList"``.

        LANG_PROJECT_LIST_ATTR
            Name of the OA property on ``project.lp`` that holds the
            target list, e.g. ``"SemanticDomainListOA"`` or
            ``"AnthroListOA"``. Used both for the non-empty guard and
            for the post-import count returned to the caller.

        DOMAIN_ITEM_LABEL_SINGULAR
            Singular form of the item label used in the guard's error
            message, e.g. ``"domain"`` or ``"anthropology item"``. Shows
            up in ``"top-level {SINGULAR}(s)"``.

        DOMAIN_ITEM_LABEL_PLURAL
            Plural form used in the "additional X on top" continuation
            of the same error, e.g. ``"domains"`` or ``"items"``. Note
            this is the label appearing in the second clause and need
            not be the strict morphological plural of
            DOMAIN_ITEM_LABEL_SINGULAR -- it matches each catalog's
            historical wording so the message stays byte-identical to
            the pre-extraction implementations.

    The mixin exposes one helper, ``_import_lcm_native_catalog``, which
    each subclass's thin ``ImportCatalog`` wrapper delegates to. The
    public method stays on the subclass (with its full docstring and
    @OperationsMethod decorator) so that
    ``Operations.__dict__["ImportCatalog"]`` introspection in the test
    suite continues to find it on the class itself, not only via MRO
    lookup.

    Why a mixin and not pure inheritance? The shared behaviour cuts
    across Operations classes whose primary inheritance is
    ``BaseOperations``; a mixin keeps the LCM-native import surface
    composable with that chain. Why a private helper rather than an
    inherited ImportCatalog? Existing tests use
    ``cls.__dict__["ImportCatalog"]`` to inspect the @OperationsMethod
    descriptor and would break under MRO-only resolution.

    Sibling-catalog importers:
        A subclass that ships multiple catalogs feeding the same target
        list (e.g. ``AnthropologyOperations`` with both ``OCM.xml`` and
        ``OCM-Frame.xml``) can expose additional public ``Import*``
        methods that route through ``_import_lcm_native_catalog`` with
        the ``catalog_file=`` runtime override (rather than overriding
        the class-level ``CATALOG_FILE`` constant). The
        ``ImportFrameCatalog`` method on AnthropologyOperations is the
        established precedent. (issue #83)
    """

    # ---- Class-level configuration (subclasses override) ---------------

    CATALOG_FILE = None
    CATALOG_SUBDIR = "Templates"
    LCM_FIELD_NAME = None
    LANG_PROJECT_LIST_ATTR = None
    DOMAIN_ITEM_LABEL_SINGULAR = "item"
    DOMAIN_ITEM_LABEL_PLURAL = "items"

    # ---- Mixin-private helper -----------------------------------------

    def _import_lcm_native_catalog(
        self, progress=None, force=False, catalog_file=None
    ):
        """
        Delegate to LCM's native XmlList.ImportList after the non-empty
        guard. Subclasses' ImportCatalog methods call this verbatim;
        their docstrings (which describe the catalog's contents and
        idempotency contract) stay on the subclass method.

        LOCAL imports: SIL.LCModel and the catalog-locator both live
        behind FieldWorks-only dependencies; importing at module top
        would break test collection on machines without FW installed.
        Both pre-extraction implementations imported locally too -- the
        pattern is preserved here.

        Args:
            progress: Optional ``SIL.LCModel.Utils.IProgress`` instance.
            force: If True, skip the non-empty guard.
            catalog_file: Optional override for ``self.CATALOG_FILE``.
                Used by sibling-catalog import methods (e.g.
                ``ImportFrameCatalog`` on AnthropologyOperations, which
                points at ``OCM-Frame.xml`` instead of the main
                ``OCM.xml``). When None (default), the subclass's
                class-level ``CATALOG_FILE`` constant is used.

        Returns:
            int: Count of top-level items in the target list after import.

        Raises:
            FP_ReadOnlyError: If the project is not write-enabled.
            FP_FileNotFoundError: If the catalog file cannot be located.
            FP_ParameterError: If the target list is already non-empty
                               and ``force`` is False.
        """
        # LOCAL import: XmlList is the only FieldWorks-dependent symbol
        # used here, and SIL.LCModel.Application.ApplicationServices is
        # only available when FieldWorks is installed. find_catalog_file
        # (pure flexlibs2) and FP_FileNotFoundError (pure flexlibs2) are
        # hoisted to module top -- they don't need deferred loading.
        # (issue #119 item 2)
        from SIL.LCModel.Application.ApplicationServices import XmlList

        self._EnsureWriteEnabled()

        # Explicit None-check rather than truthy fallback so an empty
        # string passed by mistake fails loudly via find_catalog_file
        # rather than silently degrading to the class-level default.
        # (issue #83 item 2)
        effective_catalog = catalog_file if catalog_file is not None else self.CATALOG_FILE

        target_list = getattr(self.project.lp, self.LANG_PROJECT_LIST_ATTR)
        existing = target_list.PossibilitiesOS.Count
        if existing > 0 and not force:
            # Name the specific catalog in the message so a sibling
            # caller (ImportFrameCatalog at effective_catalog='OCM-Frame.xml')
            # self-identifies in error logs instead of saying generic
            # "this". (issue #83 item 3)
            raise FP_ParameterError(
                f"{self.LANG_PROJECT_LIST_ATTR} already has {existing} "
                f"top-level {self.DOMAIN_ITEM_LABEL_SINGULAR}(s). "
                f"XmlList.ImportList APPENDS without GUID-based "
                f"deduplication, so importing {effective_catalog!r} "
                f"here would create duplicates. Pass force=True if "
                f"you intend to layer additional "
                f"{self.DOMAIN_ITEM_LABEL_PLURAL} on top, or clear "
                f"the list first."
            )

        try:
            catalog_path = find_catalog_file(
                effective_catalog, subdir=self.CATALOG_SUBDIR
            )
        except FileNotFoundError as e:
            raise FP_FileNotFoundError(effective_catalog, e)

        importer = XmlList()
        # LCM_FIELD_NAME maps to LangProject.<LANG_PROJECT_LIST_ATTR>.
        # progress=None is accepted (IProgress is a reference interface).
        importer.ImportList(
            self.project.lp,
            self.LCM_FIELD_NAME,
            catalog_path,
            progress,
        )

        return getattr(
            self.project.lp, self.LANG_PROJECT_LIST_ATTR
        ).PossibilitiesOS.Count
