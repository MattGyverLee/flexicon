# Issue #770 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #770 (P2) -- MSAOperations Add/RemoveExceptionFeature RC HVO membership  
**Parent triage:** #630 affix exception features live coverage; RC HVO sibling gap

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has open PR #641)
- Open **P2/P3** bugs without an open PR: **#770** (filed this run; exception-feature RC paths)

Untrusted open issues ignored per automation policy (#635 from rulingAnts).

## RULING (binding)

1. In `AddExceptionFeature`, treat the feature as already present when any RC
   member's `Hvo` matches the resolved feature's `Hvo` (do not use Python ``in``).
2. In `RemoveExceptionFeature`, locate the RC member by `Hvo` and pass that
   member to `Remove`; absent member remains a no-op.
3. Tag lookups with `issue #770` in comments.
4. Do not refactor unrelated MSAOperations paths in this PR.

**Out of scope:** Other MSA RC mutators; `GetExceptionFeatures` read path.

## Verification plan

- Offline: `tests/operations/test_issue770_msa_exception_feature_hvo_offline.py`
- Live: `tests/operations/test_issue770_msa_exception_feature_hvo_live.py`
- Evidence: `specs/770-msa-exception-feature-hvo/evidence/`
