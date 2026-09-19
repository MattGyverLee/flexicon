# STATUS -- lcm-member-truth-sweep

**Last updated:** 2026-09-18 (end of spurt 3)
**Status:** in_progress -- 3 of 8 checkpoints complete
**Baseline:** `598f41e` (v4.8.0); spurt-3 diffs measured against `994f2ee`
**Issues:** #302, #261, #283, #259, #303, #309 -- **none are closed yet**;
the campaign closes all six at checkpoint 8 (see "Issue-closing policy").
**Ralph loop:** STOPPED at the user's instruction after checkpoint 2
("close the loop once you finish the next issue"). Spurt 3 was run as an
operator-driven spurt, not by the loop, and checkpoint 3 is now complete.
The loop stays stopped; restart per the standing prompt in
`HANDOFF-main-session.md` if the user re-arms it.

## Offline regression baseline -- CORRECTED (read this before quoting a number)

Three different figures were in circulation during spurt 3. They differ by
the **command**, not by any regression:

| Command | Count | Why |
|---|---|---|
| `python -m pytest -m "not requires_live_project" -q` | **1878 passed / 804 deselected / 0 failed** | **Canonical.** Collects `tests/`, `flexicon/tests/` and `flexicon/sync/tests/`. |
| `python -m pytest tests/ -m "not requires_live_project" -q` | 1689 passed | Path-scoped -- silently EXCLUDES `flexicon/tests/` and `flexicon/sync/tests/`. Do not use. |
| (STATUS.md, end of spurt 2) | 1876 passed | Superseded. Off by 2 from a clean-tree re-measurement; the gap predates spurt 3 and reproduces on an untouched `994f2ee` worktree, so it is a bookkeeping error, not a regression. |

**Use the canonical command and expect 1878 / 0 failed.** Independently
measured three times at the end of spurt 3: by lex-verification on a clean
`994f2ee` worktree (1878/803), by lex-verification on the spurt-3 tree
(1878/804), and by the lead on the final committed tree (1878/804). The +1
deselected is the one new `requires_live_project` test added by T3.5(a).
Root cause of the 1689 figure found and recorded by lex-verification; the
residual 1876-vs-1878 gap is unexplained but pre-existing and harmless.

## What landed this spurt (checkpoint 3: #283)

**#283 is fixed and live-verified.** One production file, one campaign
file, two test files.

### T3.1-T3.3 -- the fix

`flexicon/code/Grammar/EnvironmentOperations.py`:

- `GetLeftContextPattern`/`GetRightContextPattern` read the real names.
  `LeftContextOA`/`RightContextOA` never existed on `IPhEnvironment`, so
  every `hasattr()` guard was silently `False` and both getters returned
  `None` unconditionally. Each is now a single
  `return getattr(env, "LeftContextRA", None)`.
- `Duplicate`'s entire `if deep:` block is gone -- the `clone_properties` /
  `ObjectRepository.NewObject(ClassID)` machinery and **both bare
  `except Exception: pass` swallows** with it. Context references are now
  assigned **unconditionally**, outside any conditional (ruling C7).
- `deep` stays in the signature (pinned at `EnvironmentOperations.pyi:18`)
  and is documented INERT for this method. Zero `LeftContextOA`/
  `RightContextOA` references survive outside prose describing the
  historical bug.

-> `reviews/cycle3-programmer.md`

### T3.4 -- Q4 answered

**No caller anywhere in `flexicon/`, `examples/` or `tests/` passes
`deep=False` to this method.** The only prior hit was the method's own
docstring example, now rewritten. Q4 is closed; the unconditional
assignment breaks nothing.

### T3.5 -- the C8 inversions

- `test_lcm_member_truth_sweep.py::test_2d_*` converted from print-only
  observation to hard assertions: both duplicate context HVOs non-null and
  HVO-equal to the source's, re-read from the LCM.
- `test_260_environment_resolver_gate.py::TestP7DiscoveredWrongPropertyName`
  keeps its class, narrative and its genuine no-context `None` assertion
  (re-justified for the true reason), and gains
  `test_left_context_returns_seeded_context_by_reference`, which seeds a
  real `IPhSimpleContextSeg`, assigns it, re-reads by HVO and asserts
  identity. lex-domain confirmed this is a genuine anchor that goes red
  against the unfixed code -- not a tautology.
- `test_2a_iphenvironment_full_surface` correctly needed **no** inversion:
  it asserts LCM ground truth, which the production fix does not change.

### T3.6 -- scope held (C9)

`compound_rule.py`, `PhonologicalRuleOperations.py` and
`test_phon_rules.py` were NOT touched, confirmed by `git diff --name-only`
in both the programmer and verification passes. Those `...OA` names are
correct on `IPhSegRuleRHS`, and `IMoEndoCompound`/`IMoExoCompound` carry
neither form.

