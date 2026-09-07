# CAMPAIGN QUEUE -- tier1-silent-data-loss

**Repo:** flexicon (`main`). **Started:** 2026-09-07.
**Scope:** the four Tier 1 (silent data loss / silent corruption) open issues.
**Driver:** ralph-loop in-session Stop hook + `/lex-lead` spurt mode.

This is a **campaign**, not a feature. Each queue item is its own feature with its
own `spec.md` / `tasks.md` / `STATUS.md` / `.crew-handoff.json` under its own
`specs/<slug>/` directory. This file is the campaign-level pointer: which item is
active, which are done.

## Completion condition

The campaign is complete -- and ONLY then may `<promise>TIER1 COMPLETE</promise>`
be emitted -- when all four items below are `done` with green gates and live
evidence on file.

**A per-feature `feature_complete` from lex-lead does NOT complete the campaign.**
When an item finishes: tick it here, advance `active` to the next item, and stop.
The loop re-enters on the next item. lex-lead's own
`<promise>FEATURE COMPLETE</promise>` token is deliberately NOT the campaign
promise, so it cannot exit the loop early.

## The queue (work strictly in this order)

| # | status | slug | issues | why here |
|---|--------|------|--------|----------|
| 1 | **`needs_human`** (CP-A closed; **CP-B/T3+T4 done and PASSED**; blocked at T6/T7 -- see the escalated `SaveChanges()` item under "Awaiting user approval") | `243-closeproject-save-guard` | #243 | Smallest diff, largest downside averted. Owner-confirmed total session loss: a run reported success, an immediate inventory saw all 11,987 new objects, a later open saw none, and `Target.fwdata` had been replaced by the crash-recovery copy -- one `[WARN]` line the only symptom. Orthogonal to items 2-4. |
| 2 | `queued` | `242-paragraph-whitespace` | #242 | Cheap, self-contained, real corruption. Paragraph/Segment text writers silently strip leading/trailing whitespace. |
| 3 | `queued` | `feature-structure-sync-gap` | #251 #252 #253 #256 | **Already in flight** -- contract frozen (C1-C8), live ground truth captured, spurt 1 done. RESUME, do not re-plan. Biggest item (T1-T17). Ships data loss today: `Allomorph` and `POS` are live sync object types. |
| 4 | `queued` | `250-writingsystem-activation` | #250 | Deliberately LAST: resolving it requires an **API-surface policy decision** (active-only `Exists` plus a separately-named whole-store predicate, vs. an `Ensure()` that activates a store-present WS). That is the item most likely to end `needs_human`, so everything landable unattended lands first. |

## Ordering rationale

Ordered by risk-averted / effort, with one override: the item carrying a likely
human decision is placed last so a `needs_human` stop cannot strand three
untouched items behind it.

## Per-item entry conditions

### 1. `243-closeproject-save-guard` (#243)

> **STATUS 2026-09-07 (end of spurt 4): `needs_human`. Do not resume this
> item autonomously except for T6.** CP-B is done and passed -- the P0 guard
> is landed and live-verified and P-3 is fixed 0/25 -> 25/25. But the owner's
> actual sequence (P-5) still measures **0/25**, and `spec.md` C14 found the
> guard makes that path *silent* where it previously raised. The remaining
> work (T7) is a public-behaviour change coupled to the still-unruled
> `SaveChanges()` depth guard, so **both must be ruled by the user together**
> -- see the escalated item under "Awaiting user approval" below.
> `specs/243-closeproject-save-guard/.crew-handoff.json` `blocker` is
> authoritative. Task order is now **T6 -> T7 -> T5**; T5 (CHANGELOG) is LAST.
> **T6 alone is pre-authorised** (probe-only, sandbox fixture, no `flexicon/`
> behaviour change) and sharpens the ruling itself.


**Spec+probe checkpoint DONE (spurt 1, 2026-09-07).** `spec.md` (contract
C1-C11), `tasks.md` (T1-T5) and `STATUS.md` are written;
`tests/operations/test_issue243_closeproject_probe.py` green with
`run_mode: live` on `target_sandbox_path`.

**CP-A1 / T1 DONE (spurt 2, 2026-09-07) -- first code landed under
`flexicon/code/`.** The P1 depth-read surface
(`_ReadActionHandlerDepth()`, `CurrentDepth` as a **property**,
`HasOpenSessionTask()`) is in `flexicon/code/FLExProject.py`: probe 6/6 green
with `run_mode: live`, offline suite 1290 passed (unchanged baseline), and
`git diff --stat flexicon/code/` = **120 insertions, 0 deletions, one file**,
so `CloseProject()` (T3) and `SaveChanges()` (the user-approval item below)
are provably untouched.

