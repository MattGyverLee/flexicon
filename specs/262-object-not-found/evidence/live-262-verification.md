# Live verification -- issue #262

**Project:** Target | **Fixture:** target_sandbox (tempdir copy of `tests/fixtures/Target 2026-07-06 0218.fwbackup`)
**Worktree:** C:\Github\flexicon-bugfix-loop  **Branch:** fix/262-object-stale-guid
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue262_object_stale_id_live.py -m requires_live_project -q
```
**run_mode:** live (confirmed via `tests/live_status.json` -> `"run_mode": "live"`, timestamp `2026-09-20T19:47:25Z`)
**Date:** 2026-09-20

## Claim under test
Commit `a2feff1` (plus two uncommitted QC fixes) changed `FLExProject.Object()` so a well-formed but stale Hvo/Guid raises `flexicon.code.exceptions.FP_ParameterError` (chaining the original CLR exception as `__cause__`) instead of leaking a raw CLR `System.Collections.Generic.KeyNotFoundException`. The same wrapping was applied at five other call sites in `GetCustomFieldValue()` and in `LexSenseOperations.SetPartOfSpeech()`.

## Result summary
7/7 tests passed. `pytest` output: `7 passed in 3.41s`. `tests/test_results.json` recorded 7 tests.

## Probe 1 -- stale id in all three input forms (load-bearing)
Created `TEST_262_stale_probe` (LexEntry), captured `Hvo=10442`, `Guid=6db1ed60-1827-45af-81e0-bc2dbbeb6c79`, then deleted it. Called `Object()` with the guid string, a `System.Guid`, and the int Hvo.

All three raised `FP_ParameterError` with `__cause__` present in every case, and the captured `__cause__` type was, in every case:

- **module:** `System.Collections.Generic`
- **name:** `KeyNotFoundException`
- **MRO:** `System.Collections.Generic.KeyNotFoundException -> System.SystemException -> System.Exception -> builtins.Exception -> builtins.BaseException -> builtins.object`

Guid-path CLR message: `Key 6db1ed60-1827-45af-81e0-bc2dbbeb6c79 not found in identity map (actually just an ID is present)` (via `IdentityMap.GetObjectOrSurrogate` -> `IdentityMap.GetObject(Guid)` -> `BackendProvider.GetObject(Guid)` -> `RepositoryBase.GetObject(Guid)` -> `StructureMapServiceLocator.GetObject(Guid)`).

Hvo-path CLR message: `Internal timing or data error [Unable to find hvo 10442 in the object dictionary. 10445 is the next available hvo]` (via `IdentityMap.GetObject(Int32)` -> `RepositoryBase.GetObject(Int32)`).

**This confirms the production except clause's dependency on `System.Collections.Generic.KeyNotFoundException` is correct against live LCM.**

## Probe 2 -- never-existed Hvo vs. genuinely-deleted Hvo (controlled A/B)
In a single test/session: created and deleted a LexEntry (Hvo=10442), then also probed a never-issued Hvo (999999999). Both raised `FP_ParameterError` with an identical `__cause__` type: `System.Collections.Generic.KeyNotFoundException` (same module and name in both cases). CLR messages differ only in the numeric Hvo value quoted, confirming the two failure modes are equivalent at the CLR-exception-type level that the fix's except clause keys on.

## Probe 3 -- edge inputs
- `Object(0)` -> `FP_ParameterError`, `__cause__` = `System.Collections.Generic.KeyNotFoundException` ("Unable to find hvo 0 in the object dictionary...").
- `Object(-1)` -> `FP_ParameterError`, `__cause__` = `System.Collections.Generic.KeyNotFoundException` ("Unable to find hvo -1 in the object dictionary...").
- `Object(System.Guid.NewGuid())` (foreign guid `fb1dc303-80f5-47e9-bed9-ba4575528bfd`) -> `FP_ParameterError`, `__cause__` = `System.Collections.Generic.KeyNotFoundException` ("Key fb1dc303-... not found in identity map...").

None of the three escaped as `ArgumentException`, `OverflowException`, or any other CLR/Python type -- each test's `except Exception` fallback (which would have converted an escape into a hard `AssertionError`) was never triggered.

## Probe 4 -- valid case round trip (unchanged)
Created `TEST_262_valid_roundtrip` (LexEntry). Read back from the LCM after creation:

| Field | Expected (captured at creation) | `Object(hvo)` re-query | `Object(System.Guid)` re-query | `Object(guid_str)` re-query |
|---|---|---|---|---|
| Hvo | 10442 | 10442 | 10442 | 10442 |
| Guid | 3de8f849-83e1-4e5a-9819-831758d5b906 | 3de8f849-83e1-4e5a-9819-831758d5b906 | (matched, hvo-equal) | (matched, hvo-equal) |
| ClassName | LexEntry | LexEntry | (asserted in-test) | (asserted in-test) |

All assertions were against values re-queried from the resolved object returned by `Object()`, not against the locally-held `created` variable. Object subsequently deleted in the test's `finally:` block.

## Probe 5 -- cascade-delete regression (`test_wfi_analysis.py` pattern)
Reproduced the exact `except Exception: leftover = None` pattern used by `TestWfiAnalysisCascadeDelete` against a genuinely deleted Hvo (10442, `TEST_262_cascade_probe`). Result:

- `caught_type` = `flexicon.code.exceptions.FP_ParameterError`
- `leftover` = `None`

Confirms `FP_ParameterError` (subclass of `FP_RuntimeError` -> `Exception`) is still caught by the pre-existing broad `except Exception:` in the cascade-delete test, and the "gone" signal (`leftover is None`) still fires correctly post-fix.

## Cleanup
All five test-created LexEntry objects (`TEST_262_stale_probe`, `TEST_262_ab_probe`, `TEST_262_valid_roundtrip`, `TEST_262_cascade_probe`, plus the one from probe 3 not needing an entry) were created and deleted inside `target_sandbox`, a fresh tempdir copy of the Target `.fwbackup` fixture that is discarded after the test session. No changes were made to the real Target project on disk.

## Per-probe pass/fail
| Probe | Test | Result |
|---|---|---|
| 1 (load-bearing) | `test_stale_guid_str_hvo_all_raise_fp_parameter_error` | PASS |
| 2 | `test_never_existed_and_deleted_hvo_raise_identical_clr_type` | PASS |
| 3a | `test_hvo_zero_raises_fp_parameter_error` | PASS |
| 3b | `test_negative_hvo_raises_fp_parameter_error` | PASS |
| 3c | `test_random_foreign_guid_raises_fp_parameter_error` | PASS |
| 4 | `test_object_by_hvo_and_guid_returns_same_correct_object` | PASS |
| 5 | `test_object_lookup_on_deleted_hvo_is_caught_by_broad_except` | PASS |

## Result
[PASS] -- Live LCM verification confirms the fix. Every stale/edge/foreign id form raises `FP_ParameterError` with `__cause__` of type `System.Collections.Generic.KeyNotFoundException` (never any other CLR type), the never-existed and genuinely-deleted cases are equivalent, the valid round-trip path is unchanged when re-queried from the LCM, and the pre-existing cascade-delete regression test's broad `except Exception:` pattern still behaves correctly under the new exception type.
