#
#   test_basic_ipa.py
#
#   Class: TestBasicIPACatalog
#          Phase 6d live-LCM contract tests for the new
#          PhonemeOperations.ImportCatalog method (BasicIPAInfo.xml ->
#          IPhPhoneme inventory). Mirrors the test-shape rationale of
#          tests/operations/test_semantic_domains.py and
#          tests/operations/test_anthropology.py (Phase 6b/6c).
#
#   IMPORTANT — Test shape rationale (project pollution + LCM non-idempotency):
#
#   BasicIPAInfo.xml ships 245 IPA segments. Unlike GOLDEtic /
#   eticGlossList catalogs, segments have NO per-entry GUIDs and
#   IPhPhoneme has no CatalogSourceId field, so the importer's
#   idempotency strategy is "refuse on non-empty PhonemeSet unless
#   force=True" (the Phase 6b/6c SemDom / Anthro pattern).
#
#   The shared test project ("Sena 3" or similar) is in an UNKNOWN
#   pre-state with respect to PhonemesOC and PhFeatureSystemOA:
#
#     - PhonemeSetsOS[0].PhonemesOC may be empty (stock Sena 3),
#       partially populated (test fallout), or fully populated
#       (someone ran ImportCatalog successfully before).
#     - PhFeatureSystemOA may be empty (no PhonFeats import yet) or
#       populated (someone ran PhonFeatures.ImportCatalog before).
#
#   Therefore the suite intentionally:
#
#     - Never calls ImportCatalog() with the expectation that it will
#       SUCCEED. We only assert refuse-paths (FP_ParameterError) and
#       static contract.
#     - NEVER calls ImportCatalog(force=True). That would dump 245
#       phonemes into the project and worsen pollution.
#     - Gracefully skips a refuse-path test if the corresponding
#       pre-state doesn't hold (e.g. skip the "refuses on empty
#       PhonFeats" test if PhonFeats is already populated).
#
#   To exercise a real end-to-end import, run against a fresh empty
#   project — outside this suite.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import sys

import pytest


# Every test in this module opens a real .fwdata project via the
# writable_project fixture.
pytestmark = pytest.mark.requires_live_project


# ---------------------------------------------------------------------------
# Live-LCM project fixture (mirrors test_semantic_domains.py)
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
# Pre-state helpers
# ---------------------------------------------------------------------------


def _phoneme_count(project):
    """
    Return the count of phonemes in PhonemeSetsOS[0].PhonemesOC, or 0 if
    there is no phonological data / phoneme set.
    """
    phon_data = project.lp.PhonologicalDataOA
    if not phon_data or phon_data.PhonemeSetsOS.Count == 0:
        return 0
    return phon_data.PhonemeSetsOS[0].PhonemesOC.Count


