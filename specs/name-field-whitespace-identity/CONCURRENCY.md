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

**AMENDED 2026-09-07 after re-derivation against committed HEAD
(`reviews/cycle2-baseline.md`). The other crew has now COMMITTED
(`4aca74a`, `61e0f87`, `e17cd7d`); their work is no longer uncommitted, and the
first version of this section is superseded. Use the list below, not the one it
replaced, and not the campaign's old fixed 1292/483 gate — that absolute is VOID
while they are active.**

Re-derived baseline at HEAD: **`3 failed, 1292 passed, 498 deselected, 0 errors`.**

All three items this file originally named as known-foreign now **pass or collect
clean** — `test_natural_class_feature_sync.py`'s collection errors, and both
ratchets (`test_no_new_type_dependencies`, `test_no_new_unbracketed_mutations`).
They were transients of the other crew's uncommitted state and are resolved. Do
not carry them forward.

The current known-foreign set, **red against committed code and therefore a
legitimate repo state rather than a transient**:

- `tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`
- `tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_depth_restored_on_exception`
- `tests/test_flexlibs2_alias_ratchet.py::TestFlexlibs2AliasIsInboundOnly::test_no_executable_flexlibs2_imports_outside_alias_package`

The distinction matters and changes how you treat them: a transient clears itself,
so "name it as foreign and move on" was right. These do **not** clear themselves.
Treat them as the expected red baseline — your run should show these three and no
others. **If your run shows a fourth, or one of these three changes its failure
message, STOP and report.** Do not fix them; they are outside this feature.

`specs/duplicate-signature-harmonisation/` (untracked) is **attributed**: orphaned
evidence from already-merged issue #246, dated 2026-08-18. It belongs to neither
crew's current work. Leave it alone; it is not a foreign-failure source.

## Line numbers in spec.md and tasks.md are already stale

The other crew's `+423` lines moved shared code. Concretely, `spec.md` C7 cites
`_ValidateStringNotEmpty` at `BaseOperations.py:2491`; it is now at **`:2915`**,
and its whitespace-only `FP_ParameterError` raise is at **`:2966`**. **Re-confirm
every line number against HEAD before editing at it.** Cite by symbol name where
you can; a stale line number in a brief is not authority to edit the wrong place.

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
