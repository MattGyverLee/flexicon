# live-T2-p2-falsification.md

## Command (run against UNMODIFIED source -- verified via `git diff --stat`
## showing no change to AllomorphOperations.py before this run)

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_260_env_resolver_hvo_gate.py -m requires_live_project -q
```

Ran against `target_sandbox` (tempdir copy of the Target `.fwbackup`).

## Result: 2 passed (expected RED, got GREEN)

```
..                                                                       [100%]
[OK] Wrote D:\Github\_Projects\_LEX\flexicon\tests\test_results.json (2 tests recorded)
...
2 passed, 19 warnings in 4.13s
```

`tests/live_status.json` for this run (verbatim):

```json
{
  "by_class": {
    "AllomorphOperations": {
      "add": { "last_verified": null, "status": "untested", "tests": [] },
      "delete": { "last_verified": null, "status": "untested", "tests": [] },
      "modify": {
        "last_verified": "2026-09-08",
        "status": "pass",
        "tests": [
          "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathCastAddPhoneEnv::test_add_phone_env_via_genuine_hvo_int_writes_through_concrete_env",
          "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathCastRemovePhoneEnv::test_remove_phone_env_via_genuine_hvo_int_writes_through_concrete_env"
        ]
      },
      "read": { "last_verified": null, "status": "untested", "tests": [] },
      "reorder": { "last_verified": null, "status": "untested", "tests": [] }
    }
  },
  "by_test": {
    "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathCastAddPhoneEnv::test_add_phone_env_via_genuine_hvo_int_writes_through_concrete_env": {
      "duration_seconds": 0.19,
      "operations_class": "AllomorphOperations",
      "phase": "modify",
      "status": "pass"
    },
    "tests/operations/test_260_env_resolver_hvo_gate.py::TestHvoPathCastRemovePhoneEnv::test_remove_phone_env_via_genuine_hvo_int_writes_through_concrete_env": {
      "duration_seconds": 0.032,
      "operations_class": "AllomorphOperations",
      "phase": "modify",
      "status": "pass"
    }
  },
  "run_mode": "live",
  "run_timestamp": "2026-09-08T15:28:12Z",
  "uncategorized_live_tests": []
}
```

`run_mode: "live"` -- genuine live run, not a mock degradation.

Both `AddPhoneEnv(allomorph, env_hvo_int)` and
`RemovePhoneEnv(allomorph, env_hvo_int)` **succeeded** against the
UNMODIFIED `__GetEnvironmentObject` (bare `ICmObject`, no cast), and
the write was confirmed present/absent via a fresh
`sandbox.Allomorphs.GetPhoneEnv(sandbox.Object(allo.Hvo))` re-fetch in
both tests.

## Adjudication: P2 FALSIFIED

P2 predicted `PhoneEnvRC.Add(a bare ICmObject)` would raise
`TypeError` / `System.InvalidCastException` / `ArgumentException`
because it "does not bind to
`ILcmReferenceCollection[IPhEnvironment].Add`". It does bind, and the
write persists correctly.

## Why -- distinguishing this from the T8 (`__GetAllomorphObject`)
## attribute-access defect

T8's defect (and its live falsifier) was direct **Python attribute
access** on the bare wrapper -- `hasattr(bare, "Form")` /
`hasattr(bare, "MsEnvFeaturesOA")` is `False` because pythonnet's
Python-side wrapper only exposes members declared on the *static*
interface it was constructed against (`ICmObject`), regardless of what
the underlying .NET object actually implements.

Passing that SAME bare wrapper as an **argument to a strongly-typed
.NET method** (`ILcmReferenceCollection<IPhEnvironment>.Add(T item)`)
is a different code path: the CLR resolves the call against the
argument's actual **runtime type**, not pythonnet's Python-side static
wrapper type. The underlying managed object genuinely implements
`IPhEnvironment` (it reflects as `SIL.LCModel.DomainImpl.PhEnvironment`,
per `live-T1-reflection.md`), so the CLR successfully binds the
argument to the collection's generic `Add`/`Remove`, with no cast
needed on the Python side.

In other words: at these two call sites, the missing cast in
`__GetEnvironmentObject` has **no observable behavioral effect**,
because neither caller does attribute access on the resolver's return
value before handing it to `PhoneEnvRC` -- they hand it straight to a
.NET collection method, and .NET's own dynamic dispatch does the
"casting" for free.

## Per `standing_rule_empty_falsifier_set_is_not_a_pass`

This cast has **no behavioral falsifier at its two call sites**.
Per the standing rule, this is reported as:

**contract/docstring fix; behavioral axis UNMEASURED.**

This is NOT a pass on P4 (P4 is UNMEASURED, not HELD -- see
`reviews/cycle1-programmer.md`), and this green run is NOT evidence
the cast was behaviorally needed. No alternate call site was sought
out and no synthetic assertion was added to manufacture a RED; per
instruction, this is flagged for a lead ruling instead, and the cast
itself was NOT applied to `AllomorphOperations.py` pending that ruling.
