# Issue #833 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/833-check-getlist from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Selected **P2 #833**: `CheckOperations._GetCheckList()` hardcoded `None` stub; enumeration and delete no-op; `_GetOrCreateCheckList()` fabricates orphan lists.

Untrusted open issues ignored per automation policy.

## RULING (binding)

Consistency-check types live on `ICmPossibilityList` objects owned by `ILangProject.CheckListsOC` (LCM contract snapshot; `docs/FUNCTION_REFERENCE.md`'s `ChecksOA` name is not present on `ILangProject`).

**Fix for this PR:**

1. Implement `_GetCheckList()` to return the first list in `self.project.lp.CheckListsOC` when present, cast with `ICmPossibilityList`.
2. Change `_GetOrCreateCheckList()` to reuse `_GetCheckList()`; when empty, create a list via `GetFactory(ICmPossibilityListFactory)` and **`CheckListsOC.Add(new_list)`** so checks are project-owned (issue #833).
3. Add public `GetCheckList()` delegating to `_GetCheckList()`.
4. Offline source ratchet + live gate under `tests/operations/test_issue833_*`.

**Out of scope:** `GetAllCheckTypes` duplicate nested yield; renaming `docs/FUNCTION_REFERENCE.md` ChecksOA wording; live proof in cloud (`FAIL: unverified` when FieldWorks absent).

**Next sibling (file after merge):** #834 NoteOperations Duplicate `insert_after` on unordered `AnnotationsOC` (open, no PR).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue833_check_getlist_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue833_check_getlist_live.py -m requires_live_project -q` on `target_sandbox`.
