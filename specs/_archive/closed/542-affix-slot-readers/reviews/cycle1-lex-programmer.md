# Issue #542: affix slot readers -- cycle 1 (lex-programmer)

Worktree: `C:\Github\flexicon-542` (branch `fix/542-affix-slot-readers`,
based on `origin/main` 5b2631a).

## Summary

Implemented five new `POSOperations` methods (`GetSlotName`, `SetSlotName`,
`IsSlotOptional`, `SetSlotOptional`, `GetAffixesInSlot`), a new `AffixSlot`
wrapper class, updated `GetAffixSlots` and the four
`AffixTemplate.*_slots` properties to return `AffixSlot` instances, and
fixed the broken docstring examples. Both offline and **real** live
verification passed (`run_mode: "live"` -- see evidence below).

## Files changed

- `flexicon/code/Grammar/POSOperations.py` -- imports `IMoInflAffixSlot`,
  `normalize_text`, `AffixSlot`; adds `GetSlotName`/`SetSlotName`/
  `IsSlotOptional`/`SetSlotOptional`/`GetAffixesInSlot`; adds private
  `__ResolveSlot` helper; `GetAffixSlots` now returns
  `[AffixSlot(slot) for slot in pos.AffixSlotsOC]` and its docstring
  example uses `.name`.
- `flexicon/code/Grammar/affix_slot.py` (new) -- `AffixSlot(LCMObjectWrapper)`
  with `.name`, `.optional`, `.affixes`, `.owner_pos`, `__repr__`/`__str__`.
- `flexicon/code/Grammar/affix_template.py` -- `prefix_slots`/
  `suffix_slots`/`proclitic_slots`/`enclitic_slots` now wrap each raw slot
  in `AffixSlot`; module docstring and all four property docstrings fixed
  from `slot.Name` to `slot.name`.
- `docs/API_ISSUES_CATEGORIZED.md` -- new "Category 14" recording the
  live-reflection-confirmed field shapes and the `__ResolveSlot` pattern.
- `CHANGELOG.md` -- `[Unreleased]` entry.
- `tests/operations/test_issue542_affix_slot_readers_offline.py` (new,
  14 tests, all pass).
- `tests/operations/test_issue542_affix_slot_readers_live.py` (new,
  4 tests, all pass, `requires_live_project`).
- `specs/_archive/closed/542-affix-slot-readers/evidence/live-542.md` (new).

## LCM path chosen for `GetAffixesInSlot`

Live reflection against the installed FieldWorks 9 (`clr.GetClrType(IMoInflAffixSlot)`,
2026-09-26) found a direct back-reference property:

```
Slot prop: Affixes  IEnumerable<IMoInflAffMsa>
Slot prop: Name      IMultiUnicode
Slot prop: Optional  System.Boolean
```

