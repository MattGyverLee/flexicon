# live-291-cascade.md -- issue #291, swallowed cascade-delete assertion

Scope: `tests/operations/test_wfi_analysis.py`
(`TestWfiAnalysisDeleteWithMorphBundles::test_delete_analysis_with_morph_bundle_cascades`),
plus the sibling site found by the pattern audit in
`tests/test_pattern_writing_systems_enumeration.py`.

This is a test-integrity change, not an Operations/LCM change. The
live run below satisfies the requirement in the issue: "confirming the
corrected assertion still passes when the cascade genuinely succeeds".

## The defect

`test_wfi_analysis.py:675-686` placed an `assert` INSIDE a
`try: ... except Exception: pass`. `AssertionError` is a subclass of
`Exception`, so a genuinely surviving `WfiMorphBundle` -- i.e. cascade
delete NOT firing, the one claim the test exists to prove -- was caught
and discarded, and the test reported green.

## Mechanism, demonstrated deterministically (offline)

Standing in a fake `Object()` that returns a SURVIVING bundle, i.e.
cascade delete failed:

```
=== OLD shape (assert inside try) ===
[FAIL] test reported GREEN despite a surviving bundle

=== NEW shape (assert outside try) ===
[OK] assertion propagated: cascade delete did not fire

=== NEW shape, cascade genuinely succeeded (Object raises) ===
[OK] exception path still treated as 'gone'; test passes
```

So the restructure (a) makes a real cascade failure fail the test, and
(b) preserves the handler's legitimate purpose -- `FLExProject.Object`
calls `ServiceLocator.GetObject(hvo)`, which raises for a deleted HVO,
and that path still means "gone".

## The fix

`assert` moved out of the `try`; the handler now assigns
`leftover = None` instead of `pass`:

```python
try:
    leftover = writable_project.Object(bundle_hvo)
except Exception:
    leftover = None

assert leftover is None, (...)
```

## Live command and result

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest "tests/operations/test_wfi_analysis.py::TestWfiAnalysisDeleteWithMorphBundles" -m requires_live_project -q
```

```
.                                                                        [100%]
1 passed in 6.13s
```

`tests/live_status.json`:

```
run_mode -> live
```

`run_mode: "live"` -- a genuine live run, not a mock degradation. The
corrected assertion executes and passes against a real cascade delete.

Note on the project used: this test file carries its own module-local
`writable_project` fixture (`test_wfi_analysis.py:31-66`) which opens
one of `("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")`
**in place**, write-enabled -- not one of the `*_sandbox` tempdir
fixtures CLAUDE.md prescribes. That is pre-existing and was not changed
here, but it is worth converting to `sena3_sandbox` separately.

## Pre-state / post-state re-queried from the LCM

Performed by the test body itself, unchanged by this fix:

- Pre-state: created a throwaway `WfiAnalysis` on an existing wordform,
  added one `WfiMorphBundle` inside an `UndoableOperation`, captured
  `bundle_hvo`, and asserted `MorphBundlesOS.Count == 1`.
- Action: `WfiAnalyses.Delete(analysis)`.
- Post-state: re-queried `candidate_wf.AnalysesOC.Count` (back to the
  starting count) and re-resolved `bundle_hvo` through
  `writable_project.Object()` -- a fresh repository lookup, not the
  in-memory bundle reference. The bundle no longer resolves, so the
  cascade fired.

## Pattern audit (CLAUDE.md sweep-pattern discipline)

An AST sweep of all of `tests/` for `assert` statements lexically inside
a `try` whose handler catches `Exception`/`BaseException`/bare found 8
further sites beyond the one in the issue:

- `tests/test_operations_baseline.py` lines 269, 270, 317, 321, 345,
  360, 361 -- **BENIGN**. Handler body is `pytest.fail(...)`, not
  `pass`, so a swallowed `AssertionError` is immediately re-raised as a
  test failure. Only the failure MESSAGE is degraded (it arrives wrapped
  as "Failed to instantiate X: ..."), not the pass/fail outcome. Left
  alone.
- `tests/test_pattern_writing_systems_enumeration.py:147` -- **GENUINE
  SIBLING, FIXED**. Handler is `except Exception as exc:
  pytest.skip(...)`, so a failing
  `assert isinstance(props, dict)` was converted into a SKIP. Arguably
  worse than the #291 site: a skip is routinely ignored in CI summaries,
  whereas a pass at least implies something ran. Fixed by the same
  restructure (assert hoisted out of the `try`, `props` initialised to
  `None` before it).

  Note `pytest.fail`/`pytest.skip` raise `_pytest.outcomes.OutcomeException`,
  which derives from `BaseException`, NOT `Exception` -- so the
  deliberate `pytest.fail` for the WritingSystems regression inside that
  same block was never swallowed and still works. Only the plain
  `assert` was affected.

Verification of the sibling fix:

```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/test_pattern_writing_systems_enumeration.py -q
```

```
5 passed in 6.02s
```

5 passed, 0 skipped -- confirming the restored assertion actually
executes (had it still been swallowed into a skip, the count would show
skips).

The 5 sites the issue itself triaged BENIGN (`except StopIteration:
pass` in `test_allomorphs_live.py:138`, `test_etymologies_live.py:176`,
`test_examples_live.py:136`, `test_pronunciations_live.py:184`,
`test_variants_live.py:197`) were re-confirmed benign by the same sweep:
`AssertionError` is not a `StopIteration`, so it propagates. Not
re-triaged.

## Pass/fail line

**PASS.** The swallowed assertion at `test_wfi_analysis.py:682` is
fixed; the corrected test passes live against a genuine cascade delete
(`run_mode: live`), and the offline mechanism demonstration confirms it
would now FAIL if the cascade did not fire. One genuine sibling of the
same bug class was found by pattern audit and fixed; seven further hits
were triaged benign with reasons recorded above.
