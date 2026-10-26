# Issue #806 -- lex-lead ruling

**Date:** 2026-10-26  
**HEAD:** fix/806-etymology-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR (all cursor-filed HVO sweep issues #640-#804 have matching open PRs).
- Selected **P2 #806** (new): `EtymologyOperations.Delete` bare-proxy `EtymologyOS.Remove` -- sibling gap next to #696 Reorder HVO indexing and #642 Duplicate insert_after in the same module.

## RULING (binding)

`EtymologyOperations.Delete` must resolve the owning-sequence member by **HVO** before calling `EtymologyOS.Remove`, matching #804 LexSense Delete / #642 Duplicate insert_after.

**Fix for this PR:**

1. After `_GetTypedOwner`, scan `owner.EtymologyOS` for a slot whose `Hvo` matches the resolved etymology.
2. `Remove` the matched member; raise `FP_ParameterError` if none found.
3. Offline source ratchet + live gate module under `tests/operations/test_issue806_*`.

**Out of scope:** `Reorder` (#696 filed separately); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

**Next sibling (filed after merge):** `PronunciationOperations.Delete` bare-proxy `PronunciationsOS.Remove` (same HVO sweep family).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue806_etymology_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue806_etymology_delete_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
