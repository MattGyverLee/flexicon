# Issue #230 close-out -- offline evidence

**Date:** 2026-09-24  
**Branch:** fix/230-reference-sequence-close-out

## Commands

```
python -m pytest tests/operations/test_issue230_dependent_clauses_rs.py \
  tests/operations/test_issue230_semantic_domain_occurrences_ratchet.py \
  -m "not requires_live_project" -q
```

## Result

Cloud agent: pending run (see commit CI / local output below).

## Live

**FAIL: unverified** -- no FieldWorks / pythonnet on Linux pod.
