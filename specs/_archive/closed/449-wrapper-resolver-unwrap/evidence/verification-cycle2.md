# Verification -- cycle 2, lex-verification

## Offline baseline diff

Detached worktree of `origin/main` @ 88e2e2b built at
`.../scratchpad/main449`.

Command (both trees, from repo root):
```
python -m pytest -m "not requires_live_project" -q -rfE -p no:cacheprovider
```

- Branch (`fix/449-wrapper-resolver-unwrap`): 148 failed, 2109 passed, 39 skipped, 48 errors
- main @ 88e2e2b: 147 failed, 2087 passed, 39 skipped, 48 errors

Diffed FAILED/ERROR node IDs (branch vs main):
- main-passes-but-branch-fails: **none** (`comm -13` empty) -- gate condition satisfied.
- branch-fails-but-not-in-main-failure-set: **1** --
  `tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncStatic::test_get_msa_object_hasattr_calls_are_allowlisted`.
  Confirmed by direct run: passes on main (1 passed), fails on branch. Root
  cause: this ratchet test source-inspects `MSAOperations.__GetMsaObject`
  for a `hasattr()` call guarding the old ad-hoc `_obj` wrapper-unwrap
  branch; cycle 1 intentionally replaced that branch with `_UnwrapLcm`,
  removing the `hasattr()` call the test's assertion looks for. The
  test's own docstring anticipates this ("if this is empty the method
  changed shape and this test's premise needs re-examining, not
  deleting"). Not a functional regression, but it IS a test that passes
  on main and fails on the branch -- fails the literal gate as stated.

Remaining ~147 pre-existing failures/48 errors: identical between trees
in cluster shape. Spot-checked three clusters by running each file in
isolation on the main worktree:
- `tests/test_operations_baseline.py` (56 on the list) -- 326 passed in isolation.
- `tests/test_wrappers.py` (46 on the list) -- 46 passed in isolation.
- `tests/write_path_transactions/test_a3_abort_session.py` (14 on the list) -- 14 passed in isolation.
All three pass standalone and only fail/error inside the full-suite run
-- a pre-existing test-isolation/ordering artifact (shared session-scoped
fixture state), reproduced identically on both trees, not caused by #449.

Worktree removed after the run (`git worktree remove ... --force`).

## Live re-run (independent)

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_449_getall_roundtrip_live.py tests/operations/test_449_wrapper_write_paths_live.py -m requires_live_project -q
```

Result: `16 passed, 1 xfailed`. `tests/live_status.json` -> `"run_mode": "live"`.

Spot-check of evidence files: `evidence/live-T6.md` and
`evidence/live-write-paths.md` both cite re-queried LCM state after each
write (e.g. `Fresh GetAll() lookup by Hvo: Disabled=True`,
`IWfiMorphBundle(project.Object(hvo))` re-fetch), not echoed inputs --
confirmed by reading both files in full.
