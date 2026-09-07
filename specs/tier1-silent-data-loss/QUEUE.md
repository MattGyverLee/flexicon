# CAMPAIGN QUEUE -- tier1-silent-data-loss

**Repo:** flexicon (`main`). **Started:** 2026-09-07.
**Scope:** the four Tier 1 (silent data loss / silent corruption) open issues.
**Driver:** ralph-loop in-session Stop hook + `/lex-lead` spurt mode --
**CANCELLED as of spurt 5 (2026-09-07). Nothing resumes automatically.**
The Stop hook is gone (`.claude/ralph-loop.local.md` deleted in the working
tree), so this campaign is now human-driven until someone restarts it. See
`specs/243-closeproject-save-guard/STATUS.md` -> **"How a human restarts
this"**. The campaign promise is still `TIER1 COMPLETE`, never
`FEATURE COMPLETE`.

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
| 1 | **`done` (crew sign-off, spurt 9 / cycle 9 -- `feature_complete`, APPROVED by `/lex-lead`)**. All five closure gates green: T7 live-verified; the C24 CHANGELOG correction landed and independently re-verified; QC score 90/100 with **P0 count 0** and BOTH P1s disposed (fail-open remedied by T9a/T9b, P-11 ruled no-action with a forward rule -- C28); the C26/C27 staleness sweep done; P-11 parked as a user-approval ask with its 25/25 pin intact. Live at closure: probe 11/11, abort-session 12/12, `run_mode: live`; offline 1292 passed / 475 deselected. **GitHub #243 is deliberately still OPEN -- the crew does not close issues, and C10's `.fwdata` half is unmeasured by design.** THREE items sit under "Awaiting user approval" (C25 rollback-discard audit, its C29 counter-measurement, the TRANSACTION_GUIDE gap) plus ONE ungated cleanup (C30, below). | `243-closeproject-save-guard` | #243 | Smallest diff, largest downside averted. Owner-confirmed total session loss: a run reported success, an immediate inventory saw all 11,987 new objects, a later open saw none, and `Target.fwdata` had been replaced by the crash-recovery copy -- one `[WARN]` line the only symptom. Orthogonal to items 2-4. |
| 2 | **`done`** (closed 2026-09-07; see the closure banner under "Per-item entry conditions" below). Q-242A/Q-242B, the two sibling-site asks this item's own cycle-2 sibling sweep surfaced, were spun out to sub-item **2a** rather than folded back in. | `242-paragraph-whitespace` | #242 | Cheap, self-contained, real corruption. Paragraph/Segment text writers silently strip leading/trailing whitespace. |
| 2a | **`active`** -- **AUTHORISED BY THE OWNER 2026-09-07**, spun out of item 2's "Awaiting user approval" list into its own feature directory (spec+probe checkpoint DONE, cycle 1). | `name-field-whitespace-identity` | Q-242A, Q-242B (both under `specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user approval", now authorised -- see the entries below) | Same bug shape as item 2 (strip -> validate -> persist the stripped copy) at 8 NAME-field sibling sites plus a more severe non-str/whitespace-only silent-empty-name defect at `CheckOperations`, deliberately triaged separately from item 2 because the identity/dedup question needed its own ruling. A **second, owner-confirmed crew** is concurrently active in the same working tree while this sub-item runs -- see `specs/name-field-whitespace-identity/CONCURRENCY.md`. |
| 3 | `queued` | `feature-structure-sync-gap` | #251 #252 #253 #256 | **Already in flight** -- contract frozen (C1-C8), live ground truth captured, spurt 1 done. RESUME, do not re-plan. Biggest item (T1-T17). Ships data loss today: `Allomorph` and `POS` are live sync object types. |
| 4 | `queued` | `250-writingsystem-activation` | #250 | Deliberately LAST: resolving it requires an **API-surface policy decision** (active-only `Exists` plus a separately-named whole-store predicate, vs. an `Ensure()` that activates a store-present WS). That is the item most likely to end `needs_human`, so everything landable unattended lands first. |

## Ordering rationale

Ordered by risk-averted / effort, with one override: the item carrying a likely
human decision is placed last so a `needs_human` stop cannot strand three
untouched items behind it.

## Per-item entry conditions

### 1. `243-closeproject-save-guard` (#243)

