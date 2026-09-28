# Issue #377 item 2 -- offline evidence

**Date:** 2026-09-24  
**Branch:** fix/377-scrdraft-type  
**run_mode:** mock (cloud agent; no FieldWorks / pythonnet)

## Command

```
python3 -m pytest tests/operations/test_issue377_scrdraft_type_offline.py -m "not requires_live_project" -q
```

## Result

**PASS** -- 3 passed (2026-09-24, cloud agent, `run_mode`: mock).

## Live

**FAIL: unverified** -- write path touches `IScrDraftFactory.Create` and
`IScrDraft.Type`; live round-trip not run on this host.
