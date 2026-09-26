# Issue #527 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #527 (P3) -- OverlayOperations / MorphRuleOperations GetAll untyped element  
**Branch:** `fix/527-overlay-getall-typing`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#528** (claimed by open PR #529)
- Selected **P3** without PR: **#527** (documentation / contract typing for FlexToolsMCP)

## RULING (binding)

1. **OverlayOperations.GetAll** must document `list[ICmOverlay]` in a `Returns:` section,
   matching other list-shaped list-module `GetAll` methods. Runtime shape is already
   `list(...)` from `OverlaysOC`; `@wrap_enumerable` is a no-op on lists.
2. **OverlayOperations.pyi** must stop claiming inheritance from
   `PossibilityItemOperations.GetAll (list[ICmPossibility])`; comment the true
   element type. Keep `List[Any]` in the stub (no `SIL.LCModel` import in `.pyi`).
3. **MorphRuleOperations.GetAll** docstring must name the post-decorator type:
   `EnumerableWrapper[CompoundRule | AffixTemplate]`, not bare `Generator[...]`.
4. **MorphRuleOperations.pyi** `GetAll` return type must be
   `EnumerableWrapper[Union[CompoundRule, AffixTemplate]]` using flexicon wrapper
   imports only.
5. Do **not** widen this PR to the eight other `List[Any]` stubs (issue optional
   follow-up).

**Out of scope:** Behaviour changes, live LCM verification (docs/stubs only).

## Verification plan

- Offline ratchet: `tests/operations/test_issue527_getall_typing_offline.py`
- `python -m pytest -m "not requires_live_project" tests/operations/test_issue527_getall_typing_offline.py -q`
