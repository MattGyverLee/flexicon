#
#   test_semantic_domains.py
#
#   Class: TestSemanticDomainsCatalog
#          Phase 6b live-LCM integration tests for the new
#          SemanticDomainOperations.ImportCatalog method. Unlike
#          POS / PhonFeatures / InflectionFeatures (which use the etic
#          CatalogEntry parser), the semantic-domain catalog is consumed
#          natively by LCM's XmlList.ImportList.
#
#   IMPORTANT — Test shape rationale (project pollution + LCM non-idempotency):
#
#   LCM's XmlList.ImportList APPENDS the full SemDom hierarchy on every
#   call without GUID-based deduplication. Earlier unguarded test runs
#   left the shared test project ("Sena 3" or similar) with dozens of
#   duplicated top-level domains. The Programmer's Phase 6b fix added a
#   refuses-by-default guard: ImportCatalog raises FP_ParameterError if
#   SemanticDomainListOA.PossibilitiesOS is non-empty, unless force=True.
#
#   Because the project is permanently polluted and we cannot cheaply
#   reset it, these tests do NOT exercise a live re-import:
#
#     - We never call ImportCatalog(force=True) — that would add another
#       full ~1700-domain hierarchy and worsen the pollution.
#     - We assert the new contract directly (raises without force) and
#       verify the catalog DID land at some point by Find()-ing the
#       canonical "1" (Universe) and "1.1" (Sky) GUIDs left over from
#       earlier successful imports.
#     - We also do a static signature check that `force` is a real kwarg.
#
#   To exercise a real import end-to-end, run against a fresh empty
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
# Constants — canonical GUIDs from SemDom.xml
# ---------------------------------------------------------------------------

# Top-level "Universe, creation" domain (number "1").
UNIVERSE_GUID = "63403699-07C1-43F3-A47C-069D6E4316E5".lower()

# First subdomain of Universe: "Sky" (number "1.1").
SKY_GUID = "999581C4-1611-4ACB-AE1B-5E6C1DFE6F0C".lower()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSemanticDomainsCatalog:
    """
    Live-LCM coverage for SemanticDomainOperations.ImportCatalog
    after the Phase 6b non-empty-list guard was added.

    These tests intentionally do NOT trigger a fresh import (the shared
    test project is already polluted with duplicates from earlier
    unguarded runs). See the module docstring for full rationale.
    """

    # -- New-contract tests ---------------------------------------------

    def test_import_catalog_raises_on_non_empty_list_without_force(
        self, writable_project
    ):
        """
        Phase 6b contract: when SemanticDomainListOA.PossibilitiesOS is
        non-empty, ImportCatalog() (without force=True) must raise
        FP_ParameterError so callers don't accidentally append a
        duplicate hierarchy. The shared test project is known to be
        non-empty here.
        """
        from flexicon.code.FLExProject import FP_ParameterError

        sd_list = writable_project.lp.SemanticDomainListOA
        assert sd_list is not None, "SemanticDomainListOA is None"
        assert sd_list.PossibilitiesOS.Count > 0, (
            "Test precondition: project must already contain some "
            "semantic domains (from prior unguarded imports) for the "
            "non-empty-guard test to be meaningful. Found 0 — run "
            "ImportCatalog once against a fresh project to seed it, "
            "then re-run."
        )

        with pytest.raises(FP_ParameterError) as exc_info:
            writable_project.SemanticDomains.ImportCatalog()

        msg = str(exc_info.value).lower()
        assert (
            "duplicate" in msg or "already" in msg or "non-empty" in msg
            or "force" in msg
        ), (
            f"FP_ParameterError raised, but message did not mention "
            f"duplicates / already-populated / force override: {exc_info.value!r}"
        )

    def test_import_catalog_progress_none_doesnt_npe(self, writable_project):
        """
        Calling ImportCatalog(progress=None) on a non-empty project must
        raise FP_ParameterError (the non-empty guard), NOT a
        NullReferenceException or TypeError from the progress path. This
        confirms the guard runs BEFORE any IProgress wiring.
        """
        from flexicon.code.FLExProject import FP_ParameterError

        with pytest.raises(FP_ParameterError):
            writable_project.SemanticDomains.ImportCatalog(progress=None)

    # -- Signature / static contract tests ------------------------------

    def test_import_catalog_signature_accepts_force_keyword(self):
        """
        Static signature check: ImportCatalog must expose a `force`
        keyword argument so callers can override the non-empty guard.
        Doesn't touch LCM at all — pure inspect on the underlying
        function. ImportCatalog is wrapped by the @OperationsMethod
        descriptor, so we reach through .func to inspect the real
        signature.
        """
        from flexicon.code.Lexicon.SemanticDomainOperations import (
            SemanticDomainOperations,
        )

        # OperationsMethod is a descriptor; the raw function lives at .func.
        descriptor = SemanticDomainOperations.__dict__["ImportCatalog"]
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

    # -- Catalog-landed-at-some-point tests (read-only) -----------------

    def test_import_catalog_finds_canonical_universe_domain(
        self, writable_project
    ):
        """
        Read-only: Find("1") must locate the canonical "Universe,
        creation" top-level domain with the catalog GUID. This confirms
        that ImportCatalog did successfully land the catalog at some
        point in this project's history (the wiring works), without
        triggering a fresh import here.

        If the project is polluted with duplicates, Find() should still
        return the first canonical-GUID match.
        """
        universe = writable_project.SemanticDomains.Find("1")
        assert universe is not None, (
            "Find('1') returned None — no top-level Universe domain "
            "exists in this project. Has ImportCatalog ever been run "
            "successfully against this project?"
        )

        actual_guid = str(universe.Guid).lower()
        assert actual_guid == UNIVERSE_GUID, (
            f"Universe domain GUID {actual_guid!r} != canonical "
            f"{UNIVERSE_GUID!r}. The Find('1') match doesn't trace back "
            f"to SemDom.xml — possibly a hand-created domain numbered '1'."
        )

    def test_import_catalog_finds_canonical_sky_subdomain(
        self, writable_project
    ):
        """
        Read-only: Find("1.1") must locate the canonical "Sky"
        subdomain. Confirms the SubPossibilities hierarchy landed
        correctly during a prior successful import.
        """
        sky = writable_project.SemanticDomains.Find("1.1")
        assert sky is not None, (
            "Find('1.1') returned None — Sky subdomain missing. "
            "SubPossibilities hierarchy may have failed to import."
        )

        actual_guid = str(sky.Guid).lower()
        assert actual_guid == SKY_GUID, (
            f"Sky subdomain GUID {actual_guid!r} != canonical "
            f"{SKY_GUID!r}."
        )
