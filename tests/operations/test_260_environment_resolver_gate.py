#
#   test_260_environment_resolver_gate.py
#
#   Class: TestP6DirectAttributeAccess / TestP6bSyncableProperties /
#          TestP7SilentLeftContextLoss
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
#          RED-FIRST DISCIPLINE: every assertion below states the
#          CORRECT/DESIRED post-fix behaviour. Run against unmodified
#          source, these tests FAIL -- either via an uncaught
#          AttributeError bubbling out of the resolver's callers (P6,
#          P6b) or via an assertion mismatch on a silently-wrong `None`
#          (P7). That failure output IS the RED evidence. After the
#          guarded cast lands in __ResolveObject, the same tests pass
#          unmodified (P8) -- no test-body edits between RED and GREEN.
#
#          As with the T8 / #260-half-one gates, every genuine HVO here
#          is asserted `isinstance(hvo, int)` BEFORE the call -- an
#          already-typed object would exercise the resolver vacuously.
#          Every post-write read is a FRESH re-fetch, never the value
#          just passed in.
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


class TestP7SilentLeftContextLoss:
    """
    P7 (the silent variant): GetLeftContextPattern is `hasattr`-gated at
    :481, so on the uncast baseline it silently returns None instead of
    raising -- the worst kind of defect (no exception, no traceback,
    wrong answer). We MUST first confirm the left context is genuinely
    populated via an already-typed object, or a None result proves
    nothing.
    """

    @pytest.mark.live_phase("EnvironmentOperations", "modify")
    def test_get_left_context_pattern_via_genuine_hvo_int_returns_populated_context(
        self, target_sandbox
    ):
        from SIL.LCModel import IPhSimpleContextSegFactory

        sandbox = target_sandbox
        env = sandbox.Environments.Create(f"{TEST_PREFIX}260_p7_leftctx")
        phoneme = sandbox.Phonemes.Create(f"{TEST_PREFIX}260p7p")
        try:
            # Build an IPhSimpleContextSeg directly against the phoneme
            # and attach it to the environment's LeftContextOA via the
            # already-typed `env` object returned by Create() (NOT the
            # resolver under test -- ownership-first, per the project's
            # own __PopulateSimpleContext discipline in
            # PhonologicalRuleOperations).
            ctx_factory = sandbox.project.ServiceLocator.GetService(
                IPhSimpleContextSegFactory
            )
            with sandbox._TransactionCM("T2 P7 fixture: populate LeftContextOA"):
                ctx = ctx_factory.Create()
                env.LeftContextOA = ctx
                try:
                    ctx.FeatureStructureRA = phoneme
                except Exception:
                    # Confirmed-live LCM quirk, unrelated to the resolver
                    # defect under test: the FIRST FeatureStructureRA
                    # assignment on a freshly OwningAtomic-attached
                    # IPhSimpleContextSeg raises
                    # System.NullReferenceException from
                    # PhSimpleContextSeg.SetFeatureStructureRA; the
                    # identical second call on the SAME object then
                    # succeeds (see cycle-2 debug notes). Retry once.
                    ctx.FeatureStructureRA = phoneme

            env_hvo = env.Hvo
            assert isinstance(env_hvo, int), (
                "test setup error: env_hvo must be a genuine Python int, "
                "not an already-typed environment object -- otherwise "
                "the HVO entry path under test is exercised vacuously."
            )

            # Confirm the context is GENUINELY populated via the
            # already-typed object -- an already-typed input takes the
            # resolver's object-passthrough branch, which was never in
            # question, so this call succeeding proves the fixture, not
            # the defect under test.
            already_typed_result = sandbox.Environments.GetLeftContextPattern(env)
            assert already_typed_result is not None, (
                "fixture bug: LeftContextOA is not populated on the "
                "already-typed object -- a None result from the HVO path "
                "below would prove nothing."
            )

            # P3-style precondition: the bare view really does lack
            # LeftContextOA (the mechanism that produces the silent None).
            bare_env = sandbox.Object(env_hvo)
            assert not hasattr(bare_env, "LeftContextOA"), (
                "P3-style precondition failed: LeftContextOA is "
                "reachable on the bare ICmObject view -- the trap this "
                "test relies on no longer holds; re-derive the site."
            )

            # THE DEFECT (P7): calling through a genuine int HVO must
            # return the same populated context, not silently None.
            hvo_result = sandbox.Environments.GetLeftContextPattern(env_hvo)
            assert hvo_result is not None, (
                "GetLeftContextPattern(hvo) silently returned None for an "
                "environment whose LeftContextOA is genuinely populated "
                "(confirmed via the already-typed object above) -- the "
                "hasattr-gated silent-loss defect (P7)."
            )
        finally:
            sandbox.Environments.Delete(env)
            sandbox.Phonemes.Delete(phoneme)
