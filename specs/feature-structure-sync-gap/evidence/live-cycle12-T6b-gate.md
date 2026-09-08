# Live verification -- Cycle 12 T6b gate (Checkpoint 3b)

**Project:** Target (target_sandbox, tempdir copy) | **Fixture:** target_sandbox
**Verifier:** independent verification agent, all commands re-run from scratch.
**Date:** 2026-09-07
**HEAD:** 84b66c86

## Claim under test

T6b (cycle 11) claims item 1 (a direct `__GetMsaObject` C2-cast test on
both HVO and GUID entry paths) is mutation-KILLED where the six
pre-existing live tests were NOT-KILLED at cycle 10, and that items 3-5
are similarly mutation-verified or honestly disclosed as boundary cases.

## Commands run (exact)

Offline comparator (shared tree, no mutation):
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -p no:cacheprovider -q
```
Result: `2 failed, 396 passed, 512 deselected` (same 2 foreign
`TestPhase2JoinOrOpen` failures, unchanged).

Live full file (shared tree, no mutation):
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue251_msa_feature_sync.py -m requires_live_project -q
```
Result: `8 passed, 25 deselected`.

`run_mode` check:
```
python -c "import json; d=json.load(open('tests/live_status.json')); print(d.get('run_mode')); print(d.get('uncategorized_live_tests'))"
```
Output: `live` / `[]`.

## Pre/post hashes

| File | Pre-mutation hash | Post-restore hash | Match |
|---|---|---|---|
| `flexicon/code/Lexicon/MSAOperations.py` | `e7e8f791edb089c0b4ae86f10cca4bcd34900194` | `e7e8f791edb089c0b4ae86f10cca4bcd34900194` | yes (after each of legs 1, 3, 4, 5a) |
| `flexicon/code/BaseOperations.py` | `a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db` | `a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db` | yes (after leg 5b) |

All mutation/restore cycles ran inside disposable worktree `wt-t6b-gate`
(and `wt-t6b-gate2` for the leg-2 isolation probe), created via
`git worktree add <tmpdir> HEAD`, fixture
`tests/fixtures/Target 2026-07-06 0218.fwbackup` copied read-only into
the worktree's own gitignored `tests/fixtures/`. Both worktrees removed
via `git worktree remove --force`; `git worktree prune --dry-run -v`
silent afterward. Shared tree never mutated (`git diff --stat` empty on
both files throughout).

## Leg 1 -- item 1 mutation (LCM re-read after each call)

Mutation: `__GetMsaObject`'s ClassName-dispatch cast table replaced with
`return obj` unconditionally.

Live re-read sequence for `test_hvo_and_guid_path_cast_to_concrete_stem_msa`
(pre-mutation, clean 8-passed run -- values actually observed, not
merely asserted):

1. `stem = sandbox.MSA.CreateStem(new_sense(), pos_obj)` -- write.
2. `hvo = stem.Hvo`; `guid_str = str(stem.Guid)` -- captured from the
   factory handle (write-time reference).
3. FRESH re-fetch: `sandbox.Object(hvo)` -> bare `ICmObject`.
   `hasattr(_, "MsFeaturesOA")` -> `False` (confirmed, this is the
   0-true/2088-false premise check).
4. FRESH re-fetch via the resolver under test:
   `sandbox.MSA._MSAOperations__GetMsaObject(hvo)` ->
   `.ClassName == "MoStemMsa"` (confirmed), `.MsFeaturesOA is None`
   (confirmed -- succeeds only because of the cast).
5. Same again via `_MSAOperations__GetMsaObject(guid_str)` ->
   `.ClassName == "MoStemMsa"` (confirmed), `.MsFeaturesOA is None`
   (confirmed).

Under the mutation (worktree `wt-t6b-gate`), step 4 raised at re-read:
`AttributeError: 'ICmObject' object has no attribute 'MsFeaturesOA'`
(`tests/operations/test_issue251_msa_feature_sync.py:1059`). Analogous
result for `InflFeatsOA` (`:1078`, InflAff test).

Full-file result under mutation: `2 failed, 6 passed` (six pre-existing
live tests still green -- reproduces cycle-10's NOT-KILLED finding for
those six; the two new tests are the only ones that die).

## Leg 2 -- isolation probe (second disposable worktree)

Worktree `wt-t6b-gate2`, same Leg-1 mutation applied plus the HVO-path
assertions in `test_hvo_and_guid_path_cast_to_concrete_stem_msa`
temporarily deleted (test-file-only change, inside the disposable
worktree, never committed, worktree discarded entire afterward -- no
restore needed for a worktree that is deleted wholesale).

