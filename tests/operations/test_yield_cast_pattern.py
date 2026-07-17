#
#   test_yield_cast_pattern.py
#
#   Class: TestYieldCastStatic / TestYieldCastLive / TestProjectSettingsAccessors
#          Regression coverage for the possibility-list "cast-on-yield" gap
#          across Grammar, Lexicon, and Notebook operations.
#
#   Bug class (closes #220, fixed by 92762fa "cast possibility-list items to
#   concrete LCM types on yield"):
#     - Iterating a `PossibilitiesOS` / `SubPossibilitiesOS` collection in
#       pythonnet yields items typed as the collection's declared element
#       interface (`ICmPossibility`), even when every element is actually a
#       more specific concrete subtype (`IMoInflClass`, `ICmSemanticDomain`,
#       `ICmLocation`, ...).
#     - Without an explicit re-cast (e.g. `IMoInflClass(ic)`), pythonnet's
#       static interface dispatch means the yielded Python wrapper only
#       exposes members declared on the base interface. Concrete-only
#       members (e.g. `ICmSemanticDomain.OcmCodes`, `ICmLocation.Elevation`)
#       raise `AttributeError` even though the underlying .NET object
#       implements them, and `type(item)` reports the base interface rather
#       than the concrete one.
#     - This is Category 5 in docs/API_ISSUES_CATEGORIZED.md.
#
#   The fix (92762fa) re-casts the loop variable to its concrete interface
#   before it is yielded/returned in:
#     - Grammar/InflectionFeatureOperations.InflectionClassGetAll
#           -> yield IMoInflClass(ic)
#     - Lexicon/SemanticDomainOperations.GetSubdomains
#           -> ICmSemanticDomain(child) (fast path + recursive walk)
#     - Notebook/LocationOperations.GetSublocations
#           -> ICmLocation(child) (fast path + recursive walk)
#   and adds LCM-backed accessors to System/ProjectSettingsOperations
#   (GetProjectGuid, GetProjectDescription, GetExternalLink,
#   GetAnalysisWritingSystem, GetVernacularWritingSystem) that were missing
#   entirely before.
#
#   This file locks the PATTERN, not just specific instances, by:
#
#     1. Static checks that each affected method's source routes the loop
#        variable through the concrete-type cast constructor before
#        yielding/returning it, and that the previously-broken bare
#        `yield <loop var>` / bare `.append(<loop var>)` shape is gone.
#        These run without LCM/FieldWorks installed.
#
#     2. A pattern-level guard, parametrised across all three affected
#        enumerator sites, asserting that `type(item)` is never the bare
#        base interface (`ICmPossibility`) for objects that the API claims
#        are a more specific subtype.
#
#     3. Live behavioural checks against a writable FLEx project verifying
#        every yielded item exposes concrete-type-ONLY members without the
#        caller having to re-cast, plus smoke tests for the new
#        ProjectSettingsOperations accessors. These skip when SIL.LCModel
#        isn't loaded. All live checks here are read-only (enumerate +
#        attribute access), so there is no `-restore` concern.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import sys
import textwrap

import pytest


# ---------------------------------------------------------------------------
# Live-LCM project fixture (mirrors the convention in
# tests/operations/test_owner_cast_pattern.py / test_anthropology.py /
# test_const_chart_marker.py).
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
    """Module-scoped write-enabled FLExProject fixture; skips when LCM unavailable."""
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
# Static source-level pattern coverage
#
# These tests do NOT require LCM. They read the source of each affected
# Operations method and verify the canonical fix is in place: the loop
# variable is routed through the concrete-type cast constructor
# (`IMoInflClass(...)`, `ICmSemanticDomain(...)`, `ICmLocation(...)`)
# before being yielded/returned, and the previously-broken bare
# `yield <var>` shape is gone.
# ---------------------------------------------------------------------------


