# Issue #268 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** `fix/268-resolver-hvo-gate` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (each open P2 already has an
  in-flight cron PR #421--#427)
- Selected **P3 #268** (bug label, no open PR): shared-resolver live-coverage
  residue from #252 / T8

## RULING (binding)

Implement the **narrow close slice** from the issue body, not blanket coverage
of all 27 call sites:

1. Add **one HVO-entry live gate per resolver** at a **read-only public method**
   that was listed as having **zero** automated coverage:
   - `POSOperations.GetCatalogSourceId` (via `__ResolveObject`)
   - `AllomorphOperations.GetPhoneEnv` (via `__GetAllomorphObject`)
2. Each test must pass a **genuine Python `int` HVO** (assert
   `isinstance(hvo, int)` before the call), assert the bare
   `sandbox.Object(hvo)` view **lacks** the subtype-only member under test, and
   assert the public method succeeds without `AttributeError`.
3. **Out of scope for this PR:** AST allowlist expansion, the remaining five
   allomorph sites, POS write-path sites, or claiming full closure of #268.

**Rationale:** Loss of the ClassName cast fails silently through `hasattr`-gated
sync paths; the HVO entry axis was unmeasured at these read-only sites. One
gate per resolver matches cycle-17 `test_t8_hvo_path_gate.py` precedent.

## Verification plan

- Offline ratchet: `tests/operations/test_issue268_resolver_hvo_gate_offline.py`
- Live (required when FieldWorks available):
  `tests/operations/test_issue268_resolver_hvo_gate_live.py` with
  `FLEXLIBS_REQUIRE_LIVE=1`
- Evidence: `specs/268-shared-resolver-coverage/evidence/offline-268.md`
