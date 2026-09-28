# Offline verification -- issue #506 (cron)

**Command:**

```bash
python3 -m pytest tests/operations/test_issue506_findbyhvo_resolver_offline.py -m "not requires_live_project" -q --noconftest
```

**Environment:** Cursor cloud agent pod (Linux).

**Result:** **PASS** (3/3).