def _phon_feature_count(project):
    """
    Return the count of features in PhFeatureSystemOA.FeaturesOC, or 0
    if the feature system is not present.
    """
    fs = project.lp.PhFeatureSystemOA
    if fs is None:
        return 0
    return fs.FeaturesOC.Count


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBasicIPACatalog:
    """
    Live-LCM coverage for PhonemeOperations.ImportCatalog (Phase 6d).
    Contract / refuse-path tests only; see module docstring for the
    pollution-aware shape rationale.
    """

    # -- Static contract -------------------------------------------------

    def test_import_catalog_signature_accepts_force_keyword(self):
        """
        Static signature check: ImportCatalog must expose a `force`
        keyword argument so callers can override the non-empty-phoneme-
        set guard. Pure inspect on the underlying function — does not
        touch LCM. ImportCatalog is wrapped by the @OperationsMethod
        descriptor, so we reach through .func to inspect the real
        signature.
        """
        from flexicon.code.Grammar.PhonemeOperations import PhonemeOperations

        # OperationsMethod is a descriptor; the raw function lives at .func.
        descriptor = PhonemeOperations.__dict__["ImportCatalog"]
        underlying = getattr(descriptor, "func", descriptor)

        sig = inspect.signature(underlying)
        params = sig.parameters
        assert "force" in params, (
            f"ImportCatalog signature is missing 'force' kwarg. "
            f"Found parameters: {list(params)}"
        )
        force_param = params["force"]
        assert force_param.default is False, (
            f"`force` default must be False (refuse-by-default), "
            f"got {force_param.default!r}"
        )

    def test_phonemes_operations_has_import_catalog(self, writable_project):
        """
        Light discoverability check: PhonemeOperations on a live project
        exposes the ImportCatalog method. If a future refactor moved
        the method back to a mixin and the export wiring lapsed, this
        catches the regression before any of the refuse-path tests
        attempt to call it.
        """
        assert hasattr(writable_project.Phonemes, "ImportCatalog"), (
            "project.Phonemes does not expose ImportCatalog; check the "
            "PhonemeOperations definition and OperationsMethod wiring."
        )
        # And it must be callable (not an attribute hijacked by a
        # property descriptor that raises on access).
        assert callable(getattr(writable_project.Phonemes, "ImportCatalog")), (
            "project.Phonemes.ImportCatalog exists but is not callable."
        )

    # -- Refuse-paths (pre-state-conditional) ---------------------------

    def test_import_catalog_refuses_when_phonfeats_empty(
        self, writable_project
    ):
        """
        Phase 6d contract: if PhFeatureSystemOA.FeaturesOC is empty,
        ImportCatalog() must refuse with FP_ParameterError. The error
        message must mention PhonFeats / the remediation step so the
        caller knows to run project.PhonFeatures.ImportCatalog() first.

        Skipped if the project's PhonFeats are already populated (a
        common pollution state from earlier verification runs).
        """
        from flexicon.code.FLExProject import FP_ParameterError

        feat_count = _phon_feature_count(writable_project)
        if feat_count > 0:
            pytest.skip(
                f"PhFeatureSystemOA already populated ({feat_count} features); "
                "the 'refuse on empty PhonFeats' branch cannot be exercised "
                "against this pre-state. Run against a fresh project to "
                "cover it end-to-end."
            )

        # ImportCatalog checks the non-empty-phoneme-set guard BEFORE the
        # phonfeats-empty guard (see PhonemeOperations.ImportCatalog body).
        # If the phoneme set is already populated we'd hit the wrong guard
        # and never exercise this branch.
        phoneme_count = _phoneme_count(writable_project)
        if phoneme_count > 0:
            pytest.skip(
                f"PhonemeSetsOS[0].PhonemesOC already populated ({phoneme_count} "
                "phonemes); the non-empty-set guard fires first and masks the "
                "PhonFeats-empty branch."
            )

        with pytest.raises(FP_ParameterError) as exc_info:
            writable_project.Phonemes.ImportCatalog()

        msg = str(exc_info.value).lower()
        assert (
            "phonfeats" in msg
            or "feature" in msg
            or "phonfeatures" in msg
        ), (
            f"FP_ParameterError raised but message did not mention "
            f"the PhonFeats prerequisite: {exc_info.value!r}"
        )

    def test_import_catalog_refuses_when_phonemes_present_without_force(
        self, writable_project
    ):
        """
        Phase 6d contract: if PhonemeSetsOS[0].PhonemesOC already
        contains phonemes, ImportCatalog() (without force=True) must
        refuse with FP_ParameterError. The message must hint at
        duplicates / non-empty inventory / the force override so the
        caller has actionable remediation.

        Skipped if the phoneme set is empty (stock Sena 3 may ship
        with 0 phonemes). We never call force=True here because that
        would dump 245 phonemes into the shared test project.
        """
        from flexicon.code.FLExProject import FP_ParameterError

        phoneme_count = _phoneme_count(writable_project)
        if phoneme_count == 0:
            pytest.skip(
                "PhonemeSetsOS[0].PhonemesOC is empty; the 'refuse on "
                "non-empty set' branch cannot be exercised against this "
                "pre-state. Calling ImportCatalog() here would either "
                "actually succeed (polluting the project with 245 "
                "phonemes) or hit the PhonFeats-empty guard first."
            )

        # Need PhonFeats populated too, otherwise the PhonFeats-empty
        # guard fires first and we never reach the non-empty-set guard.
        # In that scenario we can't isolate the non-empty-set branch.
        if _phon_feature_count(writable_project) == 0:
            pytest.skip(
                "Phonemes are present but PhFeatureSystemOA is empty; "
                "the PhonFeats-empty guard runs first and masks the "
                "non-empty-set refuse-path. Cannot isolate this branch."
            )

        with pytest.raises(FP_ParameterError) as exc_info:
            writable_project.Phonemes.ImportCatalog()

        msg = str(exc_info.value).lower()
        assert (
            "duplicate" in msg
            or "already" in msg
            or "non-empty" in msg
            or "force" in msg
            or "phoneme" in msg
        ), (
            f"FP_ParameterError raised but message did not mention "
            f"duplicates / already-populated / force / phoneme: "
            f"{exc_info.value!r}"
        )

    def test_import_catalog_progress_none_safe(self, writable_project):
        """
        Calling ImportCatalog(progress=None) must NEVER produce a
        NullReferenceException, AttributeError, or TypeError from the
        progress-wiring path. Whichever refuse-path guard fires first
        (empty PhonFeats or non-empty set) must run BEFORE any
        progress-callback wiring. We accept FP_ParameterError as the
        success outcome.

        If BOTH pre-state guards are inverted (PhonFeats populated AND
        PhonemeSet empty), then a progress=None call would actually
        SUCCEED and import 245 phonemes — which we must not do. Skip
        in that case.
        """
        from flexicon.code.FLExProject import FP_ParameterError

        feat_count = _phon_feature_count(writable_project)
        phoneme_count = _phoneme_count(writable_project)
        if feat_count > 0 and phoneme_count == 0:
            pytest.skip(
                f"PhonFeats populated ({feat_count} features) AND PhonemeSet "
                f"is empty ({phoneme_count} phonemes): under this pre-state "
                "ImportCatalog() would actually succeed end-to-end, which "
                "this suite forbids (would pollute the project with 245 "
                "phonemes). Skipped to honour the no-real-import constraint."
            )

        # Otherwise: at least one guard must fire. Assert it's
        # FP_ParameterError, and crucially NOT an NPE / TypeError from
        # the progress path. We don't pin which guard fires — pre-state
        # determines that.
        with pytest.raises(FP_ParameterError):
            writable_project.Phonemes.ImportCatalog(progress=None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
