# live-277-environments.md -- EnvironmentOperations half of issue #277

Scope: `flexicon/code/Grammar/EnvironmentOperations.py:_GetSequence`. The
`OverlayOperations.py` half of #277 is owned by a different, concurrently
running agent and is NOT covered by this file.

## Commands run (verbatim)

RED (unmodified source, `EnvironmentOperations.py` temporarily reverted via
`git stash push -- flexicon/code/Grammar/EnvironmentOperations.py`):

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_277_environment_sequence_property.py -m requires_live_project -q
```

GREEN (fix restored via `git stash pop`, identical command):

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_277_environment_sequence_property.py -m requires_live_project -q
```

Both runs executed against `target_sandbox` (a fresh tempdir copy of the
Target `.fwbackup`).

## `tests/live_status.json` run_mode (verbatim, GREEN run)

```json
"run_mode": "live"
```

Confirmed via:
```
python -c "import json; print(json.load(open('tests/live_status.json'))['run_mode'])"
-> live
```

If this had printed `mock`, none of the below would count as verification;
it did not.

## RED result (verbatim, unmodified source)

```
2 failed, 2 passed in 4.94s
FAILED tests/operations/test_277_environment_sequence_property.py::TestP2GetSequenceRegression::test_get_sequence_returns_the_real_environments_owning_sequence
FAILED tests/operations/test_277_environment_sequence_property.py::TestP3ReorderEndToEndViaTypedParent::test_move_up_reorders_environments_via_typed_parent
```

Failure body (P2, and identically for P3 via `BaseOperations.MoveUp` ->
`self._GetSequence(parent)`):

```
def _GetSequence(self, parent):
    """
    Specify which sequence to reorder for environments.
    For Environment, we reorder parent.EnvironmentsOA.PossibilitiesOS
    """
>   return parent.EnvironmentsOA.PossibilitiesOS
           ^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'IPhPhonData' object has no attribute 'EnvironmentsOA'. Did you mean: 'EnvironmentsOS'?

flexicon\code\Grammar\EnvironmentOperations.py:77: AttributeError
```

This is the LIVE reflection evidence for step 2 of the task: `parent`
(`self.project.lp.PhonologicalDataOA`, an already-cast `SIL.LCModel.IPhPhonData`
instance) has no `EnvironmentsOA` member, and pythonnet's own error message
confirms the real name is `EnvironmentsOS` -- exactly the claim in the task
briefing, now measured live rather than asserted from reading source.

TestP1 (independent live `.NET` reflection via
`clr.GetClrType(IPhPhonData).GetProperties()`) and TestP4 (the parent-contract
finding, see below) do not depend on the fix and passed in BOTH the RED and
GREEN runs, confirming they measure a live, fix-independent property of the
LCM API rather than an artifact of the patch.

## GREEN result (verbatim, fix applied)

```
....                                                                     [100%]
4 passed in 4.55s
```

`tests/live_status.json` `by_class.EnvironmentOperations` after the GREEN run:

```json
"modify": {
  "last_verified": "2026-09-09",
  "status": "pass",
  "tests": ["...TestP3ReorderEndToEndViaTypedParent::test_move_up_reorders_environments_via_typed_parent"]
},
"read": {
  "last_verified": "2026-09-09",
  "status": "pass",
  "tests": [
    "...TestP1LiveReflectionPropertyNames::test_environments_os_exists_environments_oa_does_not",
    "...TestP2GetSequenceRegression::test_get_sequence_returns_the_real_environments_owning_sequence",
    "...TestP4ParentHvoContractFinding::test_get_object_on_genuine_phon_data_hvo_environments_os_reachability"
  ]
}
```

## Pre-state / post-state re-queried from the LCM (TestP3, GREEN run)

- Pre-state: created three environments `TEST_277_a`, `TEST_277_b`,
  `TEST_277_c` via `EnvironmentOperations.Create`, then re-fetched their
  order via a FRESH `GetAll()` enumeration (not the objects returned by
  `Create`): confirmed `b` immediately precedes `c`.
- Action under test: `sandbox.Environments.MoveUp(phon_data, env_c,
  positions=1)`, where `phon_data` is the SAME already-typed
  `PhonologicalDataOA` object `GetAll`/`Create`/`Delete`/`Duplicate` all use
  internally (not an HVO). Returned `1` (one position moved).
- Post-state: re-fetched via a SECOND, independent fresh `GetAll()`
  enumeration and re-read names via `GetName` on each freshly-yielded object.
  Confirmed `c` now immediately precedes `b` -- the move persisted through
  the LCM, not just in the in-memory `env_c`/`phon_data` references held by
  the test.
