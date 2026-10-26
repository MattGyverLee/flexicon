# Issue #808 -- lex-lead ruling

**Date:** 2026-10-26  
**HEAD:** fix/808-pronunciation-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR (all cursor-filed HVO sweep issues #640-#806 have matching open PRs).
- Selected **P2 #808** (new): `PronunciationOperations.Delete` bare-proxy `PronunciationsOS.Remove` -- sibling gap named in #806 lex-lead ruling (next after Etymology Delete).

## RULING (binding)

`PronunciationOperations.Delete` must resolve the owning-sequence member by **HVO** before calling `PronunciationsOS.Remove`, matching #806 Etymology Delete / #644 Duplicate insert_after.

**Fix for this PR:**

1. After casting the owner to `ILexEntry`, scan `entry.PronunciationsOS` for a slot whose `Hvo` matches the resolved pronunciation.
2. `Remove` the matched member; raise `FP_ParameterError` if none found.
3. Offline source ratchet + live gate module under `tests/operations/test_issue808_*`.

**Out of scope:** `Reorder` (#700 filed separately); `MoveMediaFile` (#686); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

**Next sibling (filed after merge):** `ExampleOperations.Delete` bare-proxy `ExamplesOS.Remove` (same HVO sweep family).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue808_pronunciation_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue808_pronunciation_delete_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
