# Issue #528 offline evidence (cron)

## Command

```
python3 -m pytest -m "not requires_live_project" \
  tests/operations/test_issue528_replace_analysis_hvo_offline.py \
  tests/operations/test_segment_operations.py::TestSegmentAnalysesRSWriteMethods::test_ReplaceAnalysis_finds_by_hvo_not_python_identity \
  -q
```

## Result

PASS (cloud agent, no FieldWorks).

## run_mode

N/A (offline only).
