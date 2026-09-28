# Doc Agent Report -- T5 (Checkpoint 3, LAST task)

**Date:** 2026-09-07
**Trigger:** `tasks.md` T5 dispatch from `/lex-lead`
**Feature:** `name-field-whitespace-identity` (Q-242A, Q-242B)

No shell tool available; no `pytest`/`git` run. Docs-only task, no live
verification required. Main session commits.

## Read first (per brief)
- `tasks.md` Checkpoint 3 / T5, `STATUS.md` "Cycle 4 close", `spec.md` C1-C11
  (esp. C4, C6, C7, C11(c)).
- `CHANGELOG.md` precedent at the (pre-edit) #242 entry, now `:95`-ish;
  anchors re-derived by reading, not trusted from the brief.
- All four touched Operations files, read at HEAD to confirm current
  post-code-fix state before writing any docstring claim.

## CHANGELOG.md
Two **separate** entries added under `[Unreleased]` / `### Changed`, both
led `**BREAKING (behavioural): ...**`, following the #242 precedent
verbatim in form:
1. **Q-242A** -- persist (4 files, 6 sites) + comparison-symmetry (3
   sites) fix, bundled per C6's rationale. Discloses: Discourse has no
   dedup (C3 carve-out); `CreateSubitem` has no dedup (C5); Anthropology
   `Exists` deliberately untouched; **Q-242D** (whitespace-only still
   persists literal whitespace at 3 named sites, not fixed, Q-242C's
   call); **Q-DISC1** (`CreateChart` persist half `FAIL: unverified`,
   inspection-correct only) -- explicitly states "does not claim 8/8
   sites live-verified."
2. **Q-242B** -- `CheckOperations` silent-empty-name fix, separate entry
   per C6, classified `### Changed`/BREAKING (not `### Fixed`) to match
   this file's own precedent for exception-behaviour-changing bug fixes
   (the `SaveChanges()` entry). Rationale for divergence-from-default-call
   recorded inline: this is a bug fix that also changes what gets raised,
   same shape as the `SaveChanges()` precedent, not the plain `### Fixed`
   shape of the `CloseProject()` entry (which changed no exception type).
   States blast radius (external callers only) and the `_GetCheckList`
   live-verification dependency.

No entries authored for docstring-only changes (docstrings are not
CHANGELOG material).

## Docstrings -- 11 methods, all read at HEAD before editing
Added an inline `Args:`-section `Note:` (matching the existing #242 T3
precedent style in `ParagraphOperations.py`) to:
- `DiscourseOperations.CreateChart` (+ Q-DISC1 unverified caveat),
  `.SetChartName`
- `TextOperations.Create` (+ symmetric-dedup note), `.Exists`
  (comparison-symmetry note), `.SetName` (+ Q-242D note)
- `AnthropologyOperations.Create` (+ symmetric-dedup + Q-242D note),
  `.CreateSubitem` (+ no-dedup observation + Q-242D note), `.Find`
  (comparison-symmetry note)
- `CheckOperations.CreateCheckType` (+ Q-242B note), `.FindCheckType`
  (comparison-symmetry note), `.SetName` (+ Q-242B note)

`AnthropologyOperations.Exists` was **not** touched, per the brief.

**`FindCheckType` docstring RESOLVED, not appended.** Previously:
`Raises` promised `FP_NullParameterError: If name is None or empty`
(never true pre-fix) while `Notes` claimed "doesn't raise exception."
Now: `Raises` lists `FP_NullParameterError` (None only), `TypeError`
(non-`str`, Q-242B), `FP_ParameterError` (whitespace-only, Q-242B);
`Notes` states it returns `None` only when name is valid but no match
exists, and explicitly narrates the correction so a future reader isn't
puzzled by the diff. Also corrected the same previously-inaccurate
`Raises` shape at `CreateCheckType` and `SetName` (both claimed
`FP_NullParameterError: ... or empty`, which C7's shipped fix makes
newly, verifiably wrong -- `TypeError`/`FP_ParameterError` now apply).

**Not touched:** the pre-existing (and still-inaccurate) `Raises`
docstrings at `AnthropologyOperations.Create`/`CreateSubitem` and
`TextOperations.SetName` claiming `FP_NullParameterError: ... or empty`
for what is actually an `AttributeError` on non-`str` and a silent
persist on whitespace-only. That harmonisation is `Q-242C`'s scope
(C7(b)); fixing their docstrings without fixing their code would create
a NEW doc/code mismatch in the other direction, so left as-is and
flagged here for whoever picks up Q-242C.

## Mandatory disclosures -- confirmed present
- Q-242D: disclosed in Q-242A's CHANGELOG entry and in the 3 affected
  docstrings (`AnthropologyOperations.Create`/`CreateSubitem`,
  `TextOperations.SetName`).
- Q-DISC1: disclosed in Q-242A's CHANGELOG entry and in
  `CreateChart`'s docstring. **8/8 verified was never claimed.**
- No GitHub issues filed.

## Manifest
No `docs/MANIFEST.md` exists in this repo. Bootstrapping one is out of
scope for this narrowly-dispatched task (T5's brief is CHANGELOG +
docstrings only); flagging for a future standalone doc-audit invocation
rather than silently absorbing or expanding scope here.

## Files touched
- `D:\Github\_Projects\_LEX\flexicon\CHANGELOG.md`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\TextsWords\DiscourseOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\TextsWords\TextOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\Notebook\AnthropologyOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\System\CheckOperations.py`

## Open follow-ups
- C12/C13 verbatim transcription into `spec.md` is still outstanding per
  `STATUS.md` (not this task's scope; STATUS.md names it as an optional
  archivist pass).
- `Q-242C` docstring harmonisation at the 3 named `AttributeError` sites
  remains for whenever `Q-242C` is authorised.
- No commit performed -- main session's to do, per this task's hard
  constraint.

---
**Doc Agent:** /lex-doc
