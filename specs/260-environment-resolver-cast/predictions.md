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
