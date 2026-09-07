# Live verification -- T14a (shipped-suite C3 coverage for MakeFeatStruc, spec feature-structure-sync-gap)

**Project:** Target, via `target_sandbox` only (fresh tempdir copy of the
Target `.fwbackup` per test -- the real, shared Target/Sena 3 projects were
never opened in-place)
**Fixture:** `target_sandbox` (function-scoped) for all three new tests
**New file:** `tests/operations/test_makefeatstruc_c3_live.py`
**Date:** 2026-09-07

## 0. Concurrency-collision check

`git status --porcelain` before and after all work showed only this task's
own files (`tests/operations/test_makefeatstruc_c3_live.py`, this evidence
file, the cycle6-programmer-T14a report). No file under the other crew's
fence (`flexicon/code/TextsWords/`, `specs/name-field-whitespace-identity/`,
`specs/242-paragraph-whitespace/`, `specs/tier1-silent-data-loss/`,
`tests/conftest.py`) was touched, staged, or reverted.

## 1. Scope compliance

No production code was added or left modified. `flexicon/code/BaseOperations.py`
was temporarily mutated for the falsifiability test (section 4 below) and
restored byte-identical before this evidence file was written; verified via
`git hash-object` == `git rev-parse HEAD:...` (both `a32d94151fee1c3c62ccc33e71f3253990b0181a`).
`git status --porcelain flexicon/code/BaseOperations.py` shows no diff.

## 2. PRIMARY -- live run of the new file

