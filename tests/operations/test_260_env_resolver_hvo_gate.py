#
#   test_260_env_resolver_hvo_gate.py
#
#   Class: TestHvoPathCastAddPhoneEnv / TestHvoPathCastRemovePhoneEnv
#          Issue #260 half two -- gate for
#          AllomorphOperations.__GetEnvironmentObject
#          (:1371-1383). Half one, the sibling resolver
#          __GetAllomorphObject, already landed as T8 in commit df37e35
#          and is covered by tests/operations/test_t8_hvo_path_gate.py;
#          this file does NOT touch that resolver.
#
#          __GetEnvironmentObject promises "Returns: IPhEnvironment" in
#          its docstring but does not cast -- FLExProject.Object(hvo)
#          returns a bare ICmObject. Its two callers, AddPhoneEnv
#          (:1255-1256) and RemovePhoneEnv (:1297-1298), both MUTATE via
#          allomorph.PhoneEnvRC, an
#          ILcmReferenceCollection[IPhEnvironment].
#
#          CYCLE-1 CORRECTION (lead ruling, 2026-09-08). An earlier
#          version of this header asserted that the missing cast BREAKS
#          these two callers. That was prediction P2, and P2 was
#          FALSIFIED live: on unmodified HEAD both callers SUCCEED with
#          a genuine int HVO (evidence/live-T2-p2-falsification.md).
#          Reason: passing a bare wrapper as an ARGUMENT to a strongly-
#          typed .NET method is not the failing path -- the CLR binds on
#          the object's runtime type, which does implement
#          IPhEnvironment. The failing path is PYTHON ATTRIBUTE ACCESS
#          on the resolved object (pythonnet exposes only members
#          declared on the static interface the wrapper was built
#          against). #260's actually-reported AttributeError comes from
#          Grammar/EnvironmentOperations.py __ResolveObject (:648),
#          whose callers DO read env.Name / env.StringRepresentation
#          directly -- a different file from this one.
#
#          As with the T8 gate, these tests pass a GENUINE Python int
#          HVO (asserted isinstance(hvo, int) BEFORE the call) -- an
#          already-typed object exercises the cast VACUOUSLY and is
#          worthless.
#
#   Basis: specs/260-environment-resolver-cast/evidence/
#          live-T1-reflection.md measured
#          hasattr(bare_object, "StringRepresentation") -> False on a
#          bare sandbox.Object(hvo) view of a real PhEnvironment (P3,
#          HELD). That trap is what makes the ATTRIBUTE-ACCESS axis
#          real; it is re-asserted below as a live precondition so this
#          file records the measurement even though these two callers
#          do not depend on it.
#
#   WHAT THIS FILE PROVES / DOES NOT PROVE (read before citing it):
#          PROVES -- AddPhoneEnv and RemovePhoneEnv both write through
#          correctly via a genuine int-HVO entry path, verified by a
#          FRESH re-fetch in both directions. That is real live coverage
#          for two methods that previously had none (flexicon#268).
#          DOES NOT PROVE -- that any cast in __GetEnvironmentObject is
#          behaviourally required. These tests were GREEN on the uncast
#          baseline. They are a REGRESSION FENCE for the two callers,
#          not a gate on the cast. If a contract-conformance cast later
#          lands in __GetEnvironmentObject, these tests must stay GREEN
#          and UNCHANGED; a flip in either direction means the cycle-1
#          falsification was wrong and #260 must be re-opened.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def _make_entry(sandbox, tag):
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


class TestHvoPathCastAddPhoneEnv:
    """
    Primary site: AddPhoneEnv (:1215) mutates via
    allomorph.PhoneEnvRC.Add(env). sandbox-only.
    """

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_add_phone_env_via_genuine_hvo_int_writes_through_concrete_env(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "260gate_add")
        env = None
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}addform", morphType="suffix"
            )
            env = sandbox.Environments.Create(f"{TEST_PREFIX}260_add_env")
            env_hvo = env.Hvo

            # THE TRAP: this must be a genuine int, not an already-typed
            # object -- otherwise the HVO entry path through
            # __GetEnvironmentObject is exercised vacuously (the object
            # is already concrete before the call).
            assert isinstance(env_hvo, int), (
                "test setup error: env_hvo must be a genuine Python int, "
                "not an already-typed environment object -- otherwise "
                "the HVO entry path under test is exercised vacuously."
            )

            # P3: the bare-view trap holds for PhEnvironment too.
            bare_env = sandbox.Object(env_hvo)
            assert not hasattr(bare_env, "StringRepresentation"), (
                "P3 precondition failed: StringRepresentation is "
                "reachable on the bare ICmObject view -- the trap this "
                "test relies on no longer holds; re-derive the site."
            )

            sandbox.Allomorphs.AddPhoneEnv(allo, env_hvo)

            # Re-fetch fresh from the LCM after the write -- never
            # assert on the value just passed in.
            fresh_envs = sandbox.Allomorphs.GetPhoneEnv(sandbox.Object(allo.Hvo))
            fresh_hvos = [e.Hvo for e in fresh_envs]
            assert env_hvo in fresh_hvos, (
                f"AddPhoneEnv(allomorph, hvo) did not write through the "
                f"concrete PhoneEnvRC member: re-read hvos {fresh_hvos!r}, "
                f"expected {env_hvo!r} present."
            )
        finally:
            sandbox.LexEntry.Delete(entry)
            if env is not None:
                sandbox.Environments.Delete(env)


class TestHvoPathCastRemovePhoneEnv:
    """
    Second site: RemovePhoneEnv (:1262) mutates via
    allomorph.PhoneEnvRC.Remove(env). sandbox-only.

    Setup adds the environment directly via the raw LCM collection
    (using the already-typed env object returned by Create), NOT via
    AddPhoneEnv -- so this test's precondition never depends on the
    resolver under test, and stays valid whether or not the fix has
    landed yet.
    """

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_remove_phone_env_via_genuine_hvo_int_writes_through_concrete_env(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "260gate_remove")
        env = None
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}removeform", morphType="suffix"
            )
            env = sandbox.Environments.Create(f"{TEST_PREFIX}260_remove_env")
            env_hvo = env.Hvo

            assert isinstance(env_hvo, int), (
                "test setup error: env_hvo must be a genuine Python int, "
                "not an already-typed environment object -- otherwise "
                "the HVO entry path under test is exercised vacuously."
            )

            # P3 trap, re-asserted at this site independently.
            bare_env = sandbox.Object(env_hvo)
            assert not hasattr(bare_env, "StringRepresentation"), (
                "P3 precondition failed: StringRepresentation is "
                "reachable on the bare ICmObject view -- the trap this "
                "test relies on no longer holds; re-derive the site."
            )

            # Precondition setup bypasses the resolver under test: add
            # the environment via the real typed object directly on the
            # raw LCM collection.
            allo.PhoneEnvRC.Add(env)

            sandbox.Allomorphs.RemovePhoneEnv(allo, env_hvo)

            # Re-fetch fresh from the LCM after the write -- never
            # assert on the value just passed in.
            fresh_envs = sandbox.Allomorphs.GetPhoneEnv(sandbox.Object(allo.Hvo))
            fresh_hvos = [e.Hvo for e in fresh_envs]
            assert env_hvo not in fresh_hvos, (
                f"RemovePhoneEnv(allomorph, hvo) did not write through "
                f"the concrete PhoneEnvRC member: re-read hvos "
                f"{fresh_hvos!r}, expected {env_hvo!r} absent."
            )
        finally:
            sandbox.LexEntry.Delete(entry)
            if env is not None:
                sandbox.Environments.Delete(env)
