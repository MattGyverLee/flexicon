# Live evidence — issue #289

**Command (not run on this agent):**

```text
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/test_headless_threaded_progress.py tests/operations/test_target_live_smoke.py -m requires_live_project -q
```

**run_mode:** unavailable (Linux cloud agent — no FieldWorks / SIL.LCModel)

**Result:** FAIL: unverified

**Pre-state / post-state:** N/A — open-path handle-count measurement from #289
requires Windows `GetGuiResources` or equivalent against Target/Sena 3.

**Offline gate (this run):**

```text
python3 -m pytest tests/test_headless_threaded_progress.py -m "not requires_live_project" -q
```
