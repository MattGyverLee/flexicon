# Issue #309 -- live verification evidence

## Command (required live run)

```bash
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_overlay_operations.py::TestOverlayCreateLive -m requires_live_project -q
```

## Environment (2026-09-23 cloud agent)

FieldWorks / SIL.LCModel is **not installed** on this Linux pod (`python3`
available; no FLEx init). Live run was **not executed** here.

## Offline gate (executed)

```bash
python3 -m pytest tests/operations/test_overlay_operations.py -m "not requires_live_project" -q
```

**2026-09-23 automation run:** 3 passed, 4 deselected (cloud Linux pod, no libmono).

## Result

**FAIL: unverified (live)** -- write-path change requires LCM read-back on a
Windows FieldWorks host. Offline source ratchets and mock collection pass.

## Expected live read-back (for human re-run)

1. Pre: `project.Overlays.Find("TEST_309_overlay_create")` is `None`.
2. Post-create: `Create(...)` returns overlay; `Find` and `GetName(hvo)` match
   `TEST_309_overlay_create`.
3. Post-delete: `Find` is `None` again.
