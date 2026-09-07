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
| 1 | `active` | `243-closeproject-save-guard` | #243 | Smallest diff, largest downside averted. Owner-confirmed total session loss: a run reported success, an immediate inventory saw all 11,987 new objects, a later open saw none, and `Target.fwdata` had been replaced by the crash-recovery copy -- one `[WARN]` line the only symptom. Orthogonal to items 2-4. |
| 2 | `queued` | `242-paragraph-whitespace` | #242 | Cheap, self-contained, real corruption. Paragraph/Segment text writers silently strip leading/trailing whitespace. |
| 3 | `queued` | `feature-structure-sync-gap` | #251 #252 #253 #256 | **Already in flight** -- contract frozen (C1-C8), live ground truth captured, spurt 1 done. RESUME, do not re-plan. Biggest item (T1-T17). Ships data loss today: `Allomorph` and `POS` are live sync object types. |
| 4 | `queued` | `250-writingsystem-activation` | #250 | Deliberately LAST: resolving it requires an **API-surface policy decision** (active-only `Exists` plus a separately-named whole-store predicate, vs. an `Ensure()` that activates a store-present WS). That is the item most likely to end `needs_human`, so everything landable unattended lands first. |

## Ordering rationale

Ordered by risk-averted / effort, with one override: the item carrying a likely
human decision is placed last so a `needs_human` stop cannot strand three
untouched items behind it.

## Per-item entry conditions

### 1. `243-closeproject-save-guard` (#243)

**Spec+probe checkpoint DONE (spurt 1, 2026-09-07).** `spec.md` (contract
C1-C10), `tasks.md` (T1-T5) and `STATUS.md` are written;
`tests/operations/test_issue243_closeproject_probe.py` is 5/5 green with
`run_mode: live` on `target_sandbox_path`; no code under `flexicon/code/` was
modified. **Resume from `specs/243-closeproject-save-guard/.crew-handoff.json`
-- its `next_entry` is authoritative: CP-A / T1, the P1 depth-read surface.**

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
- Open issue **#259** (`InflClassRA` does not exist on `IWfiMorphBundle`) is
  Tier 2, NOT in this campaign -- but its draft lives at
  `specs/254-getmorphtype-allomorph/reviews/cycle3-archivist-inflclass-issue-draft.md`
  and touches the same file as the `IWfiAnalysis` item above. Keep them together
  when the user rules on filing.