**CP-A2 / T2 DROPPED (spurt 3, 2026-09-07) -- CP-A is now CLOSED IN FULL, and
CP-B is UNBLOCKED.** T2 (delegate the three internal lenient depth reads to
T1's helper) was attempted at all three sites and each broke the offline suite
(`transaction.py:172` -> 9 failed, `undoable_operation.py:102` -> 2 failed,
`System/CustomFieldOperations.py:306` -> 2 failed). All were reverted: **spurt
3 changed zero lines of `flexicon/`** (`git diff f3a0f50 -- flexicon/` empty
and offline at `1290 passed`, both re-verified by `/lex-lead`). It is dropped
**on the merits and frozen as `spec.md` C12** -- the strict helper (raises
`FP_ProjectError`, returns depth verbatim, C5) and the three lenient sites
(coerce non-`int` to `0` for test doubles) want DIFFERENT contracts, so sharing
one implementation is a conflation, not a de-duplication; and the prescribed
`except` wrapper would swallow the `FP_ProjectError` the helper exists to
raise, which at `CustomFieldOperations.py:306` silently disables the issue-#21
corruption guard. **Do NOT re-attempt T2**; adding `spec=` to the doubles is
NOT deferred and NOT owed. Nothing in P0/P1/P2 depended on it.

**Resume from `specs/243-closeproject-save-guard/.crew-handoff.json` -- its
`next_entry` is authoritative: CP-B / T3, the P0 guard around
`CloseProject()`'s line-326 `EndNonUndoableTask()`, then T4's regression
tests.** Live gate for T3/T4 was RE-DERIVED FROM MARKERS this spurt (a defect
in the T2 brief: `test_transaction_rollback.py` was named as a live suite but
carries ZERO `requires_live_project` markers and collected 0 tests). Binding
set: probe (6 live) + `test_undoable_mode_live.py` (33) +
`test_target_live_smoke.py` (3), with `test_transaction_rollback.py` run
OFFLINE, plus the offline suite at 1290 passed.

Two further rulings were recorded in spurt 2 and must not be re-litigated:
**Q3 is CLOSED -- NO `flexicon.CAPABILITIES` token** (so `flexicon/__init__.py`
and `tests/write_path_transactions/test_capabilities.py` are out of scope for
every remaining task), and **new contract decision C11** freezes
`HasOpenSessionTask()`'s depth-read-before-mode-check ordering (C4 has no mode
carve-out, and `self._undoable` does not even exist on a never-opened
instance). Spurt 3 added **C12** (T2 dropped; the strict helper and the three
lenient internal sites keep separate depth reads permanently). **Q2**
(try/finally around the whole `CloseProject()` body) and **Q4** (CHANGELOG
wording) remain genuinely open, at T3 and T5 -- and Q2 is provably still open,
since spurt 3 changed no code at all.

Two cycle-1 findings changed the plan and must not be re-litigated:

- **The fix shape in the bullet below is WRONG (spec.md C1).** Reordering
  `Save()` before the End mirror is not viable -- `usm.Save()` itself raises
  `Commit at wrong place.` at `CurrentDepth > 0` and its failure collapses the
  envelope (depth 1 -> 0), so the swap trades one guaranteed raise for another
  with no save either way. The fix GUARDS the existing line-326 End call so its
  exception cannot skip line 332's `Save()`. The P0 bullet's original prose is
  retained below for historical record only.
- **P1 is a hard prerequisite of P0 (spec.md C6),** not a parallel ask -- the
  guard must read the depth before deciding whether to call
  `EndNonUndoableTask()` at all. `tasks.md` sequences T1-T2 before T3.

The owner-report discrepancies the probe surfaced (`Commit at wrong place.`
provenance, and the `.fwdata` file swap) were **ruled and CLOSED** as spec.md
C9/C10 -- the incident is a P-5 -> P-3 chain that the frozen guard breaks, and
the file swap is outside flexicon's fix surface. No owner input is needed and
no task may wait on owner repro steps.

Scope discipline -- the issue thread contains a self-correction by the owner. The
originally-reported root cause (rollback destroying the session envelope) was
**withdrawn**; the real trigger was the 4.4.0 `undoable` default flip, already
fixed consumer-side by passing `undoable=False`. Do NOT re-litigate that. The
three things the owner says still stand are the scope:

