# Issue #506 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #506 (P2) -- `FindByHvo` false negative on bare `ICmObject` from `project.Object(hvo)`  
**Parent triage:** #275 / #269 resolver family; cron gap when #492–#505 each had open PRs

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** at pick time (#500/#502/#504 each had open PRs)
- Open **P3** bugs without an open PR: **none** (#494 had open PR #498)
- **Filed and selected #506** this run: `FindByHvo` in Discourse and Reversal still uses
  bare `isinstance` on `project.Object(hvo)` while `__ResolveObject` in the same modules
  already implements the ClassName cast path

## RULING (binding)

Route each `FindByHvo` through the module's existing `__ResolveObject` helper. Do not
duplicate cast logic. Preserve the public contract: return `None` when the HVO does not
refer to the expected type (catch `FP_ParameterError` and other resolution failures).

No change to `__ResolveObject` bodies in this slice unless a ratchet proves they regressed.

## Verification plan

- Offline: `tests/operations/test_issue506_findbyhvo_resolver_offline.py`
- Live: `tests/operations/test_issue506_findbyhvo_resolver_live.py`
  (`target_sandbox` or project with reversal/discourse data; genuine HVO ints only)
