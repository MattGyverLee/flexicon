# 4.13.0 release gate -- live verification evidence

**Date:** 2026-10-09
**Branch:** `main` @ `511c67e` ("Merge pull request #632 from MattGyverLee/fix/630-631-exception-features")
**Host:** Windows 11, FieldWorks 9 (same machine as the 4.12.0 gate)

## Commands

```
python -m pytest -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest -m requires_live_project -q -p no:warnings
```

## Results

| Run | Result | `run_mode` |
|---|---|---|
| Offline, `511c67e` | **3719 passed**, 1174 deselected (20.7s) | n/a |
| Live, `511c67e` | **1132 passed**, 40 skipped, 2 xfailed, 5 subtests passed (10m48s) | **`live`** |

Both runs were made on the release head itself, not taken from an earlier
commit message. `tests/live_status.json` showed `"run_mode": "live"` after
the live run, and `tests/test_results.json` recorded 1174 tests.

The live run regenerated six raw evidence files under `specs/` (probe dumps
from earlier features). Those rewrites were discarded and are not part of
the release commit.

## Release commit

The release commit bumps `flexicon/__init__.py` to 4.13.0 and edits
`CHANGELOG.md`, `history.md`, `RELEASE_NOTES_v4.13.0.md` and this file. It
touches no code path, so the gates on `511c67e` stand.
