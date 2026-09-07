# T1 -- DiscourseOperations persist fix -- programmer report (cycle 2)

## WHAT CHANGED

`flexicon/code/TextsWords/DiscourseOperations.py`, exactly two lines
removed, nothing else:
- `CreateChart`: deleted `name = name.strip()` (old `:327`). The
  `_ValidateStringNotEmpty(name, "chart name")` call at `:320` is
  byte-for-byte unchanged. `name` now flows unmodified into
  `TsStringUtils.MakeString(name, wsHandle)` at the persist site.
- `SetChartName`: deleted `name = name.strip()` (old `:482`). The
  `_ValidateStringNotEmpty(name, "chart name")` call at `:481` is
  unchanged. Same persist mechanism.

No comparison/dedup method exists or was added on `DiscourseOperations`
(C3's per-family carve-out honoured). No shared file
(`BaseOperations.py`, `Shared/string_utils.py`) touched. Line numbers
were re-confirmed by symbol lookup immediately before editing and
matched the task brief exactly (no drift this cycle, unlike the earlier
CONCURRENCY.md warning about the other crew's line-shifting -- that
warning did not materialize for this specific file).

`git diff -- flexicon/code/TextsWords/DiscourseOperations.py` confirms
only these two deletions; `git diff --stat -- flexicon/` shows this one
file only.

`tests/operations/test_name_field_identity_probe.py` extended in place
(no parallel probe file) with three new live tests: PN9 (CreateChart --
see CONTRACT CONTRADICTIONS FOUND), PN10 (SetChartName, fully verified),
PN11 (whitespace-only regression guard).

## PREDICTIONS VS MEASURED

Predictions committed in `evidence/live-t1-discourse-fix.md` BEFORE the
live measuring run (commit `361feefe`), per the C28 forward rule.

- **T1-P1 (CreateChart persist byte-identical)** -- UNTESTABLE via the
  public API, for reasons unrelated to T1's own edit (see CONTRACT
  CONTRADICTIONS FOUND). Confirmed correct by code inspection only. Not
  a MISS of the prediction's mechanism -- the prediction assumed
  CreateChart could be reached at all, which turned out false for a
  cause independent of the edit under test.
- **T1-P2 (SetChartName persist byte-identical)** -- MATCHED exactly.
  Live re-read: `'TEST_NF_Chart_Renamed '` (trailing space intact).
- **T1-P3 (no dedup regression)** -- MATCHED (nothing added, nothing to
  test).
- **T1-P4 (whitespace-only still rejected)** -- MATCHED exactly. Live:
  `FP_ParameterError: chart name cannot be empty or contain only whitespace`.

## LIVE EVIDENCE

See `specs/name-field-whitespace-identity/evidence/live-t1-discourse-fix.md`
(RESULTS section) for full detail. Summary:
- Collect count: 11 (`--collect-only -m requires_live_project`).
- Live run: `11 passed`, `tests/live_status.json` shows
  `"run_mode": "live"`, timestamp `2026-09-07T20:06:17Z`.
- PN10 (SetChartName) is a genuine, complete live verification of one of
  T1's two edited call sites, through the real public API, with a
  post-write re-read from the LCM.
- PN9 (CreateChart) characterizes rather than confirms -- see below.

## OFFLINE DELTA

Before (stable baseline): `3 failed, 1292 passed, 498 deselected, 0 errors`.
After: `3 failed, 1292 passed, 501 deselected, 0 errors`. Same three
known-foreign failures by name and message, unchanged. `passed` +0
(expected -- no new offline tests). `deselected` +3 (expected -- exactly
PN9/PN10/PN11, all `requires_live_project`). Matches the DELTA rule
exactly.

**Transient noted, not chased:** the FIRST pre-edit offline run showed a
FOURTH failure (`test_natural_class_feature_sync.py::TestNaturalClassSyncStatic::test_apply_features_raises_on_unresolved_feature_guid`),
coinciding with `git status` showing `flexicon/code/BaseOperations.py`
as modified (the other crew's live in-progress edit per
`CONCURRENCY.md`). Isolated re-run of that one test passed; a second
full-suite re-run ~30s later, once their edit had settled (file clean
again in `git status`), matched the expected 3-failure baseline exactly.
Used the stable second run as the official "before" baseline rather than
hard-stopping on a self-clearing transient, consistent with
`CONCURRENCY.md`'s own framing of transients vs. legitimate red state.

## CONTRACT CONTRADICTIONS FOUND

