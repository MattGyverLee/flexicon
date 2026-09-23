# Offline evidence -- issue #340

**Command:**

```
python3 -m pytest tests/operations/test_issue340_natural_class_kind_discoverability.py -m "not requires_live_project" -q
```

**run_mode:** N/A (no LCM session; offline fakes only)

**Result:** PASS (2 static source-lock tests; 3 behavioural tests skipped without SIL.LCModel) on cloud agent pod.

**Live verification:** FAIL: unverified -- no SIL.LCModel / FieldWorks on Linux cloud pod.
Write-path guard change is behaviour-preserving for segment vs feature discrimination;
live re-run on Windows should use existing `tests/operations/test_natural_classes.py`
GetType tests plus one AddPhoneme-on-feature-based assertion.
