# Issue #812 -- lex-lead ruling

**Date:** 2026-10-26  
**HEAD:** fix/812-allomorph-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR (#640 has PR #641; cursor-filed HVO sweep #772-#810 each have open PRs).
- Selected **P2 #812** (new): `AllomorphOperations.Delete` bare-proxy `AlternateFormsOS.Remove` and `LexemeFormOA == allomorph` identity -- sibling gap after #810 Example Delete / #646 Allomorph Duplicate HVO family.

## RULING (binding)

`AllomorphOperations.Delete` must resolve lexeme-vs-alternate role and `AlternateFormsOS` membership by **HVO** before mutating, matching #810 Example Delete / #646 Duplicate insert_after.

**Fix for this PR:**

1. Compare `LexemeFormOA.Hvo` to the target allomorph HVO to detect lexeme-form deletion (not Python identity on proxies).
2. For alternates, scan `AlternateFormsOS` for a slot whose `Hvo` matches; `Remove` the matched member; raise `FP_ParameterError` if none found.
3. Offline source ratchet + live gate module under `tests/operations/test_issue812_*`.

**Out of scope:** Duplicate (#646 / PR #647); orphan cleanup (#231); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

**Next sibling (file after merge):** Other Delete paths still using bare `.Remove(handle)` on owning sequences without an open issue (e.g. `LexReferenceOperations.Delete` on `MembersOC`).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue812_allomorph_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue812_allomorph_delete_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
