# Cycle 2 Baseline Re-derivation -- name-field-whitespace-identity

**Read-only task.** No source, test, or spec files were edited. Only this
report file was written.

## TREE STATE

`git log --oneline -6`:
```
a3fc8e3 spec(name-field-whitespace-identity): freeze C1-C8; dedup strips needle, never haystack
e17cd7d docs(feature-structure-sync-gap): T4 -- live evidence + cycle-4 report
61e0f87 test(feature-structure-sync-gap): T4 -- live coverage for _ApplyFeatureStruc
3d357d8 Merge branches main and main of https://github.com/MattGyverLee/flexicon
ec54432 Rename flexlibs2 package to flexicon (#241)
4aca74a refactor(feature-structure-sync-gap): T4 -- extract BaseOperations._ApplyFeatureStruc
```

`git status --porcelain`:
```
 D .claude/ralph-loop.local.md
?? .vscode/
?? specs/duplicate-signature-harmonisation/
```

Confirmation: the three commits named in the task brief (4aca74a, 61e0f87,
e17cd7d) are present in the committed history, as is the other crew
feature-structure-sync-gap work more broadly (also 577dab3, a26d39c further
back). CONCURRENCY.md's premise -- their work was uncommitted -- no longer
holds; the numbers in CONCURRENCY.md must be treated as void, per the task
brief, until re-derived (this report is that re-derivation).

Note on an apparent anomaly, resolved: the system-provided git snapshot at
session start listed a different set of recent commits (cfc86af, 1790fcc,
c18b43b, cfbfd43, 625fb7c) that do not appear in the -6 log above.
Investigated with git merge-base --is-ancestor cfc86af HEAD -- result: YES.
These commits are real ancestors of HEAD; they sit on the other side of the
3d357d8 merge commit, so a linear -6 view from HEAD does not surface them
even though they are already integrated. This is merge topology, not
evidence of a rewritten or diverging history.

## DUPLICATE-SIGNATURE ATTRIBUTION

specs/duplicate-signature-harmonisation/ contains exactly one file:
evidence/live-issue-246.md (no spec.md, no STATUS.md).

Its header identifies it as live verification evidence for GitHub issue #246
(every Duplicate() now accepts both deep= and insert_after=), citing commits
cc454c02 and 4c496c2d as the commits under test, dated 2026-08-18 in the file
body. Filesystem birth/modify time on the file is also 2026-08-18 03:37,
three weeks before CONCURRENCY.md was written (2026-09-07) and before the
current name-field-whitespace-identity / feature-structure-sync-gap work
began.

Both cited commits exist on main and are already merged (confirmed via
git cat-file -t and git branch --all --contains, both returning main only,
commit dates 2026-08-18 11:18/11:28 +0300, author Matthew Lee).

