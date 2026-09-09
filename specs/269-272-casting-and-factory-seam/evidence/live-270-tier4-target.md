# Live verification -- issue #270 Tier 4 (target_sandbox retarget)

**Project:** Target | **Fixture:** target_sandbox (tempdir copy of the Target
.fwbackup)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_collection_cast_pattern.py -m requires_live_project -q -rs
```
**run_mode:** live (tests/live_status.json shows "run_mode": "live",
"run_timestamp": "2026-09-09T15:57:21Z")
**Date:** 2026-09-09

## Claim under test

ConstChartCellTagOperations.GetAll(row) returns the ConstChartTag
objects actually present in row.CellsOS (pre-fix isinstance filter
matched nothing and always returned [], issue #270 Tier 4).

## Official run result

```
....                                                                     [100%]
4 passed, 68 deselected in 6.86s
```

tests/live_status.json records by_class.ConstChartCellTagOperations.add
= status pass, tests =
[test_chart_cell_tag_getall_is_not_empty_when_tags_exist].

THIS PASS IS A FALSE POSITIVE and must not be reported as verification.
Two defects compound to produce it.

### Defect A -- pre-existing bug in ConstChartRowOperations.Create, unrelated to #270

flexicon/code/Discourse/ConstChartRowOperations.py line 132 calls
new_row.Label.set_String(wsHandle, mkstr) whenever label= is passed.
Label on IConstChartRow is a bare ITsString (no set_String method,
unlike an IMultiString/ITsMultiString property). Confirmed live via a
disposable diagnostic that made the identical call the real test makes
(target_sandbox.ConstChartRows.Create(chart, label="TEST_270_row")):

```
AttributeError: ITsString object has no attribute set_String. Did you
mean: ToString.
  flexicon/code/Discourse/ConstChartRowOperations.py:132
```

The real test (tests/operations/test_collection_cast_pattern.py line
1020) calls rows.Create(chart, label="TEST_270_row") -- the same shape --
so it hits this same AttributeError inside its try block, before ever
reaching ConstChartCellTagOperations.Create/.GetAll (lines 1024-1036).
The Tier 4 assertion under test never executes in the shipped test.

### Defect B -- return inside the finally block swallows the exception

tests/operations/test_collection_cast_pattern.py lines 1037-1053:

```
        finally:
            if chart is not None:
                try:
                    charts.Delete(chart)
                except Exception:
                    pass
            for item in (marker, col):
                if item is not None:
                    try:
                        markers.Delete(item)
                    except Exception:
                        pass
                return          # <-- inside the for-loop, inside finally
        pytest.skip("No chart row with a ConstChartTag found in Sena 3")
```

The return at line 1053 is indented inside the for loop (same level as
the if item is not None: above it), so it executes unconditionally after
the first loop iteration (item = marker). A return inside a finally
block suppresses any exception propagating out of the corresponding
try block (documented Python semantics). Reproduced in isolation
(scratchpad script, not committed):

```
def demo():
    try:
        assert False, "simulated failed post-state assertion"
    finally:
        for item in ("marker", "col"):
            if item is not None:
                pass
            return
try:
    demo()
    print("demo returned normally -- exception was SWALLOWED")
except AssertionError as e:
    print("propagated:", e)
