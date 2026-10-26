# Issue #780 -- lex-lead ruling

**Date:** 2026-10-25  
**Issue:** #780 (P2) -- AgentOperations Delete HVO membership  
**Parent triage:** #772 OverlayOperations Delete OverlaysOC HVO (open PR)

## Triage (cron)

- Open **P0** bugs without an open PR (trusted authors only): **none**
- Open **P1** bugs without an open PR: **none** (#640 covered by open PR #641)
- Open **P2/P3** bugs without an open PR: **#780** filed this run (Agent Delete sibling gap)

Untrusted open issues (e.g. #635 from rulingAnts) ignored per automation policy.

## RULING (binding)

1. In `Delete`, locate the agent in `ILangProject.AnalyzingAgentsOC` by comparing each
   member's `Hvo` to the resolved agent's `Hvo`, not `agent in agents_oc`.
2. Call `Remove` on the collection member reference returned from the loop (same
   pattern as issue #772 Overlay Delete and #750 PossibilityItem Delete).
3. Tag the lookup with `issue #780` in comments.
4. Do not refactor unrelated AgentOperations paths in this PR.

**Out of scope:** Agent Duplicate (OC append has no insert_after HVO gap), WfiAnalysis
agent attach paths, PossibilityItemOperations base Delete.

## Verification plan

- Offline: `tests/operations/test_issue780_agent_delete_hvo_offline.py`
- Live: `tests/operations/test_issue780_agent_delete_hvo_live.py`
- Evidence: `specs/780-agent-delete-hvo/evidence/`
