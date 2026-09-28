# Issue #266 -- Live verification evidence: `PhonemeOperations.__ApplyBasicIPASymbol` writing-system resolution

**Task:** Close issue #266 (one-line C-D4-7 substitution: route the
`__ApplyBasicIPASymbol` writing-system lookup through the shared
`BaseOperations._resolve_ws_handle` helper #250 Defect 4 introduced for
exactly this purpose).
**Project:** `target_sandbox` ONLY (fresh tempdir copy of the Target
`.fwbackup`). Never the in-place Target, never Sena 3.
**Base commit:** `6435d92cfd38f21f39925626c130e3255e6c5e3d` (main, HEAD at
task start).
**Live test file:** `tests/operations/test_issue266_basicipasymbol_live.py`
**Offline test file:** `tests/operations/test_issue266_phoneme_ws_resolution.py`
**Fix location:** `flexicon/code/Grammar/PhonemeOperations.py` --
`__ApplyBasicIPASymbol`'s target writing-system lookup (import of
`_resolve_ws_handle` added at the top of the file).

---

## Coverage boundary (mirrors #250's D4-T3 evidence framing)

This fix closes 1 of the 2 remaining self-resolving writing-system
lookup sites left open by #250 Defect 4 (`BaseOperations._apply_props_loop`
was already fixed there). After this fix:

