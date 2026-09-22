# STATUS -- constitution-v2-amendment

**Updated:** 2026-09-22
**Spurt 1 complete (cycles 1-2).** Status: `needs_human`.

## What landed this spurt

**T1 -- Constitution amended to v2.1.0** (`.specify/memory/constitution.md`)
All five instructed edits applied; new amendment-log entry sits above the
2.0.0 one. Principle II now reads: reads unrestricted (any project, read-only,
no gate); writes bounded to Target / Sena 3 / sandbox; agents perform live
writes unattended. Principle VII clarified: a new keyword whose default
preserves a Principle V defect is not additive growth. Gate 5 reworded.
Independently verified in-file by the main session.

**T2 -- `__all__` added to `flexicon/__init__.py`** (99 names, sorted)
Principle VII now names `__all__` the single source of truth for "published".
Verified purely additive by an independent AST re-scan: |P| = 99,
|__all__| = 99, zero names dropped, zero phantom entries. **No narrowing, so
no Principle VII withdrawal occurred and no `BREAKING CHANGE:` footer is due.**
Package imports cleanly in this environment (pythonnet + FieldWorks live).

**T3 -- Propagation of the amended text**
- `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md` -- both required invocations now
  quoted; the bare-pytest prohibition rescoped to *unscoped collection*
  rather than to writing itself.
- `docs/RELEASING.md` -- same two corrections against the release checklist.
- Six closed-feature spec files carry dated superseding notes; every original
  line retained unedited as historical record:
  `specs/write-path-transactions/{plan,spec}.md`,
  `specs/lcm-member-truth-sweep/{STATUS,spec}.md`,
  `specs/242-paragraph-whitespace/tasks.md`,
  `specs/243-closeproject-save-guard/tasks.md`.

**T4 -- Read-scope sweep** (`reviews/cycle2-read-scope.md`)
Three true read-confinement defects, all the same shape: a "The two live
projects" heading whose "Use for" column hands read-path coverage to Sena 3
while nothing states reads are unrestricted, so the table reads as the
complete set of openable projects. Nothing anywhere gates a read-only open.
`.claude/bugfix-loop.md:144-149` already carries correct model wording, and
`tests/operations/test_parser_live.py` already opens IndonesianHC-Complete and
Malay Parsing read-only -- reads range past the two projects in practice.

**T5 -- Ratchet design** (`reviews/cycle1-ratchet-design.md`), design only.
7-file manifest, AST-based scanner, ~1462-entry baseline, `--baseline` regen
path, `.githooks` commit-msg guard. Not built this spurt.

## Not done -- carried forward

- **`flexicon/CLAUDE.md` (user contract).** TWO cycle-2 reports target the same
  section, lines 124-132, and did not reconcile with each other: cycle2-propagation
  rewrites it for the WRITE rule, cycle2-read-scope wants the heading retitled
  "The two live **write** projects" plus a reads-unrestricted sentence. The user
  must receive ONE merged diff, not two. Blocked on the user.
- **`C:\Users\thoua\.claude\agents\lex-verification.md:39-44`** -- same defect, but
  the file is user global agent config outside this repo. Propose only; never
  edit on a specialist's say-so. Blocked on the user.
- **`tests/LIVE_TESTING.md:13-27`** -- the strongest of the three defects and the
  only repo-owned, non-contract one. Land it before the spurt commit.
- **Gate 1 evidence.** Neither required invocation has been run this spurt, and
  `flexicon/__init__.py` changed at import time. Both must run with counts quoted
  before anything here is reported complete.
- **The ratchet build** -- the whole of the next spurt.

## Next pickup

Spurt 2 builds the Principle VII / Gate 5 outbound-surface ratchet from
`reviews/cycle1-ratchet-design.md`. One reconciliation is mandatory first:
the design rooted Set A in the 97 names bound by `from .code.X import (...)`,
but T2 landed `__all__` with **99** names, and amended Principle VII makes
`__all__` -- not the import bindings -- the single source of truth. Set A must
read `__all__`; the baseline lands at ~1464 entries, not 1462.
