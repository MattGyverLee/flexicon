# Issue #339 -- offline verification

## Command

```
python3 -m pytest tests/test_issue339_public_import_surface.py -m "not requires_live_project" -q
```

## Environment

Cloud agent, Linux, 2026-09-23. No FieldWorks / `clr`.

## run_mode

Not applicable (AST-only tests; no `tests/live_status.json` write).

## Pre-state

Issue #339: runtime logs reported `ImportError` for `MSAOperations` and
`PhonFeatureOperations` when callers used `from flexicon import ...`. #257/#311
already added the exports; this task pins them against regression.

## Post-state

`flexicon/__init__.py` and `flexicon/__init__.pyi` both list
`MSAOperations` and `PhonFeatureOperations` in `__all__` with eager
ImportFrom bindings (verified by ratchet tests).

## Result

PASS (see pytest output in CI / local run).

## Live

FAIL: unverified — no LCM write path; import surface only.
