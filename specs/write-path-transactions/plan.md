# Implementation Plan: write-path-transactions

**Feature dir**: `specs/write-path-transactions` | **Working branch**: `write-path-transactions-b1-b3`
**Date**: 2026-08-14 | **Spec**: [`spec.md`](./spec.md) | **Tasks**: [`tasks.md`](./tasks.md)

**Note**: This plan was written against work already in flight. Checkpoints 1 and 2a are
complete; it records what was built and gates what remains. It does not re-derive
decisions already settled in `spec.md` §3 (D1-D3) or `tasks.md` (D4, D5).

## Summary

Flexicon's write path advertises transactional guarantees it does not deliver. Under
`undoable=False` — today's default — the entire session is one UnitOfWork
(`FLExProject.py:236-241`), so `Transaction()` cannot roll back a single operation, and
`_GetTransactionAPI` shipped discovery code for `RollbackToMark`, an API that does not
exist in liblcm (#236). Under `undoable=True` the machinery was independently broken: a
one-argument `BeginUndoTask` call (#233) and a hand-rolled `_transaction_depth` counter
that leaked on exceptions (#234).

The work splits into two tracks. **Track A** made the live `undoable=False` path honest
and headless-safe — injectable `ILcmUI`, `RefreshFromDisk()`, removal of the fictional
rollback API, and a written contract FlexToolsMCP can build on. **Track B** makes
`undoable=True` actually correct, so it can become the default (D3): rebuild
`transaction.py` on liblcm's own `UndoableUnitOfWorkHelper`, fix `Undo()`/`Redo()`, and
bracket all 295 currently-unbracketed mutation sites per-site (D5).

## Technical Context

**Language/Version**: Python 3.12.7, via pythonnet to .NET (FieldWorks 9+)

**Primary Dependencies**: SIL LCM (liblcm) — `UndoableUnitOfWorkHelper`,
`NonUndoableUnitOfWorkHelper`, `IActionHandler`, `ILcmUI`, `IUndoStackManager`

**Storage**: FLEx project files (`.fwdata`) on disk, mediated entirely by LCM. No
database, no serialization owned by this project.

**Testing**: pytest. Required invocation, per constitution Principle II:
```
python -m pytest -m "not requires_live_project" -q
```
Current: **1424 passed, 117 failed, 11 skipped, 322 deselected, 17 errors.** Not green.
The 117 failures are pre-existing and unrelated (rename-path breakage, issue #240, plus
sync-engine failures); they were unchanged across every commit on this branch.

**Target Platform**: Windows 11 + FieldWorks 9; consumed headlessly by FlexToolsMCP

**Project Type**: Python library (`flexicon/code/`), domain-partitioned Operations classes

**Constraints**:
- No agent may execute a live LCM write (constitution II). This makes real disk-persistence
  verification structurally unavailable to every task except the `needs_human` B2t gate.
- 174 existing `with self._TransactionCM(...)` call sites must keep working unchanged
  through the B1 rewrite.
- `undoable=False` must keep working for single-process FlexToolsMCP use throughout
  (spec §9.1); Track B may not regress it.

**Scale/Scope**: 295 unbracketed mutation sites across 62 files and 11 domains; 1144
`@OperationsMethod`-decorated methods total; 6 filed issues (#233-#238) plus A4 unfiled.

## Constitution Check

*GATE: evaluated against [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) v1.0.0.*

| Principle | Status | Evidence |
|---|---|---|
| **I. Verify LCM surface first** | PASS | Every LCM claim in this feature is cited to liblcm source in [`reviews/cycle2-explore-liblcm-facts.md`](./reviews/cycle2-explore-liblcm-facts.md) (F1, F2, F5) or to `tests/contract/snapshots/liblcm_baseline.json`, extended by task CB specifically to cover the four types B1 builds on. O1/O2 resolved by source reading (`UnitOfWorkHelper.cs:31,115-116,137`; `UndoStack.cs` state machine). |
| **II. No live write without human gate** | PASS, with two recorded breaches | B2t is marked `needs_human` and unexecuted. Two historical breaches of the prose rule are disclosed in [`reviews/cycle3-verification.md`](./reviews/cycle3-verification.md) §2 and in commit `3d4fdc9`; neither corrupted data. The remediation is §7.0 of `spec.md` — the invocation is now a required, quotable control rather than an inferred prohibition. |
| **III. Controls, not prohibitions** | PASS | B2g ships `tests/write_path_transactions/scan_unbracketed_mutations.py` plus a frozen 295-entry baseline and a two-way ratchet, making D5 mechanically enforceable across 62 files. |
| **IV. Report the measurement** | PASS | The 139/1638 vs 117/1424 discrepancy was reconciled arithmetically rather than resolved by preference (1861 - 22 = 1839 = 139+1663+20+17) and the reconciliation is published in `spec.md` §7.0. |
| **V. Honest API surface** | PASS | A2 removed the `RollbackToMark` fiction; D4 keeps the `Transaction()` name but states mode-dependent semantics in the docstring plus a one-shot `OpenProject` warning; `docs/EXCEPTION_HANDLING.md` records that under `undoable=False` the atomicity unit is the session. |
| **VI. Hide complexity, not behavior** | PASS | #235 closes as **in-process-only** with that scope recorded on the issue rather than left implied. |

**Post-design re-check**: no violations. One item is deliberately deferred rather than
resolved — see Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/write-path-transactions/
├── spec.md          # Problem, verified LCM surface, decisions D1-D3, test plan §7.0
├── plan.md          # This file
├── tasks.md         # Authoritative task order; decisions D4, D5
├── reviews/         # 15 dated specialist reports — the evidence base
│   ├── cycle1-explore-b2sweep.md          # Phase 0: the 294-site inventory
│   ├── cycle2-explore-liblcm-facts.md     # Phase 0: liblcm source facts F1-F5
│   ├── cycle2-explore-dispatch-layer.md   # Phase 0: evidence behind D5
│   ├── cycle3-programmer-b1b3.md          # B1/B3 implementation record
│   ├── cycle3-programmer-b2g.md           # B2g scanner + baseline record
│   └── cycle3-verification.md             # Independent B1/B3 verification
└── issues/
    └── createfield-always-raises.md
```

Per the constitution's "evidence lives in `reviews/` and is cited by path", this plan
does **not** emit `research.md`, `data-model.md`, `quickstart.md`, or `contracts/`. Those
roles are already filled and would become second copies free to drift:

| Standard artifact | Filled by |
|---|---|
| Phase 0 research | `reviews/cycle2-explore-liblcm-facts.md`, `reviews/cycle2-explore-dispatch-layer.md` |
| Sweep inventory | `reviews/cycle1-explore-b2sweep.md`, now superseded as the enforceable form by `tests/write_path_transactions/snapshots/unbracketed_baseline.json` |
| Contracts | `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md`, `tests/contract/snapshots/liblcm_baseline.json` |
| Quickstart / validation | `spec.md` §7.0 (the required invocation) and §7.1 (per-task coverage) |

### Source code (repository root)

```text
flexicon/code/
├── transaction.py              # B1 — rewritten on UndoableUnitOfWorkHelper
├── undoable_operation.py       # B1 — _FLExUndoableOperation entry point
├── FLExProject.py              # A1c, A2, A4, B3; 7 unbracketed sites remain
├── BaseOperations.py           # validate-then-mutate discipline; 7 sites remain
├── headless_ui.py              # A1b — HeadlessLcmUI(ILcmUI)
└── <Domain>/*Operations.py     # B2 — 281 of the 295 sites, batched by domain

tests/
├── contract/                   # liblcm reflection baseline (22 tests)
├── write_path_transactions/    # B2g scanner, frozen baseline, ratchet (4 tests)
├── test_b1t_action_handler_double.py   # B1t — 30 tests, independent doubles
└── operations/test_transaction_rollback.py
```

**Structure decision**: no new top-level structure. B2's 295 edits are confined to
existing Operations classes; the only new directory is `tests/write_path_transactions/`,
which holds the ratchet because it guards a cross-cutting property rather than any one
module.

## Execution status

### Checkpoint 1 — Track A (live path) — COMPLETE, on `main`

A1a-A1d (injectable `ILcmUI` + `HeadlessLcmUI`), A2a-A2e (rollback honesty), A4
(`RefreshFromDisk`), CB (contract baseline), MCP (written contract). Landed as `b3a5bb9`,
`17a8740`, `7404163`. Closes #236, #238.

### Checkpoint 2a — Track B engine — COMPLETE, on `write-path-transactions-b1-b3`

| Task | Commit | Result |
|---|---|---|
| **B1** rewrite on `UndoableUnitOfWorkHelper`, `_transaction_depth` deleted | `1dfc464` | Closes #233, #234, #236-for-undoable. All 174 existing call sites unchanged. |
| **B3** `Undo()`/`Redo()` on `ActionHandlerAccessor`, gated on `CanUndo()`/`CanRedo()` | `1dfc464` | #235 closes as in-process-only. |
| **B1t** offline verification via independently-built action-handler doubles | `3d4fdc9` | 30 tests. All six required properties hold; **zero defects** against required behavior. |
| **B2g** AST scanner + frozen baseline + two-way ratchet | `b996d89` | 4 tests. Baseline frozen at **295**. |

Offline suite delta across the checkpoint: **+30 passed, no change** to failed / skipped /
deselected / errors. No regressions, and no pre-existing failures accidentally fixed.

**Not yet merged to `main`.** `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md` states this
explicitly: B1 exists only on this branch, so it is absent from any release satisfying
`pyflexicon>=4.3.0,<5`.

### Checkpoint 2b..2n — the B2 sweep — NOT STARTED

295 sites, per-site brackets (D5), batched one commit per domain, ratchet baseline edited
down in the same commit as each batch. Verified per-file distribution:

| Domain | Sites | | Domain | Sites |
|---|---:|---|---|---:|
| Lexicon | 84 | | code-root | **14** |
| Grammar | 59 | | Lists | 14 |
| Notebook | 44 | | System | 11 |
| TextsWords | 24 | | Scripture | 9 |
| Discourse | 21 | | Shared | 9 |
| | | | Reversal | 6 |

**Scope correction — 294 → 295.** B2g's scanner reproduced cycle-1's inventory exactly,
then found one genuine additional site cycle-1's own methodology should have counted:
`FLExProject.SetAudioPath`, an unbracketed `set_String`. It is included in the frozen
baseline rather than suppressed. Only **code-root** changes, 13 → 14; every other domain
count in `tasks.md` is confirmed correct.

**Sequencing recommendation**: start with **Reversal (6)**, not Lexicon (84). The batch
recipe — indent body, add `with`, edit the baseline down, commit — is unproven end-to-end,
and the reverse ratchet guard has never actually fired. Prove both on the smallest domain
before committing to 84 edits under an untested procedure. Then Shared (9) / Scripture (9),
then scale.

### Checkpoint 3 — close-out — BLOCKED

- **B4** `flexicon.CAPABILITIES` with the `per-operation-uow` token. Gated on B2 complete;
  the contract marks it PLANNED and the token must not ship before the capability is real
  (constitution V).
- **A3** `AbortSession()` → `IActionHandler.Rollback(0)`, carrying the O2 catch: `Rollback`
  leaves the FSM in `ReadyForBeginTask`, so under `undoable=False` it terminates the
  session envelope and must either reopen `BeginNonUndoableTask()` or be documented as
  terminal.
- **B2t** end-to-end persistence test (#237). **`needs_human`.** Requires a live LCM write
  to a scratch project. No agent may execute it.
- **DEF** flip the default to `undoable=True` (D3). **`needs_human`** — public API default
  change, gated on Checkpoint 2 green.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| 295 per-site edits instead of ~17 at a central dispatch bracket | D5, resolved on evidence in `reviews/cycle2-explore-dispatch-layer.md`. A central bracket pulls `_EnsureWriteEnabled`/`_Validate*` **inside** the UnitOfWork, so every rejected input opens an undo task and — under B1's `UndoableUnitOfWorkHelper` — fires a real `Rollback(0)`. 12/12 sampled methods across 12 domains are strictly validate-then-mutate, so 100% of the sample regresses. | The hybrid needs a "first mutation" hook that does not exist in liblcm (constitution I: we already shipped one such assumption as #236). 29% of existing sites use argument-derived undo labels a central `func.__name__` bracket would flatten to `LexEntryOperations.Create` in the linguist-facing FLEx undo menu. 48 decorated methods contain a top-level `yield`, which a dispatch-layer `with` exits before the generator's first frame runs. And 17 hand sites remain under **every** shape. |
| Real disk persistence unverified for the B1 rewrite | Constitution II forbids the live write that would verify it. B1t's doubles prove the **calling contract** — right method, right arity, right order, faithful to liblcm source — but cannot prove liblcm's internals behave as its own comments claim. | Deferring the whole rewrite until a human is available to run B2t would have blocked Checkpoint 2a indefinitely. The gap is stated rather than closed: `reviews/cycle3-verification.md` §7 enumerates exactly what remains unverifiable, and B2t stays open. |
| 117 pre-existing offline failures tolerated, not fixed | Out of scope (issue #240, rename paths, plus sync-engine); stable and unchanged across every commit on this branch, so they demonstrably conceal no regression from this work. | Fixing them inside this feature would confound its test delta with unrelated repair. **Open risk:** they are unaudited — nobody has confirmed what all 117 are. |

## Notes for the next session

`.specify/feature.json` is machine-local and gitignored (spec-kit treats it as
per-checkout state). A fresh checkout must re-pin it before any `/speckit-*` skill will
resolve paths:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/write-path-transactions'
```
