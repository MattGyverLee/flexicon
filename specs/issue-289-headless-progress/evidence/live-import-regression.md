# Live evidence: HeadlessThreadedProgress import regression + 24h PR re-verification

Date: 2026-09-23. Host: Windows 11, FieldWorks 9 (.NET Framework 4.8.9345.0), pythonnet 3.1.0.

## Defect

PR #375 (issue #289) made `HeadlessThreadedProgress` a Python subclass of
`SIL.LCModel.Utils.IThreadedProgress`. That interface inherits
`IProgress.Canceling` (a .NET event), and pythonnet 3.1 cannot emit event
members on a derived type (`Python.Runtime.dll` has no `DefineEvent` path).
The class statement raised at import time, so `import flexicon` failed:

```
TypeError: Method 'add_Canceling' in type 'Flexicon.Headless.HeadlessThreadedProgress'
from assembly 'Python.Runtime.Dynamic, ...' does not have an implementation.
```

The unit tests wrapped the import in `except Exception: pytest.skip(...)`, so
the suite went green while the package could not be imported.

Fix: compile the same no-UI implementation (shape of FieldWorks'
`NullThreadedProgress`) from C# in memory via CodeDom. `RunTask` now returns
the task's result (the interface returns `object`), not a success bool.

## Pre-state / post-state (read back from the LCM)

| | Pre (HEAD ec35efa) | Post (this change) |
|---|---|---|
| `import flexicon` | TypeError (above) | OK |
| `OpenProject("Target")` | unreachable | opened; `ProjectName()` = `Target` |
| `OpenProject("Sena 3")` read-only | n/a | opened; `LexiconNumberOfEntries()` = 1462 |
| Overlay `GetName(hvo)` | `'ICmObject' object has no attribute 'Name'` | returns created name |
| NaturalClass type-mismatch guard | `AttributeError` on `nc.Name` | raises `FP_ParameterError` |
| AnnotationDef fresh `Multi` (LCM) | `False`; GSP `AllowsMultiple` = `False`; test asserted `True` | test compares against LCM read-back |

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest <files> -m requires_live_project -q
```

One invocation per PR group. `tests/live_status.json` `run_mode` read after each.

## Results

| PR(s) | rc | run_mode | result | files |
|---|---|---|---|---|
| #355 | 0 | live | 3 passed in 27.12s | tests/operations/test_phonological_wrappers_live.py |
| #365-366 | 0 | live | 40 passed, 1 xfailed in 15.42s | tests/operations/test_325_reflection_live.py tests/operations/test_325_syncable_properties_live.py tests/operations/test_issue290_const_chart_reflection.py tests/operations/test_lexicon_brackets_live.py |
| #367 | 0 | live | 1 passed, 4 deselected in 3.29s | tests/test_pattern_writing_systems_enumeration.py |
| #369 | 1 | live | 1 failed, 1 deselected in 2.56s | tests/operations/test_issue356_text_media_helpers.py |
| #370 | 0 | live | 9 passed in 5.05s | tests/operations/test_variants_live.py |
| #371 | 0 | live | 1 passed, 3 deselected in 2.59s | tests/operations/test_issue324_clause_markers_cellsos.py |
| #372-378-384 | 0 | live | 4 passed, 6 deselected in 10.06s | tests/operations/test_overlay_operations.py |
| #374 | 0 | live | 3 passed in 2.66s | tests/operations/test_352_annodef_live.py |
| #375 | 0 | live | 3 passed, 11 deselected in 2.57s | tests/test_headless_threaded_progress.py tests/operations/test_target_live_smoke.py |
| #379 | 0 | live | 1 passed in 3.10s | tests/operations/test_issue350_agent_gsp_live.py |
| #380 | 0 | live | 1 passed in 3.24s | tests/operations/test_issue362_person_gsp_live.py |
| #381 | 0 | live | 1 passed in 3.24s | tests/operations/test_issue359_anthropology_gsp_live.py |
| #382 | 0 | live | 2 passed in 5.09s | tests/operations/test_issue363_confidence_live.py |
| #383 | 0 | live | 13 passed in 2.96s | tests/test_flexproject_discoverability.py |
| #385 | 0 | live | 21 passed in 2.86s | tests/operations/test_natural_classes.py |
| #386 | 0 | live | 4 passed, 4 deselected in 3.04s | tests/operations/test_277_environment_sequence_property.py tests/operations/test_issue301_unordered_getsequence.py |
| #387 | 0 | live | 1 passed, 1 deselected in 2.19s | tests/operations/test_issue329_datanotebook_ra.py |
| #388 | 0 | live | 1 passed in 2.40s | tests/operations/test_issue258_set_infl_aff_msa_slots_live.py |

## Still failing

- #369 `test_add_media_file_roundtrip_via_get_media_files`: `file_guid` is
  None. Live reflection shows `ICmMediaURI` has no `MediaFileRA` member (only
  `MediaURI`), so `AddMediaFile`'s `media_uri.MediaFileRA = cm_file` never
  reaches the LCM and GSP's `file_guid` can never be populated. Needs a
  sync-contract decision. FAIL.

Offline gate: `python -m pytest -m "not requires_live_project" -q`:
13 failed, 2203 passed. All 13 fail identically on HEAD + import fix only
(no regressions from this change).
