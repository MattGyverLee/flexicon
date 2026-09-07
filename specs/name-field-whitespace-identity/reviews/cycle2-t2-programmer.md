# T2 -- TextOperations persist + comparison-symmetry fix -- programmer report (cycle 2)

## WHAT CHANGED

`flexicon/code/TextsWords/TextOperations.py`, three methods, three sites,
all line numbers re-confirmed against HEAD by symbol lookup before editing
(no drift from the task brief this cycle -- `Create:151-152`,
`Exists:457-464`, `SetName:606-609` all matched exactly):

- `Create` -- deleted `name = name.strip()` (old `:152`).
  `_ValidateStringNotEmpty(name, "text name")` (`:151`) unchanged.
  `TsStringUtils.MakeString(name, wsHandle)` (`:170`) now persists the
  caller's original argument.
- `Exists` -- deleted `name = name.strip()` (old `:458`). Both comparison
  sides now strip inline:
  `target = normalize_match_key(name, casefold=False).strip()` and
  `if normalize_match_key(text_name, casefold=False).strip() == target:`.
  `casefold=False` preserved unchanged, per instruction.
- `SetName` -- replaced `name = name.strip()` (old `:608`) with a
  **throwaway, non-reassigning** `name.strip()` call (result discarded).
  This is a deliberate, documented deviation from T1's "just delete the
  line" pattern -- see CONTRACT CONTRADICTIONS FOUND below.

