# Issue #449 -- live WRITE-path verification (cycle 2)

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_449_wrapper_write_paths_live.py -m requires_live_project -q
```

(Run here via Git Bash as `export FLEXLIBS_REQUIRE_LIVE=1 && python -m pytest ...` --
same effect.)

## Result

`10 passed, 1 xfailed in 26.75s`. `tests/live_status.json` -> `"run_mode": "live"`.

Target `.fwbackup` (`Target 2026-07-06 0218.fwbackup`) was copied read-only from the
sibling `C:/Github/flexicon` checkout into this worktree's `tests/fixtures/`, exactly
as cycle 1 did for the Sena 3 backup -- this worktree had no Target fixture and
`C:/Github/flexicon` was not modified.

## Pre-state / post-state per case

| Case | Fixture | Pre-state | Action | Post-state (re-queried) | Result |
|---|---|---|---|---|---|
| MorphRuleOperations.SetDisabled | sena3_sandbox | `Disabled=False` on a MoExoCompound wrapper | `SetDisabled(wrapper, True)` | Fresh `GetAll()` lookup by Hvo: `Disabled=True` | PASS |
| MorphRuleOperations.SetStratum | sena3_sandbox | `GetStratum(wrapper)=None` | Created `TEST_449_stratum`, `SetStratum(wrapper, new)` | Fresh lookup: `GetStratum(fresh).Hvo == new.Hvo` | PASS |
| MorphRuleOperations.Duplicate | sena3_sandbox | 4 MoExoCompound rules | `Duplicate(wrapper)` | Fresh `GetAll()`: 5 MoExoCompound, dup Hvo present | PASS |
| MorphRuleOperations.Delete | sena3_sandbox | 4 MoExoCompound rules | `Delete(wrapper)` | Fresh `GetAll()`: 3 MoExoCompound, target Hvo absent | PASS |
| MorphRuleOperations.Delete (affix template) | sena3_sandbox | N MoInflAffixTemplate | `Delete(wrapper)` | Fresh `GetAll()`: still N (unchanged) | XFAIL (expected -- known owner-resolution bug, out of #449 scope, documented in cycle1-sweep.md) |
| Reorder family (MoveUp/Down/Before/After/Swap) | target_sandbox | `[TEST_449_alt_a, _b, _c]` | 5 chained wrapper-item moves | Each step re-queried via `entry.AlternateFormsOS` directly: `[a,c,b] -> [c,a,b] -> [b,c,a] -> [b,a,c] -> [c,a,b]` | PASS (all 5 sub-assertions) |
| LexSenseOperations.SetGrammaticalInfo | sena3_sandbox | sense.MorphoSyntaxAnalysisRA = MSA A | `SetGrammaticalInfo(sense, wrapper(MSA B))` | Fresh `ILexSense(project.Object(hvo))`: `MorphoSyntaxAnalysisRA.Hvo == B.Hvo`, `!= A.Hvo` | PASS |
| WfiMorphBundleOperations.SetMorph/SetMSA | sena3_sandbox | bundle.MorphRA=X, MsaRA=Y | `SetMorph(bundle, wrapper(allomorph))`, `SetMSA(bundle, wrapper(msa))` | Fresh `IWfiMorphBundle(project.Object(hvo))`: both changed, both match wrapped Hvo | PASS |
| MSAOperations.ChangeAffixVariant | sena3_sandbox | MoInflAffMsa, entry has N MSAs | `ChangeAffixVariant(wrapper, "deriv")` | Fresh entry re-query: new MoDerivAffMsa present, no sense still points at old Hvo | PASS |
| PhonologicalRuleOperations.SetName | target_sandbox | `TEST_449_phon_rule` | `SetName(wrapper, "..._renamed")` | Fresh `GetAll()` lookup: name is `"..._renamed"` | PASS |
| PhonologicalRuleOperations.SetDirection | target_sandbox | `Direction=0` | `SetDirection(wrapper, 1)` | Fresh `GetAll()` lookup: `Direction=1` | PASS |

Note: `PhonologicalRuleOperations.SetStratum` was tried first for the last case but
`IPhPhonRule` has no `StratumRA` at all (unlike `IMoCompoundRule`/
`IMoInflAffixTemplate`), so the `hasattr` guard makes it a true no-op independent of
#449 -- swapped for `SetDirection`, a real field on the type, documented inline in the
test.

## Defects found

None inside #449's scope. The one xfail (`MorphRuleOperations.Delete` on an affix
template) is the pre-existing, separately-tracked owner-resolution bug already
identified and documented in cycle 1 (`_GetObject(rule.Owner.Hvo)` returns a bare
`ICmObject`); it reproduces identically with or without a wrapper, so it is not a
#449 regression and is left as `xfail`, not fixed here.

## PASS/FAIL

**PASS: live-verified.** All 10 real write-path cases pass against a live LCM with
read-back confirmation; 1 case is a documented, out-of-scope `xfail`.
