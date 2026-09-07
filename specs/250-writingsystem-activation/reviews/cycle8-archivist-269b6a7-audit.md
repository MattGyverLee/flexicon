# Cycle 8 Archivist Audit -- commit 269b6a7 (D4-T1)

**Method note (binding, per dispatch):** 269b6a7 is treated as unreviewed
third-party code, not a recovered blob. I considered the byte-identical
convergence argument (a8e914b matches a second session's separately-authored
fix) and REJECTED it as possibly circular: `git commit --only -- <path>`
reads working-tree content regardless of staging, and the second session's
fix was in the tree during the commit window, so convergence and
read-the-other-copy are indistinguishable from the repo alone. That argument
is cited here only to explain why it is NOT used as corroboration anywhere
below. All findings come solely from `git show 269b6a7:flexicon/code/BaseOperations.py`
and `git show 269b6a7 --stat`.

## Clause-by-clause (blob-only evidence)

| Clause | Verdict | Evidence |
|---|---|---|
| C-D4-1 canonical hyphen-lowercase | PASS | `_normalize_ws_tag`: `return tag.replace("_", "-").lower()` (line 320-ish, module-level fn `def _normalize_ws_tag(tag):` at :319) |
| C-D4-2 fix at lookup, 0 map-build edits | PASS | `git show 269b6a7 --stat` = `flexicon/code/BaseOperations.py \| 115 +++...` only, 114 insertions/1 deletion, single file. The one deleted line is the old `tgt_handle = target_ws_by_id.get(tgt_ws_id)` inside `_apply_props_loop`, replaced by a call to the new helper -- no map-build site touched. |
| C-D4-3 exact-first / normalized-fallback / ambiguity raises | PASS | `_resolve_ws_handle`: `handle = target_ws_by_id.get(tgt_ws_id); if handle is not None: return handle` (step 1, untouched) followed by `if len(distinct_handles) > 1: raise FP_ParameterError(...)` naming `tgt_ws_id`, `sorted(candidates.keys())`, `sorted(distinct_handles)`. Dedup-by-handle before counting confirmed: `distinct_handles = set(candidates.values())`. |
| C-D4-4 index built >=once, <=once per apply call | PASS | `_apply_props_loop` inits `_ws_resolve_cache = {}` once per call (line 452) and threads it as `_index_cache` into every `_resolve_ws_handle` call in the loop; inside the helper: `if _index_cache is not None and "index" in _index_cache: norm_index = _index_cache["index"]` else build-and-store -- lazy, memoized, allocation-free on all-exact-hits. |
| C-D4-5 normalize tgt_ws_id AFTER ws_map indirection | PASS | Order in `_apply_props_loop`: `tgt_ws_id = (ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id)` computed first (unchanged), THEN `tgt_handle = _resolve_ws_handle(target_ws_by_id, tgt_ws_id, ...)` where normalization happens internally via `_normalize_ws_tag(tgt_ws_id)`. Normalization never touches `ws_map.get(...)`'s own arguments, so D4-b (no ws_map) is covered by construction. |
| C-D4-6 never activates/creates/consults AllWritingSystems/CurVernWss/CurAnalysisWss | PASS | grep of the full added blob for `AllWritingSystems`, `CurVernWss`, `CurAnalysisWss`, `AddToCurrent` returns exactly one hit, and it is inside the docstring's own claim ("never consults ``AllWritingSystems``..."), not executable code. The function body only ever reads the caller-supplied `target_ws_by_id`. |
| C-D4-7 helper module-level, param-only, no self | PASS | `def _resolve_ws_handle(target_ws_by_id, tgt_ws_id, _index_cache=None):` at zero indentation (:333), immediately following module-level `_normalize_ws_tag` (:319) and preceding module-level `def _apply_props_loop(` (:420) -- both siblings, not class members. Signature takes only `target_ws_by_id`/`tgt_ws_id`/`_index_cache`; no `self`, no project handle referenced anywhere in the body. |

No FAIL, no CONCERN. All seven clauses settle directly from the blob text
quoted above.

## Blast-radius confirmation

`git show 269b6a7 --stat` reports a single changed file:
`flexicon/code/BaseOperations.py | 115 +++++++++++++++++++++++++++++++++++++++-`
(114 insertions, 1 deletion, 1 file changed total). Therefore
`System/WritingSystemOperations.py`, `Grammar/PhonemeOperations.py`, and
`Lexicon/ExampleOperations.py` are untouched by this commit -- acceptance
criterion 6's automatic-rejection trigger does not fire.

## Non-issues acknowledged, not re-litigated

Per dispatch: `evidence/live-D4-T3-predictions.md` was correctly never
authored (predictions live under `[PREDICTION]` headings in the committed
`evidence/live-D4-T3.md`); not treated as a gap. `PhonemeOperations.py:1336`
(`all_ws = {ws.Id: ws.Handle ...}`) is confirmed a read-side capture inside
`GetSyncableProperties`, not a fourth resolution site; not re-derived here.

## Overall verdict

**PASS.** All seven frozen clauses (C-D4-1..C-D4-7) hold against the blob
alone; the blast-radius check confirms single-file scope. No P0. This audit
does not rely on, and explicitly rejects as possibly circular, the
byte-identical-convergence argument.
