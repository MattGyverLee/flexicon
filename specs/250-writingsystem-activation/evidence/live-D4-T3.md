# D4-T3 -- Live verification evidence: Defect 4 (writing-system case/separator divergence)

**Task:** specs/250-writingsystem-activation/spec.md, D4-T1/D4-T2/D4-T3/D4-T5
**Project:** `target_sandbox` ONLY (fresh tempdir copy of the Target `.fwbackup`).
Never the in-place Target, never Sena 3.
**Live test file:** `tests/operations/test_issue250_ws_case_divergence.py`
**Offline test file:** `tests/operations/test_issue250_defect4_ws_resolution.py`
**Fix location:** `flexicon/code/BaseOperations.py` -- `_apply_props_loop`'s
multistring writing-system resolution step, plus a new module-level helper
`_resolve_ws_handle` and `_normalize_ws_tag` in the same file.

This file is committed **before** either live run per repo precedent
(`be42aaf`, `a580f7b`, `558654e`). Sections marked `[PREDICTION]` are written
before any live pytest invocation against this test file; sections marked
`[MEASURED]` are filled in after each run, in the same commit sequence but
as a follow-up commit once results are in hand.

---

## Coverage boundary (acceptance criterion 8 -- stated up front, not implied)

This fix reaches **`BaseOperations._apply_props_loop` ONLY** -- 1 of the 3
writing-system resolution sites enumerated in spec section 3's errata table
(closed enumeration, verified by two independent greps at commit `b3ba083b`).
It does **NOT** reach:

1. `Grammar/PhonemeOperations.__ApplyBasicIPASymbol` -- builds its own
   `target_ws_by_id` and runs its own exact-case `dict.get` resolution loop,
   never calling `_apply_props_loop` or `_resolve_ws_handle`.
2. `Lexicon/ExampleOperations.ApplySyncableProperties`'s `TranslationsOC`
   loop -- same self-resolving shape, same non-delegation.

**The surprising asymmetry, spelled out:** after this fix lands, a phoneme's
`Name`/`Description` alts (which delegate to `super().ApplySyncableProperties`
and therefore to `_apply_props_loop`) **will** be saved under a divergent
case/separator spelling, while the **same phoneme's** `BasicIPASymbol` alt
**will still be silently dropped** under the identical divergent spelling,
because `__ApplyBasicIPASymbol` never delegates. The two apply paths named
above are declared OUT OF SCOPE by the spec's fence (section 1.2, C-D4-2) --
closing them means refactoring them to delegate, which is different work
requiring the user's approval to file (spec findings F2/F5). This is not a
partial fix reported as complete; it is a fix scoped to exactly one of three
known sites, and that boundary is machine-checked by the D4-T2 resolution-site
ratchet (`tests/operations/test_issue250_defect4_ws_resolution.py::TestResolutionSiteRatchet`).

---

## Anchors confirmed (spec section 6.1) -- before any edit

Grepped against the working tree at task start (`flexicon/code/BaseOperations.py`):

| Anchor | Found at | Unique? |
|---|---|---|
| `def _apply_props_loop(` | :319 | yes (matches spec's claimed :319) |
| `tgt_handle = target_ws_by_id.get(tgt_ws_id)` | :360 | yes, `grep -c` == 1 |
| `# Target lacks this WS; skip silently.` | :362 | yes |
| `ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()` (read-only ref, inside `ApplySyncableProperties`) | :1307 | yes within BaseOperations.py (not repo-wide unique per spec section 3 -- expected) |

No drift beyond the ordinary; no anchor missing or duplicated. Proceeded per
spec section 6.1's "stale line number is not a trigger" rule.

**After the fix landed**, `_apply_props_loop` moved to :420 (99 lines added
above it for `_normalize_ws_tag` + `_resolve_ws_handle`); the resolution call
site inside it is now `tgt_handle = _resolve_ws_handle(target_ws_by_id,
tgt_ws_id, _index_cache=_ws_resolve_cache)` at (approximately) :471.
`BaseOperations.ApplySyncableProperties`'s own build (the read-only reference
anchor) is now at :1419-1421 -- unedited, as required by C-D4-2.

---

## [PREDICTION] Unfixed-code run (acceptance criterion 2: the drop must be demonstrated, not assumed)

