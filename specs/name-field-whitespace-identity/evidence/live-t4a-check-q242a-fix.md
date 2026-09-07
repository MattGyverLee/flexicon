# Name-field whitespace identity -- T4A (CheckOperations Q-242A: comparison
symmetry + persist fix), live evidence

**Scope (per `tasks.md` T4 / `spec.md` C4, C5, C6, C8, C9):**
`flexicon/code/System/CheckOperations.py`, three sites, re-confirmed at HEAD
by symbol lookup immediately before editing (matched `STATUS.md`'s
cycle-3-close figures exactly -- no drift this cycle):

- `CreateCheckType` (def `:146`, coercion `:196`) -- leading
  `_ValidateParam(name, "name")` at `:194` STAYS (C7a). Replaced
  `name = name.strip() if isinstance(name, str) else ""` plus the trailing
  duplicate `_ValidateParam(name, "name")` (old `:196-197`) with a single
  call `self._ValidateStringNotEmpty(name, "name")`, **no reassignment of
  `name`**. `self.FindCheckType(name)` (`:200`) and
  `TsStringUtils.MakeString(name, wsHandle)` (`:218`) now see the caller's
  original, unstripped argument.
- `FindCheckType` (def `:300`, coercion `:341`) -- leading `_ValidateParam`
  at `:339` STAYS. Same coercion-to-`_ValidateStringNotEmpty` replacement.
  Added `.strip()` inline on BOTH sides of the comparison per C4's exact
  shape: `target = normalize_match_key(name, casefold=True).strip()`
  (`:344`) and
  `if check_name and normalize_match_key(check_name, casefold=True).strip() == target:`
  (`:350`). `casefold=True` UNCHANGED (case-insensitive Find by design; not
  harmonised with Anthropology's `casefold=False`).
- `SetName` (def `:397`, coercion `:432`) -- leading `_ValidateParam` at
  `:430` STAYS. Same coercion-to-`_ValidateStringNotEmpty` replacement.
  `TsStringUtils.MakeString(name, wsHandle)` (`:439`) now sees the caller's
  original argument.

This is C7's EXPLICIT fix shape, not C11's Shape A/B choice -- all three
sites had the SAME upstream shape (null-only `_ValidateParam` followed by
the coercing rebind), so all three take the identical replacement.

**One commit, both Q-242A and Q-242B halves (C6):** these are the SAME
three expressions -- the `_ValidateStringNotEmpty` swap simultaneously
removes the coercing rebind (fixing Q-242A's persist/comparison symmetry)
and converts the silent coercion into a loud raise (fixing Q-242B). This
file (T4A) tracks the Q-242A half; `evidence/live-t4b-check-q242b-fix.md`
tracks the distinct Q-242B half, per C6's separate-evidence requirement.

No shared file (`BaseOperations.py`, `Shared/string_utils.py`) touched --
`_ValidateStringNotEmpty` is CALLED, not edited. `git diff --stat --
flexicon/` shows this one file only.

## OFFLINE BASELINE, BEFORE THE EDIT

Command: `python -m pytest tests -m "not requires_live_project" -q`

```
3 failed, 1292 passed, 505 deselected, 12 warnings in 13.46s
```

Matches `CONCURRENCY.md`'s expected red baseline exactly (three named
known-foreign failures): `test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`,
`test_flexlibs2_alias_ratchet.py::...::test_no_executable_flexlibs2_imports_outside_alias_package`.
No fourth failure.

Derived by first making the code edit (out of the prescribed order, an
honest process note -- see the programmer report's OFFLINE DELTA section),
then stashing this task's own uncommitted edit to
`flexicon/code/System/CheckOperations.py` (author-owned path,
`git stash push -- <that path>`) to recover a true pre-edit measurement,
running the suite, then `git stash pop` to restore the edit. `git status
--porcelain` at the stashed instant showed only `.claude/ralph-loop.local.md`
(deleted, not mine), `.vscode/` (untracked, fenced), and
`specs/duplicate-signature-harmonisation/` (untracked, fenced) -- none of
those are this task's, none were staged.

## PREDICTIONS (committed BEFORE the live measuring run; C28 forward rule --
not edited after the fact even if a prediction misses)

- **T4A-P1 (CreateCheckType persist byte-identical):**
  `Checks.CreateCheckType("TEST_NF_Chk ")` (trailing space) is **PREDICTED**
  to persist the check type's `Name` re-read from the LCM
  (`ITsString(check.Name.get_String(wsHandle)).Text`) as byte-identical to
  the caller's original argument, because `TsStringUtils.MakeString(name,
  wsHandle)` at `:218` now runs against the unmodified parameter (no
  reassignment).

- **T4A-P2 (SetName persist byte-identical):**
  `Checks.SetName(check, "TEST_NF_Chk_Renamed ")` (trailing space) is
  **PREDICTED** to persist the check type's `Name` re-read from the LCM as
  byte-identical to the caller's argument, same mechanism.

- **T4A-P3 (FindCheckType comparison symmetry -- PN4 flip, plus PN18 via
  the public API):** Once a name is persisted WITH its trailing space
  intact (via layer-B bypass for PN4, simulating what the fixed
  `CreateCheckType`/`SetName` themselves now do; via the real public
  `CreateCheckType` for PN18), `FindCheckType(<unpadded needle>)` /
  `FindCheckType(<padded needle>)` are BOTH **PREDICTED** to return the
  item (not `None`) -- the opposite of PN4's pre-fix assertion (which
  required both to be `None`, proving needle-only stripping). Post-fix,
  both sides of `FindCheckType`'s comparison are stripped inline
  (`casefold=True` unchanged), so a padded or unpadded needle matches a
  padded haystack symmetrically.

- **T4A-P4 (duplicate rejection -- THE C8 pin, CreateCheckType, both
  halves):** `Checks.CreateCheckType(<name with trailing space>)` called
  TWICE through the real public API is **PREDICTED**: the first call
  succeeds and persists the padded name byte-identically; the SECOND call
  is **PREDICTED to RAISE** `FP_ParameterError` ("already exists"), because
  `CreateCheckType`'s own `self.FindCheckType(name)` check (`:200`) now
  reaches `FindCheckType`'s now-symmetric comparison with the SAME padded
  name the first call persisted. The first check's stored `Name` is
  additionally **PREDICTED** to re-read BYTE-IDENTICAL from the LCM,
  re-read AFTER the rejected duplicate attempt (genuine re-query, not a
  re-assertion of the value passed in) -- same pattern as T2's PN8
  `first_reread` / T3's PN12 `first_reread`.

## Test file

`tests/operations/test_name_field_identity_probe.py` -- EXTENDED in place.
PN4/PN5/PN6 modified in place (flipped to assert fixed behaviour, pre-fix
behaviour preserved verbatim in each docstring as a labelled
historical-record paragraph, per the T2/T3 precedent). Five NEW tests
added, PN16-PN20 (per the task brief's numbering instruction -- "your new
tests start at PN16"):
- PN16 -- T4 C8 pin, both halves, `CreateCheckType` only, through the real
  public API (this file's Q-242A half).
- PN17 -- `SetName` persist byte-identical (this file's Q-242A half).
- PN18 -- `FindCheckType` symmetry via the real public API, complementing
  PN4's layer-B version (this file's Q-242A half).
- PN19 -- Q-242B non-str pin at all three sites (tracked in
  `live-t4b-check-q242b-fix.md`).
- PN20 -- lex-domain Q6 whitespace-only pin at all three sites (tracked in
  `live-t4b-check-q242b-fix.md`).

Collect count:
`python -m pytest tests/operations/test_name_field_identity_probe.py --collect-only -q -m requires_live_project`
-> **20 tests collected** (15 existing + 5 new). Nonzero.

## Fixtures

`target_sandbox` / `target_sandbox_path` ONLY. Never the real Target, never
`scripts/restore_*.py`. `_seed_valid_check_list()` (test-instance-only
`_GetCheckList` monkeypatch, C9's sole authorised seam) used in every new
test that reaches `CreateCheckType`/`FindCheckType`/`SetName` through the
public API.

## RESULTS (filled in AFTER the live measuring run; predictions above were
not edited)

_To be filled in after the live run below._

## OFFLINE DELTA

_To be filled in after the live run below._

## CONTRACT CONTRADICTIONS FOUND

_To be filled in after the live run below._

## WHAT WAS NOT EXERCISED

_To be filled in after the live run below (C10a mandatory section)._