> **CLOSED 2026-09-07 (end of spurt 9, cycle 9): `done`.** `/lex-lead`
> signed this item off as `feature_complete` / APPROVED. Everything below
> this banner is the audit trail of how it got there -- read it as history.
> The single most important sentence in it is C17's three-part statement,
> which must always be said together: T3 fixed the P-3 path; nothing in
> `CloseProject()` could ever have fixed the owner's real P-5 -> P-3 chain;
> T8b, on the `SaveChanges()` side, has now fixed that chain too (25/25 in
> memory and 25/25 on disk). **GitHub #243 remains OPEN by design** -- see
> the campaign-log entry for spurt 9 and `spec.md` C10.
>
> **STATUS 2026-09-07 (end of spurt 8, cycle 8): `active`. The owner's
> filed incident is FIXED, live-verified, 25/25.** The user's coupled
> ruling (spurt 6) landed as `spec.md` **C20**: the `SaveChanges()` depth
> guard is APPROVED IN SUBSTANCE, constrained to depth/transaction
> correctness, not sharing exclusivity. **T8a** (spurt 6, measurement-only,
> `spec.md` C21) proved a blanket guard is safe -- no measured path where
> `SaveChanges()` succeeds at `CurrentDepth > 0`. **T8b** (spurt 7)
> implemented it: `SaveChanges()` now raises `FP_TransactionError` before
> `usm.Save()` at any `CurrentDepth > 0`, in either mode, with a
> mode-differentiated message (C21) and fail-OPEN behaviour on an
> unreadable depth. **Consequence: the full owner sequence (create,
> mid-session `SaveChanges()`, `CloseProject()`) now re-measures 25/25 in
> memory and 25/25 on disk** -- C17's ceiling ("no `CloseProject()`-side
> change can ever fix this") stood right up until a `SaveChanges()`-side
> change did, exactly as C17 predicted it would have to.
>
> T8b also enumerated and repaired its own 11-site test blast radius
> (`spec.md` C22, corrected by **C26** this cycle -- see below), and
> measured an unexpected finding, **P-11**: an `FP_TransactionError`
> escaping an `UndoableOperation()` block did NOT discard the block's
> object creations (25/25 survived), contradicting that module's own
> rollback-discards-everything docstring claim. Routed narrowly per
> `spec.md` **C25** (below).
>
> **This cycle (spurt 8): T7 (the C23-recut loudness log) landing in
> parallel via `/lex-programmer`; this docs pass (T5b) closes out
> `docs/TRANSACTION_GUIDE.md`, Q4, and a CHANGELOG factual correction
> (C24) that the pre-T8b CHANGELOG text ("this does not fix the incident
> #243 was filed about") is now FALSE and must not be cited.** See
> `spec.md` C21-C27 and `specs/243-closeproject-save-guard/reviews/cycle8-doc.md`.


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

> **CLOSED 2026-09-07 (cycle 4): `done`.** `/lex-lead` signed this item off
> as `feature_complete` (APPROVED). Four writers (`ParagraphOperations`
> `Create`/`SetText`/`InsertAt`, `SegmentOperations.AppendSentence`)
> validated emptiness on a `.strip()`'d copy then persisted that stripped
> copy; they now validate on a throwaway and persist the caller's original
> bytes, 8 payloads confirmed round-tripping byte-for-byte through all four
> writers, the layer-B raw-`MakeString` bypass, and in-memory/on-disk. C12
> additionally fixed a PRE-EXISTING `AppendSentence` join-boundary defect
> the whitespace fix exposed (not introduced): the terminator now anchors
> at the last non-whitespace character and reuses existing trailing
> whitespace as the separator, deleting zero characters, provably inert on
> every input reachable before this fix. Contract C1-C14 frozen. **NOT
> claimed:** the owner's field figures (44/104 paragraphs, 41/86 segment
> baselines) were not reproduced (Checkpoint 4 DECLINED, not deferred,
> C13). This item's own cycle-2 sibling sweep surfaced three further asks
> -- Q-242A, Q-242B, Q-242C -- routed to "Awaiting user approval" below
> rather than folded back into this item. **Q-242A and Q-242B are now
> AUTHORISED and spun out to sub-item 2a; Q-242C remains unauthorised.**
> `specs/242-paragraph-whitespace/spec.md` and `tasks.md` carry the full
> record; this banner is the audit trail, read below it as history.

No further work is scheduled inside `242-paragraph-whitespace` itself.

### 2a. `name-field-whitespace-identity` (Q-242A, Q-242B)

**AUTHORISED BY THE OWNER, 2026-09-07. `active`.** Spun out of item 2's
own "Awaiting user approval" list rather than folded back into
`242-paragraph-whitespace`, because the identity/dedup ruling it needed
was genuinely a separate decision. **Checkpoint 1 (spec + live probe) is
DONE** -- `specs/name-field-whitespace-identity/spec.md` (contract C1-C8,
FROZEN), `tasks.md`, `STATUS.md`, `.crew-handoff.json`, two cycle-1
reviews, and `tests/operations/test_name_field_identity_probe.py` (8/8
live, `run_mode: live`). See that feature's own directory for the full
record; this campaign file does not duplicate it.

**The ruling authority on the identity question changed mid-cycle, and
that provenance is binding, not incidental:** `/lex-lead` ruled C1-C8, the
owner then directed *"do what is best for the user, /lex-domain can
decide,"* placing the identity ruling (C3) under `/lex-domain`'s
authority, and `/lex-domain` independently re-tested and ACCEPTED
`/lex-lead`'s option (i) -- whitespace-insensitive comparison, symmetric
at both sides, raw-byte persistence -- on independent FLEx-domain
grounds. Full record: `specs/name-field-whitespace-identity/spec.md`
section 0 and C3.

**A second, owner-confirmed crew is concurrently active in the same
working tree while this sub-item runs.** See
`specs/name-field-whitespace-identity/CONCURRENCY.md`, binding on every
task in this sub-item: never stage, revert, or restore
`flexicon/code/BaseOperations.py`,
`flexicon/code/Grammar/NaturalClassOperations.py`,
`flexicon/code/Grammar/PhonemeOperations.py`,
`tests/operations/test_natural_class_feature_sync.py`,
`specs/feature-structure-sync-gap/`, or `specs/250-writingsystem-activation/`.
The offline suite's fixed baseline is VOID for this sub-item's duration --
`specs/name-field-whitespace-identity/tasks.md` uses a before/after DELTA
measurement instead.

**One unrelated, unplanned bug found in cycle 1, recorded not fixed:**
`CheckOperations._GetCheckList()` is a hardcoded stub whose
fallback path calls a nonexistent `ServiceLocator.GetInstance(...)`
(should be `.GetService(...)`), making `CreateCheckType()` raise
`AttributeError` on every call against a live LCM -- it appears to have
never worked against a live LCM. Worked around at the test-instance level
only (zero `flexicon/` lines changed). This is a live-verification
dependency for every future task in this sub-item that touches
`CheckOperations.py`, not a design blocker. Not filed as a GitHub issue;
see `specs/name-field-whitespace-identity/spec.md` section 3.

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

