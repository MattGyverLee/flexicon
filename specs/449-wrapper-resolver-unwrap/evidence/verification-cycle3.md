# Verification -- cycle 3, lex-verification

## Offline baseline diff

main worktree recreated (baseline was missing): detached `origin/main` @
`88e2e2b` (same SHA as cycle 2), built at
`.../scratchpad/main449b`, removed after the run.

Command (both trees):
```
python -m pytest -m "not requires_live_project" -q -rfE -p no:cacheprovider
```

- Branch (`fix/449-wrapper-resolver-unwrap` @ 629eea5): 147 failed, 2110 passed, 39 skipped, 48 errors
- main @ 88e2e2b: 147 failed, 2087 passed, 39 skipped, 48 errors (identical to cycle 2's recorded main baseline)

Diffed FAILED/ERROR node IDs (195 each): `comm -13` and `comm -23` both
**empty** -- the sets are identical. The one item that failed the
literal gate in cycle 2
(`test_get_msa_object_hasattr_calls_are_allowlisted`) is now fixed by
the programmer's cycle 3 test update and passes on both trees.
Gate satisfied: no test that passes on main fails on the branch.

Explicit confirmation:
```
python -m pytest tests/test_flexlibs2_alias_ratchet.py tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncStatic::test_get_msa_object_hasattr_calls_are_allowlisted -q
```
-> 6 passed.

## Commit message keyword scan

```
git log origin/main..HEAD --format=%B | grep -inE "(close|fix|resolve|...)s?\s+#[0-9]+"
```
-> no matches. No close/fix/resolve keyword sits directly before an
issue number in any of the 6 commits ahead of origin/main.

## Production-code diff scope

```
git diff 7af88db..HEAD --stat -- flexicon/
```
-> empty. Cycle 3 touched only a test file and docs; no live re-run
required. run_mode=live confirmation from cycle 2's live run
(`tests/operations/test_449_getall_roundtrip_live.py`,
`tests/operations/test_449_wrapper_write_paths_live.py`, 16 passed/1
xfailed, `run_mode: live`) still stands as the last live evidence for
this feature's production code, which is unchanged since.

## Result

PASS -- all gates satisfied.
