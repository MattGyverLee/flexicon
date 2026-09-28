# Issue #463 -- lex-lead ruling

**Date:** 2026-09-24  
**Issue:** #463 (P2) -- AllomorphOperations `__GetEntryObject` uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#463** (filed this run; promoted from #284)
- Did not select **#455** / **#459** / **#461** (each has an open PR) or P3 **#284** (re-triage tracking)

## RULING (binding)

Cast `__GetEntryObject` through `cast_to_concrete` on every path:

- HVO int entry resolves via `cast_to_concrete(self.project.Object(entry_or_hvo))`.
- Already-typed objects pass through `cast_to_concrete` as well (vacuous when concrete).

Do **not** return bare `self.project.Object(hvo)`; match `LexEntryOperations.__GetEntryObject` / #457 family.

## Verification plan

- Offline: source ratchet + live gate module existence check.
- Live: `target_sandbox` gate calling `Create(entry_hvo, form)` with a genuine entry HVO only (`requires_live_project`).
