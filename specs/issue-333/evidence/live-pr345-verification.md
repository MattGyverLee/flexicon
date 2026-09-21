# Live verification: issue #333 HVO-int paths (PR 345 resolution)

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_333_live_verify_TMP.py -m requires_live_project -q -s
```

Worktree: `C:/Github/flexicon-pr345`, branch
`copilot/fix-icm-object-attribute-error` + resolution commits.
Throwaway test file deleted after the run (not part of the PR).

## run_mode

`tests/live_status.json` shows `"run_mode": "live"`,
`WfiMorphBundleOperations.read.status: pass`,
timestamp `2026-09-21T06:20:13Z`.

## Pre-state

`target_sandbox` (disposable tempdir copy of the Target `.fwbackup`):
wordform `TEST_333_bundle` -> analysis -> morph bundle (hvo 10444,
`ClassName=WfiMorphBundle`), MSA unset. Entry `TEST_333_entry` with
blank sense + stem MSA created via `MSA.CreateStem(sense, None)`
(hvo 10448).

## What the run proved

1. **PR 345 as-shipped did NOT fix the bug.** The resolver-side
   `cast_to_concrete()` call was a silent no-op: `lcm_casting`'s
   `_interface_cache` had no `WfiMorphBundle` entry, so the total
   function returned the bare `ICmObject` unchanged. First live run
   reproduced the exact reported failure on the fixed code:
   `AttributeError: 'ICmObject' object has no attribute 'MsaRA'`
   (`WfiMorphBundleOperations.py:1101`, `GetMSA`).
2. **After registering `WfiMorphBundle` / `WfiWordform` /
   `MoInflClass` in `_interface_cache`** (all three already in the
   LCM contract baseline -- no new type dependency), the rerun passed:
   - `GetMSA(hvo)` -> `None` on null-MSA bundle; correct MSA hvo
     after `SetMSA(bundle_hvo, msa_hvo)` (write verified by re-query,
     not echo).
   - `GetInflectionClass(hvo)` -> `None` (null MSA and linked stem
     MSA with no class set); no exception.
   - `GetInflType(hvo)`, `GetForm` not exercised via HVO here
     (covered: `GetInflType(hvo)` -> `None`).
   - `GetAll(analysis.Hvo)` == `GetAll(analysis)` (sibling
     `__GetAnalysisObject` resolver, 1 bundle).
   - `GetOwningAnalysis(hvo)`, `GetGuid(hvo)` match object paths.
   - `SetMSA(bundle_hvo, None)` clears; `GetMSA(bundle_hvo)`
     re-reads `None`.

## Post-state

Sandbox discarded on teardown (tempdir copy). Real Target and Sena 3
untouched. (Sena 3 in-place could not be used: its `.fwdata` needs a
restore -- `LcmInitializationException`, restore declined unattended.
No action taken on the user's project.)

## Pass/fail

**PASS** -- all HVO-int paths match object paths against live LCM,
`run_mode: live`.
