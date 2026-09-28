# Issue #364 -- offline evidence

## Commands

```
python -m pytest tests/operations/test_overlay_operations.py -m "not requires_live_project" -q
python -m pytest tests/test_pattern_g_owner_of_class.py::TestOverlayGetChart -m "not requires_live_project" -q
```

## Result (cloud agent, Linux)

See pytest output captured in PR verification. No LCM write path touched;
live overlay tests unchanged.

## Behaviour

| Method | Before | After |
|--------|--------|-------|
| `IsVisible` | Checked phantom `IsVisibleRA`, then `Hidden` | `Hidden` only if present; else `True` |
| `SetVisible` | Wrote phantom `IsVisibleRA` or `Hidden` | No-op + debug log when no `Hidden` |
| `GetChart` | Phantom `ChartRA`/`Chart` fast paths | `OwnerOfClass` walk only |

**Pass/fail:** PASS -- 4 passed (overlay offline ratchets), 3 passed (Pattern G GetChart).
