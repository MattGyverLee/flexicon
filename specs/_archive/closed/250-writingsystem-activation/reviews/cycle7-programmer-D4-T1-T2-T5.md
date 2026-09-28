# Cycle 7 -- Programmer report: D4-T1, D4-T2, D4-T5 (+ offline delta, ratchet proof)

## Incident: D4-T1 was lost mid-cycle, re-authored identically

At task start, the inherited D4-T1 diff (+114/-1, confirmed via `git diff`)
vanished from the working tree between two of my own bash calls -- `git
diff` went to empty against an unchanged HEAD, and a fresh `Read` showed the
pristine pre-fix function. No git object existed for the lost edit (`git
fsck --dangling` / a full-blob string search found nothing); it was never
staged. This is the shared-working-tree risk CONCURRENCY.md warns about --
a second, concurrently-running D4 dispatch (session
`01Wr7oeVWoo3XUJHFe83Km6Y`, visible via `git log`/reflog, which meanwhile
committed `302d266` covering D4-T2/T3 test files) most likely reverted the
file. Root cause not confirmed; I did not chase it further. **I
re-authored the identical code from the diff text already captured in this
conversation** and committed it immediately (`269b6a7`) to close the
exposure window. `test_issue250_ws_case_divergence.py` is currently being
actively edited uncommitted by that other session -- left untouched per
protocol (not authored by me, not yet stable).

## Anchor re-confirmation (spec 6.1), all unique

`def _apply_props_loop(` :319 (unchanged from spec) -> after fix, function
body starts :420. `# Target lacks this WS; skip silently.` :362 pre-fix ->
:475 post-fix. Build literal (read-only ref) inside `ApplySyncableProperties`
:1307 pre-fix -> :1420 post-fix (shifted by the 114 inserted lines only; not
edited). `def ApplySyncableProperties(` :1236 -> :1349. All three anchors
occur exactly once in the file both before and after editing. No drift
beyond ordinary line-shift; matches spec section 6.1 expectations.

## Audit: PASS/FAIL against C-D4-1..C-D4-7

| Contract | Result |
|---|---|
| C-D4-1 hyphen-lowercase, local copy, comment naming source + F3 | PASS |
| C-D4-3 step 1 exact match first, byte-for-byte unaffected | PASS |
| C-D4-3 step 2a one distinct handle wins, deduped by handle | PASS |
| C-D4-3 step 2b >=2 distinct handles raise `FP_ParameterError` naming both | PASS |
| C-D4-3 step 2c absent -> None -> unchanged silent `continue` | PASS |
| C-D4-4 index lazy, built >=1x per call, all-exact-hits allocation-free | PASS |
| C-D4-5 normalization after `ws_map` indirection (covers D4-a/b/c) | PASS |
| C-D4-6 resolves only from passed-in dict; no `AllWritingSystems`/activation | PASS |
| C-D4-7 module-level, no `self`, importable unchanged by the two other sites | PASS |

No FAIL found; the re-authored code (identical to the lost original) is
contract-conformant as-is.

## D4-T2 / D4-T3 / predictions -- already present, verified not duplicated

The concurrent session's `302d266` already delivered: offline suite
`tests/operations/test_issue250_defect4_ws_resolution.py` (21 tests: exact-
match-first with a counting fake proving zero index reads on a hit, D4-a/b/c,
ambiguity naming both spellings, shared-handle non-ambiguity, absent-WS
silent continue, index-built-once across props) plus the resolution-site
ratchet; the live test file `test_issue250_ws_case_divergence.py`
(`--collect-only` verified, 3 tests, not run); and
`evidence/live-D4-T3.md` with predictions committed before any live run. I
verified rather than duplicated these (re-running offline: 21/21 pass
post-restore). I did not author a second `live-D4-T3-predictions.md` -- the
existing file already satisfies "predictions committed before any live run."

## Ratchet bites-when-mutated proof

Added untracked `flexicon/code/_scratch_ratchet_probe.py` containing both
signatures. Ratchet test: **FAILED**, reporting `'_scratch_ratchet_probe.py'`
as an extra site beyond the frozen 3. Deleted the file (never `git add`ed,
so no tracked-content checkout needed): `test -f ...` -> absent; ratchet
re-run: **1 passed**. (No tracked hash-object comparison needed -- untracked
route per task's stated alternative.)

## Offline delta (disposable worktree, e6a9492)

`git worktree add <scratchpad>/wt-e6a9492 e6a9492`; ran
`python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q`
both there and on main tree at `8c679ed3`.
Before: `2 failed, 350 passed, 501 deselected`. After: `2 failed, 371 passed,
504 deselected`. Delta: **+21 passed, +3 deselected, 0 change in failures**
(same 2 foreign `test_transaction_rollback.py` failures, unchanged messages).
Worktree removed. `tests/write_path_transactions` offline: `24 passed`
(B2g ratchet green; helper performs no mutation). Third known-red baseline
item (`test_flexlibs2_alias_ratchet.py`) re-checked separately: still the
sole, unchanged failure there.

## Commits (this spurt)

`269b6a7` fix: D4-T1 production code. `8c679ed` docs: CHANGELOG D4-T5
(coverage boundary per acceptance criterion 8). `9829e6a` docs: persist
orphaned D4-T4 report. `651577d` docs: fill offline-delta + ratchet-proof
sections of the evidence file.

## Deviations / scope notes

No production file touched besides `BaseOperations.py`. No map-build site
edited. `System/WritingSystemOperations.py` untouched. No live pytest was
run. `test_issue250_ws_case_divergence.py`'s in-flight uncommitted edits
(foreign) were left alone.
