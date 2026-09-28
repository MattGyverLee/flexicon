# Issue #449 -- cycle 2, lex-verification report

**Verdict: PASS, with one flagged offline ratchet test needing an update
(not a functional regression).**

## Gate 1 -- offline baseline diff

Branch: 148F/2109P/39S/48E. Main @ 88e2e2b: 147F/2087P/39S/48E (not
168F/2089P as cycle 1's stash comparison reported -- re-run from a clean
detached worktree gives a different, and more trustworthy, number; the
discrepancy doesn't change the verdict since node-ID diffing, not raw
counts, is the actual gate).

Diffed node IDs: zero main-passing tests fail on the branch. One test
(`test_issue251_msa_feature_sync.py::...::test_get_msa_object_hasattr_calls_are_allowlisted`)
passes on main and fails on branch -- confirmed by isolated runs on both
trees. Root cause: the test source-inspects `__GetMsaObject` for a
`hasattr()` call that cycle 1 deliberately removed (replaced by
`_UnwrapLcm`); the test's own comment anticipated this exact scenario.
This is a stale-premise ratchet test, not a functional defect, but it is
a literal violation of "no test that passes on main fails on the
branch" and should be updated (not silently left failing) before merge.

Pre-existing ~147 failures/48 errors: spot-checked 3 of the top clusters
(`test_operations_baseline.py`, `test_wrappers.py`,
`test_a3_abort_session.py`, 116 of ~195 failing IDs) -- all pass 100% in
isolation on the main worktree. Environment/test-isolation artifact
(shared session fixture state across the full run), identical on both
trees, not caused by #449.

## Gate 2 -- live re-run (independent)

`16 passed, 1 xfailed`. `tests/live_status.json` -> `run_mode: live`.
`evidence/live-T6.md` and `evidence/live-write-paths.md` both cite
values re-queried from the LCM post-write (fresh `GetAll()` lookups by
Hvo, fresh `project.Object(hvo)` re-casts), not echoed inputs -- verified
by reading both files.

## Blockers

None requiring a human. One action item: update or retire
`test_get_msa_object_hasattr_calls_are_allowlisted` to match the
`_UnwrapLcm` shape before merge, so the offline suite doesn't ship a
test that fails against the code it's meant to be testing.

## Recommendation

APPROVE, contingent on fixing the one flagged offline ratchet test.
