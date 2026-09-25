# Issue #465 -- lex-lead ruling

**Date:** 2026-09-24  
**Issue:** #465 (P2) -- SegmentOperations HVO resolvers uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#465** (filed this run; promoted from #284)
- Did not select **#455** / **#459** / **#461** / **#463** (each has an open PR) or P3 **#284** (re-triage tracking)

## RULING (binding)

Cast both private resolvers through `cast_to_concrete` on every path:

- `__GetSegmentObject` -- callers touch `ISegment` members (`AnalysesRS`,
  `BaselineText`, `FreeTranslation`, offsets, ~22 call sites).
- `__GetParagraphObject` -- callers touch `IStTxtPara.SegmentsOS` on
  paragraph HVO paths (`GetAll`, ordering helpers).

Do **not** change `__GetAnalysisObject` in this slice (Class B in the
#260 inventory: contract promises polymorphic `IAnalysis`; issue #212
fixed downstream consumers).

Do **not** add a ClassName guard that returns uncast objects on miss;
match `LexSenseOperations` (#457 family).

## Verification plan

- Offline: source ratchet + module existence check for live gate.
- Live: `target_sandbox` gate calling `GetAnalyses(hvo)` with a genuine
  segment HVO only (`requires_live_project`).
