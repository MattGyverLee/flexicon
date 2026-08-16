#
#   FLEXTOOLSMCP_WRITE_CONTRACT.md
#
#   Written contract: what FlexToolsMCP may build on when calling flexicon's
#   write path.
#
#   Covers: flexicon v4.3.0 (the pinned floor, `pyflexicon>=4.3.0,<5`) and the
#   post-Track-B surface planned in `specs/write-path-transactions/`.
#
#   Copyright 2025-2026
#

# FlexToolsMCP Write-Path Contract

**Audience:** the FlexToolsMCP maintainer, who pins `pyflexicon>=4.3.0,<5` and
must keep working against an install that never upgrades past 4.3.0, as well
as against the post-Track-B surface once it lands.

**Status of this document:** authoritative for the six questions below. Every
behavioural claim cites its source (`liblcm` source file:line, or a specific
flexicon file:line) and every planned-but-unshipped item is marked **PLANNED**
with its task ID from `specs/write-path-transactions/tasks.md`. Nothing here
is aspirational: if flexicon 4.3.0 does not do a thing, this document says so
plainly rather than describing the target state as current.

**Source basis.** This contract is built from, and must not contradict:
`specs/write-path-transactions/spec.md`, `tasks.md`, and the cycle-2 reviews
(`reviews/cycle2-explore-liblcm-facts.md` — cited as **F1**-**F6** below,
`reviews/cycle2-explore-dispatch-layer.md` — cited as **P1**-**P4**,
`reviews/cycle2-domain.md` — cited as **Q1**-**Q4**, `reviews/cycle2-qc.md`,
`reviews/cycle2-verification.md`, `reviews/cycle2-createfield-issue.md` and its
superseding `reviews/cycle2-createfield-revision.md`, `reviews/cycle2-p0-fix.md`,
and `issues/createfield-always-raises.md`). Where a source report says "NOT
FOUND IN SOURCE," this document says **unknown — do not build on it**, not a
plausible guess.

**Test-suite state, stated plainly.** The required invocation is:

```
python -m pytest -m "not requires_live_project" -q
```

Measured on that command against the current tree: **1424 passed, 117 failed,
11 skipped, 322 deselected, 17 errors.** The suite is **not green**. The 117
failures are a mix of causes unrelated to this feature, confirmed by
inspection: stale `flexlibs2`->`flexicon` rename paths (e.g.
`tests/test_write_enabled_fix.py` hardcodes `Path("flexlibs2/code/...")` — see
issue #240), and genuine pre-existing sync-engine failures (e.g.
`test_diff_engine.py::test_compare_unchanged_objects`, plus Mock-based
failures and errors in `flexicon/sync/tests/test_duplicate_operations.py`).
`tests/contract/` (Mode 1, checked-in baseline snapshot, no live liblcm) is
separately green: 22 passed. Do not cite "the suite passes" without this
qualification.

**Do NOT use `pytest --ignore=tests/contract`.** It applies no `-m` filter, so
it collects and EXECUTES the 322 `requires_live_project` tests. Per
`tests/conftest.py:1221`, Phases A-D of those run **in-place against the real
Sena 3 project** (only Phase E uses the isolated `sena3_sandbox` tempdir).
That invocation therefore performs live LCM writes against a real FLEx project
on the machine running it. An earlier revision of this document quoted
**1638 passed / 139 failed / 20 skipped / 17 errors** from that broader
command; those figures were accurate arithmetic but were produced by a run
that wrote to a live project, and the "live-LCM state pollution" they were
attributed to was that live suite executing. The two totals reconcile exactly
by scope — `-m` pool 117+1394+11+17+322 = 1861, minus the 22 contract tests
absent from the other pool = 1839 = 139+1663+20+17 — so neither number hid a
regression. The narrower command is the correct one because it is the only one
that does not touch a real project.

---

## 1. Raw-LCM user code inside `run_module`

**Question:** `run_module` executes arbitrary user scripts that touch LCM
objects directly, outside any wrapper method. Under a per-operation model,
what brackets those mutations?

**Answer, confirmed against F1/F3.** `run_module` should open **one**
`UnitOfWork` around the whole script (`Main()`), using liblcm's own
`NonUndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW` (or the undoable
equivalent, `UndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW` — both flavours
exist and both are the canonical join helper: **F3**,
`UndoableUnitOfWorkHelper.cs:91-98` / `NonUndoableUnitOfWorkHelper.cs:78-85`).
Any wrapper method the script calls that also opens a UoW sees
`ActionHandlerAccessor.CurrentDepth > 0` (already true inside the script's
envelope) and **joins** it rather than nesting — this is not new machinery to
build; it is the same idiom already in use at
`flexicon/code/System/CustomFieldOperations.py:300`.

