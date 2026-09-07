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

**Diff proof:** `git show --stat 0ab9c606` -- `flexicon/code/System/CheckOperations.py`
(13 changed lines) and `tests/operations/test_name_field_identity_probe.py`
(572 changed lines) only.

**Collect count:**
```
python -m pytest tests/operations/test_name_field_identity_probe.py --collect-only -q -m requires_live_project
```
-> **20 tests collected** (15 existing, PN4/PN5/PN6 modified in place +
PN16-PN20 added). Nonzero.

**Live run:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_name_field_identity_probe.py -m requires_live_project -q -s
```
-> `20 passed, 72 warnings in 9.32s`. `tests/live_status.json` confirms
`"run_mode": "live"`, `"run_timestamp": "2026-09-07T21:05:56Z"`, and lists
`CheckOperations` add/modify/read all `"status": "pass"`, including PN4,
PN16, PN17, PN18.

**T4A-P1 (CreateCheckType persist) -- MATCHED, confirmed directly by PN16:**
```
[TABLE][PN16] first check stored Name (direct read, before duplicate attempt): 'TEST_NF_Chk '
```
and, after the rejected duplicate attempt, re-read again as `'TEST_NF_Chk '`
(see T4A-P4 below) -- byte-identical, trailing space intact.

**T4A-P2 (SetName persist) -- MATCHED exactly, PN17:**
```
[TABLE][PN17] check stored Name (direct read): 'TEST_NF_Chk_Renamed '
[VERDICT][PN17] SetName('TEST_NF_Chk_Renamed ') stored Name -> 'TEST_NF_Chk_Renamed ' (PREDICTED byte-identical to 'TEST_NF_Chk_Renamed ')
```

**T4A-P3 (FindCheckType comparison symmetry) -- MATCHED exactly, both PN4
(layer-B bypass) and PN18 (real public API):**
```
[TABLE][PN4] raw stored Name (direct read): 'TEST_NF_Check_Raw '
[PROBE] PN4 FindCheckType(unpadded): OK -> <SIL.LCModel.ICmPossibility object ...>
[PROBE] PN4 FindCheckType(padded): OK -> <SIL.LCModel.ICmPossibility object ...>
[PROBE] PN18 FindCheckType(unpadded): OK -> <SIL.LCModel.ICmPossibility object ...>
[PROBE] PN18 FindCheckType(padded): OK -> <SIL.LCModel.ICmPossibility object ...>
```
Both the unpadded and padded needle now find the padded haystack in both
tests -- the exact opposite of cycle 1's measured PN4 result, confirming
T4's `FindCheckType` fix landed correctly, both via a bypass-written
haystack and via a real end-to-end `CreateCheckType` write.

**T4A-P4 (duplicate rejection -- THE C8 pin, CreateCheckType) -- MATCHED
exactly, BOTH halves.** Live output:
```
[TABLE][PN16] first check stored Name (direct read, before duplicate attempt): 'TEST_NF_Chk '
[PROBE] PN16 CreateCheckType #2 (padded, duplicate): RAISED FP_ParameterError: A check type with the name 'TEST_NF_Chk ' already exists
[TABLE][PN16] first check stored Name, re-read after the rejected duplicate attempt: 'TEST_NF_Chk '
[SUMMARY][PN16] check types matching 'TEST_NF_Chk ' post-fix (stripped comparison): [('b408fb13-ec90-4370-82e5-c3ecdc9a4784', 'TEST_NF_Chk ')]
```
- **C8 pin half 1 (second call raises "already exists"):** CONFIRMED --
  `FP_ParameterError: A check type with the name 'TEST_NF_Chk ' already exists`.
- **C8 pin half 2 (first check re-reads byte-identical):** CONFIRMED --
  re-read (not re-asserted against the value passed in) as `'TEST_NF_Chk '`,
  trailing space intact, GUID `b408fb13-ec90-4370-82e5-c3ecdc9a4784`.
- Exactly ONE `ICmPossibility` check type matches the name post-fix -- no
  duplicate was persisted by the rejected second call.

## OFFLINE DELTA

| | passed | failed | deselected |
|---|---|---|---|
| Before | 1292 | 3 | 505 |
| After | 1292 | 3 | 510 |
| Delta | +0 | +0 | +5 |

Deselected rose by exactly 5, matching the 5 new `requires_live_project`
tests added (PN16-PN20). `3 failed` before AND after are the SAME three
known-foreign tests, same messages, confirmed by name:
`test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`,
`test_flexlibs2_alias_ratchet.py::...::test_no_executable_flexlibs2_imports_outside_alias_package`.
No fourth failure at any point.

## CONTRACT CONTRADICTIONS FOUND

None in C1-C11. One process deviation, disclosed plainly: this task's code
edit was made BEFORE the offline baseline was recorded (out of the
prescribed STEP-4 order), rather than after. Corrected by stashing the
task's own uncommitted `CheckOperations.py` edit (author-owned path,
`git stash push`), measuring the true pre-edit baseline, then `git stash
pop` to restore -- so the reported "before" figure is a genuine pre-edit
measurement, not a reconstruction. No contract item was affected by this
ordering deviation. See the programmer report's OFFLINE DELTA / STAGING
CHECK sections for the full staging-safety audit around this sequence.

## WHAT WAS NOT EXERCISED

None -- every pin half named for this file's Q-242A scope was exercised
live: `CreateCheckType` persist (PN16), `SetName` persist (PN17),
`FindCheckType` comparison symmetry both directions via both a layer-B
bypass haystack (PN4) and a real public-API-written haystack (PN18), and
the C8 pin's both halves for `CreateCheckType` (PN16). The Q-242B half
(non-str/whitespace-only raises) is tracked and exercised in
`live-t4b-check-q242b-fix.md`, not duplicated here.
