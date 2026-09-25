# Issue #465 live verification

## Command

```bash
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue465_segment_resolver_cast_live.py -m requires_live_project -q
```

## Result

**FAIL: unverified** -- cloud agent pod has no FieldWorks / pythonnet LCM runtime.

## Offline gate (executed)

```bash
python -m pytest tests/operations/test_issue465_segment_resolver_cast_offline.py -m "not requires_live_project" -q
```

See commit-time CI / cron log for pass line.
