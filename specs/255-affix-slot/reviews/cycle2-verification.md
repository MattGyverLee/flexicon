# Cycle 2 verification: issue #255

**Overall verdict: PASS**

**Commit:** `0672b0b497b330b59274fc2ef2fb47e6ad825679`
**Live run:** yes | **run_mode:** live
**Evidence:** `specs/255-affix-slot/evidence/live-cycle2.md`
**Project:** Target (`target_sandbox`, tempdir copy of the Target `.fwbackup`)
**Production code edited by this verification:** no

`CreateAffixSlot` is `POSOperations.py` line 871. `AddSlotToTemplate` is `MorphRuleOperations.py` line 432. `SetInflAffMsaSlots` is not in the tree. Issue #258 was not implemented.

Prior evidence at `specs/255-affix-slot/evidence/live-create-and-add.md` was not treated as proof. The commands below were run from the repo root in this session.

## Commands and run_mode

```
python -m pytest tests/operations/test_issue255_affix_slot.py -m "not requires_live_project" -q
```

10 passed in 0.64s

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue255_affix_slot_live.py -m requires_live_project -q
```

1 passed in 2.29s

```
python -c "import json; print(json.load(open('tests/live_status.json', encoding='utf-8'))['run_mode'])"
```

`live`

`tests/live_status.json` `run_timestamp` 2026-09-23T06:18:01Z. `by_test` records `test_create_slot_and_add_to_prefix_side` as pass (0.069s), phase `POSOperations` / `add`.

## Claim vs. observed

| Claim | Observed live | Status |
|---|---|---|
| `CreateAffixSlot(..., optional=False)` is owned by the POS and visible to a fresh `GetAffixSlots` | POS HVO 2706, pre count 0. Re-fetched slot HVO 10442, name `TEST_PossConcord`, `Optional` false. Post count 2. | PASS |
| `AddSlotToTemplate(..., "Prefix")` appends on `PrefixSlotsRS` | Pre count 0. Slot HVO 10442 present on the re-fetched sequence. | PASS |
| `index=0` uses `Insert` | Second slot HVO 10444 is index 0. Re-read HVOs: 10444, 10442. Concrete methods on `PrefixSlotsRS`: Add, Insert. | PASS |
| Out-of-range index does not change the sequence | Index 99 raised `FP_ParameterError`. HVO order stayed 10444, 10442. | PASS |
| Default `optional=True` when the argument is omitted, read from a fresh `GetAffixSlots` | Probe: `CreateAffixSlot(pos, "TEST_C2_DefaultOptional")`. Re-fetched HVO 10442, name matches, `Optional` true. | PASS |
| suffix, proclitic, and enclitic receive the slot | Probe, re-fetched template: `SuffixSlotsRS` [10444], `ProcliticSlotsRS` [10445], `EncliticSlotsRS` [10446]. Each count went 0 to 1. `PrefixSlotsRS` stayed empty. | PASS |

The official test's `second_optional_read_back: true` is the object just returned from `CreateAffixSlot(..., optional=True)`, not a fresh `GetAffixSlots` read, and the argument was passed explicitly. The default-omitted read-back is the gap probe, not that field.

## Gap probe

A temporary test used the `target_sandbox` fixture and the shipped methods, then was deleted. It did not remain in the tree.

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/_tmp_cycle2_255_probe.py -m requires_live_project -q
```

1 passed in 2.09s.

Pre-state on that fresh sandbox: POS HVO 2706, `GetAffixSlots` count 0, all four side counts 0. Post-state: default `Optional` true on the re-fetched slot; the three non-prefix sequences held the HVOs in the table above; post slot count 4.

`Insert` was not repeated on suffix, proclitic, or enclitic. Those sides were appended (`index` omitted). That remaining insert-on-other-sides check is a coverage note. The prefix `Insert(0)` read-back already passed, and the three side sequences returned the slot HVOs.

## No code change made

`git diff` for `POSOperations.py` and `MorphRuleOperations.py` is empty. The probe file was removed after the run. `tests/live_status.json` was then refreshed by the official live command cited above, so it names `test_issue255_affix_slot_live.py` and `run_mode` live.

## Blockers

None. FieldWorks and the Target backup were available. `run_mode` was not mock.

## Recommendation

APPROVE
