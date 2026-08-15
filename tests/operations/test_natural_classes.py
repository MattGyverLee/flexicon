#
#   test_natural_classes.py
#
#   Class: TestNaturalClassFeatureBased
#          Phase 5d live-LCM integration tests for the feature-based
#          natural-class API added to NaturalClassOperations:
#          CreateFeatureBased, GetType, GetFeatures, SetFeatures.
#
#          Mirrors the writable-project fixture pattern used by
#          tests/operations/test_phon_features.py. Self-restoring
#          round-trips: each test deletes what it created as an in-body
#          tested step (green path only), so residue is a diagnostic
#          signal on failure rather than hidden state.
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
# Live-LCM project fixture (mirrors test_phon_features.py)
# ---------------------------------------------------------------------------

_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_writable_project():
    """Open one of the standard test projects in write mode, or None."""
    try:
        from flexicon.code.FLExProject import FLExProject
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
# Canonical catalog GUIDs (fPAConsonantal feature + +/- values)
# ---------------------------------------------------------------------------

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
    """Best-effort cleanup: remove a feature from PhFeatureSystemOA.FeaturesOC."""
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


def _delete_nc(project, nc):
    """Best-effort: remove a natural class regardless of subtype."""
    if nc is None:
        return
    try:
        project.NaturalClasses.Delete(nc)
    except Exception:
        pass


def _get_consonantal_positive(project, feat):
    """Locate the +consonantal IFsSymFeatVal under the given feature."""
    from SIL.LCModel import IFsSymFeatVal

    for raw in feat.ValuesOC:
        v = IFsSymFeatVal(raw)
        if str(v.Guid).lower() == CONSONANTAL_POSITIVE_VALUE_GUID:
            return v
    return None


