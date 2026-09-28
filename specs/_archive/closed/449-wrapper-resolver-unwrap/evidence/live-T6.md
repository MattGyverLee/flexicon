# Live verification -- issue #449, T6

## Commands run (from the worktree root, C:/Github/flexicon-449)

Offline gate:

```
python -m pytest -m "not requires_live_project" -q
```

Result: 148 failed, 2109 passed, 39 skipped, 958 deselected, 48 errors.
All 148 failures / 48 errors are pre-existing on unmodified origin/main
(confirmed by stashing this fix's production-code changes and re-running
the identical command: 168 failed, 2089 passed, same 48 errors -- the
21-test delta is exactly the new offline regression file,
`tests/operations/test_449_wrapper_resolver_unwrap.py`, which fails 21/23
against unmodified code and passes 23/23 against the fix). No new offline
failure was introduced by this change.

Live gate:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_449_getall_roundtrip_live.py -m requires_live_project -q
```

Result: **6 passed** in 12.06s.

Note: this worktree's `tests/fixtures/` did not contain the Sena 3
`.fwbackup` (the directory did not exist here at all). The fixture is
read-only test data, not code; it was copied in from the sibling
`C:/Github/flexicon` checkout (`tests/fixtures/Sena 3 2026-06-09
1645.fwbackup`) without modifying anything in that other worktree.

## run_mode

`tests/live_status.json` (written by this run):

```
"run_mode": "live",
"run_timestamp": "2026-09-24T19:29:00Z"
```

Per-class/phase entries recorded as `"status": "pass"`, `"last_verified":
"2026-09-24"`, for `AllomorphOperations` (read, reorder),
`MSAOperations` (read), `MorphRuleOperations` (read),
`PhonologicalRuleOperations` (read).

## Pre-state / post-state read back from the LCM

Sena 3 sandbox (fresh tempdir copy of the `.fwbackup`; read-only test,
no mutation of substance -- see "reorder" note below).

**Allomorph GetAll() class counts** (every item resolved via
`Allomorphs.GetForm(item)` and `Allomorphs.GetMorphType(item)`, both
routed through the newly-fixed `__GetAllomorphObject`):

```
{'MoStemAllomorph': 1485, 'MoAffixAllomorph': 145}
```

Both stem and affix allomorphs were hit (test asserts both counts > 0).
Sample value read back: `Allomorphs.GetForm(allomorphs[0])` ->
`"bubu bubu"`, `class_type` = `MoStemAllomorph`.

**MSA GetAll() class counts** (every item resolved via
`MSA.GetSyncableProperties(item)`, routed through the fixed
`__GetMsaObject`):

```
{'MoStemMsa': 1405, 'MoInflAffMsa': 115, 'MoDerivAffMsa': 11, 'MoUnclassifiedAffixMsa': 4}
```

All four MSA subtypes present in this dataset and all four counts are
non-zero; the live test (`test_every_msa_wrapper_resolves`) asserts this
and would fail loudly if any present subtype's count were 0.

**MorphRule GetAll() class counts** (every item resolved via
`MorphRules.GetName(item)` / `MorphRules.GetStratum(item)`, routed
through the fixed `__ResolveObject`):

```
{'MoExoCompound': 4, 'MoInflAffixTemplate': 25}
```

**PhonologicalRule GetAll() class counts**: `{}` -- Sena 3 defines no
phonological rules. The test does not hard-fail on this (dataset-
dependent), but the resolver path (`GetName`/`GetSyncableProperties`
via the fixed `__ResolveObject`) is exercised by the offline unit test
(`test_449_wrapper_resolver_unwrap.py`) using fake LCM objects instead.

**Caller-side cast check** (all four Ops classes): for every item,
`ICmObject(item.lcm_object).ClassName == item.class_type` held, proving
`.lcm_object` is the correct public unwrap path for a caller's own
pythonnet cast.

**`LexiconGetAllomorphForms`**: exercised against 25 real entries;
returns a `list[str]` for each, with no exception (this call previously
failed with no user input at all, per the sweep report's Table 1 row for
`FLExProject.py:5558-5559`).

**Reorder**: `Allomorphs.MoveToIndex(entry, wrapped_allomorph, 0)` called
on a wrapper built the same way `GetAll()` builds one, targeting the
allomorph's own current index (0). Returned `True`; post-state read back
via `list(entry.AlternateFormsOS)[0]` is unchanged (still the same raw
LCM object) -- the wrapper was correctly resolved to its raw counterpart
inside `MoveToIndex`'s equality search (previously: `ValueError: Item not
found in sequence`, since a wrapper never compares equal to a raw
sequence element).

## Pass/fail

**PASS.** Both required invocations were run from the worktree root; the
live run shows `run_mode: "live"` in `tests/live_status.json`, not
`"mock"`; per-ClassName counts and sample values above were read back
from the LCM after the calls, not merely asserted from the input.
