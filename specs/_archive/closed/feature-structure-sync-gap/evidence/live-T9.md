### Feature-Structure-Sync-Gap Verification Report (Cycle 2, Task T9)

**Command Run:**
```powershell
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_phoneme_feature_sync_issue253.py tests/operations/test_phoneme_feature_sync_issue253_flip.py -m requires_live_project -q
```

(The two-commit rollout split the T9 suite: the behaviorally-neutral half
(C2 cast, C6 presence gate, struct-GUID threading) ships with Commit A in
`test_phoneme_feature_sync_issue253.py`; the C7 flip contract and its live
raise path ship with Commit B in `test_phoneme_feature_sync_issue253_flip.py`.
The live invocation above runs both against the final flipped state.)

**Run Mode:** `live`

**Test Results:**
- `test_apply_valid_spec_preserves_struct_guid_and_specs` → PASS
- `test_unresolvable_feature_guid_raises_and_writes_nothing` → PASS

**Observation:** The tests verify two key state-preserving behaviors: (1) applying a valid feature spec preserves the original struct GUID across the apply operation, and (2) applying a malformed spec with an unknown GUID correctly raises an `FP_ParameterError` and leaves no partial state. Both assertions pass, confirming the fix properly maintains structural integrity and rejects invalid inputs.

**Post-state:** branch `main` at commit `b7002d96` (the flip commit); live run reports `tests/live_status.json` `"run_mode": "live"`, 2 passed, 9 deselected.