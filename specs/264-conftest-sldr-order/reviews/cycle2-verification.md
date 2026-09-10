# Verification Report -- issue #264 (conftest.py SLDR init order)

**Verdict:** [PASS]
**Live run:** yes | **run_mode:** live
**Evidence:** D:\Github\_Projects\_LEX\flexicon\specs\264-conftest-sldr-order\evidence\live-sldr-init.md
**Project:** Target (real, in-place) + target_sandbox (tempdir copy)

## Claim vs. observed
| Claim | Observed live | Status |
|-------|---------------|--------|
| Sole guarded `Sldr.Initialize` path in FLExInit.py is sufficient after removing conftest's second call | `Sldr.IsInitialized` read `True` pre- and post-cycle; `FLExInitialize()`/`FLExCleanup()` idempotence tests both passed live | [PASS] |
| No `.ldml.bad` quarantine files produced | `WritingSystemStore` on Target contains only `en.ldml`, `etu.ldml`, `idchangelog.xml` before and after the run | [PASS] |
| SLDR remains functional, not just flagged up | `LanguageTags.Count` = 9596 before forced cleanup/reinit cycle and 9596 after | [PASS] |
| Write-path (LexEntryOperations) still works under this SLDR init regime | Sandbox create/verify/delete round-trip passed, entry count restored | [PASS] |

## Commands run
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_target_live_smoke.py tests/operations/test_249_sldr_init_live.py -m requires_live_project -q
```
Result: 6 passed. `tests/live_status.json` -> `"run_mode": "live"`.

Note: task text named `tests/test_249_sldr_init_guard.py`, but that file's
own docstring/header states it is deliberately offline-only (CLR doubles,
no `requires_live_project` marker) and points to
`tests/operations/test_249_sldr_init_live.py` as its live counterpart --
confirmed by grep (guard file has no `requires_live_project` marker; the
live file does). Ran the live file instead, which actually exercises the
claim under a real `Sldr`/`SIL.WritingSystems`.

## Mock suite (regression, supplementary)
Not run this cycle -- live evidence above is the load-bearing artifact for
this task; mock suite was not requested and adds no evidence for an
init-path change of this kind.

## Blockers
none

## Recommendation
APPROVE