- **2026-09-07 -- item 1, spurt 5 (cycle 5): T6 DONE, the ceiling is MEASURED,
  and the ralph loop is CANCELLED.** Not a loop iteration: the user greenlit
  **T6 and only T6** (the pre-authorised probe) after spurt 4's `needs_human`
  handoff, and the main session ran it as a **one-shot** rather than
  restarting the loop, precisely so nothing could drift into T7 or T5. Crew:
  `lex-programmer` alone. **`git diff --stat -- flexicon/` is EMPTY**
  (re-verified by `/lex-lead`) -- zero behaviour change, so T6 stayed
  ruling-independent exactly as designed. Probe file **6 -> 9** live tests,
  all green with `run_mode: live`; `test_undoable_mode_live.py` 33/33;
  `test_target_live_smoke.py` 3/3; offline **1290 passed** with deselected
  470 -> 473 (exactly the +3 new live tests). **CP-B defect 2 CLOSED** --
  `test_p5_save_before_forced_end` now asserts `close_exc_msg is None` and
  the `[PROBE][P5]` lines are quoted verbatim, so C13 fact 3 is a measurement
  rather than prose. Four rulings, all frozen in `spec.md`:

  - **C16 -- the mechanism question is ANSWERED, with its limit recorded
    honestly.** **(ii) CONFIRMED**: P-7 re-read the 25 entries from the
    STILL-OPEN project immediately after `SaveChanges()` raised at depth 1 --
    **0/25**, already gone. **(i) RULED OUT**: P-8's fresh post-failure
    envelope committed **1/1**, so the `UnitOfWorkService` is not globally
    poisoned -- which also *contradicts* the cycle-4 report's asserted
    "cannot commit after a failed `CheckReadyForCommit`" wording. **(iii) is
    NOT separately distinguishable from (ii)** by anything measured and is
    **left unresolved by design** -- the report volunteered that limit itself
    instead of guessing, which is the correct outcome and is recorded that
    way rather than tidied into false certainty.
  - **C17 -- #243's CEILING, now a contract item, and the most consequential
    fact in the feature.** Because the change set never survives as far as
    `CloseProject()`, **no `CloseProject()`-side change can EVER recover the
    owner's real P-5 -> P-3 sequence -- T3's guard, T7, or any future guard
    there. Only the `SaveChanges()` fourth ask can.** C14 said "loudness, not
    data" from an inference; C16 is the measurement that proves it. **Second,
    equally binding half: T3 IS a genuine, shipped, live-verified fix for the
    independent P-3 path (0/25 -> 25/25) and C17 does not weaken it.** Any
    summary must state both halves.
  - **C18 -- T7's detector re-scoped so it cannot be over-claimed;
    supersedes C14 point 3.** `HasUnsavedChanges` read *after* `usm.Save()`
    is `False` in BOTH the real-save (25/25) and no-op (0/25) cases --
    **indistinguishable**, so C14's preferred direct post-save read is
    **void**. The programmer's prose-only recommendation (envelope-missing
    heuristic primary; pre-`Save()` read only to sharpen the message) is
    **ACCEPTED**, with two additions `/lex-lead` took from the evidence
    rather than the report: the pre-`Save()` read is **not independent
    information** (it read `True` only *after a successful `End`*, so it is a
    proxy for "did an End just succeed" -- a fact `CloseProject()` already
    holds first-hand), and the suggested wording **"there is nothing pending
    to save" is REJECTED as a proven false-negative** (it read `False` before
    the trigger `SaveChanges()` while all 25 entries still existed in
    memory). `tasks.md` T7 point 3 was rewritten accordingly.
  - **C19 -- T5 SPLIT; deferring all of it was re-costed and found not to be
    neutral.** `CHANGELOG.md` has a live `[Unreleased]` section and **T3 is
    already on `main` inside it with no entry at all**, so a version cut
    today would ship an undocumented public behaviour change including C14's
    observability regression. **T5a** (minimal `[Unreleased]` stub, T3 only,
    scoped to C17's two halves) is ruling-independent, zero-churn and
    **RECOMMENDED**; **T5b** (the prominent note + the `SaveChanges()`
    docstring correction + Q4) stays gated behind T7 and the ruling.

  **Item 1 stays `needs_human` and the ralph loop is CANCELLED** -- no Stop
  hook will re-feed anything, so the campaign is human-driven from here. The
  blocker is restated on the sharpened facts: the user is no longer deciding
  whether to approve an extra improvement, but **whether flexicon fixes
  #243's incident at all, or ships #243 documenting it as unfixed.** No
  GitHub issues filed; `SaveChanges()` untouched, unprototyped, unplanned.
  Items 2, 3 and 4 untouched, and `specs/feature-structure-sync-gap/` was not
  opened.

- **2026-09-07 -- item 1, spurt 6 (cycle 6): the user RULED, and T8a
  measured the guard shape.** The user answered the `needs_human` blocker
  directly: *"resolve #243 with /lex-lead. The goal is safe writes, but
  without sacrificing edits on shared projects; editing custom fields is
  the only edit I've seen that CAN'T be done shared."* Frozen as `spec.md`
  **C20**: the `SaveChanges()` depth guard is APPROVED IN SUBSTANCE,
  constrained to depth/transaction correctness only -- NOT sharing
  exclusivity, locking, or refusing writes because a project is shared.
  `/lex-lead` also corrected the user's premise against the code: flexicon
  contains zero sharing-based refusals; the custom-field refusal the user
  named is itself a depth guard (`CustomFieldOperations.py:306`), not an
  exclusivity one, so the fourth ask is the same KIND of guard the user
  already accepts. **T8a** (measurement-only, zero `flexicon/` diff)
  measured `SaveChanges()` at `CurrentDepth > 0` in the one case P-5/P-7
  never exercised (inside `UndoableOperation()`, `undoable=True`) plus two
  controls: no measured case exists where `SaveChanges()` currently
  succeeds at depth > 0, so a blanket guard is safe. Frozen as **C21**.
  Ralph loop stays cancelled; ran as a directed dispatch, not a loop
  iteration.

- **2026-09-07 -- item 1, spurt 7 (cycle 7): T8b LANDED -- the fourth ask
  is shipped, and the owner's filed incident measures 25/25.** Crew:
  `lex-programmer` alone. `FLExProject.SaveChanges()` now raises
  `FP_TransactionError` before `usm.Save()` at any `CurrentDepth > 0`, in
  either mode, with a mode-differentiated message (undoable=False may name
  data loss; undoable=True must not, per a measured false-positive risk) and
  fails OPEN if the depth read itself raises. The three shipped docstring
  `Example` blocks (`SaveChanges()`, `RefreshFromDisk()`,
  `AbortSession()`'s `else:` branch) were corrected in the same diff. All
  11 enumerated test-blast-radius sites (`spec.md` C22) were repaired;
  public-API pins now assert `FP_TransactionError`, liblcm-mechanism pins
  (P-7/P-8/P-9) switched to the raw `usm.Save()` accessor so C13/C16/C18's
  basis is not silently deleted. **Headline measurement: the full owner
  sequence now re-measures 25/25 in memory and 25/25 on disk**, up from
  0/25 pre-guard -- C17's ceiling is met, by the only route C17 said could
  ever meet it. **P-11** (a new probe) found an escaping
  `FP_TransactionError` inside `UndoableOperation()` does NOT discard the
  block's object creations (25/25 survived), contradicting that module's
  own rollback docstring -- a P0 finding flagged for routing, not
  absorbed here. `/lex-lead` recut **T7** as **C23**: post-T8b the only
  live route into `CloseProject()`'s Phase-1 envelope-missing branch is
  the one where the save already succeeded, so the planned
  `FP_ProjectError` raise there is WITHDRAWN (it would be a false alarm on
  success); the ERROR-level log (naming the anomaly, asserting nothing
  about loss) is the whole remaining remedy. Live: probe 11/11,
  `test_abort_session_live.py` 12/12, both `run_mode: live`; offline 1290
  passed unchanged. Item 1 moves from `needs_human` to `active`; next is
  T7 (`/lex-programmer`) and T5b (`/lex-doc`), in parallel.

- **2026-09-07 -- item 1, spurt 8 (cycle 8): T5b docs pass, plus three
  process corrections.** Crew: `/lex-doc` alone this cycle (T7 dispatched
  in parallel to `/lex-programmer`, tracked separately). Delivered: a
  CHANGELOG factual correction (`spec.md` **C24**) -- the pre-existing
  `[Unreleased]` text "this does not fix the incident #243 was filed
  about" was FALSE as of T8b and is corrected in place, with two
  anti-overclaim carve-outs preserved (C10's `.fwdata` exclusion; a new
  single-client-only caveat); `docs/TRANSACTION_GUIDE.md` corrections
  (the "no side effects on transactions" bullet, inverted; both
  `SaveChanges()` usage examples given a mode note; a bounded accuracy
  banner on the unverified Phase 1 rollback narrative); Q4 CLOSED
  (CHANGELOG amends `[Unreleased]` in place, cross-referencing `[4.4.0]`
  by prose); a new **C25** narrowly routing P-11's rollback finding (a
  docstring caveat to `/lex-programmer`'s `undoable_operation.py`, a
  broader open question to "Awaiting user approval" below, gating only
  this cycle's `TRANSACTION_GUIDE.md` wording); a **C26** correction to
  C22's test-blast-radius table (it was a different, coincidentally
  same-sized partition from `/lex-lead`'s own enumeration; re-keyed, three
  previously-unlisted edited sites surfaced, and a second widened
  source-slice window found); and **C27**, a standing rule that the doc
  agent landing a spurt's docs task owns that spurt's staleness sweep.
  Full report: `specs/243-closeproject-save-guard/reviews/cycle8-doc.md`.

- **2026-09-07 -- item 1, spurt 9 (cycle 9) COMPLETE: CP-CLOSE REACHED.
  ITEM 1 IS CLOSED -- `/lex-lead` signed `243-closeproject-save-guard` off as
  `feature_complete` (APPROVED). NO promise token was emitted: the campaign
  promise is `TIER1 COMPLETE` and items 2-4 are untouched.** Crew:
  `lex-programmer` (T9a/T9b) + `lex-doc` (C28/C29 + this file) in parallel.
  **T9a** rewrote the `SaveChanges()` fail-open comment to describe the
  `except Exception` catch the code actually has -- ANY depth-read exception
  fails open per C21 -- labelled the measured-safe case as CODE INSPECTION
  rather than a live probe, and named the un-measured residual per C10's
  discipline (claimed neither safe nor a bug). **Zero executable-line change,
  confirmed by diff.** **T9b** added the one offline test for that branch,
  forcing `CurrentDepth` to raise a `RuntimeError` (deliberately not
  `FP_ProjectError`) and asserting the WARNING fires, `SaveChanges()` does
  not raise, and **`usm.Save()` is called exactly once** -- the third
  assertion pins fail-open so a future silent flip to fail-closed cannot
  pass green. Gates: collect-only 11 and 12 as predicted; live **11/11** and
  **12/12**; `run_mode: live`; offline **1292 passed / 475 deselected**.
  **Two prediction misses are on the record, reported rather than smoothed.**
  (1) The dispatch brief predicted deselected 475 -> 476; it did not move and
  could not -- a new test WITHOUT `requires_live_project` lands in the
  `passed` bucket, while `deselected` counts only what the marker filter
  excludes. The brief was wrong, the measurement is right, and the programmer
  kept the measurement: C28's forward rule working as intended. (2) QC's
  predicted `except Exception` narrowing did not happen because `/lex-lead`
  ruled against it; T9 closed the code/comment mismatch from the comment
  side instead. **Second finding, and it is `/lex-lead`'s own debt:** C26
  addendum D's magic 6000-char source-slice window in
  `tests/test_transaction_honesty.py` broke on T9a's first draft (6589
  chars) -- an OFFLINE test outside T9's scope fence. The programmer
  correctly refused to widen the fence and rewrote the comment compactly
  (5735 chars, a **265-char margin**). Ruled as **`spec.md` C30**: not a
  task in this feature (it touches neither #243's correctness, nor any
  public claim, nor the trustworthiness of the record) but NOT left as a
  silent P2 either -- it is now an explicit **ungated cleanup** above, with
  the fix, the in-file precedent, and a trigger condition. Item 1 -> `done`;
  the `active` pointer advances to **item 2 (`242-paragraph-whitespace`)**,
  on which nothing has been done and nothing was authorised. No GitHub
  issues filed or closed; **#243 stays open for the user's decision** (C10's
  unmeasured `.fwdata` half).

