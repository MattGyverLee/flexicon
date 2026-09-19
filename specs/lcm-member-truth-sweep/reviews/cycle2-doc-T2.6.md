# Doc Agent Report -- T2.6

**Date:** 2026-09-18
**Trigger:** `lcm-member-truth-sweep` campaign, task T2.6 (ruling C13)

## What was done

Copied Catalogue 2 verbatim from `specs/lcm-member-truth-sweep/reviews/cycle1-explore.md`
lines 346-408 (the `## CATALOGUE 2` header through the trailing `---`,
inclusive of the "Runner-up candidates" and "Explicitly cleared" blocks) into
a new durable file, `specs/lcm-member-truth-sweep/catalogue2-siblings.md`.

**Row count:** all 25 numbered rows copied, plus the 3 "runner-up" bullets
and the "explicitly cleared" bullet block -- nothing dropped, nothing
reworded. Diffed by eye against the source table row-by-row; every
file:line, member name, rationale clause, and verdict cell matches
character-for-character.

**Rows I could not copy cleanly:** none. All markdown table syntax
(pipes, bold spans, backtick spans) round-tripped without escaping issues.

Added, per task instructions: a provenance/ruling/confidence header, a
"Live upgrades" placeholder table (rows 1-5, 6-10, the `:825` carve-out, and
row 25/Q3, all marked `PENDING -- T2.5` / `PENDING -- T2.5b`), and a "Traps
for a future filer" section cross-referencing ruling C9 (compound_rule.py is
NOT #283) and the `IPhSegRuleRHS` `...OA` legitimacy note.

## Manifest note

`docs/MANIFEST.md` does not exist in this repo. Not bootstrapped here --
out of scope for this narrowly-scoped campaign task; flagging per Doc Agent
protocol for a future standalone manifest-bootstrap invocation.

## Confirmation

No production file and no test file was touched. Only two new files were
created: `specs/lcm-member-truth-sweep/catalogue2-siblings.md` and this
report. `git status` was not re-run by me beyond the file-write tool calls
themselves; no `Edit`/`Write` call targeted anything under `flexicon/` or
`tests/`.

---
**Doc Agent:** /lex-doc
