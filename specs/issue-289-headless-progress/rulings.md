# /lex-lead ruling — issue #289 (cycle 1)

**Date:** 2026-09-23  
**Issue:** #289 (P1) — `OpenProject` constructs `ProgressDialogWithTask` on every open

## RULING

1. **Default progress** — Replace unconditional `ProgressDialogWithTask(th)` with
   `HeadlessThreadedProgress()`, a new `IThreadedProgress` implementation colocated
   with `HeadlessLcmUI` in `flexicon/code/headless_ui.py`. Model no-op members on
   FieldWorks' `NullThreadedProgress`; `RunTask` runs synchronously on the caller
   thread; `IsCanceling` / `Canceled` stay false unless LCM sets them via the
   writable `IsCanceling` property.

2. **`progress=` injection** — Add an optional keyword to `FLExLCM.OpenProject` and
   `FLExProject.OpenProject`, symmetrical with `ui=` (#285). Default remains
   headless; interactive hosts opt in with
   `ProgressDialogWithTask(ThreadHelper())`.

3. **Dispose** — When the progress object passed to `CreateCacheFromExistingData`
   is a `ProgressDialogWithTask`, dispose it in a `finally` block after open
   completes (issue defect 2). Do not dispose caller-owned
   `HeadlessThreadedProgress` instances unless they are the internally created
   default (dispose is a harmless no-op on the headless class).

4. **Export** — Export `HeadlessThreadedProgress` from the package top level (#271
   precedent).

5. **Pattern audit** — Single binding site (`FLExLCM.OpenProject`); no sibling
   sweep required beyond documenting that #289 closes the axis-2 finding recorded
   during #285 QC.

6. **Live verification** — Required on Windows with FieldWorks before merge to main;
   this cloud run records **FAIL: unverified** (no LCM on Linux).