```
Output: demo returned normally -- exception was SWALLOWED.

Consequences:
1. The AttributeError from Defect A is silently discarded; pytest sees a
   normal return and reports the test as passed.
2. col (the second marker, TEST_270_col) is never deleted -- the loop
   returns after processing only the first tuple element (marker). In
   the real run against the Target sandbox this leaks a ConstChartMarker
   named TEST_270_col into the (discarded) sandbox tempdir, so there is
   no lasting leak on the real Target, but the cleanup logic itself is
   broken.
3. The dangling pytest.skip call for Sena 3 at line 1054 is unreachable
   dead code left over from the pre-fix version of the test.

## Isolating the actual Tier 4 mechanism (diagnostic, not the shipped test)

To determine whether the underlying GetAll fix is itself correct
(independent of Defects A and B), a disposable pytest file was created in
tests/, run once against target_sandbox, and deleted immediately after
(never committed; git status before and after shows no residual file).
It repeated the shipped test precondition construction but called
ConstChartRows.Create(chart) with no label= argument to sidestep Defect
A, and used ordinary (non-buggy) cleanup.

Pre-state (read from LCM): row.CellsOS.Count == 0 immediately after row
creation.

Action: ConstChartCellTags.Create(row, col, marker) called twice.

Post-state (re-queried from LCM, not from the values passed in):
```
EXPECTED_HVOS [10446, 10447]
ACTUAL_HVOS   [10446, 10447]
```
(EXPECTED_HVOS = [c.Hvo for c in row.CellsOS if c.ClassName ==
"ConstChartTag"]; ACTUAL_HVOS = [t.Hvo for t in cell_tags.GetAll(row)])

len(actual) == 2 and actual == expected held. Cleanup (chart delete, both
marker deletes) completed without error; sandbox tempdir discarded by
the fixture teardown as usual.

Conclusion: the Tier 4 isinstance-filter fix in
ConstChartCellTagOperations.GetAll is genuinely correct and was observed
live. But this was proven by a disposable diagnostic, not by the shipped
test, which never reaches that code due to Defect A plus Defect B.

## Cleanup

Both diagnostic files (tests/test_zzz_diag_270_tier4.py,
tests/test_zzz_diag_270_tier4b.py) were deleted immediately after each
run. target_sandbox is a tempdir copy of the Target .fwbackup, discarded
by fixture teardown; the real Target project
(C:\ProgramData\SIL\FieldWorks\Projects\Target) was never opened by this
verification. No production or test file was modified by this agent;
git status --porcelain shows only the pre-existing cycle-2 programmer
edit to test_collection_cast_pattern.py.

## Corrected diagnosis of the cycle-1 Tier 4 skip

specs/269-272-casting-and-factory-seam/evidence/live-270-tier34.md
(cycle 1) reports the observed pytest output as:
```
SKIPPED [1] tests/operations/test_collection_cast_pattern.py:1005:
Sena 3 has no constituent charts
```
and attributes this to Sena 3 genuinely containing zero constituent
charts. This attribution is inconsistent with the code and cannot be
correct as described. The pre-fix line was
charts = list(sena3_sandbox.ConstChart.GetAll()) -- ConstChart
(singular). FLExProject (flexicon/code/FLExProject.py) defines only
ConstCharts (plural, line 2820) and no ConstChart property; the class
defines no __getattr__ or __getattribute__ override (confirmed by grep
of the full file). Accessing sena3_sandbox.ConstChart therefore raises
AttributeError unconditionally, regardless of what Sena 3 contains, and
execution can never reach the pytest.skip call two lines later. Cycle 1
"no constituent charts" data-shape explanation, and its verbatim-looking
skip message, could not have been produced by this code path. The
correct diagnosis is the one cycle 2 programmer report already gives: an
accessor typo caused an unconditional AttributeError, not a genuine
data-shape skip. Whether cycle 1 actually ran the file or transcribed an
expected or hypothetical message is outside this verifier ability to
determine; either way, the report causal claim is wrong.

## Result

- Tier 4 mechanism (ConstChartCellTagOperations.GetAll isinstance fix):
  verified correct live, via disposable diagnostic re-querying the LCM
  after the write (HVOs [10446, 10447] matched on both sides).
- Shipped test test_chart_cell_tag_getall_is_not_empty_when_tags_exist:
  [FAIL: unverified] -- it reports passed but never executes its own
  Tier 4 assertion, because ConstChartRowOperations.Create with label=
  raises AttributeError first, and that exception is silently swallowed
  by a return misplaced inside the test own finally block. The pytest
  4 passed result for this file must not be cited as verification of
  issue #270 Tier 4.
- Cycle 1 causal claim (Sena 3 has no constituent charts, a genuine
  data-shape skip) is wrong; the true cause was an unconditional
  AttributeError from the ConstChart/ConstCharts accessor typo, matching
  cycle 2 diagnosis, not cycle 1.
