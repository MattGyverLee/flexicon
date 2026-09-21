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

    # Every test in this class opens a real .fwdata project via the
    # writable_project fixture. Kept class-scoped (not module-level) so
    # the pure-mock OcmCodes coverage below (TestOcmCodesScalarType) can
    # run under `-m "not requires_live_project"` without being swept up
    # by this mark.
    pytestmark = pytest.mark.requires_live_project

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


# ---------------------------------------------------------------------------
# Mock coverage: ICmSemanticDomain.OcmCodes is a scalar Unicode /
# System.String property, NOT an IMultiString (issue #348).
#
# GetSyncableProperties, GetOcmCodes, and Duplicate() all previously
# treated OcmCodes as a MultiUnicode (calling .get_String(handle) /
# .CopyAlternatives()), which raises on every real domain -- whether
# OcmCodes is None (the common case; ~1792/1792 domains in the reported
# project) or a set string (AttributeError either way, since a plain
# `str` has neither method).
#
# Deliberately NOT under `pytestmark = requires_live_project`: these
# tests use plain-Python fakes with `OcmCodes` modeled as a bare
# `str`/`None` attribute, never as a Mock exposing `get_String` --
# a mock offering `get_String` would pass against the broken
# MultiUnicode-shaped code and is exactly the failure mode that let
# issue #318's mock suite go green against production code that raised
# on every real database. No SIL.LCModel/live project needed; run with:
#     python -m pytest -m "not requires_live_project" \
#         tests/operations/test_semantic_domains.py -q
# ---------------------------------------------------------------------------


class _FakeOcmDomain:
    """
    Minimal ICmSemanticDomain stand-in. OcmCodes is a bare attribute
    (str or None) -- exactly the pythonnet-boundary shape of a scalar
    Unicode / System.String property, never an object with get_String()
    or CopyAlternatives().

    No ClassName attribute, so SemanticDomainOperations.__ResolveObject
    falls through to `return domain_or_hvo` unchanged (it only tries to
    cast when ClassName == "CmSemanticDomain").
    """

    def __init__(self, ocm_codes=None):
        self.OcmCodes = ocm_codes


class _FakeProjectForOcmCodes:
    """Bare-minimum FLExProject stand-in for read-only OcmCodes access."""

    def __init__(self, write_enabled=True):
        self.writeEnabled = write_enabled


