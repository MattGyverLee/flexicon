# Name-field whitespace identity -- T4B (CheckOperations Q-242B: distinct
silent-empty-name fix), live evidence

**Scope (per `tasks.md` T4 / `spec.md` C6, C7, C9, C10(b)):** the SAME three
sites and the SAME single commit as T4A (`evidence/live-t4a-check-q242a-fix.md`)
-- `CheckOperations.py:196` (`CreateCheckType`), `:341` (`FindCheckType`),
`:432` (`SetName`). Tracked here with SEPARATE evidence, severity, and
CHANGELOG entry per C6, because Q-242B is a materially more severe defect
(TOTAL payload loss corrected into a loud exception) than Q-242A's
comparison-symmetry/persist fix, even though both are fixed by the identical
edit.

**The fix (C7 exactly):** replaced
`name = name.strip() if isinstance(name, str) else ""` at all three line
numbers with a call to the already-shipped
`BaseOperations._ValidateStringNotEmpty` (`BaseOperations.py:3191`) --
CALLING it, not editing it, with NO reassignment of `name`. Kept the
existing leading `_ValidateParam(name, "name")` at each site (C7a) -- its
`None` check still fires first, so `_ValidateStringNotEmpty(None)`'s
`if text is None` branch (`BaseOperations.py:3239`) remains dead code,
recorded as an OBSERVATION ONLY per C7a, not fixed here. Deleted the
trailing `_ValidateParam(name, "name")` at each site once it became a
verbatim duplicate on the unmodified value (C11b).

**`_ValidateStringNotEmpty`'s body, read at HEAD (`BaseOperations.py:3191-3242`),
pinning the exact exception types:**
```python
if not isinstance(text, str):
    raise TypeError(f"{param_name} must be a string, got {type(text).__name__}")
if text is None:
    raise FP_NullParameterError()
if len(text.strip()) == 0:
    raise FP_ParameterError(f"{param_name} cannot be empty or contain only whitespace")
```
Non-str payload -> `TypeError`. Whitespace-only `str` -> `FP_ParameterError`.
Both pinned live below (PN19, PN20).

**Did NOT** harmonise the `AttributeError` sites elsewhere in the codebase
(`TextOperations.SetName`, `AnthropologyOperations.Create`/`CreateSubitem`)
-- that is Q-242C, explicitly out of scope (C7b).

**FindCheckType return-to-raise change (flagged, not hidden):**
`FindCheckType` is a READ-PATH method. Pre-fix, a non-`str` or
whitespace-only needle was silently coerced to `""`, matched nothing, and
`FindCheckType` returned `None` with no exception -- indistinguishable from
"not found." Post-fix, the same two inputs now RAISE (`TypeError` /
`FP_ParameterError` respectively) instead of returning `None`. This is a
genuine behaviour change on a method whose docstring says "Returns None if
not found (doesn't raise exception)" -- that docstring is now inaccurate for
these two input classes. T5's CHANGELOG must carry this explicitly; it is
NOT covered by simply describing the persist-side fix.

No shared file (`BaseOperations.py`, `Shared/string_utils.py`) touched --
`_ValidateStringNotEmpty` is CALLED, not edited or modified.

## OFFLINE BASELINE, BEFORE THE EDIT

Identical run and figures as `live-t4a-check-q242a-fix.md`'s OFFLINE
BASELINE section (same commit, same edit, same measurement instant):
`3 failed, 1292 passed, 505 deselected, 12 warnings in 13.46s`. See that
file for the full derivation note (stash-based re-measurement, since the
edit had already been made before this measurement was taken this cycle).

## PREDICTIONS (committed BEFORE the live measuring run; C28 forward rule --
not edited after the fact even if a prediction misses)

- **T4B-P1 (CreateCheckType non-str -- Q-242B pin, non-str branch):**
  `Checks.CreateCheckType(<a plain non-str object>)` is **PREDICTED** to
  RAISE `TypeError` (via `_ValidateStringNotEmpty`'s
  `if not isinstance(text, str)` branch), and NO check type is created --
  confirmed by comparing the check-type count before and after the raised
  attempt (PN5 flip; PN19 extends the same pin to all three sites in one
  test).

- **T4B-P2 (CreateCheckType whitespace-only -- lex-domain Q6 pin):**
  `Checks.CreateCheckType("   ")` is **PREDICTED** to RAISE
  `FP_ParameterError` (via `_ValidateStringNotEmpty`'s
  `if len(text.strip()) == 0` branch), and NO check type is created (PN6
  flip; PN20 extends the same pin to all three sites in one test).

- **T4B-P3 (FindCheckType return-to-raise, non-str):**
  `Checks.FindCheckType(<a plain non-str object>)` is **PREDICTED** to RAISE
  `TypeError` -- previously returned `None` with no exception. This is the
  behaviour-change half explicitly measured, not merely inferred from the
  shared code path (PN19).

- **T4B-P4 (FindCheckType return-to-raise, whitespace-only):**
  `Checks.FindCheckType("   ")` is **PREDICTED** to RAISE
  `FP_ParameterError` -- previously returned `None` with no exception (PN20).

- **T4B-P5 (SetName non-str and whitespace-only -- no partial mutation):**
  `Checks.SetName(check, <non-str payload>)` and
  `Checks.SetName(check, "   ")` are each **PREDICTED** to RAISE
  (`TypeError` / `FP_ParameterError` respectively) BEFORE any write reaches
  the LCM -- the seed check's `Name` is **PREDICTED** to re-read unchanged
  after each rejected `SetName` attempt (PN19, PN20).

## Test file

