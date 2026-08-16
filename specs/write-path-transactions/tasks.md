# TASKS — write-path-transactions

Derived from `spec.md` §9 (Sequencing). Authoritative order; do not reorder without
recording a decision in `spec.md`.

Issues covered: #233 #234 #235 #236 #237 #238 + A4 (unfiled).

---

## Checkpoint 1 — Track A complete (live path)

Everything here is reachable by FlexToolsMCP today under `undoable=False`.

- [x] **A1a** `FLExLCM.OpenProject(projectName, ui=None)`, defaults to `FwLcmUI`.
- [x] **A1b** `flexicon/code/headless_ui.py` — `HeadlessLcmUI(ILcmUI)` +
      `FP_ConflictingSaveError`. Verified live via pythonnet (real .NET type,
      `isinstance(ui, ILcmUI)` True, all 10 methods + 2 properties exercised).
- [x] **A1c** `FLExProject.OpenProject(..., ui=None)` passthrough to `FLExLCM.OpenProject`.
- [x] **A1d** Tests: 12-member unit coverage of `HeadlessLcmUI`; regression asserting
      `ui=None` still constructs `FwLcmUI`.
- [x] **A4** `FLExProject.RefreshFromDisk()` wrapping `IUndoStackManager.Refresh()`.
      Without it one foreign FLEx save wedges auto-save for the rest of the session
      (`UnitOfWorkService.cs:245`). Affects BOTH modes.
- [x] **A2a** Delete `_GetTransactionAPI` `RollbackToMark` discovery
      (`FLExProject.py:470-524`) — the API does not exist in liblcm.
- [x] **A2b** Correct the fictional three-candidate docstring at `FLExProject.py:474-482`.
- [x] **A2c** `Transaction()` honesty pass — see **D4** below (name retained;
      mode-dependent semantics stated plainly).
- [x] **A2d** Move the per-transaction WARNING to a single one-shot warning at
      `OpenProject` time.
- [x] **A2e** `docs/EXCEPTION_HANDLING.md`: under `undoable=False` the atomicity unit is
      the **session**; a mid-operation exception leaves prior mutations applied.
- [x] **CB** Contract-baseline extension (`tests/contract/snapshots/liblcm_baseline.json`)
      covering `UndoableUnitOfWorkHelper`, `NonUndoableUnitOfWorkHelper`,
      `IActionHandler`, `ILcmUI`. Must land **before** B1.
- [x] **MCP** `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md` — written contract FlexToolsMCP can
      build on: what `undoable=False` guarantees, what it does not, the shared-mode
      prohibition (D3), and the migration path to `undoable=True`.

