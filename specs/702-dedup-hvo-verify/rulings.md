# Issue #702 -- lex-lead ruling

**Date:** 2026-10-24  
**Issue:** #702 (P2) -- merge dedup post-Remove verification HVO membership  
**Parent triage:** #690 RemovePicture `in` family; issue #291 dedup collapse

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#702** filed this run (dedup verify sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. After `.Remove(dupe)` in merge dedup helpers, verify absence by scanning the
   owning sequence for `member.Hvo == dupe.Hvo`, not `dupe not in sequence`.
2. Apply to:
   - `LexEntryOperations.__DeduplicatePronunciationsInEntry`
   - `LexEntryOperations.__DeduplicateAllomorphsInEntry`
   - `LexSenseOperations.__DeduplicateExamplesInSense`
3. Tag lookups with `issue #702` in comments.
4. Do not refactor unrelated dedup or merge paths in this PR.

**Out of scope:** Other `in` / `IndexOf` HVO sites (open issues #642–#700 family).

## Verification plan

- Offline: `tests/operations/test_issue702_dedup_hvo_verify_offline.py`
- Live: `tests/operations/test_issue702_dedup_hvo_verify_live.py`
- Evidence: `specs/702-dedup-hvo-verify/evidence/`
