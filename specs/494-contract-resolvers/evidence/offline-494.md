# Issue #494 -- offline evidence

**Command:**

```
python -m pytest tests/operations/test_issue494_contract_resolvers_offline.py -m "not requires_live_project" -q
```

**run_mode:** N/A (docstring-only; no LCM)

**Result:** PASS (4/4 on Cursor cloud Linux runner, 2026-09-25)

**Pre-state:** Five contract-only helpers lacked explicit docstring disclosure that HVO paths return uncast ``project.Object`` views.

**Post-state:** Docstrings updated in ``BaseOperations``, ``PhonologicalRuleOperations`` (two helpers), ``ScrNoteOperations``, ``SegmentOperations``; offline ratchet locks the disclosure text.
