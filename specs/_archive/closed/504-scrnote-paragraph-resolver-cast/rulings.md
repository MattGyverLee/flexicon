# Issue #504 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #504 (P2) -- `ScrNoteOperations.__ResolveParagraph` HVO guard false negative  
**Parent triage:** #275 / #269 resolver family; deferred from #493 / #494 scope

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** at pick time (#492/#500/#502 each had open PRs)
- **Filed and selected #504** this run: `__ResolveParagraph` still uses bare
  `isinstance` on `project.Object(hvo)` while sibling `__ResolveBook` in the
  same module already casts (#493)

## RULING (binding)

Cast `__ResolveParagraph` through `cast_to_concrete` on every return path.
On the HVO branch, keep the **union** of `isinstance(obj, IScrTxtPara)` and
`ClassName == "ScrTxtPara"` (match `__ResolveBook` in this file and
`ScrTxtParaOperations.__ResolveSection` from #493). Do not return uncast
objects from the HVO branch.

## Verification plan

- Offline: `tests/operations/test_issue504_scrnote_paragraph_resolver_cast_offline.py`
- Live: `tests/operations/test_issue504_scrnote_paragraph_resolver_cast_live.py`
  (`sena3_sandbox`; `ScrNotes.Create(book_hvo, para_hvo, ...)` with genuine
  ints only; delete created note in `finally`)
