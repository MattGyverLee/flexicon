# Cycle 1 programmer report: issue #255

Issue #258 was not implemented. `SetInflAffMsaSlots` is still absent. #258 stays open.

## Files changed

Committed in `0672b0b497b330b59274fc2ef2fb47e6ad825679`:

- `flexicon/code/Grammar/POSOperations.py` — `CreateAffixSlot(pos, name, optional=True)` next to `GetAffixSlots`. `GetAffixSlots` See Also now includes `CreateAffixSlot`.
- `flexicon/code/Grammar/MorphRuleOperations.py` — `AddSlotToTemplate(template, slot, side, index=None)` next to `CreateAffixTemplate`. The CreateAffixTemplate note now points slot assignment at `AddSlotToTemplate`.
- `tests/operations/test_issue255_affix_slot.py` — offline mocks.
- `tests/operations/test_issue255_affix_slot_live.py` — `target_sandbox`, `requires_live_project`.
- `specs/255-affix-slot/evidence/live-create-and-add.md`
- `docs/USAGE_AFFIX_TEMPLATES.md` — subsection under "Create a Template".
- `docs/FUNCTION_REFERENCE.md` — rows beside `project.POS.GetAffixSlots`.

This report was written after that commit and was not staged.

## Reflected LCM names

- Factory: `IMoInflAffixSlotFactory` from `SIL.LCModel`. The import succeeded. No substitute name was invented.
- Boolean property: `Optional`. `clr.GetClrType(IMoInflAffixSlot)` lists one boolean property, `Optional`. The created slot's concrete type lists `CanDelete`, `IsValidObject`, and `Optional`. The Python parameter stays `optional` and defaults to `True`.
- Template sides are reference sequences: `PrefixSlotsRS`, `SuffixSlotsRS`, `ProcliticSlotsRS`, `EncliticSlotsRS`.
- Insert method: `IList<T>.Insert(Int32, T)`. There is no `InsertAt`. The live `PrefixSlotsRS` concrete type exposes `Add` and `Insert`.

## Behavior

`CreateAffixSlot` resolves `pos` through `__ResolveObject`, then inside one `_TransactionCM` does `factory.Create()`, `AffixSlotsOC.Add`, analysis-WS `Name.set_String` via `TsStringUtils.MakeString` and `DefaultAnalWs`, then `Optional`. Null `pos` or `name` is `FP_NullParameterError` via `_ValidateParam`. A blank name is `FP_ParameterError`. A read-only project is `FP_ReadOnlyError` via `_EnsureWriteEnabled`.

`AddSlotToTemplate` maps `side` case-insensitively onto the four sequences. Any other side is `FP_ParameterError`. Slot and template owners are compared by HVO. `index is None` calls `Add`. An int index calls `Insert` after a range check (`0..Count` inclusive of `Count`); out of range is `FP_ParameterError`. No factory create.

## Tests

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

live (`tests/live_status.json`, `run_timestamp` 2026-09-23T06:10:54Z)

## Evidence

`specs/255-affix-slot/evidence/live-create-and-add.md`

Pre-state: slot count 0 on POS HVO 2706; prefix count 0. Post-state read back from the LCM: name `TEST_PossConcord`, Optional false, slot HVO 10442, prefix HVOs after insert-at-0 `10444, 10442`. Result line: PASS.

## Commit

`0672b0b497b330b59274fc2ef2fb47e6ad825679` on `main`. Not pushed.

## Pattern audit

Sweep skipped because there is no defective site. This is a new wrapper. Mirrored methods: `POSOperations.Create`, `MorphRuleOperations.CreateAffixTemplate`, `InflectionFeatureOperations.TypeCreate`.