- **2026-09-07 -- item 2 (`242-paragraph-whitespace`) CLOSED, recorded
  here for the first time.** This Campaign Log fell behind item 2's own
  cycles (1-4) and its closure -- `specs/tier1-silent-data-loss/.crew-handoff.json`
  recorded `242-paragraph-whitespace` as `done` (closed cycle 4,
  `feature_complete` APPROVED by `/lex-lead`, commit `249863d`) and this
  file's own queue table and per-item banner were not updated to match
  until this pass. That gap is now closed (see the item-2 table row and
  banner above); the full technical record remains in
  `specs/242-paragraph-whitespace/spec.md` (C1-C14) and `STATUS.md`,
  which this entry does not duplicate.

- **2026-09-07 -- sub-item 2a (`name-field-whitespace-identity`) OPENED
  and AUTHORISED BY THE OWNER; spurt 1 (cycle 1) COMPLETE.** Item 2's own
  cycle-2 sibling sweep had surfaced three follow-on asks -- Q-242A (8
  sibling name-field whitespace sites, blocked on an identity/dedup
  ruling), Q-242B (a more severe `CheckOperations` silent-empty-name
  defect), and Q-242C (coercion-policy harmonisation, out of scope) --
  filed to "Awaiting user approval" rather than folded into item 2. The
  owner authorised Q-242A and Q-242B; they are spun out to their own
  feature directory, `specs/name-field-whitespace-identity/`, as campaign
  sub-item **2a**, rather than reopening item 2. Q-242C remains queued and
  unauthorised, untouched by this spurt. Crew: `lex-programmer` +
  `lex-domain` in parallel (the live probe and the identity ruling), then
  `lex-archivist` sequentially (this file, plus `spec.md`/`tasks.md`/
  `STATUS.md`/`.crew-handoff.json` for the new sub-item). Delivered:
  `spec.md` (contract C1-C8, FROZEN -- the needle-only-strip mechanism,
  the persist-only-fix-produces-duplicates correction to #242's own C10,
  the whitespace-insensitive-dedup identity ruling, the fix shape and
  shared-code fence, the four-file scope, the Q-242A/Q-242B bundling
  rationale, Q-242B's own fix shape and the Q-242C boundary, and the
  anti-regression pin), `tasks.md`, `STATUS.md`, `.crew-handoff.json`, two
  cycle-1 reviews, and `tests/operations/test_name_field_identity_probe.py`
  (8/8 live, `run_mode: live`, `target_sandbox`/`target_sandbox_path`
  fixtures only, real Target untouched). **The identity ruling's authority
  changed mid-cycle:** `/lex-lead` ruled C1-C8, the owner then directed
  the identity question (C3) to `/lex-domain`'s authority, and
  `/lex-domain` independently re-tested and ACCEPTED `/lex-lead`'s option
  (i) on its own FLEx-domain grounds (the uniqueness guard at all three
  families is a flexicon invention, not a FLEx/LCM invariant). One
  unrelated, unplanned bug found and NOT fixed:
  `CheckOperations._GetCheckList()` is a hardcoded stub whose fallback
  path calls a nonexistent `ServiceLocator.GetInstance(...)`, making
  `CreateCheckType()` raise unconditionally against a live LCM -- worked
  around at the test-instance level only, recorded as a live-verification
  dependency for this sub-item's own future tasks, not filed as a GitHub
  issue.

  **A second, owner-confirmed crew was found active in this same clone
  during this spurt**, committing under the same git identity
  (`flexicon/code/BaseOperations.py`,
  `flexicon/code/Grammar/NaturalClassOperations.py`,
  `flexicon/code/Grammar/PhonemeOperations.py`,
  `tests/operations/test_natural_class_feature_sync.py`,
  `specs/feature-structure-sync-gap/`, and
  `specs/250-writingsystem-activation/` are theirs). This is confirmed by
  the owner as expected, not an anomaly. `specs/name-field-whitespace-identity/CONCURRENCY.md`
  records the binding protocol (explicit-path staging only, never revert
  or restore a path not authored by this sub-item, and a DELTA-based
  offline-suite measurement replacing the campaign's fixed baseline for
  the duration). Item 2a's own crew made zero `Edit`/`Write` calls under
  `flexicon/` this spurt; any `flexicon/` diff observed during this spurt
  belongs to the concurrent crew. No GitHub issues filed. Items 3 and 4
  untouched, not opened. `specs/tier1-silent-data-loss/.crew-handoff.json`
  is the main session's file and was not edited by this Archivist pass.

