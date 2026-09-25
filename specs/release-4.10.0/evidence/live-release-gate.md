# 4.10.0 release gate -- live verification evidence

**Date:** 2026-09-25
**Branch:** `release/4.10.0` (from `origin/main` @ `cacc34d`)
**Host:** Windows 11, FieldWorks 9.3.11.2703 (64 bit)

## Commands

```
python -m pytest -m "not requires_live_project" -q -p no:randomly
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest -m requires_live_project -q -rfEsx
```

## Results

| Run | Code | Result | `run_mode` |
|---|---|---|---|
| Offline, baseline | `origin/main` | collection ERROR (`test_issue321` ImportError, sys.modules pollution) | n/a |
| Offline, pollution contained | `origin/main` + test fixes | 162 failed / 2187 passed / 57 errors -> triaged | n/a |
| Live, baseline | `origin/main` + #468 test fix | **25 failed**, 944 passed, 38 skipped | `live` |
| Live, instrumented (cache misses logged) | same | 25 failed, 944 passed | `live` |
| Live, release candidate | this branch | 3 failed (MergeSegments identity asserts), 973 passed | `live` |
| **Live, final** | this branch | **976 passed, 0 failed**, 32 skipped, 2 xfailed, 1 xpassed | **`live`** |
| **Offline, final** | this branch | **2446 passed, 0 failed** | n/a |

The single xpass (`test_449_wrapper_write_paths_live.py`, affix-template
Delete) was a stale non-strict xfail for a bug #467 fixed; the marker was
removed and the test re-run live: `1 passed`.

## Read-back evidence for the live-only findings

- **cast_to_concrete registry.** Pre: `cast_to_concrete(project.Object(hvo))`
  on a Sena 3 `LexPronunciation` returned `ICmObject` (`hasattr(.., "Form")`
  False); debug log `ClassName 'LexPronunciation' is not in the interface
  cache`. Cache size 57. Cache misses over the full live suite (count):
  Segment 62, LexExampleSentence 44, FsClosedFeature 43, RnResearchNbk 21,
  LexPronunciation 17, PhCode 16, ScrBook 10, PhFeatureConstraint 4,
  ScrSection 3, CmPossibilityList 3, CmBaseAnnotation 2, ScrTxtPara 1,
  LexReference 1. Post: cache size 73; every HVO gate (#455 #457 #459 #465
  #486 #490 #492 #493) passes, reading the subtype member back from a fresh
  `project.Object(hvo)`.
- **ScrDraftType.** Live reflection: `System.Enum.GetNames(ScrDraftType)` ==
  `['SavedVersion', 'ImportedVersion']`. Pre: `test_352_scrdraft_live`
  failed `AttributeError: ... no attribute 'ConsultantCheck'`. Post: pass.
- **ITsString namespace.** `from SIL.LCModel import ITsString` -> ImportError;
  `SIL.LCModel.Core.KernelInterfaces.ITsString` -> OK. Post: new
  `test_issue265_makefeatstruc_names_live.py` 2 passed; MsFeaturesOA re-read
  from a fresh `IMoStemMsa(project.Object(hvo))` holds one `FsClosedValue`
  whose `ValueRA.Hvo` is the created value.
- **Annotation repository.** Pre: `GetService(ICmBaseAnnotation)` ->
  `ActivationException` (7 sync Note-duplicate tests + #323 live). Post:
  `ICmBaseAnnotationRepository`; all pass.
- **GetParentItem.** Pre: `GetParentItem(child)` -> None for a child created
  under a parent (#448 live). Post: parent returned; move-to-top-and-back
  re-reads parent and GUID from the LCM.
- **LexEntry.Duplicate deep.** Pre: `'IMoForm' object has no attribute
  'PhoneEnvRC'` (7 sync LexEntry-duplicate tests after project restore).
  Post: pass.
- **#231 premise.** Target sandbox: before `lexeme 10443, alts []`; after
  `AlternateFormsOS.Add(LexemeFormOA)`: `LexemeFormOA None, alts [10443]`
  (a move, not a duplicate). Gate skipped with this reason.
- **ICmMediaURI.** Reflected properties: `['MediaURI']` only -- `file_guid`
  can never be populated; #356 gate asserts the URI round-trip instead.

## Projects

Target and Sena 3 were restored with `scripts/restore_target.py` /
`scripts/restore_sena3.py` after an interrupted run (so no in-place test's
`finally:` cleanup was skipped silently). Destructive work used
`target_sandbox` / `sena3_sandbox` copies.

**Result: PASS (live).**
