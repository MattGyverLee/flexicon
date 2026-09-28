# Cycle 8 -- D4 Verification Gate

**Isolation path taken:** Rule (c), path A -- disposable `git worktree add <tmpdir> HEAD`.
All mutation testing (Legs 1-4, and the T14a live mutations in Leg 2) ran inside
the worktree; the shared working tree was touched only ONCE, for the Leg 7
metadata patch, which was copied in and committed via `git commit --only`
(commit `c76c399`). `tests/fixtures/*.fwbackup` (gitignored, needed for
`target_sandbox`) were copied read-only into the worktree's own gitignored
fixtures dir -- an addition of test input data inside the worktree, not a
mutation of the shared tree.

**Falsifiability rests on mutation, not on provenance.** The byte-identical
convergence between the two authoring sessions was NOT used as evidence
anywhere below. Every PASS below is a mutation that turned green tests red
and a restore verified by `git hash-object` equality against
`git rev-parse HEAD:<path>`.

## Verdict table

| Leg | Result | Evidence |
|---|---|---|
| 1: M-D4-1 (identity `_normalize_ws_tag`) | **PASS-KILLED** | Offline: 14/21 failed (predicted set: TestNormalizeWsTag, TestResolveWsHandleNormalizedFallback x6, TestResolveWsHandleAmbiguity x3, TestApplyPropsLoopWsCaseFallback D4-a/b/c + ambiguity + index test). Live: `FLEXLIBS_REQUIRE_LIVE=1 pytest test_issue250_ws_case_divergence.py -m requires_live_project -q` -> `2 failed, 1 skipped`, run_mode `live`. Restore hash `a8e914b...` == `git rev-parse HEAD:flexicon/code/BaseOperations.py`. |
| 1: M-D4-2 (ambiguity guesses lowest handle) | **PASS-KILLED** | `-k "TestResolveWsHandleAmbiguity or test_ambiguous_spelling..."` -> `3 failed, 1 passed`. Restore hash verified equal to HEAD. |
| 1: M-D4-3 (exact match forced to miss) | **PASS-KILLED** | `-k "test_exact_hit_never_consults_index or test_exact_match_still_preferred..."` -> `2 failed, 0 passed`. Restore hash verified; full file re-run `21 passed`. |
| 1: one-liner anchor | **PASS** | `python -c "from flexicon.code.BaseOperations import _resolve_ws_handle; print(_resolve_ws_handle({'etu':2},'ETU'))"` -> `2` (matches expected). |
| 2: M-T14a-2 (slot routing forced to rows[0]) | **PASS-KILLED** | Live: `pytest test_makefeatstruc_c3_live.py -k test_slot_disambiguates_from_and_to_through_makefeatstruc -m requires_live_project` -> `1 failed`. Restore hash verified; full file re-run (post-restore) `3 passed`. |
| 2: M-T14a-3 (no-slot branch picks rows[0] instead of raising) | **PASS-KILLED** | Live: `pytest test_makefeatstruc_c3_live.py -k test_ambiguous_owner_without_slot_raises_through_makefeatstruc -m requires_live_project` -> `1 failed`. Restore hash verified; full file re-run `3 passed`. Checkpoint 2c does NOT reopen -- both T14a tests are non-tautological. |
| 3: ratchet mutation (4th resolution site in `string_utils.py`) | **PASS-KILLED, tracked & hashed** | Pre: `git rev-parse HEAD:flexicon/code/Shared/string_utils.py` == `git hash-object` == `f81fbb8...`. Appended `# probe: target_ws_by_id.get(`. `TestResolutionSiteRatchet` -> `1 failed`, message: `Found: ['BaseOperations.py', 'Grammar/PhonemeOperations.py', 'Lexicon/ExampleOperations.py', 'Shared/string_utils.py']` -- names the 4th site exactly as predicted. Restored via `git show HEAD:<path>` (not checkout); post-restore hash `f81fbb8...` == pre; re-run -> `1 passed`. |
| 4: offline delta (corrected baseline) | **PASS** | `pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q`, run TWICE: both times `2 failed, 371 passed, 504 deselected`. Failures both times: `test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception` and `::test_depth_restored_on_exception` -- exactly the two named foreign failures, no third, no message drift. Counts agree across runs. |
| 5: live re-verification, as-committed | **PASS** | `FLEXLIBS_REQUIRE_LIVE=1 pytest test_issue250_ws_case_divergence.py -m requires_live_project -q` -> `2 passed, 1 skipped`. `tests/live_status.json` `run_mode` = `live`. Skip is `test_d4c_separator_divergent_resolves`, accepted per lead ruling. |
| 6: artifact check for false D4-c live claims | **PASS, no hits** | `grep -in "D4-c\|separator" CHANGELOG.md` -> 3 hits, none claim live coverage (they describe the fix's behaviour and the whitespace/separator feature, unrelated to D4-c's live status). `live-D4-T3.md` and both cycle-7 review files explicitly and repeatedly state D4-c was **SKIPPED live** and proven **offline only** -- no file claims "all three proven live." CHANGELOG (lines ~268-278) states the criterion-8 coverage boundary and names both unreached paths verbatim: `Grammar/PhonemeOperations.__ApplyBasicIPASymbol` and `Lexicon/ExampleOperations.ApplySyncableProperties`'s `TranslationsOC` loop. |
| 7: D4-T7 live_phase markers | **PASS** | Added `@pytest.mark.live_phase("POSOperations", "modify")` to all 3 tests in `test_issue250_ws_case_divergence.py` (3-line diff, metadata only -- no assertion/behaviour line touched, confirmed by `git diff`). Re-ran leg 5's command: still `2 passed, 1 skipped`, `run_mode` still `live`. `tests/live_status.json.by_test` now shows `operations_class: POSOperations, phase: modify` for all three; `uncategorized_live_tests` no longer lists any of them (`hits: []`). Committed to the shared tree: `git commit --only -F ... -- tests/operations/test_issue250_ws_case_divergence.py` (commit `c76c399`), index verified empty before and after. |

## Overall verdict: **PASS**

No mutation stayed NOT-KILLED. Checkpoint 2c does not reopen. Leg 4's delta
matches the pinned 2-failure foreign baseline exactly, on both runs. Leg 6
found zero mischaracterizations of D4-c's live status. All restores verified
byte-identical to `HEAD` via `git hash-object`.

## Blockers
None.

## Recommendation
APPROVE.