### Ungated cleanups (NO user approval needed -- just do them)

- **NEW (item 1, spurt 9, cycle 9, 2026-09-07) -- bound
  `tests/test_transaction_honesty.py`'s source-slice windows by the next
  `def `, not by a magic width.** Ruled as `spec.md` **C30**. C26 addendum D
  set `save_body = source[save_idx : save_idx + 6000]`; T9a's first
  (accurate) comment draft pushed the measured distance to **6589 chars and
  broke that OFFLINE test**, forcing a more compact rewrite that landed at
  **5735 -- a 265-character margin**. That is not a margin: the next
  docstring or comment edit near `SaveChanges()` breaks an unrelated offline
  test, and the pressure it creates is to write a LESS ACCURATE comment to
  fit a test's arbitrary width. **Fix (~6 lines):** bound `save_body` by the
  index of the next `def ` after `save_idx`, and `refresh_body` likewise,
  instead of `+ 6000` / `+ 4000`. There is an in-file precedent 20 lines
  below in `TestOneShotWarningAtOpenProject`
  (`source[open_idx:close_idx]`). **Do NOT widen 6000 to 8000** -- that
  perpetuates the anti-pattern. **Trigger:** do this at the START of the
  next spurt that edits `FLExProject.py`'s `SaveChanges()` or
  `RefreshFromDisk()` region, before that spurt's own edits. Pure test
  scaffolding: offline suite only, no live gate, no user decision, no public
  surface. This trap is item 1's own creation, which is why it leaves
  pre-ruled rather than as a discovery for the next reader.

### Awaiting user approval (do not file inside the loop)

