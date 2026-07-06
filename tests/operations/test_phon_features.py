#
#   test_phon_features.py
#
#   Class: TestPhonFeatureOperations
#          Phase 5b live-LCM integration tests for the new
#          PhonFeatureOperations module: feature/value creation,
#          MGA PhonFeatsEticGlossList catalog import, feature-struct
#          composition, and defensive regressions from earlier phases.
#
#          Mirrors the writable-project fixture pattern used by
#          tests/operations/test_pos_catalog.py and test_phon_rules.py.
#          Self-restoring round-trips: each test deletes what it created
#          as an in-body tested step (green path only), so residue is a
#          diagnostic signal on failure rather than hidden state.
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
# Constants - canonical GUIDs from PhonFeatsEticGlossList.xml
# ---------------------------------------------------------------------------

# fPAConsonantal feature + its two value children.
CONSONANTAL_FEATURE_GUID = "b4ddf8e5-1ff8-43fc-9723-04f1ee0471fc"
CONSONANTAL_POSITIVE_VALUE_GUID = "ec5800b4-52a8-4859-a976-f3005c53bd5f"
CONSONANTAL_NEGATIVE_VALUE_GUID = "81c50b82-83ff-4f73-8e27-6ff9217b810a"


# ---------------------------------------------------------------------------
# Helpers (still used for post-delete verification and catalog guard)
# ---------------------------------------------------------------------------


