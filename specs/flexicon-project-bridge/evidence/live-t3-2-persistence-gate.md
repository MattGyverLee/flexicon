# Live LCM evidence -- T3.2, the persistence gate

Feature: flexicon-project-bridge (`FLExProject.FromOpenProject()`).
Task: **T3.2 / T014**, the CP3 persistence gate. The spec body lives in the
FlexToolsMCP repo (`specs/flexicon-project-bridge`, spec.md:215-221); this file
is the live-verification record required by `CLAUDE.md` for the write-path
behaviour it clears.

Date: 2026-09-09.
Full run transcript: `evidence/t3_2_persistence_gate_scratch_2026-09-09.txt`.
This file is the protocol-shaped summary; that is the raw log.

Spec 5.2 requires the gate on a scratch project first, then on Sena 3. The
scratch pass (T014) is what this record covers. The **Sena 3 pass is a separate
task, T015**, logged in `evidence/t3_2_persistence_gate_sena3_2026-09-09.txt`:
same driver, modules and environment, also PASS, with Sena 3 copied off
beforehand (55954858 bytes) and restored byte-for-byte afterwards. It needs its
own protocol record -- `live-t3-2-persistence-gate-sena3.md` -- and is not
covered by this file.

## Why this record does not cite `tests/live_status.json`

**It cannot, by construction, and that is a real limit on this evidence --
not a formality waived.**

`tests/live_status.json` is written by `tests/conftest.py:1220` at the end of a
**pytest** session. T3.2 was not a pytest run. The gate's whole question is
whether a write commits when *the host* saves on close, so it had to be driven
through FlexTools' own entry point:

```
flextoolslib.code.FTModules.ModuleManager()
    .LoadAll()
    .RunModules(projectName, [moduleName], reporter, modifyAllowed=True)
```

`RunModules()` is what the GUI's Run button calls. Its `__closeProject()` ->
`FLExProject.CloseProject()` ("Save any changes and release the LCM Cache") is
the host save under test. No pytest session exists to write the ledger, and
`FLEXLIBS_REQUIRE_LIVE=1` -- a conftest mechanism -- likewise has nothing to
gate. A pytest harness could not have asked this question at all: it would have
been the owner of the cache, not an attachment to someone else's.

The mock-fallback risk that `run_mode` exists to catch is instead excluded
directly, by the disk check in Step 3(a) below: a mock cannot move bytes in a
`.fwdata` file. That is a stronger check than `run_mode`, but it is a
*substitute* check, and a reviewer should treat it as such.

## Command

```
cd D:\Apps\FlexTools\FlexTools
python scratchpad/ft_cli.py   # Gate A (write), then a separate process for Gate B
```

Modules: `D:\Apps\FlexTools\FlexTools\Modules\BridgeGate\`
- `T32_Gate_A_Write.py`  (`FTM_ModifiesDB: True`)
- `T32_Gate_B_Verify.py` (`FTM_ModifiesDB: False`)

Gate A ran in one process which then exited (FLExCleanup); Gate B ran in a
**separate, later process**. That is a real process boundary, not a re-read of
a warm cache.

## Environment

| | |
|---|---|
| FieldWorks | 9.3.10.1448 (64 bit) |
| python | 3.13.12 (`C:\Python313`, the `py` launcher default FlexTools uses) |
| flextoolslib | 2026.2.26b0 |
| flexlibs (stable, the donor) | 1.2.8 |
| pyflexicon | editable -> this repo, branch `flexicon-project-bridge` |
| `FLExProject.FromOpenProject` present | True |

Project used: **"Sena3 Bridge Scratch"** -- a disposable copy of Sena 3, made
for this gate. Not Target and not the real Sena 3: the gate must be driven by
FlexTools opening a project by name under its own control, which neither the
`target_sandbox` nor the `sena3_sandbox` tempdir fixture can express.

## Pre-state / post-state, read back from the LCM

Target: entry `0006f482-a078-4cef-9c5a-8bd35b53cf72` (headword `cibubu`),
its first sense `07086e7d-dfcc-4f4e-b0d6-0be7a7943f97`.

| Observation | Pre | Post |
|---|---|---|
| sense gloss | `gaguez` | **`T32-GATE-20260909-A`** |
| view is the donor object | False (ATTACH branch) | -- |
| view attached | True | -- |
| view `_undoable` | False (Phase 1, unconditional) | -- |
| view `writeEnabled` | True (borrowed from donor) | -- |

The module wrote inside `with fx.Transaction("T3.2 persistence gate"):` and
called **no save of its own** -- on an attached view `SaveChanges()` is refused
by design. The host's `CloseProject()` was the only save in play.

The post value is a **fresh re-query in a different process** (Gate B), not the
value passed in:

```
[INFO] view attached: True
[INFO] GLOSS_NOW='T32-GATE-20260909-A'
[INFO] expected sentinel='T32-GATE-20260909-A'
[INFO] original value   ='gaguez'
[INFO] T3.2 RESULT=PASS
```

A read-only dry run (`modifyAllowed=False`) preceded the write and proved the
wiring while writing nothing.

## Corroboration, two independent stacks

**(a) The raw file on disk -- no library involved.**

```
file  : C:\ProgramData\SIL\FieldWorks\Projects\Sena3 Bridge Scratch\
        Sena3 Bridge Scratch.fwdata
mtime : 2026-09-09 20:16
size  : 55954871 bytes   (was 55954858 before the write)
delta : +13 == len("T32-GATE-20260909-A") - len("gaguez") == 19 - 6

grep -c "T32-GATE-20260909-A"  ->  1
grep -c "gaguez"               ->  0
```

The sentinel is physically in the `.fwdata` and the old value is gone.

**(b) The FlexToolsMCP stack** -- different process, different host, flexicon
rather than flexlibs as the opener (op-201705234-005):

```
HEADWORD=cibubu
GLOSS_NOW='T32-GATE-20260909-A'
MATCHES_SENTINEL=True
```

## Verdict

**PASS: live-verified**, with the ledger caveat stated above.

A Phase 1 `Transaction` through a `FromOpenProject` attached view, inside the
host's session-long non-undoable task, commits when the host saves on close,
and reaches the `.fwdata`. No explicit `MainCacheAccessor` flush is required;
`contracts/from-open-project.md` section 2.2 needs no flush step. The gate does
not block CP1.

## State left behind

"Sena3 Bridge Scratch" still carries the sentinel gloss. It is disposable --
delete the folder when the campaign is done, or restore `gaguez` onto sense
`07086e7d-dfcc-4f4e-b0d6-0be7a7943f97`.

## Incidental finding for CP4 / T024

On this machine, under the Python FlexTools runs:

```
flexicon.version                         -> "4.6.0"   (the live source)
importlib.metadata.version("pyflexicon") -> "4.1.1"   (stale editable-install metadata)
```

Field evidence for T024's decision that the pre-flight must be a **capability
probe** (`hasattr(FLExProject, "FromOpenProject")`), never a version compare: a
hardcoded floor against either string gives the wrong answer here today.
