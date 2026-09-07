# Name-field whitespace identity -- T3 (AnthropologyOperations persist + comparison-symmetry fix), live evidence

**Scope (per `tasks.md` T3 / `spec.md` C3, C4, C5, C7(b), C8):**
`flexicon/code/Notebook/AnthropologyOperations.py`, four sites, re-confirmed
at HEAD by symbol lookup immediately before editing (matched the task
brief's line numbers exactly, no drift this cycle):

- `Create` (`:263-270`) -- leading `_ValidateParam(name, "name")` at `:263`
  STAYS. `Create`'s only upstream guard is `_ValidateParam`, a null-check
  only (no `isinstance` branch, per `BaseOperations.py`, re-confirmed by
  symbol this cycle) -- so `.strip()` ITSELF is what raises `AttributeError`
  for a non-str payload today, and `Create` is one of the three C7(b)-named
  sites. Per T2's precedent (`reviews/cycle2-t2-programmer.md` "NOTES FOR T3
  AND T4"), replaced the reassigning `name = name.strip()` at old `:265`
  with a **throwaway, non-reassigning** `name.strip()` call (result
  discarded) -- still raises `AttributeError` for non-str, no longer
  rebinds `name`. Deleted the now-verbatim-duplicate trailing
  `_ValidateParam(name, "name")` at old `:266` (C7a: keep the leading one
  only). `TsStringUtils.MakeString(name, wsHandle)` (`:301`, was `:300`)
  now persists the caller's original, unstripped argument.
- `CreateSubitem` (`:372-375`) -- identical shape and rationale to `Create`
  above; this is the SECOND of the three C7(b)-named sites. Leading
  `_ValidateParam(name, "name")` (`:372`) STAYS; reassigning strip replaced
  with a throwaway, non-reassigning `name.strip()` call; duplicate trailing
  `_ValidateParam` deleted; `TsStringUtils.MakeString(name, wsHandle)`
  (`:391`) now persists the caller's original argument.
- `Find` (`:553-568`) -- `_ValidateParam(name, "name")` (`:553`) STAYS.
  **KEPT** `:555`'s `if not name or not name.strip(): return None`
  unchanged -- it is both the empty-needle short-circuit AND the
  read-path `AttributeError` trigger for a non-str payload, neither of
  which C4/C7 touch. Deleted the needle rebinding `name = name.strip()` at
  old `:558`. Strip INLINE at both comparison sides instead, per C4's
  exact shape, `casefold=False` preserved unchanged:
  ```
  target = normalize_match_key(name, casefold=False).strip()
  ...
  if normalize_match_key(item_name, casefold=False).strip() == target:
  ```
- `Exists` (`:505-510`) -- **NOT TOUCHED**, per the task brief's explicit
  rule 4: its strip is a needle-only strip on a read path that delegates
  to `Find`; neither a comparison site nor a persist site, so C4 does not
  reach it, and the double-strip is harmless once `Find` is symmetric.

**Observation, not a task (C5):** `CreateSubitem` has no dedup check at
all, unlike `Create` -- confirmed unchanged; no dedup check was added.

No shared file (`BaseOperations.py`, `Shared/string_utils.py`) touched.
`git diff --stat -- flexicon/` shows this one file only.

## OFFLINE BASELINE, BEFORE THE EDIT

Command: `python -m pytest tests -m "not requires_live_project" -q`

```
3 failed, 1292 passed, 501 deselected, 12 warnings in 14.85s
```

Matches `CONCURRENCY.md`'s expected red baseline exactly (three named
known-foreign failures): `test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`,
`test_flexlibs2_alias_ratchet.py::...::test_no_executable_flexlibs2_imports_outside_alias_package`.
No fourth failure. Derived by stashing this task's own uncommitted edit to
`flexicon/code/Notebook/AnthropologyOperations.py` (author-owned path,
`git stash push -- <that path>`), running the suite, then `git stash pop`
to restore -- since the edit had already been made before this measurement
was taken. `git status --porcelain` at that point showed only the other
crew's known/attributed files as modified (`BaseOperations.py`,
`Grammar/InflectionFeatureOperations.py`, `Grammar/PhonFeatureOperations.py`,
`.claude/ralph-loop.local.md` deleted) plus `.vscode/` and
`specs/duplicate-signature-harmonisation/` untracked/attributed -- none
staged by this task.

