# Issue #814 -- lex-lead ruling

**Date:** 2026-10-26  
**HEAD:** fix/814-lexref-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR (#640 has PR #641; cursor-filed HVO sweep #772-#812 each have open PRs).
- Selected **P2 #814** (new): `LexReferenceOperations.Delete` bare-proxy `MembersOC.Remove` -- sibling gap named in #812 lex-lead ruling (`LexReferenceOperations.Delete` on `MembersOC`).

## RULING (binding)

`LexReferenceOperations.Delete` must resolve `MembersOC` membership by **HVO** before mutating, matching #808 Pronunciation Delete / #812 Allomorph Delete.

**Fix for this PR:**

1. Scan `owner.MembersOC` for a slot whose `Hvo` matches the resolved reference; `Remove` the matched member.
2. Raise `FP_ParameterError` if no member found.
3. Offline source ratchet + live gate module under `tests/operations/test_issue814_*`.

**Out of scope:** `DeleteType` (#766 / PR #767); `RemoveTarget` (#742 / PR #743); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

**Next sibling (file after merge):** Other Delete paths still using bare `.Remove(handle)` on owning sequences without an open issue (scan remaining Operations `Delete` methods).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue814_lexref_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue814_lexref_delete_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
