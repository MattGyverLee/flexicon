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
#          its docstring but (pre-fix) never casts -- FLExProject.Object
#          (hvo) returns a bare ICmObject, so subtype-only members are
#          silently lost on the HVO entry path. Its two callers,
#          AddPhoneEnv (:1255-1256) and RemovePhoneEnv (:1297-1298),
#          both MUTATE via allomorph.PhoneEnvRC, an
#          ILcmReferenceCollection[IPhEnvironment].
#
#          #260's actually-observed failure came from an OBJECT input
#          (project.Object(guid) result), not an int, so the fix must
#          merge the int and object branches (mirroring the sibling's
#          :1359-1369 int/object merge) and apply the cast to BOTH --
#          an int-only cast leaves the reported defect live.
#
#          As with the T8 gate, these tests pass a GENUINE Python int
#          HVO (asserted isinstance(hvo, int) BEFORE the call) -- an
#          already-typed object exercises the cast VACUOUSLY and is
#          worthless.
#
#   Basis: specs/260-environment-resolver-cast/evidence/
#          live-T1-reflection.md measured
#          hasattr(bare_object, "StringRepresentation") -> False on a
#          bare sandbox.Object(hvo) view of a real PhEnvironment, so
#          "StringRepresentation" is itself concrete-only through the
#          HVO entry path (the T8-style trap holds for PhEnvironment
#          too). If __GetEnvironmentObject's cast is absent/deleted, a
#          bare ICmObject reaches allomorph.PhoneEnvRC.Add/Remove and
#          (per P2) that reference-collection call does not bind to a
#          bare ICmObject.
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
            # object -- otherwise the cast under test at
            # __GetEnvironmentObject is exercised vacuously (the object
            # is already concrete before the call).
            assert isinstance(env_hvo, int), (
                "test setup error: env_hvo must be a genuine Python int, "
                "not an already-typed environment object -- otherwise "
                "the cast under test is exercised vacuously."
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
                "the cast under test is exercised vacuously."
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
