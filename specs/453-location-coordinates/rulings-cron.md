# Issue #453 -- lex-lead ruling (cron)

**Date:** 2026-09-24  
**HEAD:** `fix/453-location-coordinates` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#453** (filed this run; HANDOFF finding)
- Did not select P3 **#284** (re-triage tracking, not a defect report)

## RULING (binding)

`CmLocation` adds only `Alias` beyond `CmPossibility` in `MasterLCModel.xml`;
there is no coordinate or elevation storage in LCM. The current
`DateOfEvent` / `GenDateVal*` path is dead code (already noted unreachable
at `LocationOperations.py:670`).

1. **`SetCoordinates`** -- raise `FP_ParameterError` before opening a
   transaction, with a message that cites the missing LCM members. Do not
   report success when nothing is persisted.
2. **`GetCoordinates`** -- remove the phantom `DateOfEvent` gate; return
   `None` (honest read): no coordinates are stored.
3. **`SetElevation`** -- same fail-loud shape if `Elevation` is absent from
   the LCM model (confirmed absent in contract baseline).
4. **`GetElevation`** -- drop the `hasattr` gate; return `None`.
5. **`Duplicate` / `_DuplicateSublocationInto`** -- remove `DateOfEvent` copy
   blocks and coordinate/elevation copy calls that depend on the broken
   getters/setters.
6. **Docstrings** -- stop claiming GenDate coordinate storage.

**Out of scope:** inventing a Description/Alias encoding for geo data, custom
field integration, live verification on this cloud host (no FieldWorks).

## Verification plan

- Offline:
  `python3 -m pytest tests/operations/test_issue453_location_coordinates_offline.py -q`
- Live (FieldWorks):
  `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue453_location_coordinates_live.py -m requires_live_project -q`
- Evidence: `specs/453-location-coordinates/evidence/offline-cron.md`
