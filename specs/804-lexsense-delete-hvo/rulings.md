# Issue #804 -- lex-lead ruling

**Date:** 2026-10-26  
**HEAD:** fix/804-lexsense-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR (all cursor-filed HVO sweep issues #640-#802 have matching open PRs).
- Selected **P2 #804** (new): `LexSenseOperations.Delete` bare-proxy `SensesOS.Remove` -- sibling gap next to #550 Duplicate HVO indexing in the same method.

## RULING (binding)

`LexSenseOperations.Delete` must resolve the owning-sequence member by **HVO** before calling `SensesOS.Remove`, matching #782 WfiAnalysis Delete / #798 Phoneme Delete / #550 Duplicate insert_after.

**Fix for this PR:**

1. After `_GetTypedOwner`, scan `owner.SensesOS` for a slot whose `Hvo` matches the resolved sense.
2. `Remove` the matched member; raise `FP_ParameterError` if none found.
3. Offline source ratchet + live gate module under `tests/operations/test_issue804_*`.

**Out of scope:** Subsense parent typing changes; `Reorder` / RC mutators (separate filed issues); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue804_lexsense_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue804_lexsense_delete_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
