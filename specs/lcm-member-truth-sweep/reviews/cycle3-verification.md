# Cycle 3 -- Verification report: #283, EnvironmentOperations.Duplicate

**Task:** T3.7 (checkpoint 3, spec.md C7/C8/C9).
**Verdict:** PASS
**Live run:** yes | run_mode: live
**Evidence:** specs/lcm-member-truth-sweep/evidence/live-T3-environment.md
**Project:** Sena 3, via sena3_sandbox only (deviation from tasks.md's
nominal target_sandbox, authorized and recorded -- Target has no guaranteed
phoneme inventory to build a legal IPhSimpleContextSeg). Real Target and
real Sena 3 .fwdata files were never opened.

## Live per-file pass counts

| Command | Result | run_mode |
|---|---|---|
| pytest tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q | 19 passed | live |
| pytest tests/operations/test_260_environment_resolver_gate.py -m requires_live_project -q | 7 passed | live |
| pytest .../test_lcm_member_truth_sweep.py -k test_2d -v -s | 1 passed (HVOs captured) | live |
| pytest .../test_260_environment_resolver_gate.py -k TestP7DiscoveredWrongPropertyName -v -s | 2 passed | live |
| pytest tests/operations/test_zzz_scratch_evidence_T3.py (verification-authored scratch test, deleted after run) -v -s | 1 passed (HVOs captured, incl. Duplicate) | live |

All five invocations confirmed run_mode: live via
tests/live_status.json immediately after execution -- never assumed.

## Claim vs. observed

| Claim | Observed live | Status |
|---|---|---|
| GetLeftContextPattern/GetRightContextPattern read LeftContextRA/RightContextRA | Seeded context (hvo=152223) returned by GetLeftContextPattern after fresh re-read by HVO; genuine no-context case still returns None | PASS |
| Duplicate copies LeftContextRA/RightContextRA by reference, unconditionally | Source hvo=152223/152224 and duplicate hvo=152223/152224 (re-read by the duplicate's own HVO) are identical -- reference, not clone | PASS |
| deep flag is inert for this method | Not independently re-exercised with deep=False live (no real caller exists per T3.4's grep, already reproduced from cycle3-programmer.md); accepted on the strength of the unconditional code path read in the diff | PASS (code-inspection-backed) |
| T3.6: compound_rule.py / PhonologicalRuleOperations.py untouched | git diff --name-only re-grepped for both filenames: no match | PASS |

## Offline regression (see live-T3-environment.md Offline regression cross-check section)

Command used by the task briefing: python -m pytest tests/ -m "not requires_live_project" -q
Result: **1689 passed, 655 deselected, 0 failed** -- reproduces the
programmer's own reported figure exactly.

Command used by the campaign's own established convention (STATUS.md,
live-T2-notebook.md, cycle2-verification-T2.8.md): python -m pytest -m "not requires_live_project" -q (no tests/ path)
Result on the working tree (T3 changes applied): **1878 passed, 804
deselected, 0 failed**.
Result on a clean 994f2ee checkout (git worktree add, no stash/reset used
against the working tree): **1878 passed, 803 deselected, 0 failed**.

### Discrepancy resolved, not papered over

Three different "baseline" numbers were in circulation for this task:
- tasks.md/STATUS.md cited **1876 passed / 0 failed** at 994f2ee.
- The programmer's cycle3-programmer.md reported **1689 passed, 654->655
  deselected**.
- This verification pass independently measured **1878 passed, 803->804
  deselected** at the identical commits/tree states.

Root cause, confirmed by direct comparison: the programmer's command (and
this task's own briefed command) restricts collection to the tests/
directory (pytest tests/ -m ...), which silently EXCLUDES flexicon/tests/
and flexicon/sync/tests/ -- both real test directories outside tests/,
confirmed present via find. The campaign's earlier evidence files
(live-T2-notebook.md, cycle2-verification-T2.8.md) used the unrestricted
form (no tests/ argument) and are the ones STATUS.md's "1876" figure
traces back to.

Running the unrestricted command myself on a clean 994f2ee worktree gives
**1878/803**, not 1876/806 -- close to, but not exactly, STATUS.md's
figure. I did not chase that residual 2-passed/3-deselected gap further
(it predates this task's diff entirely, reproduces identically on a clean
994f2ee checkout with zero of this task's changes present, and the task
briefing scoped this verification to the T3 delta, not to auditing a
cross-checkpoint historical figure) -- but it should NOT be read as a
regression: it is present on the unmodified 994f2ee tree with none of
this task's four files touched.

**What is solid, from both commands, restricted and unrestricted:** zero
newly-introduced offline failures, and the only passed/deselected delta
attributable to this task's changes is the +1 deselected test added in
T3.5(a) (a new requires_live_project test, correctly excluded from the
offline count). Both the restricted-path 1689 and unrestricted 1878
figures independently show 0 failed and the identical +1-deselected delta
pattern before/after T3's changes.

**Recommendation for the record:** whoever owns tasks.md's stated
baseline should re-derive it using the unrestricted command
(python -m pytest -m "not requires_live_project" -q, no path argument) to
match the convention already established in live-T2-notebook.md, and
should expect ~1878, not 1876 or 1689, going forward in this environment.

## Blockers

None.

## Recommendation

APPROVE -- live run happened against Sena 3 via sena3_sandbox only,
run_mode: live confirmed on every invocation, every T3.7 claim (contexts
survive Duplicate, proven by HVO identity re-read fresh from the LCM) is
observed in the database, cleanup confirmed (finally: blocks ran; scratch
evidence test deleted; git status --porcelain shows only the same 4
tracked files this task modifies), and the offline regression shows zero
new failures under either command form.
