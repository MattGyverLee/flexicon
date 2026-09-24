# Issue #441 -- offline evidence

**Date:** 2026-09-24  
**Branch:** fix/441-headless-synchronize-invoke

## Command

```
python -m pytest tests/test_headless_lcm_ui.py -m "not requires_live_project" -q
```

## run_mode

Cloud agent: pytest unavailable or SIL.LCModel not loaded -- tests skip under mock mode unless FieldWorks pythonnet is present. Re-run on a Windows FW host for full module execution.

## Pre-state (main)

`HeadlessLcmUI.SynchronizeInvoke` returned `None`; LCM paths that call `SynchronizeInvokeExtensions.Invoke` NRE once a subscriber exists.

## Post-state (code inspection + tests when CLR available)

- `headless_ui.py` constructs `SingleThreadedSynchronizeInvoke()` in `__init__`.
- Tests assert non-null invoker, `InvokeRequired is False`, and `SynchronizeInvokeExtensions.Invoke` runs a delegate without NRE.

## Result

**PASS (offline gate)** when pytest + SIL.LCModel available; **SKIP/mock** on cloud agent without FW.

## Live LCM

**FAIL: unverified** -- HCParser + write repro requires FieldWorks + HC project (not on cloud agent).
