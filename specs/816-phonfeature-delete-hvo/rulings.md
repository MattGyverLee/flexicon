# Issue #816 -- lex-lead ruling

**Date:** 2026-10-26  
**HEAD:** fix/816-phonfeature-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR (#640 has PR #641; cursor-filed HVO sweep each have open PRs).
- Selected **P2 #816** (new): `PhonFeatureOperations.Delete` / `DeleteValue` bare-proxy `FeaturesOC` / `ValuesOC` `.Remove` -- sibling gap named in #814 lex-lead ruling (remaining Delete paths using bare `.Remove(handle)` without an open issue).

## RULING (binding)

`PhonFeatureOperations.Delete` and `DeleteValue` must resolve collection membership by **HVO** before mutating, matching #808 Pronunciation Delete / #814 LexReference Delete.

**Fix for this PR:**

1. Scan `FeaturesOC` / `ValuesOC` for a slot whose `Hvo` matches the resolved object; `Remove` the matched member.
2. Raise `FP_ParameterError` if no member found.
3. Offline source ratchet + live gate module under `tests/operations/test_issue816_*`.

**Out of scope:** Inflection feature system parity; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

**Next sibling (file after merge):** `DataNotebookOperations.Delete` `RecordsOC` / `SubRecordsOS` bare `.Remove` (no open issue at filing time).

## Verification plan

- Offline: `python3 -m pytest tests/operations/test_issue816_phonfeature_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue816_phonfeature_delete_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
