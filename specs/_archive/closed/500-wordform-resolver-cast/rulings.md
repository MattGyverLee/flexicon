# Issue #500 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #500 (P2) -- WordformOperations HVO resolver / isinstance false reject  
**Parent triage:** #275 / #269 resolver family (TextsWords gap)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#492** (fix on main; open PR #499 close-out), **none behavioural**
- Open **P3** bugs without an open PR: **#494** (open PR #498)
- **Filed and selected #500** this run: TextsWords `WordformOperations` inline HVO guards falsely reject every real wordform HVO

## RULING (binding)

Add `__ResolveWordform` and route every HVO entry path through it. Cast by
`ClassName == "WfiWordform"` through `cast_to_concrete` (registry maps to
`IWfiWordform`), matching the #275 widening pattern used on `TextOperations`
and the #457 / #481 `cast_to_concrete` family. Remove duplicated inline
`isinstance(obj, IWfiWordform)` blocks that false-negative on bare
`ICmObject` views from `project.Object(hvo)`.

## Verification plan

- Offline: `tests/operations/test_issue500_wordform_resolver_cast_offline.py`
- Live: `target_sandbox` gate calling `GetForm(wf.Hvo)` with precondition that
  `Form` is not reachable on bare `Object(hvo)` (`requires_live_project`).
