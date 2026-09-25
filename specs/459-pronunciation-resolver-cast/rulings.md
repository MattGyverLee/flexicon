# Issue #459 -- lex-lead ruling

**Date:** 2026-09-24  
**Issue:** #459 (P2) -- PronunciationOperations HVO resolvers uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#459** (filed this run; promoted from #284)
- Did not select **#455** (open PR #456) or P3 **#284** (re-triage tracking)

## RULING (binding)

Cast both private resolvers through `cast_to_concrete` on every path:

- `__GetPronunciationObject` -- callers touch `ILexPronunciation` members
  (`Form`, `MediaFilesOS`, `LocationRA`, `Owner`, ~15 call sites).
- `__GetEntryObject` -- callers touch `ILexEntry` members (`PronunciationsOS`,
  create/list workflows).

Do **not** add a ClassName guard that returns uncast objects on miss; match
`WfiMorphBundleOperations.__GetBundleObject` (issue #268 family).

## Verification plan

- Offline: source ratchet + module existence check for live gate.
- Live: `target_sandbox` gate calling `GetForm(hvo)` with a genuine
  pronunciation HVO only (`requires_live_project`).
