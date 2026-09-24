# Issue #268 -- lex-lead ruling (cron slice 5)

**Date:** 2026-09-24  
**HEAD:** `fix/268-resolver-hvo-gate-slice5` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **none** (#448 → #451, #449 → #450)
- Open **P1** bugs without an open PR: **none** (labeled P1: none; #441 close-out → #444)
- Open **P2** bugs without an open PR: **none** (#231 → #439 merged, #447 open)
- Selected **P3 #268** (bug label; slice 4 merged via #446; no open PR for residue)

## RULING (binding)

Extend the HVO-entry live gate pattern to the **remaining write-path** resolver
sites called out at slice 4 close:

1. `POSOperations.RemoveSubcategory` -- **both** arguments as genuine `int` HVO
   (two `__ResolveObject` calls on one public method). Parent must lack
   `SubPossibilitiesOS` on the bare `ICmObject` view; subcategory must lack the
   same before removal. Verify removal via `GetSubcategories(parent_hvo)`.
2. `AllomorphOperations.SetFormAudio` -- allomorph as genuine `int` HVO; bare
   view must not expose `Form`. Skip cleanly when Target sandbox has no audio
   writing system (same contract as #272). Round-trip via `GetFormAudio(hvo)`.

Use `target_sandbox` only; prefix created objects `TEST_268_`; delete in `finally:`.

**Out of scope:** AST allowlist expansion, phone-env mutators (already gated in
#260 cycle 2), claiming full closure of #268.

## Verification plan

- Offline: `tests/operations/test_issue268_resolver_hvo_gate_offline.py`
- Live (FieldWorks): `tests/operations/test_issue268_resolver_hvo_gate_live.py`
  with `FLEXLIBS_REQUIRE_LIVE=1`
- Evidence: `specs/268-shared-resolver-coverage/evidence/offline-268-slice5.md`
