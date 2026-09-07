# Doc Agent Report

**Date:** 2026-09-07
**Trigger:** dispatch for issue #243 -- T5a (CHANGELOG stub) + C20 (contract record)

## Manifest entries reviewed

`docs/MANIFEST.md` does not exist in this repo -- no manifest bootstrap was
in scope for this task (two surgical writes only), so this was not
attempted. Both target docs were located directly:
- `CHANGELOG.md` -- trigger matched: yes (per spec.md C19/C8, T5a is a
  pre-authorised, ruling-independent stub noting T3's shipped guard).
- `specs/243-closeproject-save-guard/spec.md` -- trigger matched: yes (per
  task instruction to record C20 as the next frozen contract entry).

## Drift findings

| Doc | Finding | Severity | Action |
|---|---|---|---|
| `CHANGELOG.md` | `[Unreleased]` had no entry for commit `9dfd55d` (T3/T4, already on `main`) | missing entry | Patched |
| `specs/243-closeproject-save-guard/spec.md` | Contract list ended at C19; user's ruling on the fourth ask (SaveChanges depth guard) was not yet recorded | missing entry | Patched (added C20) |

No stale or drift findings against existing content -- `FLExProject.py:318-386`
(`CloseProject()`) was read directly and the CHANGELOG prose matches its
current shipped behaviour, including that the Phase-1 `else` branch still
logs at `debug` (T7/C14 not yet landed, correctly not claimed as shipped).

## Patches applied

### 1. `CHANGELOG.md` -- new `### Fixed` entry under `[Unreleased]`

Inserted immediately after the existing `### Changed` block (the #254
morph-bundle entry) and before `## [4.5.2] - 2026-08-19`. New entry
(paraphrased structure; see file for exact prose):

- Lead bullet: `FLExProject.CloseProject()` no longer skips `usm.Save()` if
  its own `EndNonUndoableTask()` mirror call raises (#243) -- describes the
  two-part guard (HasOpenSessionTask() check first, try/except wrap second),
  states End-then-Save order is unchanged, and cites the live verification
  (`target_sandbox_path` tempdir copy, `run_mode: live`, real Target never
  opened, no restore script run; 0/25 -> 25/25 on the forced-double-End
  scenario).
- Second paragraph (bold-led): explicitly states this does **not** fix the
  incident #243 was filed about -- names the separate SaveChanges()-at-
  CurrentDepth==1 chain, the `Commit at wrong place.` raise, the 0/25
  re-read from the still-open project *before* CloseProject() is entered,
  and that CloseProject() currently returns normally (no error) on that
  path. Both halves of the C17 ceiling are present; no claim that #243 is
  resolved.
- Third paragraph: documents the two newly-public members shipped in the
  same window -- `CurrentDepth` (raw int passthrough) and
  `HasOpenSessionTask()` (unconditionally `False` under `undoable=True`),
  both raising `FP_ProjectError` on closed/never-opened rather than
  degrading to `0`/`False`.

No `.fwdata` claim was made anywhere in the entry (C10 constraint honoured).
No mention of a SaveChanges() guard as shipped or planned (constraint
honoured -- C20/the fourth ask is not referenced from the CHANGELOG entry
at all).

Exact insertion point: between the line ending `actionable error instead of
a raw pythonnet \`TypeError\`.` (end of the #254 entry) and
`## [4.5.2] - 2026-08-19`.

### 2. `specs/243-closeproject-save-guard/spec.md` -- new `### C20`

Appended after C19 (ending "...whether `SaveChanges()` is getting a
guard." / "This decision only establishes that it is *separable* and that
deferring it has a real, named cost.") and before the `---` / `## Open
questions -- do not silently decide` divider, matching the existing
`### C<n> -- <title>` heading format used by C1-C19.

Content: records the user's verbatim ruling, states (a) is APPROVED IN
SUBSTANCE with C16 cross-reference, states the constraint is
transaction/depth correctness only (not sharing exclusivity), records the
premise correction (zero sharing-based refusals in `flexicon/code/`;
`RefreshFromDisk()` docstring at `FLExProject.py:772` is support not
refusal; `CustomFieldOperations.py:306` is a depth refusal tied to issue
#21, not an exclusivity refusal), states the one concrete hazard (a blanket
`CurrentDepth > 0` refusal would block the documented
`RefreshFromDisk()` -> `SaveChanges()` recovery workflow) routed to
T8a/P-10 with the resulting shape to be frozen as C21, and records task
numbers T8a/T8b. Prose was tightened to house style (bold-led clauses,
`--` em-dash convention, no meaning changes) but substance is unaltered
from the task's supplied text.

## Manifest updates

None -- no `docs/MANIFEST.md` exists in this repo; out of scope for this
task per the narrow two-task brief. Flagged as a gap below.

## Open follow-ups

- `docs/MANIFEST.md` does not exist for this repo. If `/lex-doc` is
  invoked again outside a narrowly-scoped task, a manifest bootstrap
  (Scenario 3) should run first.
- The spec.md status header (line ~35, "Contract is now **C1-C19**") was
  deliberately NOT updated to C1-C20 -- out of scope for this surgical
  task, and the header already carries its own "AS OF SPURT 5 ... out of
  date, take current state from below" disclaimer. Flagging so a future
  pass (or `/lex-lead`) updates it in the same pass as the next status
  refresh rather than it being silently stale.
- T5b (the prominent P2 release note + `SaveChanges()` docstring
  correction + Q4 placement) remains gated behind T7 and C20/C21's
  eventual guard shape, per C19 -- not attempted here.

---
**Doc Agent:** /lex-doc
