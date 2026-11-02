# Issue #833 live evidence

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue833_check_getlist_live.py -m requires_live_project -q
```

**run_mode:** live gate not reached (FLEx init failed before project open)

**Pre-state / post-state:** N/A — no LCM read-back in this environment.

**Result:** FAIL: unverified — cloud agent has no .NET/FieldWorks runtime (`PYTHONNET` / mono unavailable).

**Expected on Windows with FieldWorks:** `GetCheckList()` non-None after `CreateCheckType`; `GetAllCheckTypes` includes created HVO; `DeleteCheckType` removes it; owner HVO matches check list.
