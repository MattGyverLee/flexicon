# Live verification -- T2.1 (Q1 probe, gates ruling C1)

**Project:** Target (target_sandbox) AND Sena 3 (sena3_sandbox)
**Fixture:** target_sandbox, sena3_sandbox (both tempdir copies of the
.fwbackup -- read-only probe, no writes, no restore scripts invoked)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q -k TestPart4NotebookOwnerGate -s
```
**run_mode:** live (confirmed via
`python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"`
-> `live`)
**Date:** 2026-09-18

## Claim under test

Ruling C1 (spec.md section 3) proposes rewriting #302's three
`DataNotebookOperations.py` sites to the OWNERSHIP form
(`self.project.lp.ResearchNotebookOA.RecordsOC`) rather than the
REPOSITORY form (`repos.Singleton.RecordsOC`). Q1 (spec.md section 4)
gates that ruling on three sub-claims, checked live on both projects:

1. `project.lp.ResearchNotebookOA is not None`
2. `project.lp.ResearchNotebookOA.Hvo == ServiceLocator.GetService(IRnResearchNbkRepository).Singleton.Hvo`
3. `project.lp.ResearchNotebookOA.RecordsOC` is reachable and its count
   (and HVO set) matches `Singleton.RecordsOC`.

Also recorded: `IRnResearchNbkRepository.Count`, and whether `.Singleton`
can itself be null.

## Pre-state / observed values (read live from the LCM, both sandboxes)

### Target (target_sandbox)
- `IRnResearchNbkRepository.Count` = 1
- `repo.Singleton is None` = False
- `project.lp.ResearchNotebookOA is None` = False
- `ResearchNotebookOA.Hvo` = 10335
- `repo.Singleton.Hvo` = 10335  (HVO-identical -- same underlying object)
- `ResearchNotebookOA.RecordsOC` count = 0
- `repo.Singleton.RecordsOC` count = 0
- HVO sets of `RecordsOC` from both access paths: equal (both empty)

### Sena 3 (sena3_sandbox)
- `IRnResearchNbkRepository.Count` = 1
- `repo.Singleton is None` = False
- `project.lp.ResearchNotebookOA is None` = False
- `ResearchNotebookOA.Hvo` = 27234
- `repo.Singleton.Hvo` = 27234  (HVO-identical -- same underlying object)
- `ResearchNotebookOA.RecordsOC` count = 1
- `repo.Singleton.RecordsOC` count = 1
- HVO sets of `RecordsOC` from both access paths: equal

## Action

Read-only probe. No project was written to. `TestPart4NotebookOwnerGate`
in `tests/operations/test_lcm_member_truth_sweep.py` was run against both
sandbox fixtures; each test asserts non-null `ResearchNotebookOA`,
non-null `Singleton`, HVO equality between the two, and count+HVO-set
equality of `RecordsOC` reached via each path.

## Post-state

Not applicable -- no write occurred. Both sandboxes were torn down by
their pytest fixtures (tempdir deleted) after the test; nothing to
restore, and the real Target / Sena 3 projects were never opened.

## Cleanup

None required. Read-only probe on tempdir sandbox copies; both sandboxes
were discarded by fixture teardown. `scripts/restore_target.py` and
`scripts/restore_sena3.py` were NOT invoked, per the task's non-negotiable
rules.

## Result

Both sub-claims of Q1 hold on both projects, with no exception found:
`ResearchNotebookOA` is never null where `Singleton` is not, the two
resolve to the identical underlying object (HVO-equal), and `RecordsOC`
agrees exactly between the ownership form and the repository form on
both a populated project (Sena 3, 1 record) and an empty one (Target, 0
records).

[PASS]

VERDICT: PASS -- C1 stands (ownership form)
