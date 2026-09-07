# Cycle 1 -- Archivist report: name-field-whitespace-identity spec/tasks/status scaffold

**Status: delivered, no contradictions found.** Populated the new feature
directory with `spec.md`, `tasks.md`, `STATUS.md`, `.crew-handoff.json`,
following `specs/242-paragraph-whitespace/`'s structure, and updated
`specs/tier1-silent-data-loss/QUEUE.md` to authorise Q-242A/Q-242B and spin
them out to sub-item 2a. Zero lines under `flexicon/` changed. No commit
made -- left for the main session to review and commit.

## What was done

- **`specs/name-field-whitespace-identity/spec.md`** -- authority/provenance
  section 0 (recording the mid-cycle change: `/lex-lead` ruled C1-C8, the
  owner then placed the identity question C3 under `/lex-domain`'s
  authority, `/lex-domain` independently re-tested and ACCEPTED option
  (i)); problem statement; contract items C1-C8 transcribed substantially
  verbatim from the dispatch brief, each folding in the live PN-measurement
  citations and lex-domain's Q1-Q6 in full; a recorded-not-ruled section on
  the `CheckOperations._GetCheckList()` bug found in cycle 1 (flagged
  explicitly as a live-verification dependency for future Q-242B tasks,
  not fixed, not filed); a contradictions-checked section; and an open
  questions section (none left open in scope).
- **`tasks.md`** -- a READ FIRST section carrying forward #242's standing
  gates (target_sandbox only, live REQUIRED, --collect-only marker
  derivation, no bare pytest, C28 predict-then-commit as two commits, no
  emoji, no GitHub issues) plus CONCURRENCY.md's DELTA rule replacing the
  fixed offline baseline; Checkpoint 1 (this spurt, DONE); Checkpoint 2 --
  one task per family in the requested order (T1 Discourse: persist-only,
  no comparison exists per C3's carve-out; T2 Text: persist + comparison
  symmetry together; T3 Anthropology: persist + comparison symmetry
  together, with the CreateSubitem-has-no-dedup observation carried
  forward; T4 Check: Q-242A comparison-symmetry/persist fix AND the
  distinct Q-242B fix landed in ONE commit at the same expressions per C6,
  tracked with two separate evidence files/severity labels); Checkpoint 3
  (T5, docs dispatch to `/lex-doc`, two separate CHANGELOG entries per C6).
- **`STATUS.md`** and **`.crew-handoff.json`** -- mirroring #242's
  structure, both flagging the concurrency situation prominently and
  recording `next_entry` as T1 (DiscourseOperations).
- **`specs/tier1-silent-data-loss/QUEUE.md`** -- added table row **2a**
  (`name-field-whitespace-identity`, `active`); corrected the stale item-2
  table row and per-item banner to `done` (the closure had landed in
  `.crew-handoff.json` at commit `249863d` but was never reflected in this
  file's own table/banner until this pass -- recorded as a Campaign Log
  entry, not silently fixed); added a new "### 2a." per-item entry-
  conditions section; added AUTHORISED-and-MOVED banners above the
  original Q-242A and Q-242B text in "Awaiting user approval" (kept
  verbatim below the banner as the audit trail, matching the existing
  SaveChanges-ask precedent); left Q-242C's entry completely untouched,
  still unauthorised; added two Campaign Log entries (item 2's belated
  closure record, and sub-item 2a's authorisation + spurt 1). Did **not**
  touch queue items 3 or 4, did **not** open
  `specs/feature-structure-sync-gap/` or
  `specs/250-writingsystem-activation/`, and did **not** edit
  `specs/tier1-silent-data-loss/.crew-handoff.json` (it already showed as
  modified in `git status` before this task began, and was left alone
  throughout, per instruction that it is the main session's file).

## Concurrency

Read `specs/name-field-whitespace-identity/CONCURRENCY.md` first, as
instructed, and treated it as binding throughout. This task made zero
`Edit`/`Write` calls under `flexicon/`. At the end of this pass, `git
status` no longer shows the other crew's `flexicon/code/BaseOperations.py`,
`NaturalClassOperations.py`, or `PhonemeOperations.py` as modified (they
were present as modified at the START of this task, per the initial
`gitStatus` snapshot, and are now gone -- consistent with that crew
committing their own work during this task's wall-clock window, exactly
as `CONCURRENCY.md` describes as expected). No path belonging to that
crew was staged, reverted, or restored by this task.

## Contradictions between the probe/domain reports and C1-C8

**None found.** Specifically checked and confirmed consistent:

- **C1** (needle-only strip): PN2/PN3/PN4 in
  `evidence/live-probe-cycle1.md` all measured exactly as predicted --
  no refutation.
- **C2** (persist-only fix produces duplicates): PN8's binding claim
  (Create succeeds despite a pre-existing collision, two objects result)
  MATCHED. One flagged, **non-binding** sub-detail did NOT match verbatim:
  the predicted byte-identical second record was instead measured as the
  already-stripped variant, because the probe exercised `Create()`'s
  CURRENT (pre-C4-fix) persist behaviour for the second object, not the
  post-fix behaviour C2's illustrative wording assumes. The programmer
  flagged this as non-binding BEFORE the run and it does not weaken C2's
  binding claim; I folded it into `spec.md` C2 as an explicit correction
  note rather than treating it as a contradiction.
- **C3** (whitespace-insensitive dedup ruling): `/lex-domain`'s report
  independently re-derived the SAME answer as `/lex-lead`'s option (i)
  (Q5 "ACCEPTED") from its own FLEx-domain grounds, and its Q6 directly
  answers the whitespace-only-name question C7 had left implied
  (`FP_ParameterError` on both branches). Agreement, not contradiction.
- **C4-C8**: not empirically testable by a probe (they specify a fix
  shape, scope, bundling rationale, and an acceptance pin for code not
  yet written) -- no contradiction possible at this checkpoint; nothing
  in the probe or domain report conflicts with them.

The one genuinely new fact from cycle 1 not present in the dispatch brief
-- the `CheckOperations._GetCheckList()` / `GetInstance`/`GetService`
bug -- is not a contradiction of any C-item; it is an orthogonal,
unplanned discovery, recorded in `spec.md` section 3 exactly as
instructed (not fixed, not filed as a GitHub issue), with its one direct
consequence (a live-verification dependency for future `CheckOperations.py`
tasks) stated explicitly in both `spec.md` and `tasks.md`.

## Files

- `specs/name-field-whitespace-identity/spec.md` (NEW)
- `specs/name-field-whitespace-identity/tasks.md` (NEW)
- `specs/name-field-whitespace-identity/STATUS.md` (NEW)
- `specs/name-field-whitespace-identity/.crew-handoff.json` (NEW)
- `specs/tier1-silent-data-loss/QUEUE.md` (MODIFIED -- table, item-2 banner,
  new "2a" section, Q-242A/Q-242B authorisation banners, two Campaign Log
  entries)
- This report: `specs/name-field-whitespace-identity/reviews/cycle1-archivist.md`

No commit made. `git status --porcelain` at the end of this pass shows
these files as untracked/modified, ready for the main session's review.
