# Live evidence: cycle 4 independent verification of #255

Commit `6abff1cdefd832e4913d8bcf258fb3696c48cf99`. Target sandbox (`target_sandbox`), objects prefixed `TEST_`. Production code was not edited. Issue #258 was not implemented.

`specs/255-affix-slot/evidence/live-cycle3.md` was not used as proof. The commands below were run from the repo root in this session. Each pytest invocation opens a fresh tempdir copy of the Target backup per test, so the same HVO number in the two live tests is not the same object.

## Commands

```
python -m pytest tests/operations/test_issue255_affix_slot.py -m "not requires_live_project" -q
```

13 passed in 0.62s

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue255_affix_slot_live.py -m requires_live_project -q
```

2 passed in 3.00s

```
python -c "import json; print(json.load(open('tests/live_status.json', encoding='utf-8'))['run_mode'])"
```

live

## run_mode

live

`tests/live_status.json` `run_timestamp` 2026-09-23T06:31:32Z. Both recorded tests passed: `test_create_slot_and_add_to_prefix_side` (0.059s) and `test_ancestor_slot_accepted_descendant_slot_rejected` (0.03s). Phase `POSOperations` / `add`.

## Reflected property

`clr.GetClrType(IPartOfSpeech).GetProperty("AllAffixSlots")` during the live test:

- Name: `AllAffixSlots`
- Type: `System.Collections.Generic.IEnumerable`1[[SIL.LCModel.IMoInflAffixSlot, SIL.LCModel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=null]]`

## Pre-state (ancestor / descendant test)

Read from the sandbox before the writes that the assertions cover. Source: `specs/255-affix-slot/evidence/_cycle3_measurements.json`, written by `test_ancestor_slot_accepted_descendant_slot_rejected` in its `finally` block.

- Parent POS `TEST_Cycle3Parent` HVO 10442
- Subcategory `TEST_Cycle3Child` HVO 10443, created with `POSOperations.AddSubcategory`
- Parent `GetAffixSlots` HVOs before `CreateAffixSlot`: empty (`pre_parent_slot_hvos`)
- Child template `PrefixSlotsRS` HVOs before `AddSlotToTemplate`: empty (`pre_child_prefix_hvos`)
- Parent template `PrefixSlotsRS` HVOs before the descendant `AddSlotToTemplate`: empty (`pre_parent_prefix_hvos`)

## Post-state (read back from the LCM)

`CreateAffixSlot(parent, "TEST_Cycle3Obligatory")` with `optional` omitted. The test re-fetched that slot through `GetAffixSlots` on `IPartOfSpeech(project.Object(parent_hvo))` and asserted the analysis name equals `TEST_Cycle3Obligatory`. Recorded read-back for HVO 10444:

- `optional_read_back`: false

Child `AllAffixSlots` after that create, re-fetched via `IPartOfSpeech(project.Object(child_hvo))`: HVO 10444 (the parent slot). `child_all_affix_slots_before`: [10444].

After `CreateAffixTemplate` on the subcategory and `AddSlotToTemplate(..., "prefix")`, the child template re-fetched from `AffixTemplatesOS` (`_template_on`) had `PrefixSlotsRS` HVOs: [10444]. `post_child_prefix_hvos`: [10444].

Child slot `TEST_Cycle3ChildSlot` HVO 10446. Parent `AllAffixSlots` on a fresh `IPartOfSpeech` fetch: [10444] only (10446 absent). `parent_all_affix_slots`: [10444].

`AddSlotToTemplate` of that child slot onto the parent template was asserted with `pytest.raises(FP_ParameterError)`. The test passed, so the exception was raised. Parent template `PrefixSlotsRS` HVOs on a fresh `_template_on` read after the rejection: empty. `post_parent_prefix_hvos`: [].

Measurement file `status`: pass.

Result line: PASS
