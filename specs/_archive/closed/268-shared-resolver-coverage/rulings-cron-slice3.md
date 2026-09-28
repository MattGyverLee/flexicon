# Issue #268 -- lex-lead ruling (cron slice 3)

**Date:** 2026-09-24  
**HEAD:** `fix/268-resolver-hvo-gate-slice3` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#231 has open PR #439)
- Selected **P3 #268** (bug label, no open PR; slices 1--2 on `main` via #435, #443)

## RULING (binding)

Continue the **narrow HVO-entry live gate** pattern. Add one live gate each at:

1. `AllomorphOperations.GetMorphType` (`MorphTypeRA` on resolved allomorph)
2. `POSOperations.GetSubcategories` (`SubPossibilitiesOS` on resolved POS)
3. `POSOperations.GetEntryCount` (uses `__ResolveObject`; must succeed via HVO
   and return `0` on a fresh POS with no entries)

Each test passes a **genuine Python `int` HVO**, asserts the bare
`sandbox.Object(hvo)` view **lacks** the subtype-only member where applicable,
and asserts the public method completes without `AttributeError`.

**Out of scope:** AST allowlist, write-path POS/allomorph mutators, full closure
of #268.

## Verification plan

- Offline: `tests/operations/test_issue268_resolver_hvo_gate_offline.py`
- Live (FieldWorks): `tests/operations/test_issue268_resolver_hvo_gate_live.py`
  with `FLEXLIBS_REQUIRE_LIVE=1`
- Evidence: `specs/268-shared-resolver-coverage/evidence/offline-268-slice3.md`
