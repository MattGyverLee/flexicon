# Live evidence -- T5 (`MakeFeatStruc` generalization, closes #256)

Spec: `feature-structure-sync-gap`. Comparator: spec.md section 5.1 (FROZEN,
binding from cycle 5).

## Commands (exact, run in the stated order/shell)

All offline runs used:

```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider
```

All live runs used (after `export FLEXLIBS_REQUIRE_LIVE=1` in the same
shell -- this repo's Bash tool is Git Bash/POSIX, so `export VAR=1` was used
in place of the task prompt's PowerShell `$env:FLEXLIBS_REQUIRE_LIVE = "1"`
syntax; semantically identical):

```
python -m pytest tests/operations/test_phon_features.py tests/operations/test_phonemes.py tests/operations/test_natural_classes.py tests/operations/test_natural_class_feature_sync.py tests/operations/test_feature_struc_resolver.py tests/operations/test_apply_feature_struc.py tests/operations/test_issue251_252_256_feature_struct_probe.py -m requires_live_project -q
```

## 1. PRIMARY -- live subset, both sides, same shell

Method: rather than measuring parent-commit-on-disk vs a separate checkout,
the "before" state was reconstructed with `git stash push -- <3 authored
files>` (BaseOperations.py, InflectionFeatureOperations.py,
PhonFeatureOperations.py -- explicit paths only, per the concurrency
protocol) immediately followed by the live run, then `git stash pop` and the
live run again, all in one shell invocation. This is functionally identical
to a parent-commit/HEAD comparison since the stash reverts exactly the T5
diff and nothing else.

| Side | failed | passed | skipped | deselected | `run_mode` |
|---|---|---|---|---|---|
| BEFORE (stashed to parent) | 1 | 77 | 1 | 27 | `live` |
| AFTER (T5, final, hash `a32d94151fee1c3c62ccc33e71f3253990b0181a`) | 1 | 77 | 1 | 27 | `live` |

