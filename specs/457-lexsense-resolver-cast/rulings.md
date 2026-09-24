# Issue #457 -- lex-lead ruling

**Date:** 2026-09-24  
**Issue:** #457 (P2) -- LexSenseOperations HVO resolvers uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#457** (filed this run; promoted from #284)
- Did not select **#455** (open PR #456) or P3 **#284** (re-triage tracking)

## RULING (binding)

Cast all three private resolvers through `cast_to_concrete` on every path:

- `__GetSenseObject` -- callers touch `ILexSense` members (`Gloss`,
  `Definition`, `MorphSynAnalysis`, publication helpers, ~79 call sites).
- `__GetEntryObject` -- callers touch `ILexEntry` members when resolving
  entry HVOs from sense workflows.
- `__GetSemanticDomainObject` -- callers touch `ICmSemanticDomain` members
  on domain attach/detach paths.

Do **not** add a ClassName guard that returns uncast objects on miss; match
`WfiMorphBundleOperations.__GetBundleObject` (issue #268 family).

## Verification plan

- Offline: source ratchet + module existence check for live gate.
- Live: `target_sandbox` gate calling `GetGloss(hvo)` with a genuine sense
  HVO only (`requires_live_project`).