- (carried from the `feature-structure-sync-gap` handoff) `IWfiAnalysis.MsFeaturesOA`
  never captured; `IFsFeatStruc.FeatureDisjunctionsOC` never traversed;
  `ICmBaseAnnotation` / `IScrScriptureNote.FeaturesOA` uncaptured;
  `EtymologyOperations.py:548` no-clear-on-null RA policy;
  `BaseOperations._apply_props_loop:346-353` dict-dispatch hazard.
- **APPROVED (spurt 6, `spec.md` C20) and LANDED (spurt 7, T8a/T8b) -- see
  `spec.md` C20-C23 and `evidence/live-t8b-savechanges-guard.md`. NOT
  deleted; kept below as the audit trail for how this ask was raised,
  ruled and shipped.** Original text follows verbatim for the record:
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
  the project to a position on this ask.

  **SHARPENED 2026-09-07 (spurt 5) BY T6 -- read this before deciding.** T6
  ran (probe-only, zero `flexicon/` diff) and **settled the mechanism
  question in the decisive direction**: `spec.md` **C16** confirms the change
  set is **already gone from the still-open project before `CloseProject()`
  is ever entered** (P-7: 0/25 in memory), and **C17** turns that into
  #243's ceiling. Consequences for this decision:

  - **This ask is no longer "would also help" -- it is the ONLY thing that
    can fix the incident #243 was filed about.** No `CloseProject()`-side
    change can reach 25/25 for the owner's sequence, at any price. So the
    question is not whether to approve an extra improvement; it is **whether
    flexicon fixes #243's incident at all, or ships #243 documenting it as
    unfixed.**
  - **The decline branch is now permanent, by measurement rather than by
    effort.** T7's ERROR + raise becomes the entire remedy the owner ever
    gets, which is why its severity and wording matter a great deal.
  - **Still true and still good news: the shape of the ask is unaffected by
    the residual (ii)-vs-(iii) uncertainty** -- refuse `usm.Save()` at
    `CurrentDepth > 0`, failing fast before any damage. The mechanism
    question never blocked this decision and now does not exist.
  - **One observation, NOT a fifth ask.** C16 places the loss *inside*
    `SaveChanges()`, so even T7's raise reports it **late**. If the "fail
    fast / prevent" shape is declined, the honest maximum available is "loud
    at close, already lost at `SaveChanges()`" -- so whether this same ask
    should have a *minimum* shape (report loudly at the point of loss) is
    part of the ruling about that one method. Nothing may implement,
    prototype or plan it; `SaveChanges()` stays untouchable.

  **No pre-authorised work remains on item 1** -- T6, the one exception, is
  DONE. `/lex-lead` now **offers a second, separable one** for the user to
  greenlight if they wish: **T5a**, a minimal `[Unreleased]` CHANGELOG stub
  noting T3 only and scoped to C17's two halves (`spec.md` **C19**). It is
  docs-only, ruling-independent, discloses nothing public issue #243 does not
  already state, and has **zero churn cost** because it can be edited before
  any version cut. It does **not** unblock T7 or T5b.
- **NEW (item 1, spurt 7, cycle 7, 2026-09-07) -- audit the broader class of
  schema/metadata-mutating and exclusivity-sensitive operations for
  depth-guard coverage.** `lex-domain`'s cycle-6 Q2 review (
  `specs/243-closeproject-save-guard/reviews/cycle6-domain.md`) found that
  `CustomFieldOperations.py:306`'s depth guard is **one instance of a
  broader class, not a unique case**: writing-system add/remove/change,
  model migration on version upgrade, project rename/relocation,
  possibility-list restructuring (especially deletes/moves of items with
  wide references), and deletes of objects with wide references generally
  are all schema-level or referential-integrity-sensitive mutations that
  may need the same kind of transaction-depth guard custom fields already
  have. This ask is for an **audit of that class** -- which operations need
  a depth guard, and whether any already have one -- not an implementation.
  **Overlap, stated explicitly so this is not filed as a duplicate:** the
  writing-system half of the class is **already open issue #250**, queue
  item 4 of this campaign. This ask is the audit of the whole class; #250
  is one already-tracked instance of it.
  **Why this is about transaction depth, not exclusivity** (also from
  cycle-6 domain Q1/Q3, same review): **Q1** found custom-field
  creation/editing is **NOT blocked on shared projects** -- FLEx's own gate
  at `CustomFieldOperations.py:306` is a local, in-process
  `ActionHandlerAccessor.CurrentDepth` check, independent of Send/Receive or
  LAN-sharing state. **Q3** found the issue-#21 ghost-field corruption
  mechanism (`IFwMetaDataCacheManaged.AddCustomField` inside an open task)
  would still occur on a **fully exclusive, non-shared** project -- the bug
  is about UnitOfWork/task-nesting order within one process, not about a
  second writer. So the class this audit targets is scoped by transaction
  depth and schema/metadata mutation, not by sharing/exclusivity, matching
  the C20 ruling's own correction of that premise for #243/#243's
  `SaveChanges()` guard.
- **NEW (item 1, spurt 8, cycle 8, 2026-09-07) -- does
  `UndoableUnitOfWorkHelper.Dispose()` + `set_RollBack(True)` actually
  discard anything?** T8b's P-11 (`evidence/live-t8b-savechanges-guard.md`)
  measured that an `FP_TransactionError` escaping a `with
  project.UndoableOperation(...)` block -- triggering `Dispose()` +
  `set_RollBack(True)` -- did NOT discard the block's own object
  creations: 25/25 survived both an in-memory re-read and a genuine
  close-and-reopen, contradicting `undoable_operation.py`'s and
  `transaction.py`'s own docstring claims that rollback discards the
  block's mutations. This ask is for a full audit, not an
  implementation: enumerate object creations (**MEASURED: no, 25/25
  survived both reads**), property modifications (unmeasured), deletions
  (unmeasured), plus every rollback claim in `undoable_operation.py`,
  `transaction.py`, `BaseOperations.TransactionCM`,
  `docs/TRANSACTION_GUIDE.md`, and what
  `tests/test_transaction_honesty.py` actually pins -- then a decision on
  whether the advertised rollback semantics change or the docs do. Likely
  a candidate feature directory of its own; likely also affects
  `AbortSession()`'s advertised semantics (it wraps the same
  `IActionHandler.Rollback(0)` primitive). **NO work happens on this
  until the user approves it.** Routed narrowly per `spec.md` **C25**: it
  gates only this cycle's `docs/TRANSACTION_GUIDE.md` wording (do not
  claim an escaping exception safely discards work; do not generalise the
  25/25 creation-survival measurement to property modifications or
  deletions), and gates neither T7 nor T8b's own completion -- #243's
  frozen contract never covered `UndoableOperation()` rollback semantics.
