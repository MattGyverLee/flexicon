#
#   test_inflection_features.py
#
#   Class: TestInflectionFeaturesCatalog
#          Phase 6a live-LCM integration tests for InflectionFeatureOperations'
#          catalog-backed import (issue #14 — partial). Exercises
#          CreateFromCatalog against the FW-shipped MGA EticGlossList.xml
#          catalog, confirming canonical-GUID feature + value creation,
#          prefix handling, idempotency, parser type-filtering, and — most
#          importantly — that inflection features land under
#          MsFeatureSystemOA (NOT PhFeatureSystemOA, which is the
#          phonological feature system from Phase 5b).
#
#          Mirrors the writable-project fixture pattern used by
#          tests/operations/test_phon_features.py and test_pos_catalog.py.
#          Created features and their values are tracked and removed in
#          finally blocks (cascade-delete: removing the feature from
#          FeaturesOC cascades its IFsSymFeatVal value children).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# Every test in this module opens a real .fwdata project via the
# writable_project fixture.
pytestmark = pytest.mark.requires_live_project


# ---------------------------------------------------------------------------
# Live-LCM project fixture
# ---------------------------------------------------------------------------

_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_writable_project():
    """Open one of the standard test projects in write mode, or None."""
    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception:
        return None

    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=True)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    """
    Module-scoped write-enabled FLExProject fixture. Skips dependent
    tests if SIL.LCModel isn't loaded or no candidate project can be
    opened in write mode.
    """
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")

    project = _try_open_writable_project()
    if project is None:
        pytest.skip(
            "No writable FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )

    yield project

    try:
        project.CloseProject()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Constants — canonical GUIDs from EticGlossList.xml (the morphosyntactic
# / inflection feature catalog under FW's Language Explorer/MGA/GlossLists).
# ---------------------------------------------------------------------------

# fDeg feature + its four value children (positive, comparative,
# superlative, unknown degree). GUIDs verified against the shipped FW9
# EticGlossList.xml.
DEGREE_FEATURE_GUID = "b2646044-b47e-46d7-8dd3-d57c079e7b5f"
DEGREE_POSITIVE_VALUE_GUID = "a2c5215b-86f7-4851-ac71-ab04c47137cf"
DEGREE_COMPARATIVE_VALUE_GUID = "05c3dd95-8ec3-4b13-bd18-734705b00cf7"
DEGREE_SUPERLATIVE_VALUE_GUID = "cc1dcb22-77fb-4709-8171-828646b697f0"
DEGREE_UNKNOWN_VALUE_GUID = "a927ac6f-fda6-45a6-8eed-ff9f8306259d"

DEGREE_VALUE_GUIDS = {
    DEGREE_POSITIVE_VALUE_GUID,
    DEGREE_COMPARATIVE_VALUE_GUID,
    DEGREE_SUPERLATIVE_VALUE_GUID,
    DEGREE_UNKNOWN_VALUE_GUID,
}


# ---------------------------------------------------------------------------
# Cleanup helpers
# ---------------------------------------------------------------------------


def _find_msfeat_by_guid(project, guid_str):
    """
    Walk MsFeatureSystemOA.FeaturesOC and return the IFsClosedFeature
    whose GUID matches `guid_str` (case-insensitive), or None.
    """
    from SIL.LCModel import IFsClosedFeature

    target = guid_str.lower()
    fs = project.lp.MsFeatureSystemOA
    if fs is None:
        return None
    for raw in fs.FeaturesOC:
        try:
            feat = IFsClosedFeature(raw)
        except Exception:
            continue
        if str(feat.Guid).lower() == target:
            return feat
    return None


def _find_phonfeat_by_guid(project, guid_str):
    """
    Walk PhFeatureSystemOA.FeaturesOC for a feature with `guid_str`.
    Used by the cross-system separation test to confirm inflection
    features did NOT accidentally land in the phonological system.
    """
    from SIL.LCModel import IFsClosedFeature

    target = guid_str.lower()
    fs = project.lp.PhFeatureSystemOA
    if fs is None:
        return None
    for raw in fs.FeaturesOC:
        try:
            feat = IFsClosedFeature(raw)
        except Exception:
            continue
        if str(feat.Guid).lower() == target:
            return feat
    return None


def _delete_msfeat_by_guid(project, guid_str):
    """
    Best-effort cleanup: remove a feature (and cascade its values) from
    MsFeatureSystemOA.FeaturesOC. Safe to call on missing/already-deleted.
    Value children cascade via the OC (owning collection) removal.
    """
    if not guid_str:
        return
    try:
        feat = _find_msfeat_by_guid(project, guid_str)
        if feat is None:
            return
        fs = project.lp.MsFeatureSystemOA
        if fs is not None:
            # Raw LCM write -> own unit of work (tasks.md D14).
            with project.UndoableOperation("test cleanup: delete ms feature"):
                fs.FeaturesOC.Remove(feat)
    except Exception:
        # Cleanup must never raise; if it failed, leave traces.
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInflectionFeaturesCatalog:
    """
    Live-LCM coverage for InflectionFeatureOperations.CreateFromCatalog
    against the EticGlossList.xml MGA catalog, plus a defensive check
    that closed-feature import targets MsFeatureSystemOA and never
    PhFeatureSystemOA.
    """

    def test_create_from_catalog_uses_canonical_guid(self, writable_project):
        """
        CreateFromCatalog('fDeg') must produce a feature with the
        canonical degree-feature GUID, name 'degree', and abbrev 'deg'.
        If GUID drifts, either Path A (factory 2-arg overload) or Path B
        (parameterless create + canonical-attach) silently fell back to
        a random GUID and the test should fail loudly.
        """
        pre_existing = (
            _find_msfeat_by_guid(writable_project, DEGREE_FEATURE_GUID)
            is not None
        )
        created_guid = None
        try:
            feat = writable_project.InflectionFeatures.CreateFromCatalog(
                "fDeg"
            )
            assert feat is not None, "CreateFromCatalog returned None"

            actual_guid = str(feat.Guid).lower()
            assert actual_guid == DEGREE_FEATURE_GUID, (
                f"Feature GUID {actual_guid!r} != canonical "
                f"{DEGREE_FEATURE_GUID!r}. Factory paths A/B may have "
                "fallen back to a random GUID."
            )
            if not pre_existing:
                created_guid = DEGREE_FEATURE_GUID

            # Localized strings: name='degree', abbrev='deg'.
            en_handle = writable_project.WSHandle("en")
            if en_handle is not None:
                from SIL.LCModel.Core.KernelInterfaces import ITsString

                name_en = ITsString(feat.Name.get_String(en_handle)).Text
                abbr_en = ITsString(
                    feat.Abbreviation.get_String(en_handle)
                ).Text
                assert name_en == "degree", (
                    f"Name['en'] = {name_en!r}, expected 'degree'"
                )
                assert abbr_en == "deg", (
                    f"Abbreviation['en'] = {abbr_en!r}, expected 'deg'"
                )
        finally:
            if created_guid is not None:
                _delete_msfeat_by_guid(writable_project, created_guid)

    def test_create_from_catalog_imports_values(self, writable_project):
        """
        CreateFromCatalog('fDeg') must populate ValuesOC with the FOUR
        canonical value children (positive, comparative, superlative,
        unknown). All four canonical value GUIDs must be present.
        """
        from SIL.LCModel import IFsSymFeatVal

        pre_existing = (
            _find_msfeat_by_guid(writable_project, DEGREE_FEATURE_GUID)
            is not None
        )
        created_guid = None
        try:
            feat = writable_project.InflectionFeatures.CreateFromCatalog(
                "fDeg"
            )
            if not pre_existing:
                created_guid = DEGREE_FEATURE_GUID

            assert feat.ValuesOC.Count == 4, (
                f"Expected 4 values under fDeg, got {feat.ValuesOC.Count}"
            )
            value_guids = {
                str(IFsSymFeatVal(v).Guid).lower() for v in feat.ValuesOC
            }
            missing = DEGREE_VALUE_GUIDS - value_guids
            assert not missing, (
                f"Missing canonical value GUIDs: {sorted(missing)}; "
                f"got: {sorted(value_guids)}"
            )
            # Spot-check the positive value's name.
            for raw in feat.ValuesOC:
                v = IFsSymFeatVal(raw)
                if str(v.Guid).lower() == DEGREE_POSITIVE_VALUE_GUID:
                    en_handle = writable_project.WSHandle("en")
                    if en_handle is not None:
                        from SIL.LCModel.Core.KernelInterfaces import (
                            ITsString,
                        )

                        name_en = ITsString(
                            v.Name.get_String(en_handle)
                        ).Text
                        assert name_en == "positive", (
                            f"Positive value name = {name_en!r}, "
                            "expected 'positive'"
                        )
                    break
        finally:
            if created_guid is not None:
                _delete_msfeat_by_guid(writable_project, created_guid)

    def test_create_from_catalog_accepts_infl_prefix(self, writable_project):
        """
        CreateFromCatalog('INFL:fDeg') must behave identically to the
        bare-id form: produce the same canonical feature GUID. The
        InflectionFeatureOperations docstring advertises 'INFL:' as a
        user-facing convenience prefix — if it isn't honoured by the
        shared catalog prefix-stripper, the call will raise
        FP_ParameterError ('catalog id not found').
        """
        pre_existing = (
            _find_msfeat_by_guid(writable_project, DEGREE_FEATURE_GUID)
            is not None
        )
        created_guid = None
        try:
            feat = writable_project.InflectionFeatures.CreateFromCatalog(
                "INFL:fDeg"
            )
            assert feat is not None
            assert str(feat.Guid).lower() == DEGREE_FEATURE_GUID, (
                "INFL:-prefixed form produced different GUID from bare form"
            )
            if not pre_existing:
                created_guid = DEGREE_FEATURE_GUID
        finally:
            if created_guid is not None:
                _delete_msfeat_by_guid(writable_project, created_guid)

    def test_create_from_catalog_idempotent(self, writable_project):
        """
        A second CreateFromCatalog('fDeg') must return the existing
        feature (canonical-GUID match) and must NOT duplicate the value
        children — count stays at exactly 4 and only ONE feature with
        the canonical GUID exists in MsFeatureSystemOA.
        """
        from SIL.LCModel import IFsClosedFeature

        pre_existing = (
            _find_msfeat_by_guid(writable_project, DEGREE_FEATURE_GUID)
            is not None
        )
        created_guid = None
        try:
            first = writable_project.InflectionFeatures.CreateFromCatalog(
                "fDeg"
            )
            if not pre_existing:
                created_guid = DEGREE_FEATURE_GUID

            second = writable_project.InflectionFeatures.CreateFromCatalog(
                "fDeg"
            )
            assert second is not None
            assert str(first.Guid).lower() == str(second.Guid).lower(), (
                "Idempotency violated: second CreateFromCatalog returned "
                "a different feature object"
            )
            assert second.ValuesOC.Count == 4, (
                f"Idempotency violated: value count drifted to "
                f"{second.ValuesOC.Count} after second call"
            )

            # Exactly one feature with this canonical GUID in the system.
            matches = 0
            for raw in writable_project.lp.MsFeatureSystemOA.FeaturesOC:
                try:
                    f = IFsClosedFeature(raw)
                except Exception:
                    continue
                if str(f.Guid).lower() == DEGREE_FEATURE_GUID:
                    matches += 1
            assert matches == 1, (
                f"Expected exactly one fDeg feature, found {matches}"
            )
        finally:
            if created_guid is not None:
                _delete_msfeat_by_guid(writable_project, created_guid)

    def test_get_constraints_skips_complex_feature_types(self):
        """
        parse_etic_gloss_list must return ONLY type='feature' entries
        (closed/symbolic features). The shipped EticGlossList.xml also
        contains type='complex' and type='fsType' items; the Phase 6a
        MVP defers their import, and the parser silently filters them.
        We verify here at the parser level (no live LCM required).
        """
        try:
            from flexlibs2.code import FLExGlobals
            from flexlibs2.code.Shared.catalog import (
                find_catalog_file,
                parse_etic_gloss_list,
            )
        except Exception:
            pytest.skip("flexlibs2 catalog helpers unavailable")

        if not FLExGlobals.FWCodeDir:
            pytest.skip("FWCodeDir not set (FieldWorks not detected)")

        try:
            path = find_catalog_file(
                "EticGlossList.xml", "Language Explorer/MGA/GlossLists"
            )
        except FileNotFoundError:
            pytest.skip("EticGlossList.xml not installed")

        entries = parse_etic_gloss_list(path)
        assert len(entries) > 0, (
            "parse_etic_gloss_list returned zero entries; the catalog "
            "should contain at least the standard inflection features."
        )

        # All returned entries must have value-typed children (or be
        # leaf features with no children at all). They must NOT contain
        # nested 'feature' entries (that would imply complex/fsType
        # leaked through). The parser is what gives us this guarantee:
        # _parse_gloss_item only recurses into expected_type='value'
        # children of feature items.
        import xml.etree.ElementTree as ET

        tree = ET.parse(path)
        root = tree.getroot()

        # Total feature count in raw XML at any depth (used as upper bound).
        raw_feature_ids = set()

        def _walk_features(elem):
            for item in elem.findall("item"):
                if item.get("type") == "feature":
                    raw_feature_ids.add(item.get("id") or "")
                _walk_features(item)

        _walk_features(root)

        parsed_ids = {e.id for e in entries}
        # Every parsed entry id must correspond to a type='feature' in
        # the raw XML (no complex/fsType bleed-through).
        leaked = parsed_ids - raw_feature_ids
        assert not leaked, (
            f"parse_etic_gloss_list returned non-feature entries: {leaked}"
        )

        # And complex/fsType ids must NOT be in the parsed set.
        complex_ids = set()
        fstype_ids = set()

        def _walk_complex(elem):
            for item in elem.findall("item"):
                t = item.get("type")
                if t == "complex":
                    complex_ids.add(item.get("id") or "")
                elif t == "fsType":
                    fstype_ids.add(item.get("id") or "")
                _walk_complex(item)

        _walk_complex(root)

        assert not (parsed_ids & complex_ids), (
            f"Complex-feature ids leaked into parsed output: "
            f"{parsed_ids & complex_ids}"
        )
        assert not (parsed_ids & fstype_ids), (
            f"fsType ids leaked into parsed output: "
            f"{parsed_ids & fstype_ids}"
        )

    def test_inflection_features_use_ms_feature_system(self, writable_project):
        """
        CRITICAL cross-system separation test: a feature created via
        InflectionFeatureOperations.CreateFromCatalog must appear in
        MsFeatureSystemOA.FeaturesOC and must NOT appear in
        PhFeatureSystemOA.FeaturesOC. Phase 5b (PhonFeats) and Phase 6a
        (InflFeats) operate on the same eticGlossList shape; an
        owner-mixup would route inflection imports into the phonological
        feature system, corrupting the project's morphosyntax. This is
        the most important regression to catch early.
        """
        pre_existing_ms = (
            _find_msfeat_by_guid(writable_project, DEGREE_FEATURE_GUID)
            is not None
        )
        pre_existing_ph = (
            _find_phonfeat_by_guid(writable_project, DEGREE_FEATURE_GUID)
            is not None
        )
        # If the canonical GUID already exists in PhFeatureSystemOA
        # before we even touch it, that's a pre-existing project quirk
        # unrelated to this test; record but don't blame Phase 6a.
        created_guid = None
        try:
            feat = writable_project.InflectionFeatures.CreateFromCatalog(
                "fDeg"
            )
            assert feat is not None
            actual_guid = str(feat.Guid).lower()
            assert actual_guid == DEGREE_FEATURE_GUID
            if not pre_existing_ms:
                created_guid = DEGREE_FEATURE_GUID

            # Must be in MsFeatureSystemOA.
            ms_match = _find_msfeat_by_guid(
                writable_project, DEGREE_FEATURE_GUID
            )
            assert ms_match is not None, (
                "Catalog-created inflection feature is NOT in "
                "MsFeatureSystemOA.FeaturesOC — owner routing is broken."
            )

            # Must NOT have appeared in PhFeatureSystemOA as a result of
            # this call. (If it was there before, that's pre-existing
            # project state; we only flag a regression if it appeared
            # newly during this test.)
            ph_match = _find_phonfeat_by_guid(
                writable_project, DEGREE_FEATURE_GUID
            )
            if not pre_existing_ph:
                assert ph_match is None, (
                    "CRITICAL: Inflection feature was created in "
                    "PhFeatureSystemOA (phonological feature system) "
                    "instead of MsFeatureSystemOA. This is a serious "
                    "owner-routing bug — InflectionFeatureOperations' "
                    "_get_root_list / _path_b_attach hooks must target "
                    "MsFeatureSystemOA."
                )
        finally:
            if created_guid is not None:
                _delete_msfeat_by_guid(writable_project, created_guid)


def _delete_mstype_by_guid(project, guid_str):
    """
    Best-effort delete of an IFsFeatStrucType from
    MsFeatureSystemOA.TypesOC by GUID. Used by the issue #37 tests
    to keep MsFeatureSystemOA.TypesOC clean across runs.
    """
    feature_system = project.lp.MsFeatureSystemOA
    if feature_system is None:
        return
    target_guid = guid_str.lower()
    for raw in list(feature_system.TypesOC):
        if str(raw.Guid).lower() == target_guid:
            try:
                feature_system.TypesOC.Remove(raw)
            except Exception:
                pass
            return


class TestInflectionFeaturesTypeFindCreate:
    """
    Coverage for InflectionFeatureOperations.TypeFind / TypeCreate
    (closes issue #37 -- deferred from #19's wish list). These wrap
    IFsFeatStrucType lookup and creation in MsFeatureSystemOA.TypesOC.
    Used by advanced workflows that group closed features into
    shared FsFeatStruc shapes (e.g. Bantu tCommonAgr).
    """

    def test_type_find_returns_none_for_missing(self, writable_project):
        """TypeFind for a name that doesn't exist returns None, not raise."""
        result = writable_project.InflectionFeatures.TypeFind(
            "qZ_definitely_does_not_exist_fsType"
        )
        assert result is None, (
            f"TypeFind for a missing type must return None, got {result!r}"
        )

    def test_type_create_then_find_round_trip(self, writable_project):
        """
        Round-trip: TypeCreate -> TypeFind by the same name -> identity
        match. Verifies the new IFsFeatStrucType lands in
        MsFeatureSystemOA.TypesOC and is reachable through TypeFind.
        """
        name = "qZ_TypeCreate_RoundTrip"

        # Pre-clean any leftover from a previous run.
        existing = writable_project.InflectionFeatures.TypeFind(name)
        if existing is not None:
            _delete_mstype_by_guid(writable_project, str(existing.Guid))

        new_type = writable_project.InflectionFeatures.TypeCreate(
            name, "qZTC"
        )
        try:
            assert new_type is not None, "TypeCreate returned None"

            # Find it back.
            found = writable_project.InflectionFeatures.TypeFind(name)
            assert found is not None, (
                f"TypeFind({name!r}) returned None for the just-created "
                "type; lookup did not find it in MsFeatureSystemOA.TypesOC"
            )
            assert found.Hvo == new_type.Hvo, (
                "TypeFind returned a different type than was created "
                f"(found Hvo={found.Hvo}, created Hvo={new_type.Hvo})"
            )
        finally:
            _delete_mstype_by_guid(writable_project, str(new_type.Guid))

    def test_type_create_rejects_duplicate(self, writable_project):
        """
        TypeCreate must refuse to create a second type with the same
        name. Prevents callers from silently shadowing existing types.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        name = "qZ_TypeCreate_DuplicateGuard"

        existing = writable_project.InflectionFeatures.TypeFind(name)
        if existing is not None:
            _delete_mstype_by_guid(writable_project, str(existing.Guid))

        first = writable_project.InflectionFeatures.TypeCreate(name, "qZdg")
        try:
            with pytest.raises(FP_ParameterError):
                writable_project.InflectionFeatures.TypeCreate(name, "qZdg2")
        finally:
            _delete_mstype_by_guid(writable_project, str(first.Guid))

    def test_type_create_rejects_empty_name(self, writable_project):
        """Empty name / abbreviation are rejected with FP_ParameterError."""
        from flexlibs2.code.FLExProject import FP_ParameterError

        with pytest.raises(FP_ParameterError):
            writable_project.InflectionFeatures.TypeCreate("", "abb")
        with pytest.raises(FP_ParameterError):
            writable_project.InflectionFeatures.TypeCreate("name", "")
        with pytest.raises(FP_ParameterError):
            writable_project.InflectionFeatures.TypeCreate("   ", "abb")


# ---------------------------------------------------------------------------
# Mock-based unit tests for Find / Exists / Create / CreateValue (issue #137)
# ---------------------------------------------------------------------------
# These tests exercise the Python logic of each method -- loops, condition
# checks, normalize_match_key comparisons, factory dispatch, error paths --
# by patching all LCM-specific calls (IFsFeatDefn casting, ITsString text
# extraction, TsStringUtils, factory.Create) so the tests run without a live
# FieldWorks project but still verify the actual code paths.
#
# Pattern: build a minimal mock FLExProject, patch LCM helpers at the
# InflectionFeatureOperations module level, then call the method under test.
# ---------------------------------------------------------------------------


def _make_infl_project(features=None, write_enabled=True):
    """
    Return a minimal mock FLExProject suitable for InflectionFeatureOperations.

    ``features`` is a list of (name_text, hvo) pairs that will be visible as
    mock IFsFeatDefn objects in MsFeatureSystemOA.FeaturesOC.
    """
    import contextlib
    from unittest.mock import Mock, MagicMock

    project = Mock()
    project.writeEnabled = write_enabled

    # _TransactionCM reads this as a real value (not an auto-vivified Mock) so
    # it can choose Phase 1. Phase 1 (non-undoable) is used here;
    # Transaction()/UndoableOperation() return real no-op context managers so
    # `with self._TransactionCM(...)` enters cleanly. Phase 1 never consults
    # ActionHandlerAccessor.CurrentDepth (only Phase 2 does), so no action
    # handler double is needed here.
    project._undoable = False
    project.Transaction = Mock(side_effect=lambda label="transaction": contextlib.nullcontext())
    project.UndoableOperation = Mock(side_effect=lambda label: contextlib.nullcontext())

    # project.project is the internal LCM cache accessor
    project.project = Mock()
    project.project.DefaultAnalWs = 2   # analysis WS handle = 2

    # project._FLExProject__WSHandle is called by __WSHandle(wsHandle) when a
    # non-None wsHandle is passed. Default: return the value unchanged.
    project._FLExProject__WSHandle = Mock(side_effect=lambda ws, default: ws)

    # MsFeatureSystemOA with FeaturesOC
    feature_system = Mock()
    feature_system.TypesOC = []

    raw_features = []
    for name_text, hvo in (features or []):
        raw = Mock()
        raw.Hvo = hvo
        # Store the text so the IFsFeatDefn + ITsString patch can retrieve it.
        raw._name_text = name_text
        raw_features.append(raw)
    feature_system.FeaturesOC = raw_features

    project.lp = Mock()
    project.lp.MsFeatureSystemOA = feature_system

    # ServiceLocator factory (used by Create / CreateValue)
    factory_mock = Mock()
    factory_mock.Create = Mock(return_value=Mock())
    service_locator = Mock()
    service_locator.GetService = Mock(return_value=factory_mock)
    project.project.ServiceLocator = service_locator

    return project, feature_system, factory_mock


def _patch_infl_ops_lcm(raw_features):
    """
    Return a context-manager stack that patches the LCM calls inside
    InflectionFeatureOperations at module level:
      - IFsFeatDefn(raw)  -> returns a Mock whose .Name.get_String(ws).Text
                             equals raw._name_text
      - ITsString(ts)     -> returns ts  (pass-through; Name.get_String already
                             returns an object with .Text set)
      - TsStringUtils     -> MagicMock whose .MakeString(text, ws) returns a
                             Mock with .Text = text. Patching the module-level
                             binding rather than .MakeString directly is
                             required because TsStringUtils is a CLR class
                             and its members are read-only at the .NET level.
    """
    from unittest.mock import Mock, patch, MagicMock

    def _ifsfeatdefn(raw):
        m = Mock()
        ts = Mock()
        ts.Text = getattr(raw, "_name_text", "")
        m.Name = Mock()
        m.Name.get_String = Mock(return_value=ts)
        m.Hvo = getattr(raw, "Hvo", 0)
        return m

    def _itsstring(ts_obj):
        # ITsString(feat.Name.get_String(ws)) - the ts_obj already has .Text
        return ts_obj

    def _makestring(text, ws):
        m = Mock()
        m.Text = text
        return m

    ts_string_utils_stub = MagicMock()
    ts_string_utils_stub.MakeString = Mock(side_effect=_makestring)

    target = "flexlibs2.code.Grammar.InflectionFeatureOperations"
    patches = [
        patch(f"{target}.IFsFeatDefn", side_effect=_ifsfeatdefn),
        patch(f"{target}.ITsString", side_effect=_itsstring),
        patch(f"{target}.TsStringUtils", new=ts_string_utils_stub),
    ]
    return patches


# Marker: these tests require the InflectionFeatureOperations module to be
# importable (i.e. SIL.LCModel available), so they naturally skip on machines
# without FieldWorks -- same contract as every other class in this file.

class TestInflectionFeaturesMock:
    """
    Mock-based unit tests for InflectionFeatureOperations.
    Covers Find, Exists, Create, CreateValue (issue #137).
    """

    def _get_ops(self, project):
        from flexlibs2.code.Grammar.InflectionFeatureOperations import (
            InflectionFeatureOperations,
        )
        return InflectionFeatureOperations(project)

    # -----------------------------------------------------------------------
    # Find
    # -----------------------------------------------------------------------

    def test_find_returns_matching_feature(self):
        """Find locates a feature by exact name (case-insensitive NFD match)."""
        project, fs, _ = _make_infl_project([("person", 10), ("number", 11)])
        ops = self._get_ops(project)

        patches = _patch_infl_ops_lcm(fs.FeaturesOC)
        import contextlib
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = ops.Find("person")

        assert result is not None, "Find('person') should find the feature"

    def test_find_returns_none_for_missing(self):
        """Find returns None when no feature has the given name."""
        project, fs, _ = _make_infl_project([("person", 10)])
        ops = self._get_ops(project)

        patches = _patch_infl_ops_lcm(fs.FeaturesOC)
        import contextlib
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = ops.Find("gender")

        assert result is None

    def test_find_is_case_insensitive(self):
        """Find matches 'Person' even when stored name is 'person'."""
        project, fs, _ = _make_infl_project([("person", 10)])
        ops = self._get_ops(project)

        patches = _patch_infl_ops_lcm(fs.FeaturesOC)
        import contextlib
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = ops.Find("PERSON")

        assert result is not None, "Find must be case-insensitive"

    def test_find_returns_none_when_feature_system_missing(self):
        """Find returns None gracefully when MsFeatureSystemOA is None."""
        project, fs, _ = _make_infl_project([])
        project.lp.MsFeatureSystemOA = None
        ops = self._get_ops(project)

        result = ops.Find("person")
        assert result is None

    # -----------------------------------------------------------------------
    # Exists
    # -----------------------------------------------------------------------

    def test_exists_true_for_present_feature(self):
        """Exists returns True when the feature is in MsFeatureSystemOA."""
        project, fs, _ = _make_infl_project([("number", 11)])
        ops = self._get_ops(project)

        patches = _patch_infl_ops_lcm(fs.FeaturesOC)
        import contextlib
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            exists = ops.Exists("number")

        assert exists is True

    def test_exists_false_for_absent_feature(self):
        """Exists returns False when no feature has the given name."""
        project, fs, _ = _make_infl_project([("number", 11)])
        ops = self._get_ops(project)

        patches = _patch_infl_ops_lcm(fs.FeaturesOC)
        import contextlib
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            exists = ops.Exists("tense")

        assert exists is False

    # -----------------------------------------------------------------------
    # Create
    # -----------------------------------------------------------------------

    def test_create_closed_feature_succeeds(self):
        """Create adds a closed feature when name does not exist."""
        from unittest.mock import Mock, patch, MagicMock

        project, fs, factory_mock = _make_infl_project([])

        # Make the factory return a clean mock and track Add calls
        new_feat_raw = Mock()
        new_feat_raw.Name = Mock()
        new_feat_raw.Name.set_String = Mock()
        new_feat_raw.Abbreviation = Mock()
        new_feat_raw.Abbreviation.set_String = Mock()
        factory_mock.Create = Mock(return_value=new_feat_raw)

        added_items = []
        fs.FeaturesOC = []
        original_add = Mock(side_effect=lambda x: added_items.append(x))
        # FeaturesOC needs .Add() and must be iterable for Exists check
        feat_oc_mock = Mock()
        feat_oc_mock.__iter__ = Mock(return_value=iter([]))
        feat_oc_mock.Add = original_add
        fs.FeaturesOC = feat_oc_mock

        ops = self._get_ops(project)

        target = "flexlibs2.code.Grammar.InflectionFeatureOperations"
        ts_string_utils_stub = MagicMock()
        ts_string_utils_stub.MakeString = Mock(side_effect=lambda t, ws: Mock(Text=t))
        with patch(f"{target}.IFsFeatDefn", side_effect=lambda r: r), \
             patch(f"{target}.ITsString", side_effect=lambda t: t), \
             patch(f"{target}.TsStringUtils", new=ts_string_utils_stub), \
             patch(f"{target}.IFsClosedFeature", side_effect=lambda r: r), \
             patch(f"{target}.IFsClosedFeatureFactory", MagicMock()):
            result = ops.Create("gender", "gend", type="closed")

        assert result is not None
        assert len(added_items) == 1, "New feature must be added to FeaturesOC"

    def test_create_raises_if_feature_exists(self):
        """Create raises FP_ParameterError when a feature with that name exists."""
        from flexlibs2.code.FLExProject import FP_ParameterError

        project, fs, _ = _make_infl_project([("gender", 20)])
        ops = self._get_ops(project)

        patches = _patch_infl_ops_lcm(fs.FeaturesOC)
        import contextlib, pytest
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            with pytest.raises(FP_ParameterError):
                ops.Create("gender", "gend")

    def test_create_raises_on_empty_name(self):
        """Create raises FP_ParameterError for an empty name."""
        from flexlibs2.code.FLExProject import FP_ParameterError

        project, _, _ = _make_infl_project([])
        ops = self._get_ops(project)

        with pytest.raises(FP_ParameterError):
            ops.Create("", "gend")

    def test_create_raises_on_empty_abbreviation(self):
        """Create raises FP_ParameterError for an empty abbreviation."""
        from flexlibs2.code.FLExProject import FP_ParameterError

        project, fs, _ = _make_infl_project([])
        ops = self._get_ops(project)

        patches = _patch_infl_ops_lcm(fs.FeaturesOC)
        import contextlib
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            with pytest.raises(FP_ParameterError):
                ops.Create("gender", "")

    def test_create_raises_when_write_disabled(self):
        """Create raises FP_ReadOnlyError when project is read-only."""
        from flexlibs2.code.FLExProject import FP_ReadOnlyError

        project, _, _ = _make_infl_project([], write_enabled=False)
        ops = self._get_ops(project)

        with pytest.raises(FP_ReadOnlyError):
            ops.Create("gender", "gend")

    # -----------------------------------------------------------------------
    # CreateValue
    # -----------------------------------------------------------------------

    def test_create_value_adds_to_feature_values_oc(self):
        """CreateValue attaches a new IFsSymFeatVal to the feature's ValuesOC."""
        from unittest.mock import Mock, patch, MagicMock

        project, fs, factory_mock = _make_infl_project([])

        # Build a mock closed feature with ValuesOC
        feature_mock = Mock()
        feature_mock.Hvo = 50
        values_oc = Mock()
        added_values = []
        values_oc.Add = Mock(side_effect=lambda v: added_values.append(v))
        feature_mock.ValuesOC = values_oc

        # New value returned by factory
        new_val = Mock()
        new_val.Name = Mock()
        new_val.Name.set_String = Mock()
        new_val.Abbreviation = Mock()
        new_val.Abbreviation.set_String = Mock()
        factory_mock.Create = Mock(return_value=new_val)

        ops = self._get_ops(project)

        target = "flexlibs2.code.Grammar.InflectionFeatureOperations"
        ts_string_utils_stub = MagicMock()
        ts_string_utils_stub.MakeString = Mock(side_effect=lambda t, ws: Mock(Text=t))
        with patch(f"{target}.IFsClosedFeature", side_effect=lambda r: r), \
             patch(f"{target}.IFsSymFeatVal", side_effect=lambda r: r), \
             patch(f"{target}.IFsSymFeatValFactory", MagicMock()), \
             patch(f"{target}.TsStringUtils", new=ts_string_utils_stub):
            result = ops.CreateValue(feature_mock, "masculine", "m")

        assert result is not None
        assert len(added_values) == 1, "CreateValue must add value to feature.ValuesOC"

    def test_create_value_raises_on_empty_name(self):
        """CreateValue raises FP_ParameterError for an empty value name."""
        from flexlibs2.code.FLExProject import FP_ParameterError
        from unittest.mock import Mock

        project, _, _ = _make_infl_project([])
        ops = self._get_ops(project)

        feature_mock = Mock()
        with pytest.raises(FP_ParameterError):
            ops.CreateValue(feature_mock, "", "m")

    def test_create_value_raises_when_write_disabled(self):
        """CreateValue raises FP_ReadOnlyError when project is read-only."""
        from flexlibs2.code.FLExProject import FP_ReadOnlyError
        from unittest.mock import Mock

        project, _, _ = _make_infl_project([], write_enabled=False)
        ops = self._get_ops(project)

        with pytest.raises(FP_ReadOnlyError):
            ops.CreateValue(Mock(), "masculine", "m")

    def test_create_value_raises_on_null_feature(self):
        """CreateValue raises FP_NullParameterError when feature is None."""
        from flexlibs2.code.FLExProject import FP_NullParameterError

        project, _, _ = _make_infl_project([])
        ops = self._get_ops(project)

        with pytest.raises(FP_NullParameterError):
            ops.CreateValue(None, "masculine", "m")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
