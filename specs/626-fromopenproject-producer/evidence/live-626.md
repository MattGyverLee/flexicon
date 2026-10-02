# Live evidence: #626 FromOpenProject stamps Producer="flexicon"

Command (PowerShell, worktree root):

    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest tests/operations/test_issue607_608_ws_store_live.py tests/operations/test_issue626_fromopenproject_producer_live.py -m requires_live_project -q

`tests/live_status.json` run_mode: `live`

Project: `target_sandbox` (tempdir copy of the Target .fwbackup; the real
Target is never touched).

## Pre-state (read back from the LCM / disk)

- Host cache's writing-system change-log mapper type, after restoring the
  stock mapper to model a host that never stamped:
  `SIL.WritingSystems.*` (stock libpalaso mapper, not
  `Flexicon.Interop.ProducerStampingMapper`).
- `idchangelog.xml` has no entry for `qaa-x-test626`.

## Action

`FLExProject.FromOpenProject(<duck-typed write-enabled donor over the cache>)`,
then `view.WritingSystems.Ensure("qaa-x-test626", ...)` (created=True), then
`WritingSystemManager.Save()`.

## Post-state (re-read)

- Mapper type on the host cache: `Flexicon.Interop.ProducerStampingMapper`.
- `idchangelog.xml` read from disk: exactly one entry for
  `qaa-x-test626`, element `Add`, `Producer="flexicon"`,
  `ProducerVersion=<flexicon.version>`.
- A read-only donor leaves the mapper as the stock `SIL.WritingSystems.*`.

## Result

PASS: 8 passed (2 new #626 live tests + 6 existing #607/#608 live tests, which
confirm the OpenProject path still stamps). Offline: 3636 passed, 1144
deselected.
