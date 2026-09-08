# Verification Report -- issue #285 PRE-FIX conflict measurement

**Verdict:** PASS (Goal A) / MEASURED, not assumed (Goals B/C) -- see notes
**Live run:** yes | **run_mode:** live
**Evidence:** specs/285-headless-ui-default/evidence/live-prefix-conflict.md
**Project:** Target (tempdir sandbox copies only; real Target/Sena 3
untouched, confirmed via `restore_target.py --check` after the run)

## Pre-fix worktree
Isolated via `git worktree add <scratch>/pre285 8e657e85faf2ece9633a6f54fa11a145c29a4161`.
`8e657e8` is the branch tip at task start; confirmed `flexicon/code/FLExLCM.py:99`
still reads `ui = FwLcmUI(None, th)` there. The actual fix (`ui = HeadlessLcmUI()`)
existed only in the concurrent agent's *uncommitted* working tree at that
moment -- never read or measured here.

## Claim vs. observed
| Claim | Observed live | Status |
|-------|---------------|--------|
| A genuine conflicting save needs `projectSharing` + a real second writer; `target_sandbox` alone can't produce one | Staged via two `LcmCache` instances forcing `BackendProviderType.kSharedXML` on a tempdir copy of Target's `.fwbackup`. Both opened concurrently; a real `FP_ConflictingSaveError` fired under `HeadlessLcmUI()`, confirming the mechanism is genuine | PASS |
| Pre-fix `ui=None` conflicting save is either a block or a silent discard (#238 predicted this from static reflection, not measurement) | Measured **both**, in different invocation contexts: a bare-script run completed in ~2s with no exception and a fresh third-session re-read confirmed the caller's edit was silently discarded (`RevertToSavedState`); the mandated pytest+subprocess invocation reproducibly hung (>105s, twice) instead | PASS (measured; behaviour is non-deterministic across contexts) |
| Explicit `ui=FwLcmUI(None, ThreadHelper())` opt-out reaches the same historical path as the default | Measured identically to the default in both contexts (silent discard in bare-script, block under pytest+subprocess) | PASS |

## Mock suite (regression, supplementary)
Not run -- out of scope for this task (pre-fix half of a both-sides
measurement; no library code was touched here).

## Blockers
None for Goal A. Goal B/C produced a genuine, reproducible LCM-level
process hang under the mandated pytest invocation; this was contained
using a subprocess timeout wrapper so the harness itself never hung, and
the stuck child processes were terminated after confirming (via
`Get-Process` CPU sampling) they were blocked, not merely slow. No
destructive write occurred against a live, not-yet-restored project at
any point.

## Recommendation
Hand back to lex-lead / cycle 2 (post-fix measurement). Key finding to
carry forward: the pre-fix default's exact failure mode is
context-dependent (silent discard vs. block), which is a stronger
argument for the fix than either single manifestation alone -- an
unpredictable defect surface, not a merely-undesirable-but-consistent one.
Full detail, exact commands, and the worker script logic are in the
evidence file above.
