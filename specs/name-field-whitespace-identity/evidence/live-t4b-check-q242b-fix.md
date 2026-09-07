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

_To be filled in after the live run below._

## OFFLINE DELTA

_To be filled in after the live run below._

## CONTRACT CONTRADICTIONS FOUND

_To be filled in after the live run below._

## WHAT WAS NOT EXERCISED

_To be filled in after the live run below (C10a mandatory section)._
