# Issue #377 sena3_sandbox fail-loud slice -- offline evidence

**Date:** 2026-09-24  
**Branch:** fix/377-sena3-require-live-parity  
**run_mode:** mock (no FieldWorks on host; test-infrastructure change only)

## Commands

```
python3 -m pytest tests/test_issue377_sena3_fixture_fail_loud.py -m "not requires_live_project" -q
python3 -m pytest -m "not requires_live_project" -q
```

## Result

- Targeted ratchet: **1 passed**
- Full offline gate: see CI / local full run output on PR

## Change summary

`sena3_sandbox` OpenProject failure now calls `_unavailable()` instead of
bare `pytest.skip()`, matching `target_sandbox` and honoring
`FLEXLIBS_REQUIRE_LIVE=1`.
