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

Command run (verbatim):
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue250_ws_case_divergence.py -m requires_live_project -q
```

Method: `flexicon/code/BaseOperations.py` was temporarily overwritten in the
shared working tree with the pre-fix blob (verified via
`git hash-object` == `git rev-parse HEAD:flexicon/code/BaseOperations.py`
at the pre-fix commit, `a32d94151fee1c3c62ccc33e71f3253990b0181a`), the live
suite was run, then the fixed blob was restored from a scratchpad backup and
re-verified by hash (`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db`) before any
further work continued.

**Result: `tests/live_status.json` -> `"run_mode": "live"`. 2 FAILED, 1 SKIPPED
-- matches the prediction exactly for D4-a/D4-b; D4-c did not reach a
pass/fail verdict for a different, pre-existing-project reason (see below).**

- `test_d4a_ws_map_case_divergent_resolves`: **FAILED**, as predicted.
  ```
  AssertionError: D4-a: ws_map value 'en' -> 'ETU' (case-divergent from the
  target's real ws.Id 'etu') must resolve to handle 999000002 and save the
  text. Got '' -- if this is empty, the fix did not land or did not reach
  this call path.
  assert '' == 'TEST_D4a'
  ```
- `test_d4b_no_ws_map_source_id_case_divergent_resolves`: **FAILED**, as
  predicted.
  ```
  AssertionError: D4-b: no ws_map, source key 'ETU' (case-divergent from
  target's real ws.Id 'etu') must still resolve to handle 999000002. Got ''.
  assert '' == 'TEST_D4b'
  ```
- `test_d4c_separator_divergent_resolves`: **SKIPPED** (loud skip, both
  before and after the fix -- this is a project-inventory limitation, not a
  pass/fail result). `target_sandbox`'s only two active writing systems are
  `en` (analysis, handle 999000001) and `etu` (vernacular, handle
  999000002) -- **neither has a `-` or `_` separator to flip**, so no
  separator-divergent spelling can be constructed live from this project's
  actual WS inventory. The skip message names the WS Id and states plainly
  that D4-a/D4-b are unaffected and that C-D4-5's separator path is proven
  offline instead (`test_issue250_defect4_ws_resolution.py`, D4-c-shaped
  unit tests using fabricated dicts). This is a documented gap in the LIVE
  half of D4-c coverage, not a silent one -- see acceptance-criteria notes
  below.

This is the required acceptance-criterion-2 demonstration: the pre-fix drop
is measured, not assumed, for both trigger paths this project's WS inventory
can exercise live (D4-a and D4-b).

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

Command run (verbatim, identical to the unfixed-side invocation):
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue250_ws_case_divergence.py -m requires_live_project -q
```

**Result: `tests/live_status.json` -> `"run_mode": "live"`. 2 PASSED, 1
SKIPPED -- matches the prediction exactly.**

- `test_d4a_ws_map_case_divergent_resolves`: **PASSED.** `post ==
  "TEST_D4a"` -- `ws_map={"en": "ETU"}` resolved through the normalized
  fallback to handle `999000002` (the real `etu` writing system).
- `test_d4b_no_ws_map_source_id_case_divergent_resolves`: **PASSED.**
  `post == "TEST_D4b"` -- no `ws_map`; source key `"ETU"` passed through
  unchanged as `tgt_ws_id` and still resolved to `999000002` via the same
  fallback (this is the D4-b path the original issue omits).
- `test_d4c_separator_divergent_resolves`: **SKIPPED**, same loud-skip
  reason as the unfixed side (no separator-bearing WS Id in this project's
  inventory) -- the fix's behaviour on this path is unmeasured live in this
  run and is covered offline only (see the section above and the "Ambiguity"
  section below for the general pattern of offline-only coverage where live
  project state cannot construct the trigger).
- **C-D4-6 assertions** (embedded in each passing test): writing-system
  count, `CurVernWss` (`"etu"`), and `CurAnalysisWss` (`"en"`) were asserted
  unchanged from each test's own pre-run baseline and did not fail --
  Defect 4 activates and creates nothing.

This is the required acceptance-criterion-1 demonstration for D4-a and D4-b:
the fix resolves the divergent spelling to the correct existing handle, read
back from the LCM by re-fetching the object fresh via `project.Object(hvo)`
(cast back to `IPartOfSpeech`), not by trusting the pre-write reference.

**D4-c live coverage gap, stated plainly (not left to be inferred):** this
run demonstrates D4-a and D4-b live, both before (drop) and after (save).
D4-c (separator divergence) could not be demonstrated live against
`target_sandbox` because neither of its two active writing systems (`en`,
`etu`) contains a `-` or `_` character to flip -- the sandbox's fixed,
tiny WS inventory (a property of the `Target` `.fwbackup` fixture, not of
this fix) makes the separator trigger unconstructible from real project
state without hunting for/fabricating a differently-shaped project, which
section 6.4's "no special project state" design explicitly rules out doing.
C-D4-5's separator-divergence guarantee is instead proven **offline**, at
the `_apply_props_loop`/`_resolve_ws_handle` unit level, in
`tests/operations/test_issue250_defect4_ws_resolution.py`
(`test_d4c_separator_divergent_resolves`,
`test_separator_divergence_resolves`), which fabricates the target dict
directly and is therefore independent of any particular project's WS
inventory. This is a live-evidence gap for D4-c specifically, disclosed
here rather than papered over by claiming full live coverage of all three
D4 variants.

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

## CONCURRENCY DISCLOSURE (read this before trusting section provenance)

While this task's live-verification work (this section and everything above
it) was in progress, a **second, independent agent instance**
(`Claude-Session: https://claude.ai/code/session_01RGBHqwkd2STFHfAXgeCbWt`,
distinct from this file's `Claude-Session:
https://claude.ai/code/session_01Wr7oeVWoo3XUJHFe83Km6Y`) was concurrently
dispatched against the **same spec** in the **same shared working tree** and
independently:

1. Committed `269b6a7` -- `fix(250-writingsystem-activation): D4-T1 --
   normalized WS-id lookup fallback in _apply_props_loop`. **Verified by
   hash:** the `flexicon/code/BaseOperations.py` blob this commit landed
   (`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db`) is **byte-identical** to this
   task's own independently-authored fix, confirmed via `git hash-object`
   against the scratchpad backup taken before this file's author restored
   the fixed content for the STEP 5 measurement below. This is almost
   certainly because `git commit --only -- <path>` reads **working-tree**
   content directly regardless of staging state -- the other agent's commit
   picked up whatever was sitting unstaged in the shared `BaseOperations.py`
   at that moment, which was this task's own in-progress, not-yet-committed
   D4-T1 edit. Net effect: the fix is correct and landed exactly once, but
   under the other session's attribution rather than this one's.
2. Committed `8c679ed` -- `docs(250-writingsystem-activation): D4-T5 --
   CHANGELOG entry for Defect 4 fix`. Reviewed in full: it correctly states
   the bug-fix-not-breaking-change framing, the new `FP_ParameterError`
   failure mode, and the full acceptance-criterion-8 coverage boundary
   (naming both `PhonemeOperations.__ApplyBasicIPASymbol` and
   `ExampleOperations.ApplySyncableProperties`'s `TranslationsOC` loop).
   D4-T5 is therefore ALSO already satisfied; no further CHANGELOG edit is
   needed from this task.
3. Edited (uncommitted, in the shared working tree) the "Offline delta"
   and "Resolution-site ratchet result" sections immediately below, plus
   the `git diff --stat` pointer at the end of this file -- using a
   disposable `git worktree` for its own "before" offline measurement
   (a cleaner isolation technique than this task used for the equivalent
   live before/after swap above; noted for future reference). Its content
   is retained below as-is; this task's author reviewed it and found it
   consistent with, though methodologically distinct from, this task's own
   offline delta (see the discrepancy note under "Offline delta" below).
4. Also independently created and deleted a transient
   `flexicon/code/_scratch_ratchet_probe.py` file as its own "bites when
   mutated" proof for the D4-T2 ratchet test. **This explains an otherwise
   mysterious transient ratchet-test failure this task's author observed
   mid-session**: a single `TestResolutionSiteRatchet` run failed, listing
   `_scratch_ratchet_probe.py` as a fourth site, then passed again on
   immediate re-run with no code change on this task's side. At the time
   this looked alarming (a real fourth site appearing and vanishing); it is
   now understood to be the other agent's own deliberate, momentary probe
   file overlapping with this task's test invocation, not a defect in
   either agent's work.

**What this task's author did NOT do in response:** rewrite, amend, reset,
or otherwise alter commits `269b6a7` or `8c679ed` -- per the standing
git-safety rules (never amend, never force-push, always new commits), and
because the content is independently verified correct regardless of
attribution. **What this task's author DID do:** complete and commit the
live D4-T3 verification (D4-T1's one piece the other agent's session did
not appear to attempt -- its edits above touch only offline measurement),
merge the other session's in-progress offline-delta/ratchet edits into the
final version of this file rather than discarding them, and write this
disclosure so a human or `/lex-lead` reviewing this file understands why it
carries findings from two different sessions. **Recommendation to the
user/lead:** the dispatch that produced `session_01RGBHqwkd2STFHfAXgeCbWt`
and the dispatch that produced this file were evidently the same D4-T1/T2/
T3/T5 task instructions sent to two separate agent threads against the same
tree at the same time; deduplicating that dispatch is a process fix outside
either agent's authority to make.

---

## Offline delta (STEP 6) -- filled in cycle 7 (programmer, D4-T1/T2/T5 spurt)

Command (identical both sides):
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q
```

**Before** -- disposable `git worktree add <tmp> e6a9492` (never the shared
main working tree; removed after measurement):
`2 failed, 350 passed, 501 deselected`. The 2 failures are the FOREIGN
`test_transaction_rollback.py::TestPhase2JoinOrOpen` pair (known-red
baseline, unrelated crew).

**After** -- same command, main working tree at commit `8c679ed3` (D4-T1 +
D4-T5 landed; D4-T2 tests were already present at `302d266`, ancestor of
both measurements): `2 failed, 371 passed, 504 deselected`. Same 2 failures,
unchanged messages.

**Delta: +21 passed (the new `test_issue250_defect4_ws_resolution.py`
offline suite), +3 deselected (the new `test_issue250_ws_case_divergence.py`
live tests, correctly excluded by `-m "not requires_live_project"`), 0
change in failures.** Zero offline-suite regressions (acceptance criterion
3). Worktree removed with `git worktree remove --force <tmp>` after the
`e6a9492` measurement.

Additionally, `tests/write_path_transactions` (B2g unbracketed-mutation
ratchet) run offline on the main tree: `24 passed`, confirming the new
helper performs no mutation.

**Cross-check from this task's own independent measurement (no
`git worktree` used; before/after both taken in the shared main tree by
swapping `flexicon/code/BaseOperations.py` between its scratchpad-backed
unfixed and fixed blobs, hash-verified each time):**
`--before` (unfixed blob, `--ignore=tests/operations/test_issue250_defect4_ws_resolution.py`
since that file imports fix-only symbols and cannot even collect against
unfixed code): `2 failed, 350 passed, 504 deselected`.
`--after` (fixed blob, full command as above, run four times total across
this session -- three consecutively plus one after the scratch-file scare
in item 4 of the concurrency disclosure -- all four agreeing):
`2 failed, 371 passed, 504 deselected`. Same delta conclusion (+21 passed,
0 change in failures, same two known-foreign `TestPhase2JoinOrOpen`
failures with unchanged messages). The `501` vs `504` deselected-count
difference between the two sessions' "before" figures is fully explained by
reference-point choice, not disagreement: the other session's `git worktree`
pinned to `e6a9492` (before either session's new test files existed, hence
501), while this session's in-tree "before" run already had
`test_issue250_ws_case_divergence.py` present (adding its 3
`requires_live_project`-marked tests to the deselected count, hence
504) and only excluded the fix-dependent offline file. Both measurements
independently confirm zero offline-suite regressions.

---

## Resolution-site ratchet result (D4-T2) -- filled in cycle 7

Ran green post-fix:
`python -m pytest tests/operations/test_issue250_defect4_ws_resolution.py::TestResolutionSiteRatchet -m "not requires_live_project" -q` -> `1 passed`.

**Bites-when-mutated proof:** added an untracked scratch file
`flexicon/code/_scratch_ratchet_probe.py` containing both signature
substrings (`ws_map.get(src_ws_id, src_ws_id)` / `target_ws_by_id.get(`).
Re-ran the same ratchet test: **FAILED**, `AssertionError` listing
`'_scratch_ratchet_probe.py'` as an extra item beyond the frozen 3-file
set. Deleted the scratch file (`rm flexicon/code/_scratch_ratchet_probe.py`;
it was never `git add`ed, so no `git checkout` of tracked content was
needed) and re-ran: **1 passed** again. Full detail in
`specs/250-writingsystem-activation/reviews/cycle7-programmer-D4-T1-T2-T5.md`.

---

## `git diff --stat` (acceptance criterion 6)

See `specs/250-writingsystem-activation/reviews/cycle7-programmer-D4-T1-T3.md`.

**Report reconciliation (corrected 2026-09-07, after cross-session
coordination).** An earlier revision of this paragraph claimed
`cycle7-programmer-D4-T1-T2-T5.md` "was never written as a file". **That was
wrong.** It exists and is tracked as of commit `4287114`, authored by the
concurrent session `flexicon-cd` described in the CONCURRENCY DISCLOSURE
above. Two reports exist for this one spurt because two sessions
independently executed the same dispatch plan. Both are genuine work and
neither is discarded. The ruling, made by the session holding
`specs/250-writingsystem-activation/spec.md`:

| Report | Canonical for |
|---|---|
| `cycle7-programmer-D4-T1-T2-T5.md` (`4287114`, flexicon-cd) | **D4-T1** (the fix) and **D4-T5** (CHANGELOG) |
| `cycle7-programmer-D4-T1-T3.md` (`312c5c3`, flexicon-19) | **D4-T2** (offline tests + ratchet) and **D4-T3** (live evidence) |

The production fix itself landed once, as `269b6a7`; the two sessions'
implementations were byte-identical by hash.