def _get_consonantal_negative(project, feat):
    """Locate the -consonantal IFsSymFeatVal under the given feature."""
    from SIL.LCModel import IFsSymFeatVal

    for raw in feat.ValuesOC:
        v = IFsSymFeatVal(raw)
        if str(v.Guid).lower() == CONSONANTAL_NEGATIVE_VALUE_GUID:
            return v
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNaturalClassFeatureBased:
    """
    Phase 5d coverage for feature-based natural class operations:
    CreateFeatureBased, GetType, GetFeatures, SetFeatures.

    Round-trip design: each test creates an object, exercises the API,
    then deletes the object IN THE TEST BODY and asserts it is gone.
    On green the DB is net-zero. On failure the created object stays as
    a diagnostic signal (no finally-cleanup on the main object).
    """

    # --- CreateFeatureBased ----------------------------------------------

    def test_create_feature_based_no_specs_returns_nc_with_no_features(
        self, writable_project
    ):
        """
        CreateFeatureBased(name, abbr) with no specs must return an
        IPhNCFeatures whose FeaturesOA is None (no struct attached
        yet) so the caller can later populate via SetFeatures.
        """
        nc = writable_project.NaturalClasses.CreateFeatureBased(
            "test", "t"
        )
        assert nc is not None, "CreateFeatureBased returned None"

        # Concrete LCM ClassName must be IPhNCFeatures.
        assert nc.ClassName == "PhNCFeatures", (
            f"Expected ClassName 'PhNCFeatures', got {nc.ClassName!r}"
        )
        # No specs provided => FeaturesOA must remain None.
        assert nc.FeaturesOA is None, (
            "CreateFeatureBased(specs=None) should leave FeaturesOA "
            "unset; got a non-None struct."
        )

        # --- round-trip teardown (in body, tested) ---
        nc_hvo = nc.Hvo
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find("test") is None, (
            "Natural class still findable after Delete - round-trip not net-zero"
        )

    def test_create_feature_based_with_specs_populates_featuresoa(
        self, writable_project
    ):
        """
        CreateFeatureBased(name, abbr, specs=[(feat, val)]) must attach a
        populated IFsFeatStruc to FeaturesOA whose FeatureSpecsOC has one
        entry. We use the canonical fPAConsonantal catalog feature + its
        positive value to avoid touching project-defined features.
        """
        from SIL.LCModel import IFsFeatStruc

        pre_existing = (
            _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            )
            is not None
        )

        feat = writable_project.PhonFeatures.CreateFromCatalog(
            "fPAConsonantal"
        )

        plus = _get_consonantal_positive(writable_project, feat)
        assert plus is not None, (
            "Could not locate +consonantal value under fPAConsonantal"
        )

        nc = writable_project.NaturalClasses.CreateFeatureBased(
            "voiced", "v", specs=[(feat, plus)]
        )
        assert nc is not None
        assert nc.FeaturesOA is not None, (
            "CreateFeatureBased(specs=[...]) did not attach FeaturesOA"
        )
        fs = IFsFeatStruc(nc.FeaturesOA)
        assert fs.FeatureSpecsOC.Count == 1, (
            f"Expected FeatureSpecsOC.Count == 1, "
            f"got {fs.FeatureSpecsOC.Count}"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find("voiced") is None, (
            "Natural class still findable after Delete - round-trip not net-zero"
        )
        if not pre_existing:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            assert _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            ) is None, (
                "Catalog feature still present after delete - "
                "round-trip not net-zero"
            )

    # --- GetType ---------------------------------------------------------

    def test_get_type_returns_features_for_feature_based(
        self, writable_project
    ):
        """GetType on an IPhNCFeatures must return 'features'."""
        nc = writable_project.NaturalClasses.CreateFeatureBased(
            "test_feat_type", "tft"
        )

        assert (
            writable_project.NaturalClasses.GetType(nc) == "features"
        ), "GetType did not return 'features' for IPhNCFeatures"

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find("test_feat_type") is None, (
            "Natural class still findable after Delete - round-trip not net-zero"
        )

    def test_get_type_returns_segments_for_segment_based(
        self, writable_project
    ):
        """GetType on an IPhNCSegments (Create) must return 'segments'."""
        nc = writable_project.NaturalClasses.Create(
            "test_seg_type", "tst"
        )

        assert (
            writable_project.NaturalClasses.GetType(nc) == "segments"
        ), "GetType did not return 'segments' for IPhNCSegments"

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find("test_seg_type") is None, (
            "Natural class still findable after Delete - round-trip not net-zero"
        )

    # --- GetFeatures -----------------------------------------------------

    def test_get_features_raises_on_segment_nc(self, writable_project):
        """
        GetFeatures must raise FP_ParameterError when called on a
        segment-based natural class (IPhNCSegments has no FeaturesOA).
        """
        from flexicon.code.FLExProject import FP_ParameterError

        nc = writable_project.NaturalClasses.Create(
            "test_seg_getf", "tsg"
        )

        with pytest.raises(FP_ParameterError):
            writable_project.NaturalClasses.GetFeatures(nc)

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find("test_seg_getf") is None, (
            "Natural class still findable after Delete - round-trip not net-zero"
        )

    def test_get_features_returns_none_when_unset(self, writable_project):
        """
        GetFeatures on a feature-based NC with no struct attached must
        return None (the underlying FeaturesOA).
        """
        nc = writable_project.NaturalClasses.CreateFeatureBased(
            "test_no_specs", "tns"
        )

        result = writable_project.NaturalClasses.GetFeatures(nc)
        assert result is None, (
            f"GetFeatures on unset feature-based NC should return "
            f"None; got {result!r}"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find("test_no_specs") is None, (
            "Natural class still findable after Delete - round-trip not net-zero"
        )

    def test_get_features_returns_featstruc_when_set(
        self, writable_project
    ):
        """
        GetFeatures on a populated feature-based NC must return an
        IFsFeatStruc whose FeatureSpecsOC matches what we passed in.
        """
        from SIL.LCModel import IFsFeatStruc

        pre_existing = (
            _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            )
            is not None
        )

        feat = writable_project.PhonFeatures.CreateFromCatalog(
            "fPAConsonantal"
        )

        plus = _get_consonantal_positive(writable_project, feat)
        assert plus is not None

        nc = writable_project.NaturalClasses.CreateFeatureBased(
            "test_getf_set", "tgs", specs=[(feat, plus)]
        )

        fs = writable_project.NaturalClasses.GetFeatures(nc)
        assert fs is not None, (
            "GetFeatures returned None for a feature-based NC "
            "created with specs."
        )
        fs_cast = IFsFeatStruc(fs)
        assert fs_cast.FeatureSpecsOC.Count == 1, (
            f"Expected FeatureSpecsOC.Count == 1, "
            f"got {fs_cast.FeatureSpecsOC.Count}"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find("test_getf_set") is None, (
            "Natural class still findable after Delete - round-trip not net-zero"
        )
        if not pre_existing:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            assert _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            ) is None, (
                "Catalog feature still present after delete - "
                "round-trip not net-zero"
            )

    # --- SetFeatures -----------------------------------------------------

    def test_set_features_replaces_existing(self, writable_project):
        """
        SetFeatures with new specs must replace any existing FeaturesOA.
        After replacement, FeatureSpecsOC reflects the new specs only.
        We create with one spec (+consonantal), then SetFeatures with a
        different spec (-consonantal) and verify the count is still 1
        and the new spec's value GUID is the one we just set.
        """
        from SIL.LCModel import IFsFeatStruc, IFsClosedValue

        pre_existing = (
            _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            )
            is not None
        )

        feat = writable_project.PhonFeatures.CreateFromCatalog(
            "fPAConsonantal"
        )

        plus = _get_consonantal_positive(writable_project, feat)
        minus = _get_consonantal_negative(writable_project, feat)
        assert plus is not None and minus is not None

        # Create with +consonantal.
        nc = writable_project.NaturalClasses.CreateFeatureBased(
            "test_setf_replace", "tsr", specs=[(feat, plus)]
        )
        initial_fs = IFsFeatStruc(nc.FeaturesOA)
        assert initial_fs.FeatureSpecsOC.Count == 1

        # Replace with -consonantal.
        writable_project.NaturalClasses.SetFeatures(
            nc, [(feat, minus)]
        )

        replaced = writable_project.NaturalClasses.GetFeatures(nc)
        assert replaced is not None, (
            "After SetFeatures, FeaturesOA is None"
        )
        replaced_fs = IFsFeatStruc(replaced)
        assert replaced_fs.FeatureSpecsOC.Count == 1, (
            f"Expected FeatureSpecsOC.Count == 1 after replacement, "
            f"got {replaced_fs.FeatureSpecsOC.Count}"
        )

        # Confirm the spec now references the -consonantal value.
        value_guids = set()
        for spec in replaced_fs.FeatureSpecsOC:
            cv = IFsClosedValue(spec)
            if cv.ValueRA is not None:
                value_guids.add(str(cv.ValueRA.Guid).lower())
        assert CONSONANTAL_NEGATIVE_VALUE_GUID in value_guids, (
            f"Replacement spec does not reference -consonantal value; "
            f"got {sorted(value_guids)}"
        )
        assert CONSONANTAL_POSITIVE_VALUE_GUID not in value_guids, (
            "Original +consonantal spec was not discarded on replacement"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find("test_setf_replace") is None, (
            "Natural class still findable after Delete - round-trip not net-zero"
        )
        if not pre_existing:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            assert _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            ) is None, (
                "Catalog feature still present after delete - "
                "round-trip not net-zero"
            )

    def test_set_features_raises_on_segment_nc(self, writable_project):
        """
        SetFeatures must raise FP_ParameterError when called on a
        segment-based natural class (no FeaturesOA available).
        """
        from flexicon.code.FLExProject import FP_ParameterError

        pre_existing = (
            _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            )
            is not None
        )

        feat = writable_project.PhonFeatures.CreateFromCatalog(
            "fPAConsonantal"
        )
        plus = _get_consonantal_positive(writable_project, feat)
        assert plus is not None

        nc = writable_project.NaturalClasses.Create(
            "test_seg_setf", "tss"
        )

        with pytest.raises(FP_ParameterError):
            writable_project.NaturalClasses.SetFeatures(
                nc, [(feat, plus)]
            )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find("test_seg_setf") is None, (
            "Natural class still findable after Delete - round-trip not net-zero"
        )
        if not pre_existing:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            assert _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            ) is None, (
                "Catalog feature still present after delete - "
                "round-trip not net-zero"
            )


