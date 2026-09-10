# Live LCM evidence -- T3.2 persistence gate, second pass (Sena 3)

Feature: flexicon-project-bridge (`FLExProject.FromOpenProject()`).
Task: **T015**, the Sena 3 pass of the CP3 persistence gate. Spec 5.2 requires
the gate on a scratch project first, then on Sena 3; this is the second half.
The scratch pass (T014) has its own record in
`live-t3-2-persistence-gate.md`.

Date: 2026-09-09.
Full run transcript: `evidence/t3_2_persistence_gate_sena3_2026-09-09.txt`.

Method, driver, modules and environment are **identical to the scratch pass** --
see that record for why this is genuine FlexTools
(`ModuleManager.RunModules()`, the GUI's own code path) and for the same
`tests/live_status.json` limitation, which applies here unchanged: this was not
a pytest run, so the conftest ledger cannot cover it, and the disk check below
substitutes for `run_mode`.

Project used: **"Sena 3"** -- the real one, not a copy. Spec 5.2 asks for it by
name. Because it is not disposable, it was copied off first and verified
restored afterwards (Step 4).

## Command

Same driver as T014, plus a third module:

```
cd D:\Apps\FlexTools\FlexTools
python scratchpad/ft_cli.py   # Gate A (write) -> Gate B (verify) -> Gate C (restore)
```

Each gate ran in its own process. Modules in
`D:\Apps\FlexTools\FlexTools\Modules\BridgeGate\`:
`T32_Gate_A_Write.py`, `T32_Gate_B_Verify.py`, `T32_Gate_C_Restore.py`.

## Step 0 -- insurance, before touching a non-disposable project

```
cp "C:\ProgramData\SIL\FieldWorks\Projects\Sena 3\Sena 3.fwdata" \
   <scratchpad>/Sena3.pre-T015.fwdata
-> 55954858 bytes
pre-state clean: sentinel count 0, "gaguez" count 1
```

## Pre-state / post-state, read back from the LCM

Target: entry `0006f482-a078-4cef-9c5a-8bd35b53cf72` (`cibubu`), first sense
`07086e7d-dfcc-4f4e-b0d6-0be7a7943f97`.

| Observation | Pre | Post (Gate B, new process) |
|---|---|---|
| sense gloss | `gaguez` | **`T32-GATE-20260909-A`** |
| view is the donor object | False (ATTACH branch) | -- |
| view attached | True | True |
| view `_undoable` | False (Phase 1, unconditional) | -- |
| view `writeEnabled` | True (borrowed from donor) | -- |

The module wrote inside a `Transaction` and requested no save of its own; the
host's `CloseProject()` was the only save. `Errors: 0; Warnings: 0`.

Gate B is a fresh re-query in a later process:

```
[INFO] view attached: True
[INFO] GLOSS_NOW='T32-GATE-20260909-A'
[INFO] T3.2 RESULT=PASS
```

## Step 3 -- the file on disk

```
Sena 3.fwdata   55954871 bytes   (was 55954858)
delta +13 == len("T32-GATE-20260909-A") - len("gaguez") == 19 - 6
grep -c "T32-GATE-20260909-A"  ->  1
grep -c "gaguez"               ->  0
```

Identical byte arithmetic to the scratch pass. The result reproduces on a
second project.

## Step 4 -- Gate C, restore (Sena 3 must not be left modified)

```
[INFO] GLOSS_BEFORE='T32-GATE-20260909-A'
[INFO] GLOSS_AFTER_IN_MEMORY='gaguez'
[INFO] RESTORE OK

after close:
  Sena 3.fwdata   55954858 bytes   (original size)
  grep -c "T32-GATE-20260909-A"  ->  0
  grep -c "gaguez"               ->  1
  cmp "Sena 3.fwdata" <scratchpad>/Sena3.pre-T015.fwdata  ->  IDENTICAL
```

Not merely "the gloss is back": the whole 55,954,858-byte file matches the
pre-run backup byte for byte.

## Verdict

**PASS: live-verified**, reproducing the scratch result exactly, with the same
ledger caveat as T014.

An unplanned finding from the restore: writing the sentinel and writing the
original back produced a byte-identical file. The attached-view write path is
therefore durable *and* cleanly reversible -- it introduces no incidental churn
(no stray timestamps, no reordering, no residue) beyond the field changed.

With T014, the gate is settled on two projects and does not block. CP1 may
ship; US4 (docs) and US5 (template pre-flight) are unblocked.

## State left behind

| | |
|---|---|
| Sena 3 | pristine, verified byte-identical |
| Sena3 Bridge Scratch | still carries the sentinel; disposable, delete when done |
| `Modules\BridgeGate\` | three gate modules left installed in `D:\Apps\FlexTools\FlexTools\Modules\BridgeGate` (A write / B verify / C restore) -- remove if you do not want them in the FlexTools module list |
