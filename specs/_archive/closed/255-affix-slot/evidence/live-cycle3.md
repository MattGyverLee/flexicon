# Live evidence: cycle 3 domain corrections for #255

Target sandbox (`target_sandbox`), objects prefixed `TEST_`. Issue #258 was not implemented. Side names and index behavior were not changed.

Each pytest invocation opens a fresh tempdir copy of the Target backup per test, so the same HVO number in the two live tests is not the same object.

## Commands

```
python -m pytest tests/operations/test_issue255_affix_slot.py -m "not requires_live_project" -q
```

13 passed in 0.64s

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue255_affix_slot_live.py -m requires_live_project -q
```

2 passed in 2.35s

```
python -c "import json; print(json.load(open('tests/live_status.json', encoding='utf-8'))['run_mode'])"
```

live

## run_mode

live

`tests/live_status.json` `run_timestamp` 2026-09-23T06:28:36Z. Both recorded tests passed: `test_create_slot_and_add_to_prefix_side` (0.062s) and `test_ancestor_slot_accepted_descendant_slot_rejected` (0.025s).

## Reflected property

`clr.GetClrType(IPartOfSpeech).GetProperty("AllAffixSlots")` during the live test:

- Name: `AllAffixSlots`
- Type: IEnumerable of IMoInflAffixSlot (SIL.LCModel 11.0.0.0)

The owner check uses that property. It does not compare owner HVOs.

## Pre-state (ancestor / descendant test)

Read from the sandbox before the writes that the assertions cover:

- Parent POS `TEST_Cycle3Parent` HVO 10442
- Subcategory `TEST_Cycle3Child` HVO 10443, created with `POSOperations.AddSubcategory`
- Parent `GetAffixSlots` HVOs before `CreateAffixSlot`: empty
- Child template `PrefixSlotsRS` HVOs before `AddSlotToTemplate`: empty
- Parent template `PrefixSlotsRS` HVOs before the descendant `AddSlotToTemplate`: empty

## Post-state (read back from the LCM)

`CreateAffixSlot(parent, "TEST_Cycle3Obligatory")` with `optional` omitted. Fresh `GetAffixSlots` hit for HVO 10444:

- Name: `TEST_Cycle3Obligatory`
- `Optional`: false

Child `AllAffixSlots` after that create, re-fetched via `IPartOfSpeech(project.Object(child_hvo))`: HVO 10444 (the parent slot).

After `CreateAffixTemplate` on the subcategory and `AddSlotToTemplate(..., "prefix")`, the child template re-fetched from `AffixTemplatesOS` had `PrefixSlotsRS` HVOs: 10444.

Child slot `TEST_Cycle3ChildSlot` HVO 10446. Parent `AllAffixSlots` on a fresh `IPartOfSpeech` fetch: HVO 10444 only (10446 absent). `AddSlotToTemplate` of that child slot onto the parent template raised `FP_ParameterError`. Parent template `PrefixSlotsRS` HVOs on a fresh read after the rejection: empty (unchanged from the pre-state empty sequence).

Result line: PASS
