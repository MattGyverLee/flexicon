# Issue #502 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #502 (P2) -- WfiGlossOperations analysis HVO resolver uncast / isinstance guard  
**Parent triage:** #275 TextsWords gap (sibling to #500)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#500** has open PR #501; **filed and selected #502** this run
- Open **P3** bugs without an open PR: **#494** has open PR #498

## RULING (binding)

Add ``__ResolveAnalysis`` and route every analysis HVO entry site through
``cast_to_concrete`` on the HVO path. Match #500 / #275 / #269: guard on the
**union** of ``ClassName == "WfiAnalysis"`` and ``isinstance(..., IWfiAnalysis)``.
Do not leave inline ``isinstance``-only HVO guards on analysis parameters.

## Verification plan

- Offline: `tests/operations/test_issue502_wfigloss_analysis_resolver_cast_offline.py`
- Live: `target_sandbox` gate calling `GetCount(analysis.Hvo)` and
  `GetAll(analysis.Hvo)` with genuine HVO ints only (`requires_live_project`).