def _operation_source(import_path, attr_chain):
    """
    Import a module then walk a dotted attr chain to a method's underlying
    function, and return its source text. The method is wrapped in
    OperationsMethod (and possibly wrap_enumerable) descriptors; we access
    the class via __dict__ so __get__ does not synthesise the class-method
    wrapper, then peel back to the raw function.
    """
    import importlib

    module = importlib.import_module(import_path)
    cls = getattr(module, attr_chain[0])
    obj = cls
    for part in attr_chain[1:]:
        if isinstance(obj, type):
            try:
                obj = obj.__dict__[part]
            except KeyError:
                for base in obj.__mro__[1:]:
                    if part in base.__dict__:
                        obj = base.__dict__[part]
                        break
                else:
                    raise AttributeError(
                        f"{obj.__name__} has no attribute {part}"
                    )
        else:
            obj = getattr(obj, part)

    # Unwrap descriptor layers (OperationsMethod, wrap_enumerable, etc.)
    seen = set()
    while True:
        oid = id(obj)
        if oid in seen:
            break
        seen.add(oid)
        if hasattr(obj, "func") and not inspect.isfunction(obj):
            obj = obj.func
            continue
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
            continue
        break

    return inspect.getsource(obj)


# (label, import_path, attr_chain, concrete_type_name, cast_expr, min_count)
#
# `cast_expr` is the substring that must appear in the method body -- the
# concrete-type constructor call wrapping the loop variable. `min_count`
# guards against a partial fix (e.g. only the fast path cast, but not the
# recursive-walk branch).
_SITES = [
    (
        "InflectionFeatureOperations.InflectionClassGetAll",
        "flexlibs2.code.Grammar.InflectionFeatureOperations",
        ("InflectionFeatureOperations", "InflectionClassGetAll"),
        "IMoInflClass",
        "IMoInflClass(",
        1,
    ),
    (
        "SemanticDomainOperations.GetSubdomains",
        "flexlibs2.code.Lexicon.SemanticDomainOperations",
        ("SemanticDomainOperations", "GetSubdomains"),
        "ICmSemanticDomain",
        "ICmSemanticDomain(",
        2,  # fast path (list comprehension) + recursive walk() body
    ),
    (
        "LocationOperations.GetSublocations",
        "flexlibs2.code.Notebook.LocationOperations",
        ("LocationOperations", "GetSublocations"),
        "ICmLocation",
        "ICmLocation(",
        2,  # fast path (list comprehension) + recursive walk() body
    ),
]


class TestYieldCastStatic:
    """
    Static pattern locks. Run without LCM. Verify that every affected
    enumerator routes its loop variable through the concrete-type cast
    constructor before yielding/returning it. These checks describe the
    bug *class*, not one canonical line, so they tolerate future
    refactors that keep the cast but change surrounding code.
    """

    @pytest.mark.parametrize(
        "label,import_path,attr_chain,concrete_type,cast_expr,min_count", _SITES
    )
    def test_casts_before_yield(
        self, label, import_path, attr_chain, concrete_type, cast_expr, min_count
    ):
        src = _operation_source(import_path, attr_chain)
        msg_prefix = f"{label}:\n{textwrap.indent(src, '    ')}\n"
        count = src.count(cast_expr)
        assert count >= min_count, (
            f"{msg_prefix}Expected `{cast_expr}` to appear at least "
            f"{min_count} time(s) (fast path + recursive walk, where "
            f"applicable). Found {count}. This is the cast-on-yield fix "
            f"for issue #220 -- items from a PossibilitiesOS/"
            f"SubPossibilitiesOS collection must be re-cast to "
            f"`{concrete_type}` before being handed to the caller."
        )

    def test_inflection_class_no_bare_yield(self):
        """
        InflectionClassGetAll previously did `yield ic` directly off the
        PossibilitiesOS loop variable. That bare shape is the bug
        signature for issue #220.
        """
        src = _operation_source(
            "flexlibs2.code.Grammar.InflectionFeatureOperations",
            ("InflectionFeatureOperations", "InflectionClassGetAll"),
        )
        assert "yield ic\n" not in src, (
            "InflectionClassGetAll still contains a bare `yield ic` "
            "(uncast base-interface item). Issue #220 requires "
            "`yield IMoInflClass(ic)`."
        )

    def test_semantic_domain_no_bare_collection_pass_through(self):
        """
        GetSubdomains previously returned `list(domain.SubPossibilitiesOS)`
        (fast path) and appended the raw loop variable directly (recursive
        path) without casting. Both bare shapes are the bug signature.
        """
        src = _operation_source(
            "flexlibs2.code.Lexicon.SemanticDomainOperations",
            ("SemanticDomainOperations", "GetSubdomains"),
        )
        assert "return list(domain.SubPossibilitiesOS)" not in src, (
            "GetSubdomains still returns the raw SubPossibilitiesOS "
            "collection uncast -- see issue #220."
        )
        assert "for child in collection:\n" not in src, (
            "GetSubdomains' recursive walk() still uses the pre-fix "
            "`for child in collection:` shape, where `child` was the "
            "raw uncast loop variable appended directly. After the fix "
            "the raw loop variable is named `raw` and cast into `child` "
            "via `ICmSemanticDomain(raw)` before use."
        )

    def test_location_no_bare_collection_pass_through(self):
        """
        GetSublocations previously returned
        `list(location.SubPossibilitiesOS)` (fast path) and appended the
        raw loop variable directly (recursive path) without casting.
        """
        src = _operation_source(
            "flexlibs2.code.Notebook.LocationOperations",
            ("LocationOperations", "GetSublocations"),
        )
        assert "return list(location.SubPossibilitiesOS)" not in src, (
            "GetSublocations still returns the raw SubPossibilitiesOS "
            "collection uncast -- see issue #220."
        )
        assert "for child in collection:\n" not in src, (
            "GetSublocations' recursive walk() still uses the pre-fix "
            "`for child in collection:` shape, where `child` was the "
            "raw uncast loop variable appended directly. After the fix "
            "the raw loop variable is named `raw` and cast into `child` "
            "via `ICmLocation(raw)` before use."
        )


