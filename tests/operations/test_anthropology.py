#
#   test_anthropology.py
#
#   Class: TestAnthropologyOCMCatalog
#          Phase 6c live-LCM integration tests for the new
#          AnthropologyOperations.ImportCatalog method. Mechanically
#          mirrors Phase 6b's SemanticDomainOperations.ImportCatalog,
#          but wraps the OCM (Outline of Cultural Materials) catalog
#          at <FWCodeDir>/Templates/OCM.xml via LCM's native
#          XmlList.ImportList("AnthroList", ...).
#
#   IMPORTANT -- Test shape rationale (project pollution + LCM non-idempotency):
#
#   LCM's XmlList.ImportList APPENDS items into AnthroListOA without
#   GUID-based deduplication. The Phase 6c implementation matches the
#   Phase 6b SemDom guard: refuses-by-default when the list is non-empty,
#   override with force=True. See test_semantic_domains.py for the
#   full discussion of why we deliberately don't trigger a fresh import
#   here -- earlier unguarded Phase 6b SemDom test runs already left the
#   shared test project polluted with 72+ duplicated top-level domains,
#   and we explicitly do NOT want to make the same mistake for OCM.
#
#   Additional wrinkle vs Phase 6b: AnthroListOA may or may NOT have
#   ever been populated in this project. Sena 3 ships with an empty
#   AnthroListOA by default (unlike SemanticDomainListOA, which is
#   commonly seeded). Therefore:
#
#     - We never call ImportCatalog(force=True) -- that would seed a
#       full OCM hierarchy and start a brand-new pollution cycle.
#     - The non-empty-guard tests are CONDITIONAL: if AnthroListOA is
#       empty at test time, the guard cannot be exercised live and we
#       pytest.skip rather than provoke an import.
#     - We do NOT add a canonical-GUID Find() probe like SemDom's
#       Find("1") test, because the canonical OCM items will be absent
#       from a project that has never had ImportCatalog run against it.
#     - We always do a pure static signature check, plus an accessor
#       hasattr check, so coverage is non-trivial even when the live
#       project is empty.
#
#   The runtime AnthroListOA count is printed to stdout via capsys so
#   reviewers can see the project state these tests ran against.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import sys
from unittest import mock

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


def _anthro_count(project):
    """Number of top-level items in AnthroListOA.PossibilitiesOS (or 0 if list is None)."""
    anthro_list = project.lp.AnthroListOA
    if anthro_list is None:
        return 0
    return int(anthro_list.PossibilitiesOS.Count)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnthropologyOCMCatalog:
    """
    Live-LCM coverage for AnthropologyOperations.ImportCatalog after
    the Phase 6c non-empty-list guard was added.

    These tests intentionally do NOT trigger a fresh import. See the
    module docstring for the full pollution-awareness rationale -- we
    learned the hard way during Phase 6b SemDom that calling LCM's
    XmlList.ImportList without a guard quickly accumulates duplicates,
    and we are not going to repeat that for OCM.
    """

    # -- Signature / static contract tests ------------------------------

    def test_import_catalog_signature_accepts_force_keyword(self):
        """
        Static signature check: ImportCatalog must expose a `force`
        keyword argument so callers can override the non-empty guard.
        Doesn't touch LCM at all -- pure inspect on the underlying
        function. ImportCatalog is wrapped by the @OperationsMethod
        descriptor, so we reach through .func to inspect the real
        signature (mirrors the Phase 6b SemDom approach).
        """
        from flexicon.code.Notebook.AnthropologyOperations import (
            AnthropologyOperations,
        )

        # OperationsMethod is a descriptor; the raw function lives at .func.
        descriptor = AnthropologyOperations.__dict__["ImportCatalog"]
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

    # -- Accessor wiring test -------------------------------------------

    def test_anthropology_operations_has_import_catalog(self, writable_project):
        """
        The FLExProject.Anthropology accessor must expose the new
        ImportCatalog method. Confirms the Phase 6c wiring landed on
        the right operations class and that callers can reach it via
        the documented `project.Anthropology.ImportCatalog(...)` path.
        """
        assert hasattr(writable_project, "Anthropology"), (
            "project.Anthropology accessor missing -- verify FLExProject "
            "still exposes AnthropologyOperations."
        )
        assert hasattr(writable_project.Anthropology, "ImportCatalog"), (
            "project.Anthropology.ImportCatalog missing -- Phase 6c "
            "wiring not landed on AnthropologyOperations."
        )

    # -- Conditional live-guard tests -----------------------------------
    #
    # These can only exercise the guard if AnthroListOA is already
    # non-empty. Sena 3 ships empty by default, so most of the time
    # these will skip. That's intentional -- the alternative (forcing
    # an import to seed the list) is what got Phase 6b into trouble.

    def test_import_catalog_progress_none_doesnt_npe_when_guard_fires(
        self, writable_project, capsys
    ):
        """
        Calling ImportCatalog(progress=None) on a non-empty project
        must raise FP_ParameterError (the non-empty guard), NOT a
        NullReferenceException or TypeError from the progress path.
        This confirms the guard runs BEFORE any IProgress wiring --
        equivalent to Phase 6b's SemDom progress-None test.

        Skipped if AnthroListOA is empty (the guard cannot fire in
        that state, and we won't seed via force=True).
        """
        from flexicon.code.FLExProject import FP_ParameterError

        existing_count = _anthro_count(writable_project)
        with capsys.disabled():
            print(
                f"\n[INFO] AnthroListOA top-level count at test time: "
                f"{existing_count}"
            )

        if existing_count == 0:
            pytest.skip(
                "AnthroListOA already empty; guard not exercised -- "
                "see Phase 6b for the bulk-import discussion. Run "
                "ImportCatalog(force=True) once against a throwaway "
                "project to seed and exercise the guard live."
            )

        with pytest.raises(FP_ParameterError):
            writable_project.Anthropology.ImportCatalog(progress=None)

    def test_import_catalog_raises_on_non_empty_list_without_force(
        self, writable_project, capsys
    ):
        """
        Phase 6c contract: when AnthroListOA.PossibilitiesOS is
        non-empty, ImportCatalog() (without force=True) must raise
        FP_ParameterError so callers don't accidentally append a
        duplicate OCM hierarchy.

        Skipped if AnthroListOA is empty -- we deliberately do not
        seed via force=True (see module docstring).
        """
        from flexicon.code.FLExProject import FP_ParameterError

        existing_count = _anthro_count(writable_project)
        with capsys.disabled():
            print(
                f"\n[INFO] AnthroListOA top-level count at test time: "
                f"{existing_count}"
            )

        if existing_count == 0:
            pytest.skip(
                "AnthroListOA already empty in this project; non-empty "
                "guard cannot be exercised without first seeding via "
                "force=True, which would itself start a pollution cycle. "
                "See module docstring for full rationale."
            )

        with pytest.raises(FP_ParameterError) as exc_info:
            writable_project.Anthropology.ImportCatalog()

        msg = str(exc_info.value).lower()
        assert (
            "duplicate" in msg
            or "already" in msg
            or "non-empty" in msg
            or "force" in msg
        ), (
            f"FP_ParameterError raised, but message did not mention "
            f"duplicates / already-populated / force override: "
            f"{exc_info.value!r}"
        )


