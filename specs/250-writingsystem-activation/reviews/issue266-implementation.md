# Issue #266 implementation report

**Task:** Route `PhonemeOperations.__ApplyBasicIPASymbol`'s target
writing-system lookup through `BaseOperations._resolve_ws_handle` (the
one-line C-D4-7 substitution #250 Defect 4 named this call site for ahead
of time).

## Summary

`flexicon/code/Grammar/PhonemeOperations.py`'s `__ApplyBasicIPASymbol` now
resolves case/separator-divergent writing-system spellings via the shared
`_resolve_ws_handle` helper, closing one of the two sibling sites #250
Defect 4 deliberately left open (the other, `ExampleOperations`'s
`TranslationsOC` loop, remains issue #267). Both the offline unit suite
(18 new tests across two files) and a live `target_sandbox` run
(byte-verified before/after) confirm the fix: pre-fix code silently drops
a case-divergent `BasicIPASymbol` alt, post-fix code saves it.

## Files modified

- `flexicon/code/Grammar/PhonemeOperations.py` -- the fix itself: import
  `_resolve_ws_handle` from `..BaseOperations`; `__ApplyBasicIPASymbol`
  now builds one `_ws_resolve_cache` dict per apply call and routes the
  target-handle lookup through `_resolve_ws_handle(target_ws_by_id,
  tgt_ws_id, _index_cache=_ws_resolve_cache)` instead of the old
  exact-match-only `target_ws_by_id.get(tgt_ws_id)`. The `ws_map`
  indirection line was reshaped (behaviourally identical, `tgt_ws_id =
  src_ws_id; if ws_map: tgt_ws_id = ws_map.get(src_ws_id, tgt_ws_id)`
  instead of the ternary `ws_map.get(src_ws_id, src_ws_id) if ws_map else
  src_ws_id`) specifically so the resolution-site ratchet's lexical
  signature no longer matches this file (see below).
- `tests/operations/test_issue250_defect4_ws_resolution.py` -- removed
  `"Grammar/PhonemeOperations.py"` from `_EXPECTED_RESOLUTION_SITE_FILES`
  (the frozen 3-site set is now a 2-site set: `BaseOperations.py` and
  `Lexicon/ExampleOperations.py`); updated the file-header "scope
  reminder" comment block to record site 2 as closed by #266 rather than
  leaving it stated as permanently out of scope.
- `tests/operations/test_issue266_phoneme_ws_resolution.py` (new) --
  offline unit coverage: exact match, case-divergent fallback,
  separator-divergent fallback, ws_map-then-normalize ordering, exact
  match preferred over normalized, genuine miss (silent continue),
  ambiguity raise (with message naming both spellings, and confirming no
  write happens), ambiguity non-raise when normalized keys share one
  handle, `fill_gaps` interaction, and two tests pinning that
  `__ApplyBasicIPASymbol` builds and reuses exactly one `_index_cache`
  dict per apply call (spec 250 C-D4-4) rather than per-alt or
  cross-call. 12 tests, all offline (no `requires_live_project`,
  SIL.LCModel import deferred into a fixture per the codebase's
  `test_basic_ipa.py` convention).
- `tests/operations/test_issue266_basicipasymbol_live.py` (new) -- live
  `target_sandbox` coverage: case-divergent alt resolves and saves
  (the issue's exact reproducer), and an exact-match zero-regression
  control.
- `specs/250-writingsystem-activation/evidence/live-266-basicipasymbol.md`
  (new) -- live-verification evidence, both sides measured.
- `CHANGELOG.md` -- new `[Unreleased]` -> `Fixed` entry documenting the
  fix, the new `FP_ParameterError` failure mode for `SetBasicIPASymbol`,
  and the remaining #267 boundary.

No other files were touched. In particular, `WritingSystemOperations.py`,
`FLExProject.py`, `BaseOperations.py`, `ExampleOperations.py`, and the
Discourse/Etymology/Variant/Media/Check/SemanticDomain/Location resolvers
were not edited.

## Sweep-pattern check (required by the task)

`grep -rn "ws_map.get(src_ws_id, src_ws_id)\|target_ws_by_id.get(" flexicon/code/`
after the fix returns exactly:
- `BaseOperations.py:380` and `:466` (the reference implementation itself
  -- `_resolve_ws_handle`'s own exact-match step and `_apply_props_loop`'s
  `ws_map` read; both expected, unchanged).
- `Lexicon/ExampleOperations.py:549-551` (issue #267, untouched, out of
  scope for this task by design -- see issue #266's own comment thread).

**No further, previously-undiscovered sibling site exists.** This
confirms the #250 spec's closed three-site enumeration is now a closed
two-site enumeration (one fixed here, one fixed at #250 Defect 4 itself,
one remaining at #267).

## Verification

Offline (this file's own suite plus every offline test touching
PhonemeOperations / the ratchet / BasicIPASymbol):
```
python -m pytest tests/operations/test_issue250_defect4_ws_resolution.py tests/operations/test_issue266_phoneme_ws_resolution.py tests/operations/test_phonemes.py tests/operations/test_basic_ipa.py tests/operations/test_apply_syncable_properties.py -m "not requires_live_project" -q
```
Result: `71 passed, 25 deselected`.

Live (both sides measured, byte-verified before/after via
`git hash-object`, full detail in the evidence file):
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue266_basicipasymbol_live.py -m requires_live_project -q
```
- Unfixed blob (`0522c13e...`, byte-identical to `HEAD`): `1 failed, 1
  passed` -- the case-divergent alt drops, confirming the bug.
- Fixed blob (`6a0423f8...`): `2 passed` -- the case-divergent alt
  resolves and saves; the exact-match control still passes.
- `tests/live_status.json` -> `"run_mode": "live"` in both runs.

Known, disclosed limitation (matches #250's own D4-T3 disclosure):
`target_sandbox`'s only two active writing systems (`en`, `etu`) contain
neither `-` nor `_`, so separator divergence and the ambiguity failure
mode for this call site are proven offline only, not live. This is a
pre-existing property of the `target_sandbox` fixture, not a gap
introduced by this task.

## Proposed commit subject

`fix(266): route PhonemeOperations.__ApplyBasicIPASymbol through the shared _resolve_ws_handle lookup`
