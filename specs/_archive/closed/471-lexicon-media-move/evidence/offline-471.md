# Issue #471 -- offline evidence

**Command:**

```
python -m pytest tests/operations/test_issue471_lexicon_media_move_offline.py -m "not requires_live_project" -q
```

**Result:** 3 passed in 0.07s (cloud agent, 2026-09-25).

**Live:** FAIL: unverified (no FieldWorks / live LCM on cloud agent).
