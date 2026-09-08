P1: IPhEnvironment has NO concrete LCM subtypes, and a real environment
    created via EnvironmentOperations.Create reports
    ClassName == "PhEnvironment".
P2 (LOAD-BEARING): on unmodified HEAD, AddPhoneEnv(allomorph, env_hvo_int)
    FAILS -- PhoneEnvRC.Add(a bare ICmObject) does not bind to
    ILcmReferenceCollection[IPhEnvironment].Add, raising TypeError /
    System.InvalidCastException / ArgumentException. The pre-fix baseline
    is RED, not merely contract-impure.
P3: hasattr(sandbox.Object(env_hvo), "StringRepresentation") is False on
    the bare ICmObject view -- the T8-style trap holds for PhEnvironment too.
P4: after the cast, AddPhoneEnv and RemovePhoneEnv both succeed with a
    genuine int HVO, confirmed by re-reading GetPhoneEnv from a FRESH
    re-fetch (never asserting on the value passed in).
P5: the offline suite stays at 439 passed / 2 failed / (526 + N)
    deselected, red set exactly the two foreign
    tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen
    failures. N = the number of new live-marked tests you add; write the
    exact N into predictions.md BEFORE running.

N = 2 (two new `requires_live_project`-marked test methods:
TestHvoPathCastAddPhoneEnv.test_add_phone_env_via_genuine_hvo_int_writes_through
and TestHvoPathCastRemovePhoneEnv.test_remove_phone_env_via_genuine_hvo_int_writes_through,
in tests/operations/test_260_env_resolver_hvo_gate.py). So P5's expected
deselected count is 526 + 2 = 528.

---

# Cycle 2 predictions (committed by lead BEFORE any cycle-2 run)

Basis: cycle 1's P3 measured live that `hasattr(bare, "Name")` and
`hasattr(bare, "StringRepresentation")` are both `False` on a bare
`project.Object(hvo)` view of a real `PhEnvironment`. Cycle 2's
predictions are that measurement carried to the file whose callers
actually perform Python attribute access.

P6 (load-bearing, T2): against UNMODIFIED
    `EnvironmentOperations.__ResolveObject`, `GetName(env_hvo_int)` and
    `GetStringRepresentation(env_hvo_int)` each RAISE
    `AttributeError: 'ICmObject' object has no attribute 'Name'` /
    `'StringRepresentation'` -- the same failure string #260 was
    originally reported with. The pre-fix baseline is genuinely RED.
    If this comes back GREEN, STOP and report -- do not hunt for a
    substitute falsifier, and do not apply the cast on a green baseline.

P6b (load-bearing, T2 -- added by the lead at cycle-1 close, still
    BEFORE any cycle-2 run, from a first-hand read of
    EnvironmentOperations.py:688-700 that the cycle-1 report did not
    cover): against UNMODIFIED source,
    `GetSyncableProperties(env_hvo_int)` RAISES on its
    `getattr(env, prop_name)` loop at :700 for the FIRST of
    `Name` / `Description` / `StringRepresentation` it reaches -- a
    third independent falsifier on the attribute-access axis, and the
    one that matters most because it is on the sync path. If this comes
    back GREEN while P6 comes back RED, stop and report: the two
    disagree about the same mechanism and something in the model of
    pythonnet's wrapper gate is wrong.

P7 (T2, the silent variant): against UNMODIFIED source,
    `GetLeftContext(env_hvo_int)` returns `None` WITHOUT raising, on an
    environment whose `LeftContextOA` is genuinely populated -- because
    `hasattr(bare, "LeftContextOA")` is `False`. This is silent wrong-
    answer loss, not an exception. Verify the context really is
    populated first (via an already-typed object) or the `None` proves
    nothing.

P8 (T2, post-fix): after the guarded cast, all four of GetName /
    SetName / GetStringRepresentation / SetStringRepresentation succeed
    through the int-HVO path, and GetLeftContext returns the populated
    context. Every post-write assertion re-reads from a FRESH re-fetch.

P9 (T3): landing the guarded cast in
    `AllomorphOperations.__GetEnvironmentObject` changes NOTHING
    observable at `AddPhoneEnv`/`RemovePhoneEnv` -- the existing two
    gate tests stay GREEN, exactly as they were pre-cast. This is the
    prediction that keeps T3 honest: if anything flips, the cycle-1
    falsification was wrong and must be re-opened.

P10 (T4): `hasattr(bare_allo, "PhoneEnvRC")` is `False` on a bare
    `project.Object(allo.Hvo)` view -- i.e. `PhoneEnvRC` is a
    subtype-only member, so passing the ALLOMORPH as a genuine int HVO
    exercises `__GetAllomorphObject`'s T8 cast non-vacuously and makes
    the flexicon#268 coverage claim true. If it measures `True`,
    `PhoneEnvRC` is reachable on the base view, the allomorph-HVO path
    is vacuous too, and the #268 claim for AddPhoneEnv/RemovePhoneEnv
    must be WITHDRAWN rather than fixed. Measure before deciding.

P11: offline suite stays at 439 passed / 2 failed / (526 + N)
     deselected, red set exactly the two foreign
     `TestPhase2JoinOrOpen` failures. Write the exact N into this file
     BEFORE running.

N = 8 (cycle-2 new live-marked tests, written BEFORE running the
offline suite): 6 new methods in the new file
`tests/operations/test_260_environment_resolver_gate.py`
(TestP6DirectAttributeAccess x4, TestP6bSyncableProperties x1,
TestP7SilentLeftContextLoss x1), plus 2 new methods appended to
`tests/operations/test_260_env_resolver_hvo_gate.py`
(TestHvoPathBothIntCastAddPhoneEnv,
TestHvoPathBothIntCastRemovePhoneEnv -- the T4/P10 both-int-HVO
coverage). Cycle-1's N=2 is already baked into the 528 baseline
(526 + 2), so P11's expected deselected count is 528 + 8 = 536.
