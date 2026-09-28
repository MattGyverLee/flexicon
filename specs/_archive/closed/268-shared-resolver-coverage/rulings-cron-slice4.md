# Issue #268 -- lex-lead ruling (cron slice 4)

**Date:** 2026-09-24  
**HEAD:** `fix/268-resolver-hvo-gate-slice4` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#441 fix merged; close-out PR #444
  is docs-only)
- Open **P2** bugs without an open PR: **none** (#231 has open PR #439)
- Selected **P3 #268** (bug label, no open PR; slices 1--3 on `main` via #435, #443,
  #445)

## RULING (binding)

Extend the HVO-entry live gate pattern to the **remaining write-path** call sites
that still had **zero** live HVO coverage per the issue inventory (POS:
`AddSubcategory`, `Duplicate`; allomorph: `SetMorphType`). `AddPhoneEnv` /
`RemovePhoneEnv` are already gated in `test_260_env_resolver_hvo_gate.py` (both-int
HVO path, cycle 2).

Add one live gate each at:

1. `POSOperations.AddSubcategory` -- parent passed as genuine `int` HVO; assert bare
   `SubPossibilitiesOS` is not on the base view; verify subcategory appears via
   `GetSubcategories(hvo)`.
2. `POSOperations.Duplicate` -- source passed as genuine `int` HVO; verify duplicate
   name round-trips via `GetName(dup_hvo)`.
3. `AllomorphOperations.SetMorphType` -- allomorph passed as genuine `int` HVO;
   assert bare view lacks `MorphTypeRA`; set morph type and re-read via fresh
   `GetMorphType(hvo)`.

Use `target_sandbox` only; prefix created objects `TEST_268_`; delete in `finally:`.

**Out of scope:** `RemoveSubcategory` (two resolve sites -- next slice),
`SetFormAudio`, AST allowlist, claiming full closure of #268.

## Verification plan

- Offline: `tests/operations/test_issue268_resolver_hvo_gate_offline.py`
- Live (FieldWorks): `tests/operations/test_issue268_resolver_hvo_gate_live.py`
  with `FLEXLIBS_REQUIRE_LIVE=1`
- Evidence: `specs/268-shared-resolver-coverage/evidence/offline-268-slice4.md`
