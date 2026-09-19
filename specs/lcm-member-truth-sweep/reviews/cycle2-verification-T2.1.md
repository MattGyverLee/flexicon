# Verification Report -- T2.1 (Q1 probe, gates ruling C1)

**Verdict:** [PASS]
**Live run:** yes | **run_mode:** live
**Evidence:** specs/lcm-member-truth-sweep/evidence/live-T2.1-notebook-owner.md
**Project:** Target (target_sandbox) and Sena 3 (sena3_sandbox), both read-only

## Claim vs. observed

| Claim | Observed live | Status |
|-------|---------------|--------|
| `project.lp.ResearchNotebookOA is not None` (Target) | Hvo=10335, non-null | [PASS] |
| `project.lp.ResearchNotebookOA is not None` (Sena 3) | Hvo=27234, non-null | [PASS] |
| `ResearchNotebookOA.Hvo == repos.Singleton.Hvo` (both) | Target 10335==10335; Sena 3 27234==27234 | [PASS] |
| `ResearchNotebookOA.RecordsOC` reachable, count matches `Singleton.RecordsOC` | Target 0==0; Sena 3 1==1; HVO sets equal both projects | [PASS] |
| `repos.Singleton` can itself be null? | False on both projects | recorded |
| `IRnResearchNbkRepository.Count` | 1 on both projects | recorded |

## Method

Added `TestPart4NotebookOwnerGate` (2 live tests, one per fixture) to the
existing ratchet file `tests/operations/test_lcm_member_truth_sweep.py`,
matching its `[SURFACE]`/`[N]`-prefixed print convention and
`pytest.mark.live_phase` usage. No production file was touched. Ran:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q -k TestPart4NotebookOwnerGate -s
```
Result: 2 passed. `--collect-only` confirmed 2 tests collected (not zero).
`tests/live_status.json` read back `"run_mode": "live"` after the run.

## Mock suite (regression, supplementary)

Not run -- out of scope for a read-only reflection probe; no production
code changed.

## Blockers

None. Neither the real Target nor real Sena 3 was opened; only
`target_sandbox`/`sena3_sandbox` tempdir copies were used, and no
`scripts/restore_*.py` was invoked.

## Recommendation

APPROVE ruling C1 as written: adopt the ownership form
(`self.project.lp.ResearchNotebookOA.RecordsOC`) for the T2.2 fix to
`Notebook/DataNotebookOperations.py`. Q1 is answered on both live
projects with no exception: `ResearchNotebookOA` is never null where
`Singleton` is not, the two are the same underlying object (HVO-equal),
and `RecordsOC` agrees exactly via either access path on both a
populated project (Sena 3) and an empty one (Target). The fix spurt
gated behind this probe (T2.2) may proceed.