### T3.7 -- verification: PASS

`run_mode: live` confirmed on **every** invocation (5 of 5), never assumed.
Source contexts `152223`/`152224`; the duplicate, re-read fresh **by its
own HVO**, returns `152223`/`152224` -- identical and non-null, proving
reference semantics rather than a clone. 19 + 7 live tests pass on the two
campaign files. -> `evidence/live-T3-environment.md`,
`reviews/cycle3-verification.md`

**Fixture deviation, recorded not buried:** T3.5(a) and T3.7 ran on
`sena3_sandbox`, not T3.7's nominal `target_sandbox`. A legal
`IPhSimpleContextSeg` needs an existing `IPhPhoneme` for
`FeatureStructureRA`, and Target is "mostly blank scratch" with no
guaranteed phoneme inventory. Sandbox-only either way -- no real project
file was opened, and standing gate 1 is fully met.

### Review gates

| Gate | Result |
|---|---|
| Verification | PASS, `run_mode: live`, HVO identity observed |
| QC | APPROVE, 96/100 |
| Domain | Q-A PASS (C7 stands, no flip), Q-B PASS, Q-C PASS |
| Offline regression | 1878 passed / 0 failed, zero new failures |

Two non-blocking findings, both dispositioned (nothing left dangling):

- **QC P2 -- FIXED in this spurt.** The docstring and CHANGELOG cited
  `EnvironmentOperations.pyi:19`; `Duplicate` is at `:18`. Corrected in all
  five places it appeared (`EnvironmentOperations.py`, `CHANGELOG.md`,
  `spec.md` x2, `tasks.md`).
- **Domain Q-B coverage gap -- DEFERRED to T8.6, scheduled not shelved.**
  No test deletes the duplicate and re-reads the source's `LeftContextRA`.
  Deferred because the risk is unrealized in the shipped diff: `Delete`
  (`:195-233`) only calls `phon_data.EnvironmentsOS.Remove(env)` and never
  touches `ContextsOS`, so it cannot cascade-delete a still-referenced
  context. This is missing coverage of the highest-risk regression path,
  not a live defect. **Checkpoint 8 must not close with T8.6 open.**

## Issue-closing policy (binding for the rest of the campaign)