**B1 status, precisely.** B1 is implemented and has passed offline verification
against a test double that reproduces liblcm's destructive double-begin
ordering, but it is **committed on the branch
`write-path-transactions-b1-b3` only — not merged to `main`, not released, and
therefore NOT present in any version satisfying `pyflexicon>=4.3.0,<5`.** On
that branch `_NestingAwareTransaction.__enter__` reads
`cache.ActionHandlerAccessor.CurrentDepth` directly, with the Python-side
`_transaction_depth` counter deleted, and no-ops when depth > 0. Treat B1 as
PLANNED for integration purposes until it ships in a release. Nothing needs
hand-rolling; `DoUsingNewOrCurrentUOW`'s body is literally
`if actionHandler.CurrentDepth > 0: task() else: Do(undoText, redoText,
actionHandler, task)` (**F3**, lines 94-97). The result is a single
script-scoped envelope: it opens when the script starts, every wrapper call
inside joins it, and it closes (and becomes eligible to save) only when the
script ends.

**This is load-bearing, not stylistic — say it plainly:** **a second
`BeginUndoTask` while one is already open does not merely throw. Per F1,
`UndoStack.cs:209-216` calls `Rollback(0)` FIRST — discarding every change the
already-open UoW held, uncommitted — resets the FSM to `ReadyForBeginTask`,
releases the write lock, and only then throws
`InvalidOperationException("Nested tasks are not supported.")`.** If
`run_module`'s envelope and a wrapper method's internal bracket both tried to
open independently instead of joining, the *outer* script's accumulated
in-memory work would be silently discarded on the very first nested call —
not merely refused. Join-not-nest is therefore a data-loss guard, not a
convenience.

`CurrentDepth` itself is binary (**F2**, `UndoStack.cs:731-734`: 1 if
`ProcessingDataChanges`, 0 otherwise — never 2+) and cannot distinguish an
undoable task from a non-undoable one; both set the identical FSM state
(**F2**). That is sufficient for the join test above (`> 0` is all
`DoUsingNewOrCurrentUOW` checks) but means `CurrentDepth` cannot be used to
detect "am I nested two deep" — there is no such state to detect.

