# Issue #542 live evidence

## Environment

FieldWorks 9 is installed on this runner (`C:\Program Files\SIL\FieldWorks 9\`),
so `SIL.LCModel` loads as the real .NET assembly for the whole pytest
session -- both the "offline" and the live-required run. The `Target`
project exists in-place at
`C:\ProgramData\SIL\FieldWorks\Projects\Target\Target.fwdata`, and `Sena 3`
at `C:\ProgramData\SIL\FieldWorks\Projects\Sena 3\Sena 3.fwdata`. No
`tests/fixtures/*.fwbackup` file is present on this runner, so the
`target_sandbox`/`sena3_sandbox` fixtures (which unzip a `.fwbackup`) are
unavailable; the tests use `target_project` (in-place, write-enabled,
capture-and-restore in `finally:`, `TEST_542_` prefix) instead, which
CLAUDE.md sanctions equally for in-place writes.

## Command (exact, as run)

```
cd C:\Github\flexicon-542
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue542_affix_slot_readers_live.py -m requires_live_project -q
```

## Result

```
....
4 passed in 5.52s
```

## run_mode

`tests/live_status.json` after the run:

```json
"run_mode": "live",
"run_timestamp": "2026-09-26T22:31:06Z"
```

`by_class.POSOperations.read.status` = `"pass"`, all four tests listed.

## Pre-state / post-state read back from the LCM

Test `test_slot_readers_round_trip_via_object_and_hvo`:

| Step | Read back via | Value |
|---|---|---|
| After `CreateAffixSlot(..., "TEST_542_slot_req", optional=False)` | `GetSlotName(slot)` / `GetSlotName(hvo)` | `"TEST_542_slot_req"` (both) |
| Same slot | `IsSlotOptional(slot)` | `False` |
| After `CreateAffixSlot(..., "TEST_542_slot_opt", optional=True)` | `IsSlotOptional(slot)` / `IsSlotOptional(hvo)` | `True` (both) |
| After `SetSlotName(slot_required, "TEST_542_slot_req_renamed")` | Fresh `IMoInflAffixSlot(project.Object(hvo))`, `ITsString(...Name.get_String(analWs)).Text` (re-queried from the LCM, not the value passed in) | `"TEST_542_slot_req_renamed"` |
| Same, via wrapper | `GetSlotName(hvo)` | `"TEST_542_slot_req_renamed"` |
| After `SetSlotOptional(slot_required, True)` | Fresh `IMoInflAffixSlot(project.Object(hvo)).Optional` | `True` |
| Same | `IsSlotOptional(hvo)` | `True` |
| After `SetSlotOptional(slot_optional_hvo, False)` | Fresh `IMoInflAffixSlot(...).Optional` | `False` |
| After `MSA.CreateInflAff(sense, pos, slots=[slot_required])` | `GetAffixesInSlot(slot_required)` -> `{Hvo}` | `{msa_hvo}` |
| Cross-check | `MSA.GetInflAffMsaSlots(sense)` (#543, inverse lookup) -> `{Hvo}` | `{slot_required_hvo}` (agrees) |
| Same, via HVO | `GetAffixesInSlot(req_hvo)` | `{msa_hvo}` |
| Untouched optional slot | `GetAffixesInSlot(slot_optional)` | `[]` |

Test `test_get_affix_slots_returns_affixslot_wrapper`:

| Step | Read back via | Value |
|---|---|---|
| `CreateAffixSlot(pos, "TEST_542_wrap_slot", optional=True)` | `GetAffixSlots(pos)[0]` | `isinstance(..., AffixSlot)` True; `.name == "TEST_542_wrap_slot"`; `.optional is True`; `.affixes == []` |
| Backward compat | `wrapped.Hvo` / `wrapped.Optional` (raw LCM proxy) | matches raw `slot.Hvo`; `True` |
| Wrapper into `AddSlotToTemplate` | `AffixTemplate(template).prefix_slots[0]` | `isinstance(..., AffixSlot)`; `.name == "TEST_542_wrap_slot"` |

Test `test_bad_slot_input_raises_parameter_error`: passing a `IPartOfSpeech`
(not a slot) to `GetSlotName` raises `FP_ParameterError` -- confirms
`__ResolveSlot` really casts instead of silently returning the wrong type.

Test `test_sena3_affix_slots_are_readable_if_present`: opened Sena 3
directly, read-only (`OpenProject("Sena 3", writeEnabled=False)`, no
sandbox fixture needed since reads are unrestricted). Iterated every POS's
`GetAffixSlots()` and, for any slot found, read `.name` (str), `.optional`
(bool), and `GetAffixesInSlot(slot)` (list) without raising. Passed in
2.35s.

## Cleanup verification

A follow-up pytest run (removed after use) opened `target_project` and
confirmed zero POS objects with `"TEST_542"` in the name remain in Target
after the suite's `finally:` blocks ran:

```
1 passed in 2.24s   # test_no_leaked_test542_pos
```

## Offline run (companion, not a substitute)

```
python -m pytest -m "not requires_live_project" -q
```

```
5 failed, 2506 passed, 1040 deselected, 16 warnings in 11.06s
```

The 5 failures are pre-existing on `origin/main` (5b2631a) before this
branch's changes -- confirmed via `git stash` + re-run
(`tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies`
and 4 tests in `tests/operations/test_morphrule_duplicate_deep.py`, all
failing on an unrelated `AffixTemplatesOS` Mock-iteration issue). All 14
new tests in `tests/operations/test_issue542_affix_slot_readers_offline.py`
pass; no existing passing test regressed.

## Pass/fail

**PASS: live-verified.** `run_mode: "live"`, both required invocations
run, pre/post LCM state re-queried (not just asserted against the value
passed in), Target left clean.
