# Name-field whitespace identity -- T2 (TextOperations persist + comparison-symmetry fix), live evidence

**Scope (per `tasks.md` T2 / `spec.md` C1-C5, C8):**
`flexicon/code/TextsWords/TextOperations.py`, three sites, re-confirmed at
HEAD by symbol lookup immediately before editing (no drift from the task
brief's line numbers this cycle):

- `Create` (`:151-152`) -- `_ValidateStringNotEmpty(name, "text name")` at
  `:151` STAYS unchanged. Remove the rebinding `name = name.strip()` at
  `:152` so `TsStringUtils.MakeString(name, wsHandle)` at `:170` persists
  the caller's original, unstripped argument. `self.Exists(name)` at
  `:155` now receives the RAW name -- correct and safe once `Exists`
  strips both sides of its own comparison (below).
- `Exists` (`:457-464`) -- `_ValidateStringNotEmpty(name, "text name")` at
  `:457` STAYS. Remove the rebinding `name = name.strip()` at `:458`.
  Strip INLINE at both comparison sides instead, per C4's exact shape,
  `casefold=False` preserved unchanged:
  ```
  target = normalize_match_key(name, casefold=False).strip()
  ...
  if normalize_match_key(text_name, casefold=False).strip() == target:
  ```
- `SetName` (`:606-609`) -- `_ValidateParam(name, "name")` at `:606` STAYS.
  The existing shape is `_ValidateParam` -> `name = name.strip()` -> a
  SECOND `_ValidateParam(name, "name")` at `:609`. Per C7(b), SetName's
  `AttributeError`-on-non-str behaviour (raised today by `.strip()` itself,
  since `_ValidateParam` is a null-check only -- confirmed by reading
  `BaseOperations.py:2747-2796`, which documents "Lightweight null check"
  with no `isinstance` branch) is explicitly OUT OF SCOPE (belongs to
  Q-242C) and must NOT change type. Simply deleting the `.strip()` call
  entirely (as T1 did for `DiscourseOperations`) would REMOVE that
  `AttributeError` trigger for a non-str payload, since there `_ValidateStringNotEmpty`
  already type-checks upstream and `TextOperations.SetName` has no
  equivalent guard. To preserve the exact existing exception shape while
  still not rebinding `name`, the fix keeps the `.strip()` CALL as a
  throwaway (discarding its result, not reassigning `name`):
  ```
  self._ValidateParam(name, "name")

  name.strip()  # throwaway: still raises AttributeError for a non-str
                # payload (C7(b) -- exception TYPE unchanged), but no
                # longer rebinds `name`, so the persist below writes the
                # caller's original argument.
  self._ValidateParam(name, "name")
  ```
  This is a deliberate, documented DEVIATION in mechanism (not in outcome)
  from T1's "just delete the line" shape, driven by C7(b)'s binding
  constraint that SetName's non-str exception type must not change. It is
  recorded here as a CONTRACT CONTRADICTIONS FOUND item if T3/T4 copy this
  file's shape naively without checking whether their own sites have an
  upstream type-check already (they do, via `_ValidateStringNotEmpty` for
  `CheckOperations`, but `AnthropologyOperations.Create`/`CreateSubitem`
  are explicitly EXCLUDED from harmonisation per C7(b) and are not part of
  T3's persist-only scope in the same way -- T3 must check its own sites'
  shape independently, not copy this mechanically).

No shared file (`BaseOperations.py`, `Shared/string_utils.py`) touched.
No new comparison method added; `Exists` is the only comparison site in
scope for T2 (per `tasks.md` T2, `Find` at `:507-517` is NOT listed and is
NOT touched).

## OFFLINE BASELINE, BEFORE THE EDIT

Command: `python -m pytest tests -m "not requires_live_project" -q`

```
3 failed, 1292 passed, 501 deselected, 12 warnings in 14.59s
```

Matches `CONCURRENCY.md`'s expected red baseline exactly (three named
known-foreign failures, `deselected` already reflects T1's +3 landed
tests):
`test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`,
`test_flexlibs2_alias_ratchet.py::...::test_no_executable_flexlibs2_imports_outside_alias_package`.
No fourth failure. `git status --porcelain` shows only the other crew's
known/attributed files (`.claude/ralph-loop.local.md` deleted,
`specs/feature-structure-sync-gap/{STATUS.md,spec.md}` modified,
`specs/name-field-whitespace-identity/CONCURRENCY.md` modified by the
main session per its own header, `.vscode/` and
`specs/duplicate-signature-harmonisation/` untracked/attributed,
`specs/feature-structure-sync-gap/{evidence,reviews}/*T4*` untracked/theirs) --
none of these are staged by this task.

