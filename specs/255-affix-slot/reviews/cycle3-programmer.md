# Cycle 3 programmer report: for #255

Issue #258 was not implemented. Side names and index behavior were not changed. `0672b0b` was not amended. This commit was not pushed.

## Files changed

Committed in `6abff1cdefd832e4913d8bcf258fb3696c48cf99`:

- `flexicon/code/Grammar/POSOperations.py` — `CreateAffixSlot` default `optional=False`. Attach-then-populate is unchanged: `factory.Create()`, `AffixSlotsOC.Add`, then Name and Optional, inside one `_TransactionCM`.
- `flexicon/code/Grammar/MorphRuleOperations.py` — `AddSlotToTemplate` accepts a slot whose HVO is in the template owner's `AllAffixSlots`. The same-owner HVO test is gone. `__ResolveObject` casts `ClassName == "PartOfSpeech"` to `IPartOfSpeech` so a bare `Owner` exposes that property.
- `tests/operations/test_issue255_affix_slot.py` — omitted `optional` writes `Optional` false only after `Add`. Owner cases follow `AllAffixSlots` membership, including an ancestor success and a descendant rejection.
- `tests/operations/test_issue255_affix_slot_live.py` — `target_sandbox` parent POS, subcategory, omitted-optional read-back, ancestor insert, descendant `FP_ParameterError` with the parent side unchanged.
- `docs/FUNCTION_REFERENCE.md` — `optional=False`, and the slot must be in the template category's `AllAffixSlots` (itself or an ancestor).
- `docs/USAGE_AFFIX_TEMPLATES.md` — omitting `optional` creates an obligatory slot; a subcategory template may take an ancestor-owned slot.
- `specs/255-affix-slot/evidence/live-cycle3.md`

This report was written after that commit and was not staged. `specs/255-affix-slot/evidence/_live_measurements.json` and `_cycle3_measurements.json` were not staged.

## Behavior

`CreateAffixSlot(pos, name)` stores `Optional` false. Callers can still pass `optional=True`. `CreateAffixSlot` still creates on the POS it is given. `GetHvoOfHighestPOS` is not a create target.

`AddSlotToTemplate` resolves `template.Owner` through `__ResolveObject`. A missing owner, a non-POS owner, a reflected `AllAffixSlots` that is absent, or a slot HVO outside that set raises `FP_ParameterError`: "Affix slot must be in the template category's AllAffixSlots (the category itself or an ancestor)". There is no HVO-equality fallback.

`clr.GetClrType(IPartOfSpeech)` on the installed SIL.LCModel shows `AllAffixSlots` (`IEnumerable` of `IMoInflAffixSlot`). The check uses that property.

## Tests

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

live (`tests/live_status.json`, `run_timestamp` 2026-09-23T06:28:36Z)

## Evidence

`specs/255-affix-slot/evidence/live-cycle3.md`

Reflected property: `AllAffixSlots`. Pre-state: parent HVO 10442, child HVO 10443, parent slot list empty, both template prefix sequences empty. Post-state read back from the LCM: omitted `optional` on HVO 10444 is false; child `AllAffixSlots` and the child template prefix sequence contain 10444; child slot 10446 is absent from parent `AllAffixSlots`; the parent prefix sequence stayed empty after `FP_ParameterError`. Result line: PASS.

## Commit

`6abff1cdefd832e4913d8bcf258fb3696c48cf99` on `main`. Not pushed. `0672b0b` was left as-is.

## Pattern audit

Sweep skipped, this corrects a new wrapper's default and owner rule, not a shaped bug. The PartOfSpeech cast added to `MorphRuleOperations.__ResolveObject` follows `POSOperations.__ResolveObject`.
