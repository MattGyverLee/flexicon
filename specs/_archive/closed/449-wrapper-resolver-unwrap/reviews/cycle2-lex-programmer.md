# Issue #449 -- cycle 2, lex-programmer report

## Gap addressed

Cycle 1's live test (`test_449_getall_roundtrip_live.py`) was read-only. Added
`tests/operations/test_449_wrapper_write_paths_live.py` covering the WRITE
paths #449 touches, none of which had live read-back before this cycle.

## Cases (10 pass, 1 xfail)

- MorphRuleOperations (sena3_sandbox, compound rule wrapper): `SetDisabled`,
  `SetStratum`, `Duplicate`, `Delete` -- all PASS, re-queried via fresh
  `GetAll()` lookup by Hvo.
- MorphRuleOperations affix-template `Delete` -- **XFAIL** (expected): the
  pre-existing owner-resolution bug from cycle 1's sweep
  (`_GetObject(rule.Owner.Hvo)` returns a bare `ICmObject`), reproduces with
  or without a wrapper, out of #449's scope. Documented inline and in
  evidence.
- Reorder family (target_sandbox, TEST_ entry, 3 allomorphs): `MoveUp`,
  `MoveDown`, `MoveBefore`, `MoveAfter`, `Swap`, chained as 5 sub-assertions
  in one test, each re-querying `entry.AlternateFormsOS` directly -- PASS.
- `LexSenseOperations.SetGrammaticalInfo` (sena3_sandbox) with a wrapper MSA
  -- PASS, re-queried via `ILexSense(project.Object(hvo))`.
- `WfiMorphBundleOperations.SetMorph`/`SetMSA` (sena3_sandbox, real analysed
  wordform) with wrapper allomorph/MSA -- PASS, re-queried via
  `IWfiMorphBundle(project.Object(hvo))`.
- `MSAOperations.ChangeAffixVariant` (sena3_sandbox, MoInflAffMsa -> deriv)
  -- PASS, re-queried via a fresh entry MSA collection.
- `PhonologicalRuleOperations` (target_sandbox, TEST_ rule created fresh):
  `SetName` and `SetDirection`, both PASS via fresh `GetAll()` lookup.
  `SetStratum` was tried first but `IPhPhonRule` has no `StratumRA` field at
  all (unlike the MorphRule types), so it is a true no-op independent of
  #449; swapped to `SetDirection`, a real field.

## Run mode / commands

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_449_wrapper_write_paths_live.py -m requires_live_project -q
```
-> `10 passed, 1 xfailed`. `tests/live_status.json` -> `"run_mode": "live"`.

Offline gate re-run (`python -m pytest -m "not requires_live_project" -q`) ->
148 failed / 2109 passed / 39 skipped / 48 errors, matching cycle 1's stashed
baseline exactly -- no new offline failure.

Note: this worktree had no Target `.fwbackup`; copied read-only from the
sibling `C:/Github/flexicon` checkout (unmodified), same as cycle 1 did for
Sena 3.

## New defects

None inside #449's scope.

## Commits (branch fix/449-wrapper-resolver-unwrap)

- `60489a8` test(#449): live write-path verification for wrapper unwrap sites
- `7af88db` docs(#449): record cycle 1 lex-programmer report and status handoff

Not pushed.