Command:
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest "tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncLiveGetMsaObjectCast::test_hvo_and_guid_path_cast_to_concrete_stem_msa" -m requires_live_project -q
```
Result: `1 failed` --
`AttributeError: 'ICmObject' object has no attribute 'MsFeaturesOA'`
at line 1059 (now the GUID-path assertion, run in isolation). Confirms
the GUID path is independently load-bearing, not merely
short-circuit-shadowed by the HVO-path assertion.

Worktree removed: `git worktree remove --force wt-t6b-gate2`.

## Leg 3 -- item 3 mutation (offline, worktree `wt-t6b-gate`)

Mutation: `__ApplyFeatureStrucProp` line 1094,
`if key in props or guid_key in props:` ->
`if props.get(key) or props.get(guid_key):`.

Command:
```
python -m pytest "tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncApplyPresenceGate" -m "not requires_live_project" -q
```
Result: `2 failed, 2 passed`.
- `test_falsy_but_present_feature_struct_key_still_triggers_apply` --
  `assert 0 == 1` at line 715.
- `test_falsy_but_present_guid_only_key_still_triggers_apply` --
  `assert 0 == 1` at line 751.
- `test_guid_only_present_still_triggers_apply_with_empty_spec` -- PASS.
- `test_neither_key_present_never_calls_apply_feature_struc` -- PASS.

Restored; `git hash-object` == `e7e8f791edb089c0b4ae86f10cca4bcd34900194`.

## Leg 4 -- item 2 mutation (offline, worktree `wt-t6b-gate`)

Mutation: `__ApplyFeatureStrucProp` line 1105,
`on_unresolved="raise"` -> `on_unresolved="skip"`.

Command:
```
python -m pytest "tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncApplyRaisePropagationThroughPublicSurface" -m "not requires_live_project" -q
```
Result: `1 failed` --
`assert 'skip' == 'raise'` at line 961. KILLED (contradicts the
programmer's own characterization of this item as unmutated -- it was
in fact never run by them, but this gate ran it and it dies cleanly).

Restored; `git hash-object` == `e7e8f791edb089c0b4ae86f10cca4bcd34900194`.

## Leg 5 -- item 4 AST allowlist non-vacuity

5a: inserted `hasattr(obj, "MsFeaturesOA")` into
`MSAOperations.__GetMsaObject`. Command:
```
python -m pytest "tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncStatic::test_get_msa_object_hasattr_calls_are_allowlisted" -m "not requires_live_project" -q
```
Result: `1 failed` -- `AssertionError: __GetMsaObject calls hasattr(x,
'MsFeaturesOA') -- only ['ClassName', 'Hvo', '_obj'] are permitted.`
at line 287. Restored; hash == `e7e8f791edb089c0b4ae86f10cca4bcd34900194`.

5b: inserted `hasattr(unwrapped, "MsFeaturesOA")` into
`BaseOperations._ResolveFeatureStrucOwner`. Command:
```
python -m pytest "tests/operations/test_issue251_msa_feature_sync.py::TestMSASyncStatic::test_resolve_feature_struc_owner_hasattr_calls_are_allowlisted" -m "not requires_live_project" -q
```
Result: `1 failed` -- `AssertionError: _ResolveFeatureStrucOwner calls
hasattr(x, 'MsFeaturesOA') -- only ['ClassName', 'Hvo', '_obj'] are
permitted (D5).` at line 313. Restored; hash ==
`a8e914bfd7c31d2d34f2a0e42e47794bd4ad32db`.

## Cleanup

Both mutations reverted with `git checkout -- <path>` inside
`wt-t6b-gate` and hash-verified after every single mutation/restore
cycle (5 mutations total: legs 1, 3, 4, 5a on `MSAOperations.py`, leg 5b
on `BaseOperations.py`). Full offline+live worktree suite re-passed
clean after all restores (25 passed / 8 deselected). Both disposable
worktrees removed with `git worktree remove --force`;
`git worktree prune --dry-run -v` silent. Shared tree confirmed
untouched: `git diff --stat` empty on both files, `git status
--porcelain=v1 -uall` shows only the five pre-existing unrelated noise
items (deleted `.claude/ralph-loop.local.md`; untracked
`.vscode/settings.json`, `specs/243-closeproject-save-guard/.spec-context.json`,
`specs/duplicate-signature-harmonisation/evidence/live-issue-246.md`,
`specs/getall-contract-flexicon/.spec-context.json`), none touched or
committed by this gate.

## Result

PASS -- run_mode live throughout, all six mutation legs (1, 2-isolation,
3, 4, 5a, 5b) produced the exact predicted differential, shared tree
restored byte-identical, no overclaim found in any artifact.
