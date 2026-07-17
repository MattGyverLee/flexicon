# Verification Report - Cycle 2

Date: 2026-07-17
Scope: Test-only regression coverage for issues #220 (yield/cast pattern +
ProjectSettings accessor delegation) and #217 (ApplySyncableProperties /
_apply_props_loop branch coverage + Category-8 type-shape locks).
Status: PASS (one Medium-severity portability risk noted, no blockers)

## Executive Summary

- Requirements met: 2/2 (both test files author their full stated coverage
  scope; no gaps found)
- Tests passing (non-live subset): yield_cast_pattern 17 passed / 2 skipped
  (0 failed); apply_syncable_properties 38 passed / 5 deselected (0 failed)
- Collection: both files collect cleanly, 0 import errors, 19 and 43 tests
  respectively
- Static source-lock assertions: all verified to match CURRENT production
  source, no drift found
- git status: only the two new test files + specs/ untracked, plus one
  unrelated pre-existing .claude/settings.local.json modification -- no
  production .py touched
- Portability risk: 9 Section-C tests in test_apply_syncable_properties.py
  import real flexicon.code.Lexicon.* modules at test-execution time
  (not collection time); on a machine without FieldWorks/SIL.LCModel these
  will ERROR at runtime, not skip cleanly. Severity: Medium (see Section 4
  below for full analysis).

Recommendation: APPROVE. Fix (or at least explicitly accept) the Section-C
portability risk before merge/CI rollout to non-FieldWorks runners.

---

## 1. Test Execution Results

### test_yield_cast_pattern.py (issue #220)

    python -m pytest tests/operations/test_yield_cast_pattern.py -q
    ......s.s..........                                                      [100%]
    17 passed, 2 skipped, 5 warnings in 8.09s

The 2 skips are the TestYieldCastLive / TestProjectSettingsAccessorsLive
tests gated on a live writable project fixture (expected -- no -m filter
was requested for this file per the task instructions).

--collect-only: 19 tests collected, 0 errors.

### test_apply_syncable_properties.py (issue #217, non-live subset)

    python -m pytest tests/operations/test_apply_syncable_properties.py -q -m "not requires_live_project"
    ......................................                                   [100%]
    38 passed, 5 deselected, 1 warning in 1.80s

5 deselected = the TestApplySyncablePropertiesLive round-trip tests
(correctly marked requires_live_project and excluded by the -m filter).

--collect-only: 43 tests collected, 0 errors (38 + 5 live = 43, consistent).

Both runs executed cleanly in the authoring environment, which has
FieldWorks/pythonnet installed -- see Section 4 for what happens on a
machine without it.
## 2. Static Source-Lock Verification (against current production source)

All assertions below were checked by reading the actual current production
files, not just trusting the test file's claims.

### #220 - Grammar/InflectionFeatureOperations.py

InflectionClassGetAll (line 152-183):

    for ic in infl_classes.PossibilitiesOS:
        yield IMoInflClass(ic)

Cast happens before the yield. Substring "IMoInflClass(ic)" present, exactly
once. Matches test expectation.

### #220 - Lexicon/SemanticDomainOperations.py - GetSubdomains

Lines 610-656. Contains "ICmSemanticDomain(" twice (non-recursive branch
line 646: [ICmSemanticDomain(child) for child in domain.SubPossibilitiesOS];
recursive walk() closure line 651: child = ICmSemanticDomain(raw)).
Recursive loop variable is named "raw", not "child" -- confirmed no
"for child in collection:" substring exists, and no
"return list(domain.SubPossibilitiesOS)" bare pass-through exists. Matches
test expectation (>=2 casts, both negatives absent).

### #220 - Notebook/LocationOperations.py - GetSublocations

Lines 1036-1083. Same shape as SemanticDomainOperations: "ICmLocation("
appears twice (line 1073 non-recursive comprehension, line 1078 recursive
walk() with loop var "raw"). No "for child in collection:", no
"return list(location.SubPossibilitiesOS)". Matches.

### #220 - System/ProjectSettingsOperations.py - 5 accessor aliases

| Method | Line | Delegate substring asserted | Found |
|---|---|---|---|
| GetProjectGuid | 863 | self.project.lp.Guid | Yes |
| GetProjectDescription | 888 | self.GetDescription | Yes |
| GetExternalLink | 907 | self.GetExtLinkRootDir | Yes |
| GetAnalysisWritingSystem | 922 | DefaultAnalysisWritingSystem | Yes |
| GetVernacularWritingSystem | 947 | DefaultVernacularWritingSystem | Yes |

