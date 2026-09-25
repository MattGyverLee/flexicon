# Issue #492 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #492 (P2) -- PossibilityListOperations `__ResolveItem` / `__ResolveList` uncast  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#492**, **#493** (behavioural rows from #284 re-triage)
- Did not select **#493** this run (one slice per cron); **#492** ranked first in the behavioural list (`hasattr`-gated silent-loss on `__ResolveItem`)
- Did not select **#494** (P3 contract-only batch) or docs PR **#495** (not a fix PR)

## RULING (binding)

Cast both private resolvers through `cast_to_concrete` on every path:

- `__ResolveItem` -- callers read `Name` / `Abbreviation` / `Description`, use
  `SubPossibilitiesOS`, and gate on `hasattr(poss_item, "Description")` (silent
  loss when uncast).
- `__ResolveList` -- callers read `Name` and `PossibilitiesOS`.

On the HVO path, keep the **union** of `isinstance` and `ClassName` validation
(match #269 / `LexEntryOperations.__ResolveObject`); do not narrow to
ClassName-only.

Do **not** change contract-only helpers in this slice (#494).

## Verification plan

- Offline: `tests/operations/test_issue492_possibility_resolver_cast_offline.py`
- Live: `target_sandbox` gates calling `GetItemName(item_hvo)` and
  `GetListName(list_hvo)` with genuine HVOs only (`requires_live_project`).