## PREDICTIONS (committed BEFORE the live measuring run; C28 forward rule --
not edited after the fact even if a prediction misses)

- **T3-P1 (Create persist byte-identical):** `Anthropology.Create("TEST_NF_...  ")`
  (trailing space) is **PREDICTED** to persist the item's `Name` re-read
  from the LCM (`ITsString(item.Name.get_String(wsHandle)).Text`) as
  byte-identical to the caller's original argument, because
  `TsStringUtils.MakeString(name, wsHandle)` at `:301` now runs against the
  unmodified parameter (throwaway strip only, no reassignment).

- **T3-P2 (CreateSubitem persist byte-identical):** `Anthropology.CreateSubitem(parent,
  "TEST_NF_... ")` (trailing space) is **PREDICTED** to persist the
  subitem's `Name` re-read from the LCM as byte-identical to the caller's
  argument, same mechanism as Create.

- **T3-P3 (Find/Exists comparison symmetry -- PN3 flip):** Once a name is
  persisted WITH its trailing space intact (via layer-B bypass, simulating
  what the fixed `Create`/`CreateSubitem` themselves now do),
  `Find(<unpadded needle>)` / `Find(<padded needle>)` are BOTH **PREDICTED**
  to return the item (not `None`), and `Exists(<unpadded needle>)` /
  `Exists(<padded needle>)` are BOTH **PREDICTED** to return `True` -- the
  opposite of PN3's pre-fix assertion (which required all four to be
  `None`/`False`, proving needle-only stripping). Post-fix, both sides of
  `Find`'s comparison are stripped inline, so a padded or unpadded needle
  matches a padded haystack symmetrically.

- **T3-P4 (duplicate rejection -- THE C8 pin, Create only, both halves):**
  `Anthropology.Create(<name with trailing space>)` called TWICE through
  the real public API is **PREDICTED**: the first call succeeds and
  persists the padded name byte-identically; the SECOND call is
  **PREDICTED to RAISE** `FP_ParameterError` ("already exists"), because
  `Create`'s own `self.Exists(name)` check now reaches `Find`'s
  now-symmetric comparison with the SAME padded name the first call
  persisted. The first item's stored `Name` is additionally **PREDICTED**
  to re-read BYTE-IDENTICAL from the LCM, re-read AFTER the rejected
  duplicate attempt (genuine re-query, not a re-assertion of the value
  passed in) -- same pattern as T2's PN8 `first_reread`.
  **`CreateSubitem` has NO dedup check (C5) -- no analogous rejection is
  predicted or asserted for it.**

- **T3-P5 (Shape-B preservation -- non-str payload):** A plain non-str
  payload (no `.strip()` method) passed as `name` is **PREDICTED** to still
  raise `AttributeError` at BOTH `Create()` and `CreateSubitem()`, unchanged
  from pre-fix, because the throwaway `.strip()` call introduced by this
  fix is still the first thing to fail on a non-str payload (both sites'
  only upstream guard, `_ValidateParam`, is a null-check only).

- **T3-P6 (Q-242D disclosure measurement -- NOT a fix):**
  `Anthropology.Create("   ")` (whitespace-only) is **PREDICTED** to raise
  NO exception and to persist the literal three-space string `"   "`
  verbatim, because (a) `_ValidateParam("   ", "name")` does not reject a
  non-empty (even whitespace-only) string, (b) the throwaway `.strip()`
  call has no effect on what gets persisted (non-reassigning), and (c)
  `self.Exists("   ")` delegates to `Find("   ")`, whose unchanged `:555`
  guard (`if not name or not name.strip(): return None`) returns `None`
  for an all-whitespace needle, so the dedup check never fires regardless
  of prior persisted state. This is a **DELIBERATE, DISCLOSED** behaviour
  change (pre-fix: persisted `""`; post-fix: persists `"   "`), explicitly
  ruled OUT OF SCOPE to "fix" by `spec.md` C7(b) / `tasks.md` T3 rule 6
  (Q-242C/Q-242D territory) -- this test MEASURES and RECORDS the value, it
  does not adjudicate whether it is desirable.

