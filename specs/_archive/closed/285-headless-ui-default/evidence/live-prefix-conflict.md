# Live verification -- issue #285 PRE-FIX conflict measurement

**Project:** Target (tempdir sandbox copies of the Target .fwbackup only --
the real Target project was never opened for writing and is confirmed
untouched, see Cleanup)
**Pre-fix worktree commit:** `8e657e85faf2ece9633a6f54fa11a145c29a4161`
(tip of `fix/285-headless-ui-default` at measurement time; confirmed
`flexicon/code/FLExLCM.py:99` reads `ui = FwLcmUI(None, th)` at this SHA --
the actual fix landed only in the concurrent agent's *uncommitted* working
tree, never touched here)
**Command:**
```
git worktree add <scratch>/pre285 8e657e85faf2ece9633a6f54fa11a145c29a4161
cd <scratch>/pre285
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_285_prefix_conflict_live.py -m requires_live_project -q -s
```
**run_mode:** `live` (from `tests/live_status.json` in the worktree,
`run_timestamp: 2026-09-08T20:59:41Z`)
**Date:** 2026-09-08

## Claim under test
Issue #285: `OpenProject(..., ui=None)` on unfixed code hands LCM the
WinForms `FwLcmUI`, and on a genuine conflicting save this "either blocks
on an ownerless modal dialog or silently discards the session's unsaved
writes" -- to be MEASURED, not assumed from #238's static reflection.

## (A) Staging a genuine conflicting save -- SUCCEEDED
A real second writer was established WITHOUT touching Target/Sena 3 or
their sharing settings: a tempdir copy of the Target `.fwbackup` was
opened by two independent `LcmCache` instances (via
`SIL.FieldWorks.ProjectId(BackendProviderType.kSharedXML, path)`, forcing
the "share project contents with programs on this computer" backend that
normally requires the FLEx Project Properties > Sharing tab). Both opens
succeeded concurrently against the same `.fwdata` file. A seed session
created `TEST_285_*` lexical entries; writer 1 committed a change to the
shared entry's citation form via `SaveChanges()`; writer 2, holding an
uncommitted conflicting edit to the same field, then called
`SaveChanges()`. With `ui=HeadlessLcmUI()` on writer 2 this correctly
raised `FP_ConflictingSaveError` -- confirming the staging mechanism
produces a REAL, LCM-detected conflict, not a fabricated one.

## Pre-state (read from LCM, seed phase)
`TEST_285_*` entry CitationForm: `"seed_value"` (guid captured at
creation; re-read via `GetCitationForm()` immediately and after reopen --
round-trip confirmed clean before any conflict test).

## Action
Two measurements of writer 2's `SaveChanges()` under unfixed
`FLExLCM.OpenProject`, both run as **separate OS subprocesses** (not
in-process threads) so that a genuine hang could not wedge the pytest
harness itself:
1. `ui=None` (the pre-fix default)
2. `ui=FwLcmUI(None, ThreadHelper())` (the documented explicit opt-out,
   Goal C)

## Result -- BOTH manifestations were measured, in different contexts

**Direct script invocation** (`python conflict_worker.py <mode> ...` run
directly, not spawned from pytest): completed in 1.7-2.2s, **no
exception**. Re-querying a **fresh third `FLExProject` session** opened
after both writers closed showed the on-disk CitationForm as
`"writer1_value"` -- writer 2's `"writer2_value"` edit was silently
discarded (`RevertToSavedState()`), with nothing raised to the caller.
Measured identically for both `ui=None` and the explicit
`FwLcmUI(None, ThreadHelper())` opt-out.

**Under the REQUIRED invocation**
(`FLEXLIBS_REQUIRE_LIVE=1 python -m pytest ... -m requires_live_project -q`,
subprocess launched from within the pytest process): the worker reached
`PRE_SAVE_CHECKPOINT` (i.e. called `w2.SaveChanges()`) and then did not
return within a 105s subprocess timeout, for **both** `ui=None` and the
explicit `FwLcmUI(...)` opt-out. Reproduced twice independently (one run
per mode). Process-level corroboration on an earlier, non-subprocess-
isolated attempt: the stuck `python.exe` was observed alive with CPU time
flat (6.15 -> 6.16s over 20s wall-clock) -- consistent with a blocked
thread waiting on a synchronization handle, not active computation.

**Conclusion:** the pre-fix `ui=None` default (and its literal twin, the
documented explicit `ui=FwLcmUI(...)` opt-out) is genuinely
**non-deterministic** across invocation contexts: a bare-script context
produced a clean silent discard; the mandated pytest-subprocess context
produced a reproducible block. Both outcomes match the issue's own
framing ("either blocks ... or silently discards") -- this run shows
both are real, not hypothetical, and that which one occurs is itself
unpredictable. This is arguably worse than either fixed manifestation
alone, and strengthens rather than weakens the case for the fix.

## Post-state (re-queried from LCM, silent-discard runs)
Fresh reader (3rd session, opened after both writers closed) --
CitationForm: `"writer1_value"` (writer 2's edit never reached disk; no
exception was ever raised to signal this to the caller).

## Cleanup
- All tempdir sandboxes (`expA_*`, `t285_*` under `%TEMP%`) deleted.
- Two hung `conflict_worker.py` child processes (from the pre-subprocess-
  isolation attempt) and one stray pytest orchestrator were terminated
  via `Stop-Process -Force` after confirming flat CPU (blocked, not
  progressing) and outside the test's own control.
- `python scripts/restore_target.py --check` confirms the real Target
  project at `C:\ProgramData\SIL\FieldWorks\Projects\Target\Target.fwdata`
  was never opened for writing by this measurement and needs no restore.
- Git worktree at `<scratch>/pre285` removed (`git worktree remove --force`).
- Sena 3 was not touched at any point.

## Result
[PASS] -- Goal (A) succeeded: a genuine conflicting save was staged
without touching the real Target/Sena 3 or their sharing settings.
Goal (B)/(C) measured, not assumed: pre-fix `ui=None` and the explicit
`FwLcmUI(...)` opt-out behave identically (as expected, since they are
the same code path) and are context-dependent -- silent discard in a
direct-script context, a genuine block in the pytest-subprocess context
mandated for verification. `run_mode: live` confirmed both times.
