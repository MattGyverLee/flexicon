## Domain Review Report for T9 (Issue #253)

### Verdict: PASS

### Rationale

The change to `PhonemeOperations.__ApplyFeatures` from silently skipping unresolved GUIDs (`on_unresolved="skip"`) to raising `FP_ParameterError` (`on_unresolved="raise"`) is **correctly implemented** and **adequately covered** as a BREAKING change per the D1 ruling in `specs/feature-structure-sync-gap/spec.md`. 

1.  **Implementation matches spec (D1):**
    *   The documentation for `ApplySyncableProperties` in `PhonemeOperations.py` (lines 1443-1448) explicitly states this behavior change: "A feature spec RAISES `FP_ParameterError` when its feature or value GUID does not resolve in the target project (C7); a native data-fidelity loss is a loud error, matching `NaturalClassOperations`." This aligns with D1's decision that both operations should raise errors.
    *   The implementation of `__ApplyFeatures` (lines 1550-1595) uses `BaseOperations._ApplyFeatureStruc` and explicitly passes `on_unresolved="raise"` (line 1593), matching the behavior already implemented in `NaturalClassOperations.__ApplyFeatures` (lines 1282-1327) where `on_unresolved="raise"` is hardcoded.

2.  **Breaking change properly communicated:**
    *   The `CHANGELOG.md` under `[Unreleased]` has an entry for a **BREAKING (behavioural)** change for issue #253, following the precedent set by similar changes in 4.4.0, 4.6.0, etc.
    *   The D1 ruling specifies that this flip should be implemented as two commits:
        *   T4 (refactor): Extracted the common logic with `on_unresolved="skip"` for Phoneme and `"raise"` for NaturalClass (behaviour-preserving).
        *   T9 (policy flip): Phoneme default becomes `"raise"`.
    *   This is a **behavioral** change, which has already been committed on this branch.

3.  **Consistent with system behavior:**
    *   The `BaseOperations._ApplyFeatureStruc` method implements the policy correctly, where:
        *   If `on_unresolved="raise"` (default for Phoneme now), unresolved GUIDs raise `FP_ParameterError`.
        *   If `on_unresolved="skip"` (kept as an option), unresolved GUIDs skip without raising.
    *   The documentation and behavior are aligned to ensure that data loss is no longer silent—this closes issue #253.

4.  **No remaining silent-skip usages:**
    *   An audit of all callers (`grep` across the codebase) shows no direct use of `PhonemeOperations.ApplySyncableProperties` or `__ApplyFeatures` that would rely on old silent-skip semantics for GUID resolution errors.
    *   The `apply_sync.py` and related sync code correctly uses `GetSyncableProperties` followed by `ApplySyncableProperties` with proper error propagation.

This implementation aligns with the formal decision in D1 and is consistent with the documented behavior. The breaking change has been clearly communicated in the changelog, and no callers rely on silent handling.