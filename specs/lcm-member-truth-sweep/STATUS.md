# STATUS -- lcm-member-truth-sweep

**Last updated:** 2026-09-18 (end of spurt 2)
**Status:** in_progress -- 2 of 8 checkpoints complete
**Baseline:** `598f41e` (v4.8.0); spurt-2 diffs measured against `03d82c6`
**Issues:** #302, #261, #283, #259, #303, #309
**Ralph loop:** STOPPED at the user's instruction after checkpoint 2
("close the loop once you finish the next issue"). Checkpoint 3 has not
been started. Restart per the standing prompt in `HANDOFF-main-session.md`.

## What landed this spurt (checkpoint 2: #302 + #261)

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
tests out, 20 live tests in). -> `evidence/live-T2-notebook.md`,
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

No ruling changed this spurt. C1 was confirmed rather than flipped; C9 was
confirmed by the Q3 clearance. C13's filing gate is now discharged.

## Next pickup (checkpoint 3)

**#283 in `Grammar/EnvironmentOperations.py`** -- T3.1 through T3.5. Start
with T3.1/T3.2: rename `LeftContextOA`/`RightContextOA` ->
`...RA` at `:494,495,550,551`, then replace `Duplicate`'s whole `if deep:`
context block with unconditional reference assignment. C8 requires inverting
`test_260_environment_resolver_gate.py:311-317` -- which deliberately asserts
the bug -- **in the same commit**.

## Nothing is blocked

No `needs_human` gate is open. The one that was (Catalogue 2 filing) was
authorized and discharged this spurt.