- **P0:** `CloseProject()`'s `EndNonUndoableTask()` is unguarded and runs *before*
  `usm.Save()`. Any exception in that bookkeeping mirror costs the whole session's
  data. Order `Save()` before -- or independently of -- the `End` mirror.
- **P1:** expose a task-depth read (`HasOpenSessionTask()` / `CurrentDepth`).
  `_NestingAwareTransaction` already reads `ActionHandlerAccessor.CurrentDepth`
  internally; expose that same read so external callers can follow the
  "ask LCM's own state, never track it ourselves" rule. Without it, both possible
  caller-side recoveries corrupt in opposite directions.
- **P2:** a prominent release note for the 4.4.0 `undoable` default flip -- a
  silent behavioural change that fails later, at the first checkpoint, with a
  message pointing nowhere near `OpenProject`.

### 2. `242-paragraph-whitespace` (#242)

No spec exists yet. **Checkpoint 1 = spec + a live probe that measures what is
actually stripped**, on which writers, and whether any caller depends on the
stripping (it may be load-bearing for the FLEx null-marker path -- check
`Shared/string_utils.normalize_text` before changing behaviour).

### 3. `feature-structure-sync-gap` (#251 #252 #253 #256)

RESUME from `specs/feature-structure-sync-gap/.crew-handoff.json`. Its
`next_entry` is authoritative: **T1 ALONE** first -- add the 13 feature-struct
owner classes to `lcm_casting._interface_cache`, enumerate the behaviour delta for
every `cast_to_concrete` / `_GetTypedOwner` caller, and get the full offline suite
plus the NC/Phoneme live tests green BEFORE starting T2. Every other task depends
on it. Honour the frozen contract C1-C8; do not reopen settled rulings D1-D5.

The `deferred` array in that handoff json lists items marked
**"needs USER APPROVAL to file"**. Do NOT file those issues inside the loop.
Collect them under "Awaiting user approval" below instead.

### 4. `250-writingsystem-activation` (#250)

No spec exists yet. **Checkpoint 1 = spec + the API-surface options paper, then
hand off `needs_human` with the decision stated in one line.** Do not pick the
surface unilaterally: the issue thread documents that `Exists` is the *only*
tag-normalized whole-store lookup in a codebase that is otherwise uniformly
active-only exact-case `GetAll()`, so the fix changes a published contract.

Two independent routes into the same silent skip must both be covered by whatever
surface is chosen: **store-vs-active** and **case/separator normalization**
(`Exists('EN')` is live-confirmed True while `'EN' in <active ids>` is False).

## Hard rules for every iteration

1. **Live verification is REQUIRED** for anything touching an Operations class, a
   factory call, a property setter, `FLExProject`, or the transaction/write path
   (CLAUDE.md). Mock-only is `FAIL: unverified`, never a clean result.
2. **Prefer the `target_sandbox` fixture** (write-enabled tempdir copy of the
   Target `.fwbackup`) for every write-path test. Nothing can leak.
3. **Never write to the real Target unattended.** If a task genuinely requires the
   real Target -- or any `scripts/restore_*.py` run -- stop with
   `status: needs_human`. Every item here is a write-path item, so this rule is
   live for the whole campaign.
4. **Never run bare `pytest`** or `pytest --ignore=tests/contract`: neither applies
   an `-m` filter, so both execute the ~322 `requires_live_project` tests in place
   against real projects. Always set `FLEXLIBS_REQUIRE_LIVE=1` and pass
   `-m requires_live_project` with an explicit test file.
5. **Evidence or it did not happen.** Each item writes
   `specs/<slug>/evidence/live-<task>.md` with the exact command, the
   `run_mode` value from `tests/live_status.json`, pre-state and post-state values
   **re-read from the LCM** after the write, and a pass/fail line.
6. **Relay report PATHS, not bodies** (lex-lead spurt rule 2).
7. **One checkpoint per iteration.** Then update state, commit, stop.
8. **No emoji in console output** (Windows). Use `[OK]` / `[FAIL]` / `[WARN]`.

## Campaign Log

- **2026-09-07** -- campaign opened by the main session. Directories scaffolded for
  items 1, 2 and 4; item 3 already existed. `active` = item 1
  (`243-closeproject-save-guard`), entry = Checkpoint 1 (spec + live probe).
  No code under `flexicon/code/` modified yet.