## Test file

`tests/operations/test_name_field_identity_probe.py` -- EXTENDED in place.
PN3 modified in place (flipped to assert fixed behaviour, pre-fix behaviour
preserved verbatim in its docstring as a labelled historical-record
paragraph, per the T2 precedent). Four NEW tests added, PN12-PN15 (PN9-PN11
are T1's, per the task brief's numbering instruction):
- PN12 -- T3 C8 pin, both halves, `Create` only, through the real public API.
- PN13 -- `CreateSubitem` persist half only, no dedup assertion.
- PN14 -- Shape-B preservation, non-str payload at both `Create` and
  `CreateSubitem`.
- PN15 -- Q-242D disclosure measurement, `Create("   ")`.

Collect count: `python -m pytest tests/operations/test_name_field_identity_probe.py --collect-only -q -m requires_live_project`
-> **15 tests collected** (11 existing + 4 new). Nonzero.

## Fixtures

`target_sandbox` / `target_sandbox_path` ONLY. Never the real Target,
never `scripts/restore_*.py`.

## RESULTS (filled in AFTER the live measuring run; predictions above were
not edited)

**Diff proof:** `git show --stat ab638aae` --
`flexicon/code/Notebook/AnthropologyOperations.py` (27 changed lines) and
`tests/operations/test_name_field_identity_probe.py` (349 insertions / 21
deletions) only. `Create` -- reassigning `name = name.strip()` and the
duplicate trailing `_ValidateParam` both replaced by a single throwaway
`name.strip()` call plus a rationale comment. `CreateSubitem` -- identical
shape. `Find` -- needle rebinding deleted; `target =` line and the loop's
comparison line each gained `.strip()` on their `normalize_match_key(...)`
calls, `casefold=False` unchanged. `Exists` -- byte-for-byte untouched
(confirmed by the diff showing zero hunks in that method).

**Collect count:**
```
python -m pytest tests/operations/test_name_field_identity_probe.py --collect-only -q -m requires_live_project
```
-> **15 tests collected** (11 existing, PN3 modified in place + PN12-PN15
added). Nonzero.

