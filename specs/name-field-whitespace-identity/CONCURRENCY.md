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

**RE-DERIVED AGAINST HEAD, 2026-09-07 (this cycle): the `:2915`/`:2966` figures
above are ALREADY STALE AGAIN.** Measured at HEAD: `_ValidateStringNotEmpty` is
`BaseOperations.py:3182`, its `TypeError` raise `:3230`, its whitespace-only
`FP_ParameterError` raise `:3234`; `_ValidateParam` is `:3014`. **Re-confirm
every line number against HEAD before editing at it.** Cite by symbol name where
you can; a stale line number is not authority to edit the wrong place -- that
rule is now proven twice over.

**THIRD DRIFT, measured at HEAD by `/lex-lead` at the cycle-3 checkpoint (same
day, after the other crew's `6643b48`): the `:3182`/`:3230`/`:3234`/`:3014`
figures above are ALSO ALREADY STALE.** Now: `_ValidateStringNotEmpty` is
`BaseOperations.py:3191`, `_ValidateParam` is `:3023`, `_ValidateParamNotEmpty`
is `:3085`. Do not trust this paragraph either -- **derive the number yourself,
in your own session, immediately before you edit at it.** Three drifts in one
day is the measurement; the rule is symbol-first, always.

Not drifted, confirmed at HEAD in the same sweep: `CheckOperations.py`'s three
coercion sites are UNCHANGED at `:196` (`CreateCheckType`, def `:146`), `:341`
(`FindCheckType`, def `:300`), `:432` (`SetName`, def `:397`) -- T4's targets
still match `tasks.md`. Re-confirm anyway.

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

## AMENDMENT 2 (2026-09-07, cycle 3) -- the staging window is a RACE; check at COMMIT time too

**Binding from T4 onward. This STRENGTHENS the staging rule above; it does not
replace it. Authored by `/lex-lead` at the cycle-3 checkpoint, on `/lex-programmer`
(T3)'s recommendation, after a real incident.**

During cycle 3, T3's first `git commit` swept in five of the other crew's files
(`flexicon/code/BaseOperations.py`, two `Grammar/` files, two
`specs/feature-structure-sync-gap/` files). **T3 had followed the rule exactly as
written**: it ran `git status --porcelain` before its `git add`, and the tree was
clean at that instant. The other crew's own `git add` landed **in the window
between that check and T3's commit**, so their paths were already sitting in the
shared index by commit time. The pre-`add` check is structurally incapable of
detecting this. It is a race, not a lapse of discipline -- and it will recur.

T3 self-caught it via `git show --stat HEAD`, corrected with `git reset --soft
HEAD~1` followed by an index-only `git reset HEAD -- <foreign paths>` (zero
working-tree bytes touched, verified by diff before and after), and re-committed
clean. `/lex-lead` independently audited the resulting history and confirms it is
clean: `7bc6d01` contains only its own evidence file, and the other crew's work
landed separately as their own commit `6643b48`.

Because the index is shared and they can stage at any instant, **every commit made
while they are active must be bracketed on both sides**:

1. `git status --porcelain` immediately BEFORE `git add` (the existing rule).
2. `git add <explicit paths>` -- never `-A`, never `.`, never `-u`, never
   `git commit -a`.
3. **`git status --porcelain` AGAIN immediately BEFORE `git commit`.** Read the
   STAGED (first-column) entries specifically. If any staged path is one you did
   not author, run `git reset HEAD -- <that path>` **before** committing. Never
   `git checkout` / `git restore` / `git stash` it -- that destroys their
   unrecoverable uncommitted work.
4. **`git show --stat HEAD` immediately AFTER `git commit`.** Confirm the file
   list is exactly what you intended and nothing more.
5. If a foreign path did get committed anyway: `git reset --soft HEAD~1`, then
   index-only `git reset HEAD -- <foreign paths>`, then re-commit. `--soft` and
   an index-only `git reset HEAD -- <path>` are the ONLY two reset forms
   authorised in this clone; both touch zero working-tree bytes. **`git reset
   --hard` is FORBIDDEN here while the other crew is active**, as is any rewrite
   of a commit that is not yours.
6. **Report the outcome of steps 3 and 4 in your task report, even when clean.**
   A line of the form "no foreign paths staged at commit time; `git show --stat
   HEAD` lists only <N> files, all mine" is REQUIRED, not optional. Silence is
   read as "not checked".

Steps 3 and 4 cost seconds and catch the only failure mode the pre-`add` check
cannot. Skipping them is a protocol violation **regardless of whether the commit
happened to come out clean** -- T3's incident is proof that a clean pre-`add`
check predicts nothing about the index a moment later.


## AMENDMENT 3 (2026-09-07, cycle 4) -- `git stash` is authorised ONLY with an explicit pathspec

**Binding from T5 onward. Authored by `/lex-lead` at the cycle-4 checkpoint,
mirroring `spec.md` C13(c). This CLOSES A GAP in the staging rule above; it
does not contradict it.**

The staging rule already forbids stashing **a path you did not author**. It did
not say, in terms, that a **bare** `git stash` is forbidden -- and AMENDMENT 2
step 5's "only two authorised forms" clause is scoped to `git reset` forms, not
to `git stash`. A reader had to derive the prohibition. State it directly:

- **`git stash push -- <your own path>` is the ONLY authorised stash form in
  this clone.**
- **A bare `git stash` is FORBIDDEN, at the same level as `git reset --hard`**,
  as are `git stash -u`, `git stash --all`, and `git stash push` with no
  pathspec. All of them operate on the WHOLE working tree, which here means the
  other crew's uncommitted, unrecoverable in-flight work would be swept into a
  stash they do not know exists.
- Stash only paths you authored. Never stash, `git checkout`, or `git restore` a
  path you did not author -- unchanged from the staging rule above.
- After any stash, confirm **`git stash list` is EMPTY** before you finish, and
  report that it is. Never carry a stash across a checkpoint or a handoff.
- Do not use a stash to "tidy" the working tree. Its only authorised use here is
  the narrow one in C13(d): recovering a correct pre-edit offline baseline after
  an ordering slip, when the baseline was not taken first as required.

Occasioned by T4 (cycle 4), which used a correctly pathspec'd stash to recover a
genuine pre-edit baseline -- the safe form -- and self-disclosed it. The delta
was accepted (`spec.md` C13(b)). This amendment exists so that the NEXT agent,
reading only that a stash-based recovery was accepted, does not reach for the
bare form.

**Authorised destructive-adjacent git operations in this clone, consolidated:**
`git reset --soft HEAD~1`; index-only `git reset HEAD -- <path>`;
`git stash push -- <your own path>`. **Everything else is FORBIDDEN while the
other crew is active** -- including `git reset --hard`, bare `git stash`,
`git checkout`/`git restore` of any path, and any rewrite of a commit that is
not yours.

## If you find yourself needing one of their files

Stop and report `needs_human`. Do not edit it, do not work around it by copying code out
of it, and do not wait for them.