class TestAnthropologyFrameCatalog:
    """
    Coverage for AnthropologyOperations.ImportFrameCatalog -- the
    OCM-Frame sibling catalog wired in to follow up on issue #29 item
    1. Same XmlList.ImportList plumbing as ImportCatalog, same
    non-empty-list guard; only the catalog file differs
    (OCM-Frame.xml vs OCM.xml). We don't trigger a live import here
    (same Sena-3 pollution rationale as ImportCatalog), but we verify
    the method exists, its signature, and that the guard fires when
    the project already has anthropology items.
    """

    def test_import_frame_catalog_method_exists(self):
        """
        ImportFrameCatalog must be on the class and expose force /
        progress kwargs. Pure static introspection; no LCM required.
        """
        from flexicon.code.Notebook.AnthropologyOperations import (
            AnthropologyOperations,
        )

        assert "ImportFrameCatalog" in AnthropologyOperations.__dict__, (
            "ImportFrameCatalog not on AnthropologyOperations class "
            "(only as inherited mixin entry); the wrapper method "
            "should be defined on the operations class so it appears "
            "in dir(project.Anthropology) and inspection."
        )

        descriptor = AnthropologyOperations.__dict__["ImportFrameCatalog"]
        underlying = getattr(descriptor, "func", descriptor)
        params = inspect.signature(underlying).parameters
        assert "force" in params, (
            f"ImportFrameCatalog missing 'force' kwarg; got: {list(params)}"
        )
        assert "progress" in params, (
            f"ImportFrameCatalog missing 'progress' kwarg; "
            f"got: {list(params)}"
        )
        assert params["force"].default is False, (
            "ImportFrameCatalog force must default to False (refuse-by-default)"
        )

    def test_import_frame_catalog_guard_fires_on_non_empty_list(
        self, writable_project
    ):
        """
        Same guard semantics as ImportCatalog: when AnthroListOA is
        non-empty, ImportFrameCatalog (without force=True) must raise
        FP_ParameterError. Skipped when the list is empty (no way to
        exercise the guard without seeding, which is a pollution risk).
        """
        from flexicon.code.FLExProject import FP_ParameterError

        if _anthro_count(writable_project) == 0:
            pytest.skip(
                "AnthroListOA empty; non-empty guard cannot be exercised."
            )

        with pytest.raises(FP_ParameterError):
            writable_project.Anthropology.ImportFrameCatalog()

    def test_import_frame_catalog_passes_correct_filename(self):
        """
        ImportFrameCatalog must pass catalog_file="OCM-Frame.xml" to
        _import_lcm_native_catalog. Tests the actual payload of the
        commit: the catalog_file kwarg routing. No live project needed.
        (issue #81)
        """
        from flexicon.code.Notebook.AnthropologyOperations import (
            AnthropologyOperations,
        )

        ops = AnthropologyOperations.__new__(AnthropologyOperations)
        with mock.patch.object(
            ops, "_import_lcm_native_catalog", return_value=None
        ) as m:
            ops.ImportFrameCatalog(progress=None, force=True)

        m.assert_called_once_with(
            progress=None, force=True, catalog_file="OCM-Frame.xml"
        )
