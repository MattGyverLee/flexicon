# T3 -- AnthropologyOperations persist + comparison-symmetry fix -- programmer report (cycle 3)

## WHAT CHANGED

`flexicon/code/Notebook/AnthropologyOperations.py`, four sites, all line
numbers re-confirmed against HEAD by symbol lookup before editing (matched
the brief exactly): `Create:263-270`, `CreateSubitem:372-375`,
`Find:553-568`, `Exists:505-510` (untouched).

- `Create`/`CreateSubitem` -- replaced the reassigning `name = name.strip()`
  with a throwaway, non-reassigning `name.strip()` call; deleted the
  now-duplicate trailing `_ValidateParam(name, "name")`. Persist
  (`TsStringUtils.MakeString(name, wsHandle)`) now writes the caller's
  original bytes.
- `Find` -- deleted the needle rebinding; added inline `.strip()` on both
  `target = normalize_match_key(name, casefold=False)` and the loop's
  comparison, `casefold=False` unchanged. Kept `:555`'s
  `if not name or not name.strip(): return None` unchanged.
- `Exists` -- untouched, per the brief's rule 4.

Commits: `7bc6d01c` (predictions), `ab638aae` (code + test), `7409ad6d`
(results). `git diff --stat -- flexicon/` shows this one file only.

## SHAPE CHOSEN PER SITE AND WHY

`Create`/`CreateSubitem` are two of C7(b)'s three named `AttributeError`
sites -- their only upstream guard is the null-check-only `_ValidateParam`,
so `.strip()` itself raises for non-str. Copied T2's `SetName` shape
(throwaway call) exactly, not T1's plain deletion, per the cycle-2 report's
explicit note. `Find`'s comparison shape is identical to T2's `Exists`.

## PREDICTIONS VS MEASURED

All six predictions (T3-P1 persist, P2 CreateSubitem persist, P3 Find/
Exists symmetry, P4 C8 pin, P5 Shape-B, P6 Q-242D) MATCHED exactly, live.
Full transcripts in the evidence file.

## C8 PIN BOTH HALVES

Live (PN12): `Create('TEST_NF_Anth ')` called twice -> second call RAISES
`FP_ParameterError: Anthropology item 'TEST_NF_Anth ' already exists`; the
first item's `Name` re-reads byte-identical `'TEST_NF_Anth '` after the
rejected attempt (genuine re-query). Exactly one matching item post-fix.

## Q-242D MEASURED BEHAVIOUR

`Create("   ")` (PN15): raises no exception, persists the literal
three-space string `'   '` (was `''` pre-fix). Measured and recorded, not
fixed, per C7(b)/tasks.md T3 rule 6.

## LIVE EVIDENCE

`specs/name-field-whitespace-identity/evidence/live-t3-anthropology-fix.md`.
Collect count 15 (11 existing + PN12-PN15). Live run: `15 passed`,
`run_mode: live`, `2026-09-07T20:43:15Z`.

## OFFLINE DELTA

Before: `3 failed, 1292 passed, 501 deselected`. After: identical. Delta
`+0/+0/+0`. Same three known-foreign failures by name and message; no
fourth at any point.

## CONTRACT CONTRADICTIONS FOUND

None in C1-C8. One **process incident**, not a contract issue: the first
attempt to commit the predictions evidence file swept in the other crew's
then-concurrently-staged files (`BaseOperations.py`, two Grammar files, two
`feature-structure-sync-gap/` files) due to a race between my `git status`
check and their `git add`. Caught immediately via `git show --stat HEAD`;
corrected with `git reset --soft HEAD~1` + `git reset HEAD -- <foreign
paths>` (index-only, zero working-tree bytes touched, verified by diff
before/after) and a clean re-commit. Flagged for T4: re-run `git status
--porcelain` immediately before `git commit`, not only before `git add`,
while the other crew is active.

## WHAT I DID NOT DO

- Did not touch `BaseOperations.py`, `Shared/string_utils.py`, or `Exists`.
- Did not add a dedup check to `CreateSubitem` (C5).
- Did not add whitespace-only rejection or swap validators (Q-242C/D ruled
  out this cycle) -- PN15 discloses instead of fixing.
- Did not harmonise the `AttributeError` sites (C7(b), confirmed unchanged
  live via PN7/PN14).
- Did not file a GitHub issue.
- Did not stage any other-crew or archivist file.
- Did not touch the real Target or run `scripts/restore_*.py`.