**Checkpoint:** Track A green — COMPLETE. Landed on `main` (not pushed) as
`b3a5bb9` (impl, closes #236 #238), `17a8740` (contract baseline), `7404163` (docs).

---

## Checkpoint 2 — Track B core (`undoable=True` correctness)

Per **D3** this is the critical path for interactive shared-mode use, not follow-up.
Shape of B2 fixed by **D5** below (per-site, all 294).

### Checkpoint 2a — engine — COMPLETE

Landed on `write-path-transactions-b1-b3`: `1dfc464` (B1, B3), `b996d89` (B2g),
`3d4fdc9` (B1t + verification). Offline gate per **§7.0**: `117 failed, 1424 passed,
11 skipped, 322 deselected, 17 errors` — +30 passed vs. baseline, zero regressions;
the 117 are pre-existing and unrelated (#240 rename path, sync engine).

- [x] **B1** Rewrite `transaction.py` on `UndoableUnitOfWorkHelper`; delete
      `_transaction_depth` outright (kills #234 by construction). Use the liblcm nesting
      idiom verbatim: `if actionHandler.CurrentDepth > 0: task() else: Do(...)`.
      Closes #233, #234, #236-for-undoable. **174** `with self._TransactionCM(...)` call
      sites across the tree must keep working unchanged. Does **not** close #237 — that
      needs B2 + B2t.
- [x] **B3** `Undo()`/`Redo()` on `cache.ActionHandlerAccessor`, gated on
      `CanUndo()`/`CanRedo()`. Delete the dead `if undo_stack is None` and `else`
      branches at `FLExProject.py:719-733` and `:765-779`. Close #235 as
      **in-process-only**, recording that scope caveat on the issue.
- [x] **B1t** Offline tests: nesting join-vs-open, inner-CM raise leaves no residual
      depth, double-`BeginUndoTask` guard. Uses an action-handler double; **no live
      LCM write**. Landed as `tests/test_b1t_action_handler_double.py` (30 tests);
      all 6 required properties independently verified — `reviews/cycle3-verification.md`.
- [x] **B2g** Ratchet guard: AST mutator scan as a pytest with a frozen baseline, so the
      294 can only shrink and no 295th can be added unnoticed. Makes D5 enforceable.

### Checkpoint 2b..2n — the sweep (later spurts, batched by domain)

- [x] **B2s** Sweep inventory complete: `reviews/cycle1-explore-b2sweep.md` (294 methods).
- [x] **B2** Bracket all 295 per **D5**. Batched by domain, one commit per batch, guard
      baseline ratcheted down each time. **COMPLETE: 11/11 batches landed; baseline
      295 -> 0.**
      - [x] 1/11 Reversal 6 (`4d3add6`)      - [x] 2/11 Shared 9 (`5880d8d`)
      - [x] 3/11 Scripture 9 (`e9f31e2`)     - [x] 4/11 System 11 (`6144970`)
      - [x] 5/11 Lists 14 (`fff961f`)        - [x] 6/11 code-root 14 (`e24cffa`, `db1dff7`)
      - [x] 7/11 Discourse 21 (`d2dfdfe`)
      - [x] 8/11 TextsWords 24               - [x] 9/11 Notebook 44
      - [x] 10/11 Grammar 59   - [x] 11/11 Lexicon 84
      Includes the 17 residual hand sites (8 catalog-chain private helpers, 6
      `FLExProject` methods, 3 undecorated `CatalogBackedMixin` publics) that no scheme
      covers mechanically. Batch 7 absorbed two of the catalog-chain helpers
      (`__GetOrCreateChartMarkers`, `__GetOrCreateDiscourse`) — both run *before* their
      `Create`'s own bracket is entered, so the bracket goes in the helper.
      Batch 9 absorbed three more mirror-image private helpers
      (`NoteOperations._DuplicateReplyInto`,
      `LocationOperations._DuplicateSublocationInto`,
      `AnthropologyOperations._DuplicateSubitemInto`,
      `DataNotebookOperations._DuplicateSubRecordInto`) plus one genuinely
      unbracketed mutation that no batch had covered:
      `AnthropologyOperations.Create` left its `AnthroListOA` list creation
      outside *any* transaction. See **D6**.
      Batch 8's one private helper is the mirror image: `SegmentOperations.
      __MigrateTranslations` is called from *inside* `MergeSegments`' existing
      "Merge segments" bracket, so its mutations were already covered at runtime and
      the added bracket merely joins that transaction (nesting-aware per B1). It is
      stated anyway so the site is `grep`-auditable per D5 and no future caller can
      reach it unbracketed.
      Batch 10 absorbed the remaining catalog-chain private helpers on the Grammar
      side: `_factory_create_attached` / `_path_b_attach` on both POSOperations and
      PhonFeatureOperations and InflectionFeatureOperations, plus `_CreateValueFromEntry`
      and `__OverlayCanonicalLabels` on the two feature classes. Unlike batch 7's pair,
      all of these are reached from *inside* the mixin's own
      "Create ... from catalog" bracket (`Shared/catalog_backed.py:481`), so their
      brackets join rather than open — stated anyway so the sites are `grep`-auditable
      per D5. Same for the five PhonologicalRuleOperations context helpers
      (`__ClearSequence`, `__CleanupSequenceContextMembers`, `__WireContext`,
      `__BuildSimpleContext`, `__PopulateSimpleContext`), all reached from inside
      "Wire phonological rule". `PhonemeOperations.__ApplyFeatures` was the one Grammar
      helper genuinely running outside any transaction — it gets real brackets.
      Count is 295, not the 294 of the cycle-1 table: the B2g scanner reconciled one
      site the sweep missed (`FLExProject.SetAudioPath`, code-root 13 -> 14).
      Batch 11 (final) covered the Lexicon domain: 29 LexSense, 16 LexEntry, 7 Example,
      7 Etymology, 6 LexReference, 5 Pronunciation, 4 Variant, 4 Allomorph,
      3 SemanticDomain, 3 MSA. Three shapes worth noting: the deep-copy pair
      (`LexSenseOperations._deep_copy_sense_to` / `__copy_sense_content`) is bracketed
      as ONE unit each rather than per-field, so a failure partway through cannot leave
      a half-populated duplicate; `MSAOperations.ChangeAffixVariant` takes three
      separate brackets after `__CreateAndAttach`'s own has committed (D6);
      and `LexSenseOperations.RemovePicture` keeps the optional physical-file
      deletion OUTSIDE the bracket, since the LCM cannot roll back a filesystem
      unlink and a bracket around it would imply otherwise.
      With the baseline at 0, the B2g ratchet inverts meaning: it is no longer a
      countdown but a permanent guard, and `test_scanner_runs_and_finds_entries` was
      replaced by `test_scanner_is_functional` (a zero result is now the correct
      answer, so the old `len(scan()) > 0` assertion would fail *because* the sweep
      succeeded). The three ratchet tests themselves are kept, not deleted.
- [x] **B4** `flexicon.CAPABILITIES` frozenset, shipping the `per-operation-uow` token.
      Gated on B2 complete — contract §3 marks it PLANNED and the token must not appear
      before the capability is real. **DONE.** Ships all four contract §3 tokens
      (`ui-injection`, `refresh-from-disk`, `per-operation-uow`,
      `transaction-rollback`), each backed by a landed capability: A1a-A1c, A4, B1+B2,
      B1 respectively. Contract §3 rewritten from PLANNED to landed-but-unreleased,
      plus the stale B1/B1t/B2s/B2/B3 rows in its status table and the two `undoable=True`
      rows that still called B1 PLANNED. Guard test:
      `tests/write_path_transactions/test_capabilities.py` (6 tests). See **D7**.
- [x] **B2t** End-to-end persistence test from #237: `undoable=True` -> `SetGloss` ->
      `CloseProject` -> reopen -> assert persisted. **DONE.** The needs_human gate was
      lifted explicitly by the maintainer ("make it so -- we can't release untested
      software"), on the standing condition that no agent writes to a project that is
      not a throwaway: the new `target_sandbox_path` fixture hands over a tempdir copy
      of the Target `.fwbackup` and the test owns the open/close/reopen cycle, so the
      real Target is never opened. Landed as
      `tests/operations/test_undoable_mode_live.py::TestPersistenceAcrossReopen`
      (4 tests) inside the wider **DEF-COV** suite below. Closes #237.
- [x] **DEF-COV** Live `undoable=True` coverage -- the blocker D9 recorded against DEF.
      **DONE.** `tests/operations/test_undoable_mode_live.py`, 33 live tests against a
      tempdir Target sandbox, covering the eight claims the mode makes: clean-block
      commit, real rollback, per-operation UoW, nesting-joins, Undo/Redo, the B2
      brackets under *this* mode, persistence across reopen, and a live pin on D9's
      pythonnet surface. Evidence: `evidence/live-def-undoable-coverage.md`.
      The suite is validated by mutation, not just by passing: reintroducing D9
      (`set_RollBack(...)` -> `helper.RollBack = ...`) turns **19 of 33 red**, and does
      so on observed data loss rather than on call-shape assertions. See **D10**, which
      also corrects an expectation that did not survive measurement.

**Checkpoint:** Track B core green -- COMPLETE.

---

## Checkpoint 3 — Close-out

- [x] ~~**B3**~~ Duplicate of the Checkpoint 2a entry (stale line numbers); B3 landed
      in `1dfc464`. Residual close-out work: record the **in-process-only** scope
      caveat on #235 — tracked under **CO1** below.
- [x] **CO1** Close #235 with the in-process-only scope caveat recorded on the issue
      (`Undo()`/`Redo()` drive the live `ActionHandlerAccessor`; they do not reverse
      changes already committed to disk by a prior session). **DONE.** The
      `needs_human` gate on the outward-facing write was lifted by the maintainer
      ("finish the tasks this time"). Comment posted and issue closed as completed:
      MattGyverLee/flexicon#235 (`issuecomment-5307881281`). The comment records the
      `ActionHandlerAccessor` + `CanUndo()`/`CanRedo()` fix, states the caveat, and
      cites the live evidence: `test_undoable_mode_live.py::TestPersistenceAcrossReopen::
      test_undo_stack_does_not_survive_reopen` shows a committed write persisting while
      `CanUndo()` reads False on the reopened project, and
      `TestUndoRedoLive` covers the in-session Undo/Redo round trip. Before posting,
      the fix's three public claims were re-verified against the source: no
      `self.project.UndoStack` reference survives anywhere in `FLExProject.py` (the 12
      remaining `UndoStack` hits are `IUndoStackManager` or C# citations in comments),
      and both methods gate on `CanUndo()`/`CanRedo()` with the dead branches deleted.
- [x] **A3** `FLExProject.AbortSession()` -> `IActionHandler.Rollback(0)`. Demoted below
      Track B. Must document the **O2 catch**: `Rollback` leaves the FSM in
      `ReadyForBeginTask`, so in `undoable=False` it terminates the session envelope and
      must either reopen `BeginNonUndoableTask()` or be documented as terminal.
      **DONE.** Takes the *reopen* branch (see **D8**), so the abort is non-terminal and
      repeatable. Guards: read-only -> `FP_ReadOnlyError`; nothing open (`CurrentDepth == 0`,
      the exact precondition `Rollback` checks) -> `False` rather than a raw
      `InvalidOperationException`; `undoable=True` with a block open -> `FP_TransactionError`
      rather than rolling back underneath the owning helper. Tests:
      `tests/write_path_transactions/test_a3_abort_session.py` (14 offline) and
      `tests/operations/test_abort_session_live.py` (12 live).
      Evidence: `evidence/live-a3-abort-session.md`.
      **A3's live run also found and fixed a critical pre-existing B1 defect — see D9 —
      and found a second pre-existing defect in `SaveChanges()`, recorded not fixed.**
- [x] **DEF** Flip the default to `undoable=True` (D3). Gated on Checkpoint 2 green.
      **DONE.** The `needs_human` gate was lifted by the maintainer ("finish the tasks
      this time"); the coverage blocker had already been cleared by **DEF-COV** + **B2t**.
      `FLExProject.OpenProject(..., undoable=True, ...)` is now the signature default;
      the legacy mode requires an explicit `undoable=False`, which still emits the
      one-shot A2d warning (reworded — it now names the caller's opt-out rather than
      describing an unavoidable limitation). Evidence:
      `evidence/live-def-default-flip.md`. The two caveats recorded here before the
      flip both survive it and are now documented at the `OpenProject` docstring, in
      `docs/EXCEPTION_HANDLING.md`, and in the CHANGELOG entry:
      (a) nested blocks JOIN, so an inner block has no independent rollback — callers
      who catch an inner exception inside an outer block get the inner's partial writes
      committed (pinned by
      `test_inner_exception_caught_inside_the_outer_block_still_commits`);
      (b) `AbortSession()` becomes a near-no-op for anyone who was relying on it, since
      it refuses inside a block and returns `False` outside one (D8).

      **Two things the flip changed that this entry did not predict, both found by
      running the live suite unpinned before deciding anything — see D11 and D12:**
      - **D11** — it exposed a genuine unbracketed mutation site that B2's 295-site
        sweep had missed, `BaseOperations.ApplySyncableProperties` (writes live in the
        module-level helper `_apply_props_loop`, which no per-*method* scheme reached).
        Latent under `undoable=False`, a hard `InvalidOperationException: Not in the
        right state to register a change.` under the new default. Fixed here with a
        bracket; a sweep for the same shape across `flexicon/code/` found exactly one
        other module-level writer, `lcm_casting.clone_properties`, and confirmed all
        seven of its call sites are already inside a caller's bracket.
      - **D12** — three conftest fixtures (`target_project`, `target_sandbox`,
        `sena3_sandbox`) opened with the *implicit* default, so the flip silently
        converted them to `undoable=True` and collapsed the mode distinction the suite
        is built on. Pinned to `undoable=False` explicitly.

---

- **D6 — A mutation deliberately hoisted *out* of a transaction still needs a
  transaction of its own. RESOLVED (batch 9).** `AnthropologyOperations.Create`
  resolved `AnthroListOA` before opening its per-item bracket, with a comment
  explaining that a missing list must not leave an orphaned `ICmAnthroItem`. That
  reasoning is right about *ordering* and wrong about *coverage*: it left
  `list_factory.Create()` and the `AnthroListOA` assignment inside no unit of work
  at all, which `undoable=True` rejects outright. Resolution: keep the hoist, give
  the hoisted work its own named bracket ("Create anthropology list"), and leave
  the `is None` guard outside both so an already-initialised list stays a true
  no-op. Generalises to any future "resolve before the transaction" hoist —
  *before* must mean *in an earlier transaction*, never *in none*.

## Resolved open questions

- **O1 RESOLVED** (`UnitOfWorkHelper.cs`): ctor sets `RollBack=true` (:31); `Dispose`
  calls `RollBackChanges()` when set (:115-116), delegating to
  `m_actionHandler.Rollback(0)` (:137). `RollBack` is `{private get; set;}` — write-only
  from outside, so never read it back. B1's rollback claim holds.
- **O2 RESOLVED WITH CATCH** (`UndoStack.Rollback(int)`): ignores `nDepth`, requires
  `CurrentProcessingState == ProcessingDataChanges` (else throws), rolls back
  `m_currentBundle`, leaves the FSM in `ReadyForBeginTask`. See A3.
- **O3 STILL OPEN** (`DiscardToMark`): discards undo records vs reverts data —
  unverified. **Do not build on it.** Current reading: it discards history only, and
  `Rollback` is the sole true revert.

## Decisions added after spec.md

- **D4 — `Transaction()` keeps its name.** `spec.md` A2 preferred a rename
  (`OperationGroup`). That preference predates D3. Once B1 lands,
  `Transaction()` becomes genuinely transactional under `undoable=True` — the mode D3
  designates as the destination — so renaming it away would make the name wrong exactly
  where it is right. Take the alternative A2 explicitly permits: keep the name, and state
  mode-dependent semantics plainly in the docstring plus a one-shot `OpenProject`
  warning when `writeEnabled and not undoable`. Revisit only if QC/domain dissent.

- **D5 — B2 bracket shape: PER-SITE, all 294. RESOLVED (cycle 3).** Reverses the
  provisional cycle-2 preference for a central bracket at the `@OperationsMethod`
  dispatch layer. Evidence: `reviews/cycle2-explore-dispatch-layer.md`.

  *Why the central bracket lost:*
  1. **P3 is dispositive.** 12/12 sampled methods across 12 domains are strictly
     validate-then-mutate, zero interleave — the exact discipline
     `BaseOperations.py:1784-1787` instructs and the codebase actually keeps. A
     dispatch-layer bracket pulls `_EnsureWriteEnabled`/`_Validate*` *inside* the UoW,
     so every rejected input opens an undo task, raises, and closes it. Under B1 that
     is not merely an empty named entry on a linguist's Ctrl+Z stack — with
     `UndoableUnitOfWorkHelper` it also fires a real `Rollback(0)`. 100% of the sample
     regresses, and it is fixable only by hoisting validators out of 294 method
     bodies, which is the per-site edit cost we were trying to avoid.
  2. **P4 label fidelity.** 50/174 (29%) existing sites use argument-derived labels
     (`f"Create entry '{form}'"`). A central `func.__name__` bracket degrades the FLEx
     undo menu to `LexEntryOperations.Create`. That menu is product surface a linguist
     reads; the existing 174 sites are the codebase's own evidence that per-site,
     argument-derived labelling is the house convention.
  3. **The hybrid is unbuildable as specified.** It needs a "first mutation" hook that
     does not exist in liblcm. We have already been burned once assuming an unverified
     API existed (`RollbackToMark`, #236). Not twice. The probe concedes that if the
     hook is unreachable the hybrid collapses to "central + ~50-67 hand edits".
  4. **P2 generators.** 48 decorated methods contain a top-level `yield`; a
     dispatch-layer `with` exits before the generator's first frame runs. Latent today
     (overlap with the 294 is 0) but it makes correctness depend on "nobody ever
     writes a `yield`-based writer" across 1144 decorated methods.
  5. **Residual is nonzero under every shape** — 17 hand sites minimum. Central buys
     91% mechanical coverage with the wrong semantics *and still* needs handwork.

  *Honest cost of the choice:* 294 edits instead of ~17. Accepted, because each is a
  mechanical two-line change (indent body, add `with`), it is batchable by domain, it
  introduces no new concept a future maintainer must learn, and it is `grep`-auditable
  per site — which a central bracket is not. **B2g** makes that auditability a CI
  ratchet rather than a promise.

  *Reversibility:* per-site preserves the option. A central net can be added on top
  later (it would find `CurrentDepth > 0` and join). The reverse — retrofitting
  per-site labels and validator hoists under a shipped central bracket — is not
  cheaply reversible. Choose the option that keeps options.

  *Not adopted from the probe:* its hybrid recommendation. Adopted instead: its own
  stated fallback, which it correctly calls "more honest, fully auditable by grep, and
  preserves label fidelity everywhere."

- **D7 — `CAPABILITIES` ships all four tokens and describes the BUILD, not the
  session. RESOLVED (B4).** Contract §3's table said `transaction-rollback` is
  "`undoable=True` only; `undoable=False` never sets this token" — which presumes a
  mode-aware set. A module-level frozenset cannot vary by mode, and the same tension
  applies to `per-operation-uow`, which tasks.md nonetheless mandates B4 ship.

  Resolved by making the token mean *"this build implements the capability"* rather
  than *"the capability is active in your session"*, and stating the mode dependence
  in three places: the `flexicon/__init__.py` docstring, contract §3, and the existing
  one-shot `OpenProject()` warning (**A2d**) at the boundary where the mode is chosen.
  That is precisely the shape constitution V permits — "where a guarantee is
  mode-dependent, state the mode dependence plainly at the call site's docstring and
  warn once at the boundary where the mode is chosen" — so reporting a mode-dependent
  token is honest, and withholding one the build genuinely implements would instead
  make the probe under-report.

  *Rejected:* (a) shipping only the two unconditional tokens, which would leave
  FlexToolsMCP unable to detect B1+B2 at all — the entire point of B4; (b) adding a
  mode-aware `FLExProject.capabilities` accessor, which honors §3's wording exactly
  but is API surface beyond B4's scope. (b) remains the clean answer if a consumer
  ever needs per-session granularity — see the concern recorded for **DEF**.

  *Also settled:* B4 is **landed, not released**. The contract now says so, matching
  the framing §2 already used for B1, because a version-pinned FlexToolsMCP install
  cannot see either until a release cuts.

- **D8 — `AbortSession()` reopens the envelope rather than being terminal, and
  refuses under `undoable=True`. RESOLVED (A3).** The O2 catch left two options and
  tasks.md permitted either. Reopening wins on evidence, not taste: `Rollback(0)`
  sets the FSM to `ReadyForBeginTask` (`UndoStack.cs:724`), which *ends* the
  session envelope, and `CloseProject()` unconditionally calls
  `EndNonUndoableTask()`. Documenting the abort as terminal would therefore have
  left every abort followed by a broken close, and would have made the one real
  revert primitive a one-shot that costs you the rest of the session — a poor trade
  for a method whose whole purpose is recovering from a bad batch. Reopening makes
  it non-terminal, repeatable, and safe to call in an `except:` block.

  The second half is the `undoable=True` refusal. There, an open unit is always
  owned by an `UndoableUnitOfWorkHelper` (that mode opens no session envelope), so
  rolling back underneath it would leave the helper's `Dispose()` acting on a FSM
  already back in `ReadyForBeginTask` — raising a *second* exception out of the
  `with` block's exit and masking whatever the caller was handling. `FP_TransactionError`
  is the honest answer; the correct tool inside a block is to let the exception
  propagate, which rolls that block back by design. Consequence worth stating
  plainly: despite spec.md A3's "available in both modes", `AbortSession()` is in
  practice an `undoable=False` primitive — under `undoable=True` it returns `False`
  between operations and refuses inside them. That is the correct outcome, since
  per-operation rollback already covers that mode.

  *Rejected:* documenting the abort as terminal (breaks `CloseProject()`); rolling
  back regardless of mode (corrupts the owning helper).

- **D9 — pythonnet does not expose a `RollBack` property; `set_RollBack(...)` is the
  only path to .NET. RESOLVED (found during A3 live verification).** `RollBack` is
  `{private get; set;}`, and pythonnet synthesizes no property when the getter is
  private — it surfaces only `set_RollBack`. Critically, `helper.RollBack = False`
  does **not** raise: pythonnet accepts it as a plain Python attribute on the wrapper
  while the real field keeps its constructor default of `True`, so `Dispose()` rolled
  back **every** UnitOfWork, clean ones included. Under `undoable=True` every write
  was silently discarded. Both call sites now call `set_RollBack(...)`.

  This is the same failure shape already recorded in this feature's concerns for
  `ILexEtymology.LanguageRA`, and it is now a third instance of the same class —
  strong evidence it deserves a standing rule, not another one-off note: **a
  pythonnet attribute assignment that silently succeeds proves nothing; a write to a
  .NET object must be verified by reading the effect back through the LCM.**

  Two process lessons, both structural rather than incidental:
  1. **The offline doubles encoded the bug.** They modelled `RollBack` as assignable,
     so 30 tests passed against code that destroyed all data live. Doubles for
     pythonnet-wrapped types must model *pythonnet's* surface, not the C# source's.
     Both doubles now raise on the assignment form, plus a source-level guard.
  2. **Phase 2 had never been run against a live LCM.** Every landed live suite used
     `target_sandbox`, which is `undoable=False`. B1/B2 were marked complete on
     offline-double evidence alone for the mode they exist to serve. Hence the new
     `target_sandbox_undoable` fixture — **DEF must not be attempted until the
     `undoable=True` path has live coverage comparable to `undoable=False`.**
     *Discharged by DEF-COV* (`tests/operations/test_undoable_mode_live.py`).

- **D10 — A test suite that only asserts the FAILURE path cannot detect a
  roll-back-everything bug. RESOLVED (DEF-COV).** Reintroducing D9 turns 19 of
  DEF-COV's 33 live tests red. The 14 that survive are the tell — they are largely
  the ones asserting that a rollback *happened*, and a build that rolls back
  everything satisfies those perfectly. B1t had been built mostly out of that shape,
  because rollback was the interesting new behavior B1 introduced and the commit path
  looked like the boring control case.

  *Measured, not assumed:* the offline suite was expected to stay green under the
  same mutation and does not — it fails 14. D9's fix had also hardened both doubles
  to raise on the assignment form and added a source-level guard, so the suite that
  missed D9 no longer exists. The distinction that survives is about *what* is being
  asserted: the offline guards pin **how the code calls pythonnet**, which would not
  catch a different mechanism with the same effect, while the live tests observe
  **data loss**, including across a `CloseProject()` boundary that no double can
  model. Both are worth having; only the second is coverage.

  It was the opposite. Under `undoable=True` the commit path is the one carrying a
  silent, total-data-loss failure mode: a discarded write raises nothing, and every
  in-session read still returns the cached value, so the damage is invisible until
  someone reopens the project. Generalised rule for this codebase: **for any
  construct with a commit branch and a rollback branch, the commit branch needs the
  stronger test, and at least one test must survive `CloseProject()`** — an
  in-memory assertion cannot distinguish "written" from "written and then
  discarded". That is what `TestPersistenceAcrossReopen` is for, and why B2t
  belonged *inside* this coverage rather than queued after it.

  *Method worth reusing:* the mutation check itself. A coverage claim for a
  silent-failure bug should be stated as "reintroducing the bug turns N tests red",
  not as "N tests pass" — the second is true of the suite that missed D9 in the
  first place.

- **D11 — A per-*method* mutation sweep cannot see writes that live in module-level
  helpers. RESOLVED (DEF).** B2 bracketed 295 sites and B2g ratcheted the baseline to
  0, which read as "every mutation is now inside a unit of work". It was not.
  `BaseOperations.ApplySyncableProperties` validates and then delegates every one of
  its writes to `_apply_props_loop`, a **module-level function** — so the site the
  sweep enumerated (the method) contained no mutation, and the code that mutates was
  not a method at all. Under `undoable=False` this was invisible, because the session
  envelope covered it. The moment DEF made `undoable=True` the default it became a
  hard failure: `MultiUnicodeAccessor.set_String` raises
  `InvalidOperationException: Not in the right state to register a change.`

  Fixed by bracketing the call as one unit rather than per property — a partial sync
  that failed halfway would otherwise leave the target item with some fields updated
  and some stale, a state its callers cannot detect.

  *Swept, not assumed:* an AST pass over every module-level function in
  `flexicon/code/` looking for write-shaped calls outside a `_TransactionCM` found
  exactly two: this one and `lcm_casting.clone_properties`. All seven
  `clone_properties` call sites were checked individually and every one is already
  inside a caller's bracket ("Duplicate environment", "Duplicate phoneme",
  "Duplicate phonological rule", plus two internal recursions reached from those), so
  it joins rather than opens and needs no change. Two module-level writers, one gap,
  one fixed.

  *Generalises:* B2g's ratchet is a guard against *regression*, not a proof of
  *coverage* — it can only count sites its scanner's shape can see. Any future claim
  of the form "all N mutation sites are bracketed" should state the enumeration's
  blind spot. This one's was "writes reached through a non-method callee".

- **D12 — Flipping a library default silently reinterprets every fixture that relied
  on it. RESOLVED (DEF).** Three conftest fixtures — `target_project`,
  `target_sandbox`, `sena3_sandbox` — called `OpenProject(..., writeEnabled=True)`
  with no `undoable=`, so DEF converted them to `undoable=True` without a single
  line of test code changing. That collapsed them into `target_sandbox_undoable`,
  whose own docstring exists to say the two modes are different LCM state machines
  and that "a `undoable=False` fixture cannot stand in" — the converse holds just as
  hard, and the collapse broke every `AbortSession` / `CurrentDepth` / undo-stack
  assertion in the suite (12 failures in `test_abort_session_live.py` alone, all
  green again once pinned).

  Resolution: pin all three to `undoable=False` explicitly, with a comment saying
  the pin is deliberate. A fixture whose *identity* is a mode must name that mode.

  *Deliberate consequence, recorded so it is not mistaken for an oversight:* the
  broad live suite therefore keeps exercising `undoable=False`, and coverage of the
  new default rests on `test_undoable_mode_live.py` (33 tests, `target_sandbox_undoable`).
  That is a real coverage asymmetry and the honest follow-up from this task — but it
  is the *pre-existing* asymmetry, unchanged by DEF, and closing it means re-verifying
  ~400 tests against different atomicity semantics, which is its own task and not a
  default flip.

  *Method worth reusing:* the blast radius was measured by running the whole live
  suite **unpinned** first — deliberately letting the flip reinterpret the fixtures —
  and only then deciding what to pin. Pinning first would have produced a green suite
  that proved nothing, and D11 would have shipped undetected.

- **D13 — B2's "295/295, baseline 0" was a measurement of the scanner, not of the
  codebase. RESOLVED (DEF).** D11 found one module-level gap; pulling that thread
  found the general case. `scan_unbracketed_mutations.py` recognised a mutation in
  exactly two shapes: a call whose attribute is in a hardcoded `MUTATION_CALL_ATTRS`
  set, or an assignment to a property whose name ends `RA`/`OA`/`OS`/`RS`. Three
  whole classes of LCM write fell outside both:

  1. **Unsuffixed scalar property assignment** — `sense.ScientificName = ...`,
     `entry.HomographNumber = ...`, `ws.RightToLeftScript = ...`. ITsString,
     Unicode, bool, int and GenDate properties carry no ownership suffix, so none
     of them ever counted. **43 sites across 22 files.**
  2. **ISilDataAccess scalar setters** — `DomainDataByFlid.SetInt` / `SetObjProp`.
     Calls, so the property rule cannot see them; not in the call set either. Left
     `FLExProject.LexiconSetFieldInteger`, `LexiconSetListFieldSingle` and
     `LexiconClearListFieldSingle` unbracketed *beside* three siblings B2 did
     bracket, which is the tell that the sweep was name-driven rather than
     effect-driven.
  3. **LCM domain mutators that read as ordinary setters** —
     `ICmAgent.SetEvaluation`, which creates and rewires owned evaluation objects.

  All three are now bracketed, and all three shapes were added to the scanner, so
  the ratchet measures them from here. *Mutation-checked, per D10:* the extended
  scanner reports **39 unbracketed methods against the pre-DEF tree and 0 against
  the fixed one** — the guard fails when the bug is reintroduced, which the old one
  did not. `test_scanner_is_functional` grew assertions pinning the unsuffixed rule
  in both directions (flags unbracketed, ignores bracketed) plus a negative case for
  `self.Attr = ...`, which is Python wrapper state and must never count.

  *The generalisation, and it is the real lesson of this feature:* a mutation
  scanner built from a **list of names** measures the list. B2g's zero was true of
  its own definition and false of the codebase, and it stayed green through 295
  correct edits *and* 47 missing ones. An effect-driven check — does this method
  reach the LCM outside a unit of work — is what the ratchet was believed to be. The
  live `undoable=True` suite is the only thing that actually tests that property,
  which is why DEF found this and no offline gate ever could.

- **D14 — Tests that write raw LCM need their own unit of work, and a bare
  `except: pass` turns that into a mystery. RESOLVED (DEF).** ~20 live tests set up
  or tore down fixtures by writing through the LCM directly rather than through the
  wrapper — `parser_agent.SetEvaluation(...)`, `fs.FeaturesOC.Remove(feat)`,
  `DomainDataByFlid.DeleteObj(hvo)`, `possibilities.MoveTo(...)`,
  `entry.LexemeFormOA.Form.set_String(...)` — often deliberately, to stay independent
  of whatever the test was not testing. Under `undoable=False` the session envelope
  covered them for free; under the new default they raise. Each now takes an explicit
  `UndoableOperation("test: ...")`. Full site list in
  `evidence/live-def-default-flip.md` §4.4.

  This is a harness fix, not a library defect — the failing writes bypass the public
  API by design. It is recorded because the same hazard applies to **user** scripts
  that reach through to raw LCM, which is why the CHANGELOG entry and the
  `OpenProject` docstring both call it out.

  **The part worth remembering is how badly this misled the diagnosis.** Nearly every
  one of these sites sits inside `except Exception: pass`. The write raises, the
  except swallows it, and the failure resurfaces later in a *different* test as
  "a text with the name 'zz_split_test' already exists" or a canonical-GUID
  collision. And the swallowed write is **half-applied**: `LcmSet.Remove` takes the
  object out of the collection and *then* raises while registering the undo action,
  so the object is gone from `FeaturesOC` yet still live in the object repository
  with its GUID held. `_find_by_guid` returning `None` while `factory.Create(guid)`
  reports "identical GUIDs" looks like a contradiction, and it is really just the two
  halves of one interrupted write.

  That appearance produced a **wrong hypothesis, recorded here because it was
  believed and acted on**: that `undoable=True` keeps deleted objects on the undo
  stack and therefore reserves their GUIDs for the session — a design blocker with no
  cheap fix. A direct live probe (create → delete → inspect
  `ICmObjectRepository.TryGetObject` → recreate) refuted it in one run: the delete
  releases the GUID and the recreate succeeds. Re-running the probe with the *test's*
  raw removal instead of the wrapper's reproduced the failure exactly. Rule:
  **never theorise about LCM semantics from a symptom observed downstream of a
  swallowed exception — probe the write itself.**

  *Also found, and not a DEF regression at all:* 19 residual failures were `zz_*`
  objects left in **Sena 3** by earlier runs in this very session.
  `test_segment_operations.py` and the catalog suites open `Sena 3` through their own
  module `writable_project` fixture, not the Target, so `scripts/restore_target.py`
  never cleaned them. Any paired live measurement in this repo has to restore **both**
  projects, or it measures its own history.