None in C1-C8 themselves. Two NEW, UNPLANNED, PRE-EXISTING bugs were
discovered in `DiscourseOperations.CreateChart`, both **unrelated to
this feature's whitespace/identity question**, both **recorded, NOT
fixed** (out of T1's exact two-expression scope), both confirmed to
predate T1 by `git blame`:

1. **`IConstChartFactory` NameError** (`DiscourseOperations.py:335`,
   now-shifted from the original `:337` after this edit -- unaffected by
   T1's deletions). The module's import list was already corrected to
   `IDsConstChartFactory` (comment: "Fixed: was IConstChartFactory",
   commit `8716a5f2d`, 2025-11-26) but the usage site was never updated
   to match (introduced by `d0aac1a54`, 2026-06-23). `CreateChart()`
   raises `NameError` on every call, every payload. Worked around at the
   test-harness level only (module-namespace patch,
   `_patch_discourse_factory_bug()` in the probe file) -- zero
   `flexicon/` lines touched by the workaround.
2. **Wrong chart-ownership interface** (`DiscourseOperations.py:340`,
   `if hasattr(text_obj.ContentsOA, "ChartsOC")`). Confirmed by direct
   reflection on the live LCM assemblies: `IStText` (the type of
   `IText.ContentsOA`) has **no** `ChartsOC` member at all; the real
   owner is `IDsDiscourseData`, a project-level singleton reached via
   `LangProject.DiscourseDataOA`, unrelated to any individual
   `IText`/`IStText`. `CreateChart()`'s `hasattr` check therefore takes
   the `else` branch on every call, unconditionally, and raises
   `FP_ParameterError("Text contents does not support charts")` --
   independent of and deeper than bug 1. **Confirmed empirically that
   this cannot be worked around by a non-invasive test-harness patch**:
   a throwaway probe proved pythonnet regenerates a fresh Python wrapper
   on every `.ContentsOA` property access, so a Python-level attribute
   assigned to one wrapper (`text.ContentsOA.ChartsOC = stub`) is
   invisible the next time `CreateChart`'s own code re-accesses
   `text_obj.ContentsOA` internally. Reaching `CreateChart`'s persist
   line through its own, unmodified, real method body is therefore
   **not possible without editing `DiscourseOperations.py` beyond T1's
   authorised scope** -- so it was not attempted.

**Consequence for the anti-regression pin:** the persist half of C8 for
`CreateChart` specifically (T1-P1) is `FAIL: unverified` at the live
level, per CLAUDE.md's explicit instruction not to substitute a mock/
partial pass for a genuine block. T1's own edit is confirmed correct by
direct code inspection (the caller's `name` reaches
`TsStringUtils.MakeString` unmodified), and PN9 proves the padded and
unpadded inputs fail IDENTICALLY (ruling out T1's edit as the cause of
the block), but the persist-and-reread half of the pin could not be
independently exercised through `CreateChart`'s own public entry point.
`SetChartName` (T1's other site) WAS fully, honestly live-verified
(PN10), by constructing a chart through the LCM-correct ownership path
(`LangProject.DiscourseDataOA.ChartsOC`) instead of through the broken
`CreateChart`.

This is escalated here rather than silently smoothed over. Recommend a
future, separately-scoped task (not this feature, per `spec.md`
section 3's precedent for the analogous `CheckOperations._GetCheckList`
bug) to fix both `CreateChart` defects together, since fixing bug 1
alone would just expose bug 2 immediately, and fixing bug 2 requires
deciding a design question (should `DiscourseOperations` charts be
looked up via `LangProject.DiscourseDataOA` going forward, with
`BasedOnRA`/similar back-reference to the text?) that is out of scope
for a mechanical persist fix.

## WHAT I DID NOT DO

- Did not touch `BaseOperations.py` or `Shared/string_utils.py` (fenced,
  C4).
- Did not add a comparison/dedup method to `DiscourseOperations` (C3's
  carve-out).
- Did not fix either of the two newly-discovered `CreateChart` bugs
  (out of T1's exact two-expression scope; recorded above instead,
  per the `spec.md` section 3 precedent).
- Did not touch any file belonging to the other crew
  (`BaseOperations.py`, `NaturalClassOperations.py`,
  `PhonemeOperations.py`, `test_natural_class_feature_sync.py`,
  `specs/feature-structure-sync-gap/`, `specs/250-writingsystem-activation/`).
- Did not stage or commit `CONCURRENCY.md`'s modification, the untracked
  `.vscode/`, `specs/duplicate-signature-harmonisation/`, or the other
  crew's untracked spec/evidence files seen in `git status` during this
  task -- only my own two files (`evidence/live-t1-discourse-fix.md`,
  and the code + probe-file edits in the second commit) were staged,
  each with explicit `git add <path>`.
- Did not run `scripts/restore_*.py` or touch the real Target; used
  `target_sandbox` exclusively.