- Cleanup: all three test environments deleted in a `finally:` block;
  confirmed by re-running `GetAll()` after the test (not asserted in the
  test body, but consistent with `target_sandbox` being a disposable
  tempdir copy regardless).

## Property-name reflection (TestP1, both runs)

Live `.NET` reflection via `clr.GetClrType(IPhPhonData).GetProperties()`:
- `EnvironmentsOS` -- present.
- `EnvironmentsOA` -- absent.

This matches the pythonnet `AttributeError` hint seen in the RED run
character-for-character ("Did you mean: 'EnvironmentsOS'?").

## Step 3 finding: the `_GetObject` / parent-contract question (TestP4)

**Measured live, both RED and GREEN runs (fix-independent):**
`BaseOperations._GetObject` on a genuine `IPhPhonData` HVO (int) returns a
bare object on which `hasattr(resolved, "EnvironmentsOS")` is **`False`**.

Mechanism (per the flexicon#260 precedent already documented in this
codebase): `_GetObject` (`BaseOperations.py:1673-1675`) calls
`self.project.Object(obj_or_hvo)` for an int input, which returns a bare
`ICmObject` view -- pythonnet's static-wrapper-type gate means this view
exposes only members declared on `ICmObject` itself, not on the concrete
`IPhPhonData` interface, regardless of the runtime type of the underlying
.NET object. No cast to `IPhPhonData` is performed anywhere in
`_GetObject` or in `EnvironmentOperations`.

**Practical consequence, stated precisely:**
- The property-name fix (`_GetSequence` returning `parent.EnvironmentsOS`)
  is CORRECT and VERIFIED LIVE (TestP1, TestP2).
- The reorder path (`MoveUp`/`MoveDown`/`MoveToIndex`/`Sort`) is VERIFIED
  LIVE END-TO-END (TestP3) **only for the calling convention
  `EnvironmentOperations` itself uses everywhere else in the file**: an
  already-typed `PhonologicalDataOA` object (`self.project.lp.PhonologicalDataOA`),
  never an HVO. This is realistically how any caller would invoke it too,
  since nothing in this codebase exposes a way to obtain an
  `IPhPhonData` HVO other than reading `PhonologicalDataOA.Hvo` off the
  object itself -- there is no `EnvironmentOperations` method that hands a
  caller a bare phon-data HVO to round-trip back in.
- If a caller instead passes the raw HVO int as `parent_or_hvo` to
  `MoveUp`/`MoveDown`/`MoveToIndex`/`Sort` (e.g. `envOps.MoveUp(phon_data.Hvo,
  item)`), `_GetObject` resolves it to a bare `ICmObject`, and
  `_GetSequence`'s `parent.EnvironmentsOS` access will raise
  `AttributeError` on THAT path too -- an independent, pre-existing gap in
  `BaseOperations._GetObject` (it never casts), not something introduced or
  fixed by this change, and not exercised by any current caller in this
  codebase. This is the same missing-cast shape as flexicon#260's
  `EnvironmentOperations.__ResolveObject`, but on `_GetObject` in the
  shared base class, so a general fix (if wanted) belongs at the
  `BaseOperations._GetObject` level, potentially affecting every
  `_GetSequence` override, not something to special-case in
  `EnvironmentOperations`. Filing this as a new, separate issue is
  recommended rather than folding it into #277's one-line fix.

## Pass/fail line

**PASS (property-name fix, live-verified):**
`EnvironmentOperations._GetSequence` now reads `parent.EnvironmentsOS`,
confirmed correct by live `.NET` reflection (TestP1) and by the regression
test failing on the old code / passing on the fix (TestP2).

**PASS (reorder path, live-verified, typed-parent calling convention only):**
`MoveUp` (and by direct code-path inspection, `MoveDown`/`MoveToIndex`/`Sort`,
which share the identical `self._GetObject(parent_or_hvo)` ->
`self._GetSequence(parent)` call shape) now works end-to-end when called
with the already-typed `PhonologicalDataOA` object, live-verified (TestP3).

**FINDING, not a defect in scope for #277:** the HVO-parent calling
convention for these same four reorder methods was never wired up for
`IPhPhonData` (missing cast in the shared `BaseOperations._GetObject`,
not in `EnvironmentOperations`), confirmed live (TestP4) both before and
after this fix -- unaffected by it either way. Recommend filing separately.