Command:
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue250_ws_case_divergence.py -m requires_live_project -q
```
Run against `BaseOperations.py` **before** the D4-T1 edit (i.e. the version at
the task's starting commit, anchors as recorded above, with the original
`tgt_handle = target_ws_by_id.get(tgt_ws_id)` exact-case-only resolution).

**Predicted result: all three tests FAIL.**

- `test_d4a_ws_map_case_divergent_resolves`: the pre-state assertion
  (`pre == ""`) passes (POSOperations.Create only populates the default
  analysis WS); the post-state assertion (`post == "TEST_D4a"`) FAILS because
  the unfixed exact-case `dict.get(flipped_case)` misses and the alt is
  silently dropped by the existing `continue` -- `post` reads back as `""`.
- `test_d4b_no_ws_map_source_id_case_divergent_resolves`: same shape, same
  predicted failure -- `post` reads back as `""`.
- `test_d4c_separator_divergent_resolves`: same shape, same predicted
  failure -- `post` reads back as `""`.

`tests/live_status.json` predicted to read `"run_mode": "live"` in all three
cases (the fixture opens a real LCM cache regardless of whether the fix is
present -- only the resolution behaviour differs).

## [MEASURED] Unfixed-code run

<!-- Filled in after running against the pre-fix BaseOperations.py. -->

Command run: (recorded verbatim below)

Result: PENDING -- see follow-up commit / STEP 3 log.

---

## [PREDICTION] Fixed-code run (acceptance criterion 1)

Same command, run against `BaseOperations.py` **after** the D4-T1 edit.

**Predicted result: all three tests PASS.**

- D4-a: `ws_map={"en": flipped_case}` -> `tgt_ws_id = flipped_case` ->
  `_resolve_ws_handle` misses exact match, builds the normalized index once,
  finds exactly one candidate (the real `ws_id`) under the normalized key,
  returns its handle. `post == "TEST_D4a"`.
- D4-b: no `ws_map` -> `src_ws_id` (`flipped_case`) passes through unchanged
  as `tgt_ws_id` -> same normalized resolution -> `post == "TEST_D4b"`.
- D4-c: `flipped_sep` (underscore/hyphen-flipped) resolves the same way ->
  `post == "TEST_D4c"`.
- C-D4-6 assertions pass in all three: writing-system count, `CurVernWss`,
  `CurAnalysisWss` unchanged from the pre-run baseline recorded in the shared
  fixture.

`tests/live_status.json` predicted `"run_mode": "live"`.

## [MEASURED] Fixed-code run

<!-- Filled in after running against the post-fix BaseOperations.py. -->

Command run: (recorded verbatim below)

Result: PENDING -- see follow-up commit / STEP 5 log.

---

## Ambiguity (D4-a2/step 9 of section 6.4) -- offline only, live deliberately NOT attempted

Per spec section 6.4 step 9: fabricating two live writing systems in the same
project that differ solely by case is not reliably possible (LDML/ICU
writing-system creation is itself case-insensitive on lookup in the places
that matter, and forcing two distinct WS defs with colliding normalized forms
would drift toward Defect 2 territory, which is out of scope here). The
ambiguity contract (C-D4-3 step 2b: two distinct handles raise
`FP_ParameterError` naming both) is covered **offline only**, in
`tests/operations/test_issue250_defect4_ws_resolution.py::TestResolveWsHandleAmbiguity`
and `TestApplyPropsLoopWsCaseFallback::test_ambiguous_spelling_raises_and_stops_the_apply`.

---

## Deviation from the section 6.4 illustrative sequence (documented, not silent)

Section 6.4 describes D4-a/D4-b/D4-c as sequential steps against one shared
POS object at one shared writing-system handle. This test file instead
creates **one throwaway `TEST_`-prefixed POS per variant** (three POS objects
total, each deleted in a `finally:` block), all sharing the same picked
`(ws_id, handle)` pair and its case/separator flips via a common fixture.
Reusing a single object across all three writes would mean D4-b's and D4-c's
"pre-state empty" assertion is untrue after D4-a's write lands (under fixed
code) -- the alt at that handle would already hold `"TEST_D4a"`, contaminating
the very pre-state check the spec's step 3 asks for. Three independent objects
keep every variant's pre-state genuinely empty and its post-state
unambiguously attributable to that variant's own apply call. The underlying
mechanism exercised (ws_map+case, no-ws_map+case, no-ws_map+separator) and all
C-D4-6 assertions are unchanged from the frozen shape.

---

## Offline delta (STEP 6)

<!-- Filled in after the D4-T1 fix lands, per the delta protocol: run the
"after" command three times (twice same shell, once fresh shell) and report
if they disagree. -->

PENDING -- see follow-up commit.

---

## Resolution-site ratchet result (D4-T2)

<!-- Filled in after running the offline suite. -->

PENDING -- see follow-up commit.

---

## `git diff --stat` (acceptance criterion 6)

<!-- Filled in in the final report / commit, once all edits are complete. -->

PENDING -- see cycle7-programmer-D4-T1-T3.md.