`IMoInflAffixSlot.Affixes` is already the inverse of
`IMoInflAffMsa.SlotsRC` (the field `MSAOperations.GetInflAffMsaSlots`,
#543, reads from the MSA side). `GetAffixesInSlot` therefore just returns
`list(slot.Affixes)` -- no `IMoInflAffMsaRepository` scan and no
entry-by-entry `MorphoSyntaxAnalysesOC` walk needed. Cross-checked live
against `GetInflAffMsaSlots`: both sides agree on the same HVO set in the
live test.

## Field types confirmed by live reflection (not copied from another class)

| Field | Type |
|---|---|
| `IMoInflAffixSlot.Name` | `IMultiUnicode` |
| `IMoInflAffixSlot.Optional` | `System.Boolean` |
| `IMoInflAffixSlot.Affixes` | `IEnumerable<IMoInflAffMsa>` |

## Resolver shape

`__ResolveSlot` performs a real `IMoInflAffixSlot(obj)` pythonnet cast
(after unwrapping HVO / `AffixSlot` wrapper via `_UnwrapLcmObject`) and
raises `FP_ParameterError` on failure -- deliberately not the
never-raising `hasattr`/`ClassName`-string-compare shape `__ResolveObject`
uses (that shape is where the 4.10.0 live gate found "resolvers that
never cast", commit 9218b3c). Verified live: passing a `IPartOfSpeech`
into `GetSlotName` raises `FP_ParameterError`.

## Backward compatibility

`AffixSlot` is an `LCMObjectWrapper` subclass, so unknown attribute
access (`.Name`, `.Optional`, `.Hvo`) proxies through to the raw LCM
object via `__getattr__` -- verified live in
`test_get_affix_slots_returns_affixslot_wrapper`.

Grepped every caller of `GetAffixSlots`/`prefix_slots`/`suffix_slots`/
`proclitic_slots`/`enclitic_slots`/`AddSlotToTemplate`/`CreateAffixSlot`
across `flexicon/` and `tests/`:

- `MSAOperations.SetInflAffMsaSlots` resolves slots via `__Resolve`, which
  checks `hasattr(obj_or_hvo, "_obj")` -- true for `AffixSlot`. Passing a
  wrapper in works unchanged.
- `MorphRuleOperations.AddSlotToTemplate` resolves `slot` via
  `BaseOperations._UnwrapLcm`, which does `isinstance(obj, LCMObjectWrapper)`
  -- true for `AffixSlot`. Verified live: created a wrapper via
  `GetAffixSlots`, passed it straight into `AddSlotToTemplate`, and read
  it back through `AffixTemplate(template).prefix_slots`.
- `POSOperations.CreateAffixSlot` is unchanged -- it still returns the raw
  `IMoInflAffixSlot`, not a wrapper, matching the issue's explicit scope
  (only `GetAffixSlots` and the four `AffixTemplate.*_slots` properties
  are asked to return `AffixSlot`). Existing offline tests in
  `tests/operations/test_issue255_affix_slot.py` (which set `slot.Hvo = 50`
  directly on a raw Mock) are unaffected.
- `tests/test_affix_template_wrappers.py`'s mock-based tests
  (`len(wrapped.prefix_slots) == 2`, etc.) still pass: wrapping each Mock
  slot in `AffixSlot` doesn't change `len()`/list semantics, and
  `cast_to_concrete` is total (never raises) even on non-LCM Mocks, so
  wrapper construction never fails offline.

**Behaviour change for callers relying on the *type* of `GetAffixSlots`'s
return items** (rather than duck-typed `.Name`/`.Optional`/`.Hvo`
access): items are now `AffixSlot` instances, not raw `IMoInflAffixSlot`.
Any code doing `isinstance(slot, IMoInflAffixSlot)` or a raw pythonnet
cast like `IMoInflAffixSlot(slot)` directly on a `GetAffixSlots()` item
would need `IMoInflAffixSlot(slot.lcm_object)` instead (documented pattern,
Category 13). No such caller was found in this repository.

## Test counts

- Offline (`python -m pytest -m "not requires_live_project" -q`):
  **2506 passed, 5 failed, 1040 deselected**. The 5 failures
  (`test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies`
  and 4 in `test_morphrule_duplicate_deep.py`) are pre-existing on
  `origin/main` before this branch -- confirmed via `git stash` +
  re-run, unrelated `AffixTemplatesOS` Mock-iteration issue. All 14 new
  tests in `test_issue542_affix_slot_readers_offline.py` pass; no
  previously-passing test regressed.
- Live (`FLEXLIBS_REQUIRE_LIVE=1 python -m pytest
  tests/operations/test_issue542_affix_slot_readers_live.py -m
  requires_live_project -q`): **4 passed**.

## run_mode

`tests/live_status.json` after the live run: `"run_mode": "live"`,
`"run_timestamp": "2026-09-26T22:31:06Z"`,
`by_class.POSOperations.read.status: "pass"`.

## Environment note (relevant to the offline test design)

FieldWorks 9 is installed on this runner, so the pytest session-scoped
fixture in `tests/flex_plugin.py` loads the **real** `SIL.LCModel`
assemblies even for the "offline" (`not requires_live_project`) run --
confirmed directly (`IPartOfSpeech(Fake())` raises `TypeError: object
does not implement IPartOfSpeech` even in the offline run). A plain
Python `Mock` therefore cannot exercise `__ResolveSlot`'s
`IMoInflAffixSlot(obj)` cast offline; the offline suite is written as
source-ratchet tests (checking method existence, write-guard placement,
the real-cast/raise pattern, and the fixed docstrings) rather than
mock-executed runtime tests, mirroring the approach already used in
`tests/operations/test_issue543_get_infl_aff_msa_slots_offline.py` for the
same constraint. Because FieldWorks was actually available, the live
suite in this cycle is a **real** live run against the real in-place
`Target` project (via the `target_project` fixture; no
`tests/fixtures/*.fwbackup` exists on this runner, so
`target_sandbox`/`sena3_sandbox` were unavailable) plus a direct
read-only open of `Sena 3` -- not a "FAIL: unverified" report.

## Commits on `fix/542-affix-slot-readers`

- `0411d51` -- feat(grammar): add affix slot readers and AffixSlot wrapper (#542)
- `ac736e0` -- test: cover affix slot readers offline and live (#542)
- `8fa3476` -- docs: record affix slot reader additions and field types (#542)

Not pushed; no PR opened, per instructions.

## Worktree

`C:\Github\flexicon-542`
