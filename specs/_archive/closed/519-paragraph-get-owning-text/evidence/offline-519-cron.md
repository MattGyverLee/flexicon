# Offline evidence -- issue #519 (cron)

**Command:**

```
python3 -m pytest tests/operations/test_issue519_paragraph_get_owning_text_offline.py tests/operations/test_issue517_paragraph_duplicate_parent_offline.py -m "not requires_live_project" -q
```

**Result:** 5 passed in 0.10s

**run_mode:** N/A (offline)

**Pre/post LCM:** N/A

**Pass/fail:** PASS