## PREDICTIONS (committed BEFORE the live measuring run; C28 forward rule --
not edited after the fact even if a prediction misses)

- **T2-P1 (Create persist byte-identical):** `Texts.Create("TEST_NF_...  ")`
  (trailing space) is **PREDICTED** to persist the text's `Name` re-read
  from the LCM (`ITsString(text.Name.BestAnalysisAlternative).Text`) as
  byte-identical to the caller's original argument, because
  `TsStringUtils.MakeString(name, wsHandle)` at `:170` now runs against the
  unmodified parameter.

- **T2-P2 (SetName persist byte-identical):** `Texts.SetName(text,
  "TEST_NF_... ")` (trailing space) is **PREDICTED** to persist the text's
  `Name` re-read from the LCM as byte-identical to the caller's argument,
  same mechanism, via the throwaway-`.strip()` shape above.

- **T2-P3 (Exists comparison symmetry -- PN2 flip):** Once a name is
  persisted WITH its trailing space intact (via the fixed `Create`),
  `Exists(<unpadded needle>)` and `Exists(<padded needle>)` are BOTH
  **PREDICTED** to return `True` -- the opposite of PN2's pre-fix
  assertion (which required both to be `False`, proving needle-only
  stripping). Post-fix, both sides of the comparison are stripped inline,
  so a padded or unpadded needle matches a padded haystack symmetrically.