No shared file (`BaseOperations.py`, `Shared/string_utils.py`) touched.
`Find` (`:498-525`, not listed in T2's scope) is untouched. `git diff
--stat -- flexicon/` shows this one file only.

`tests/operations/test_name_field_identity_probe.py`: PN2 and PN8
**modified in place** (no new tests, no parallel probe file) to assert
the fixed behaviour, with the pre-fix behaviour preserved verbatim in each
docstring for the historical record, per the `242-paragraph-whitespace`
T1 precedent.

## PREDICTIONS VS MEASURED

Predictions committed in `evidence/live-t2-text-fix.md` BEFORE the live
measuring run (commit `6ff3e5ec`), per the C28 forward rule; RESULTS
filled in after, in a second commit (`da580cdf`), unedited predictions.

- **T2-P1 (Create persist)** -- MATCHED (confirmed by code inspection plus
  indirect live confirmation via PN8's second-call rejection, which only
  makes sense if a padded `Create()` persists padded bytes).
- **T2-P2 (SetName persist)** -- MATCHED by code inspection; the
  throwaway-`.strip()` AttributeError-preservation mechanism was
  independently confirmed live via PN7 (`Texts.SetName(non-str)` still
  raises `AttributeError`, unchanged).
- **T2-P3 (Exists symmetry, PN2 flip)** -- MATCHED exactly. Live:
  `Exists('TEST_NF_Raw')` and `Exists('TEST_NF_Raw ')` both `-> True`.
- **T2-P4 (duplicate rejection, PN8 flip, THE C8 pin)** -- MATCHED exactly,
  both halves (see C8 PIN section below).
- **T2-P5 (C2's byte-identity prediction)** -- CONFIRMED by absence of the
  scenario: post-fix there is no second record to compare, so C2's
  "both records byte-identical" intermediate state never arises for
  `TextOperations` -- C2 was describing an unfinished (persist-only)
  state that T2 never ships.
- **T2-P6 (whitespace-only unaffected)** -- not independently re-tested
  by a new assertion (out of the brief's PN2/PN8-specific scope), but
  `:151`/`:457` confirmed byte-for-byte unchanged and the offline suite's
  existing coverage stayed green.

## C8 PIN BOTH HALVES

Live, from `tests/live_status.json` (`run_mode: live`,
`2026-09-07T20:15:41Z`) and console output:

1. `Texts.Create("TEST_NF_Dup ")` called a SECOND time (after a first,
   layer-B-written record with the same padded name) **RAISES**
   `FP_ParameterError: A text with the name 'TEST_NF_Dup ' already exists.`
2. The FIRST record's stored `Name` **re-reads BYTE-IDENTICAL** --
   `'TEST_NF_Dup '` (trailing space intact) -- re-read from the LCM after
   the rejected duplicate attempt, not merely re-asserted against the
   value passed in. Exactly ONE `IText` matches the name post-fix (down
   from TWO pre-fix).

Both halves CONFIRMED. Full transcript in
`evidence/live-t2-text-fix.md`'s RESULTS section.

## LIVE EVIDENCE

`specs/name-field-whitespace-identity/evidence/live-t2-text-fix.md`
(RESULTS section). Summary: collect count 11 (unchanged -- PN2/PN8
modified in place, not added), live run `11 passed`, `run_mode: live`.

## OFFLINE DELTA

Before: `3 failed, 1292 passed, 501 deselected, 0 errors`. After:
identical -- `3 failed, 1292 passed, 501 deselected, 0 errors`. Delta
`+0/+0/+0`, matching the DELTA rule exactly for a task that modifies
existing tests in place rather than adding new ones. Same three
known-foreign failures by name and message, matching
`CONCURRENCY.md`'s expected red baseline; no fourth failure at any point.

## CONTRACT CONTRADICTIONS FOUND

None in C1-C8 themselves. One **mechanism deviation from T1's pattern**,
flagged explicitly for T3/T4:

T1 (`DiscourseOperations`) deleted its `.strip()` rebindings entirely,
because both its sites (`CreateChart`, `SetChartName`) call
`_ValidateStringNotEmpty`, which already type-checks (raises `TypeError`
for non-str) BEFORE ever reaching `.strip()`. `TextOperations.SetName`
has **no** such upstream type-check -- it only calls `_ValidateParam`,
which is a null-check only (confirmed by reading
`BaseOperations.py:2747-2796`, docstring: "Lightweight null check", no
`isinstance` branch). At `SetName`, `.strip()` ITSELF is what raises
`AttributeError` for a non-str payload today (confirmed live via PN7,
both before and after this fix). Deleting that call entirely, copying
T1's shape mechanically, would have **silently removed** the
`AttributeError` trigger -- changing the exception TYPE that C7(b)
explicitly forbids changing (SetName's non-str behaviour belongs to
Q-242C, out of this feature's scope). The fix instead keeps a throwaway,
non-reassigning `name.strip()` call: still raises `AttributeError` for
non-str, no longer rebinds `name` for a valid str, so the persist writes
the caller's original bytes. This is recorded as a contract-adjacent
finding, not a contradiction of C4/C7 -- it's an implementation detail
C4/C7 didn't need to specify because they didn't anticipate two different
site shapes needing two different mechanisms to preserve the same outcome
(unchanged exception type).

## WHAT I DID NOT DO

- Did not touch `BaseOperations.py` or `Shared/string_utils.py` (fenced,
  C4).
- Did not touch `Find` (`TextOperations.py:498-525`) -- not listed in
  T2's scope; its own `normalize_match_key` calls are untouched.
- Did not harmonise `SetName`'s `AttributeError`-on-non-str exception type
  (C7(b), Q-242C, explicitly out of scope) -- confirmed still raises
  `AttributeError` live via PN7, unchanged.
- Did not add a dedicated new probe test for `SetName`'s persist fix
  beyond PN7's existing non-str confirmation; the task brief named PN2
  and PN8 specifically as the tests to extend.
- Did not create a parallel probe file; extended the existing one in
  place, consistent with T1 and the tasks.md instruction.
- Did not stage or commit `CONCURRENCY.md` (modified during this task by
  the main session/other crew, per its own header), the deleted
  `.claude/ralph-loop.local.md`, `.vscode/`,
  `specs/duplicate-signature-harmonisation/`, or
  `specs/name-field-whitespace-identity/reviews/cycle2-baseline.md` (the
  verification agent's file) -- only my own files were staged, each with
  explicit `git add <path>`, `git status --porcelain` checked clean
  before every commit.
- Did not run `scripts/restore_*.py` or touch the real Target; used
  `target_sandbox` exclusively.

## NOTES FOR T3 AND T4 COPYING THIS SHAPE

1. **Check each site's own upstream validation before choosing "delete
   the strip line" vs. "keep a throwaway strip call."** T1's shape (plain
   deletion) is only safe when the site's own validator (e.g.
   `_ValidateStringNotEmpty`) already type-checks before the `.strip()`
   line is ever reached. Any site whose only upstream guard is a
   null-check-only `_ValidateParam` (or nothing) needs the throwaway-call
   shape from this task's `SetName`, to avoid silently removing a
   pre-existing `AttributeError` and changing its exception type -- which
   C7(b) forbids for the three named sites
   (`TextOperations.SetName`, `AnthropologyOperations.Create`,
   `CreateSubitem`). **T3's two persist sites**
   (`AnthropologyOperations.Create:265`, `CreateSubitem:374`) are two of
   those exact three named C7(b) sites -- check whether their current
   validation shape is `_ValidateParam`-only (making them AttributeError-
   raising via `.strip()` today, per C7's own "3 AttributeError sites"
   table) before deciding which shape to use; do not assume T1's simpler
   deletion is safe there without checking.
2. **For the comparison-symmetry half**, the shape is identical for every
   family: drop the needle's `name = name.strip()` rebinding, then add
   `.strip()` inline at BOTH the `target =` line and the loop's/lookup's
   comparison line, keeping the existing `casefold=` argument unchanged.
   `_ValidateStringNotEmpty` upstream (where present) already rules out a
   whitespace-only `target == ""` collision -- no defensive empty-target
   guard is needed, and none was added here.
3. **The C8 pin's re-read must be a genuine re-read**, not a re-assertion
   of the value passed in -- PN8's `first_reread = ITsString(...)` line,
   executed AFTER the rejected duplicate `Create()` call, is the pattern
   to copy for T3's `AnthropologyOperations.Create` pin and T4's
   `CheckOperations.CreateCheckType` pin.
4. **Modify existing PN tests in place, do not duplicate them**, when the
   task brief names specific PN numbers to extend -- keep the pre-fix
   docstring content as a labeled historical-record paragraph inside the
   same test, rather than a separate skipped/archived test.