class TestNaturalClassDuplicateDispatch:
    """
    Regression coverage for issue #27: NaturalClassOperations.Duplicate
    previously hardcoded IPhNCSegmentsFactory and the SegmentsRC copy
    loop, silently producing a wrong-type empty clone from a
    feature-based source. The fix dispatches on the concrete source
    type and clones FeaturesOA for IPhNCFeatures sources.

    Round-trip design: each test creates objects, exercises the API,
    then deletes IN THE TEST BODY and asserts gone. On failure residue
    is left as a diagnostic signal.
    """

    def test_duplicate_segments_returns_segments_clone(
        self, writable_project
    ):
        """
        Segment-based source -> segment-based duplicate. Existing
        membership in SegmentsRC must be preserved (shallow reference
        copy is fine; the spec is "same phonemes pointed to by both
        classes").
        """
        source = writable_project.NaturalClasses.Create(
            "qZ_dup_segments_src", "qZs"
        )

        duplicate = writable_project.NaturalClasses.Duplicate(source)
        assert duplicate is not None, "Duplicate returned None"
        assert (
            writable_project.NaturalClasses.GetType(duplicate)
            == "segments"
        ), (
            "Segment-based source produced a non-segments duplicate: "
            f"{writable_project.NaturalClasses.GetType(duplicate)!r}"
        )
        # Sanity: distinct Hvo from source.
        assert duplicate.Hvo != source.Hvo, (
            "Duplicate returned the source object itself"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, duplicate)
        _delete_nc(writable_project, source)
        assert writable_project.NaturalClasses.Find("qZ_dup_segments_src") is None, (
            "Source NC still findable after Delete - round-trip not net-zero"
        )

    def test_duplicate_features_returns_features_clone(
        self, writable_project
    ):
        """
        Feature-based source -> feature-based duplicate with cloned
        FeaturesOA. Before the fix, this produced an IPhNCSegments
        with empty SegmentsRC instead -- losing the feature constraints
        entirely.
        """
        pre_existing = (
            _find_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            is not None
        )

        feat = writable_project.PhonFeatures.CreateFromCatalog(
            "fPAConsonantal"
        )
        plus = _get_consonantal_positive(writable_project, feat)
        assert plus is not None, "Could not find +consonantal value"

        source = writable_project.NaturalClasses.CreateFeatureBased(
            "qZ_dup_features_src", "qZf", specs=[(feat, plus)]
        )

        duplicate = writable_project.NaturalClasses.Duplicate(source)

        # Core assertion: duplicate is feature-based, not segments.
        assert (
            writable_project.NaturalClasses.GetType(duplicate)
            == "features"
        ), (
            "Feature-based source produced a non-features duplicate: "
            f"{writable_project.NaturalClasses.GetType(duplicate)!r} "
            "(this is exactly the issue #27 bug)"
        )

        # FeaturesOA must be populated with the cloned spec.
        dup_struct = duplicate.FeaturesOA
        assert dup_struct is not None, (
            "Duplicate has no FeaturesOA - spec clone path didn't run"
        )
        spec_count = sum(1 for _ in dup_struct.FeatureSpecsOC)
        assert spec_count == 1, (
            f"Duplicate FeaturesOA should have 1 spec, "
            f"got {spec_count}"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, duplicate)
        _delete_nc(writable_project, source)
        assert writable_project.NaturalClasses.Find("qZ_dup_features_src") is None, (
            "Source NC still findable after Delete - round-trip not net-zero"
        )
        if not pre_existing:
            _delete_feature_by_guid(writable_project, CONSONANTAL_FEATURE_GUID)
            assert _find_feature_by_guid(
                writable_project, CONSONANTAL_FEATURE_GUID
            ) is None, (
                "Catalog feature still present after delete - "
                "round-trip not net-zero"
            )


