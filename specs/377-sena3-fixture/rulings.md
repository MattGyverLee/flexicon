# Issue #377 -- lex-lead ruling (sena3_sandbox fail-loud slice)

**Date:** 2026-09-24  
**Branch:** fix/377-sena3-require-live-parity from origin/main

## Triage (cron)

| Priority | Open bug without an open PR |
|----------|-----------------------------|
| P0 | none |
| P1 | none |
| P2 | none (each open P2 already has a cron PR) |
| **Selected** | **P3 #377** item 3 -- PhaseE / `sena3_sandbox` degrade path |

## RULING (binding)

`tests/flex_plugin.py` `sena3_sandbox` must use the same `_unavailable()`
gate as `target_sandbox` when `OpenProject` rejects the sandbox path.

Bare `pytest.skip()` on that path let `FLEXLIBS_REQUIRE_LIVE=1` sessions go
green while Phase E tests verified nothing -- the failure mode CLAUDE.md
documents for the live flag.

**Out of scope for this slice:** Sena 3 `stem_name` live proof, `ScrDraft.Create`
`type` application, adding a Sena 3 `.fwbackup` to this environment.

## Verification

- Offline AST ratchet: `tests/test_issue377_sena3_fixture_fail_loud.py`
- Offline gate: `python -m pytest tests/test_issue377_sena3_fixture_fail_loud.py -m "not requires_live_project" -q`
- Live: not required (test-infrastructure only; no LCM write path).