def _find_feature_by_guid(project, guid_str):
    """
    Walk PhFeatureSystemOA.FeaturesOC and return the IFsClosedFeature whose
    GUID matches `guid_str` (case-insensitive), or None.
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


def _delete_feature_by_guid(project, guid_str):
    """
    Best-effort cleanup: remove a feature (and cascade its values) from
    PhFeatureSystemOA.FeaturesOC. Safe to call on missing/already-deleted.
    """
    if not guid_str:
        return
    try:
        feat = _find_feature_by_guid(project, guid_str)
        if feat is None:
            return
        fs = project.lp.PhFeatureSystemOA
        if fs is not None:
            fs.FeaturesOC.Remove(feat)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPhonFeatureOperations:
    """
    Live-LCM coverage for PhonFeatureOperations Create/CreateValue,
    CreateFromCatalog, MakeFeatStruc, and defensive Phase 3/4 regressions.

    Round-trip design: each test creates an object, exercises the API,
    then deletes the object IN THE TEST BODY and asserts it is gone.
    On green the DB is net-zero. On failure the created object stays as
    a diagnostic signal (no finally-cleanup on the main object).
    """

    # --- Create -----------------------------------------------------------

    def test_create_feature_random_guid(self, writable_project):
        """
        Create(name=..., abbreviation=...) without a catalogSourceId must
        produce an IFsClosedFeature attached to PhFeatureSystemOA.FeaturesOC
        with a fresh (random) GUID and no CatalogSourceId set.
        """
        feat = writable_project.PhonFeatures.Create(
            name="testfeat", abbreviation="tf"
        )
        assert feat is not None, "Create returned None"
        created_guid = str(feat.Guid).lower()

        # GUID must NOT be a canonical catalog GUID (it was a fresh
        # random one from the parameterless factory create).
        assert created_guid != CONSONANTAL_FEATURE_GUID, (
            "Random-GUID create accidentally produced the canonical "
            "fPAConsonantal GUID."
        )
        # CatalogSourceId must be empty/None for non-catalog creates.
        cat_id = getattr(feat, "CatalogSourceId", "") or ""
        assert cat_id == "", (
            f"Non-catalog create unexpectedly set CatalogSourceId="
            f"{cat_id!r}"
        )

        # And the feature is actually findable by name (sanity).
        found = writable_project.PhonFeatures.Find("testfeat")
        assert found is not None, (
            "Newly created feature is not findable by name"
        )

        # --- round-trip teardown (in body, tested) ---
        writable_project.PhonFeatures.Delete(feat)
        assert writable_project.PhonFeatures.Find("testfeat") is None, (
            "Feature still findable after Delete - round-trip not net-zero"
        )

    def test_create_value_under_feature(self, writable_project):
        """
        CreateValue(feature, name, abbreviation) must attach the new value
        to feature.ValuesOC. We construct a fresh feature so we don't
        perturb pre-existing project state.
        """
        from SIL.LCModel import IFsSymFeatVal

        feat = writable_project.PhonFeatures.Create(
            name="testfeatval", abbreviation="tfv"
        )
        created_guid = str(feat.Guid).lower()

        before = feat.ValuesOC.Count
        val = writable_project.PhonFeatures.CreateValue(
            feat, name="positive", abbreviation="+"
        )
        assert val is not None, "CreateValue returned None"
        after = feat.ValuesOC.Count
        assert after == before + 1, (
            f"ValuesOC count did not increase: before={before}, after={after}"
        )

        # The created value's GUID must appear in ValuesOC.
        target = str(IFsSymFeatVal(val).Guid).lower()
        guids = {str(IFsSymFeatVal(v).Guid).lower() for v in feat.ValuesOC}
        assert target in guids, (
            "CreateValue's return value is not in feature.ValuesOC"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_feature_by_guid(writable_project, created_guid)
        assert _find_feature_by_guid(writable_project, created_guid) is None, (
            "Feature still present after delete - round-trip not net-zero"
        )

    # --- CreateFromCatalog ------------------------------------------------

    def test_create_from_catalog_uses_canonical_guid(self, writable_project):
        """
        CreateFromCatalog('fPAConsonantal') must produce a feature whose
        GUID is canonical, name 'consonantal', abbreviation 'cons', and
        TWO IFsSymFeatVal children with canonical positive/negative
        value GUIDs.

        If the canonical GUID is wrong, _CreateFeatureFromEntry's
        Path A and Path B both failed and the hardened Path C raised.
        (Phase 5a discovered this scenario; flag it as a real LCM
        compatibility issue if it surfaces.)
        """
        pre_existing = (
            _find_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            is not None
        )

        feat = writable_project.PhonFeatures.CreateFromCatalog(
            "fPAConsonantal"
        )
        assert feat is not None, "CreateFromCatalog returned None"

        actual_guid = str(feat.Guid).lower()
        assert actual_guid == CONSONANTAL_FEATURE_GUID, (
            f"Feature GUID {actual_guid!r} != canonical "
            f"{CONSONANTAL_FEATURE_GUID!r}. The hardened factory path "
            "may have fallen back; check _CreateFeatureFromEntry."
        )

        # Localized strings: name = 'consonantal', abbrev = 'cons'.
        en_handle = writable_project.WSHandle("en")
        if en_handle is not None:
            name_en = writable_project.PhonFeatures.GetName(
                feat, en_handle
            )
            abbr_en = writable_project.PhonFeatures.GetAbbreviation(
                feat, en_handle
            )
            assert name_en == "consonantal", (
                f"Name['en'] = {name_en!r}, expected 'consonantal'"
            )
            assert abbr_en == "cons", (
                f"Abbreviation['en'] = {abbr_en!r}, expected 'cons'"
            )

        # Exactly two value children with canonical GUIDs.
        from SIL.LCModel import IFsSymFeatVal

        value_guids = {
            str(IFsSymFeatVal(v).Guid).lower() for v in feat.ValuesOC
        }
        assert feat.ValuesOC.Count == 2, (
            f"Expected 2 values under fPAConsonantal, "
            f"got {feat.ValuesOC.Count}"
        )
        assert CONSONANTAL_POSITIVE_VALUE_GUID in value_guids, (
            f"Positive value GUID not found; got: {sorted(value_guids)}"
        )
        assert CONSONANTAL_NEGATIVE_VALUE_GUID in value_guids, (
            f"Negative value GUID not found; got: {sorted(value_guids)}"
        )

        # --- round-trip teardown: only delete if this test created it ---
        if not pre_existing:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            assert _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            ) is None, (
                "Catalog feature still present after delete - "
                "round-trip not net-zero"
            )

    def test_create_from_catalog_accepts_phon_prefix(self, writable_project):
        """
        CreateFromCatalog('PHON:fPAConsonantal') must behave identically
        to the bare-id form: same canonical feature GUID.
        """
        pre_existing = (
            _find_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            is not None
        )

        feat = writable_project.PhonFeatures.CreateFromCatalog(
            "PHON:fPAConsonantal"
        )
        assert feat is not None
        assert str(feat.Guid).lower() == CONSONANTAL_FEATURE_GUID, (
            "PHON:-prefixed form produced different GUID from bare form"
        )

        # --- round-trip teardown: only delete if this test created it ---
        if not pre_existing:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            assert _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            ) is None, (
                "Catalog feature still present after delete - "
                "round-trip not net-zero"
            )

    def test_create_from_catalog_idempotent(self, writable_project):
        """
        A second call to CreateFromCatalog with the same source_id must
        return the existing feature (canonical GUID match) and not add
        any new value children - count stays at 2.
        """
        pre_existing = (
            _find_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            is not None
        )

        first = writable_project.PhonFeatures.CreateFromCatalog(
            "fPAConsonantal"
        )

        second = writable_project.PhonFeatures.CreateFromCatalog(
            "fPAConsonantal"
        )

        assert second is not None
        assert str(first.Guid).lower() == str(second.Guid).lower(), (
            "Idempotency violated: second CreateFromCatalog returned "
            "a different feature"
        )
        # Value count stable at 2.
        assert second.ValuesOC.Count == 2, (
            f"Idempotency violated: value count drifted to "
            f"{second.ValuesOC.Count} after second call"
        )

        # And only ONE feature with this canonical GUID exists.
        from SIL.LCModel import IFsClosedFeature

        matches = 0
        for raw in writable_project.lp.PhFeatureSystemOA.FeaturesOC:
            try:
                f = IFsClosedFeature(raw)
            except Exception:
                continue
            if str(f.Guid).lower() == CONSONANTAL_FEATURE_GUID:
                matches += 1
        assert matches == 1, (
            f"Expected exactly one fPAConsonantal feature, found {matches}"
        )

        # --- round-trip teardown: only delete if this test created it ---
        if not pre_existing:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            assert _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            ) is None, (
                "Catalog feature still present after delete - "
                "round-trip not net-zero"
            )

    # --- MakeFeatStruc ----------------------------------------------------

    def test_make_featstruc_rejects_owner_none(self, writable_project):
        """
        MakeFeatStruc(specs=[], owner=None) must raise FP_ParameterError
        (issue #28). The previous behaviour returned an unowned struct
        whose property accessors NPE'd inside CmObject.get_Services(),
        making the returned object unusable. The tightened contract
        rejects the case outright - explicit failures over silent
        partial functionality.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        with pytest.raises(FP_ParameterError):
            writable_project.PhonFeatures.MakeFeatStruc([])

        # Non-empty specs with owner=None must still raise (this case
        # was already rejected; verifying it still is after the contract
        # tightening).
        with pytest.raises(FP_ParameterError):
            writable_project.PhonFeatures.MakeFeatStruc(
                [(object(), object())]
            )

    def test_make_featstruc_unowned_requires_empty_specs(
        self, writable_project
    ):
        """
        Phase 5b contract tightening: MakeFeatStruc(owner=None, specs=[...])
        with NON-EMPTY specs must raise FP_ParameterError, because LCM
        forbids property writes on unowned IFsFeatStruc objects (Phase 2
        ownership-NPE pattern). Callers must either provide an owner or
        pass empty specs.
        """
        from SIL.LCModel import IFsSymFeatVal
        from flexlibs2.code.FLExProject import FP_ParameterError

        pre_existing = (
            _find_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            is not None
        )

        feat = writable_project.PhonFeatures.CreateFromCatalog(
            "fPAConsonantal"
        )

        # Pick the positive value.
        positive = None
        for raw in feat.ValuesOC:
            v = IFsSymFeatVal(raw)
            if str(v.Guid).lower() == CONSONANTAL_POSITIVE_VALUE_GUID:
                positive = v
                break
        assert positive is not None, (
            "Could not locate positive value under fPAConsonantal"
        )

        with pytest.raises(FP_ParameterError):
            writable_project.PhonFeatures.MakeFeatStruc(
                [(feat, positive)]
            )

        # --- round-trip teardown: only delete if this test created it ---
        if not pre_existing:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            assert _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            ) is None, (
                "Catalog feature still present after delete - "
                "round-trip not net-zero"
            )

    def test_make_featstruc_owned(self, writable_project):
        """
        MakeFeatStruc with owner=phoneme must attach the struct to
        phoneme.FeaturesOA BEFORE populating FeatureSpecsOC. The Phase 2
        ownership-ordering rule means that if attachment happened AFTER
        populating, LCM would raise NPE on the orphan property setter.
        Successful completion proves the order is correct.
        """
        from SIL.LCModel import IFsFeatStruc, IFsSymFeatVal

        # Use the most common test phoneme; create it if missing.
        phoneme = writable_project.Phonemes.Find("o")
        phoneme_was_created = False
        if phoneme is None:
            phoneme = writable_project.Phonemes.Create("o")
            phoneme_was_created = True

        pre_existing = (
            _find_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            is not None
        )
        original_features = phoneme.FeaturesOA  # may be None
        try:
            feat = writable_project.PhonFeatures.CreateFromCatalog(
                "fPAConsonantal"
            )

            negative = None
            for raw in feat.ValuesOC:
                v = IFsSymFeatVal(raw)
                if str(v.Guid).lower() == CONSONANTAL_NEGATIVE_VALUE_GUID:
                    negative = v
                    break
            assert negative is not None

            # If the phoneme already had a FeaturesOA, our attach will
            # replace it. That's fine for the test; the finally restores it.
            struct = writable_project.PhonFeatures.MakeFeatStruc(
                [(feat, negative)], owner=phoneme
            )
            assert struct is not None
            struct = IFsFeatStruc(struct)

            # Phoneme.FeaturesOA must point at the struct we created.
            attached = phoneme.FeaturesOA
            assert attached is not None, (
                "After MakeFeatStruc(owner=phoneme), phoneme.FeaturesOA "
                "is still None"
            )
            # And the struct contains the spec we asked for.
            assert IFsFeatStruc(attached).FeatureSpecsOC.Count == 1, (
                "Owned struct's FeatureSpecsOC count != 1; ownership "
                "ordering may have skipped the population step."
            )
        finally:
            # The phoneme/FeaturesOA restore is a genuine unrelated teardown
            # (we borrowed a phoneme that may have pre-existed). Keep finally
            # here for those two items only.
            try:
                phoneme.FeaturesOA = original_features
            except Exception:
                pass
            if not pre_existing:
                _delete_feature_by_guid(
                    writable_project, CONSONANTAL_FEATURE_GUID
                )
            if phoneme_was_created:
                try:
                    writable_project.Phonemes.Delete(phoneme)
                except Exception:
                    pass

    # --- Defensive regressions -------------------------------------------

    def test_find_feature_with_diacritic(self, writable_project):
        """
        Phase 3 NFC/NFD regression: Find() must locate a feature by name
        even when the caller passes a string in a different Unicode
        normalisation form. We write a name containing a Unicode
        character and look it up via the same string passed to NFC().
        """
        import unicodedata

        # Composed string ("syllabic" is ASCII, but we use a name with
        # a guaranteed-recognisable Unicode codepoint to exercise NFC
        # vs NFD normalisation).
        composed = unicodedata.normalize("NFC", "syllabicé")  # "syllabicé"

        feat = writable_project.PhonFeatures.Create(
            name=composed, abbreviation="syl"
        )
        created_guid = str(feat.Guid).lower()

        # Look up using a different normalisation form to confirm
        # normalize_match_key (NFD + casefold) is doing its job.
        decomposed = unicodedata.normalize("NFD", composed)
        found = writable_project.PhonFeatures.Find(decomposed)
        assert found is not None, (
            "Find() with NFD input could not match an NFC-stored "
            f"feature name {composed!r}"
        )
        assert str(found.Guid).lower() == created_guid, (
            "Find() returned a different feature than the one we "
            "just created."
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_feature_by_guid(writable_project, created_guid)
        assert _find_feature_by_guid(writable_project, created_guid) is None, (
            "Feature still present after delete - round-trip not net-zero"
        )

    def test_delete_feature_unwraps_wrapper(self, writable_project):
        """
        Phase 4 wrapper-aware regression: Delete() must accept an item
        from GetAll() even if GetAll yields wrappers (rather than naked
        LCM objects). If GetAll never yields wrappers in this build,
        skip - the unwrap path is still exercised by other tests.
        """
        # Create a feature, then locate it via GetAll() iteration and
        # pass that (possibly-wrapped) reference back to Delete().
        feat = writable_project.PhonFeatures.Create(
            name="wrapperdel", abbreviation="wd"
        )
        created_guid = str(feat.Guid).lower()

        # Walk GetAll(); find ours.
        target_ref = None
        wrapper_seen = False
        for entry in writable_project.PhonFeatures.GetAll():
            # Detect whether the iterator yields a wrapper that
            # exposes ._obj (LCMObjectWrapper-style).
            if hasattr(entry, "_obj") and not hasattr(entry, "Hvo"):
                wrapper_seen = True
            # Compare via the underlying LCM GUID regardless of shape.
            try:
                inner = entry._obj if hasattr(entry, "_obj") else entry
                if str(inner.Guid).lower() == created_guid:
                    target_ref = entry
                    break
            except Exception:
                pass

        if not wrapper_seen:
            # No wrapper yielded - clean up and skip.
            _delete_feature_by_guid(writable_project, created_guid)
            pytest.skip(
                "PhonFeatures.GetAll() yields naked LCM objects in "
                "this build; wrapper-unwrap path not exercised."
            )

        assert target_ref is not None, (
            "Could not locate freshly-created feature via GetAll()"
        )

        # Delete via the wrapper-typed reference; if __Unwrap is
        # missing or wrong, LCM raises ArgumentException.
        writable_project.PhonFeatures.Delete(target_ref)

        # --- round-trip teardown (in body, tested) ---
        assert _find_feature_by_guid(
            writable_project, created_guid
        ) is None, "Delete() did not actually remove the feature"


class TestPhonFeatureSync:
    """
    Live-LCM coverage for PhonFeatureOperations.GetSyncableProperties /
    ApplySyncableProperties (issue #222).

    A closed feature owns its symbolic values; the syncable-properties
    round-trip must carry those values (with GUIDs) so a feature applied
    onto a fresh target is not left an empty shell.
    """

    def test_getsyncable_includes_values_with_guids(self, writable_project):
        """
        GetSyncableProperties on a catalog feature must surface Name /
        Abbreviation and a Values list, each value carrying its own GUID.
        """
        ops = writable_project.PhonFeatures
        feat = ops.CreateFromCatalog("PHON:fPAConsonantal")
        try:
            props = ops.GetSyncableProperties(feat)

            assert isinstance(props, dict)
            assert "Name" in props and isinstance(props["Name"], dict)
            assert "Values" in props, "Values list missing from syncable props"

            value_guids = {
                v["Guid"].lower() for v in props["Values"] if v.get("Guid")
            }
            assert CONSONANTAL_POSITIVE_VALUE_GUID in value_guids
            assert CONSONANTAL_NEGATIVE_VALUE_GUID in value_guids
            # Each value carries at least an abbreviation (the +/- marker).
            for v in props["Values"]:
                assert "Abbreviation" in v or "Name" in v
        finally:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)

    def test_apply_cocreates_values_guid_aligned(self, writable_project):
        """
        ApplySyncableProperties onto a fresh feature must co-create the
        owned values GUID-aligned, so the target feature mirrors the source
        (not an empty shell).
        """
        ops = writable_project.PhonFeatures

        # Build a source props dict by hand so the test does not depend on a
        # second project. Uses the canonical value GUIDs.
        anal_ws = next(iter(
            ws.Id for ws in writable_project.WritingSystems.GetAll()
        ))
        src_props = {
            "Name": {anal_ws: "synctest-feature"},
            "Abbreviation": {anal_ws: "stf"},
            "Values": [
                {
                    "Guid": CONSONANTAL_POSITIVE_VALUE_GUID,
                    "Name": {anal_ws: "positive"},
                    "Abbreviation": {anal_ws: "+"},
                },
                {
                    "Guid": CONSONANTAL_NEGATIVE_VALUE_GUID,
                    "Name": {anal_ws: "negative"},
                    "Abbreviation": {anal_ws: "-"},
                },
            ],
        }

        feat = ops.Create(name="synctest-shell", abbreviation="sts")
        created_guid = str(feat.Guid)
        try:
            ops.ApplySyncableProperties(feat, src_props)

            # Re-read: the two values must exist under the feature with the
            # requested GUIDs.
            props_back = ops.GetSyncableProperties(feat)
            back_guids = {
                v["Guid"].lower() for v in props_back.get("Values", [])
            }
            assert CONSONANTAL_POSITIVE_VALUE_GUID in back_guids
            assert CONSONANTAL_NEGATIVE_VALUE_GUID in back_guids
            assert props_back["Name"][anal_ws] == "synctest-feature"
        finally:
            _delete_feature_by_guid(writable_project, created_guid)

    def test_apply_is_idempotent(self, writable_project):
        """
        Applying the same value set twice must not duplicate values (GUID
        match reuses the existing value).
        """
        ops = writable_project.PhonFeatures
        anal_ws = next(iter(
            ws.Id for ws in writable_project.WritingSystems.GetAll()
        ))
        src_props = {
            "Name": {anal_ws: "idem-feature"},
            "Values": [
                {"Guid": CONSONANTAL_POSITIVE_VALUE_GUID,
                 "Abbreviation": {anal_ws: "+"}},
            ],
        }

        feat = ops.Create(name="idem-shell", abbreviation="idm")
        created_guid = str(feat.Guid)
        try:
            ops.ApplySyncableProperties(feat, src_props)
            ops.ApplySyncableProperties(feat, src_props)

            values = list(ops.GetValues(feat))
            matching = [
                v for v in values
                if str(v.Guid).lower() == CONSONANTAL_POSITIVE_VALUE_GUID
            ]
            assert len(matching) == 1, "Value duplicated across two applies"
        finally:
            _delete_feature_by_guid(writable_project, created_guid)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
