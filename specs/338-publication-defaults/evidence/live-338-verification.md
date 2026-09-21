# Live LCM Regression Verification Report

## Test File
`tests/operations/test_issue338_publication_defaults_live.py`

## Execution Command
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest tests/operations/test_issue338_publication_defaults_live.py -m requires_live_project -q
```

## Run Mode
`live`

## Test Case Results
- `LexEntry.Create(create_blank_sense=True)`: 1 passed
- `Senses.Create`: 1 passed
- `LexEntry.AddSense`: 1 passed
- `Senses.CreateSubsense`: 1 passed
- `Examples.Create`: 1 passed
- `Senses.AddExample`: 1 passed

## Overall Verification Status
[PASS] All 6 test cases passed in live mode.