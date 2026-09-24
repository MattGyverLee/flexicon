# Live evidence -- #330 SetDateOfEvent / SetDateOfBirth GenDate (HANDOFF item 3a)

**Date:** 2026-09-23
**Project:** `target_sandbox` (tempdir copy of the Target `.fwbackup`)

## Finding: #376 did not fix #330

With #376 on `main`, the new live test fails on every call:

```
record.DateOfEvent = gen_date_str
TypeError: 'str' value cannot be converted to SIL.LCModel.Core.Cellar.GenDate
3 failed in 2.86s
```

pythonnet converts neither `str` nor `System.DateTime` to `GenDate`. #376
swapped one unconvertible type for another. `PersonOperations.SetDateOfBirth`
had the same `str` assignment (sweep sibling: `ICmPerson.DateOfBirth` and
`DateOfDeath` are also `GenDate`, per live reflection).

## Fix

`flexicon/code/Shared/gendate_utils.py::gendate_from_input` builds
`GenDate(PrecisionType.Exact, month, day, year, ad=True)`. Both setters use it.
`GenDate` has no time component, so any time of day is dropped.

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue330_setdateofevent_live.py -m requires_live_project -q
```

`tests/live_status.json` -> `"run_mode": "live"`

## Pre / post state (re-queried by GUID, GenDate components)

| Call | Pre (fresh TEST_ object) | Post `(Year, Month, Day)` / `IsEmpty` |
|---|---|---|
| `SetDateOfEvent(rec, "2024-06-01")` | empty | `(2024, 6, 1)` / False |
| `SetDateOfEvent(rec, DateTime(2023,11,20,9,15,0))` | empty | `(2023, 11, 20)` / False |
| `SetDateOfEvent` "2020-01-02" then "2021-03-04" | empty | `(2021, 3, 4)` / False |
| `SetDateOfBirth(p, "1985-03-15")` | empty | `(1985, 3, 15)` / False |
| `SetDateOfBirth(p, "")` | `(1985, 3, 15)` | `IsEmpty` True |

## Result

- Before fix: `3 failed` (the DateOfEvent tests; TypeError above)
- After fix: `[PASS] 4 passed in 3.35s`

## Follow-on: FindByDate compared GenDate with DateTime

Code-review finding on the #330 fix. `FindByDate` still parsed string bounds
into `System.DateTime`. `GenDate.op_LessThan` / `op_GreaterThan` take two
`GenDate` operands only, so any bounded query that reached a dated record
raised:

```
TypeError: No method matches given arguments for GenDate.op_LessThan: (<class 'System.DateTime'>)
```

A second defect showed up while probing. An unset `DateOfEvent` is an empty
`GenDate` struct, and under pythonnet that struct is truthy. So
`GetDateOfEvent` returned the empty date instead of `None`, and an
upper-bounded query included undated records (`empty < hi` is `True`).

**Fix:** `FindByDate` normalizes non-`None` bounds with `gendate_from_input`,
so a bad bound raises `FP_ParameterError` before iteration. `GetDateOfEvent`
returns `None` when `IsEmpty`.

**Command** (same file, new class `TestIssue330FindByDateLive`):

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue330_setdateofevent_live.py -m requires_live_project -q
```

`tests/live_status.json` -> `"run_mode": "live"` (run_timestamp 2026-09-23T14:25:30Z)

**State.** Four fresh `TEST_330 find *` records. Values were re-read by GUID
after the writes:

| Record | Written | Read back | `GetDateOfEvent` |
|---|---|---|---|
| early | "2023-12-31" | `(2023, 12, 31)` | GenDate |
| mid | "2024-06-01" | `(2024, 6, 1)` | GenDate |
| late | "2025-01-01" | `(2025, 1, 1)` | GenDate |
| undated | -- | `IsEmpty == True` | `None` |

| Query | Result (restricted to the four TEST_ records) |
|---|---|
| `FindByDate("2024-01-01", "2024-12-31")` | `[mid]` |
| `FindByDate(start_date="2024-01-01")` | `[late, mid]` |
| `FindByDate(end_date="2024-12-31")` | `[early, mid]` (undated excluded) |

**Result:** `5 passed in 3.52s` (live). Offline: `2222 passed, 940 deselected`.
Before the fix, all 8 new offline tests in `TestIssue330FindByDateGenDate`
failed.
