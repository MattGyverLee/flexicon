# Issue #441 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/441-headless-synchronize-invoke from origin/main

## RULING (binding)

**Problem:** `HeadlessLcmUI.SynchronizeInvoke` returned `None`. After HermitCrab
loads an `HCParser`, LCM registers a change listener and
`UnitOfWorkService.SendPropChangedNotifications` dereferences
`ISynchronizeInvoke` unguarded -- every write raises
`NullReferenceException` (#441).

**Fix (in scope for this PR):**

1. Construct one `SIL.LCModel.Utils.SingleThreadedSynchronizeInvoke` per
   `HeadlessLcmUI` instance in `__init__`.
2. Return it from `SynchronizeInvoke` / `get_SynchronizeInvoke`.
3. **Do not** switch the default back to `FwLcmUI` (#238 deadlock path stays
   closed). `SingleThreadedSynchronizeInvoke.InvokeRequired` is `False`, so
   LCM's `SynchronizeInvokeExtensions.Invoke` runs callbacks **inline** on the
   calling thread -- no WinForms pump, no cross-thread marshal.
4. Update unit tests: assert non-`None` invoker, `InvokeRequired is False`, and
   that `SynchronizeInvokeExtensions.Invoke` executes without NRE.
5. **Out of scope:** `HeadlessThreadedProgress.SynchronizeInvoke` (still
   `null` in compiled C#); parser/HCParser live repro (requires FieldWorks +
   HC project on Target/Sena).

## Verification plan

- Offline: `tests/test_headless_lcm_ui.py` (updated assertions + invoke smoke).
- Live: optional follow-up with `ParseWord` then a trivial write on Target when
  FW is available; not gating this PR on cloud agent (no LCM).
