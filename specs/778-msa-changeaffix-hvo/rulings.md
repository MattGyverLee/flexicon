# Issue #778 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #778 (P2) -- MSAOperations ChangeAffixVariant exception-feature RC HVO  
**Parent triage:** #770 Add/RemoveExceptionFeature (PR #771)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#640 has PR #641)
- Open **P2/P3** bugs without an open PR: **#778** filed this run (ChangeAffixVariant
  copy loop; out of scope in #770 ruling)

Untrusted open issues ignored per automation policy.

## RULING (binding)

1. In `ChangeAffixVariant`, when copying snapshot `from_features` into
   `new_msa.FromProdRestrictRC`, treat a feature as already present when any RC
   member's `Hvo` matches (do not use Python ``in``).
2. Tag the copy loop with `issue #778` in comments.
3. Do not refactor Add/RemoveExceptionFeature (#770) or unrelated MSA paths in
   this PR.

## Verification plan

- Offline: `tests/operations/test_issue778_msa_changeaffix_hvo_offline.py`
- Live: `tests/operations/test_issue778_msa_changeaffix_hvo_live.py`
- Evidence: `specs/778-msa-changeaffix-hvo/evidence/`