- **2026-09-07 -- item 1, spurt 1 (cycle 1) COMPLETE.** Spec+probe checkpoint
  reached for `243-closeproject-save-guard`. Crew: `lex-programmer` +
  `lex-domain` in parallel, then `lex-archivist` sequentially. Delivered
  `spec.md` (C1-C10), `tasks.md` (T1-T5 / CP-A..CP-C), `STATUS.md`,
  `.crew-handoff.json`, three cycle-1 reviews, and
  `tests/operations/test_issue243_closeproject_probe.py` (5/5, `run_mode: live`,
  sandbox only, real Target untouched). **Nothing under `flexicon/code/` was
  modified.** Headline: the issue's own proposed fix (reorder `Save()` before
  the End mirror) was DISPROVED live and replaced by a guard (C1), and the
  owner's unreproduced symptoms were ruled and closed (C9/C10) rather than left
  hanging -- the incident is a `SaveChanges()`-at-depth-1 trigger chaining into
  the unguarded-End loss mechanism, reachable from flexicon's own shipped
  `SaveChanges()` docstring Example. Item 1 remains `active`; next entry is
  CP-A / T1, the first task that touches `flexicon/code/`.

- **2026-09-07 -- item 1, spurt 2 (cycle 2) COMPLETE: CP-A1 / T1.** First code
  in this campaign to land under `flexicon/code/`. Crew: `lex-programmer`
  alone (T1 gated solo on purpose; T2 deferred, Q3 pre-ruled). Delivered the
  P1 depth-read surface in `flexicon/code/FLExProject.py` --
  `_ReadActionHandlerDepth()` (raises `FP_ProjectError` on closed/never-opened,
  no lenient fallback per C5), `CurrentDepth` as a **property** (matching the
  `Cache` precedent), and `HasOpenSessionTask()`. Live: extended probe 6/6
  green, `tests/live_status.json` `"run_mode": "live"`, `target_sandbox_path`
  only, real Target never opened, no restore script run. Offline: 1290 passed
  -- unchanged baseline. `/lex-lead` independently verified the scope fences
  rather than trusting the report: `git diff --stat flexicon/code/` = **120
  insertions, 0 deletions, ONE file**, so `CloseProject()` and `SaveChanges()`
  are provably untouched, and neither `flexicon/__init__.py` nor the
  capabilities test moved. Two rulings recorded: **Q3 CLOSED (no capability
  token)** and **new C11** -- the programmer deviated from the dispatch brief
  by reading depth BEFORE the `_undoable` short-circuit, raised it explicitly,
  and the deviation was ruled CORRECT (the brief wording would have broken C4
  for a closed `undoable=True` project and, on a never-opened instance, thrown
  a bare `AttributeError` because `self._undoable` is assigned after
  `self.project`). Both are written into `spec.md` and `tasks.md`, not just a
  dispatch rationale, so a context reset cannot lose them. Item 1 remains
  `active`; next entry is **CP-A2 / T2 alone**, then CP-B (T3-T4) and CP-C
  (T5). No GitHub issues filed; the `SaveChanges()` depth-guard item below is
  still awaiting the user's ruling and was NOT acted on.

- **2026-09-07 -- item 1, spurt 3 (cycle 3) COMPLETE: CP-A2 / T2 DROPPED.**
  The first spurt in this campaign to land **zero lines of production code by
  design** -- and the correct outcome. Crew: `lex-programmer` alone. T2 was
  executed exactly as specified, came back as a FINDING rather than a diff, and
  `/lex-lead` ruled on it: **T2 is DROPPED on the merits, frozen as `spec.md`
  C12**, with both escape hatches the report named explicitly REJECTED (an
  `isinstance(depth, int)` guard, and editing the static source-grep test at
  `tests/test_custom_field_create_refusal.py:54-60`) and the third option --
  adding `spec=` to the bare `Mock()` project doubles -- declined outright
  rather than deferred, since T2's death removes its purpose. Decisive reason
  beyond the report's: the prescribed `except` wrapper would swallow the
  `FP_ProjectError` T1's helper exists to raise and substitute `0`, which at
  `CustomFieldOperations.py:306` silently disables the issue-#21 corruption
  guard -- three duplicated depth reads are strictly better. `/lex-lead`
  re-verified every claim rather than trusting the report: empty
  `git diff f3a0f50 -- flexicon/`, offline `1290 passed`, the grep test
  present as described, and the live-collection counts. **Second finding, in
  `/lex-lead`'s own plan:** the T2 brief named live suites BY FILENAME, and
  `tests/operations/test_transaction_rollback.py` carries zero
  `requires_live_project` markers (0 collected / 20 deselected), so one of the
  three named "live suites" verified nothing while a second env-skipped. The
  programmer flagged it instead of substituting a file -- correct. The rule is
  now binding in `tasks.md`: derive every live set with
  `--collect-only -q -m requires_live_project` and paste the count into the
  evidence file; `no tests collected` is a ZERO, never a pass. Item 1 remains
  `active`; next entry is **CP-B / T3** (the P0 guard), then T4, then CP-C
  (T5). No GitHub issues filed; the `SaveChanges()` depth-guard item below is
  STILL awaiting the user's ruling and was not acted on, planned around, or
  prototyped.

