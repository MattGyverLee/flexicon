# Issue #798 live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue798_phoneme_delete_hvo_live.py -m requires_live_project -q
```

**run_mode:** FAIL: unverified (cloud agent has no pythonnet / FieldWorks LCM)

**Pre-state / post-state:** not collected — live suite not executed in this environment.

**Result:** Live gate module present; verification deferred to Windows CI or developer workstation with Target sandbox.