# ---------------------------------------------------------------------------
# Live behavioural coverage
#
# These verify the OUTCOME we care about: every item yielded/returned from
# the three affected enumerators is a *concrete* object -- not the bare
# base interface -- and exposes concrete-type-ONLY members without the
# caller having to re-cast. All reads here are read-only (no writes), so
# there is no `-restore` concern.
# ---------------------------------------------------------------------------


@pytest.mark.requires_live_project
class TestYieldCastLive:
    def test_inflection_class_get_all_yields_concrete_type(self, writable_project):
        """
        Pattern-level guard: InflectionClassGetAll must never yield a bare
        ICmPossibility. `type(item)` must be the concrete `IMoInflClass`
        interface, not the base interface the collection is declared over.
        """
        from SIL.LCModel import ICmPossibility, IMoInflClass

        items = list(writable_project.InflectionFeatures.InflectionClassGetAll())
        if not items:
            pytest.skip("Project has no inflection classes to enumerate")

        for item in items:
            assert type(item) is not ICmPossibility, (
                "InflectionClassGetAll yielded a bare ICmPossibility -- "
                "the cast-on-yield fix for issue #220 has regressed."
            )
            assert type(item) is IMoInflClass, (
                f"InflectionClassGetAll yielded {type(item)!r}; expected "
                f"the concrete IMoInflClass interface."
            )
            # Concrete-only sanity: accessing .Name must succeed without
            # the caller re-casting (would already work on ICmPossibility,
            # but confirms the wrapper is fully usable post-cast).
            assert hasattr(item, "Name")

    def test_get_subdomains_yields_concrete_type_and_ocm_codes(self, writable_project):
        """
        Pattern-level guard + concrete-member access: every subdomain
        returned by GetSubdomains (both recursive and direct-children
        modes) must be `ICmSemanticDomain`, not bare `ICmPossibility`, and
        must expose `OcmCodes` (a concrete-only member) directly.
        """
        from SIL.LCModel import ICmPossibility, ICmSemanticDomain

        domains = list(writable_project.SemanticDomains.GetAll())
        top = None
        for d in domains:
            if writable_project.SemanticDomains.GetSubdomains(d, recursive=False):
                top = d
                break

        if top is None:
            pytest.skip("No semantic domain with subdomains available")

        for recursive in (False, True):
            subs = writable_project.SemanticDomains.GetSubdomains(top, recursive=recursive)
            assert subs, "Expected at least one subdomain"
            for sub in subs:
                assert type(sub) is not ICmPossibility, (
                    "GetSubdomains yielded a bare ICmPossibility -- the "
                    "cast-on-yield fix for issue #220 has regressed "
                    f"(recursive={recursive})."
                )
                assert type(sub) is ICmSemanticDomain, (
                    f"GetSubdomains yielded {type(sub)!r} (recursive="
                    f"{recursive}); expected ICmSemanticDomain."
                )
                # Concrete-only member access, no re-cast by the caller.
                assert hasattr(sub, "OcmCodes"), (
                    "Subdomain item does not expose OcmCodes without "
                    "re-casting -- ICmSemanticDomain cast has regressed."
                )

    def test_get_sublocations_yields_concrete_type_and_elevation(self, writable_project):
        """
        Pattern-level guard + concrete-member access: every sublocation
        returned by GetSublocations (both recursive and direct-children
        modes) must be `ICmLocation`, not bare `ICmPossibility`, and must
        expose `Elevation` (a concrete-only member) directly.
        """
        from SIL.LCModel import ICmPossibility, ICmLocation

        locations = list(writable_project.Location.GetAll())
        top = None
        for loc in locations:
            if writable_project.Location.GetSublocations(loc, recursive=False):
                top = loc
                break

        if top is None:
            pytest.skip("No location with sublocations available")

        for recursive in (False, True):
            subs = writable_project.Location.GetSublocations(top, recursive=recursive)
            assert subs, "Expected at least one sublocation"
            for sub in subs:
                assert type(sub) is not ICmPossibility, (
                    "GetSublocations yielded a bare ICmPossibility -- the "
                    "cast-on-yield fix for issue #220 has regressed "
                    f"(recursive={recursive})."
                )
                assert type(sub) is ICmLocation, (
                    f"GetSublocations yielded {type(sub)!r} (recursive="
                    f"{recursive}); expected ICmLocation."
                )
                # Concrete-only member access, no re-cast by the caller.
                assert hasattr(sub, "Elevation"), (
                    "Sublocation item does not expose Elevation without "
                    "re-casting -- ICmLocation cast has regressed."
                )


