# Issues #302, #328, #261 -- lex-lead ruling

**Date:** 2026-09-23  
**Branch:** fix/302-328-datanotebook-close from origin/main

## Context

Live verification during the #352 / lcm-member-truth-sweep campaign proved
three independent defects in `DataNotebookOperations`. Production fixes for
Title/Text/RecordsOC/GetObject landed on `main` under issue #352; GitHub
issues #302, #328, and #261 remained open without dedicated ratchets.

## RULING (binding)

**Scope:** Pin the remediated behaviour and close the three tracker issues.
No further API redesign.

### #302 -- repository vs notebook ownership

1. Top-level record create/delete/duplicate must use
   `self.project.lp.ResearchNotebookOA.RecordsOC`, not
   `IRnResearchNbkRepository.RecordsOC` (repository has no such member).
2. `__GetRecordObject` must resolve HVOs via `self.project.Object(hvo)`
   (ServiceLocator path), never `self.project.project.GetObject`.

### #328 -- bare `ITsString` Title and no `Text` member

1. Writes to title assign `record.Title = self._MakeTsString(...)` (no
   `set_String` on Title).
2. Body content uses `DescriptionOA` via `_SetRecordContent` /
   `_ReadRecordContent`; do not reference `record.Text`.
3. Duplicate copies title by assignment and content via `_CopyRecordContent`
   (no `CopyAlternatives` on phantom `Text`).

### #261

Same resolver fix as #302 item 2; closed together with #302.

**Out of scope:** DataNotebook RA getters (#329), sync payload redesign.

## Verification plan

- Offline: source ratchets in
  `tests/operations/test_issue302_328_datanotebook_offline.py`.
- Live: existing `tests/operations/test_352_datanotebook_live.py` (Target
  sandbox); re-run when FieldWorks is available.
