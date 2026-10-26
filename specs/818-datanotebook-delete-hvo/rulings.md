# Issue #818 -- lex-lead ruling

**Date:** 2026-10-26  
**HEAD:** fix/818-datanotebook-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR (#640 has PR #641; cursor-filed HVO sweep issues each have open PRs).
- Selected **P2 #818** (new): `DataNotebookOperations.Delete` bare-proxy `RecordsOC` / `SubRecordsOS` `.Remove` -- sibling gap named in #816 lex-lead ruling.

## RULING (binding)

`DataNotebookOperations.Delete` must resolve collection membership by **HVO** before mutating, matching #680 Note Delete / #816 PhonFeature Delete.

**Fix for this PR:**

1. After `_GetTypedOwner`, scan `SubRecordsOS` or top-level `RecordsOC` for a slot whose `Hvo` matches the resolved record; `Remove` the matched member.
2. Raise `FP_ParameterError` if no member found.
3. Offline source ratchet + live gate module under `tests/operations/test_issue818_*`.

**Out of scope:** ResearchersRC/LocationsRC/SourcesRC `in` checks (#708–#712 open PRs); Duplicate `IndexOf` (#650 open PR); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

**Next sibling (file after merge):** `InflectionFeatureOperations.FeatureDelete` bare `MsFeatureSystemOA.FeaturesOC.Remove` (no open issue at filing time).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue818_datanotebook_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue818_datanotebook_delete_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