class TestNaturalClassFindExists:
    """
    Coverage for `NaturalClassOperations.Find()` and `Exists()` - closes
    the API-parity gap reported in issue #30. Sister classes
    (POSOperations, PhonemeOperations, PhonFeatureOperations,
    PhonRuleOperations) already expose Find/Exists; this verifies the
    same pair on NaturalClassOperations behaves consistently.

    The implementations are NFD-aware casefold matchers, so coverage
    includes both segment-based (IPhNCSegments) and feature-based
    (IPhNCFeatures) variants - Find must succeed for both because it
    iterates GetAll() which yields IPhNaturalClass regardless of
    concrete type.

    Round-trip design: each test creates an object, exercises the API,
    then deletes IN THE TEST BODY and asserts gone. On failure residue
    is left as a diagnostic signal (no pre-clean at test start).
    """

    def test_find_returns_segment_class_when_present(self, writable_project):
        """Round-trip: Create -> Find -> identity match."""
        name = "qZ_find_roundtrip_segments"

        nc = writable_project.NaturalClasses.Create(name, "qZf")
        found = writable_project.NaturalClasses.Find(name)
        assert found is not None, (
            f"Find({name!r}) returned None for a just-created NC"
        )
        assert found.Hvo == nc.Hvo, (
            "Find returned a different NC than was just created "
            f"(found Hvo={found.Hvo}, created Hvo={nc.Hvo})"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find(name) is None, (
            "NC still findable after Delete - round-trip not net-zero"
        )

    def test_find_returns_none_for_missing(self, writable_project):
        """Find for a name that doesn't exist must return None, not raise."""
        result = writable_project.NaturalClasses.Find(
            "qZ_definitely_does_not_exist_natural_class"
        )
        assert result is None, (
            f"Find for a missing NC must return None, got {result!r}"
        )

    def test_find_is_nfd_aware(self, writable_project):
        """
        Catalog-aligned NC names containing combining marks must be
        findable using their NFC-encoded form (Python source convention),
        even though FLEx stores them NFD. POSOperations.Find behaves
        this way; NaturalClassOperations.Find must match.
        """
        # 'négatif' in NFC (single é) vs NFD (e + combining acute).
        # Both must resolve to the same NC.
        nfc_name = "qZ_négatif"           # composed: é
        nfd_name = "qZ_négatif"          # decomposed: e + combining acute

        nc = writable_project.NaturalClasses.Create(nfc_name, "qZn")

        # Find via the alternate normalisation form must hit the
        # same NC. Which form FLEx stores internally is an LCM
        # implementation detail; the wrapper must hide it.
        found_via_nfc = writable_project.NaturalClasses.Find(nfc_name)
        found_via_nfd = writable_project.NaturalClasses.Find(nfd_name)

        assert found_via_nfc is not None, (
            "Find(NFC) failed for a name created from an NFC string"
        )
        assert found_via_nfd is not None, (
            "Find(NFD) failed for a name created from an NFC string - "
            "Find is not NFD-aware, contrary to the issue #30 contract"
        )
        assert found_via_nfc.Hvo == found_via_nfd.Hvo, (
            "Find(NFC) and Find(NFD) resolved to different NCs"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find(nfc_name) is None, (
            "NC still findable after Delete - round-trip not net-zero"
        )

    def test_exists_mirrors_find(self, writable_project):
        """
        Exists must return True for a created NC and False for a missing
        one. Spec says Exists is a thin bool wrapper around Find.
        """
        name = "qZ_exists_roundtrip"

        # Before creation, Exists must be False.
        assert writable_project.NaturalClasses.Exists(name) is False, (
            "Exists returned True for a non-existent NC"
        )

        nc = writable_project.NaturalClasses.Create(name, "qZe")
        assert writable_project.NaturalClasses.Exists(name) is True, (
            "Exists returned False for an NC that was just created"
        )

        # --- round-trip teardown (in body, tested) ---
        _delete_nc(writable_project, nc)
        assert writable_project.NaturalClasses.Find(name) is None, (
            "NC still findable after Delete - round-trip not net-zero"
        )
        assert writable_project.NaturalClasses.Exists(name) is False, (
            "Exists still True after Delete - round-trip not net-zero"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