| | 4.3.0 today | Post-Track-B |
|---|---|---|
| Does a raw-LCM script under `run_module` get any envelope at all? | Only incidentally: under the default `undoable=False`, `OpenProject()` already holds one session-long `BeginNonUndoableTask()` open (`FLExProject.py:257-280`), so raw LCM code the script runs joins that by construction — there is no `run_module`-specific bracket. | `run_module` opens one script-scoped UoW via `DoUsingNewOrCurrentUOW`; wrapper calls inside join it. **PLANNED**; its flexicon-side prerequisite, task **B1** (rewrite `transaction.py` on the liblcm helper), has LANDED (unreleased), so this is now blocked only on `run_module`'s own bracket, which is FlexToolsMCP-side work not tracked by a flexicon task ID here. |
| What happens if a wrapper method inside the script also opens `BeginUndoTask` naively? | N/A today — no wrapper opens `BeginUndoTask` in the default mode; `undoable=True` currently opens no per-operation envelope at all (#237, still open). | Must join via `CurrentDepth > 0`, never re-open. This is what B1 delivers. |

---

## 2. Save cadence

**Question:** per operation, or at `CloseProject()`? What does a user watching
FLEx in shared mode see during a run, and what happens on a mid-run crash?

**Mechanism (F4).** liblcm's own auto-save is a 1-second `System.Timers.Timer`
(`UnitOfWorkService.cs:174-177`) whose handler, `SaveOnIdle`, returns without
saving unless **all** of: the FSM is back at `ReadyForBeginTask` (not mid-UoW,
line 240); no undo stack holds an open mark (line 251); at least 10 seconds
have passed since the last save (line 255); and the caller has been idle at
least 2 seconds, waived only if the last save is more than 5 minutes stale
(line 258). **Ending a UoW does not itself guarantee a disk write** —
`EndUndoTaskCommon` (`UndoStack.cs:289-360`) contains no save call; it only
resets the FSM (line 354), and the write happens only on the next timer tick
that clears every gate above. `IUndoStackManager.Save()` (what
`CloseProject()` calls, `FLExProject.py:298-300`) bypasses all four throttles
and goes straight to `SaveInternal`, but that still requires
`ReadyForBeginTask` via `CheckReadyForCommit`, which **rolls back** if the
state is wrong (`UndoStack.cs:239-246`) rather than saving a partial state.

**What this means for `undoable=False` (the 4.3.0 default and floor):**
`OpenProject()` holds one `BeginNonUndoableTask()` open from open to close
(`FLExProject.py:257-280`), so the FSM never returns to `ReadyForBeginTask`
during the run. **None of `SaveOnIdle`'s gates ever clear. Nothing reaches
disk until `CloseProject()`.**

**What a linguist watching shared-mode FLEx sees during a headless run under
`undoable=False` (Q1, domain seat):** nothing, for the run's entire duration,
then everything at once when the script calls `CloseProject()`. The domain
seat is explicit that this reads as a hang or a corruption event to a user
trained by Send/Receive to expect incremental colleague updates, not a
silent multi-minute pause followed by a bulk flush.

**What happens on a mid-run crash under `undoable=False`:** total loss. Since
nothing was ever committed, a crash at entry 1,500 of 2,000 leaves **zero**
trace that the run ever happened — worse than a linguist's normal "I lost the
last edit" mental model of undo/save (Q1).

**Domain seat's recommendation (Q1):** per-operation save cadence — i.e.
`undoable=True` plus Track B per-operation brackets — is the only mode a
linguist should be asked to trust for any run long enough to matter.
`undoable=False` should be positioned as short-lived, single-process,
non-interactive only.

| | 4.3.0 today (`undoable=False`) | Post-Track-B (`undoable=True` + B1/B2) |
|---|---|---|
| Save cadence | None until `CloseProject()`. FSM never returns to `ReadyForBeginTask` mid-run. | Each bracketed operation returns the FSM to `ReadyForBeginTask`; auto-save can fire on the next 1s tick once the 10s/2s gates clear. |
| Shared-mode visibility during run | Nothing visible; a colleague's FLEx session sees no incremental updates. | Incremental — the unsaved footprint stays at roughly one operation's worth at a time (spec.md D3). |
| Mid-run crash | Entire session's work lost; no partial save. | Only the in-flight operation's work is at risk; prior operations already had a chance to auto-save. |

---

## 3. Capability detection at runtime

**Agreed design:** an explicit `flexicon.CAPABILITIES` frozenset of tokens —
`"ui-injection"`, `"per-operation-uow"`, `"refresh-from-disk"`,
`"transaction-rollback"` — probed with `in`.

**CRITICAL — state this explicitly.** On flexicon 4.3.0, `flexicon.CAPABILITIES`
**does not exist as an attribute at all**. A bare reference raises
`AttributeError`:

```python
>>> import flexicon
>>> flexicon.CAPABILITIES
AttributeError: module 'flexicon' has no attribute 'CAPABILITIES'
```

**The only correct probe**, safe on both 4.3.0 and any future version that
adds `CAPABILITIES`:

```python
CAPS = getattr(flexicon, "CAPABILITIES", frozenset())

if "per-operation-uow" in CAPS:
    # Post-Track-B surface: undoable=True gives per-operation brackets.
    ...
else:
    # 4.3.0 floor: fall back to the undoable=False / session-envelope path.
    ...
```

Do not write `hasattr(flexicon, "CAPABILITIES") and "x" in flexicon.CAPABILITIES`
as two steps — the one-line `getattr(..., frozenset())` form is shorter and
cannot race with a concurrent import in a way the two-step form could be
misread to.

**`CAPABILITIES` has LANDED, not yet RELEASED** (task **B4**,
`flexicon/__init__.py`), carrying all four tokens. It is on the
`write-path-transactions-b1-b3` branch; as with B1 (see §2), treat it as
PLANNED for integration purposes until it ships in a release, since a
version-pinned install will not see it before then. It was filed as B4 under
Checkpoint 2 rather than Checkpoint 1 because the `per-operation-uow` token
could not honestly be reported before B1+B2 made the capability real
(constitution V).

The `getattr(..., frozenset())` probe above remains the **only** correct form,
and is now load-bearing rather than merely forward-compatible: it is what lets
one FlexToolsMCP build work against both a pinned 4.3.0 install (which resolves
to an empty frozenset, correctly reporting zero capabilities) and a post-Track-B
install (which reports all four).

**A token means "this build implements the capability", not "the capability is
active in your session."** `CAPABILITIES` is a module-level constant, so it
cannot vary by mode, and two of the four tokens are mode-dependent. This is the
one place in this contract where a token is *reported* in a mode that does not
*deliver* it, so it is stated here, in the `flexicon/__init__.py` docstring, and
at the boundary where the mode is chosen (`OpenProject()`'s one-shot warning,
task A2d) — which is what constitution V requires of a mode-dependent guarantee.

A consumer that needs to know whether rollback is live in *this* session must
check the mode it passed to `OpenProject()`, not the token.

| Token | 4.3.0 (pinned floor) | Post-Track-B build (landed, unreleased) |
|---|---|---|
| `"ui-injection"` | Feature exists (`ui=` param, #238), but `CAPABILITIES` does not exist to report it. | **Reported.** Active in both modes. |
| `"per-operation-uow"` | Not implemented (`undoable=True` opens no per-operation envelope; #237 open). | **Reported** (B1+B2 landed; 295/295 mutation sites bracketed, B2g ratchet baseline at 0). Active **only under `undoable=True`** — under `undoable=False` the atomicity unit is the session. |
| `"refresh-from-disk"` | Feature exists (`RefreshFromDisk()`, task A4), but `CAPABILITIES` does not exist to report it. | **Reported.** Active in both modes. |
| `"transaction-rollback"` | Not implemented (no reachable rollback in either mode today — see §5). | **Reported** (B1 landed). Active **only under `undoable=True`**, via `UndoableUnitOfWorkHelper`'s `Rollback(0)` on `Dispose`. Under `undoable=False` there is still no rollback (#236) — the token is present, the guarantee is not. |

---

## 4. Nesting: which methods open their own UoW, and what happens on
   wrapper-calls-wrapper?

**4.3.0 today.** No `Operations` method opens a per-operation UoW at all.
Under the default `undoable=False`, the entire session runs inside the one
`BeginNonUndoableTask()` opened by `OpenProject()` (`FLExProject.py:278`) and
closed by `CloseProject()` (`FLExProject.py:294`) — every wrapper call, and
every wrapper-calls-wrapper chain, executes inside that same single envelope.
There is nothing to nest because nothing opens a second one.

**Post-Track-B (per the dispatch-layer probe, P1/P2).** Coverage of the 294
public/mutating methods surveyed: 235 already carry `@OperationsMethod`
directly; 32 are private helpers whose callers are transitively decorated;
13 are generic base-class helpers (7 in `BaseOperations.py`, decorated; 3 in
`possibility_item_base.py`, decorated; 3 in `Shared/catalog_backed.py`,
**undecorated**); 8 are private helpers in the SIL-catalog import chain
reachable from outside any decorated method; and 6 are `FLExProject` methods
that are not `BaseOperations` subclasses at all (`LexiconSetFieldText`,
`LexiconClearField`, `LexiconSetListFieldMultiple`, `LexiconDeleteObject`,
`LexiconSetComplexFormType`, `LexiconAddComplexForm`). Whichever bracket shape
is chosen (§ below — central vs. per-site is **still open**), a residual of
at least 17 sites (8 + 6 + 3 undecorated `CatalogBackedMixin` methods) needs
individual, hand-added brackets regardless.

**Wrapper-calls-wrapper: three real, decorated→decorated, mutating pairs
exist today (P2):**

- `Lexicon/LexSenseOperations.py:1439` `SetPartOfSpeech` →
  `self.project.MSA.CreateInflAff` (`Lexicon/MSAOperations.py:243`)
- `Lexicon/ExampleOperations.py:1215` `AddMediaFile` →
  `self.project.Media.CopyToProject` (`Shared/MediaOperations.py:1280`)
- `TextsWords/ParagraphOperations.py:342` `Duplicate` →
  `self.project.Segments.AppendSentence` (`TextsWords/SegmentOperations.py:544`)

Nesting-awareness for these is **not new work**: `_NestingAwareTransaction.__enter__`
(`transaction.py`) reads `cache.ActionHandlerAccessor.CurrentDepth` and
no-ops when depth > 0 — this machinery predates Track B; **B1** has now
landed it on liblcm's own `CurrentDepth` instead of the hand-rolled
`_transaction_depth` counter (defect #234, which no longer exists to leak).

**The one-sentence rule a caller can memorise:** *a wrapper method that calls
another wrapper method never opens a second bracket — it always joins
whatever bracket (if any) is already open, exactly like liblcm's own
`DoUsingNewOrCurrentUOW`, so calling `LexEntry.Create` from inside your own
`with project.Transaction(...):` block behaves identically to calling it
bare.*

| | 4.3.0 today | Post-Track-B |
|---|---|---|
| Do wrapper methods open their own UoW? | No — one session-long envelope from `OpenProject`/`CloseProject`. | Yes, per-operation, for methods carrying `@OperationsMethod` with `mutating=True` (shape still open — see §"Open disagreements" below). |
| Wrapper calling wrapper | Both run inside the same pre-existing session envelope; no nesting concern. | Joins via `CurrentDepth > 0`; never nests. Already-solved by `_NestingAwareTransaction`. |
| Coverage gaps | N/A (nothing brackets today). | 17 methods (8 catalog-chain private helpers + 6 non-`BaseOperations` `FLExProject` methods + 3 undecorated `CatalogBackedMixin` publics) need hand bracketing under any bracket shape. |

---

## 5. `ILcmUI` injection (#238) and rollback's real status (#236)

**What landed, 4.3.0 today (confirmed by direct source read and by the
independent verification agent):**

- `FLExProject.OpenProject(self, projectName, writeEnabled=False,
  undoable=False, ui=None)` (`FLExProject.py:164`), passing `ui` straight
  through to `FLExLCM.OpenProject(projectName, ui)`. `ui=None` (the default,
  unchanged for backward compatibility) still constructs `FwLcmUI` — verified
  by monkeypatch test and by the verification agent reading `FLExLCM.py:98-99`.
- `flexicon/code/headless_ui.py::HeadlessLcmUI(ILcmUI)` — implements all 10
  methods and both properties of the real `ILcmUI` (cross-checked directly
  against `liblcm/src/SIL.LCModel/ILcmUI.cs` by the verification agent — the
  interface really is 10 methods + 2 properties, and all 12 are present,
  including `RestoreLinkedFilesInProjectFolder`, found missing and fixed
  during Track A). `ConflictingSave()` returns `False` — never the
  `RevertToSavedState()` branch — and by default raises
  `FP_ConflictingSaveError`. No member marshals through `ISynchronizeInvoke`
  (grepped, zero `.Invoke(`/`.BeginInvoke(` occurrences).
- `FP_ConflictingSaveError` — **canonical import as of the P0 fix**:

  ```python
  from flexicon.code.exceptions import FP_ConflictingSaveError
  # or, equivalently, the package-level re-export:
  from flexicon import FP_ConflictingSaveError
  ```

  It lives in `flexicon/code/exceptions.py`, subclasses `FP_RuntimeError`
  (not bare `Exception` and not `FP_ProjectError` — the QC P0 finding that
  drove the move), and is exported from `flexicon/__init__.py` alongside
  every other `FP_*` type, so `except FP_RuntimeError` (the documented
  catch-all pattern in `docs/EXCEPTION_HANDLING.md`) now catches it too. The
  `flexlibs2` alias package picks it up automatically. **Back-compat import
  still works** — `flexicon/code/headless_ui.py` re-imports (does not
  redefine) it from `.exceptions`, so
  `from flexicon.code.headless_ui import FP_ConflictingSaveError` continues
  to resolve to the identical class object (verified by identity check in
  the P0-fix pass). New code should use the canonical import; the
  back-compat path exists only so nothing already written against
  `headless_ui` breaks.

**What the MCP can promise about conflict handling today:** a conflicting
save under `HeadlessLcmUI` never blocks on a dialog and never silently
discards the session's unsaved changes (unlike `SilentLcmUI`, whose
`ConflictingSave()` returns `true` unconditionally — a strictly worse
default that must never be used). It raises an exception the caller can
catch by name.

**Rollback's real status — blunt.** **No `RollbackToMark` exists anywhere**,
confirmed by three independent means: source grep across all of
`liblcm/src` (zero hits), binary metadata-heap inspection of
`SIL.LCModel.Core.dll` (contains `Rollback`, `CollapseToMark`, `CurrentDepth`,
`BeginUndoTask`; does **not** contain `RollbackToMark` — **F5(a)**), and a
grep of `flexicon/code/` for `RollbackToMark` (zero matches, confirmed by the
verification agent). `IActionHandler` itself is not defined in the liblcm
repo (it ships in the external `SIL.LCModel.Core` package) — source-level
confirmation of its full contract is **unknown, do not build on it** beyond
what the binary evidence shows.

What atomicity *is* available, per mode, today:

| Mode | Atomicity unit today | Real revert primitive |
|---|---|---|
| `undoable=False` (4.3.0 default) | The whole session (`OpenProject()`...`CloseProject()`). A mid-operation exception leaves every prior mutation applied — `docs/EXCEPTION_HANDLING.md`'s "Atomicity Under `undoable=False`" section states this plainly. | `IActionHandler.Rollback(0)` is valid mid-task (**F5(c)**, `UndoStack.cs:705-724`) and would discard the *entire session's* uncommitted changes — genuine, but session-granularity, all-or-nothing. Not currently exposed as a flexicon API; task **A3** (`AbortSession()`) is planned but demoted below Track B. |
| `undoable=True` (4.3.0 today) | **None reliably** — no per-operation envelope exists yet (#237 open); a single unbracketed setter like `SetGloss` can be refused outright by LCM. | Same `Rollback(0)`, same session-wide caveat; `Transaction()`'s docstring is explicit today that neither mode is atomic (`UndoableOperation()` docstring, `FLExProject.py:632-642`). |
| `undoable=True` (post-B1) | Per-operation, now that `transaction.py` is rewritten on `UndoableUnitOfWorkHelper` (**task B1 LANDED, unreleased**). `RollBack=true` is the ctor default and `Dispose()` reverts via `Rollback(0)` when set (tasks.md "O1 RESOLVED"). | Genuine per-operation rollback — the first mode in which "rollback" means what the word implies. |

**Domain seat's guidance on `FP_ConflictingSaveError` (Q4), carried
verbatim:** catching it means **full stop and re-open** — abandon the run
and re-open the project fresh (replaying only the unapplied portion), or
close without saving and reconcile manually in FLEx's own UI — **never an
automatic retry loop**. A caught `FP_ConflictingSaveError` means real
object-level data collided per `ChangeReconciler.OkToReconcileChanges`, not a
spurious lock; retrying without addressing the underlying concurrent edit
will fail again.

| | 4.3.0 today | Post-Track-B |
|---|---|---|
| `ui=` injection | Landed (#238). | Unchanged. |
| `FP_ConflictingSaveError` canonical import | `flexicon.code.exceptions` / `flexicon` package root. | Unchanged. |
| `RollbackToMark` | Does not exist; never did. | Still does not exist — B1 uses `Rollback(0)` via `UndoableUnitOfWorkHelper.Dispose()`, not a mark-based API. |
| Real revert primitive | `Rollback(0)`, session-wide, exposed as `AbortSession()` (task A3, landed not released); reopens the envelope, so it is repeatable. | `Rollback(0)`, per-operation scope, exposed transparently via B1's `_TransactionCM.__exit__`. `AbortSession()` deliberately refuses here — see task A3 / D8. |

---

## 6. `CreateField` preconditions

**Confirmed defect (per the REVISED draft, `reviews/cycle2-createfield-revision.md`,
superseding the original `cycle2-createfield-issue.md` where they disagree):**
`CustomFieldOperations.CreateField` (`flexicon/code/System/CustomFieldOperations.py:280-326`)
raises `FP_TransactionError` on **both** of its possible code paths in
v4.3.0. There is no reachable project state in which it returns successfully
today.

1. A guard at `:300-301` reads `ActionHandlerAccessor.CurrentDepth` and
   raises if `> 0`. Under the default `undoable=False`, `CurrentDepth` is 1
   for the entire `OpenProject()`...`CloseProject()` lifetime (§1/§4 above),
   so this guard **always** fires.
2. Even in a hypothetical state where `CurrentDepth == 0`, execution falls
   through to an **unconditional** second raise at `:320-326` — a stub, not
   a second guard — whose own message says "not yet implemented for the
   no-UoW path."

**Carry this correction verbatim, in bold, per instructions:**

> **Per-operation UoWs unblock only the PRECONDITION; the unimplemented
> no-UoW path means CreateField still raises post-Track-B.** Landing Track B
> (per-operation brackets) only makes it possible for `CurrentDepth == 0` to
> hold between operations — it satisfies guard 1. It does **not** implement
> the schema mutation behind guard 2. Until that separate, currently-stubbed
> work is written, `CreateField` will still raise
> `FP_TransactionError("CreateField is not yet implemented for the no-UoW
> path...")` on every call, in every mode, even after Track B ships.

**The guard's stated *rationale* was refuted, but the guard itself was not.**
liblcm fact **F6** refutes the in-code comment/error text at
`CustomFieldOperations.py:288-289` and `:305-306`, which claims schema
mutation inside an open data UoW "raises InvalidOperationException at
UndoStack.CheckNotProcessingDataChanges." Per **F6**:
`LcmMetaDataCache.AddCustomField` (`LcmMetaDataCache.cs:920-965`) never
touches `UnitOfWorkService`/`CurrentProcessingState`/
`CheckNotProcessingDataChanges` (zero grep hits across the whole file), and
liblcm's own test suite mutates schema successfully **inside** an open
undoable UoW (`LexEntryTests.cs:825-828` → `:1075` `MakeCustomProperty` →
`:1078` sets a value on the new flid → `:924` asserts it survives). The
guard's stated mechanism is wrong. **This does not mean the guard should be
removed** — the real hazard it gestures at (the "ghost flid" problem: raw
`AddCustomField` skips `RegisterObjectAsModified`, so `SetValue` against the
new field can reference a flid never registered as part of any object's
modified set, risking corruption-on-reopen per issue #21) may still justify
keeping some guard. Whoever fixes this needs to re-derive the actual
constraint rather than reusing the current (refuted) comment.

**Known-correct implementation path exists — this is implementable work, not
an architectural wall.** liblcm's own production code already contains the
reference sequence: `FieldDescription.UpdateCustomField()`
(`liblcm/src/SIL.LCModel/FieldDescription.cs:336`) — for a new field, calls
`mdc.AddCustomField(...)` (`:406`), then `mdc.UpdateCustomField(...)` (`:407`),
then, for value types, iterates every instance and calls
`uowService.RegisterObjectAsModified(obj)` (`:411-413`) — this last step is
exactly what bare `AddCustomField` skips and what closes the ghost-flid gap.
`FieldDescription.cs` itself calls no UoW helper — the caller is expected to
supply one, most plausibly `NonUndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW`.
Schema persistence rides the ordinary commit/save cadence via `BackendProvider`
(`BackendProvider.cs:799`, `:929`), not a synchronous write inside
`AddCustomField` itself.

**Issue draft:** `specs/write-path-transactions/issues/createfield-always-raises.md`
(revised; not yet filed via `gh issue create` — command drafted, marked NOT
RUN).

| | 4.3.0 today | Post-Track-B |
|---|---|---|
| `CreateField()` under `undoable=False` | Always raises (guard 1 fires — `CurrentDepth` is 1 all session). | Unaffected by Track B directly (this mode's envelope is unchanged by B1/B2). |
| `CreateField()` under `undoable=True` | Always raises (guard 1 may pass, but guard 2's stub always fires). | **Still always raises** — Track B unblocks guard 1's precondition only; guard 2's schema-mutation implementation is separate, unstarted work. |
| Guard's stated rationale | Present and refuted per F6 (cites a mechanism `AddCustomField` never invokes). | Unchanged unless a separate fix rewrites the comment per the ghost-flid rationale. |
| Workaround | Create custom fields via the FLEx UI (Tools > Configure > Custom Fields); populate values via the wrapper afterward. Accurate and current per `docs/CUSTOM_FIELDS.md`. | Same workaround remains necessary until the schema-mutation implementation lands. |

---

## What `undoable=False` guarantees, and does not

**Guarantees:**
- Unbracketed single-call mutations (`SetGloss`, `Delete`, etc.) work,
  because the whole session already sits inside one open
  `BeginNonUndoableTask()` — LCM never sees a "no active task" state to
  refuse.
- All accumulated changes are written to disk on a clean `CloseProject()`
  (`IUndoStackManager.Save()`, `FLExProject.py:298-300`).
- `Transaction()` still labels and nests writes for readability, and
  correctly no-ops on nested entry (no double-open hazard).

**Does not guarantee:**
- Any rollback narrower than the whole session (§5 — no `RollbackToMark`
  exists, and the one real primitive, `Rollback(0)`, is session-wide). It is
  now exposed as `FLExProject.AbortSession()` (task **A3**, landed but not
  released), which discards the whole session's uncommitted work and reopens
  the envelope so the session stays usable.
- Any save before `CloseProject()` (§2 — the FSM never returns to
  `ReadyForBeginTask` mid-session, so `SaveOnIdle`'s gates never clear).
  **Concretely: `SaveChanges()` cannot succeed in this mode.** It reaches
  `CheckReadyForCommit("Commit at wrong place.")`, raises a raw
  `System.InvalidOperationException`, and — per `UndoStack.cs:239-246` —
  rolls back the open bundle on the way out, discarding the session's
  uncommitted work. Verified live during A3. Do not call it under
  `undoable=False`; use `CloseProject()`, which ends the envelope first.
- Safety in shared mode (see below — D3).
- Survival of a mid-run crash (§2 — total loss, nothing was ever committed).

---

## Shared-mode position (spec.md D3)

**Decision D3, endorsed by the domain seat (Q2):** `undoable=False`'s
session-long non-undoable envelope is exactly the structure
`ChangeReconciler`'s undo-stack-based reconciliation machinery cannot
revert, and it maximizes the unsaved/conflict window to the entire run. The
domain seat concurs without reservation and frames the risk in linguist
terms: a colleague working alongside a headless script in Send/Receive mode
has no way to know their own unsaved edits sit exposed to a conflict
footprint that grows for the run's entire duration.

**The domain seat's recommendation, carried as a recommendation, not a
shipped enforcement:** shared-mode-safe operation should be promised **only**
under `undoable=True` with per-operation brackets (D2/B1/B2 landed).
`undoable=False` should be **prohibited** whenever a project may be open
elsewhere or under Send/Receive, and the domain seat is explicit that this
should be an **enforced precondition, not a documentation note**.

**Current state, stated plainly: this is NOT enforced in code today.**
Nothing in `OpenProject()` or elsewhere checks whether a project might be
shared, or whether another client has it open, before allowing
`undoable=False`. The one-shot warning added at `OpenProject()`
(`FLExProject.py:257-273`) documents the session-is-the-atomicity-unit
consequence, but it is advisory logging, not a precondition that can block
an unsafe call. FlexToolsMCP should treat this as its own responsibility
until flexicon adds enforcement (no task ID currently tracks this
enforcement work — recommend filing one alongside **DEF** in
`tasks.md` Checkpoint 3).

**Migration path to `undoable=True`:**

1. Land **B1** (`transaction.py` rewrite on `UndoableUnitOfWorkHelper`,
   deletes `_transaction_depth`, closes #233/#234/#236-for-undoable).
2. Land **B2** (per-operation brackets on the known unbracketed mutators —
   `LexSenseOperations.SetGloss`, `LexEntryOperations.SetLexemeForm`,
   `LexEntryOperations.Delete`, plus the B2s sweep for the rest) — gated on
   the **B2 shape** disagreement below being resolved first, since it
   determines what "bracket" means at each site.
3. Pass **B2t**, the end-to-end persistence test from #237
   (`undoable=True` → `SetGloss` → `CloseProject` → reopen → assert
   persisted). **LANDED** as
   `tests/operations/test_undoable_mode_live.py::TestPersistenceAcrossReopen`,
   together with the rest of the live `undoable=True` coverage DEF was
   gated on (33 live tests). #237 is closed by it.
4. Only then does **DEF** (flipping the default to `undoable=True`) become
   viable, and it is itself a separate `needs_human`-gated public-API
   default change per `tasks.md` Checkpoint 3.

Steps 1-3 have landed (unreleased). Until **DEF** lands *and a release
cuts*, FlexToolsMCP should pass `undoable=True` explicitly rather than rely
on a future default flip — a version-pinned 4.3.0 install still has the
broken behavior #237 reported, and still defaults to `undoable=False`.

One caveat worth reading before switching: nested blocks **join** the
enclosing unit of work, so an inner block has no independent rollback. If
your generated code catches an exception from an inner block inside an
outer one, the inner block's partial writes commit with the outer. See
`docs/EXCEPTION_HANDLING.md`, "Atomicity Under `undoable=True`".

---

## Open disagreements — surfaced, not resolved

### 1. `RefreshFromDisk()`'s `writeEnabled` guard

- **Domain seat (Q3):** approves the guard as shipped. A read-only session
  never saves, so there is no open UnitOfWork to reconcile against in the
  first place — gating matches `SaveChanges()`'s existing precedent and
  avoids exposing a no-op on read-only sessions.
- **QC (P1 finding):** argues a read-only monitoring/reporting session on a
  shared project is a plausible caller this guard forecloses entirely. The
  method's stated purpose ("reconcile in-memory state with a foreign
  change") is broader than the auto-save-unblocking half the current
  justification argues; if `IUndoStackManager.Refresh()` is safe/meaningful
  outside an open UnitOfWork envelope, the guard may be unnecessarily
  restrictive.
- **Status: unresolved.** `FLExProject.py:591-592` raises `FP_ReadOnlyError`
  unconditionally when `not self.writeEnabled`, as shipped. FlexToolsMCP
  should not build a read-only monitoring feature on `RefreshFromDisk()`
  without first checking whether this position has changed.

### 2. B2 implementation shape — central dispatch-layer bracket vs. per-site brackets

- `lex-lead` provisionally resolved this for a **central** bracket at the
  `@OperationsMethod` dispatch layer.
- The dispatch-layer probe (**P1**-**P4**) then found: a central bracket is
  mechanically cheap and covers 267/294 (91%) of methods, and the descriptor
  can host a wrapping closure without breaking the existing class-level
  call path (**P2**) — but it pulls input validation *inside* the UoW.
  Sampled 12/12 domains are uniformly validate-then-mutate today (**P3**),
  which a central bracket would invert: every `_ValidateParam` failure and
  every read-only rejection would open an undo task, raise, and close it —
  an **empty named entry landing on the user's Ctrl+Z stack for a rejected
  input that changed nothing**. 100% of the sampled methods regress under
  this scheme. Separately, **50 of 174 (29%)** existing `_TransactionCM`
  call sites use argument-derived labels (e.g. `f"Create entry '{form}'"`)
  that a purely central, `func.__name__`-only bracket cannot reproduce —
  those degrade to generic method-name labels in the FLEx undo menu
  (**P4**).
- The probe's own recommendation is a **hybrid** (dispatch layer as a safety
  net gated on a first-mutation hook, plus ~50 label-bearing sites and all
  17 uncovered sites bracketed by hand) but flags its own weakest point: the
  hybrid depends on a first-mutation hook that does not exist in liblcm
  today, and if that hook proves unreachable (as `Transaction`'s
  rollback-on-mark API already did, issue #236), the hybrid collapses into
  "central bracket plus ~50-67 hand edits" — at which point bracketing all
  294 individually, while more labor, is fully auditable by grep and
  preserves label fidelity everywhere.
- **Status: OPEN.** This affects *when* per-operation UoWs (task **B2**)
  land, which FlexToolsMCP's own planning depends on for the migration path
  above. Do not assume a ship date for B2 until this shape question is
  settled.

---

## Task-ID cross-reference (from `tasks.md`)

| Task | What it delivers | Status as of this contract |
|---|---|---|
| A1a/A1b | `ui=` param + `HeadlessLcmUI`/`FP_ConflictingSaveError` | Landed |
| A1c | `FLExProject.OpenProject(..., ui=None)` passthrough | Landed |
| A1d | `HeadlessLcmUI` test coverage | Landed |
| A4 | `RefreshFromDisk()` | Landed (writeEnabled guard contested — see above) |
| A2a-A2e | Rollback-honesty pass (`Transaction()` docstrings, one-shot warning, `RollbackToMark` deletion, `EXCEPTION_HANDLING.md` atomicity section) | Landed |
| CB | Contract-baseline extension (`UndoableUnitOfWorkHelper`, `NonUndoableUnitOfWorkHelper`, `IActionHandler`, `ILcmUI`) | Landed and independently verified: `reviews/cycle2-verification.md` confirms 22 passed / 0 failed and that `TestTransactionLayerContract` runs in Mode 1 (checked-in baseline fixture, no live liblcm required) |
| MCP | This document | Delivered by this pass |
| B1 | `transaction.py` rewrite on `UndoableUnitOfWorkHelper` | Landed |
| B1t | Rollback/nesting regression tests for B1 | Landed (`tests/test_b1t_action_handler_double.py`, action-handler double; no live LCM write). **Superseded for coverage purposes** by `tests/operations/test_undoable_mode_live.py`, which re-proves the same claims against the real liblcm FSM — the doubles had encoded D9 |
| B2s | Sweep: full inventory of unbracketed mutators | Landed (`reviews/cycle1-explore-b2sweep.md`; 294, reconciled to 295 by B2g) |
| B2 | Per-operation brackets | Landed — shape RESOLVED **per-site** (decision D5); 11/11 domain batches, B2g ratchet baseline 295 -> 0 |
| B2g | Ratchet guard against new unbracketed mutations | Landed — now a permanent zero-tolerance guard, not a countdown |
| B2t | End-to-end persistence test, `needs_human` (scratch project) | **LANDED, not released** — `tests/operations/test_undoable_mode_live.py::TestPersistenceAcrossReopen`; closes #237. Runs on a tempdir copy of the Target `.fwbackup`, never the real project |
| DEF-COV | Live `undoable=True` coverage (the DEF blocker) | **LANDED, not released** — `tests/operations/test_undoable_mode_live.py`, 33 live tests. Reintroducing D9 turns 19 of them red, on observed data loss across a `CloseProject()` boundary rather than on call-shape assertions |
| B3 | Fix `Undo()`/`Redo()` | Landed. Recording the in-process-only scope caveat on #235 is still open (task CO1) |
| A3 | `AbortSession()` (`Rollback(0)`) | **LANDED, not released** — `undoable=False` primitive; returns `False`/raises under `undoable=True` (D8) |
| DEF | Flip default to `undoable=True` | PLANNED, `needs_human` — public-API default change. Its **coverage** blocker is cleared (DEF-COV/B2t above); what remains is the human decision itself |
| B4 | `flexicon.CAPABILITIES` frozenset | Landed — all four tokens; two are mode-dependent (see §3) |
| (unfiled) | Enforce D3 (block `undoable=False` in shared mode) as a precondition | PLANNED, **no task ID assigned yet** — recommend filing alongside DEF |
| (separate from B1/B2) | Implement `CreateField`'s actual schema mutation | PLANNED, **no task ID assigned** — tracked only in the issue draft, not in `tasks.md` |