Conclusion: this is neither the currently-active other crew nor a current
spurt of this session. It is orphaned evidence from an earlier,
already-completed, already-merged piece of work (issue #246 Duplicate()
signature harmonisation) whose verification-evidence file was apparently
never git-added at the time, and has sat untracked ever since. It is not on
CONCURRENCY.md's known-foreign list because CONCURRENCY.md's author had no
reason to know about a three-week-old untracked leftover -- it predates
that protocol entirely. It does not belong to the live other crew described
in CONCURRENCY.md (their named files/specs are all dated 2026-09-07 and
reference feature-structure-sync-gap / 250-writingsystem-activation, not
issue #246).

Recommendation: leave it untouched (per this task's read-only mandate); a
future housekeeping pass, not this cycle, should either commit it (if the
evidence is still wanted) or delete it -- a decision for a human/lex-lead,
not for this agent.

## OFFLINE COUNTS

Command run exactly as specified:
```
python -m pytest tests -m "not requires_live_project" -q
```

Tail line:
```
3 failed, 1292 passed, 498 deselected, 12 warnings in 29.57s
```

Zero collection errors this run (no "error" entries in the summary; full
output grepped for ^ERROR returned nothing).

This differs from CONCURRENCY.md's stale snapshot (2 failed, 1286 passed,
491 deselected, 8 errors) in every field, confirming the numbers there are
void and must not be quoted going forward.

## FAILURE CLASSIFICATION

Full failing-test list from the run above:

1. tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception
2. tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_depth_restored_on_exception
3. tests/test_flexlibs2_alias_ratchet.py::TestFlexlibs2AliasIsInboundOnly::test_no_executable_flexlibs2_imports_outside_alias_package

None of the three previously-named known-foreign items appear in this list
at all (see RATCHET VERDICT -- two of the three now pass outright, and the
third's collection-error file now collects cleanly). All three failures
above are (b) NEW, not previously listed in CONCURRENCY.md.

### 1-2. test_transaction_rollback.py::TestPhase2JoinOrOpen (both failures)

```
TypeError: No method matches given arguments for UndoableUnitOfWorkHelper..ctor:
(class tests.operations.test_transaction_rollback._FakeActionHandler,
 class str, class str)
flexicon/code/transaction.py:122: TypeError
```
A pythonnet overload-resolution failure when the test's _FakeActionHandler
double is passed into the real UndoableUnitOfWorkHelper .NET constructor.
git log on flexicon/code/transaction.py and the test file shows the last
touches were fe42ddf5 / 287bb20e (write-path-transactions feature, already
long merged) -- not touched by any commit from either the
name-field-whitespace-identity line or the feature-structure-sync-gap
(other crew) line today. Classification: (c) unattributable to either
crew's current in-flight work -- a pre-existing fragility in a mock/live
type-overload boundary, not a regression from today's commits.

### 3. test_flexlibs2_alias_ratchet.py::test_no_executable_flexlibs2_imports_outside_alias_package

Assertion output (offenders list):
```
tests/conftest.py:1392: from flexlibs2.code.FLExProject import ...
tests/conftest.py:1451: from flexlibs2.code.FLExProject import ...
tests/operations/test_issue251_252_256_feature_struct_probe.py:36: from flexlibs2.code.FLExProject import ...
tests/operations/test_natural_classes.py:917: from flexlibs2.code.FLExProject import ...
tests/operations/test_natural_classes.py:954: from flexlibs2.code.FLExProject import ...
tests/operations/test_natural_class_feature_sync.py:721: from flexlibs2.code.FLExProject import ...
tests/operations/test_owner_cast_pattern.py:71: from flexlibs2.code.FLExProject import ...
tests/operations/test_owner_cast_pattern.py:630: from flexlibs2.code.lcm_casting import ...
tests/write_path_transactions/test_capabilities.py:96: import flexlibs2
```
Blame on each offending line:
- tests/conftest.py:1392,1451 -> c72c5296b, 2026-08-15 (pre-existing,
  predates both the rename PR and CONCURRENCY.md; inside a try/except
  legacy-fallback block).
- tests/operations/test_owner_cast_pattern.py,
  tests/operations/test_natural_classes.py -> ec54432 "Rename flexlibs2
  package to flexicon (#241)" -- the mechanical rename itself did not
  fully convert/exempt these files.
- tests/write_path_transactions/test_capabilities.py -> fe42ddf5 (old,
  write-path-transactions feature).
- tests/operations/test_natural_class_feature_sync.py:721 -> 4aca74a
  "refactor(feature-structure-sync-gap): T4 -- extract
  BaseOperations._ApplyFeatureStruc" (other crew, now committed).
- tests/operations/test_issue251_252_256_feature_struct_probe.py:36 ->
  c18b43b "spec(251,252,253,256): freeze feature-structure owner-resolver
  contract; fold #253 in" (other crew, now committed).

Classification: (b) NEW foreign failure, not on CONCURRENCY.md's 3-item
list. Root cause is mixed: a pre-existing gap in the rename commit's
exemption list (ec54432), compounded by the other crew's
feature-structure-sync-gap commits adding two more offending files. No
commit from the name-field-whitespace-identity line touches any of the
nine offending lines. This ratchet is currently RED against committed HEAD
and should be named on CONCURRENCY.md going forward (see amendments
below).

## RATCHET VERDICT

Both previously-named ratchets were run individually against committed
HEAD:

```
python -m pytest tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies -m "not requires_live_project" -q
-> 1 passed in 1.07s

python -m pytest "tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_no_new_unbracketed_mutations" -m "not requires_live_project" -q
-> 1 passed in 1.69s
```

Both are GREEN against committed HEAD, not red. Neither appeared in the
full-suite failure list either, confirming this is the true current state,
not a fluke of isolation. The test_natural_class_feature_sync.py
collection-error item is also resolved: --collect-only on that file now
cleanly enumerates 14 tests with zero collection errors.

This is significant and changes how future tasks in this feature must
treat CONCURRENCY.md's three-item list: all three previously-named
known-foreign items are stale/resolved as of committed HEAD. A different
ratchet (test_flexlibs2_alias_ratchet.py) is the one that is actually red
right now, and it is red against committed code -- per the task's
instruction, that makes it "a legitimate repo state, not a transient."
Any future cycle that sees this specific ratchet fail should name it as a
known, currently-real, pre-existing-and-other-crew-compounded failure and
not chase it as something this feature broke -- but should NOT wave off
other ratchet failures as "probably this one" without checking, since two
of the three old ones are now clean.

## PROBE COLLECT COUNT

```
python -m pytest tests/operations/test_name_field_identity_probe.py --collect-only -q -m requires_live_project
```
Result: 8 tests collected (test_pn1 through test_pn8). Nonzero -- the live
probe still collects correctly. Live tests were NOT executed in this task,
per instructions.

## RECOMMENDED CONCURRENCY.md AMENDMENTS

Replace the "The offline suite is RED for reasons that are not ours"
section's numbers and known-foreign list with:

```markdown
## The offline suite is RED for reasons that are not ours

As of 2026-09-07 (re-derived against committed HEAD by the verification
agent, cycle2-baseline), python -m pytest tests -m "not requires_live_project" -q
gives 3 failed, 1292 passed, 498 deselected, 0 errors. This absolute count
is already stale the moment it is read -- re-derive it yourself before
trusting it; do not copy these numbers into a future report.

The three items previously named here (test_natural_class_feature_sync.py
collection errors, test_lcm_contract.py::test_no_new_type_dependencies,
test_unbracketed_mutations.py::test_no_new_unbracketed_mutations) are
RESOLVED as of the commits landing in 4aca74a/61e0f87/e17cd7d. All three
now pass / collect cleanly. Do not report them as known-foreign without
re-checking first -- they may already be fixed by the time you read this.

Currently-known-foreign failures, re-verified 2026-09-07:

- tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception
  and ::test_depth_restored_on_exception -- pre-existing pythonnet
  overload-resolution TypeError in UndoableUnitOfWorkHelper..ctor, traced
  to flexicon/code/transaction.py (last touched by fe42ddf5/287bb20e,
  unrelated to either active crew's current commits).
- tests/test_flexlibs2_alias_ratchet.py::TestFlexlibs2AliasIsInboundOnly::test_no_executable_flexlibs2_imports_outside_alias_package
  -- RED against committed HEAD (not a transient). Caused jointly by the
  ec54432 rename PR not exempting test_owner_cast_pattern.py /
  test_natural_classes.py / test_capabilities.py, a pre-existing legacy
  import in tests/conftest.py (c72c5296b, predates the rename), and two
  new offending files added by the other crew's feature-structure-sync-gap
  commits (4aca74a, c18b43b). No name-field-whitespace-identity commit
  touches any offending line.
```

Also add, under "What belongs to the other crew": note that
577dab3/a26d39c/4aca74a/61e0f87/e17cd7d (feature-structure-sync-gap) are
now committed, so the "uncommitted (+423)" language for BaseOperations.py
no longer describes reality -- the fence itself (do-not-touch) still
stands, but the diff is now on disk in git history, not a working-tree
diff.

Add a new subsection flagging the untracked directory found during this
cycle:

```markdown
## Untracked, unrelated to either crew -- leave alone

specs/duplicate-signature-harmonisation/evidence/live-issue-246.md is
leftover, never-committed evidence from an already-merged issue (#246,
commits cc454c02/4c496c2d, dated 2026-08-18). It predates this protocol
and belongs to neither crew's current work. Do not stage, commit, or
delete it without an explicit human/lex-lead decision.
```

## Result

[INFO] Re-derivation complete. Full command outputs and blame evidence
above are the basis for every claim; no source, test, or spec file was
modified in the course of this task.