- **NEW (item 1, spurt 9, cycle 9, 2026-09-07) -- the counter-measurement to
  the item directly above, and it gets its own line rather than folding
  into it.** The cycle-8 programmer, checking `transaction.py` per its
  brief, found a live measurement at `flexicon/code/transaction.py`
  lines ~146-153: a created POS VANISHED on clean exit under the
  `helper.RollBack = False` assignment-bug (`UnitOfWorkHelper.Dispose()`
  rolling back every unit of work, clean ones included, because pythonnet
  silently accepts the plain-attribute write instead of reaching the
  private-setter .NET property). Ruled per `spec.md` **C29**: this is a
  TRUE RECORD of a live measurement, protected exactly as C10's
  unexplained facts are -- do not edit it, do not "reconcile" it with
  P-11. Same `Dispose()`-with-`RollBack`-effectively-`True` mechanism as
  P-11 above, OPPOSITE outcome (POS vanished vs 25/25 survived), which is
  exactly why it must not be generalised away: it is the one thing
  preventing a future reader from reading P-11 as "rollback never
  discards." **NO work happens on this until the user approves it.** The
  discriminating variables that were not controlled between the two
  measurements, and would need to be to reconcile them: object type (POS
  vs LexEntry), helper class (`UnitOfWorkHelper` vs
  `UndoableUnitOfWorkHelper`), exit path (clean exit vs an escaping
  exception), and whether an outer envelope/stack was open. Not resolvable
  inside #243's scope.
- **NEW (item 1, spurt 9, cycle 9, 2026-09-07) -- `docs/TRANSACTION_GUIDE.md`
  API-Reference gap, flagged by the cycle-8 doc agent as outside its
  authorised scope, gated behind the same C25 ask (the two items directly
  above).** Its correct wording depends on the answer to whether
  `Dispose()`/`set_RollBack(True)` actually discards anything, so writing
  it now would be guessing. No work happens on it until that question is
  resolved.
- Open issue **#259** (`InflClassRA` does not exist on `IWfiMorphBundle`) is
  Tier 2, NOT in this campaign -- but its draft lives at
  `specs/254-getmorphtype-allomorph/reviews/cycle3-archivist-inflclass-issue-draft.md`
  and touches the same file as the `IWfiAnalysis` item above. Keep them together
  when the user rules on filing.
- **AUTHORISED BY THE OWNER 2026-09-07 and MOVED to sub-item 2a
  (`specs/name-field-whitespace-identity/`) -- see that feature's `spec.md`
  C1-C8 and `specs/tier1-silent-data-loss/QUEUE.md` section "2a" above.
  NOT deleted; kept below as the audit trail for how this ask was raised
  and ruled.** Original text follows verbatim for the record:
