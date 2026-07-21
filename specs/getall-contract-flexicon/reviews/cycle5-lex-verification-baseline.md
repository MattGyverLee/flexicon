# Verification Report — Regression Baseline Comparison

**Feature:** getall-contract-flexicon
**Date:** 2026-07-20
**Verified By:** Verification Agent
**Status:** PASS

## Objective

Prove that the flexicon changeset (current uncommitted working-tree edits in
`d:/Github/_Projects/_LEX/flexicon`) introduces ZERO new test failures/errors
relative to clean `main` (HEAD `ff1c008`, "build: derive package version
dynamically from flexicon.version"). A prior reviewer asserted the
139 failed / 1538 passed / 33 errors figure is a pre-existing baseline
unrelated to the changeset, but supplied no numeric comparison. This report
supplies it.

## Method

1. Confirmed the changeset is the current dirty working tree (no stash
   entries exist — `git stash list` empty). `git status --porcelain` showed
   ~50 modified `.py` files across `flexicon/code/**` (docstring/behavior
   edits touching every Operations module, not only the 3 files named in the
   task brief — see Note below) plus `README.rst` and an untracked
   `docs/getall-contract.md` / `specs/getall-contract-flexicon/`.
2. Ran `python -m pytest -q -p no:cacheprovider --tb=no -rfE` in the
   changeset (current working tree) state. Captured full FAILED/ERROR node
   IDs.
3. Created an isolated worktree at HEAD with
   `git worktree add <scratch>/clean-main HEAD` (no stash/reset touched the
   user's dirty tree). Confirmed `git status --porcelain` in the worktree was
   clean and `git log -1` showed `ff1c008`. Ran the identical pytest command
   there.
4. Diffed the two FAILED/ERROR node-ID sets with `comm`.
5. Removed the worktree (`git worktree remove --force`).

## Raw Results

| | Failed | Passed | Skipped | Errors | Fail+Error node IDs |
|---|---|---|---|---|---|
| **Baseline (clean main, HEAD ff1c008)** | 139 | 1539 | 26 | 33 | 172 |
| **Changeset (working tree)** | 139 | 1545 | 20 | 33 | 172 |

Both runs report `139 failed, ... 33 errors` — matching the prior reviewer's
figures for the changeset side. The full-collection run completed
successfully in both states; the `flexlibs2\code\...WfiAnalysisOperations.py`
FileNotFoundError collection error mentioned as a possible environmental
caveat did **not** occur in either run — collection succeeded cleanly both
times, so that caveat is moot for this comparison.

## Node-ID Set Diff

- `new_failures = changeset_fails - baseline_fails` → **0 node IDs**
- `fixed = baseline_fails - changeset_fails` → **0 node IDs**

The two 172-line FAILED/ERROR node-ID sets are byte-for-byte identical
(`diff`/`comm` confirms exact match — same 139 test names, same 33 error
names, no membership change in either direction).

## Secondary Observation: Passed/Skipped Discrepancy (Non-Regression)

Passed count differs (1539 vs 1545) and skipped count differs (26 vs 20) by
the same delta (6), even though the failed/error sets are identical. Root
cause identified: `git worktree add` only materializes **tracked** files.
The baseline worktree lacks the untracked Sena 3 `.fwbackup` test fixture
files that are present (untracked) in the original working directory. 10 of
the skip reasons in the baseline run read
`No Sena 3 .fwbackup found in <scratch>\clean-main\tests\fixtures`, whereas
the same tests in the changeset tree find the fixture and execute (and pass).
This is a worktree-fixture artifact of the comparison methodology, not a
code behavior difference introduced by the changeset — no changeset source
edit touches fixture discovery, and none of these 6 tests appear in either
failed/error set. It does not affect the regression verdict.

## Note on Changeset Scope

The task brief described the changeset as "source docstrings, BaseOperations.py,
the 3 code fixes in Shared/MediaOperations.py, Lists/AgentOperations.py,
Lists/TranslationTypeOperations.py, plus docs/README.rst." The actual dirty
working tree is broader: it touches nearly every `Operations.py` file under
`flexicon/code/**` (Discourse, Grammar, Lexicon, Lists, Notebook, Reversal,
Scripture, Shared, System, TextsWords — ~50 files total), in addition to the
3 named code-fix files and `README.rst`. This report's comparison covers the
changeset **as it actually exists on disk** at verification time, which is
the correct object of verification regardless of the brief's file list. This
broader scope does not change the verdict: the failed/error node-ID sets
still match baseline exactly.

## Verdict

**REGRESSION-CLEAN (delta 0)**

- `|new_failures|` = 0
- `|fixed|` = 0
- Failed/error counts and node-ID membership are identical between clean
  main (HEAD `ff1c008`) and the changeset working tree.
- The 139 failed / 33 errors are confirmed pre-existing and unrelated to the
  changeset — the prior reviewer's assertion is now backed by an exact
  node-ID-level comparison, not just matching counts.
- The 6-test passed/skipped shift is a worktree-fixture artifact (untracked
  `.fwbackup` files not copied by `git worktree add`), not a code regression
  or code-driven improvement between the two runs.

## Artifacts (scratchpad, not committed)

- Changeset run output: `C:\Users\thoua\AppData\Local\Temp\claude\d--Github--Projects--LEX-FlexToolsMCP\4fe72c6b-51c5-44d2-87cb-5cba1c42f008\scratchpad\changeset_pytest.txt`
- Baseline run output: `C:\Users\thoua\AppData\Local\Temp\claude\d--Github--Projects--LEX-FlexToolsMCP\4fe72c6b-51c5-44d2-87cb-5cba1c42f008\scratchpad\baseline_pytest.txt`
- Changeset node IDs: `...\scratchpad\changeset_nodeids.txt` (172 lines)
- Baseline node IDs: `...\scratchpad\baseline_nodeids.txt` (172 lines)
- Diff outputs: `...\scratchpad\new_failures.txt` (0 lines), `...\scratchpad\fixed.txt` (0 lines)

---
**Verified By:** Verification Agent
**Date:** 2026-07-20
