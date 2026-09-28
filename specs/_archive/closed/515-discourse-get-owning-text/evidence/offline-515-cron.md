# Issue #515 offline evidence (cron)

**Command:**

```
python3 -m pytest -m "not requires_live_project" tests/operations/test_issue515_get_owning_text_offline.py -q
```

**Result:** PASS (2/2)

**run_mode:** mock (no LCM on cloud agent; offline ratchet only)

**Pre-state:** `GetOwningText` used `chart_obj.Owner` / `owner.Owner` + bare `IText()`.

**Post-state (source):** `_GetTypedOwner(chart_obj)` then `__GetTextObject(st_text.Owner)`.
