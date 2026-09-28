# Issue #268 -- lex-lead ruling (cron slice 2)

**Date:** 2026-09-24  
**HEAD:** `fix/268-resolver-hvo-gate-slice2` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (#441 is P1-caliber but has open PR #442)
- Open **P2** bugs without an open PR: **none** (#231 has open PR #439)
- Selected **P3 #268** (bug label, no open PR; slice 1 landed on `main` via #435)

## RULING (binding)

Continue the **narrow HVO-entry live gate** pattern from slice 1 and cycle-17
`test_t8_hvo_path_gate.py`. Add one live gate each at these **read-only**
public methods that the issue lists as having **zero** automated coverage and
that slice 1 did not cover:

1. `POSOperations.GetInflectionClasses` (`InflectionClassesOC` on resolved POS)
2. `POSOperations.GetAffixSlots` (`AffixSlotsOC` on resolved POS)
3. `AllomorphOperations.GetFormAudio` (`Form` on resolved allomorph via
   `__GetAllomorphObject`)

Each test must pass a **genuine Python `int` HVO**, assert the bare
`sandbox.Object(hvo)` view **lacks** the subtype-only member under test (or
`Form` for allomorph audio), and assert the public method completes without
`AttributeError`.

**Out of scope:** AST allowlist expansion, write-path POS sites, remaining
allomorph mutators (`SetFormAudio`, morph type, phone-env mutators), or
claiming full closure of #268.

## Verification plan

- Offline: extend `tests/operations/test_issue268_resolver_hvo_gate_offline.py`
- Live (when FieldWorks available):
  `tests/operations/test_issue268_resolver_hvo_gate_live.py` with
  `FLEXLIBS_REQUIRE_LIVE=1`
- Evidence: `specs/268-shared-resolver-coverage/evidence/offline-268-slice2.md`
