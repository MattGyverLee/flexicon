# live-T2-green-p6-p6b-p8.md -- GREEN, after the guarded cast

## Command

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_260_environment_resolver_gate.py -m requires_live_project -q
```

Run against `target_sandbox`, with the guarded cast landed in
`Grammar/EnvironmentOperations.py __ResolveObject`.

## Raw result (verbatim)

```
6 passed, 23 warnings in 6.67s
```

## `tests/live_status.json` (verbatim, this run)

```json
{
  "by_class": {
    "EnvironmentOperations": {
      "add": {"last_verified": null, "status": "untested", "tests": []},
      "delete": {"last_verified": null, "status": "untested", "tests": []},
      "modify": {
        "last_verified": "2026-09-08",
        "status": "pass",
        "tests": [
          "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_name_via_genuine_hvo_int_reads_concrete_name",
          "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_name_via_genuine_hvo_int_writes_through_concrete_name",
          "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_string_representation_via_genuine_hvo_int_reads_concrete_notation",
          "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_string_representation_via_genuine_hvo_int_writes_through"
        ]
      },
      "read": {
        "last_verified": "2026-09-08",
        "status": "pass",
        "tests": [
          "tests/operations/test_260_environment_resolver_gate.py::TestP6bSyncableProperties::test_get_syncable_properties_via_genuine_hvo_int_reads_dict",
          "tests/operations/test_260_environment_resolver_gate.py::TestP7DiscoveredWrongPropertyName::test_left_and_right_context_are_reference_atomic_not_owning_atomic"
        ]
      },
      "reorder": {"last_verified": null, "status": "untested", "tests": []}
    }
  },
  "by_test": {
    "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_name_via_genuine_hvo_int_reads_concrete_name": {"duration_seconds": 0.058, "operations_class": "EnvironmentOperations", "phase": "modify", "status": "pass"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_get_string_representation_via_genuine_hvo_int_reads_concrete_notation": {"duration_seconds": 0.029, "operations_class": "EnvironmentOperations", "phase": "modify", "status": "pass"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_name_via_genuine_hvo_int_writes_through_concrete_name": {"duration_seconds": 0.013, "operations_class": "EnvironmentOperations", "phase": "modify", "status": "pass"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP6DirectAttributeAccess::test_set_string_representation_via_genuine_hvo_int_writes_through": {"duration_seconds": 0.009, "operations_class": "EnvironmentOperations", "phase": "modify", "status": "pass"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP6bSyncableProperties::test_get_syncable_properties_via_genuine_hvo_int_reads_dict": {"duration_seconds": 0.014, "operations_class": "EnvironmentOperations", "phase": "read", "status": "pass"},
    "tests/operations/test_260_environment_resolver_gate.py::TestP7DiscoveredWrongPropertyName::test_left_and_right_context_are_reference_atomic_not_owning_atomic": {"duration_seconds": 0.024, "operations_class": "EnvironmentOperations", "phase": "read", "status": "pass"}
  },
  "run_mode": "live",
  "run_timestamp": "2026-09-08T16:21:09Z",
  "uncategorized_live_tests": []
}
```

`run_mode: "live"` -- genuine live run.

## P8 adjudication

**P8 PARTIALLY HELD.** GetName / SetName / GetStringRepresentation /
SetStringRepresentation all succeed through the int-HVO path post-cast,
re-read from a fresh re-fetch (TestP6DirectAttributeAccess, 4/4 green).
GetSyncableProperties reads the concrete Name value through the int-HVO
path post-cast (TestP6bSyncableProperties, green). The GetLeftContext leg
of P8 does **NOT** hold: see the P7 correction below -- the cast does not
make `GetLeftContextPattern` return a populated context, because that
method (and `GetRightContextPattern`/`Duplicate`'s deep-copy block) reads
a property name (`LeftContextOA`/`RightContextOA`) that does not exist
anywhere in the LCM API. This is a separate, pre-existing bug, out of
scope for T2.

## P9 -- re-run of the AllomorphOperations gate after the T2 cast landed

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_260_env_resolver_hvo_gate.py -m requires_live_project -q
```

```
4 passed, 37 warnings in 4.81s
```

All four tests (the original two plus the two T4 both-int-HVO additions)
stay green and unchanged after `EnvironmentOperations.__ResolveObject`'s
cast landed -- expected, since `AllomorphOperations.__GetEnvironmentObject`
is a completely separate resolver, untouched by this commit. **P9 (partial)
HELD** for this leg; the full P9 re-run (after T3's AllomorphOperations
cast also lands) is in a separate evidence file.

## P7 correction -- the wrong-property-name discovery

See the header of `tests/operations/test_260_environment_resolver_gate.py`
and `TestP7DiscoveredWrongPropertyName` for the full mechanism. Summary:
`clr.GetClrType(IPhEnvironment).GetProperties()` lists `LeftContextRA` /
`RightContextRA` (Reference Atomic) but no `LeftContextOA` /
`RightContextOA` (Owning Atomic) anywhere -- confirmed both on the
interface and on the sole concrete implementation `PhEnvironment`. The
original P7 hypothesis (cast fixes the silent None) is **FALSIFIED**:
the guarded cast does not change `GetLeftContextPattern`'s behaviour at
all, because the property it reads does not exist, cast or not. Flagged
for a new issue (see cycle2-programmer.md); not fixed in this task.
