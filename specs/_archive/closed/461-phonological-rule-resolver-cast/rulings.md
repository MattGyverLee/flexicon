# Issue #461 -- lex-lead ruling

**Date:** 2026-09-24  
**Issue:** #461 (P2) -- PhonologicalRuleOperations HVO resolver uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#461** (filed this run; promoted from #284)
- Did not select **#459** (open PR #460), **#455** (open PR #456), or P3 **#284** (re-triage tracking)

## RULING (binding)

Cast ``__ResolveObject`` through ``cast_to_concrete`` on every path after HVO
resolution and wrapper unwrapping:

- Int-HVO callers hit ``GetName`` / ``SetName`` / ``GetDescription`` and
  related accessors that read ``IPhPhonRule.Name`` and ``Description`` (~13 call
  sites).
- Preserve the existing wrapper peel (``_obj`` / ``_concrete`` duck-type) before
  casting so ``GetAll()`` round-trips stay identity-safe.
- Do **not** change ``__ResolveFeature`` or ``__ResolveLcmObject`` -- those are
  deliberately generic / identity-preserving per inventory row Class B.

Do **not** add a ClassName guard that returns uncast objects on miss; match
``WfiMorphBundleOperations.__GetBundleObject`` (issue #268 family).

## Verification plan

- Offline: source ratchet + module existence check for live gate.
- Live: ``target_sandbox`` gate calling ``GetName(hvo)`` with a genuine rule
  HVO only (`requires_live_project`).
