# live-T2-red-p6-p6b-p7.md -- RED, unmodified source

## Command

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_260_environment_resolver_gate.py -m requires_live_project -q
```

Run against `target_sandbox` (tempdir copy of the Target `.fwbackup`),
`Grammar/EnvironmentOperations.py` UNMODIFIED (confirmed via `git status`/
`git diff` showing no changes to that file at the time of this run).

## Raw result (verbatim)

```
6 failed, 28 warnings in 5.58s
FAILED tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_name_via_genuine_hvo_int_reads_concrete_name
FAILED tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_name_via_genuine_hvo_int_writes_through_concrete_name
FAILED tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_string_representation_via_genuine_hvo_int_reads_concrete_notation
FAILED tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_string_representation_via_genuine_hvo_int_writes_through
FAILED tests/operations/test_260_environment_resolver_gate.py::TestP6bSyncableProperties::test_get_syncable_properties_via_genuine_hvo_int_reads_dict
FAILED tests/operations/test_260_environment_resolver_gate.py::TestP7SilentLeftContextLoss::test_get_left_context_pattern_via_genuine_hvo_int_returns_populated_context
```

Key failure bodies, verbatim:

### P6 -- GetName

```
name = sandbox.Environments.GetName(env_hvo)
...
env = self.__ResolveObject(env_or_hvo)
wsHandle = self.__WSHandle(wsHandle)
name = ITsString(env.Name.get_String(wsHandle)).Text
AttributeError: 'ICmObject' object has no attribute 'Name'
```

### P6b -- GetSyncableProperties (the sync-path falsifier)

```
env = self.__ResolveObject(item)
...
for prop_name in ["Name", "Description", "StringRepresentation"]:
    prop_obj = getattr(env, prop_name)
AttributeError: 'ICmObject' object has no attribute 'Name'
```
(EnvironmentOperations.py:700, first property in the loop.)

### P7 -- GetLeftContextPattern (the silent variant)

```
AssertionError: GetLeftContextPattern(hvo) silently returned None for an
environment whose LeftContextOA is genuinely populated (confirmed via the
already-typed object above) -- the hasattr-gated silent-loss defect (P7).
assert None is not None
```
No exception raised -- confirmed via the already-typed-object precondition
(`already_typed_result is not None` passed) that the left context was
genuinely populated before the HVO-int call silently returned `None`.

## `tests/live_status.json` (verbatim, this run)

```json
{
  "by_class": {
    "EnvironmentOperations": {
      "add": {"last_verified": null, "status": "untested", "tests": []},
      "delete": {"last_verified": null, "status": "untested", "tests": []},
      "modify": {
        "last_verified": null,
        "status": "fail",
        "tests": [
          "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_name_via_genuine_hvo_int_reads_concrete_name",
          "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_name_via_genuine_hvo_int_writes_through_concrete_name",
          "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_string_representation_via_genuine_hvo_int_reads_concrete_notation",
          "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_string_representation_via_genuine_hvo_int_writes_through",
          "tests/operations/test_260_environment_resolver_gate.py::TestP7SilentLeftContextLoss::test_get_left_context_pattern_via_genuine_hvo_int_returns_populated_context"
        ]
      },
      "read": {
        "last_verified": null,
        "status": "fail",
        "tests": [
          "tests/operations/test_260_environment_resolver_gate.py::TestP6bSyncableProperties::test_get_syncable_properties_via_genuine_hvo_int_reads_dict"
        ]
      },
      "reorder": {"last_verified": null, "status": "untested", "tests": []}
    }
  },
  "by_test": {
    "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_name_via_genuine_hvo_int_reads_concrete_name": {"duration_seconds": 0.047, "operations_class": "EnvironmentOperations", "phase": "modify", "status": "fail"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_string_representation_via_genuine_hvo_int_reads_concrete_notation": {"duration_seconds": 0.027, "operations_class": "EnvironmentOperations", "phase": "modify", "status": "fail"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_name_via_genuine_hvo_int_writes_through_concrete_name": {"duration_seconds": 0.007, "operations_class": "EnvironmentOperations", "phase": "modify", "status": "fail"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_string_representation_via_genuine_hvo_int_writes_through": {"duration_seconds": 0.007, "operations_class": "EnvironmentOperations", "phase": "modify", "status": "fail"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP6bSyncableProperties::test_get_syncable_properties_via_genuine_hvo_int_reads_dict": {"duration_seconds": 0.011, "operations_class": "EnvironmentOperations", "phase": "read", "status": "fail"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP7SilentLeftContextLoss::test_get_left_context_pattern_via_genuine_hvo_int_returns_populated_context": {"duration_seconds": 0.054, "operations_class": "EnvironmentOperations", "phase": "modify", "status": "fail"}
  },
  "run_mode": "live",
  "run_timestamp": "2026-09-08T16:12:52Z",
  "uncategorized_live_tests": []
}
```

`run_mode: "live"` -- genuine live run, not a mock degradation.

## P10 measurement (T4), same live session

Throwaway probe `tests/operations/test_260_p10_scratch_measure.py` (deleted
immediately after capture; not part of the permanent suite), run in the
same invocation:

```
P10 MEASUREMENT: hasattr(bare_allo, 'PhoneEnvRC') = False
```

**P10 HELD.** `PhoneEnvRC` is subtype-only (unreachable on a bare
`project.Object(allo.Hvo)` view) -- see cycle2-programmer.md for the T4
disposition.

## Note on a pre-existing LCM quirk hit while building the P7 fixture

Building a genuinely-populated `LeftContextOA` for the P7 fixture (no
naturally-occurring example exists in Target -- 0 environments -- or Sena 3
-- 44 environments, 0 with a populated context, also measured live this
session) surfaced an unrelated LCM quirk: the FIRST
`ctx.FeatureStructureRA = phoneme` assignment on a freshly
`OwningAtomic`-attached `IPhSimpleContextSeg` raises
`System.NullReferenceException` from
`PhSimpleContextSeg.SetFeatureStructureRA`; an identical second call on the
SAME object then succeeds. The fixture retries once (see the comment at the
call site in `test_260_environment_resolver_gate.py`). This is orthogonal to
the `__ResolveObject` cast under test in this feature -- noted for the
record, not filed, out of scope for #260.
