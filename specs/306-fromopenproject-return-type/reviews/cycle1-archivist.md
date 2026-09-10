# Archivist Investigation: companion issue draft for flexicon#306 (option 1, downstream half)

**Date:** 2026-09-10
**Repo of record for this file:** flexicon (draft targets FlexToolsMCP)
**Action:** Draft only -- nothing filed, moved, or edited. Read-only per task.

## Dedup check

`gh issue list --repo MattGyverLee/FlexToolsMCP --state all` (searched for
pyi/stub/return-type/annotation terms, all 29 results reviewed): no open or
closed issue proposes stub-preferring return-type extraction. Nearest
neighbors are #130 (bug, P1, open -- "Unguarded mutations reached through
FromOpenProject bypass every write gate (facade receiver is untyped)") and
#124 (GetAll behavioral-collection contract vs. index shapes). Neither is a
duplicate; #130 is the issue this companion strengthens (see body). No
conflict with #131 or #7 either (those concern a separate, already-drafted
stripping-FP issue sitting uncommitted in the same checkout -- see blocker
below).

## BLOCKER -- surfaced per task instructions

The FlexToolsMCP checkout (`D:\Github\_Projects\_LEX\FlexToolsMCP`) is on
branch `flexicon-project-bridge-mcp` with a **dirty tree**, and
`specs/flexicon-project-bridge/.crew-handoff.json` is in status
`needs_human`. Its blocker: the user must authorize disposition of an
**uncommitted `validators.py` diff (+183/-38)**, and its `qc_of_new_code`
gate is **OPEN**. `validators.py` owns `certify_script_readonly()`, whose
shape table is the natural evidence source for this companion issue's
verification section.

Consequently: the proposed evidence for this companion -- a before/after
`python -m flextoolsmcp.refresh` showing `FLExProject.FromOpenProject`
flipping `return_type` from `''` to `'FLExProject'`, plus the
`certify_script_readonly()` `fx.*` shape rows flipping to "yes" -- **cannot
be produced cleanly until that tree is settled**, because the two changes
(the pending Finding A/B write-gate fix and this new stub-preference
capability) would be conflated in one diff. I did not run `refresh` or any
test in that repo, per instructions.

## Recommended disposition for #306 (flexicon, upstream)

Leave #306 open as-is, scoped to the upstream half only (flexicon side of
option 1, if any remains) or simply as the tracking issue that references
the new downstream companion once filed -- do not close or edit it.

## Ready-to-paste issue for MattGyverLee/FlexToolsMCP

---
**Title:** Prefer sibling `.pyi` stub over docstring parsing for return-type extraction

**Body:**

## Summary

`flexicon_analyzer.py` extracts a function's return type solely by regex
over its docstring's `Returns:` section. When a `.pyi` stub sits alongside
the source and already carries the correct return annotation, the indexer
ignores it. This is the downstream half of the fix proposed in
`MattGyverLee/flexicon#306` (option 1); the upstream repo owner asked that
it be split into a companion here rather than moved wholesale, since the
indexer lives in this repo. flexicon#306 stays open for its own scope.

## Current behavior (verified)

- `src/flextoolsmcp/flexicon_analyzer.py:284` extracts the return type via
  `PATTERN_RETURN_TYPE` (line 44):
  `r'^([A-Za-z_][\w\[\], ]*?):\s+'`, applied only to the first line of a
  Google-style `Returns:` docstring section. Nothing else is consulted.
- `grep -rn "\.pyi" src/` returns nothing -- the analyzer has zero stub
  awareness today. This is a new capability, not a small tweak.
- In upstream flexicon, `flexicon/code/FLExProject.py` has 168 public
  defs: 87 have a `Returns:` block, 81 do not, and 0 carry a runtime
  return annotation. Repo-wide, flexicon has ~1639 public defs and only
  ~17 (~1%) are annotated. The docstring-only path will keep producing
  gaps like this indefinitely, not just for `FromOpenProject`.
- `FLExProject.pyi:210` already carries the correct
  `-> "FLExProject"` for `FromOpenProject`. A stub-preferring reader
  would resolve this immediately, with no upstream docstring change
  required.

## Proposed change

Teach the analyzer to check for a sibling `.pyi` file next to the module
being indexed, and prefer its return annotation over docstring parsing
when the two disagree or the docstring is silent. Docstring parsing
remains the fallback for modules with no stub.

