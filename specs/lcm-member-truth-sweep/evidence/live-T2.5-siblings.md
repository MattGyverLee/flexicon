# Live verification -- T2.5 (Catalogue 2 absence ratchets, ruling C2 pin) and T2.5b (Q3)

**Fixture:** pure `clr.GetClrType` reflection for T2.5's five absence rows and
ruling C2 (no project needs to be open); `target_sandbox` for the C2 functional
pin (test_5g) and for T2.5b (Q3), which creates one real `MoEndoCompound` and
one real `MoExoCompound` via `project.MorphRules.CreateCompoundRule()` and
deletes both in a `finally:`.

**Command (exact, both new test files together, per the task's standing
invocation):**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_datanotebook_duplicate.py tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q
```

**run_mode:** live (confirmed via
`python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"`
-> `live`)

**Date:** 2026-09-18

**Collected / passed:** 25 collected (6 in
`test_datanotebook_duplicate.py`, 19 in `test_lcm_member_truth_sweep.py`,
of which 8 are new under this task: `test_5a`-`test_5g` and `test_6a`),
25 passed, 0 failed.

---

## T2.5 -- six absence results

All five via `_dump_type_surface` (declared+inherited `clr.GetClrType`
properties), plus the C2 pin (both interface-level and functional):

| # | Claim | Live result |
|---|---|---|
| 1 | `IRnGenericRec` has no `TextsRC` | CONFIRMED ABSENT. Full 34-property live surface has `TextRA` (atomic ref) and no `TextsRC` anywhere. |
| 2 | `ICmAnthroItem` has no `TextsRC` | CONFIRMED ABSENT. Live surface is 0 declared properties (base interfaces only: `ICmObject`, `ICmObjectOrId`, `ICmPossibility`). |
| 3 | `ILangProject` has no `RecTypesOA` | CONFIRMED ABSENT. Full 59-property live surface has no `RecTypesOA` (has `ResearchNotebookOA`, `StatusOA`, `PartsOfSpeechOA`, etc., but the record-types list is NOT on `ILangProject` under this name). |
| 4 | `ICmPerson` has no `LanguagesRC` | CONFIRMED ABSENT. Live 9-property surface: `PositionsRC`, `PlacesOfResidenceRC`, no `LanguagesRC`. (`ResearchersRC`/`RestrictionsRC` mentioned in the catalogue turn out to live on `IRnGenericRec`, not `ICmPerson` itself -- doesn't change the absence verdict for `ICmPerson.LanguagesRC`.) |
| 5 | `ICmBaseAnnotation` has no `RepliesOS` | CONFIRMED ABSENT. Live 11-property surface: `BeginObjectRA`, `EndObjectRA`, `OtherObjectsRC`, `TextAnnotated`, etc. -- no `Replies*` of any kind. |
| C2 pin | `IRnResearchNbkRepository` exposes `Count` and `Singleton` | **Singleton** confirmed via interface reflection (declared directly). **Count** does NOT appear via `clr.GetClrType(...).GetProperties()` on the derived interface -- it is inherited from the generic base `IRepository<IRnResearchNbk>` and .NET interface reflection does not flatten it into `GetProperties()` on the derived interface (a reflection quirk, matching cycle-1's own `test_3a`, which already printed `['Singleton']` only). The FUNCTIONAL half is pinned live instead (test_5g, target_sandbox): `hasattr(repo, "Count")` is True, `repo.Count` is a real int (`1`), `hasattr(repo, "Singleton")` is True, `hasattr(repo, "RecordsOC")` is False. C2 holds -- **Count is genuinely reachable, just not via bare interface-type reflection.** |

No production line for any of these rows was edited.

## T2.5b -- Q3 (Catalogue 2 row 25)

Created one real `MoEndoCompound` and one real `MoExoCompound` in
`target_sandbox` via `target_sandbox.MorphRules.CreateCompoundRule(name,
endocentric=True/False)`, then checked FOUR surfaces for any member whose
name contains "Context": `clr.GetClrType(IMoEndoCompound)` /
`clr.GetClrType(IMoExoCompound)` declared+inherited properties, AND live
`dir()` over the actual instances (`cast_to_concrete(endo)` /
`cast_to_concrete(exo)`).

```
[SURFACE] IMoEndoCompound: 2 public properties (declared+inherited):
  HeadLast : System.Boolean
  OverridingMsaOA : SIL.LCModel.IMoStemMsa
[SURFACE] IMoExoCompound: 1 public properties (declared+inherited):
  ToMsaOA : SIL.LCModel.IMoStemMsa

[Q3] IMoEndoCompound CLR-reflection Context* members: []
[Q3] IMoExoCompound CLR-reflection Context* members: []
[Q3] live MoEndoCompound instance dir() Context* members: []
[Q3] live MoExoCompound instance dir() Context* members: []
```

**Q3 ANSWER: no Context-named member exists under ANY suffix (OA, RA, OS,
RS, or bare) on either MoEndoCompound or MoExoCompound.** Catalogue 2 row 25
is CLEARED, not raised -- `left_context`/`right_context`/`contexts` in
`CompoundRule` (`Grammar/compound_rule.py:220,244`) are unconditionally
`None` for both concrete types; there is no reference or owned context to
navigate to under any name. This confirms the cycle-1 snapshot finding live.
Ruling C9 remains binding: `compound_rule.py` is untouched by this task.

Both created compound rules were deleted (`target_sandbox.MorphRules.Delete`)
in the test's `finally:` block; `target_sandbox` is a disposable tempdir
copy in any case.

## Result

[PASS] -- all five absence rows and the C2 pin are now live-confirmed
(upgraded from snapshot-derived); Q3 is answered and clears Catalogue 2 row
25. No production line was edited by this task.
