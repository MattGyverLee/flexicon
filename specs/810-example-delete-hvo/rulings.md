# Issue #810 -- lex-lead ruling

**Date:** 2026-10-26  
**HEAD:** fix/810-example-delete-hvo from origin/main

## Triage (cron)

- No open **P0** or **P1** bugs without an open PR (all cursor-filed HVO sweep issues #640-#808 have matching open PRs; #640 has PR #641).
- Selected **P2 #810** (new): `ExampleOperations.Delete` bare-proxy `ExamplesOS.Remove` -- next sibling named in #808 lex-lead ruling out-of-scope note.

## RULING (binding)

`ExampleOperations.Delete` must resolve the owning-sequence member by **HVO** before calling `ExamplesOS.Remove`, matching #808 Pronunciation Delete / #804 LexSense Delete / #552 Example Duplicate insert_after.

**Fix for this PR:**

1. After `_GetTypedOwner`, scan `sense.ExamplesOS` for a slot whose `Hvo` matches the resolved example.
2. `Remove` the matched member; raise `FP_ParameterError` if none found (including missing owner).
3. Offline source ratchet + live gate module under `tests/operations/test_issue810_*`.

**Out of scope:** `Reorder` (#694); `MoveMediaFile` (#684); live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

**Next sibling (file after merge):** `AllomorphOperations.Delete` bare-proxy `AlternateFormsOS.Remove` / lexeme-form path.

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue810_example_delete_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue810_example_delete_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
