# Live verification -- T6 (`MSAOperations.GetSyncableProperties`/`ApplySyncableProperties`)

**Project:** `target_sandbox` (tempdir copy of the Target `.fwbackup` -- the
real Target is never opened).
**New test file:** `tests/operations/test_issue251_msa_feature_sync.py`,
Section D (`TestMSASyncLiveRoundTrip`, 6 tests, all `requires_live_project`,
all `@pytest.mark.live_phase("MSAOperations", "modify")`). Sections A-C of
the same file (21 tests) are offline (static source locks + fake-object
dispatch coverage) and are not part of this live run.

## [PREDICTION] -- recorded BEFORE the live run

1. `test_stem_msa_capture_apply_roundtrip`: a real `MoStemMsa.MsFeaturesOA`
   populated via `_ApplyFeatureStruc` on a source stem, captured through
   `GetSyncableProperties(bare_object)`, applied onto a second, freshly
   created stem via `ApplySyncableProperties`, then RE-READ from a fresh
   `sandbox.Object(hvo)` fetch. Expect `props["MsFeaturesGuid"]` truthy and
   `props["MsFeatures"]["specs"]` equal to `{featGuid: valGuid}` on both the
   source capture and the target re-read.
2. `test_infl_aff_msa_capture_apply_roundtrip`: same shape for
   `MoInflAffMsa.InflFeatsOA`. Expect
   `reread_props["InflFeats"]["specs"] == {featGuid: valGuid}`.
3. `test_deriv_aff_msa_both_slots_roundtrip`: a `MoDerivAffMsa` with BOTH
   `FromMsFeaturesOA` and `ToMsFeaturesOA` populated with independent
   feature/value pairs. Expect capture to emit both `FromMsFeatures`/
   `ToMsFeatures` key-pairs correctly, and the re-read after apply onto a
   fresh target `MoDerivAffMsa` to match both slots independently (proves
   the `slot="From"`/`"To"` disambiguation actually reaches two distinct
   LCM properties, not one).
4. `test_unclassified_affix_msa_capture_and_apply_do_not_raise`: a REAL
   `MoUnclassifiedAffixMsa` (not a fake). Expect `GetSyncableProperties`
   returns `{}` and `ApplySyncableProperties(unclass, {})` does not raise
   (R2, against a genuine LCM object this time, not a Python fake).