Identical counts on both sides -- the single known failure is the
pre-existing, documented foreign one
(`test_apply_raises_on_type_mismatch_segments_target`,
`NaturalClassOperations.py:1270`, C2/HVO-cast symptom, expected to fall out
of T10). No `test_issue251_252_256_feature_struct_probe.py` test flips its
pytest PASS/FAIL status, because item 7 (the #256 reproduction) is a
print-only probe with no assertion (see spec.md "Item 7" and the probe
file's own docstring) -- but its *printed evidence* flips exactly as
predicted:

BEFORE (stashed to parent commit):
```
[ITEM 7] Created IMoStemMsa ClassName='MoStemMsa'
[ITEM 7] hasattr(stem, FeaturesOA) = False
[ITEM 7] hasattr(stem, MsFeaturesOA) = True
[ITEM 7] MakeFeatStruc([], owner=stem) result: FP_ParameterError: owner has no FeaturesOA property; cannot attach FsFeatStruc.
```

AFTER (T5, final):
```
[ITEM 7] Created IMoStemMsa ClassName='MoStemMsa'
[ITEM 7] hasattr(stem, FeaturesOA) = False
[ITEM 7] hasattr(stem, MsFeaturesOA) = True
[ITEM 7] MakeFeatStruc([], owner=stem) result: NO EXCEPTION -- returned <SIL.LCModel.IFsFeatStruc object at 0x...>
```

`tests/live_status.json` confirmed `"run_mode": "live"` after every one of
the live invocations in this evidence file (spot-checked timestamps
`2026-09-07T20:27:09Z`, `2026-09-07T20:29:54Z` (see incident note below),
`2026-09-07T20:32:46Z`, `2026-09-07T20:36:36Z`, `2026-09-07T20:38:01Z`).

## 2. SECONDARY -- pinned offline subset, delta only

Command (identical before/after, same shell):
```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider
```

| Side | failed | passed | deselected |
|---|---|---|---|
| BEFORE (stashed to parent) | 2 | 350 | 489 |
| AFTER (T5, final) | 2 | 350 | 489 |

Delta: **0**. The 2 failures are both on the known-foreign list
(`test_transaction_rollback.py::TestPhase2JoinOrOpen::*`). No offline test
was added by T5, so `passed` unchanged and `deselected` unchanged is the
expected delta per section 5.1 rule 2.

## 3. DETERMINISM CHECK

Pinned offline subset run twice in the same shell (immediately after the
stash-pop, AFTER state) and once more in a fresh shell:

| Run | failed | passed | deselected |
|---|---|---|---|
| Same-shell run 1 | 2 | 350 | 489 |
| Same-shell run 2 | 2 | 350 | 489 |
| Fresh-shell run | 2 | 350 | 489 |

All three agree. Comparator is valid (not `FAIL: unfalsifiable`).

## 4. FALSIFIABILITY -- mutation test

Mutation: inserted one line immediately after the `_ResolveFeatureStrucOwner`
call inside `BaseOperations._MakeFeatStruc`:
```python
prop_name = "MUTATION_TEST_BOGUS_PROP"  # T5 mutation test
```
This discards the C1-resolved owning property name and forces every owner
onto a nonexistent property, reproducing the exact shape of the #256 bug
(wrong/absent property name) one level up the call chain.

Live run with the mutation active (`test_phon_features.py test_phonemes.py
test_natural_classes.py -m requires_live_project`):

```
8 failed, 39 passed, 1 skipped, 1 warning
FAILED test_phon_features.py::TestPhonFeatureOperations::test_make_featstruc_owned
FAILED test_phonemes.py::TestPhonemeSync::test_getsyncable_surfaces_feature_specs
FAILED test_natural_classes.py::TestNaturalClassFeatureBased::test_create_feature_based_with_specs_populates_featuresoa
FAILED test_natural_classes.py::TestNaturalClassFeatureBased::test_get_features_returns_featstruc_when_set
FAILED test_natural_classes.py::TestNaturalClassFeatureBased::test_set_features_replaces_existing
FAILED test_natural_classes.py::TestNaturalClassDuplicateDispatch::test_duplicate_features_returns_features_clone
FAILED test_natural_classes.py::TestNaturalClassSync::test_getsyncable_surfaces_feature_specs
FAILED test_natural_classes.py::TestNaturalClassSync::test_apply_raises_on_type_mismatch_segments_target  (the 1 known-foreign)
```

**7 NEW real failures** beyond the 1 known-foreign one -- the mutation is
falsifiable and the tests genuinely exercise the C1 owner-resolution path
through both `NaturalClassOperations`/`PhonemeOperations` (via their
`SetFeatures`/`ApplySyncableProperties` call-throughs to `MakeFeatStruc`)
and `PhonFeatureOperations.MakeFeatStruc` directly.

Mutation reverted; `git hash-object flexicon/code/BaseOperations.py` before
the mutation, after the mutation was reverted, and at final commit-ready
state all read identically: `a32d94151fee1c3c62ccc33e71f3253990b0181a`.

Post-restore live re-run (same 7-file subset) returned to
`1 failed, 77 passed, 1 skipped, 27 deselected` -- the clean baseline.

### Incident during the mutation test, disclosed

`test_phon_features.py`, `test_phonemes.py`, and `test_natural_classes.py`
open the **real "Sena 3" project directly, write-enabled, module-scoped, no
sandbox** (`_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon",
"SampleLexicon3")`), per the file's own header note: "residue is a
diagnostic signal on failure rather than hidden state." The mutation
deliberately broke `test_make_featstruc_owned`'s downstream assertions;
although that specific test's own `finally:` block correctly cleaned up its
catalog feature, one or more of the *other* 7 tests broken by the same
mutation left the catalog feature `fPAConsonantal`/its child value
`vPAConsonantalPositive` (canonical GUID
`ec5800b4-52a8-4859-a976-f3005c53bd5f`) in a state that caused a **second**,
unrelated-looking failure on the next run
(`test_create_from_catalog_uses_canonical_guid` and 9 others, all
`FP_ParameterError: Could not create feature value ... via either
Create(Guid, parent) or Create(Guid) factory overloads`) -- i.e. residue
from the intentional mutation run, not a new defect.

Remedied with `python scripts/restore_sena3.py` (the documented remedy --
its own header: "Re-run after any session to wipe accumulated test
mutations"), run **twice**: once after the first mutation-test pass (pre
transaction-bracketing fix) and once after the final mutation-test pass
(post transaction-bracketing fix, i.e. the code actually shipped). Both
restores were verified by a clean live re-run immediately after (`1 failed,
77 passed`). The real `Target` project was never touched -- none of the
mutation-affected files use `target_project`/`target_sandbox`; the probe
file's item 7 is the only mutation-affected test using `target_sandbox`
(ephemeral tempdir copy per test, no persistent residue possible there).

**Lesson for future mutation tests against this suite:** prefer scoping a
live mutation-falsifiability run to files that use `target_sandbox`/
`sena3_sandbox` fixtures where possible; where the target files under test
use a direct-write module-scoped `writable_project` fixture (as these three
do), budget a `restore_sena3.py` run immediately after and verify clean
before considering the gate closed.

## 5. Nested round-trip (definition-of-done item 6)

Not re-proven here -- T4's evidence (`live-T4.md`) already demonstrates
nested recursion end-to-end for the C4/C5 apply surface
(`_ApplyFeatureStruc`/`_ApplyFeatureStrucSpecMap`), and
`test_feature_struc_resolver.py::TestGetFeatureStrucLive::test_nested_struct_round_trips_full_c4_shape`
(passed in every run above) covers the serialize side. T5's own recursive
dict support for `MakeFeatStruc` (C3) is covered by construction --
`__PopulateFeatStrucLevel`'s nested branch is the same
create-IFsComplexValue-then-recurse shape as `_ApplyFeatureStrucSpecMap`'s,
and the mutation test above proves the resolution path it depends on
(`_ResolveFeatureStrucOwner`) is live-exercised -- but no NEW dedicated live
test was added in T5 asserting a multi-level nested `MakeFeatStruc(...)`
dict end-to-end against a live MSA/POS owner. This is recorded as a gap for
T14 (spec.md), which already owns "nested round-trip ... slot=
disambiguation errors, unknown-ClassName raise" as its own task.