`tests/operations/test_name_field_identity_probe.py` -- SAME extension as
T4A (this is the same commit, same test file, tracked with separate
evidence per C6). PN5/PN6 flipped in place; PN19 (non-str, all three sites)
and PN20 (whitespace-only, all three sites) are this file's two dedicated
new tests. Collect count: **20 tests collected** (15 existing + 5 new,
identical figure to T4A -- same test file).

## Fixtures

`target_sandbox` / `target_sandbox_path` ONLY. Never the real Target, never
`scripts/restore_*.py`. `_seed_valid_check_list()` used throughout.

## RESULTS (filled in AFTER the live measuring run; predictions above were
not edited)

**Diff proof:** `git show --stat 0ab9c606` (same commit as T4A) --
`flexicon/code/System/CheckOperations.py` (13 changed lines) and
`tests/operations/test_name_field_identity_probe.py` (572 changed lines)
only.

**Collect count:** **20 tests collected** (same figure as T4A -- same test
file, same commit).

**Live run:** `20 passed, 72 warnings in 9.32s`. `tests/live_status.json`
confirms `"run_mode": "live"`, `"run_timestamp": "2026-09-07T21:05:56Z"`.

**T4B-P1 (CreateCheckType non-str) -- MATCHED exactly, PN5 (flip) and PN19:**
```
[PROBE] PN5 CreateCheckType(non-str): RAISED TypeError: name must be a string, got _NonStrPayload
[TABLE][PN5] check-type count before=0 after=0 (PREDICTED unchanged -- no silent persist on the raised path)
[PROBE] PN19 CreateCheckType(non-str): RAISED TypeError: name must be a string, got _NonStrPayload
```
No check type was created on either raised path -- confirmed by count.

**T4B-P2 (CreateCheckType whitespace-only) -- MATCHED exactly, PN6 (flip)
and PN20:**
```
[PROBE] PN6 CreateCheckType('   '): RAISED FP_ParameterError: name cannot be empty or contain only whitespace
[TABLE][PN6] check-type count before=0 after=0 (PREDICTED unchanged -- no silent persist on the raised path)
[PROBE] PN20 CreateCheckType('   '): RAISED FP_ParameterError: name cannot be empty or contain only whitespace
```

**T4B-P3 (FindCheckType return-to-raise, non-str) -- MATCHED exactly, PN19:**
```
[PROBE] PN19 FindCheckType(non-str): RAISED TypeError: name must be a string, got _NonStrPayload
```
Confirmed: pre-fix `FindCheckType(<non-str>)` returned `None` silently
(cycle-1 measurement, PN4's pre-fix design); post-fix it RAISES `TypeError`.
This is the RETURN-TO-RAISE change, measured directly and not merely
inferred.

**T4B-P4 (FindCheckType return-to-raise, whitespace-only) -- MATCHED
exactly, PN20:**
```
[PROBE] PN20 FindCheckType('   '): RAISED FP_ParameterError: name cannot be empty or contain only whitespace
```
Same return-to-raise change confirmed on the whitespace-only branch.

**T4B-P5 (SetName non-str / whitespace-only, no partial mutation) --
MATCHED exactly, PN19/PN20:**
```
[PROBE] PN19 SetName(non-str): RAISED TypeError: name must be a string, got _NonStrPayload
[TABLE][PN19] SetName seed's Name after rejected SetName(non-str): 'TEST_NF_Chk_SetName_NonStr_Seed'
[PROBE] PN20 SetName('   '): RAISED FP_ParameterError: name cannot be empty or contain only whitespace
[TABLE][PN20] SetName seed's Name after rejected SetName('   '): 'TEST_NF_Chk_SetName_WsOnly_Seed'
```
Both rejected `SetName` attempts raised BEFORE any write reached the LCM --
the seed check's `Name` re-read unchanged in both cases (genuine re-query,
not a re-assertion of the value set at seed time).

**Exact exception messages, pinned live (matches `_ValidateStringNotEmpty`'s
body read at HEAD):**
- Non-str: `TypeError: name must be a string, got _NonStrPayload`
- Whitespace-only: `FP_ParameterError: name cannot be empty or contain only whitespace`

## OFFLINE DELTA

Identical figures to `live-t4a-check-q242a-fix.md`'s OFFLINE DELTA section
(same commit, same run): `+0` passed, `+0` failed (same three known-foreign
tests, same messages, no fourth), `+5` deselected (PN16-PN20).

## CONTRACT CONTRADICTIONS FOUND

None in C1-C11. Same process deviation disclosed in T4A's evidence file
(code edit made before the offline baseline was recorded, corrected via
stash-based re-measurement) -- not repeated here to avoid duplication; see
`live-t4a-check-q242a-fix.md`'s CONTRACT CONTRADICTIONS FOUND section for
the full account. No contract item specific to Q-242B (C7, C9, C10(b)) was
contradicted.

## WHAT WAS NOT EXERCISED

None -- every pin half named for this file's Q-242B scope was exercised
live: `CreateCheckType` non-str (PN5, PN19) and whitespace-only (PN6, PN20)
both RAISE and persist nothing; `FindCheckType`'s return-to-raise change on
BOTH branches (PN19, PN20), measured directly rather than inferred from the
shared validator; `SetName`'s non-str and whitespace-only rejection with no
partial mutation (PN19, PN20). The dead `if text is None` branch inside
`_ValidateStringNotEmpty` (unreachable because the leading `_ValidateParam`
already excludes `None`) was confirmed by CODE INSPECTION ONLY, per C7a --
it is explicitly not exercisable through the public API (the leading guard
always fires first for a `None` payload), and fixing or removing it is
shared-code and out of this feature's scope.