- **NEW (item 2, cycle 2, 2026-09-07) -- Q-242A: 8 sibling name-field
  whitespace sites, routed here by `/lex-lead`'s R3 ruling
  (`specs/242-paragraph-whitespace/spec.md` C10).** Explore's full
  AST-verified table (`specs/242-paragraph-whitespace/reviews/cycle1-explore.md`
  Bucket 1), file:line / method / transform line / persist line:

  | site | method | transform line | persist line |
  |---|---|---|---|
  | `flexicon/code/System/CheckOperations.py:196` | `CreateCheckType` | 196 | 218 |
  | `flexicon/code/System/CheckOperations.py:432` | `SetName` | 432 | 439 |
  | `flexicon/code/TextsWords/TextOperations.py:152` | `Create` | 152 | 170 |
  | `flexicon/code/TextsWords/TextOperations.py:608` | `SetName` | 608 | 616 |
  | `flexicon/code/TextsWords/DiscourseOperations.py:327` | `CreateChart` | 327 | 351 |
  | `flexicon/code/TextsWords/DiscourseOperations.py:482` | `SetChartName` | 482 | 492 |
  | `flexicon/code/Notebook/AnthropologyOperations.py:265` | `Create` | 265 | 301 |
  | `flexicon/code/Notebook/AnthropologyOperations.py:374` | `CreateSubitem` | 374 | 391 |

  **The blocker is a name-field identity ruling, not effort.** Three of
  the four families feed the *stripped* value into a uniqueness check
  ahead of the persist (`CheckOperations.py:196`->`FindCheckType`
  at `:200`; `TextOperations.py:152`->`Exists` at `:155`;
  `AnthropologyOperations.py:265`->`Exists` at `:269`) -- per
  `#242/spec.md` C10, preserving the unstripped payload here would leave
  an unanswered question ("is `\"Genesis \"` the same text as
  `\"Genesis\"`?") that #242's own four filed sites never had to answer,
  because none of them has a name-uniqueness check. No work happens on
  this until the user rules on the dedup-identity question.
- **AUTHORISED BY THE OWNER 2026-09-07 and MOVED to sub-item 2a
  (`specs/name-field-whitespace-identity/`), landed TOGETHER with Q-242A
  at the same expressions per that feature's `spec.md` C6 -- separate
  tasks, severity labels, CHANGELOG entries, and live evidence, but ONE
  commit at `CheckOperations.py:196`/`:341`/`:432` rather than two
  sequential edits of the same lines. NOT deleted; kept below as the
  audit trail.** Original text follows verbatim for the record:
- **NEW (item 2, cycle 2, 2026-09-07) -- Q-242B:
  `CheckOperations.py:196` and `:432`
  (`name.strip() if isinstance(name, str) else ""` against a None-only
  `_ValidateParam`) persists a non-`str` argument as an EMPTY NAME with
  no exception -- total payload loss, silently.** `:341`
  (`FindCheckType`) is the read-path twin of the same coercion. This is
  flagged as **Tier-1 silent data loss in its own right**, and it is
  **DISTINCT from and MORE SEVERE than #242's whitespace loss** --
  #242's sites lose padding around real content; this site can lose the
  entire name. It is deliberately **NOT bundled with Q-242A** so it is
  not triaged at whitespace severity (`specs/242-paragraph-whitespace/spec.md`
  C10, C6 item 3). No work happens on this until the user approves it.
- **APPENDED CORRECTION (name-field-whitespace-identity, cycle 3,
  `spec.md` C10(b)) -- Q-242B severity correction, does NOT alter the row
  above, which is preserved verbatim as an audit trail.** The row above
  describes the defect as reachable by a non-`str` payload. Live cycle-1
  measurement (PN5/PN6) established it is ALSO reachable by an ordinary
  `str`: `CreateCheckType("   ")` strips to `""`, passes the None-only
  `_ValidateParam`, and persists an empty name with no exception (see
  `spec.md` C7). The exposure is strictly WIDER than the row states -- no
  type error on the caller's part is required to lose the entire payload.
- **NEW (item 2, cycle 2, 2026-09-07) -- Q-242C: coerce-vs-reject for
  non-`str` payloads.** `BaseOperations._ValidateParam`
  (`BaseOperations.py:2377`) is a `None`-check plus a stale-LCM guard
  ONLY, with no type check, so `str(obj)` can silently persist a value
  like `"<Foo object at 0x...>"` at 12+ sites sharing this shape across
  the codebase. Per `specs/242-paragraph-whitespace/spec.md` C11, this
  needs a `_ValidateParam` / shared-code decision -- CLAUDE.md requires
  consultation before changing shared validation methods, so this is
  queued rather than implemented incidentally inside #242. No work
  happens on this until the user rules on it.
- **Q-CHK1** -- `CheckOperations._GetCheckList()`
  (`flexicon/code/System/CheckOperations.py:1168-1179`) is a hardcoded stub
  that always returns `None`, forcing `_GetOrCreateCheckList()`
  (`:1181-1205`) down its create-a-new-list branch, which calls
  `self.project.project.ServiceLocator.GetInstance(ICmPossibilityListFactory)`
  at `:1198`. `ILcmServiceLocator` has no `GetInstance` method -- every
  other call site in this same file (`:209`, `:1391`, `:1430`) and every
  other Operations class uses `.GetService(...)`. Effect: `CreateCheckType()`
  raises `AttributeError` on every call, for every payload, `str` or not; it
  appears never to have worked against a live LCM. TWO defects, not one: the
  `GetInstance`/`GetService` typo AND the unowned-list design gap (what
  SHOULD `_GetCheckList` return, and who owns the check list?) -- the second
  is a design question, not a typo fix. Found by this feature's cycle-1 probe;
  worked around at the test-instance level ONLY (see C9), zero `flexicon/`
  lines touched. UNAUTHORISED; no work until the user approves.
- **Q-DISC1** -- `DiscourseOperations.CreateChart` is unreachable through its
  own public API, for two independent pre-existing defects, both confirmed by
  `git blame` to predate this feature: (1) `IConstChartFactory` NameError at
  `flexicon/code/TextsWords/DiscourseOperations.py:~335` -- the import list was
  corrected to `IDsConstChartFactory` in `8716a5f2d` (2025-11-26) but the usage
  site introduced by `d0aac1a54` (2026-06-23) was never updated; (2) wrong
  chart-ownership interface at `:~340` (`hasattr(text_obj.ContentsOA, "ChartsOC")`)
  -- confirmed by direct reflection on the live LCM assemblies that `IStText`
  has NO `ChartsOC` member; the real owner is `IDsDiscourseData`, a
  project-level singleton reached via `LangProject.DiscourseDataOA`, unrelated
  to any individual `IText`/`IStText`. The `hasattr` takes its `else` branch
  unconditionally and raises `FP_ParameterError("Text contents does not support
  charts")`. Fixing (1) alone merely exposes (2); fixing (2) requires a design
  decision (should charts be looked up via `LangProject.DiscourseDataOA` with a
  `BasedOnRA`-style back-reference to the text?). Empirically NOT workaroundable
  at the harness level: pythonnet regenerates a fresh Python wrapper on every
  `.ContentsOA` access, so an attribute assigned to one wrapper is invisible when
  `CreateChart` re-accesses the property internally. **Direct consequence: this
  feature's C8 persist pin for `CreateChart` is `FAIL: unverified`** -- the edit
  is confirmed correct by code inspection, and padded/unpadded inputs were
  measured to fail IDENTICALLY (ruling out the edit as the cause), but the
  persist-and-reread half could not be exercised. UNAUTHORISED; no work until the
  user approves.
- **Q-242D** -- whitespace-only names are silently persisted at the three
  `_ValidateParam`-only name sites: `AnthropologyOperations.Create`,
  `AnthropologyOperations.CreateSubitem`, and `TextOperations.SetName`. Because
  `_ValidateParam` is a null check only, `"   "` passes validation; pre-fix it
  was stored as `""` (total payload loss), post-fix it is stored as the caller's
  actual whitespace (raw-byte persistence per C3). Either way no exception is
  raised and the FLEx list/tree shows a blank-looking row. NOT fixed by
  `name-field-whitespace-identity` per its C11(c): adopting
  `_ValidateStringNotEmpty` at these sites is the validator-harmonisation
  decision **Q-242C** owns, and these are the three sites C7(b) fences into
  Q-242C. Does not overturn lex-domain's Q6, which is scoped to
  `CheckOperations`. Should be decided TOGETHER with Q-242C, not before it.
  UNAUTHORISED; no work until the user approves.