class TestOcmCodesScalarType:
    """
    Pure-mock regression coverage for issue #348: OcmCodes must be read
    and written as a plain scalar string at all three call sites, never
    via MultiUnicode-only APIs (get_String / CopyAlternatives).
    """

    # -- GetSyncableProperties --------------------------------------------

    def test_get_syncable_properties_unset_ocm_codes_yields_empty_string(self):
        """
        An unset (None) OcmCodes must surface as "" in the props dict
        without raising -- this is the exact shape of the reported bug
        (1792/1792 domains failing because `.get_String()` was called
        on None).
        """
        from flexicon.code.Lexicon.SemanticDomainOperations import (
            SemanticDomainOperations,
        )

        project = _FakeProjectForOcmCodes()
        ops = SemanticDomainOperations(project)
        domain = _FakeOcmDomain(ocm_codes=None)

        props = ops.GetSyncableProperties(domain)

        assert props["OcmCodes"] == ""

    def test_get_syncable_properties_set_ocm_codes_reads_back_the_string(self):
        """A populated OcmCodes value must come back verbatim."""
        from flexicon.code.Lexicon.SemanticDomainOperations import (
            SemanticDomainOperations,
        )

        project = _FakeProjectForOcmCodes()
        ops = SemanticDomainOperations(project)
        domain = _FakeOcmDomain(ocm_codes="484")

        props = ops.GetSyncableProperties(domain)

        assert props["OcmCodes"] == "484"

    def test_get_syncable_properties_never_emits_none_for_ocm_codes(self):
        """
        BaseOperations._apply_props_loop skips None values outright, so
        emitting None here would silently drop the field on the apply
        side. Belt-and-suspenders check that the key is always a str.
        """
        from flexicon.code.Lexicon.SemanticDomainOperations import (
            SemanticDomainOperations,
        )

        project = _FakeProjectForOcmCodes()
        ops = SemanticDomainOperations(project)
        domain = _FakeOcmDomain(ocm_codes=None)

        props = ops.GetSyncableProperties(domain)

        assert props["OcmCodes"] is not None
        assert isinstance(props["OcmCodes"], str)

    # -- GetOcmCodes -------------------------------------------------------

    def test_get_ocm_codes_unset_returns_empty_string(self):
        from flexicon.code.Lexicon.SemanticDomainOperations import (
            SemanticDomainOperations,
        )

        project = _FakeProjectForOcmCodes()
        ops = SemanticDomainOperations(project)
        domain = _FakeOcmDomain(ocm_codes=None)

        assert ops.GetOcmCodes(domain) == ""

    def test_get_ocm_codes_set_value_reads_back_correctly(self):
        from flexicon.code.Lexicon.SemanticDomainOperations import (
            SemanticDomainOperations,
        )

        project = _FakeProjectForOcmCodes()
        ops = SemanticDomainOperations(project)
        domain = _FakeOcmDomain(ocm_codes="484")

        assert ops.GetOcmCodes(domain) == "484"

    # -- Duplicate ----------------------------------------------------------

    class _FakeMultiStringField:
        """
        Stand-in for the genuinely-multistring fields Duplicate() also
        copies (Name, Description, Abbreviation, Questions) -- these DO
        support CopyAlternatives(), unlike OcmCodes.
        """

        def CopyAlternatives(self, other):
            pass

    class _FakeDuplicateTarget:
        """factory.Create() return value: a fresh domain with real
        MultiString-shaped fields for Name/Description/Abbreviation/
        Questions, and a plain scalar OcmCodes attribute."""

        def __init__(self):
            self.Name = TestOcmCodesScalarType._FakeMultiStringField()
            self.Description = TestOcmCodesScalarType._FakeMultiStringField()
            self.Abbreviation = TestOcmCodesScalarType._FakeMultiStringField()
            self.Questions = TestOcmCodesScalarType._FakeMultiStringField()
            self.OcmCodes = None
            self.SubPossibilitiesOS = []

    class _FakeDuplicateSource(_FakeOcmDomain):
        def __init__(self, ocm_codes=None):
            super().__init__(ocm_codes=ocm_codes)
            self.Name = TestOcmCodesScalarType._FakeMultiStringField()
            self.Description = TestOcmCodesScalarType._FakeMultiStringField()
            self.Abbreviation = TestOcmCodesScalarType._FakeMultiStringField()
            self.Questions = TestOcmCodesScalarType._FakeMultiStringField()
            self.SubPossibilitiesOS = []
            self.OccurrencesRS = []

    class _FakePossibilitiesOS(list):
        def IndexOf(self, item):
            return self.index(item)

        def Insert(self, index, item):
            self.insert(index, item)

        def Add(self, item):
            self.append(item)

    def _make_duplicate_ops(self, monkeypatch, duplicate_target):
        """
        Build a SemanticDomainOperations instance wired just enough to
        drive the Duplicate() body: write-enabled, a no-op transaction
        context manager (transaction plumbing is not what's under test
        here), no parent (top-level insert path), and a factory that
        hands back `duplicate_target`.
        """
        import contextlib

        from flexicon.code.Lexicon.SemanticDomainOperations import (
            SemanticDomainOperations,
        )

        class _FakeFactory:
            def __init__(self, target):
                self._target = target

            def Create(self):
                return self._target

        class _FakeServiceLocator:
            def __init__(self, factory):
                self._factory = factory

            def GetService(self, iface):
                return self._factory

        class _FakeLp:
            def __init__(self):
                self.SemanticDomainListOA = self

            PossibilitiesOS = None  # set below

        class _FakeInnerProject:
            def __init__(self, factory):
                self.ServiceLocator = _FakeServiceLocator(factory)

        class _FakeProject:
            def __init__(self, factory):
                self.writeEnabled = True
                self.project = _FakeInnerProject(factory)
                self.lp = _FakeLp()
                self.lp.PossibilitiesOS = (
                    TestOcmCodesScalarType._FakePossibilitiesOS()
                )

        factory = _FakeFactory(duplicate_target)
        project = _FakeProject(factory)
        ops = SemanticDomainOperations(project)

        monkeypatch.setattr(
            ops, "_TransactionCM", lambda label: contextlib.nullcontext()
        )
        monkeypatch.setattr(ops, "GetParent", lambda domain: None)

        return ops

    def test_duplicate_copies_a_set_ocm_codes_value(self, monkeypatch):
        target = self._FakeDuplicateTarget()
        ops = self._make_duplicate_ops(monkeypatch, target)
        source = self._FakeDuplicateSource(ocm_codes="484")

        result = ops.Duplicate(source, insert_after=False, deep=False)

        assert result.OcmCodes == "484"

    def test_duplicate_tolerates_an_unset_ocm_codes_value(self, monkeypatch):
        target = self._FakeDuplicateTarget()
        ops = self._make_duplicate_ops(monkeypatch, target)
        source = self._FakeDuplicateSource(ocm_codes=None)

        # Must not raise (the pre-fix CopyAlternatives(None) call did).
        result = ops.Duplicate(source, insert_after=False, deep=False)

        assert result.OcmCodes == ""
