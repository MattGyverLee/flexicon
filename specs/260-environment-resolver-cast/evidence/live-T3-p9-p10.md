# live-T3-p9-p10.md -- P9 re-run after the AllomorphOperations cast landed

## Command

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_260_env_resolver_hvo_gate.py -m requires_live_project -q
```

Run against `target_sandbox`, AFTER both T2's `EnvironmentOperations.
__ResolveObject` cast AND T3's `AllomorphOperations.__GetEnvironmentObject`
cast had landed.

## Raw result (verbatim)

```
4 passed, 37 warnings in 5.26s
```

## `tests/live_status.json` (verbatim, this run)

```json
{
  "by_class": {
    "AllomorphOperations": {
      "add": {"last_verified": null, "status": "untested", "tests": []},
      "delete": {"last_verified": null, "status": "untested", "tests": []},
      "modify": {
        "last_verified": "2026-09-08",
        "status": "pass",
        "tests": [
          "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathCastAddPhoneEnv::test_add_phone_env_via_genuine_hvo_int_writes_through_concrete_env",
          "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathCastRemovePhoneEnv::test_remove_phone_env_via_genuine_hvo_int_writes_through_concrete_env",
          "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathBothIntCastAddPhoneEnv::test_add_phone_env_via_genuine_hvo_int_on_both_args",
          "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathBothIntCastRemovePhoneEnv::test_remove_phone_env_via_genuine_hvo_int_on_both_args"
        ]
      },
      "read": {"last_verified": null, "status": "untested", "tests": []},
      "reorder": {"last_verified": null, "status": "untested", "tests": []}
    }
  },
  "by_test": {
    "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathBothIntCastAddPhoneEnv::test_add_phone_env_via_genuine_hvo_int_on_both_args": {"duration_seconds": 0.033, "operations_class": "AllomorphOperations", "phase": "modify", "status": "pass"},
    "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathBothIntCastRemovePhoneEnv::test_remove_phone_env_via_genuine_hvo_int_on_both_args": {"duration_seconds": 0.036, "operations_class": "AllomorphOperations", "phase": "modify", "status": "pass"},
    "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathCastAddPhoneEnv::test_add_phone_env_via_genuine_hvo_int_writes_through_concrete_env": {"duration_seconds": 0.205, "operations_class": "AllomorphOperations", "phase": "modify", "status": "pass"},
    "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathCastRemovePhoneEnv::test_remove_phone_env_via_genuine_hvo_int_writes_through_concrete_env": {"duration_seconds": 0.035, "operations_class": "AllomorphOperations", "phase": "modify", "status": "pass"}
  },
  "run_mode": "live",
  "run_timestamp": "2026-09-08T16:23:06Z",
  "uncategorized_live_tests": []
}
```

`run_mode: "live"` -- genuine live run.

## P9 adjudication

**P9 HELD.** All four tests -- the two original single-HVO gate tests
AND the two T4 both-int-HVO additions -- stay green and UNCHANGED after
the `AllomorphOperations.__GetEnvironmentObject` cast landed. In
particular `RemovePhoneEnv`'s `if env in allomorph.PhoneEnvRC` membership
test (the identity hazard flagged in tasks.md T3 -- casting mints a NEW
pythonnet wrapper, so `in` now depends on .NET equality of a re-wrapped
object) still resolves correctly: `TestHvoPathCastRemovePhoneEnv` and
`TestHvoPathBothIntCastRemovePhoneEnv` both pass, confirmed by a FRESH
`GetPhoneEnv` re-fetch showing the environment HVO absent after removal.
Nothing flipped; the cycle-1 falsification stands.

## P10 (T4) -- already reported in live-T2-red-p6-p6b-p7.md

`hasattr(bare_allo, "PhoneEnvRC")` measured `False` live (same session as
the T2 RED run). **P10 HELD.** Disposition: added
`TestHvoPathBothIntCastAddPhoneEnv` / `TestHvoPathBothIntCastRemovePhoneEnv`
to `tests/operations/test_260_env_resolver_hvo_gate.py`, passing BOTH the
allomorph and the environment as genuine int HVOs, each preceded by a
live `not hasattr(bare_allo, "PhoneEnvRC")` precondition assertion. The
flexicon#268 "AddPhoneEnv/RemovePhoneEnv now have live coverage" claim is
now true for both the allomorph-HVO and environment-HVO halves of the
call, not just the environment half.
