#
#   test_260_environment_resolver_gate.py
#
#   Class: TestP6DirectAttributeAccess / TestP6bSyncableProperties /
#          TestP7DiscoveredWrongPropertyName
#          Issue #260 half two, cycle 2, task T2 -- the REAL defect.
#
#          Grammar/EnvironmentOperations.py __ResolveObject (:648-660)
#          is uncast, same shape as AllomorphOperations'
#          __GetEnvironmentObject, but UNLIKE that sibling (cleared in
#          cycle 1 -- P2 falsified, both its callers only ever hand the
#          resolved object to a strongly-typed .NET reference-collection
#          method), EVERY caller in THIS file performs direct PYTHON
#          attribute access on the resolved object:
#            GetName             (:255 resolve, :258 env.Name.get_String)
#            SetName             (:298 resolve, :304 env.Name.set_String)
#            GetStringRepresentation (:362 resolve, :365 env.StringRepresentation.Text)
#            SetStringRepresentation (:422 resolve, :428 env.StringRepresentation =)
#            GetSyncableProperties   (:688 resolve, :700 getattr(env, prop_name))
#            GetLeftContextPattern   (:478 resolve, :481 hasattr(env, "LeftContextOA"))
#            GetRightContextPattern  (:534 resolve, :537 hasattr(env, "RightContextOA"))
#
#          NOTE ON METHOD NAMES: the cycle-2 briefing and predictions.md
#          refer to "GetLeftContext"/"GetRightContext". The methods that
#          actually exist on EnvironmentOperations are
#          GetLeftContextPattern / GetRightContextPattern (verified by
#          reading Grammar/EnvironmentOperations.py directly -- there is
#          no GetLeftContext/GetRightContext anywhere in the file). P7 is
#          exercised against the real method, GetLeftContextPattern.
#
#          pythonnet's static wrapper-type gate means a bare
#          `project.Object(hvo)` view exposes only members declared on
#          the interface it was built against (ICmObject), so `env.Name`
#          / `env.StringRepresentation` raise AttributeError, and
#          `hasattr(env, "LeftContextOA")` is silently False. Cycle 1's
#          P3 already measured `hasattr(bare, "Name")` and
#          `hasattr(bare, "StringRepresentation")` False live for a real
#          PhEnvironment; this file is that measurement carried to its
#          actual call sites.
#
#          RED-FIRST DISCIPLINE (P6/P6b only -- see P7 note below):
#          every TestP6*/TestP6b* assertion states the CORRECT/DESIRED
#          post-fix behaviour. Run against unmodified source, these
#          tests FAIL via an uncaught AttributeError bubbling out of the
#          resolver's callers. That failure output IS the RED evidence
#          (specs/260-environment-resolver-cast/evidence/
#          live-T2-red-p6-p6b-p7.md). After the guarded cast lands in
#          __ResolveObject, the same tests pass unmodified (P8) -- no
#          test-body edits between RED and GREEN.
#
#          As with the T8 / #260-half-one gates, every genuine HVO here
#          is asserted `isinstance(hvo, int)` BEFORE the call -- an
#          already-typed object would exercise the resolver vacuously.
#          Every post-write read is a FRESH re-fetch, never the value
#          just passed in.
#
#          P7 CORRECTION (found while building this cycle's P7 fixture,
#          NOT predicted): the original P7 hypothesis was that
#          GetLeftContextPattern's `hasattr(env, "LeftContextOA")` gate
#          silently returns `None` on the uncast baseline and would
#          return the populated context once the guarded cast landed.
#          MEASURED LIVE (post-cast): it does NOT. `IPhEnvironment` and
#          its sole concrete implementation `PhEnvironment` declare NO
#          `LeftContextOA`/`RightContextOA` property anywhere --
#          confirmed via `.NET` reflection
#          (`clr.GetClrType(IPhEnvironment).GetProperties()` lists only
#          `LeftContextRA`/`RightContextRA`, Reference Atomic, not
#          Owning Atomic; "Did you mean: 'LeftContextRA'?" is pythonnet's
#          own AttributeError hint on a freshly-cast object). The reason
#          the ORIGINAL uncast baseline "worked" via an already-typed
#          object at all is a pythonnet quirk, not a real read: assigning
#          `.LeftContextOA` to an object whose Python wrapper is NOT
#          narrowed to an interface silently creates a dynamic PYTHON
#          instance attribute (never a real .NET member, never
#          persisted) -- it vanishes on any fresh wrapper of the same
#          object, cast or bare. `GetLeftContextPattern` /
#          `GetRightContextPattern` / `Duplicate`'s deep-copy block all
#          read this same nonexistent property name and therefore return
#          `None` / copy nothing for EVERY environment, unconditionally,
#          regardless of any cast. This is a SEPARATE, pre-existing bug
#          (wrong property name), independent of the missing-cast defect
#          this task fixes, and OUT OF SCOPE for T2 -- flagged for a new
#          issue, not fixed here (see cycle2-programmer.md).
#          TestP7DiscoveredWrongPropertyName below locks the DISCOVERY
#          (the real property names), not a fix.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