1. `BaseOperations._apply_props_loop` -- REACHED (closed by #250 Defect 4).
2. `Grammar/PhonemeOperations.__ApplyBasicIPASymbol` -- **REACHED (closed
   by this task, issue #266).**
3. `Lexicon/ExampleOperations.ApplySyncableProperties`'s `TranslationsOC`
   loop -- **still NOT reached.** Tracked separately as issue #267, filed
   deliberately separately because that loop creates and attaches the
   `ICmTranslation` object *before* resolving any writing system, so
   introducing a resolver that can raise `FP_ParameterError` mid-loop would
   leave an orphaned translation with zero alts unless the loop is
   reordered or a rollback is proven first. That is different work,
   requiring its own review.

**Sweep-pattern check performed:** `grep -rn "ws_map.get(src_ws_id,
src_ws_id)\|target_ws_by_id.get(" flexicon/code/` at task start returned
exactly the two known sites (`BaseOperations.py`, the reference
implementation, and `Lexicon/ExampleOperations.py:549-551`, issue #267).
No third, previously-undiscovered sibling site exists.

---

## Anchors confirmed (before any edit)

Grepped against the working tree at task start:

| Anchor | Found at | Unique? |
|---|---|---|
| `def __ApplyBasicIPASymbol(` | `flexicon/code/Grammar/PhonemeOperations.py:1434` | yes |
| `tgt_handle = target_ws_by_id.get(tgt_ws_id)` | `:1447` | yes within this file |
| `ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id` | `:1446` | yes within this file |
| `def _resolve_ws_handle(` | `flexicon/code/BaseOperations.py:333` | yes, already-landed #250 Defect 4 helper |

No drift; matches the issue's cited line numbers closely (issue text says
`:1447` for the `.get()` call, confirmed).

---

## [MEASURED] Unfixed-code run (both sides measured, per issue requirement)

Command (verbatim, both runs):
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue266_basicipasymbol_live.py -m requires_live_project -q
```

**Method:** `flexicon/code/Grammar/PhonemeOperations.py` was temporarily
reverted in place (via the `Edit` tool, not a raw file overwrite) to the
exact pre-fix blob, hash-verified byte-identical to `HEAD`:

```
git hash-object flexicon/code/Grammar/PhonemeOperations.py
  -> 0522c13eacced95ffa8cb2b97f803d84be8f6914
git show HEAD:flexicon/code/Grammar/PhonemeOperations.py | git hash-object --stdin
  -> 0522c13eacced95ffa8cb2b97f803d84be8f6914
```

Live run against this byte-verified pre-fix blob:

**Result: `1 failed, 1 passed`. `tests/live_status.json` -> `"run_mode": "live"`.**

- `test_case_divergent_basicipasymbol_alt_resolves_and_saves`: **FAILED**,
  demonstrating the drop:
  ```
  AssertionError: #266: source key 'ETU' (case-divergent from the target's
  real ws.Id 'etu') must resolve to handle 999000002 and save the
  BasicIPASymbol text. Got '' -- if this is empty, the fix did not land or
  did not reach __ApplyBasicIPASymbol.
  assert '' == 'TEST_266_ipa'
  ```
  Pre-state (`GetBasicIPASymbol` at handle `999000002` before the apply)
  was confirmed empty (`""`) via a freshly re-fetched `IPhPhoneme` (not a
  stale reference). Post-state, re-read from the LCM after re-fetching the
  phoneme by Hvo, was also `""` -- the alt was silently dropped, exactly
  as the pre-fix `target_ws_by_id.get(tgt_ws_id)` exact-match-only lookup
  predicts.
- `test_exact_match_still_saves_unchanged` (zero-regression control, an
  exact-case spelling): **PASSED**, confirming the pre-fix code's
  already-working exact-match path is untouched by this measurement
  methodology.

This is the required "demonstrate the drop, do not assume it" evidence:
the same test file, same project, same writing-system inventory, only the
production code differs.

---

## [MEASURED] Fixed-code run

The fixed blob was restored (via the `Edit` tool, reapplying the exact
`_resolve_ws_handle` routing) and re-verified by hash before any further
work continued:

```
git hash-object flexicon/code/Grammar/PhonemeOperations.py
  -> 6a0423f82a978274f9c13e27509295f80355439a
```

(This is the hash of the working-tree blob containing the #266 fix --
the import of `_resolve_ws_handle` and the routed lookup in
`__ApplyBasicIPASymbol`, described above.)

Same command, run against this fixed blob:

**Result: `2 passed`. `tests/live_status.json` -> `"run_mode": "live"`.**

- `test_case_divergent_basicipasymbol_alt_resolves_and_saves`: **PASSED.**
  `post == "TEST_266_ipa"` -- the source key `'ETU'` (case-divergent from
  the target's real vernacular `ws.Id` `'etu'`) resolved through
  `_resolve_ws_handle`'s normalized fallback to handle `999000002` and the
  BasicIPASymbol text was saved. Read back from the LCM via a **freshly
  re-fetched** `IPhPhoneme` (`project.Object(hvo)` cast to `IPhPhoneme`),
  not the pre-write reference.
- `test_exact_match_still_saves_unchanged`: **PASSED.** An exact-case
  spelling (`'etu'`) still resolves and saves unchanged -- the
  zero-regression basis (step 1 of `_resolve_ws_handle` is byte-for-byte
  the pre-fix exact-match path).
- Both tests assert the writing-system store is untouched: WS count,
  `CurVernWss` (`"etu"`), and `CurAnalysisWss` (`"en"`) were unchanged
  from each test's own pre-run baseline. The fix activates, creates, and
  widens nothing.

---

## Live-inventory limitation (disclosed, not overclaimed)

`target_sandbox`'s only two active writing systems are `en` (analysis,
handle `999000001`) and `etu` (vernacular, handle `999000002`) -- neither
contains a `-` or `_` character, so **separator divergence** (`en_US` vs
`en-US` shape) cannot be constructed live from this project's real WS
inventory, matching the exact limitation already recorded for #250's own
D4-T3 evidence (`live-D4-T3.md`). **Case divergence** (`etu` vs `ETU`) IS
constructible and is what this file proves live, both before (drop) and
after (save).

Separator divergence for this call site is covered **offline only**, in
`tests/operations/test_issue266_phoneme_ws_resolution.py::
TestApplyBasicIPASymbolNormalizedFallback::
test_separator_divergent_alt_resolves`, which fabricates the
`target_ws_by_id` dict directly and is therefore independent of any
particular project's WS inventory. This is a live-evidence gap for the
separator variant specifically, disclosed here rather than papered over
by claiming full live coverage of both divergence shapes.

Ambiguity (the new `FP_ParameterError` failure mode) is likewise covered
**offline only** (`TestApplyBasicIPASymbolAmbiguity` in the same file), for
the same reason #250's own ambiguity contract was covered offline only:
fabricating two live writing systems in one project that differ solely by
case/separator normalization is not reliably constructible, per spec 250
section 6.4 step 9's reasoning (reproducing a colliding-normalized-form WS
pair would itself drift into Defect-2 territory, out of scope here).

---

## Offline delta

Command:
```
python -m pytest tests/operations/test_issue250_defect4_ws_resolution.py tests/operations/test_issue266_phoneme_ws_resolution.py tests/operations/test_phonemes.py tests/operations/test_basic_ipa.py tests/operations/test_apply_syncable_properties.py -m "not requires_live_project" -q
```

Result on the fixed tree: `71 passed, 25 deselected`. No failures.

---

## Resolution-site ratchet result

`tests/operations/test_issue250_defect4_ws_resolution.py::
TestResolutionSiteRatchet::test_exactly_three_resolution_sites_exist`
(now pinning **two** sites, not three -- `Grammar/PhonemeOperations.py`
removed from `_EXPECTED_RESOLUTION_SITE_FILES` in this same change):

```
python -m pytest tests/operations/test_issue250_defect4_ws_resolution.py::TestResolutionSiteRatchet -m "not requires_live_project" -q
```
-> `1 passed`.

Confirmed the actual lexical hit-set after the fix, independent of the
test:
```
grep -rn "ws_map.get(src_ws_id, src_ws_id)\|target_ws_by_id.get(" flexicon/code/
  -> BaseOperations.py:380   (inside _resolve_ws_handle itself -- expected)
  -> BaseOperations.py:466   (inside _apply_props_loop's own ws_map read -- expected)
  -> Lexicon/ExampleOperations.py:549  (issue #267, untouched)
  -> Lexicon/ExampleOperations.py:551  (issue #267, untouched)
```
`Grammar/PhonemeOperations.py` no longer appears in either signature's
hit-set: the handle lookup now goes through `_resolve_ws_handle` (no
literal `target_ws_by_id.get(` text remains), and the `ws_map`
indirection was reshaped to `ws_map.get(src_ws_id, tgt_ws_id)` (default
argument is the already-initialised `tgt_ws_id` local, not a repeated
`src_ws_id` literal), which is behaviourally identical to the original
`ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id` but no longer
matches the ratchet's lexical signature for the pre-fix self-resolving
shape.

---

## Pass/fail line

**PASS.** `run_mode: live` confirmed in both the unfixed-code run (drop
demonstrated, byte-verified pre-fix blob) and the fixed-code run (save
demonstrated, byte-verified fixed blob). Offline suite green (71 passed).
Ratchet updated and green. Separator-divergence and ambiguity variants for
this specific call site are proven offline only, disclosed above as a
known, pre-existing (see #250 D4-T3) limitation of `target_sandbox`'s WS
inventory, not a gap introduced by this task.
