# Live evidence: cycle 2 verification of issue #255

Commit `0672b0b497b330b59274fc2ef2fb47e6ad825679`. Target sandbox (`target_sandbox`), objects prefixed `TEST_`. Production code was not edited. Issue #258 was not implemented (`SetInflAffMsaSlots` is absent).

Each pytest invocation opens a fresh tempdir copy of the Target backup, so HVO numbers can repeat across runs. They are not the same objects.

## Commands

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

live

## run_mode

live

`tests/live_status.json` `run_timestamp` 2026-09-23T06:18:01Z. The recorded test is `test_create_slot_and_add_to_prefix_side`, phase `add`, status `pass`, duration 0.069s. An earlier invocation of the same command in this session (2026-09-23T06:16:06Z, 1 passed in 2.18s) also reported `run_mode` live before a gap probe overwrote the file. The timestamp above is the re-run after that probe file was deleted.

## Pre-state (official live test)

Read before the writes, from the sandbox copy of Target:

- POS HVO 2706 (existing category; `created_pos` false)
- Affix slot count via `GetAffixSlots`: 0
- Chosen side: prefix (`PrefixSlotsRS`)
- `PrefixSlotsRS.Count` on the new template, before `AddSlotToTemplate`: 0

## Post-state (official live test)

Values read back from the LCM after the writes:

- Slot name via a fresh `GetAffixSlots` hit, then `ITsString(Name.get_String(DefaultAnalWs)).Text`: `TEST_PossConcord`
- `Optional` on that same re-fetched slot: false (argument was `optional=False`)
- Slot HVO: 10442
- After `AddSlotToTemplate(..., "Prefix")`, `PrefixSlotsRS` contained HVO 10442
- Second slot `TEST_NounClass` (HVO 10444, created with `optional=True`) inserted at index 0. Re-read `PrefixSlotsRS` HVOs: 10444, 10442
- Post slot count via `GetAffixSlots`: 2
- Post `PrefixSlotsRS.Count`: 2
- Index 99 raised `FP_ParameterError` and the HVO order stayed 10444, 10442
- Concrete `PrefixSlotsRS` methods present: Add, Insert

The official test's `second_optional_read_back: true` is `IMoInflAffixSlot(second).Optional` on the object `CreateAffixSlot` just returned, with `optional=True` passed explicitly. It is not a fresh `GetAffixSlots` read of the default.

## Gap probe (same sandbox fixture, probe file deleted after the run)

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/_tmp_cycle2_255_probe.py -m requires_live_project -q
```

1 passed in 2.09s. The probe called the shipped `CreateAffixSlot` and `AddSlotToTemplate`. It did not edit `POSOperations.py` or `MorphRuleOperations.py`.

### Pre-state

- POS HVO 2706
- `GetAffixSlots` count: 0 (HVO list empty)
- New template side counts before any insert: `SuffixSlotsRS` 0, `ProcliticSlotsRS` 0, `EncliticSlotsRS` 0, `PrefixSlotsRS` 0

### Post-state

`CreateAffixSlot(pos, "TEST_C2_DefaultOptional")` with `optional` omitted. Fresh `GetAffixSlots` hit for HVO 10442:

- Name: `TEST_C2_DefaultOptional`
- `Optional`: true

Three further slots, each appended (`index` omitted) and re-read from the template fetched again off `IPartOfSpeech.AffixTemplatesOS`:

| Side | Property | Count | HVOs |
|------|----------|-------|------|
| suffix | `SuffixSlotsRS` | 1 | 10444 |
| proclitic | `ProcliticSlotsRS` | 1 | 10445 |
| enclitic | `EncliticSlotsRS` | 1 | 10446 |

`PrefixSlotsRS` HVOs after those adds: empty. Post `GetAffixSlots` count: 4.

`Insert` was not repeated on suffix, proclitic, or enclitic. The official test already showed `Insert(0)` on `PrefixSlotsRS`.

## Result

PASS
