# Issue #515 live evidence (cron)

**Command:**

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue515_get_owning_text_live.py -m requires_live_project -q
```

**run_mode:** mock (FLEx/.NET runtime unavailable on cloud agent)

**Result:** FAIL: unverified — `pytest.UsageError` from `tests/flex_plugin.py` when
`FLEXLIBS_REQUIRE_LIVE=1` and FLEx init fails (no mono/pythonnet runtime).

**Blocker:** Live LCM verification requires FieldWorks on Windows; not available in this environment.

**Expected on machine with Target sandbox:** create `TEST_515_` text + chart, assert
`GetOwningText(chart.Hvo)` and `GetOwningText(project.Object(hvo))` return the owning text HVO.
