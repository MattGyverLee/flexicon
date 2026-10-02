# 4.12.0 release gate -- live verification evidence

**Date:** 2026-10-02
**Branch:** `main` @ `77aa8aa` ("test: restore green live suite for release")
**Host:** Windows 11, FieldWorks 9 (same machine as the 4.11.0 gate)

## Commands

```
python -m pytest -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest -m requires_live_project -q
```

## Results

| Run | Result | `run_mode` |
|---|---|---|
| Offline, `77aa8aa` | **3626 passed** | n/a |
| Live, `77aa8aa` | **1099 passed**, 41 skipped, 2 xfailed | **`live`** |

`tests/live_status.json` shows `"run_mode": "live"` for the live run
(checked at the cut). Numbers are taken from the verification paragraph of
`77aa8aa`'s commit message; the suites were not rerun for the release commit,
which changes only version metadata and documentation.

## Test-side defects fixed before the gate (`77aa8aa`)

All three were red only in the live run and were test defects, not library
defects; no library code changed in that commit.

1. Reversal index fixtures created a second index for the en writing system;
   they now reuse the existing one via `FindByWritingSystem` (the
   one-index-per-WS guard made the unconditional `Create` fail).
2. `test_wfi_analysis` saved the class-level closure instead of the
   `OperationsMethod` descriptor from the class `__dict__`, permanently
   replacing the descriptor and breaking every later `GetHumanAgents` call in
   the session.
3. Two legacy sync modules now tolerate `FP_ConflictingSaveError` at
   teardown: back-to-back write sessions on Sena 3 race LCM's asynchronous
   backend commit. The tests are self-cleaning, so discarding matches the
   pre-#285 silent-discard behaviour.

## Release commit

The release commit itself bumps `flexicon/__init__.py` to 4.12.0 and edits
`CHANGELOG.md`, `history.md`, `RELEASE_NOTES_v4.12.0.md` and this file. It
touches no code path, so the gates on `77aa8aa` stand.