All 5 delegation patterns confirmed present verbatim. Matches.
### #217 Section C - 7 _TYPE_CORRECTION_SITES

| Site | Module | Expected shape | Verified |
|---|---|---|---|
| EtymologyOperations.Source | EtymologyOperations.py:374 | multistring | item.Source.get_String(ws_def.Handle) loop, line 417 -- confirmed |
| LexSenseOperations.Source | LexSenseOperations.py:467 | tsstring | self._ReadTsString(item.Source) line 568 -- confirmed |
| LexSenseOperations.ScientificName | LexSenseOperations.py:467 | tsstring | self._ReadTsString(item.ScientificName) line 613 -- confirmed |
| LexSenseOperations.ImportResidue | LexSenseOperations.py:467 | tsstring | self._ReadTsString(item.ImportResidue) line 617 -- confirmed |
| LexEntryOperations.ImportResidue | LexEntryOperations.py:478 | tsstring | self._ReadTsString(item.ImportResidue) line 574 -- confirmed |
| ExampleOperations.Reference | ExampleOperations.py:364 | tsstring | self._ReadTsString(item.Reference) line 398 -- confirmed |
| PronunciationOperations.Form | PronunciationOperations.py:374 | multistring | item.Form.get_String(ws_def.Handle) loop, line 391 -- confirmed |

For each site, confirmed the wrong-shape substring is absent by inspecting
the full method bodies. All 7/7 match.

### #217 Section C - apply-side corrections

- ExampleOperations.ApplySyncableProperties (line 430-493): contains
  item.Reference = TsStringUtils.MakeString(ref_text, ws_handle) (line
  473). Confirmed.
- LexSenseOperations.ApplySyncableProperties (line 649+):
  _special_fields = ("SenseTypeRA", "DoNotPublishInRC", "DoNotShowMainEntryInRC")
  (line 678). None of Source, ScientificName, ImportResidue appear in this
  tuple. Confirmed.

No source drift detected anywhere in Section 2.
## 3. Git Status Check

    $ git status --short
     M .claude/settings.local.json
    ?? specs/issues-212-219/
    ?? tests/operations/test_apply_syncable_properties.py
    ?? tests/operations/test_yield_cast_pattern.py

Only the two new test files (plus the specs/issues-212-219/ planning
directory) are new. No production .py file was modified. Confirmed clean.

---

## 4. Portability Risk Assessment (Section C collection-time import)

Finding: The 9 tests call a helper, _method_source(import_path, class_name,
method_name), which does importlib.import_module(import_path) INSIDE the
test function body (line 555), not at module import / collection time.

However, the modules being imported all have module-level imports of the
form:

    from SIL.LCModel import (...)
    from SIL.LCModel.Core.KernelInterfaces import ITsString
    from SIL.LCModel.Core.Text import TsStringUtils

On a machine without FieldWorks installed but with pythonnet (clr) present,
this import will raise ModuleNotFoundError: No module named 'SIL' at test
execution time, not skip cleanly.

Severity: Medium.
Contrast with the file's own Section D (requires_live_project marker +
fixture-level pytest.skip()), which DOES skip cleanly by design -- Section C
has no equivalent guard.

Suggested fix (not applied, test-only scope per task): wrap the
importlib.import_module(...) call with pytest.importorskip("SIL.LCModel")
at the top of the two Section-C test classes, or catch ModuleNotFoundError
there and pytest.skip(...).

---

## Final Assessment

Overall Status: PASS

Blockers: None. Production code is untouched; both test files pass in full
in the authoring (FieldWorks-equipped) environment; all static source-lock
assertions are currently true against production source with no drift.

Non-blocking issue: Section C of test_apply_syncable_properties.py (9
tests) will error rather than skip on machines without a registered
FieldWorks/SIL.LCModel install. Recommend adding
pytest.importorskip("SIL.LCModel") to those two test classes before this
file is run in a non-FieldWorks CI lane.

Recommendation: APPROVE for merge as test-only regression coverage. Track
the Section-C portability guard as a small follow-up fix.

---
Verified By: Verification Agent
Date: 2026-07-17