Command:
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_makefeatstruc_c3_live.py -m requires_live_project -q
```
Result: **3 passed**, 46 warnings (all deprecation/SLDR noise, none new).
`tests/live_status.json`: `"run_mode": "live"`, all three tests recorded
under `InflectionFeatureOperations` / `add`, status `pass`.

### Pre-state / post-state read back from the LCM (anti-tautology)

Every assertion below re-derives its value from a **fresh**
`project.Object(hvo)` lookup (and a fresh concrete cast), never from the
reference passed into or returned by `MakeFeatStruc`.

**Test 1 -- nested recursive dict** (`TestMakeFeatStrucNestedDictLive`):
- Pre-state: fresh `MoStemMsa` has `MsFeaturesOA is None`.
- Call: `InflectionFeatures.MakeFeatStruc({agreement_feat.Hvo: {number_feat.Hvo: sg_val.Hvo}}, owner=<bare object>)`.
- Post-state (re-fetched via `IMoStemMsa(sandbox.Object(stem_hvo))`):
  `MsFeaturesOA` non-None; its one `FeatureSpecsOC` entry, cast to
  `IFsComplexValue`, has `FeatureRA.Name...Text == "TEST_c14a_agreement"`;
  its `ValueOA`, cast to `IFsFeatStruc`, has one `FeatureSpecsOC` entry,
  cast to `IFsClosedValue`, with `FeatureRA.Name...Text ==
  "TEST_c14a_number"` and `ValueRA.Name...Text == "TEST_c14a_sg"`.

**Test 2 -- `slot=` disambiguation through `MakeFeatStruc`**
(`TestMakeFeatStrucSlotDisambiguationLive`):
- Pre-state: fresh `MoDerivAffMsa` has both `FromMsFeaturesOA` and
  `ToMsFeaturesOA` `None`.
- Calls: `MakeFeatStruc({number_feat.Hvo: sg_val.Hvo}, owner=<fresh bare object>, slot="From")`
  then, against a **second, independently-fetched** `sandbox.Object(deriv_hvo)`,
  `MakeFeatStruc({number_feat.Hvo: pl_val.Hvo}, owner=<fresh bare object>, slot="To")`.
- Post-state (re-fetched via `IMoDerivAffMsa(sandbox.Object(deriv_hvo))`):
  `FromMsFeaturesOA.Hvo != ToMsFeaturesOA.Hvo`; From's closed value's
  `ValueRA.Name...Text == "TEST_c14a_slot_sg"`; To's ==
  `"TEST_c14a_slot_pl"`.

**Test 3 -- ambiguous owner, no slot** (`TestMakeFeatStrucAmbiguousOwnerNoSlotLive`):
- Pre-state: fresh `MoDerivAffMsa` has both feature-struct properties `None`.
- Call: `MakeFeatStruc({}, owner=<bare object>)` (no `slot=`).
- Result: raises `FP_ParameterError` containing both `"MoDerivAffMsa"` and
  `"slot"` -- NOT a silent guess (see ruling in section 5).
- Post-state (re-fetched): both `FromMsFeaturesOA` and `ToMsFeaturesOA`
  remain `None` -- confirms the raise happened before any attach, not a
  partial/guessed write.

## 3. SECONDARY -- pinned offline subset, delta only (own two runs, same shell)

Command: `python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider`

| Run | Result |
|---|---|
| BEFORE (new test file moved out of the tree) | 2 failed, 350 passed, 498 deselected |
| AFTER (new test file restored) | 2 failed, 350 passed, 501 deselected |

Delta: `passed` unchanged (+0); `deselected` up by exactly **3** -- the
three new `requires_live_project` tests added. `failed` unchanged (still
only the two documented known-foreign `test_transaction_rollback.py::TestPhase2JoinOrOpen`
failures). No third or fourth failure appeared.

## 4. DETERMINISM CHECK

Same AFTER command run three times: twice in the same shell, once in a
fresh shell (separate tool invocation, cwd/env reset).

All three: **2 failed, 350 passed, 501 deselected**. Comparator valid.

## 5. FALSIFIABILITY -- mutation test (mandatory)

Backup taken first: copied `flexicon/code/BaseOperations.py` to the
scratchpad before mutating. Pre-mutation blob hash:
`git rev-parse HEAD:flexicon/code/BaseOperations.py` =
`a32d94151fee1c3c62ccc33e71f3253990b0181a`; `git hash-object` on the
working file matched exactly before mutating.

**Mutation:** inside `BaseOperations.__NormalizeFeatStrucLevel`
(`:2575`), changed:
```python
nested = self.__NormalizeFeatStrucLevel(val_raw)
```
to:
```python
nested = val_raw  # MUTATION_TEST_T14A: recursion disabled
```
This defeats the nested-dict branch specifically -- a dict-shaped spec
value is no longer recursively resolved, so it is later mishandled as a
malformed operand instead of a nested `IFsComplexValue.ValueOA`.

**Result (live run against mutated code):**
`tests/operations/test_makefeatstruc_c3_live.py -m requires_live_project -q`
-> **1 failed, 2 passed** (down from the clean baseline's 3 passed).
`TestMakeFeatStrucNestedDictLive::test_nested_dict_spec_round_trips_through_makefeatstruc`
FAILED (a `TypeError` surfaced from the LCM property setter when the
unresolved raw dict was assigned to `ValueRA`, caught and reported by
pytest as a test failure -- a real, non-incidental break). The other two
tests (slot disambiguation, ambiguous-owner raise) do not exercise the
nested-dict branch and correctly remained green -- they are not the
target of this particular mutation.

This confirms the recursive-dict test is a real falsifier, not a
tautology.

**Restore:** copied the pre-mutation backup back over
`flexicon/code/BaseOperations.py` (never `git checkout`).
`git hash-object flexicon/code/BaseOperations.py` =
`a32d94151fee1c3c62ccc33e71f3253990b0181a`, matching
`git rev-parse HEAD:flexicon/code/BaseOperations.py` exactly.
`git status --porcelain flexicon/code/BaseOperations.py` shows no diff.

**Clean re-run after restore:**
`tests/operations/test_makefeatstruc_c3_live.py -m requires_live_project -q`
-> **3 passed**, `run_mode: live` in `tests/live_status.json`. Matches the
pre-mutation baseline exactly.

Because every live test in this file uses `target_sandbox` (a per-test
tempdir copy), the mutation run left **no residue** in the real Target or
Sena 3 projects -- confirmed by `python scripts/restore_target.py --check`
before and after this entire verification (Target present and unlocked
both times). No `restore_sena3.py`/`restore_target.py` restore-from-backup
was needed.

## 6. Ruling on test 3 (ambiguous owner, no slot)

Per the task's instruction to read `FEATURE_STRUC_OWNER_TABLE` and
`_ResolveFeatureStrucOwner` BEFORE deciding whether to write this test:
the resolver does **not** silently pick one of the two rows when an
ambiguous `ClassName`'s owner is passed with `slot=None` -- it raises
`FP_ParameterError` naming the `ClassName` and listing the valid `slot`
values (`BaseOperations.py:1728-1745`). This is documented, deliberate
behaviour (frozen contract C1, "never guessed"), not a silent guess to
avoid ratifying. The test therefore locks the raise, not a guess, and was
written and kept.

## Result

PASS. All three new tests verified live (`run_mode: live`), each
re-fetching from a fresh LCM lookup rather than asserting against the
value just written. Offline pinned-subset delta is `+0 passed / +3
deselected / +0 failed`, deterministic across three runs. The mutation
test falsifies the nested-dict test specifically, and
`BaseOperations.py` is confirmed byte-identical to HEAD after restore.
No production code was added or left modified.
