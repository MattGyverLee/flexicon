# Issue #844 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/844-phonfeature-deletevalue-except from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs #833, #834, #836, #840, #842 each have open non-draft PRs (#837–#839, #841, #843).
- Open **P3** bugs without an open PR: **none**
- Selected **P2 #844** (new): `PhonFeatureOperations.DeleteValue` broad `except Exception: pass` swallows the `FP_ParameterError` raised when HVO membership fails -- sibling gap from #816 (HVO Remove landed; error path still fail-open).

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. Restrict the cast guard on `IFsClosedFeature(owner)` to invalid-owner failures only (`AttributeError`, `System.InvalidCastException`); do not wrap the HVO scan or `FP_ParameterError` in a bare `except Exception`.
2. When no `ValuesOC` slot matches the value HVO, raise `FP_ParameterError` with the existing message (issue #816 behaviour).
3. Tag the membership block with `issue #844` in comments where the control-flow change is visible.
4. Extend the #816 offline ratchet to assert `DeleteValue` does not use `except Exception:` (or equivalent swallow of the parameter error path).

**Out of scope:** `Delete()` and other PhonFeatureOperations methods; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue844_phonfeature_deletevalue_except_offline.py tests/operations/test_issue816_phonfeature_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue844_phonfeature_deletevalue_except_live.py -m requires_live_project -q` on `target_sandbox`.
