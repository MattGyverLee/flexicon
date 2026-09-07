# Cycle 1 -- Programmer report: name-field whitespace identity live probe

**Status: measured, no refutation.** All 8 predictions' binding claims
matched (one non-binding sub-detail in PN8 missed, flagged in the
predictions before the run). One unplanned, unrelated bug discovered and
reported (not fixed).

## What was done

- New file `tests/operations/test_name_field_identity_probe.py` (8 live
  tests: PN1-PN8), self-contained, does not extend `test_issue242_*`.
- Predictions (PN1-PN8) committed to
  `specs/name-field-whitespace-identity/evidence/live-probe-cycle1.md` in
  commit `bdbce02`, BEFORE the test file existed or any live command ran
  (C28 forward rule).
- Line numbers from the background brief re-verified by direct `Read` of
  each file at HEAD -- all matched exactly, no drift.
- Live run: `tests/live_status.json` shows `"run_mode": "live"`. Command:
  `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest
  tests/operations/test_name_field_identity_probe.py -m
  requires_live_project -q -s`. Result: `8 passed`.
- Offline baseline: `1292 passed, 491 deselected` (unmarked suite) --
  `1292 passed` unchanged from the documented `ed428f7` baseline;
  `deselected` rose `483 -> 491`, exactly `+8` for the 8 new tests.
- Collect-only count: 8 (non-zero), pasted into the evidence file.

## Headline finding

The ruling's premise is **CONFIRMED, not refuted**. `Exists`/`Find` in
`TextOperations`, `AnthropologyOperations`, and `CheckOperations` all
strip the search needle only, never the stored haystack (PN2/PN3/PN4 all
matched). `Create()`'s own duplicate-collision guard inherits this same
blind spot: a layer-B-written text with a trailing-space name is
completely invisible to `Exists()`, so `Create()` happily mints a second
`IText` object a human would call by the same name (PN8's binding claim
matched -- exactly two texts found). Separately, `CreateCheckType` silently
converts both a non-str payload and a whitespace-only string into a
persisted empty name with **no exception** (Q-242B, PN5/PN6 both
matched), via the same `name = name.strip() if isinstance(name, str) else
""` + None-only `_ValidateParam` shape already flagged at `SetName`.

**One non-binding miss, flagged before measuring:** PN8's predicted
literal text "both named 'TEST_NF_Dup '" (byte-identical, with trailing
space) did not hold -- the second (public-API `Create()`-made) text's
stored name is `"TEST_NF_Dup"` (no trailing space), because `Create()`
persists its own already-stripped local `name`, not the caller's original
argument (`TextOperations.py:152`, reused at `:170-171`). The BINDING
claim -- `Create()` succeeds despite a pre-existing collision, yielding
two distinct objects -- is unaffected and matched exactly.

## Unplanned discovery (reported, not fixed)

`CheckOperations._GetCheckList()` (`CheckOperations.py:1168-1179`) is a
hardcoded stub that always `return None`s. This forces
`_GetOrCreateCheckList()` to always take its "create new list" branch,
which calls the nonexistent `ServiceLocator.GetInstance(...)`
(`:1198` -- should be `.GetService(...)`, as at every other call site in
the file). Net effect: `CreateCheckType()` raises `AttributeError` on
every call, for every payload, and appears to have never worked against a
live LCM. This is orthogonal to the name-field whitespace question and is
NOT fixed here (zero `flexicon/` lines touched); it was worked around at
the test-instance level only (`_seed_valid_check_list()` monkeypatches one
fixture instance's `_GetCheckList` to return a validly-built list, so the
broken `GetInstance` line is never reached and `CreateCheckType`'s own
name-handling logic -- the actual thing PN4/PN5/PN6 measure -- becomes
reachable). Full writeup in the evidence file.

## `git diff --stat -- flexicon/` -- not empty, but not this task's doing

This task made zero `Edit`/`Write` calls against any file under
`flexicon/`. At the end of the cycle, `git diff --stat -- flexicon/`
showed two modified files
(`flexicon/code/BaseOperations.py`,
`flexicon/code/Grammar/NaturalClassOperations.py`), caused by a
**concurrent, unrelated crew process** editing feature-structure-sync-gap
code in the same shared working directory during this task's own
wall-clock window (confirmed by file-content unrelatedness and mtime
overlap -- full evidence, including the exact diff and timestamps, is in
the evidence file). This task neither reverted nor committed those files,
since doing either would destroy another agent's in-progress work outside
this task's scope. Full detail, including the reasoning for not touching
those files, is documented in the evidence file's "git diff --stat --
flexicon/ proof" section.

## Files

- Test file (NEW): `tests/operations/test_name_field_identity_probe.py`
- Evidence: `specs/name-field-whitespace-identity/evidence/live-probe-cycle1.md`
- This report: `specs/name-field-whitespace-identity/reviews/cycle1-programmer.md`