5. `test_apply_raises_on_unresolved_feature_guid`: a bogus, never-minted
   feature GUID passed through the PUBLIC `ApplySyncableProperties`
   surface (not `_ApplyFeatureStruc` directly -- that path is already
   covered live by T4's `test_apply_feature_struc.py`). Expect
   `FP_ParameterError` raised, message containing the literal bogus GUID
   (C7, exercised through OUR dispatch, confirming propagation is not
   swallowed anywhere in `MSAOperations.ApplySyncableProperties`).
6. `test_hvo_and_guid_entry_paths_capture_feature_keys`: the SAME stem
   resolved via `GetSyncableProperties(hvo_int)` and
   `GetSyncableProperties(guid_str)` (never the already-typed object).
   Expect both entry paths to capture identical, non-empty
   `MsFeatures.specs` (C2 -- `FLExProject.Object(hvo_or_guid)` returns a
   bare `ICmObject`; `__GetMsaObject` must cast before any subtype access
   is attempted downstream).

Expected offline-suite baseline (measured immediately before this commit,
same shell, `python -m pytest tests/operations tests/contract -m "not
requires_live_project" -p no:cacheprovider -q`): **392 passed, 2 failed
(the known-foreign `TestPhase2JoinOrOpen` pair), 510 deselected** -- +21
passed / +6 deselected relative to the pre-T6 baseline of 371 passed / 504
deselected, matching exactly the 21 offline + 6 live tests this task adds,
with zero other-count change.

## [RESULT] -- recorded AFTER the live run

### Command (exact)

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_issue251_msa_feature_sync.py -m requires_live_project -q
```
(An earlier attempt used PowerShell `$env:` syntax inside this session's
POSIX-sh Bash tool, which set no environment variable at all -- the tests
still passed on that attempt because `target_sandbox` does not itself
require the flag to run, only to fail loudly if unavailable, but it is
NOT the flag-set run counted as evidence. The command above, with `export`,
is the one whose `run_mode` was actually checked.)

Result: **6 passed, 21 deselected** (the 21 offline tests in Sections
A-C of the same file, correctly excluded by `-m requires_live_project`).

### run_mode

`tests/live_status.json` after this run:
```json
"run_mode": "live",
"run_timestamp": "2026-09-07T23:09:11Z"
```
All 6 tests appear under `by_test` with `"status": "pass"` and
`"operations_class": "MSAOperations"`, `"phase": "modify"` -- confirming
every live test in this file carries its `live_phase` marker (the cycle-7
telemetry-defect class: `uncategorized_live_tests` is `[]`).

### Predictions vs. actual (all 6 matched; no surprises)

1. **`test_stem_msa_capture_apply_roundtrip`** -- PASS as predicted.
   Source `MoStemMsa.MsFeaturesOA` populated via `_ApplyFeatureStruc`;
   `GetSyncableProperties(sandbox.Object(src_stem.Hvo))` returned
   `MsFeaturesGuid` truthy and `MsFeatures["specs"] ==
   {feat.Guid: value.Guid}`. Applied onto a second, independently-created
   stem via `ApplySyncableProperties`; RE-READ via a fresh
   `sandbox.Object(tgt_stem.Hvo)` -> `GetSyncableProperties` reproduced
   the identical `specs` dict. PRE-state: target's `MsFeaturesOA` was
   `None` before the apply (implicit -- `CreateStem` never populates it).
   POST-state (re-queried, not the value passed in): non-`None`, with the
   exact feature/value GUID pair.
2. **`test_infl_aff_msa_capture_apply_roundtrip`** -- PASS as predicted.
   Same shape for `MoInflAffMsa.InflFeatsOA`.
3. **`test_deriv_aff_msa_both_slots_roundtrip`** -- PASS as predicted.
   Both `FromMsFeaturesOA` and `ToMsFeaturesOA` populated with
   INDEPENDENT feature/value pairs on the source; capture emitted both
   `FromMsFeatures`/`ToMsFeatures` key-pairs; re-read after apply onto a
   fresh target `MoDerivAffMsa` matched both slots independently,
   confirming `slot="From"`/`"To"` reach two genuinely distinct LCM
   properties rather than one overwriting the other.
4. **`test_unclassified_affix_msa_capture_and_apply_do_not_raise`** --
   PASS as predicted, against a REAL `MoUnclassifiedAffixMsa` created via
   `CreateUnclassifiedAffix`. `GetSyncableProperties` returned `{}`;
   `ApplySyncableProperties(unclass, {})` raised nothing (R2 holds against
   genuine LCM data, not just the offline fakes).
5. **`test_apply_raises_on_unresolved_feature_guid`** -- PASS as
   predicted. `ApplySyncableProperties` (the public MSAOperations
   surface, not `_ApplyFeatureStruc` directly) raised `FP_ParameterError`
   whose message contained the literal bogus feature GUID
   (`00000000-0000-0000-0000-0000000000aa`) -- confirms C7 propagation is
   not swallowed anywhere in the new dispatch code.
6. **`test_hvo_and_guid_entry_paths_capture_feature_keys`** -- PASS as
   predicted. `GetSyncableProperties(stem.Hvo)` (int) and
   `GetSyncableProperties(str(stem.Guid))` (str) both captured the
   identical, non-empty `MsFeatures["specs"]` dict -- the C2 HVO/GUID
   entry path is cast correctly (via `_ResolveFeatureStrucOwner`'s own
   internal `ClassName`-driven cast, reached regardless of whether
   `__GetMsaObject`'s own eager cast fires first).

### Offline comparator (measured in the same shell, before vs. after this task's commits)

`python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q`

- Before (pre-T6, HEAD at task start): **371 passed, 2 failed
  (known-foreign `TestPhase2JoinOrOpen` pair), 504 deselected**.
- After (post all T6 commits, run twice for determinism): **392 passed, 2
  failed (same known-foreign pair, unchanged), 510 deselected** -- both
  runs identical.
- Delta: **+21 passed** (exactly the 21 new offline tests in Sections
  A-C), **+6 deselected** (exactly the 6 new live tests in Section D),
  **0 change** in the failed count or the known-foreign identity. No
  other test file's pass/fail status changed (R4 -- checked, nothing
  went red).

### Pass/fail line

**PASS.** `run_mode: live` confirmed; all 6 live tests green; all
predictions matched; offline comparator delta is exactly +21/+6/+0 as
expected; no existing test went red.
