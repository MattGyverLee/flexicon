# Issue #267 implementation report

**Task:** Route `ExampleOperations.ApplySyncableProperties`'s
`TranslationsOC` loop target writing-system lookup through
`BaseOperations._resolve_ws_handle` (the last of the three sibling sites
#250 Defect 4 deliberately left open), **without** reintroducing an
orphaned zero-alt `ICmTranslation` when the resolver raises on an
ambiguous normalized spelling. Mid-task, the coordinator additionally
required an unconditional miss-case warning matching the one
`BaseOperations._apply_props_loop` just landed for #250 Defect 3.

## Summary

Unlike #266 (a genuine one-line substitution), this site's pre-fix loop
created and attached the `ICmTranslation` (`ICmTranslationFactory.Create`
+ `TranslationsOC.Add`) **before** resolving any of its alts' target
writing systems. A naive substitution of `_resolve_ws_handle` in place
would have left a zero-alt `ICmTranslation` orphaned on the example
whenever an ambiguous normalized spelling raised `FP_ParameterError`
mid-loop. The fix restructures the loop to resolve every alt's target
handle **before** `Create`/`Add` run, proven both by a dedicated offline
regression test and by red/green-testing the required test against a
deliberately-reproduced naive-substitution variant (which fails exactly
the two orphan tests and nothing else). A genuine miss (Defect 3) still
skips, but now logs an unconditional warning mirroring the sibling fix
already landed in `BaseOperations._apply_props_loop`.

## Why pre-resolve, not rollback

The issue's second candidate ("rely on the surrounding transaction to
roll back") was checked empirically, not assumed. `BaseOperations
._TransactionCM`'s own docstring (unmodified by this task, read as
found) states plainly that **neither of its two phases auto-rolls-back a
partial write in the current build**: Phase 1 (`Transaction`, selected
when `undoable=False` -- exactly the mode `target_sandbox` uses) "does
NOT roll back on exception in the current build. liblcm exposes no
reachable rollback-to-mark API in this mode (issue #236)." Phase 2
(`UndoableOperation`) is rollback-capable, but only for the block it
itself opens, and only when the whole call is the *outermost* nested
`_TransactionCM` -- not a property this loop's caller controls. Relying
on the transaction would therefore have been silently broken in the
common `undoable=False` case and unreliable in the other. Pre-resolving
before creation is the only shape that makes the operation total by
construction regardless of transaction phase, so that is what was
implemented.

## Files modified (within the declared ownership)

- `flexicon/code/Lexicon/ExampleOperations.py`:
  - Import `_resolve_ws_handle` from `..BaseOperations` alongside the
    existing `BaseOperations`/`OperationsMethod`/`wrap_enumerable`
    imports.
  - In the `TranslationsOC` branch of `ApplySyncableProperties`: build
    one `_ws_resolve_cache = {}` per apply call, alongside the existing
    once-per-call `target_ws_by_id` build (C-D4-4).
  - Per `trans_dict` in `translations_data`: resolve **every** alt's
    target writing-system handle into a `resolved_alts` list *before*
    calling `ICmTranslationFactory.Create` / `item.TranslationsOC.Add`.
    An ambiguous normalized spelling now raises `FP_ParameterError`
    before any `ICmTranslation` is created, so no orphan is possible. A
    genuine miss (absent under both exact and normalized matching) still
    `continue`s (Defect 3, unchanged, out of scope for this issue), but
    now logs an unconditional `logging.getLogger(__name__).warning(...)`
    naming the dropped writing system (source id, resolved target id)
    and the owning example's type/Hvo -- the `ICmTranslation` does not
    exist yet at the point the miss is detected, so the example (not the
    translation) is what gets named, mirroring `_apply_props_loop`'s
    shape as closely as the reordered control flow allows.
  - The `ws_map` indirection line was reshaped (behaviourally identical:
    `tgt_ws_id = src_ws_id; if ws_map: tgt_ws_id = ws_map.get(src_ws_id,
    tgt_ws_id)` instead of the ternary) specifically so the
    resolution-site ratchet's lexical signature no longer matches this
    file, exactly as #266 did for `PhonemeOperations.py`.
- `tests/operations/test_issue250_defect4_ws_resolution.py` -- removed
  `"Lexicon/ExampleOperations.py"` from `_EXPECTED_RESOLUTION_SITE_FILES`
  (now a single-entry frozen set, `{"BaseOperations.py"}` -- the
  resolver's own implementation file, which legitimately contains the
  lexical signatures forever); updated the file-header "scope reminder"
  comment block to record site 3 as closed by #267 and point at both new
  test files' coverage rather than stating it out of scope pending #267.
- `tests/operations/test_issue267_translations_ws_resolution.py` (new)
  -- offline unit coverage, 14 tests:
  - `TestTranslationsOCExactMatch` -- zero-regression basis.
  - `TestTranslationsOCNormalizedFallback` -- case-divergent hit,
    separator-divergent hit, `ws_map`-then-normalize ordering, exact
    match preferred over normalized.
  - `TestTranslationsOCGenuineMiss` -- silent-skip behaviour unchanged
    (translation still created with zero alts) plus (added for the
    coordinator's mid-task requirement) the miss-case warning fires with
    the expected content, and does NOT fire on either an exact or a
    normalized hit.
  - `TestTranslationsOCAmbiguity` -- ambiguous normalized match raises
    `FP_ParameterError` naming both spellings; keys that normalize
    together but share one handle do not raise.
  - `TestApplyTranslationsOCOrphanRegression` -- **the mandatory
    regression test.** Forces the ambiguity raise and asserts
    `ICmTranslationFactory.Create` was never called (zero entries in the
    fake factory's `create_calls`) -- proven to fail against a naive
    one-line substitution (see Verification below). A second test
    exercises the same assertion with two translation entries in one
    call (one resolves fine, the second raises), confirming the earlier,
    fully-resolved translation survives while the raising entry still
    creates zero `ICmTranslation` objects.
  - `TestTranslationsOCSharedIndexCache` -- pins that `_ws_resolve_cache`
    is the SAME dict object across every alt and every translation entry
    within one `ApplySyncableProperties` call, and a FRESH dict on the
    next call (C-D4-4).
  - All fakes are local Python stand-ins (`_FakeWs`, `_FakeProject`,
    `_FakeTranslationFactory`, `_FakeTranslationsOC`, etc.); the real
    `TsStringUtils.MakeString` from `SIL.LCModel.Core.Text` is used
    unmocked (confirmed to work standalone with an arbitrary int handle,
    no live project needed, once the `flexicon` package's own CLR
    bootstrap has run). `_TransactionCM` is replaced with
    `contextlib.nullcontext()` via instance-dict shadowing (it is a
    plain method, not a data descriptor). No `requires_live_project`
    marker; the `ExampleOperations` import is deferred into a fixture
    that skips if `SIL.LCModel` never loaded, matching
    `test_issue266_phoneme_ws_resolution.py`'s convention.
- `tests/operations/test_issue267_translations_live.py` (new) -- live
  `target_sandbox` coverage, 3 tests: the case-divergent reproducer
  (resolves and saves), an exact-match zero-regression control, and the
  miss-case warning (fires on a genuine miss, alt still absent).
- `specs/250-writingsystem-activation/evidence/live-267-translations.md`
  (new) -- live-verification evidence, both sides measured.
- `CHANGELOG.md` -- one new `[Unreleased]` -> `Fixed` bullet for #267,
  inserted immediately after #266's own bullet, additive only (#266's
  entry, #250's Defects 1-3 entries, and the #264 entry below are
  untouched). Documents the orphan-prevention restructure, cites the
  `_TransactionCM` docstring finding, and documents the new miss-case
  warning added for the coordinator's mid-task requirement.

No other files were touched. In particular `BaseOperations.py`,
`PhonemeOperations.py`, `WritingSystemOperations.py`, `FLExProject.py`,
and `lcm_casting.py` (all modified by other concurrent agents in this
working tree, confirmed via `git status`) were left exactly as found.

## Ratchet status

```
grep -n "ws_map.get(src_ws_id, src_ws_id)\|target_ws_by_id.get(" flexicon/code/Lexicon/ExampleOperations.py
```
returns nothing -- the file no longer contains either pre-fix signature.
`_EXPECTED_RESOLUTION_SITE_FILES` is now `frozenset({"BaseOperations.py"})`
(down from the two-entry set #266 left), and
`test_exactly_three_resolution_sites_exist` still passes, confirming the
ratchet is down to exactly one legitimate site (the resolver's own
implementation) and still enforcing: any future self-resolving
writing-system loop added anywhere under `flexicon/code/` would trip it.

## Verification

### Offline

```
python -m pytest tests/operations/test_issue267_translations_ws_resolution.py tests/operations/test_issue250_defect4_ws_resolution.py tests/operations/test_apply_syncable_properties.py tests/operations/test_examples_live.py tests/operations/test_issue266_phoneme_ws_resolution.py tests/operations/test_phonemes.py -m "not requires_live_project" -q
```
Result: `85 passed, 26 deselected`.

**Red-then-green, twice** (both against the offline suite and, again, the
live suite -- see the evidence file for the live half):

1. Fully unfixed baseline. `flexicon/code/Lexicon/ExampleOperations.py`
   was byte-verified identical to `HEAD` (`git hash-object` ==
   `git rev-parse HEAD:...`, both `c503aa3b...`) via a scratch
   backup/restore of just that one file (never `git checkout`/`stash` on
   the shared working tree, per the task's hard constraint). Running the
   new offline suite against it: **10 failed, 4 passed** -- including
   both orphan-regression tests and the new miss-case-warning test.
   Restored the fixed blob (`git hash-object` ==
   `17c82a2c7654aaf14efdf85326493c8c1a23271d`) and reran: **14 passed**.
2. **Naive one-line substitution**, constructed specifically to prove the
   mandatory regression test catches the exact shape the issue warns
   about (not just "any bug"): kept `ICmTranslationFactory.Create` /
   `TranslationsOC.Add` in their original pre-fix position (before
   resolution) and routed only the handle lookup itself through
   `_resolve_ws_handle`. Running the offline suite against this variant:
   **2 failed, 10 passed** -- and the two failures were *exactly*
   `TestApplyTranslationsOCOrphanRegression`'s two tests (asserting
   `create_calls == []`, which becomes `[one call]` under the naive
   shape); every other test, including the ambiguity-raises and
   normalized-fallback tests, still passed, confirming the orphan tests
   are the ones carrying the "structural reorder, not substitution"
   requirement. Restored the real fix afterward and reconfirmed
   `14 passed`.

### Live

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue267_translations_live.py -m requires_live_project -q
```
- Fixed blob: `3 passed` (run twice, before and after the red run, both
  green).
- Unfixed blob (byte-verified identical to `HEAD`): `2 failed, 1 passed`
  -- the case-divergent alt drops (reads back `None`) and the warning
  test finds no warning logged; the exact-match control still passes.
- `tests/live_status.json` -> `"run_mode": "live"` in both runs.
- Full detail, including the exact pre/post-state values re-read from a
  freshly re-fetched `ILexExampleSentence` and the C-D4-6
  writing-system-store-unchanged assertions, is in
  `specs/250-writingsystem-activation/evidence/live-267-translations.md`.

**Disclosed limitation (matches #266's own disclosure, extended):**
`target_sandbox`'s only two active writing systems (`en`, `etu`) contain
neither `-` nor `_`, so separator divergence is proven offline only. This
task additionally could not construct a live ambiguity raise (two
DISTINCT active writing systems normalizing to the same form) because
FieldWorks case-normalizes BCP-47 tags on creation, so there is no
supported way to stand up a second active WS differing from an existing
one only by case. The orphan-regression mechanism itself is therefore
**proven offline only**, via the fake-factory `create_calls` assertion
and the naive-substitution red/green proof above -- clearly stated in
both the evidence file and here rather than overclaimed as live-covered.

## Orphan-prevention shape chosen

**Pre-resolve before creation/attachment** (the issue's first candidate,
and the one it called "generally the cleaner fix"). Rejected the
rollback-reliance alternative on the empirical grounds described above
(`_TransactionCM`'s own docstring: neither phase auto-rolls-back a
partial write in the current build). This makes the operation total by
construction: an ambiguous spelling raises before
`ICmTranslationFactory.Create` is ever called, so there is no window in
which a zero-alt `ICmTranslation` could exist, regardless of whether the
surrounding project is opened `undoable=True` or `undoable=False`.

## Proposed commit subject

`fix(267): resolve ExampleOperations TranslationsOC writing-system lookup without orphaning ICmTranslation`