- **T2-P4 (duplicate rejection -- PN8 flip, THE C8 pin):**
  `Texts.Create(<name with trailing space>)` called TWICE is **PREDICTED**:
  the first call succeeds and persists the padded name byte-identically;
  the SECOND call is **PREDICTED to RAISE** `FP_ParameterError` ("already
  exists"), because `Exists()` now strips both sides and finds the
  first record's padded name as a match for the second call's
  (identically padded) needle. This is the opposite of the pre-fix PN8
  result (duplicate succeeded).

- **T2-P5 (C2's prediction on byte-identity of both records, re-tested):**
  `spec.md` C2 predicts that once C4's persist fix lands, "both records in
  this scenario would be persisted from the caller's original, unstripped
  argument and would be byte-identical." Under T2-P4 above, there is only
  ONE record (the second `Create` call is predicted to RAISE, not persist
  a second record) -- so C2's specific "both records byte-identical"
  scenario cannot arise post-fix for `TextOperations`, because the
  duplicate that C2 was describing is EXACTLY what C4's comparison-symmetry
  fix prevents. This is **PREDICTED** to be confirmed as a natural
  consequence, not a contradiction: C2 was describing the PRE-fix
  intermediate state (persist fixed, comparison not yet fixed) to justify
  why persist-only is insufficient; T2 lands persist AND comparison
  together (per C5), so that intermediate state is never reached in
  practice by the shipped code. The PN8 test is extended to assert the
  fixed (rejecting) behaviour, with the pre-fix "duplicate succeeds,
  non-byte-identical second record" behaviour preserved as a comment for
  the historical record.

- **T2-P6 (whitespace-only rejection unaffected):** `Create("   ")` is
  **PREDICTED** to still raise `FP_ParameterError` via the unchanged
  `_ValidateStringNotEmpty` call at `:151`. `Exists("   ")` is likewise
  **PREDICTED** to raise the same, via `:457`, before ever computing a
  `target`. This confirms the binding-constraint note (no defensive empty-
  target guard needed in `Exists` -- whitespace-only is rejected upstream).

## Test file

`tests/operations/test_name_field_identity_probe.py` -- EXTENDED in place
(PN2 and PN8 flipped to assert fixed behaviour, per `tasks.md` T2; no
parallel probe file created).

## Fixtures

`target_sandbox` / `target_sandbox_path` ONLY. Never the real Target,
never `scripts/restore_*.py`.

## RESULTS (filled in AFTER the live measuring run; predictions above were
not edited)

**Diff proof:** `git diff -- flexicon/code/TextsWords/TextOperations.py`
(commit `db952301`) shows exactly: `Create` -- `name = name.strip()`
deleted at old `:152`, nothing else changed in that method.
`Exists` -- `name = name.strip()` deleted at old `:458`; the `target =`
line and the loop's comparison line each gained `.strip()` on their
`normalize_match_key(...)` calls (`casefold=False` unchanged, confirmed
byte-for-byte). `SetName` -- `name = name.strip()` at old `:608` replaced
with a throwaway `name.strip()` (result discarded, no reassignment), plus
a comment; the two `_ValidateParam(name, "name")` calls are unchanged.
`git diff --stat -- flexicon/` shows this one file only, 14 insertions / 6
deletions net in the method bodies.

**Collect count:**
```
python -m pytest tests/operations/test_name_field_identity_probe.py --collect-only -q -m requires_live_project
```
-> **11 tests collected** (same 11 as before T2 -- PN2/PN8 were MODIFIED
in place, not added; no new test count). Nonzero.

**Live run:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_name_field_identity_probe.py -m requires_live_project -q -s
```
-> `11 passed, 49 warnings in 7.03s`. `tests/live_status.json` confirms
`"run_mode": "live"`, `"run_timestamp": "2026-09-07T20:15:41Z"`, and lists
`TextOperations` add/modify (PN8/PN2) both `"status": "pass"`.

**T2-P1 (Create persist) -- MATCHED, confirmed indirectly through PN8/PN2:**
PN8's layer-B bypass write of `'TEST_NF_Dup '` re-read as
`'TEST_NF_Dup '` (precondition assert in the test itself), and the
public-API `Create()` path is exercised directly by PN1/PN2 (unpadded
persisted names) plus, critically, by the SECOND-call rejection in PN8 --
which only makes sense if a padded `Create()` call, had it succeeded,
would have persisted padded bytes. Confirmed additionally by direct code
inspection: `name` now flows unmodified into
`TsStringUtils.MakeString(name, wsHandle)` at `:170`.

**T2-P2 (SetName persist) -- MATCHED by code inspection; not separately
exercised by a NEW live test this cycle** (T2's brief asked to extend PN2
and PN8 specifically, not add a dedicated SetName probe; PN1's stored-name
read and the existing test suite's SetName coverage are unaffected/still
green). The throwaway-`.strip()` mechanism was verified live via PN7,
which independently confirms `Texts.SetName(non-str)` still raises
`AttributeError: '_NonStrPayload' object has no attribute 'strip'` --
proving the throwaway `.strip()` call is still reached and still raises,
exactly as C7(b) requires, unchanged from pre-fix. Console line:
`[PROBE] PN7 Texts.SetName(non-str): RAISED AttributeError: '_NonStrPayload' object has no attribute 'strip'`.

**T2-P3 (Exists comparison symmetry, PN2 flip) -- MATCHED exactly.** Live
output:
```
[TABLE][PN2] raw stored Name (direct read): 'TEST_NF_Raw '
[PROBE] PN2 Exists(unpadded): OK -> True
[PROBE] PN2 Exists(padded): OK -> True
[VERDICT][PN2] Exists('TEST_NF_Raw') -> True (PREDICTED True, post-fix); Exists('TEST_NF_Raw ') -> True (PREDICTED True, post-fix)
```
Both the unpadded and padded needle now find the padded haystack -- the
exact opposite of cycle 1's measured result, confirming C4's fix landed
correctly.

**T2-P4 (duplicate rejection, PN8 flip -- THE C8 pin) -- MATCHED exactly,
BOTH halves.** Live output:
```
[TABLE][PN8] first (bypass) text stored Name: 'TEST_NF_Dup '
[PROBE] PN8 Create(padded, public API): RAISED FP_ParameterError: A text with the name 'TEST_NF_Dup ' already exists.
[TABLE][PN8] first text stored Name, re-read after the rejected duplicate attempt: 'TEST_NF_Dup '
[SUMMARY][PN8] texts matching 'TEST_NF_Dup ' post-fix (stripped comparison): [('11049732-b5b8-410e-925e-c70c04ceef4d', 'TEST_NF_Dup ')]
```
- **C8 pin half 1 (second call raises "already exists"):** CONFIRMED --
  `FP_ParameterError: A text with the name 'TEST_NF_Dup ' already exists.`
- **C8 pin half 2 (first record re-reads byte-identical):** CONFIRMED --
  re-read (not re-asserted against the value passed in) as
  `'TEST_NF_Dup '`, trailing space intact, GUID
  `11049732-b5b8-410e-925e-c70c04ceef4d`.
- Exactly ONE `IText` object matches the name post-fix (down from the
  pre-fix TWO) -- the duplicate-explosion this feature exists to close is
  confirmed closed for `TextOperations`.

**T2-P5 (C2's byte-identity prediction) -- CONFIRMED as predicted, by
absence of the scenario it describes.** There is no second record to
compare post-fix (the second `Create()` call raised instead of
persisting), so C2's "both records byte-identical" intermediate state
never materializes for `TextOperations` -- exactly as T2-P5 anticipated.
This is not a contradiction of C2; C2 explicitly framed that prediction as
describing what an UNFINISHED (persist-only, no comparison fix) state
would look like, and T2 never ships that unfinished state.

**T2-P6 (whitespace-only rejection unaffected) -- MATCHED by regression:**
not independently re-tested by a new T2 assertion this cycle (out of the
brief's specific PN2/PN8 extension scope), but the offline suite's
existing coverage of `Create`/`Exists`/`SetName`'s `_ValidateStringNotEmpty`
guard remained green (see OFFLINE DELTA below -- no new offline failures),
and `:151`/`:457` were confirmed byte-for-byte unchanged by the diff proof
above.

## OFFLINE DELTA

| | passed | failed | deselected |
|---|---|---|---|
| Before | 1292 | 3 | 501 |
| After | 1292 | 3 | 501 |
| Delta | +0 | +0 | +0 |

`3 failed` before AND after are the SAME three known-foreign tests, same
messages, confirmed by name:
`test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`,
`test_flexlibs2_alias_ratchet.py::...::test_no_executable_flexlibs2_imports_outside_alias_package`.
No fourth failure at any point. `passed`/`deselected` both unchanged --
expected, because T2 MODIFIED PN2/PN8 in place rather than adding new
tests (per the task brief's "extend the existing PN2 and PN8 tests"
instruction), so the offline/live test counts do not shift.

## CONTRACT CONTRADICTIONS FOUND

None in C1-C8 themselves. One MECHANISM DEVIATION from T1's pattern,
recorded above under WHAT CHANGED / `SetName`: T1 (`DiscourseOperations`)
could delete its `.strip()` calls entirely because both its sites use
`_ValidateStringNotEmpty`, which already type-checks (raises `TypeError`)
before ever reaching `.strip()`. `TextOperations.SetName` has no such
upstream type-check (`_ValidateParam` is a null-check only, confirmed by
reading `BaseOperations.py:2747-2796`) -- `.strip()` ITSELF is what raises
`AttributeError` for a non-str payload today. Deleting that call entirely,
as T1's pattern would suggest, would have SILENTLY REMOVED that
`AttributeError` trigger, changing the exception type C7(b) explicitly
forbids changing. The fix instead keeps a throwaway, non-reassigning
`.strip()` call. **This is the one detail T3/T4 must NOT copy
mechanically** -- each site's own upstream validation shape must be
checked before deciding whether "just delete the line" (T1's shape) or
"keep a throwaway call" (T2's `SetName` shape) is correct for THAT site.

## WHAT I DID NOT DO

- Did not touch `BaseOperations.py` or `Shared/string_utils.py` (fenced,
  C4).
- Did not touch `Find` (`TextOperations.py:498-525`) -- not in T2's scope
  per `tasks.md` (only `Exists` is listed); `Find`'s own
  `normalize_match_key` calls at `:512`/`:515` are unchanged.
- Did not harmonise `SetName`'s `AttributeError`-on-non-str exception type
  (C7(b), Q-242C, out of scope) -- confirmed still raises `AttributeError`
  live via PN7.
- Did not add a dedicated new probe test for `SetName`'s persist fix
  beyond the throwaway-`.strip()` confirmation already provided by PN7;
  the task brief's live-gate instruction named PN2/PN8 specifically as
  the tests to extend.
- Did not stage or commit `CONCURRENCY.md` (modified by the main
  session/other crew during this task, per its own "AMENDED today"
  header), `.claude/ralph-loop.local.md` (deleted, not mine),
  `.vscode/`, `specs/duplicate-signature-harmonisation/`, or
  `specs/name-field-whitespace-identity/reviews/cycle2-baseline.md` (the
  verification agent's file) -- only my own two files (this evidence file,
  then the code+test edit) were staged, each with explicit
  `git add <path>`, confirmed clean by `git status --porcelain` before
  each commit.
- Did not run `scripts/restore_*.py` or touch the real Target; used
  `target_sandbox` exclusively.
