# Issue #265 -- MakeFeatStruc name operands (offline evidence)

## Ruling

See `specs/265-makefeatstruc-name-operands/rulings.md`.

## Command

```
python3 -m pytest tests/operations/test_issue265_makefeatstruc_names_offline.py -m "not requires_live_project" -q
```

## Result (2026-09-24, cloud worktree)

**Not run** -- collection fails without `pythonnet` / SIL.LCModel (`ModuleNotFoundError: clr`).

## Live LCM

**FAIL: unverified** -- no FieldWorks / SIL.LCModel on Linux cloud pod.
