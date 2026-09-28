# Live verification -- issue #334

**Project:** Target | **Fixture:** target_sandbox (tempdir copy; real Target untouched)
**Commands:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue334_guid_parse_formatexception_live.py -m requires_live_project -q
python -m pytest -m "not requires_live_project" tests/operations/test_issue334_guid_parse_formatexception.py -q
python -m pytest tests/operations/test_phon_features.py tests/operations/test_inflection_features.py tests/operations/test_semantic_domains.py tests/operations/test_apply_syncable_properties.py -m requires_live_project -q
```
**run_mode:** `live` (confirmed via `tests/live_status.json` before and after all runs)
**Date:** 2026-09-20

## Claim under test
Four unguarded `System.Guid(...)` parses (PhonFeatureOperations x2,
InflectionFeatureOperations x1, catalog_backed.py x1) now catch
`(System.FormatException, System.ArgumentNullException)` and raise
`FP_ParameterError` with the original CLR exception preserved as
`__cause__`, without breaking the well-formed-GUID path or marking the
undo stack for a raise that must happen before the transaction opens.

## Test results -- primary live file
`tests/operations/test_issue334_guid_parse_formatexception_live.py`
(target_sandbox, requires_live_project): **4 passed, 0 failed, 0 skipped**
(8.30s)

| Test | Result | Notes |
|---|---|---|
| `TestCatalogSourcedGuidRaisesFpParameterError::test_empty_catalog_guid_raises_fp_parameter_error` | PASS | `ops._create_from_entry` on a `CatalogEntry(guid="")` raised `FP_ParameterError`; `excinfo.value.__cause__` was a `System.FormatException`/`System.ArgumentNullException` instance (not None, correct CLR type); `entry.id` appeared in the message. Exercises `Shared/catalog_backed.py:479` directly (PhonFeatureOperations uses the mixin's `_create_from_entry` unmodified for feature-level creation). |
| `TestCatalogSourcedGuidRaisesFpParameterError::test_malformed_catalog_guid_does_not_mark_undo_stack` | PASS | **This assertion had never been run live before this task.** It held: `action_handler.CurrentDepth` and `action_handler.UndoableSequenceCount`, read from `target_sandbox.project.ActionHandlerAccessor`, were unchanged before vs. after the raise on a `CatalogEntry(guid="not-a-guid")`. Both members exist and behave as assumed on this LCM build -- `CurrentDepth` returned to its pre-call value (no leaked open transaction) and `UndoableSequenceCount` did not increment (no undo task pushed). This confirms the raise in `_create_from_entry` happens before `_TransactionCM` opens, as claimed. |
| `TestApplySyncablePropertiesMalformedGuid::test_malformed_value_guid_in_props_raises_fp_parameter_error` | PASS | A real `PhonFeatureOperations` feature (`TEST_334_shell_feature`) was created, then `ApplySyncableProperties` called with a `Values` entry carrying `"Guid": "not-a-guid"`. Raised `FP_ParameterError` with `__cause__` a `System.FormatException`/`System.ArgumentNullException` instance. Exercises `PhonFeatureOperations.py`'s `__CreateValueWithGuid` via its only public entry point. Feature deleted in `finally`. |
| `TestValidCatalogGuidStillImports::test_valid_catalog_guid_still_creates_feature` | PASS | Non-error regression guard. `ops.CreateFromCatalog("PHON:fPAConsonantal")` still succeeds. Post-state **read back from the LCM**: `target_sandbox.Object(feat.Guid)` re-fetched the object by GUID (not the in-memory `feat` reference) and its `.Guid` matched. A second `CreateFromCatalog` call for the same source_id returned the same GUID (pre-existing idempotency contract, unaffected). Feature removed from `feature_system.FeaturesOC` in `finally`. |

## Pre-state / Post-state (read from LCM) -- non-error path
- Pre-state: no `PhFeatureDefn` for source id `PHON:fPAConsonantal` existed under `feature_system.FeaturesOC` prior to the call in this sandbox session (fresh `CreateFromCatalog`).
- Action: `ops.CreateFromCatalog("PHON:fPAConsonantal")`.
- Post-state (re-queried, not the passed-in value): `target_sandbox.Object(feat.Guid)` returned a live object whose `str(Guid).lower()` equals `str(feat.Guid).lower()`; a repeat `CreateFromCatalog` call resolved to the identical GUID, confirming the feature is durably present in the LCM under its catalog GUID, not just held in the local Python variable.

## Undo-stack assertion -- explicit finding
The docstring in the test file flagged this as never-run-live and
instructed dropping it if the LCM members didn't exist or didn't mean
what was assumed. Result: `ActionHandlerAccessor.CurrentDepth` and
`ActionHandlerAccessor.UndoableSequenceCount` both exist on this LCM
build (FieldWorks 9, Target project) and behaved exactly as assumed --
unchanged across a raise that occurs before `_TransactionCM` opens. No
change to the test was needed; the assertion holds as written.

## Mock suite (regression, supplementary)
`python -m pytest -m "not requires_live_project" tests/operations/test_issue334_guid_parse_formatexception.py -q`
Result: **26 passed**, 0 failed.

## Related live suites (regression check on affected modules)
`python -m pytest tests/operations/test_phon_features.py tests/operations/test_inflection_features.py tests/operations/test_semantic_domains.py tests/operations/test_apply_syncable_properties.py -m requires_live_project -q`
Result: **47 passed, 1 skipped** (skip pre-existing/unrelated), 38 deselected (non-live tests in same files). `run_mode: live` confirmed both before and after.

## Cleanup
All live tests use `target_sandbox` (a tempdir copy of the Target
`.fwbackup`); nothing was written to the real Target. Objects created
inside the sandbox (`TEST_334_shell_feature`, the `PHON:fPAConsonantal`
catalog feature) were deleted/removed within each test's `finally` block.
`python scripts/restore_target.py --check` after all runs confirms the
real Target project is unaffected (present, untouched).

## Result
[PASS] -- All four #334 fix sites verified live against a real (sandboxed)
FieldWorks LCM: malformed GUIDs from both catalog data and caller-supplied
props now raise `FP_ParameterError` with the CLR exception preserved as
`__cause__`; the well-formed-GUID path is unbroken (confirmed by re-query,
not by echoing the input); and the never-before-run undo-stack assertion
held live, confirming the raise happens before the transaction opens for
the catalog-sourced sites.