- **2026-09-07 -- item 1, spurt 4 (cycle 4): CP-B REACHED AND PASSED, and item
  1 is now `needs_human`.** Crew: `lex-programmer` alone (T3 and T4 dispatched
  together -- T4 is T3's regression proof and CP-B's checkpoint line requires
  both green). **T3, the P0 guard, is landed and live-verified**: probe 6/6,
  `test_undoable_mode_live.py` 33/33, `test_target_live_smoke.py` 3/3, all
  `run_mode: live`; `test_transaction_rollback.py` 20/20 offline; offline suite
  unchanged at `1290 passed`; every marker count derived with `--collect-only`
  per the spurt-3 rule. **P-3 -- the loss mechanism C9 names -- is FIXED:
  0/25 -> 25/25 with no raise**, `.fwdata` grew +20,625 bytes and a
  `Target.bak` sibling appeared. Acceptance criteria 1-4 satisfied.
  `SaveChanges()` provably unmodified.

  **But P-5 -- the owner's ACTUAL sequence -- measured 0/25, not 25/25**, and
  `/lex-lead` ruled on it rather than accepting either the report's diagnosis
  or its framing. Three rulings, frozen in `spec.md`:

  - **C13 -- what the measurement does and does NOT establish.** The rival
    hypothesis that would have implicated the FIX SHAPE ("the guard skipped an
    `End` that should have run") is **disproved by measurement inside the same
    run**: the probe force-calls `EndNonUndoableTask()` manually before
    `CloseProject()` and it still raises `Cannot end task that has not been
    started.` -- the envelope was genuinely gone, so no `End` could have
    succeeded either way. C1/C6/C7 stand and **T3 needs no rework**. Equally:
    the report's asserted mechanism ("the `UnitOfWorkService` cannot commit
    after a failed `CheckReadyForCommit`") is **NOT frozen** -- it is a
    liblcm-internals claim from one black-box survivor count, and C13 records
    three rival mechanisms with identical observations. One of them
    (`SaveChanges()` discarded the change set) would mean the data is already
    gone before `CloseProject()` is entered, so **no `CloseProject()`-side
    change could ever reach 25/25** -- decisive for #243's ceiling, so it goes
    to a probe (new **T6**), not into the contract.
  - **C14 -- we created a NEW silent-loss surface, and closing it is in scope.**
    For the owner's chain, T3 turned "0/25 lost, `CloseProject()` RAISED" into
    "0/25 lost, `CloseProject()` returns normally with one `debug` line."
    Identical loss, only the close-path signal removed -- and observability is
    the filed complaint verbatim. **The instruction was wrong, not the
    implementation:** `tasks.md` T3 said "log at debug level", but in Phase 1 a
    `False` from `HasOpenSessionTask()` is anomalous by construction and means
    we are standing inside the owner's incident. Same class as C11, and
    `/lex-lead`'s defect to own. Remedy = new **T7** (log at ERROR; always
    attempt `usm.Save()`, then RAISE when it cannot be trusted). **T7 restores
    LOUDNESS, not DATA.**
  - **C15 -- Q2(a) RESOLVED** (forced by C14): `Dispose()` moves into a
    `try/finally` so T7's raise cannot leak the LCM handle. Genuinely open
    after T3; not deferred a fourth time.

  Two CP-B defects were found in review that the report did not raise: the
  debug-level branch above, and **P-5's "`CloseProject()` did not raise" being
  unasserted and unquoted** (`close_exc_msg` is captured and never checked,
  unlike P-3) -- load-bearing for C13, pinned by T6. The cycle-4 note filed
  under `spec.md` Q2 was ruled **misfiled and moved to a new Q5** (Q2 is about
  `usm.Save()` *raising*; this is the complement -- it does not raise and
  silently persists nothing).

  **Task order changed: T6 -> T7 -> T5, and T5 (CHANGELOG) is now LAST.**
  T6/T7 were appended rather than renumbered so existing cross-references stay
  valid. **Item 1 STOPS here as `needs_human`** -- the `SaveChanges()` fourth
  ask below is no longer merely queued, it is **BLOCKING**. No GitHub issues
  filed; the `SaveChanges()` guard was not implemented, prototyped or planned
  around. Items 2, 3 and 4 untouched.