class TestP6DirectAttributeAccess:
    """
    P6 (load-bearing): GetName / GetStringRepresentation perform direct
    Python attribute access (`env.Name...`, `env.StringRepresentation...`)
    on the resolver's return value. Also covers the write side (SetName /
    SetStringRepresentation) so P8's four-method post-fix claim is fully
    exercised in one pass.
    """

    @pytest.mark.live_phase("EnvironmentOperations", "modify")
    def test_get_name_via_genuine_hvo_int_reads_concrete_name(self, target_sandbox):
        sandbox = target_sandbox
        env = sandbox.Environments.Create(f"{TEST_PREFIX}260_p6_getname")
        env_hvo = env.Hvo
        try:
            # THE TRAP: genuine int, not an already-typed object -- an
            # already-typed object exercises the resolver vacuously.
            assert isinstance(env_hvo, int), (
                "test setup error: env_hvo must be a genuine Python int, "
                "not an already-typed environment object -- otherwise "
                "the HVO entry path under test is exercised vacuously."
            )

            # P3-style precondition: the bare view really does lack Name.
            bare_env = sandbox.Object(env_hvo)
            assert not hasattr(bare_env, "Name"), (
                "P3 precondition failed: Name is reachable on the bare "
                "ICmObject view -- the trap this test relies on no "
                "longer holds; re-derive the site."
            )

            name = sandbox.Environments.GetName(env_hvo)
            assert name == f"{TEST_PREFIX}260_p6_getname", (
                f"GetName(hvo) did not reach the concrete Name member: "
                f"got {name!r}"
            )
        finally:
            sandbox.Environments.Delete(env)

    @pytest.mark.live_phase("EnvironmentOperations", "modify")
    def test_set_name_via_genuine_hvo_int_writes_through_concrete_name(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        env = sandbox.Environments.Create(f"{TEST_PREFIX}260_p6_setname_old")
        env_hvo = env.Hvo
        try:
            assert isinstance(env_hvo, int)

            sandbox.Environments.SetName(env_hvo, f"{TEST_PREFIX}260_p6_setname_new")

            # Fresh re-fetch via the OBJECT branch of the resolver (a
            # definitely-bare ICmObject, not the value passed in) --
            # exercises the merged int/object branches independently.
            bare_reread = sandbox.Object(env_hvo)
            reread_name = sandbox.Environments.GetName(bare_reread)
            assert reread_name == f"{TEST_PREFIX}260_p6_setname_new", (
                f"SetName(hvo, ...) did not persist through the concrete "
                f"Name member: re-read {reread_name!r}"
            )
        finally:
            sandbox.Environments.Delete(env)

    @pytest.mark.live_phase("EnvironmentOperations", "modify")
    def test_get_string_representation_via_genuine_hvo_int_reads_concrete_notation(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        env = sandbox.Environments.Create(f"{TEST_PREFIX}260_p6_getstrrep")
        env_hvo = env.Hvo
        try:
            assert isinstance(env_hvo, int)

            # Set notation via the already-typed object first (not the
            # path under test), so GetStringRepresentation(hvo) below
            # is reading real, independently-established data.
            sandbox.Environments.SetStringRepresentation(env, "V_V")

            bare_env = sandbox.Object(env_hvo)
            assert not hasattr(bare_env, "StringRepresentation"), (
                "P3 precondition failed: StringRepresentation is "
                "reachable on the bare ICmObject view -- the trap this "
                "test relies on no longer holds; re-derive the site."
            )

            notation = sandbox.Environments.GetStringRepresentation(env_hvo)
            assert notation == "V_V", (
                f"GetStringRepresentation(hvo) did not reach the concrete "
                f"StringRepresentation member: got {notation!r}"
            )
        finally:
            sandbox.Environments.Delete(env)

    @pytest.mark.live_phase("EnvironmentOperations", "modify")
    def test_set_string_representation_via_genuine_hvo_int_writes_through(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        env = sandbox.Environments.Create(f"{TEST_PREFIX}260_p6_setstrrep")
        env_hvo = env.Hvo
        try:
            assert isinstance(env_hvo, int)

            sandbox.Environments.SetStringRepresentation(env_hvo, "#_")

            # Fresh re-fetch via the OBJECT branch, not the value passed in.
            bare_reread = sandbox.Object(env_hvo)
            reread_notation = sandbox.Environments.GetStringRepresentation(
                bare_reread
            )
            assert reread_notation == "#_", (
                f"SetStringRepresentation(hvo, ...) did not persist "
                f"through the concrete StringRepresentation member: "
                f"re-read {reread_notation!r}"
            )
        finally:
            sandbox.Environments.Delete(env)


class TestP6bSyncableProperties:
    """
    P6b (load-bearing, sync path): GetSyncableProperties loops
    `getattr(env, prop_name)` over Name / Description / StringRepresentation
    at :700. This is the falsifier that matters most because it sits on
    the cross-project sync path.
    """

    @pytest.mark.live_phase("EnvironmentOperations", "read")
    def test_get_syncable_properties_via_genuine_hvo_int_reads_dict(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        env = sandbox.Environments.Create(
            f"{TEST_PREFIX}260_p6b_sync", f"{TEST_PREFIX}260_p6b_sync_desc"
        )
        env_hvo = env.Hvo
        try:
            assert isinstance(env_hvo, int), (
                "test setup error: env_hvo must be a genuine Python int, "
                "not an already-typed environment object -- otherwise "
                "the HVO entry path under test is exercised vacuously."
            )

            bare_env = sandbox.Object(env_hvo)
            assert not hasattr(bare_env, "Name"), (
                "P3 precondition failed: Name is reachable on the bare "
                "ICmObject view -- the trap this test relies on no "
                "longer holds; re-derive the site."
            )

            props = sandbox.Environments.GetSyncableProperties(env_hvo)
            assert "Name" in props, (
                f"GetSyncableProperties(hvo) did not reach the concrete "
                f"Name member: got keys {list(props.keys())!r}"
            )
            name_values = list(props["Name"].values())
            assert f"{TEST_PREFIX}260_p6b_sync" in name_values, (
                f"GetSyncableProperties(hvo)['Name'] does not contain the "
                f"expected value: got {props['Name']!r}"
            )
        finally:
            sandbox.Environments.Delete(env)


class TestP7DiscoveredWrongPropertyName:
    """
    P7 correction (see the module header and cycle2-programmer.md): the
    original P7 hypothesis -- that the missing cast is why
    GetLeftContextPattern silently returns None -- does not hold.
    MEASURED LIVE: `IPhEnvironment` and its sole concrete implementation
    `PhEnvironment` declare `LeftContextRA`/`RightContextRA` (Reference
    Atomic), NOT `LeftContextOA`/`RightContextOA` (Owning Atomic, which
    do not exist anywhere in the LCM API for this type).
    GetLeftContextPattern / GetRightContextPattern / Duplicate's deep-copy
    block all read the nonexistent name, so they return None / copy
    nothing for EVERY environment, cast or not. This is a separate,
    pre-existing bug, out of scope for this cast-only task -- this class
    locks the DISCOVERY, not a fix, so a future sweep has a live,
    reproducible anchor instead of having to re-derive it.
    """

    @pytest.mark.live_phase("EnvironmentOperations", "read")
    def test_left_and_right_context_are_reference_atomic_not_owning_atomic(
        self, target_sandbox
    ):
        from SIL.LCModel import IPhEnvironment
        import clr

        sandbox = target_sandbox
        clr_type = clr.GetClrType(IPhEnvironment)
        prop_names = {p.Name for p in clr_type.GetProperties()}

        assert {"LeftContextRA", "RightContextRA"} <= prop_names, (
            "expected real property names LeftContextRA/RightContextRA "
            "on IPhEnvironment; re-derive this discovery if the LCM API "
            "has changed."
        )
        assert not ({"LeftContextOA", "RightContextOA"} & prop_names), (
            "LeftContextOA/RightContextOA now exist on IPhEnvironment -- "
            "GetLeftContextPattern/GetRightContextPattern/Duplicate's "
            "wrong-property-name bug may already be fixed independently; "
            "re-verify against a fresh environment before relying on "
            "this test to justify filing a new issue."
        )

        # Confirm the ACTUAL production method returns None even on an
        # already-typed object -- not because of the missing cast (this
        # object needs no resolving), but because the property name it
        # reads does not exist.
        env = sandbox.Environments.Create(f"{TEST_PREFIX}260_p7_wrongname")
        try:
            result = sandbox.Environments.GetLeftContextPattern(env)
            assert result is None, (
                "GetLeftContextPattern returned non-None on an "
                "already-typed object with no context ever set -- the "
                "baseline this discovery rests on no longer holds; "
                "re-derive before citing it."
            )
        finally:
            sandbox.Environments.Delete(env)