## Related

- Companion of `MattGyverLee/flexicon#306` (upstream half stays there).
- Strengthens `#130` ("Unguarded mutations reached through
  FromOpenProject bypass every write gate (facade receiver is untyped)",
  P1): #130 already lists "read the `.pyi` return type" as its option 1.
  This issue is that option, generalized to all indexed functions rather
  than just `FromOpenProject`. #130's options 2 and 3 (runtime guards /
  wrapper-level typing) are explicitly **out of scope** here -- this issue
  covers indexer-side stub preference only.

## Priority

Proposing **P2 / non-urgent**, not P1. Both this issue and the
`FromOpenProject` case it fixes are demoted: this should happen because
the indexed annotation ought to be correct, not because anything is
currently unblocked or unsafe as a result of the gap. `#130` retains its
own priority independently for the write-gate-bypass angle.

## Verification

A before/after `python -m flextoolsmcp.refresh` diff should be captured,
showing `FLExProject.FromOpenProject`'s `return_type` moving from `''` to
`'FLExProject'`, together with the `certify_script_readonly()` `fx.*`
shape rows in `validators.py` flipping to "yes" for calls made through a
`FromOpenProject`-typed receiver.

**Note:** this evidence cannot be produced right now. The checkout
(`flexicon-project-bridge-mcp` branch) currently has an uncommitted,
unrelated `validators.py` diff (+183/-38) awaiting user disposition, with
its `qc_of_new_code` gate open (see
`specs/flexicon-project-bridge/.crew-handoff.json`). Running `refresh` or
touching `validators.py` before that tree is settled would conflate this
issue's evidence with the pending Finding A/B fix. Evidence should be
captured only after that tree is committed/resolved.

---

## Files referenced (read-only, flexicon repo)
- `D:\Github\_Projects\_LEX\FlexToolsMCP\src\flextoolsmcp\flexicon_analyzer.py` (facts reused, not re-verified this session)
- `D:\Github\_Projects\_LEX\FlexToolsMCP\specs\flexicon-project-bridge\.crew-handoff.json` (read this session to confirm blocker)

## Doc handoff
- N/A -- read-only investigation, no code or doc change made.

## Pending follow-ups
- User must resolve the `flexicon-project-bridge-mcp` `validators.py`
  uncommitted diff before this companion's verification evidence can be
  captured.
- User decides whether/when to file this companion issue in
  MattGyverLee/FlexToolsMCP.

---
**Archivist:** /lex-archivist

---

## LEAD CORRECTION (cycle 1 synthesis, 2026-09-10)

**The BLOCKER section above is STALE and must not be carried into the
filed issue.** Verified in `D:\Github\_Projects\_LEX\FlexToolsMCP` at
synthesis time:

* `git status --porcelain` -> **empty**. The tree is clean.
* `HEAD` = `23ff2c8 "fix: two write-gate bypasses that certified
  unguarded writes read-only"` -- the `validators.py` diff described as
  "uncommitted (+183/-38) awaiting user disposition" was committed.
* `specs/flexicon-project-bridge/.crew-handoff.json` reads
  `"status": "feature_complete"`, `"uncommitted": []`, and
  `gates.qc_of_new_code = "PASS -- lex-qc APPROVE"` (not OPEN).
* That json also records the stripping-FP issue as **filed with user
  authorization**, not left drafted.

Consequence: the drafted companion's "**Note:** this evidence cannot be
produced right now" paragraph is false and should be **deleted** before
the user files the issue. The before/after `refresh` evidence can be
captured now against a clean `23ff2c8`.

**Also correct before filing:** the body's "`FLExProject.py` has 168
public defs: 87 have a `Returns:` block, 81 do not" is module-scope.
Class-scope (the relevant unit) is **166 / 87 / 79** pre-edit and
**166 / 88 / 78** post-edit. Issue #306's own `166/79` was right.

Verified sound and left as-is: the dedup check (no FlexToolsMCP issue
proposes stub-preferred extraction; #130 and #124 are neighbors, not
duplicates), `FLExProject.pyi:210` really does carry
`-> "FLExProject"`, and the repo-wide census "~1639 public defs, ~17
(~1%) annotated" reconciles exactly for `flexicon/code` (1639 defs, 18
annotated post-edit = 17 pre-edit).

**Filing remains unauthorized.** Draft only; only the user files issues.
