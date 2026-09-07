# T4 -- CheckOperations Q-242A/Q-242B fix -- programmer report (cycle 4)

## LINE NUMBERS RE-DERIVED AT HEAD

By symbol lookup, immediately before editing: `CreateCheckType` def `:146`,
coercion `:196`; `FindCheckType` def `:300`, coercion `:341`, `target=`
`:344`, comparison `:350`; `SetName` def `:397`, coercion `:432`.
`_ValidateParam` `BaseOperations.py:3023`; `_ValidateStringNotEmpty` `:3191`
(`TypeError` `:3238`, `FP_ParameterError` `:3242`). All match `STATUS.md`'s
cycle-3-close figures exactly -- no drift this cycle.

## WHAT CHANGED

`flexicon/code/System/CheckOperations.py`, all three sites: replaced
`name = name.strip() if isinstance(name, str) else ""` plus the duplicate
trailing `_ValidateParam` with `self._ValidateStringNotEmpty(name, "name")`,
no reassignment of `name`. Leading `_ValidateParam(name, "name")` kept at
each site (C7a). `FindCheckType` additionally gained `.strip()` inline on
both `target = normalize_match_key(name, casefold=True)` and the loop's
comparison; `casefold=True` unchanged.

## Q-242A HALF

Persist: `CreateCheckType`/`SetName` now write the caller's original bytes
(no reassignment upstream of `TsStringUtils.MakeString`). Comparison:
`FindCheckType` strips both sides inline. C8 pin, both halves, confirmed
live (PN16).

## Q-242B HALF

Non-str payload -> `TypeError: name must be a string, got <type>`.
Whitespace-only `"   "` -> `FP_ParameterError: name cannot be empty or
contain only whitespace`, per lex-domain Q6 (CheckOperations is NOT a
C11(c) carve-out site). Both pinned at all three sites live (PN19, PN20).
No persist occurs on either raised path (check-type counts confirmed
unchanged for `CreateCheckType`; `SetName` seed's `Name` re-reads
unchanged).

## FindCheckType RETURN-TO-RAISE CHANGE

`FindCheckType`'s docstring says "Returns None if not found (doesn't raise
exception)." Pre-fix, a non-str or whitespace-only needle was silently
coerced to `""` and returned `None`. Post-fix it RAISES (`TypeError` /
`FP_ParameterError`) for those two input classes instead. Measured directly
(PN19/PN20), not inferred. Flagged for T5's CHANGELOG as its own line, not
folded into the persist-side description.

## C8 PIN BOTH HALVES

PN16: `CreateCheckType('TEST_NF_Chk ')` x2 -> second RAISES
`FP_ParameterError: A check type with the name 'TEST_NF_Chk ' already
exists`; first item's `Name` re-reads byte-identical `'TEST_NF_Chk '`
(genuine re-query, GUID `b408fb13-...`) after the rejected attempt. Exactly
one matching check type post-fix.

## C9 SEAM -- WHAT WAS MONKEYPATCHED AND WHAT WAS NOT

Reused the existing `_seed_valid_check_list()` test-instance-only
monkeypatch of `_GetCheckList` ALONE, returning a real
`ICmPossibilityList` built via the correct `.GetService(...)` call. This
displaces `_GetOrCreateCheckList`'s broken `GetInstance` fallback branch
(Q-CHK1, not touched). Nothing else was patched: `CreateCheckType`,
`FindCheckType`, `SetName`, `ServiceLocator`/`GetInstance`/`GetService`
were all exercised unmodified.

## LIVE EVIDENCE

Collect count: `20 tests collected` (`--collect-only -m requires_live_project`),
nonzero. `FLEXLIBS_REQUIRE_LIVE=1`, `pytest .../test_name_field_identity_probe.py
-m requires_live_project -q -s` -> `20 passed`. `tests/live_status.json`:
`"run_mode": "live"`. All predictions (T4A-P1..P4, T4B-P1..P5) MATCHED
exactly. Evidence: `evidence/live-t4a-check-q242a-fix.md`,
`evidence/live-t4b-check-q242b-fix.md`, both with `## WHAT WAS NOT
EXERCISED` (C10a).

## OFFLINE DELTA

Before: `3 failed, 1292 passed, 505 deselected`. After: `3 failed, 1292
passed, 510 deselected`. Delta `+0/+0/+5` (five new `requires_live_project`
tests). Same three known-foreign failures, same messages, no fourth.
**Process note, disclosed:** the code edit was made before recording the
"before" baseline (order slip against STEP 4). Corrected by stashing the
author-owned `CheckOperations.py` edit, measuring the true pre-edit
baseline, then restoring via `git stash pop` -- so the reported figures are
a genuine before/after pair, not a reconstruction.

## STAGING CHECK (AMENDMENT 2, steps 3 and 4)

Four commits this task, each bracketed: `2d8bfc57` (predictions),
`0ab9c606` (code+test), `cbbb55e6` (results), `f5291e90` (this report). For
the first three: `git status --porcelain` immediately before `git add`,
explicit paths only, `git status --porcelain` again immediately before
`git commit` showed no foreign path in the staged/first-column entries
(foreign paths seen mid-task included `.claude/ralph-loop.local.md`
deleted, `.vscode/`, `specs/duplicate-signature-harmonisation/`,
`specs/feature-structure-sync-gap/{STATUS.md,spec.md}` -- none staged), and
`git show --stat HEAD` immediately after each commit confirmed exactly the
intended file list (2, 2, and 2 files respectively, all mine).

**An actual race DID occur on the 4th commit (this report), exactly the
AMENDMENT 2 scenario.** After `git add` of only my review file, the
pre-commit `git status --porcelain` check showed FIVE of the other crew's
`specs/feature-structure-sync-gap/` files already sitting in the shared
index with staged (first-column) markers -- `.crew-handoff.json`,
`STATUS.md`, `evidence/live-cycle5-verification-t5.md`,
`reviews/cycle5-verification-T5.md`, `spec.md` -- landed there by their own
concurrent `git add` between my `git add` and my pre-commit check. Caught
BEFORE committing (per the protocol's intended catch point): ran
`git reset HEAD -- <those five paths>` (index-only, zero working-tree bytes
touched), re-ran `git status --porcelain` to confirm only my review file
remained staged, then committed. `git show --stat HEAD` afterward confirms
`f5291e90` contains exactly one file, mine. No foreign content was read,
altered, or read back incorrectly at any point.

## CONTRACT CONTRADICTIONS FOUND

None in C1-C11. One process deviation only (STEP-4 ordering, see OFFLINE
DELTA above), not a contract issue.

## WHAT I DID NOT DO

Did not touch `BaseOperations.py` or `Shared/string_utils.py`. Did not
touch `_GetOrCreateCheckList`, `ServiceLocator`, or fix Q-CHK1. Did not
harmonise the `AttributeError` sites (Q-242C). Did not add a whitespace-only
carve-out at CheckOperations (Q6 rules it loud there). Did not bundle T5.
Did not touch the real Target or run `scripts/restore_*.py`. Did not stage
any foreign path.