**Live run:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_name_field_identity_probe.py -m requires_live_project -q -s
```
-> `15 passed, 58 warnings in 8.60s`. `tests/live_status.json` confirms
`"run_mode": "live"`, `"run_timestamp": "2026-09-07T20:43:15Z"`, and lists
`AnthropologyOperations` add/modify/read (PN12/PN13/PN15, PN3, PN14) all
`"status": "pass"`.

**T3-P1 (Create persist) -- MATCHED, confirmed directly by PN12:**
```
[TABLE][PN12] first item stored Name (direct read, before duplicate attempt): 'TEST_NF_Anth '
```
and, after the rejected duplicate attempt, re-read again as `'TEST_NF_Anth '`
(see T3-P4 below) -- byte-identical, trailing space intact.

**T3-P2 (CreateSubitem persist) -- MATCHED exactly, PN13:**
```
[TABLE][PN13] subitem stored Name (direct read): 'TEST_NF_Sub '
[VERDICT][PN13] CreateSubitem('TEST_NF_Sub ') stored Name -> 'TEST_NF_Sub ' (PREDICTED byte-identical to 'TEST_NF_Sub ')
```

**T3-P3 (Find/Exists comparison symmetry, PN3 flip) -- MATCHED exactly.**
Live output:
```
[TABLE][PN3] raw stored Name (direct read): 'TEST_NF_Anthro_Raw '
[PROBE] PN3 Find(unpadded): OK -> <SIL.LCModel.ICmAnthroItem object ...>
[PROBE] PN3 Find(padded): OK -> <SIL.LCModel.ICmAnthroItem object ...>
[PROBE] PN3 Exists(unpadded): OK -> True
[PROBE] PN3 Exists(padded): OK -> True
```
Both the unpadded and padded needle now find the padded haystack -- the
exact opposite of cycle 1's measured result, confirming T3's `Find` fix
landed correctly.

**T3-P4 (duplicate rejection -- THE C8 pin, Create only) -- MATCHED
exactly, BOTH halves.** Live output:
```
[TABLE][PN12] first item stored Name (direct read, before duplicate attempt): 'TEST_NF_Anth '
[PROBE] PN12 Create #2 (padded, duplicate): RAISED FP_ParameterError: Anthropology item 'TEST_NF_Anth ' already exists
[TABLE][PN12] first item stored Name, re-read after the rejected duplicate attempt: 'TEST_NF_Anth '
[SUMMARY][PN12] items matching 'TEST_NF_Anth ' post-fix (stripped comparison): [('6f333b89-a2b8-45d9-b3b8-194693b8bebc', 'TEST_NF_Anth ')]
```
- **C8 pin half 1 (second call raises "already exists"):** CONFIRMED --
  `FP_ParameterError: Anthropology item 'TEST_NF_Anth ' already exists`.
- **C8 pin half 2 (first item re-reads byte-identical):** CONFIRMED --
  re-read (not re-asserted against the value passed in) as
  `'TEST_NF_Anth '`, trailing space intact, GUID
  `6f333b89-a2b8-45d9-b3b8-194693b8bebc`.
- Exactly ONE `ICmAnthroItem` matches the name post-fix -- no duplicate was
  persisted by the rejected second call.

**T3-P5 (Shape-B preservation) -- MATCHED exactly, PN14 (plus PN7's
pre-existing Create coverage, unaffected):**
```
[PROBE] PN14 Anthropology.Create(non-str): RAISED AttributeError: '_NonStrPayload' object has no attribute 'strip'
[PROBE] PN14 Anthropology.CreateSubitem(non-str): RAISED AttributeError: '_NonStrPayload' object has no attribute 'strip'
```
Both sites still raise `AttributeError`, unchanged from pre-fix, confirming
the throwaway-strip mechanism (not plain deletion) was used correctly at
both C7(b)-named sites. PN7's own `Anthropology.Create(non-str)` assertion
(untouched by this task) also still passed with the identical exception.

**T3-P6 (Q-242D disclosure measurement) -- MATCHED exactly, PN15:**
```
[VERDICT][PN15] Create('   ') -> exc=None (PREDICTED None, disclosure only)
[TABLE][PN15] Create('   ') stored Name (direct read, MEASURED): '   '
[SUMMARY][PN15] Q-242D disclosure: Anthropology.Create('   ') post-fix persists '   ' (predicted '   ') -- measured, NOT fixed, per spec.md C7(b)/tasks.md T3 rule 6.
```
Measured value recorded verbatim: post-fix, `Create("   ")` raises no
exception and persists the literal three-space string. This is the
disclosed, not-fixed Q-242D consequence -- no whitespace-only rejection was
added.

## OFFLINE DELTA

| | passed | failed | deselected |
|---|---|---|---|
| Before | 1292 | 3 | 501 |
| After | 1292 | 3 | 501 |
| Delta | +0 | +0 | +0 |

Measured by stashing this task's own uncommitted edit to
`AnthropologyOperations.py` (`git stash push -- <that path>`, an
author-owned path), running the offline suite for the "before" figure,
then `git stash pop` to restore the edit and running it again for the
"after" figure -- since the edit had already been made before this
measurement was taken this cycle. `3 failed` before AND after are the SAME
three known-foreign tests, same messages, confirmed by name:
`test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`,
`test_flexlibs2_alias_ratchet.py::...::test_no_executable_flexlibs2_imports_outside_alias_package`.
No fourth failure at any point. `passed`/`deselected` both unchanged
offline (expected -- the four new tests are all `requires_live_project`,
so they are deselected from this run, not counted in `passed`).

## CONTRACT CONTRADICTIONS FOUND

None. T2's `SetName` mechanism-deviation note (`reviews/cycle2-t2-
programmer.md`) predicted exactly this shape for T3's two persist sites,
and it held: `Create`/`CreateSubitem`'s only upstream guard is the
null-check-only `_ValidateParam` (confirmed by symbol lookup, no
`isinstance` branch), so the throwaway-strip shape (not T1's plain
deletion) was required and used at both sites, live-confirmed unchanged by
PN14. `Find`'s comparison-symmetry shape was identical to T2's `Exists`,
as predicted -- no per-family variation was needed there. One incidental
process note, not a C1-C8 contradiction: this task's FIRST commit attempt
of the predictions evidence file accidentally swept in the other crew's
then-staged, uncommitted files (`BaseOperations.py`,
`Grammar/InflectionFeatureOperations.py`,
`Grammar/PhonFeatureOperations.py`, and two
`feature-structure-sync-gap/` files) due to a race between this session's
`git status` check and the other crew's concurrent `git add`. Caught
immediately by inspecting `git show --stat HEAD` after the commit;
corrected via `git reset --soft HEAD~1` followed by `git reset HEAD --
<foreign paths>` (index-only operations, zero working-tree content
touched) and a clean re-commit containing only this feature's own file.
No foreign file content was read, altered, or lost at any point --
confirmed by diffing the foreign files' working-tree state before and
after the correction (identical). Recorded here as a process-safety
finding for later tasks: **always re-run `git status --porcelain`
immediately before `git commit`, not just before `git add`**, when a
concurrent crew is active in the same tree.

## WHAT I DID NOT DO

- Did not touch `BaseOperations.py` or `Shared/string_utils.py` (fenced, C4).
- Did not touch `Exists` (`AnthropologyOperations.py:505-510`), per the
  task brief's explicit rule 4 -- confirmed byte-for-byte unchanged by the
  diff proof above.
- Did not add a dedup check to `CreateSubitem` (C5) -- confirmed by PN13's
  docstring/scope and by the diff showing no new `Exists`/`Find` call
  introduced in that method.
- Did not add a whitespace-only rejection to `Create`/`CreateSubitem`, and
  did not swap `_ValidateParam` for `_ValidateStringNotEmpty` (Q-242C/
  Q-242D, explicitly ruled out this cycle) -- PN15 measures and discloses
  the resulting behaviour change instead of fixing it.
- Did not harmonise `Create`/`CreateSubitem`'s `AttributeError`-on-non-str
  exception type (C7(b), Q-242C, out of scope) -- confirmed still raises
  `AttributeError` live via PN7 and PN14.
- Did not file a GitHub issue for anything found this cycle.
- Did not stage or commit `.claude/ralph-loop.local.md` (deleted, not
  mine), `.vscode/`, `specs/duplicate-signature-harmonisation/`,
  `specs/name-field-whitespace-identity/reviews/cycle3-archivist.md` (the
  Archivist's file), or any other-crew file -- only this task's own two
  files (code+test commit `ab638aae`) plus this evidence file (predictions
  commit `7bc6d01c`) were staged, each confirmed via `git diff --cached
  --stat` immediately before commit after the race described above was
  corrected.
- Did not run `scripts/restore_*.py` or touch the real Target; used
  `target_sandbox` exclusively.

## WHAT WAS NOT EXERCISED

None -- every pin half named in the task brief was exercised live: Create
persist (PN12), CreateSubitem persist (PN13), Find/Exists comparison
symmetry both directions (PN3), the C8 pin's both halves for Create
(PN12), Shape-B AttributeError preservation at both sites (PN14, plus
PN7's pre-existing Create coverage), and the Q-242D disclosure measurement
(PN15). `Exists` itself was not independently re-exercised beyond PN3's
existing calls (it delegates entirely to `Find` and was not modified), but
that is a request to touch untouched code, not a pin half left
unmeasured.
