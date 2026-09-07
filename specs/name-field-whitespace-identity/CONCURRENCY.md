# CONCURRENCY PROTOCOL — shared working tree

**Written by the main session, 2026-09-07. Binding on every agent working this feature.**

A **second crew, confirmed by the project owner as theirs and expected**, is working
in this same clone at the same time, committing under the same git identity. This is
not an anomaly to investigate or clean up. Work around it, precisely.

## What belongs to the other crew — DO NOT TOUCH, DO NOT STAGE, DO NOT REVERT

Files they were actively editing when this protocol was written:

- `flexicon/code/BaseOperations.py` (+423 uncommitted)
- `flexicon/code/Grammar/NaturalClassOperations.py`
- `tests/operations/test_natural_class_feature_sync.py` (+103 uncommitted)
- `specs/feature-structure-sync-gap/` (campaign queue item 3)
- `specs/250-writingsystem-activation/` (campaign queue item 4)

Their commits interleave with ours: `577dab3`, `a26d39c` are theirs; `bdbce02` is ours,
landing between them.

`BaseOperations.py` was ALREADY fenced off for this feature on design grounds
(lex-lead C4/C7: shared code is out of scope, `needs_human` if it must change). The
concurrency makes that fence absolute rather than merely a scope rule.

## Staging rule — never relax it

**Always `git add <explicit paths>`. NEVER `git add -A`, `git add .`, `git add -u`, or
`git commit -a`.** All four would sweep the other crew's in-flight work into our commit.
Before committing, run `git status --porcelain` and confirm every staged path is one you
authored. Four of our commits were audited against this rule and were clean; keep it that way.

Never `git checkout`, `git restore`, `git stash`, or `git reset` a path you did not
author — their uncommitted work is unrecoverable if discarded.

## The offline suite is RED for reasons that are not ours

As of writing, `python -m pytest tests -m "not requires_live_project" -q` gives roughly
`2 failed, 1286 passed, 491 deselected, 8 errors`. **The campaign's old fixed baseline of
1292 passed / 483 deselected is VOID for the duration.** Do not chase it, do not "restore"
it, and do not report it as a regression you caused.

Known-foreign failures, all traceable to the other crew's uncommitted `BaseOperations.py`:

- `tests/operations/test_natural_class_feature_sync.py` — collection errors (their file)
- `tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies`
  — a RATCHET test tripping on their new type dependencies
- `tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_no_new_unbracketed_mutations`
  — a RATCHET test tripping on their new mutations

Those two ratchet tests are the trap: they fail in files nobody here touched, because they
assert repo-wide properties. Seeing them red does NOT mean your change broke something.

## Measure a DELTA, never an absolute

Because their numbers move while you work, an absolute pass count proves nothing.

1. Run the offline suite and record the counts **immediately before** your first edit.
2. Make your change.
3. Run it again and record the counts.
4. **Only the delta between your own two runs is yours.** Report both raw numbers and the
   delta. Expected delta for a correct change: `passed` unchanged or up by the offline
   tests you added; `deselected` up by exactly the `requires_live_project` tests you added.
5. If a test fails in a file **you did not touch** and it is on the known-foreign list
   above, name it as foreign and move on. If it fails in a file you did not touch and is
   NOT on that list, STOP and report — that one may genuinely be yours.

Live verification is unaffected: sandbox fixtures are per-test tempdir copies, so
`run_mode: live` runs remain trustworthy. The `--collect-only` marker-count rule is
also unaffected and still binding — no tests collected is a ZERO, never a pass.

## If you find yourself needing one of their files

Stop and report `needs_human`. Do not edit it, do not work around it by copying code out
of it, and do not wait for them.
