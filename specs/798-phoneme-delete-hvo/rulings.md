# Issue #798 -- lex-lead ruling

**Date:** 2026-10-26  
**Issue:** #798 (P2) -- PhonemeOperations Delete PhonemesOC HVO membership  
**Parent triage:** HVO sweep / issue #796 NaturalClassOperations Delete sibling

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#798** filed this run (Phoneme Delete sibling gap after #796)

Untrusted open issues ignored per automation policy (e.g. #635 rulingAnts duplicate of #640).

## RULING (binding)

1. In `Delete`, locate the phoneme in `phoneme_set.PhonemesOC` by comparing each
   member's `Hvo` to the resolved phoneme's `Hvo`, not by passing the caller handle
   straight to `Remove`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #796 NaturalClassOperations Delete).
3. If no member matches, raise `FP_ParameterError`.
4. Tag the lookup with `issue #798` in comments.
5. Do not refactor unrelated PhonemeOperations paths in this PR.

**Out of scope:** Phoneme RemoveCode (#746), StratumOperations Delete, MorphRuleOperations
Delete, PhonFeatureOperations Delete unless separate issues are filed.

## Verification plan

- Offline: `tests/operations/test_issue798_phoneme_delete_hvo_offline.py`
- Live: `tests/operations/test_issue798_phoneme_delete_hvo_live.py`
- Evidence: `specs/798-phoneme-delete-hvo/evidence/`
