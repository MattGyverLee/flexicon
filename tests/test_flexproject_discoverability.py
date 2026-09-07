#
#   test_flexproject_discoverability.py
#
#   Class: TestFLExProjectDiscoverability
#          Smoke tests for the Phase 1 discoverability additions on
#          FLExProject: the `Cache` property, `GetService(interface_type)`
#          method, and the writing-system handle helpers
#          (`GetDefaultVernacularWSHandle`, `GetDefaultAnalysisWSHandle`).
#
#          Also acts as a regression guard for the existing
#          tuple-returning `GetDefaultVernacularWS` / `GetDefaultAnalysisWS`
#          methods (must still return `(language_tag, display_name)`).
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
# live_project fixture.
pytestmark = pytest.mark.requires_live_project


# ---------------------------------------------------------------------------
# Helpers for live-LCM tests
# ---------------------------------------------------------------------------

# Candidate FieldWorks project names to try, in priority order. The first one
# that opens successfully is used for the entire test session.
_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_project():
    """
    Attempt to open one of the standard test projects read-only.

    Returns the open FLExProject instance on success, or None if no FieldWorks
    project is reachable in this environment. Caller is responsible for
    CloseProject() on the returned object.

    NOTE: A sandbox .fwbackup fallback was tried and rejected -- opening
    the sandbox read-only triggers a modal "Unable to create writing
    system: en" dialog from liblcm, freezing the suite. These tests
    require a real installed candidate project; if none is present,
    they correctly skip.
    """
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception:
        return None

    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=False)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def live_project():
    """
    Module-scoped fixture providing an open, read-only FLExProject.

    Skips dependent tests if SIL.LCModel isn't loaded or no candidate
    FieldWorks project can be opened. Matches the skip style used in
    `tests/test_lcm_api_real.py`.
    """
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")

    project = _try_open_project()
    if project is None:
        pytest.skip(
            "No FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )

    yield project

    try:
        project.CloseProject()
    except Exception:
        # Best-effort cleanup; don't mask test failures with teardown noise.
        pass


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestFLExProjectDiscoverability:
    """
    Smoke tests covering the Phase 1 FLExProject discoverability surfaces:

      * `Cache` property                 -> underlying LcmCache
      * `GetService(interface_type)`     -> ServiceLocator.GetService delegate
      * `GetDefaultVernacularWSHandle()` -> int handle
      * `GetDefaultAnalysisWSHandle()`   -> int handle

    Plus a regression guard for the existing tuple-returning methods.
    """

    # ----- Static introspection tests (always run; no LCM required) --------

    def test_cache_property_appears_in_dir(self):
        """
        Cache must be exposed as a real `property` descriptor on the class so
        that `dir(FLExProject)` and IDE auto-complete surface it.
        """
        from flexicon.code.FLExProject import FLExProject

        assert "Cache" in dir(FLExProject), (
            "Cache property is not visible via dir(FLExProject)"
        )

        descriptor = inspect.getattr_static(FLExProject, "Cache")
        assert isinstance(descriptor, property), (
            f"FLExProject.Cache must be a property descriptor, "
            f"got {type(descriptor).__name__}"
        )

    def test_new_methods_visible_via_dir(self):
        """
        All four Phase 1 additions must be visible on the class so that
        `dir(project)` and tab-completion surface them. This is the core
        discoverability guarantee.
        """
        from flexicon.code.FLExProject import FLExProject

        names = dir(FLExProject)
        expected = [
            "Cache",
            "GetService",
            "GetDefaultVernacularWSHandle",
            "GetDefaultAnalysisWSHandle",
        ]
        missing = [n for n in expected if n not in names]
        assert not missing, f"Missing from dir(FLExProject): {missing}"

        # GetService must be a callable (function/method), not a property.
        getservice = inspect.getattr_static(FLExProject, "GetService")
        assert callable(getservice), "GetService must be callable"
        assert not isinstance(getservice, property), (
            "GetService must be a method, not a property"
        )

        # Verify GetService signature accepts a single positional arg
        # (besides self).
        sig = inspect.signature(getservice)
        params = [
            p for p in sig.parameters.values()
            if p.name != "self"
        ]
        assert len(params) == 1, (
            f"GetService should take one parameter besides self, "
            f"got {len(params)}: {[p.name for p in params]}"
        )

        # Both *WSHandle methods are plain methods too.
        for method_name in (
            "GetDefaultVernacularWSHandle",
            "GetDefaultAnalysisWSHandle",
        ):
            method = inspect.getattr_static(FLExProject, method_name)
            assert callable(method), f"{method_name} must be callable"
            assert not isinstance(method, property), (
                f"{method_name} must be a method, not a property"
            )

    # ----- Live-LCM behavioral tests (skipped without a real project) ------

    def test_cache_property_returns_underlying_lcm_cache(self, live_project):
        """
        FLExProject.Cache must return the same object as the private
        `project` attribute (i.e. the underlying LcmCache).
        """
        cache = live_project.Cache
        assert cache is not None, "Cache returned None"
        assert cache is live_project.project, (
            "Cache must return the same instance as FLExProject.project"
        )
        # Sanity: the LcmCache exposes ServiceLocator.
        assert hasattr(cache, "ServiceLocator"), (
            "Returned Cache does not look like an LcmCache "
            "(no ServiceLocator attribute)"
        )

    def test_getservice_routes_through_servicelocator(self, live_project):
        """
        GetService(interface_type) must delegate to
        `project.ServiceLocator.GetService(interface_type)` and return a
        non-None instance for a well-known interface.

        Note: pythonnet creates a fresh Python wrapper around the same CLR
        instance on each access, so Python `is` will not work for identity
        checks. Use .NET `Equals` (reference equality for these singleton
        services) to verify both paths resolve to the same underlying object.
        """
        from SIL.LCModel import ICmObjectRepository

        service_via_helper = live_project.GetService(ICmObjectRepository)
        service_via_locator = (
            live_project.project.ServiceLocator.GetService(ICmObjectRepository)
        )

        assert service_via_helper is not None, (
            "GetService returned None for ICmObjectRepository"
        )
        # The ServiceLocator returns the same registered singleton each call,
        # so the helper's .NET object must equal a direct call's result.
        assert service_via_helper.Equals(service_via_locator), (
            "GetService(interface_type) is not delegating to "
            "ServiceLocator.GetService(interface_type) - "
            f"helper returned {service_via_helper}, "
            f"direct call returned {service_via_locator}"
        )

    def test_get_default_vernacular_ws_handle_returns_int(self, live_project):
        """
        GetDefaultVernacularWSHandle() must return a Python int suitable for
        TsStringUtils.MakeString(text, ws_handle).
        """
        handle = live_project.GetDefaultVernacularWSHandle()
        assert isinstance(handle, int), (
            f"Expected int handle, got {type(handle).__name__}: {handle!r}"
        )
        # WS handles are positive identifiers in LCM.
        assert handle > 0, f"Expected positive WS handle, got {handle}"

        # Cross-check: matches WritingSystems.GetDefaultVernacular().Handle
        expected = live_project.WritingSystems.GetDefaultVernacular().Handle
        assert handle == expected, (
            f"Handle from helper ({handle}) does not match "
            f"WritingSystems.GetDefaultVernacular().Handle ({expected})"
        )

    def test_get_default_analysis_ws_handle_returns_int(self, live_project):
        """
        GetDefaultAnalysisWSHandle() must return a Python int suitable for
        TsStringUtils.MakeString(text, ws_handle).
        """
        handle = live_project.GetDefaultAnalysisWSHandle()
        assert isinstance(handle, int), (
            f"Expected int handle, got {type(handle).__name__}: {handle!r}"
        )
        assert handle > 0, f"Expected positive WS handle, got {handle}"

        expected = live_project.WritingSystems.GetDefaultAnalysis().Handle
        assert handle == expected, (
            f"Handle from helper ({handle}) does not match "
            f"WritingSystems.GetDefaultAnalysis().Handle ({expected})"
        )

    def test_existing_tuple_methods_unchanged_returns_tuple(self, live_project):
        """
        Regression guard: the pre-existing GetDefaultVernacularWS() and
        GetDefaultAnalysisWS() methods must still return a 2-tuple of
        (language_tag, display_name) strings. The new *Handle helpers are
        siblings, not replacements.
        """
        for method_name in ("GetDefaultVernacularWS", "GetDefaultAnalysisWS"):
            result = getattr(live_project, method_name)()
            assert isinstance(result, tuple), (
                f"{method_name}() must return a tuple, "
                f"got {type(result).__name__}"
            )
            assert len(result) == 2, (
                f"{method_name}() must return a 2-tuple, "
                f"got {len(result)} elements: {result!r}"
            )
            tag, name = result
            assert isinstance(tag, str), (
                f"{method_name}()[0] (language tag) must be str, "
                f"got {type(tag).__name__}: {tag!r}"
            )
            assert isinstance(name, str), (
                f"{method_name}()[1] (display name) must be str, "
                f"got {type(name).__name__}: {name!r}"
            )
            assert tag, f"{method_name}() returned empty language tag"
            assert name, f"{method_name}() returned empty display name"


class TestGetFactory:
    """
    Coverage for `FLExProject.GetFactory(interface_type)` — issue #34.

    GetFactory wraps the pythonnet reflection dance for the LCM
    ServiceLocator's generic `GetInstance<T>()` method. It's the
    discoverable entry point for factory dispatch and must work for
    both well-known factories (IPhPhonemeFactory) and the factories
    whose subscript-generic invocation originally surfaced the bug
    (IFsClosedFeatureFactory / IMoInflAffMsaFactory).
    """

    # ----- Static introspection (no LCM required) --------------------

    def test_get_factory_is_callable_method(self):
        """
        GetFactory must be exposed as a callable method (not a property)
        taking a single positional `interface_type` argument besides self.
        """
        from flexicon.code.FLExProject import FLExProject

        assert "GetFactory" in dir(FLExProject), (
            "GetFactory not visible via dir(FLExProject)"
        )

        descriptor = inspect.getattr_static(FLExProject, "GetFactory")
        assert callable(descriptor), "GetFactory must be callable"
        assert not isinstance(descriptor, property), (
            "GetFactory must be a method, not a property"
        )

        params = [
            p for p in inspect.signature(descriptor).parameters.values()
            if p.name != "self"
        ]
        assert len(params) == 1, (
            "GetFactory should take one parameter besides self, "
            f"got {len(params)}: {[p.name for p in params]}"
        )

    def test_get_factory_rejects_none(self):
        """
        GetFactory(None) must raise FP_NullParameterError without
        touching the ServiceLocator — input validation is the first
        thing to fire.
        """
        from flexicon.code.exceptions import FP_NullParameterError
        from flexicon.code.FLExProject import FLExProject

        # We don't need a live project for this — the guard runs before
        # any LCM access. Use a sentinel object as `self` to make sure
        # the test fails loudly if the implementation reorders the
        # check and touches `self.project`.
        class _Sentinel:
            @property
            def project(self):
                raise AssertionError(
                    "GetFactory accessed self.project before validating "
                    "interface_type — guard order is wrong"
                )

        with pytest.raises(FP_NullParameterError):
            FLExProject.GetFactory(_Sentinel(), None)

    # ----- Live-LCM behavior (skipped without a real project) --------

    def test_get_factory_resolves_phoneme_factory(self, live_project):
        """
        GetFactory(IPhPhonemeFactory) must return a non-null factory
        whose Create() produces an IPhPhoneme-like object. This is the
        canonical "factory dispatch" smoke test.
        """
        from SIL.LCModel import IPhPhonemeFactory

        factory = live_project.GetFactory(IPhPhonemeFactory)
        assert factory is not None, (
            "GetFactory(IPhPhonemeFactory) returned None"
        )
        # Discoverability: a factory must expose Create().
        assert hasattr(factory, "Create"), (
            f"Resolved object {factory!r} has no Create() method - "
            "GetFactory did not return a real factory"
        )

    def test_get_factory_resolves_closed_feature_factory(self, live_project):
        """
        GetFactory(IFsClosedFeatureFactory) — this is the factory whose
        subscript-generic dispatch (`GetInstance[IFsClosedFeatureFactory]()`)
        originally surfaced issue #34. It must resolve via GetFactory
        regardless of which internal path is taken.
        """
        from SIL.LCModel import IFsClosedFeatureFactory

        factory = live_project.GetFactory(IFsClosedFeatureFactory)
        assert factory is not None, (
            "GetFactory(IFsClosedFeatureFactory) returned None - "
            "neither GetInstance(Type) nor reflection path resolved it"
        )
        assert hasattr(factory, "Create"), (
            f"Resolved object {factory!r} has no Create() method"
        )

    def test_get_factory_is_consistent_across_calls(self, live_project):
        """
        Repeated calls for the same interface must return a non-null
        factory each time. ServiceLocator factories are typically
        singletons, so the MethodInfo cache shouldn't break behavior.
        Use .NET Equals (not Python `is`) because pythonnet wraps the
        same CLR object in a fresh Python proxy on each access.
        """
        from SIL.LCModel import IPhPhonemeFactory

        first = live_project.GetFactory(IPhPhonemeFactory)
        second = live_project.GetFactory(IPhPhonemeFactory)
        assert first is not None and second is not None, (
            "GetFactory returned None on a repeated call"
        )
        assert first.Equals(second), (
            "ServiceLocator should hand back the same factory singleton; "
            "GetFactory's MethodInfo cache may be corrupting state"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
