# Issue #341 -- offline verification

**Command:**

```
python3 -m pytest tests/test_issue341_possibility_create_pattern.py -m "not requires_live_project" -q
```

**Result:** 3 passed (2026-09-24, cloud agent worktree `fix/341-cm-possibility-create`).

**run_mode:** mock (no LCM; AST-only ratchets per ruling).

**PASS:** offline gate for doc/wrapper surface.
