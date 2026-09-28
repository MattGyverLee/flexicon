# Issue #293 -- offline verification evidence

**Date:** 2026-09-24  
**Branch:** `fix/293-gramcat-stray-docs`  
**run_mode:** docs-only (no LCM)

## Command

```bash
python3 -m pytest tests/test_issue293_gramcat_stray_docs_ratchet.py \
  -m "not requires_live_project" -q
```

## Result

**PASS:** 1 passed (cloud agent, 2026-09-24).

## Pre/post state

- **Pre:** Migration guide had a short stray-type paragraph without the full
  hand-cleanup checklist from #293.
- **Post:** Expanded recipe under GramCat breaking change; ratchet test pins
  required phrases.
