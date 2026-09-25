# Issue #476 -- lex-lead ruling (cron)

**Date:** 2026-09-25  
**Branch:** `fix/476-sysmodules-pollution` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **none** (#470–#473 have open PRs)
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#467 has PR #479; #455–#465 have PRs)
- Selected **P3 #476** (test hygiene: permanent `sys.modules` pollution)

## RULING (binding)

1. **Root cause** -- `_load_const_chart_clause_marker_ops` assigns fake stand-in
   modules with plain `sys.modules[name] = ...` while accepting `monkeypatch`
   but never using it. Pytest only restores entries registered via
   `monkeypatch.setitem(sys.modules, ...)`.
2. **Fix** -- Route every stand-in registration (including the dynamically
   loaded operations module) through `monkeypatch.setitem`. No production
   code change.
3. **Out of scope** -- Removing the stand-in load pattern entirely (larger
   refactor); reverting #448 workarounds in other tests unless they fail after
   this fix.

## Verification plan

- Offline:
  `python3 -m pytest tests/operations/test_issue357_clause_marker_getwordgroup_offline.py -m "not requires_live_project" -q`
- Regression spot-check (order-sensitive):
  `python3 -m pytest tests/operations/test_issue357_clause_marker_getwordgroup_offline.py tests/operations/test_lexentry_operations.py::TestLexEntryOperationsInheritance::test_inherits_from_base_operations -m "not requires_live_project" -q`
- Live: **N/A** (test-only change)
- Evidence: `specs/476-sysmodules-pollution/evidence/offline-476.md`