# ---------------------------------------------------------------------------
# ProjectSettingsOperations new accessors (added alongside the yield-cast
# fix in the same commit -- 92762fa). These are simple LCM-backed reads,
# not cast-on-yield sites, but issue #220 groups them with the same
# regression risk (methods added without any test coverage at all).
# ---------------------------------------------------------------------------


class TestProjectSettingsAccessorsStatic:
    """Static source checks: each new accessor must exist and delegate
    to (or read directly from) the expected LCM-backed source."""

    def _method_source(self, name):
        from flexlibs2.code.System.ProjectSettingsOperations import (
            ProjectSettingsOperations,
        )

        assert hasattr(ProjectSettingsOperations, name), (
            f"ProjectSettingsOperations.{name} is missing -- this accessor "
            f"was added by 92762fa for issue #220."
        )
        return _operation_source(
            "flexlibs2.code.System.ProjectSettingsOperations",
            ("ProjectSettingsOperations", name),
        )

    def test_get_project_guid_reads_lp_guid(self):
        src = self._method_source("GetProjectGuid")
        assert "self.project.lp.Guid" in src

    def test_get_project_description_delegates_to_get_description(self):
        src = self._method_source("GetProjectDescription")
        assert "self.GetDescription" in src

    def test_get_external_link_delegates_to_get_ext_link_root_dir(self):
        src = self._method_source("GetExternalLink")
        assert "self.GetExtLinkRootDir" in src

    def test_get_analysis_writing_system_reads_lp_default(self):
        src = self._method_source("GetAnalysisWritingSystem")
        assert "DefaultAnalysisWritingSystem" in src

    def test_get_vernacular_writing_system_reads_lp_default(self):
        src = self._method_source("GetVernacularWritingSystem")
        assert "DefaultVernacularWritingSystem" in src


@pytest.mark.requires_live_project
class TestProjectSettingsAccessorsLive:
    def test_get_project_guid_returns_nonempty_string(self, writable_project):
        guid = writable_project.ProjectSettings.GetProjectGuid()
        assert isinstance(guid, str) and guid, (
            "GetProjectGuid should return a non-empty GUID string."
        )

    def test_get_project_description_matches_get_description(self, writable_project):
        assert (
            writable_project.ProjectSettings.GetProjectDescription()
            == writable_project.ProjectSettings.GetDescription()
        )

    def test_get_external_link_matches_get_ext_link_root_dir(self, writable_project):
        assert (
            writable_project.ProjectSettings.GetExternalLink()
            == writable_project.ProjectSettings.GetExtLinkRootDir()
        )

    def test_get_analysis_writing_system_returns_ws_with_id(self, writable_project):
        ws = writable_project.ProjectSettings.GetAnalysisWritingSystem()
        assert ws is not None and hasattr(ws, "Id")

    def test_get_vernacular_writing_system_returns_ws_with_id(self, writable_project):
        ws = writable_project.ProjectSettings.GetVernacularWritingSystem()
        assert ws is not None and hasattr(ws, "Id")
