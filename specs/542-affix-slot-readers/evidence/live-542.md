# Issue #542 live evidence (cycle 2: Sena 3 sandbox, no Target writes)

## Why this supersedes the cycle-1 evidence

Cycle 1 used the `target_project` fixture, writing in-place to the real
`Target` project. Per binding user directive for cycle 2, live write tests
may write ONLY to Sena 3; nothing may write to Target. This run uses the
`sena3_sandbox` fixture -- a fresh tempdir copy of the Sena 3 `.fwbackup`,
unzipped, opened write-enabled, and discarded on teardown. Target was never
opened write-enabled during this run.

## Environment

FieldWorks 9 is installed on this runner (`C:\Program Files\SIL\FieldWorks 9\`),
so `SIL.LCModel` loads as the real .NET assembly for the whole pytest
session. `tests/fixtures/Sena 3 2026-06-09 1645.fwbackup` was copied (not
moved) from `C:\Github\flexicon\tests\fixtures\` into this worktree so the
`sena3_sandbox` fixture (`tests/flex_plugin.py` ~L1285) can find it; the
copy is covered by the existing `.gitignore` pattern
`tests/fixtures/*.fwbackup` (confirmed with `git check-ignore -v`) and does
not appear in `git status`.

## Fixture used

`sena3_sandbox` (function-scoped, `tests/flex_plugin.py::sena3_sandbox`):
unzips the Sena 3 `.fwbackup` into a fresh tempdir per test, opens the
`.fwdata` write-enabled (`writeEnabled=True, undoable=False`), yields the
project, and on teardown closes the project and deletes the tempdir. No
in-place `sena3_project` fixture was needed -- the sandbox worked without
modification, so the fallback plan (adding an in-place fixture to
`flex_plugin.py`) was not used.

## Command (exact, as run)

```
cd C:\Github\flexicon-542
python -m pytest -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue542_affix_slot_readers_live.py -m requires_live_project -q
```

(Bash-tool equivalents used in this session: `export FLEXLIBS_REQUIRE_LIVE=1`.)

## Result

Offline (non-live) run:

```
5 failed, 2506 passed, 1040 deselected, 16 warnings in 11.52s
```

The 5 failures are pre-existing and unrelated to this change -- confirmed
by `git stash -u` (reverting the test-file edit) and re-running the same
command: identical 5 failures
(`tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies`
and 4 tests in `tests/operations/test_morphrule_duplicate_deep.py`), same
2506 passed. No regression from this change.

Live run:

```
....
4 passed in 8.59s
```

## run_mode

`tests/live_status.json` after the live run:

```json
"run_mode": "live",
"run_timestamp": "2026-09-26T22:39:37Z"
```

`by_class.POSOperations.read.status` = `"pass"`, all four tests listed:
`test_slot_readers_round_trip_via_object_and_hvo`,
`test_get_affix_slots_returns_affixslot_wrapper`,
`test_bad_slot_input_raises_parameter_error`,
`test_sena3_affix_slots_are_readable_if_present`.

## Pre-state / post-state read back from the LCM

Test `test_slot_readers_round_trip_via_object_and_hvo` (all against the
Sena 3 sandbox):

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

Test `test_get_affix_slots_returns_affixslot_wrapper` (Sena 3 sandbox):

| Step | Read back via | Value |
|---|---|---|
| `CreateAffixSlot(pos, "TEST_542_wrap_slot", optional=True)` | `GetAffixSlots(pos)[0]` | `isinstance(..., AffixSlot)` True; `.name == "TEST_542_wrap_slot"`; `.optional is True`; `.affixes == []` |
| Backward compat | `wrapped.Hvo` / `wrapped.Optional` (raw LCM proxy) | matches raw `slot.Hvo`; `True` |
| Wrapper into `AddSlotToTemplate` | `AffixTemplate(template).prefix_slots[0]` | `isinstance(..., AffixSlot)`; `.name == "TEST_542_wrap_slot"` |

Test `test_bad_slot_input_raises_parameter_error` (Sena 3 sandbox): passing
an `IPartOfSpeech` (not a slot) to `GetSlotName` raises `FP_ParameterError`
-- confirms the slot resolver really casts instead of silently returning
the wrong type.

Test `test_sena3_affix_slots_are_readable_if_present`: now runs against the
same `sena3_sandbox` project already open for the other tests in this file
(previously it opened the real `Sena 3` project directly, read-only, as a
separate project handle). Iterated every POS's `GetAffixSlots()` and, for
any slot found, read `.name` (str), `.optional` (bool), and
`GetAffixesInSlot(slot)` (list) without raising.

## Cleanup

Every test in this file that creates objects (`TEST_542_pos`,
`TEST_542_wrap_pos`, `TEST_542_bad_pos`, and their slots/entries/templates)
deletes them in a `finally:` block. Because all writes went to a tempdir
sandbox that is deleted on fixture teardown regardless, no cleanup can
leak into a real project even if a `finally:` block were skipped.

## No writes to Target

Confirmed: this test file no longer imports or references `target_project`
or `target_sandbox` anywhere. The only project handle opened by any test in
this file is `sena3_sandbox`, a disposable tempdir copy. The real Target
project (`C:\ProgramData\SIL\FieldWorks\Projects\Target\Target.fwdata`) was
not opened write-enabled at any point during this verification.
`scripts/restore_target.py` was not run.

## Pass/fail

**PASS: live-verified.** `run_mode: "live"`, both required invocations run,
pre/post LCM state re-queried (not just asserted against the value passed
in), all writes confined to a Sena 3 sandbox tempdir, zero writes to
Target.
