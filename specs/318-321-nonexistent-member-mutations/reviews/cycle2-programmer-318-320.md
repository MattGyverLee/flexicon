# Programmer Cycle 2 -- Issues #318 and #320

Implements the fixes decided in cycle-1 domain/author review. Scope limited
to #318 (dedup `OwningList`) and #320 (overlay elements) per assignment;
#319/#321 are being handled elsewhere (their in-flight files were left
untouched here).

## Issue #318 -- dedup never ran

**`flexicon/code/exceptions.py`** (+12 lines, after `FP_TransactionError`):
added `FP_DeduplicationError(FP_RuntimeError)`, verbatim per the Original
Author review's exact code block (verified `FP_RuntimeError` is the real
base class name in this file).

**`flexicon/code/FLExProject.py`**: added `FP_DeduplicationError` to the
`from .exceptions import (...)` re-export block (line 24-36), matching how
`FP_ParameterError`/`FP_TransactionError` are already re-exported and
imported downstream via `from ..FLExProject import (...)`.

**`flexicon/code/Lexicon/LexEntryOperations.py`**:
- Import block (~line 43): added `FP_DeduplicationError` alongside
  `FP_ParameterError`.
- `__DeduplicatePronunciationsInEntry` (~line 3102-3155) and
  `__DeduplicateAllomorphsInEntry` (~line 3157-3222): for both,
  - `dupe.OwningList.Remove(dupe)` -> `entry.PronunciationsOS.Remove(dupe)`
    / `entry.AlternateFormsOS.Remove(dupe)`.
  - Removed the outer catch-all `try/except Exception:
    logger.warning("Error during ... deduplication: ...")` that wrapped
    the whole method body (was at the old ~3146/3217 line numbers cited in
    the ticket).
  - Removed the inner per-dupe `try/except Exception:
    logger.warning("Could not remove duplicate ...")`. No genuinely benign
    LCM-side removal-failure exception class was identifiable, so per the
    Original Author's Q1 instruction ("if none exists, catch nothing and
    let the whole block raise"), there is now no inner catch at all --
    `AttributeError`/`TypeError`/anything else propagates immediately.
  - Track `found_count` (duplicates detected) separately from
    `removed_count`. Rather than trusting "the `.Remove()` call didn't
    raise" as proof of removal, `removed_count` only increments after
    re-checking `dupe not in entry.PronunciationsOS` -- this is what makes
    a *silent* (non-raising) removal failure detectable at all, and is
    what the "simulated removal failure" unit test exercises.
  - After the loop: `if found_count > 0: if removed_count < found_count:
    raise FP_DeduplicationError(...)` -- so "0 found" and "found but not
    all removed" can no longer collapse into the same silent return
    (issue #291's defect shape).
  - `removed_count`/`merged_count` are not plumbed out to any caller
    (Q3: `MergeObject()` documents no return value; not changed).

**`flexicon/code/Lexicon/LexSenseOperations.py`**: same shape for
`__DeduplicateExamplesInSense` (~line 3852-3892): import added, outer
catch-all and inner per-dupe catch removed, `dupe.OwningList.Remove(dupe)`
-> `sense.ExamplesOS.Remove(dupe)`, `found_count`/`merged_count` split with
a post-removal membership re-check, raises `FP_DeduplicationError` on
partial failure.

**Not done / decisions left as specified**: did not touch
`__DeduplicateSensesInEntry` (uses `sense_ops.MergeObject()`, not
`OwningList`, and was not named in the ticket's three sites) or anything
in `DataNotebookOperations.py`/`lcm_casting.py` (#319/#321, already being
edited by another agent per git status at start of this task).

## Issue #320 -- overlay elements

**`flexicon/code/Lists/OverlayOperations.py`** (`GetElements`/`AddElement`/
`RemoveElement`, ~line 283-370 pre-fix): rewrote all three against
`overlay.PossItemsRC`, deleting both dead `hasattr(overlay, "InstancesOS")`
/ `hasattr(overlay, "Elements")` branches entirely (not kept as
fallbacks), mirroring `GetPossItems`'s existing comment style and citing
the same live-reflection evidence file
(`specs/277-nonexistent-property-reads/evidence/live-277-overlays.md`).

`AddElement` also implements the team-lead-decided membership guard:
before adding, checks `getattr(element, "OwningList", None)` against
`overlay.PossListRA` (by `.Hvo`) and raises `FP_ParameterError` if the
element does not belong to the list the overlay is bound to, when
`overlay.PossListRA` is set. The check is a single clearly-labelled
"--- Membership guard ---" block, structured so it can be lifted in one
diff if the parallel live probe on FLEx's actual UI enforcement comes back
permissive (per the ticket's explicit ask). If `overlay.PossListRA` is
`None`, the guard is skipped (nothing to validate membership against).

## Exception-shape verification

Confirmed `FP_RuntimeError` (not e.g. `FP_BaseError`) is the actual base
class name in `exceptions.py` before adding `FP_DeduplicationError` under
it, matching house style (message built once, passed to `super().__init__`).

## CHANGELOG.md

Added two `### Fixed` entries under `[Unreleased]`, plus a `BREAKING
(behavioural)` callout blockquote directly under the `## [Unreleased]`
heading (mirroring the 4.8.0 preamble's phrasing and "minor bump per
4.4.0/4.6.0/4.7.0/4.8.0 precedent" framing):
- #318: states the defect, the fix, and the breaking behaviour change
  (`MergeObject(auto_deduplicate=True)` is the default, so the new
  exception can surface at call sites that never mentioned dedup;
  documents `auto_deduplicate=False` as the opt-out).
- #320: states the defect, the fix, and the new `AddElement` membership
  guard.

## Tests

New files (all pass locally, all unit-level -- no live project opened):

- `tests/operations/test_issue318_dedup_owninglist.py` (12 tests, all
  pass). Calls the real name-mangled private methods
  (`ops._LexEntryOperations__DeduplicatePronunciationsInEntry`, etc.) on
  real `LexEntryOperations`/`LexSenseOperations` instances with the shared
  `mock_flex_project` fixture -- not a reimplementation of the fix.
  Effect assertions: pre/post `PronunciationsOS`/`AlternateFormsOS`/
  `ExamplesOS` length, survivor identity by `.Hvo`. A dedicated test
  simulates a `.Remove()` that neither raises nor actually removes (the
  shape of a silent/benign LCM failure) and asserts `FP_DeduplicationError`
  is raised -- this is the assertion that catches the old
  `dupe.OwningList` no-op (which the 3 trailing source-ratchet tests also
  pin directly via `inspect.getsource`, checking `"dupe.OwningList.Remove"
  not in source`). A separate test confirms a genuine `AttributeError`
  from `.Remove()` propagates rather than being swallowed.
- `tests/operations/test_issue320_overlay_elements.py` (11 tests, all
  pass). Calls the real `OverlayOperations.GetElements/AddElement/
  RemoveElement` through a minimal mock `ICmOverlay`/`PossItemsRC`.
  Effect assertions re-read `PossItemsRC` membership fresh after each
  mutating call (not a stale handle). Includes the membership-guard raise
  test and a source-ratchet parametrized test pinning that
  `hasattr(overlay, "InstancesOS")`/`hasattr(overlay, "Elements")` do not
  reappear.
- `tests/operations/__init__.py`: added `__len__`/`__contains__` to the
  shared `MockOwningSequence` (it previously supported iteration but not
  `len()`/`in`, both of which the fixed dedup code now needs, and which
  the existing production code already relies on for real
  `ILcmOwningSequence` objects elsewhere, e.g.
  `PhonemeOperations.py:883`).

Ran:
```
python -m pytest tests/operations/test_issue318_dedup_owninglist.py tests/operations/test_issue320_overlay_elements.py -v
=> 23 passed
python -m pytest tests/operations/test_overlay_operations.py tests/operations/test_lexentry_operations.py tests/operations/test_lexsense_operations.py -m "not requires_live_project" -q
=> 44 passed
python -m pytest tests/ -m "not requires_live_project" -q
=> 2 failed, 1740 passed
```
The 2 failures (`test_issue266_phoneme_ws_resolution.py::...
test_fresh_index_cache_per_apply_call`, `test_issue267_translations_ws_
resolution.py::...test_fresh_index_cache_per_apply_call`) are pre-existing
and unrelated: they compare Python `id()` values across two calls and are
inherently flaky under CPython's object-id reuse, in files this task never
touched (phoneme/translation writing-system resolution, no relation to
dedup or overlays). Confirmed via `git status` that these files are not
part of this change set.

## Not done / open items

- No live-project (`requires_live_project`) tests were added for #318/#320
  -- the ticket only required unit-level tests with effect assertions,
  which are provided; live coverage can be added the way
  `test_overlay_operations.py::TestGetPossItemsLive` already does for
  `GetPossItems`, if QC wants it.
- Did not verify against a real FieldWorks/LCM 11 install (no live
  FieldWorks available in this environment) -- relied on the domain
  review's confirmed static-reflection evidence for `PronunciationsOS`/
  `AlternateFormsOS`/`ExamplesOS`/`PossItemsRC`/`PossListRA`.
