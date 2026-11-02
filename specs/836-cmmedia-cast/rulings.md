# Issue #836 -- lex-lead ruling

**Date:** 2026-11-02  
**Issue:** #836 (P2) -- `cast_to_concrete` returns bare `ICmObject` for `CmMedia`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **#836** (this run; #833 has PR #837; #834 deferred)

## RULING (binding)

1. Register `CmMedia` -> `ICmMedia` in `lcm_casting._interface_cache` via the
   existing HVO-resolver import block (same pattern as `LexPronunciation`, issue
   #455-#508 family).
2. Do not change `PronunciationOperations` media write paths in this PR (#828 is
   already merged).
3. Update `tests/contract/snapshots/expected_contract.json` if the static
   extractor reports a new `ICmMedia` import on `lcm_casting.py`.
4. Tag the registry entry with `issue #836` in comments.

**Out of scope:** Full-table audit for other missing ClassNames (issue body
suggests it; file a follow-up if needed). #834 NoteOperations Duplicate
`insert_after` warning path.

## Verification plan

- Offline: `tests/operations/test_issue836_cmmedia_cast_offline.py` +
  `pytest tests/contract/test_lcm_contract.py -m "not requires_liblcm" -q`
- Live: `tests/operations/test_issue836_cmmedia_cast_live.py` (read-back via
  `Object(hvo)` + `cast_to_concrete`)
- Evidence: `specs/836-cmmedia-cast/evidence/live-836-cmmedia-cast.md`
- Cloud agent live: **FAIL: unverified** when `clr`/FieldWorks unavailable
