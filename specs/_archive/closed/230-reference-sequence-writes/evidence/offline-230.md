# Issue #230 -- offline verification (DependentClausesRS writes)

## Command

```
python3 -m pytest tests/operations/test_issue230_dependent_clauses_rs.py -m "not requires_live_project" -q
```

## Result

**Not executed on cloud pod** (2026-09-24): pythonnet could not load a .NET
runtime (`RuntimeError: Could not find libmono`). Re-run on Windows CI or a
FieldWorks dev machine.

## Notes

Live write-path verification on `target_sandbox` not performed in this
environment (**FAIL: unverified** for LCM read-back).
