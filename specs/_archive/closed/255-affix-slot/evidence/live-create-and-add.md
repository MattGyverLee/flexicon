# Live evidence: create an affix slot and add it to a template

Issue #255. Target sandbox (`target_sandbox`), objects prefixed `TEST_`.

## Commands

```
python -m pytest tests/operations/test_issue255_affix_slot.py -m "not requires_live_project" -q
```

10 passed in 0.58s

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue255_affix_slot_live.py -m requires_live_project -q
```

1 passed in 2.12s

```
python -c "import json; print(json.load(open('tests/live_status.json', encoding='utf-8'))['run_mode'])"
```

live

## run_mode

live

`tests/live_status.json` `run_timestamp` 2026-09-23T06:10:54Z. POSOperations add status: pass.

## Pre-state

Read before the writes, from the sandbox copy of Target:

- POS HVO 2706 (an existing category; `created_pos` false)
- Affix slot count via `GetAffixSlots`: 0
- Chosen side: prefix (`PrefixSlotsRS`)
- `PrefixSlotsRS.Count` on the new template, before `AddSlotToTemplate`: 0

## Post-state

Values read back from the LCM after the writes, not the arguments just passed in:

- Slot name via a fresh `GetAffixSlots` hit, then `ITsString(Name.get_String(DefaultAnalWs)).Text`: `TEST_PossConcord`
- `Optional` on that same re-fetched slot: false
- Slot HVO: 10442
- After `AddSlotToTemplate(..., "Prefix")` and before the index insert, `PrefixSlotsRS.Count` was 1 and contained HVO 10442
- Second slot `TEST_NounClass` (HVO 10444) inserted at index 0. Re-read `PrefixSlotsRS` HVOs: 10444, 10442
- Post slot count via `GetAffixSlots`: 2
- Post `PrefixSlotsRS.Count`: 2
- Index 99 raised `FP_ParameterError` and the HVO order stayed 10444, 10442
- Concrete slot boolean properties: CanDelete, IsValidObject, Optional
- `IMoInflAffixSlot` interface boolean properties: Optional
- Concrete `PrefixSlotsRS` methods present: Add, Insert. InsertAt was absent.

## Result

PASS