No commit in this campaign may carry a close keyword against #302, #261,
#283, #259, #303 or #309. All six close at **checkpoint 8**, after T8.5's
final crew gate on the whole campaign diff. This was set at checkpoint 2
(commit `994f2ee`: "Neither issue is closed by this commit -- the campaign
closes them at checkpoint 8") and is re-affirmed here for #283. The
mid-spurt user authorization to *file* issues explicitly did not extend to
closing any of the six. Phrase around the verb in commit messages; the
`.githooks` `commit-msg` guard also blocks possessive, negated, quoted and
narrated forms, so write neither `closes #283` nor `does not close #283`.

## What landed in spurt 2 (checkpoint 2: #302 + #261)

**#302 and #261 are fixed and live-verified.** This is the first spurt to
modify a production file.

### T2.1 -- the C1 gate: PASS

`lp.ResearchNotebookOA` is non-null and HVO-identical to
`IRnResearchNbkRepository.Singleton` on both projects (Target 10335, Sena 3
27234); `RecordsOC` counts and HVO sets match; `.Singleton` was never null;
`Count` is 1 on both. **C1 stands in its ownership form** -- no spec flip was
needed. -> `evidence/live-T2.1-notebook-owner.md`,
`reviews/cycle2-verification-T2.1.md`

### T2.2 / T2.3 -- the fixes

`flexicon/code/Notebook/DataNotebookOperations.py`:

- Three `RecordsOC` sites (`Create`, `Delete`'s top-level `else:`,
  `Duplicate`) now go through `self.project.lp.ResearchNotebookOA.RecordsOC`;
  the three dead `GetService(IRnResearchNbkRepository)` lookups that fed them
  are deleted. The C3 site in the enumerable getter (`:238`, was `:232`) and
  its import survive untouched.
- `__GetRecordObject` now calls `self.project.Object(hvo)` instead of the
  nonexistent `LcmCache.GetObject`. `AttributeError` is out of the `except`
  tuple and the raise is chained `from e`, so the mask that mislabelled the
  cause across all 38 routed methods is off (C6).

-> `reviews/cycle2-programmer-T2.2-T2.3.md`

### T2.4 / T2.5 / T2.5b -- tests

- `tests/operations/test_datanotebook_duplicate.py` deleted and rewritten
  (C4). The old file never imported the production module and could not
  fail; the replacement is 6 live tests that genuinely exercise
  `DataNotebookOperations`, re-read by HVO, and cover the int-HVO entry path
  with six routed methods.
- `tests/operations/test_lcm_member_truth_sweep.py` extended from 9 to 19
  live tests: T2.1's `TestPart4NotebookOwnerGate`, T2.5's five absence
  ratchets plus the C2 pin, and T2.5b's compound-context surface dump.
- **Q3 answered and row 25 CLEARED:** no Context-named member exists under
  any suffix on `MoEndoCompound` or `MoExoCompound`. `compound_rule.py`
  stays untouched (C9).

-> `evidence/live-T2.5-siblings.md`, `reviews/cycle2-programmer-T2.4-T2.5.md`

### T2.8 -- verification: PASS

25/25 live on the two campaign files plus 4/4 on an independently-written
probe, `run_mode: live` on both. Offline regression **1876 passed / 0 failed**
vs **1883 / 0** at `03d82c6`; the -7/+20 delta closes exactly (7 deleted mock
tests out, 20 live tests in). *(Superseded: the absolute 1876 figure is off by
2 -- see "Offline regression baseline -- CORRECTED" above. The delta reasoning
is unaffected; the run was 0 failed either way.)* ->
`evidence/live-T2-notebook.md`,
`reviews/cycle2-verification-T2.8.md`

**One scope limitation, recorded not buried:** `Duplicate()` does not run to
completion. Four lines after the #302 placement it raises on
`duplicate.Title.CopyAlternatives(...)` -- a separate pre-existing defect now
filed as #328. The #302 placement is verified by its observable effect on
`RecordsOC` before that crash, and the probe pins the crash to that specific
defect so a real placement regression cannot hide behind it.

### T2.6 / T2.7 -- Catalogue 2 made durable, and FILED

- `catalogue2-siblings.md` holds all 25 rows verbatim, with the Live
  upgrades table backfilled from real T2.5/T2.5b evidence.
- `proposed-issues.md` drafted 10 clusters, and **all ten were filed** as
  **#322-#331** on `MattGyverLee/flexicon` after the user authorized filing
  mid-spurt. The C13 `needs_human` gate is therefore **closed**.

## Four new defects found incidentally (all filed)

T2.4's live work surfaced four `DataNotebookOperations` defects that are not
among the six chartered issues and were not in Catalogue 2:

- **#328** `Title` is a bare `ITsString` and there is no `Text` member at all
  -- `Create`, `CreateSubRecord`, `SetTitle`, `SetContent` and `Duplicate`'s
  copy lines crash unconditionally; the getters silently return `""`.
- **#329** real names are `StatusRA`/`TypeRA`/`ConfidenceRA` -- getters always
  return `None`, and the setters write a throwaway Python attribute that
  never reaches the LCM.
- **#330** `DateOfEvent` is `GenDate`, not `System.DateTime` --
  `SetDateOfEvent` raises `TypeError` on every call.
- **#331** `Duplicate()`/`GetParentRecord()` use `isinstance()` on the raw
  uncast `.Owner`, always False live -- the same bug class `Delete()` already
  fixed under #133.

#328 is why both the crew's tests and the T2.8 probe seed records through the
raw factory rather than through `Create()`.

## Rulings

**Spurt 3:** no ruling changed. C7 was tested against the domain expert and
**stands as written** -- Reference Atomic means the environment does not own
its context (`IPhPhonData.ContextsOS` does), so pointing the duplicate at the
same `IPhPhonContext` is the only semantics consistent with FLEx's own model;
a deep clone would invent ownership and orphan the clone from `ContextsOS`
bookkeeping. C8 and C9 were both confirmed rather than flipped. Q4 is
RESOLVED (no `deep=False` caller exists).

**Spurt 2:** C1 was confirmed rather than flipped; C9 was confirmed by the Q3
clearance. C13's filing gate is discharged.

## Next pickup (checkpoint 4)

**#259, morph bundle inflection class** -- T4.1 through T4.8, across
`WfiMorphBundleOperations.py`, `WfiAnalysisOperations.py` and
`WordformOperations.py`. Start with **T4.1**: implement the navigation
helper once (`bundle.MsaRA` -> null check -> `cast_to_concrete` -> narrow to
`IMoStemMsa` -> `.InflectionClassRA`), returning `None` for a null MSA or a
non-stem subtype and never raising, then route `GetInflectionClass`
(`WfiMorphBundleOperations.py:1261`) through it. Then T4.2's three silent
copy loops and T4.3's `GetSyncableProperties`.

**T4.5 stays blocked on Q2** -- do not implement `SetInflectionClass:1313`
until T4.4's live MSA-sharing count has fed a domain ruling on whether
writing through a shared MSA should refuse, warn or accept. T4.7 needs
`target_sandbox` for the writes and `sena3_sandbox` for the subtype-mix read
path (the 1144-bundle non-stem population).

## Nothing is blocked

No `needs_human` gate is open. Q2 gates T4.5 only, and it is answerable by
the crew's own live probe (T4.4) -- it needs a domain ruling, not a user
decision.
