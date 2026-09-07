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

*(pending measuring run)*
