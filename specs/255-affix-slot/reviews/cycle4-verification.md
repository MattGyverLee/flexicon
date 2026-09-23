# Cycle 4 verification: issue #255

**Overall verdict: PASS**

**Commit:** `6abff1cdefd832e4913d8bcf258fb3696c48cf99`
**Live run:** yes | **run_mode:** live
**Evidence:** `specs/255-affix-slot/evidence/live-cycle4.md`
**Project:** Target (`target_sandbox`, tempdir copy of the Target `.fwbackup`)
**Production code edited by this verification:** no
**Issue #258:** not implemented

`specs/255-affix-slot/evidence/live-cycle3.md` was not treated as proof. The commands below were run from the repo root in this session against commit `6abff1cdefd832e4913d8bcf258fb3696c48cf99` (HEAD). `git diff` for `flexicon/` and the two affix-slot test modules is empty.

## Commands and run_mode

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

`live`

`tests/live_status.json` `run_timestamp` 2026-09-23T06:31:32Z. `by_test` records both live tests as pass, phase `POSOperations` / `add`:

- `test_create_slot_and_add_to_prefix_side` (0.059s)
- `test_ancestor_slot_accepted_descendant_slot_rejected` (0.03s)

`run_mode` is not `mock`. FieldWorks and the Target backup were available.

## What the live test actually checks

The three claims sit in `test_ancestor_slot_accepted_descendant_slot_rejected` (`tests/operations/test_issue255_affix_slot_live.py`). The test writes `specs/255-affix-slot/evidence/_cycle3_measurements.json` from values read off re-fetched LCM objects. That file's `status` is `pass`.

`CreateAffixSlot(parent, slot_name)` is called with `optional` omitted (no third argument). The slot is then selected from a fresh `GetAffixSlots` on `IPartOfSpeech(project.Object(parent_hvo))`, and `Optional` is read from that hit.

The child POS is re-fetched with `project.Object(child_hvo)` before `AllAffixSlots` is read. The child template is re-fetched from `owner.AffixTemplatesOS` via `_template_on` both before and after `AddSlotToTemplate`.

The parent POS is re-fetched before `AllAffixSlots` is read. `AddSlotToTemplate` of the child-owned slot onto the parent template is wrapped in `pytest.raises(FP_ParameterError)`. The parent prefix sequence is read again through `_template_on` and compared to the pre-call sequence.

Each live test uses `target_sandbox`, so the two tests do not share objects. HVO 10442 in the first test is a slot; HVO 10442 in the ancestor test is the parent POS.

## Claim vs. observed

| Claim | Observed live | Status |
|---|---|---|
| `CreateAffixSlot(pos, name)` with `optional` omitted stores `Optional` false, read from a fresh `GetAffixSlots` hit | Parent POS HVO 10442. Pre `GetAffixSlots` HVOs empty. Created slot HVO 10444. Test asserted analysis name `TEST_Cycle3Obligatory` on the re-fetched slot. `optional_read_back` false. | PASS |
| A slot owned by a parent POS is in the subcategory's `AllAffixSlots`, and `AddSlotToTemplate` places that HVO on the child template's prefix sequence, read back from `AffixTemplatesOS` | Child POS HVO 10443. `child_all_affix_slots_before` [10444]. Pre child `PrefixSlotsRS` empty. Post child `PrefixSlotsRS` [10444]. | PASS |
| A slot owned by the subcategory is absent from the parent's `AllAffixSlots`. `AddSlotToTemplate` onto the parent template raises `FP_ParameterError` and the parent prefix sequence stays empty on a fresh read | Child slot HVO 10446. `parent_all_affix_slots` [10444] (10446 absent). Pre and post parent `PrefixSlotsRS` both empty. The `pytest.raises(FP_ParameterError)` assertion passed. | PASS |

## Blockers

None.

## Recommendation

APPROVE