### Awaiting user approval (do not file inside the loop)

- (carried from the `feature-structure-sync-gap` handoff) `IWfiAnalysis.MsFeaturesOA`
  never captured; `IFsFeatStruc.FeatureDisjunctionsOC` never traversed;
  `ICmBaseAnnotation` / `IScrScriptureNote.FeaturesOA` uncaptured;
  `EtymologyOperations.py:548` no-clear-on-null RA policy;
  `BaseOperations._apply_props_loop:346-353` dict-dispatch hazard.
- **NEW (item 1, spurt 1, 2026-09-07) -- `SaveChanges()` has no depth guard.**
  Under `undoable=False`, `FLExProject.SaveChanges()` (`FLExProject.py:563-588`)
  calls `usm.Save()` with no check on `ActionHandlerAccessor.CurrentDepth`. The
  session-long envelope holds depth at 1 for the whole session, so the call
  raises liblcm's `InvalidOperationException: Commit at wrong place.` AND
  collapses the envelope (depth 1 -> 0) as a side effect -- which is what then
  makes `CloseProject()`'s unguarded End raise and discard the session. This is
  reachable straight from the method's **own shipped docstring Example**
  (`with project.Transaction(...)` then `project.SaveChanges()`), which is
  correct under `undoable=True` and a guaranteed raise under `undoable=False`.
  Live-confirmed (probe P-5, `evidence/live-cycle1-probe.md`).
  Making `SaveChanges()` fail fast, or handle depth > 0, is a **behaviour
  change and a fourth ask** beyond #243's three surviving asks, so it is NOT
  absorbed into item 1 -- it needs the user's ruling on whether to file it as
  its own issue. **Already covered in-scope:** item 1's T5 corrects the
  misleading docstring Example (prose only, no behaviour change).

  **ESCALATED 2026-09-07 (spurt 4): this is no longer merely queued -- it is
  the BLOCKER that stopped item 1, and it has grown a second coupled part.**
  T4 measured the owner's own P-5 sequence at **0/25 survivors even with the
  #243 guard in place** (`spec.md` C13), so #243's three asks fix the P-3 loss
  mechanism but do **not** fix the incident #243 was filed about. Separately,
  `spec.md` C14 found that the guard makes that same path *silent* where it
  previously raised, and its remedy (**T7**: `CloseProject()` raises when it
  detects a save it cannot trust) is itself a public-behaviour change in the
  **same failure path** as this ask. **The two must be ruled together:**

  - **Approve the `SaveChanges()` guard** -> the envelope is never collapsed,
    the P-5 chain never forms, the owner's sequence can reach 25/25, and T7's
    raise becomes near-unreachable defensive code (still worth having, but its
    wording is low-stakes).
  - **Decline it** -> T7's raise is the ONLY thing standing between the owner
    and silent total loss, and its severity and wording matter a great deal.

  Nothing in item 1 can be honestly closed before this ruling: T5's release
  note would have to either claim a fix that does not hold for the filed
  incident, or publicly document that it is unfixed -- and the latter commits
  the project to a position on this ask. **Pre-authorised without the ruling:
  item 1's T6 only** (probe-only, sandbox fixture, no `flexicon/` behaviour
  change); it sharpens this very decision by settling whether the data is
  already gone before `CloseProject()` is entered. Note that **all three rival
  mechanisms in C13 imply the same shape for this ask** (refuse `usm.Save()`
  at `CurrentDepth > 0`, failing fast before any damage), so the open
  mechanism question does not block the decision -- it only bounds what #243
  may claim without it.
- Open issue **#259** (`InflClassRA` does not exist on `IWfiMorphBundle`) is
  Tier 2, NOT in this campaign -- but its draft lives at
  `specs/254-getmorphtype-allomorph/reviews/cycle3-archivist-inflclass-issue-draft.md`
  and touches the same file as the `IWfiAnalysis` item above. Keep them together
  when the user rules on filing.
