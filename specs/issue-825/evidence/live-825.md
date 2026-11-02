# Live verification: issue #825 (FLEXICON_FW_DIR override)

Command (PowerShell equivalent: set $env:FLEXICON_FW_DIR and $env:FLEXLIBS_REQUIRE_LIVE):

    FLEXICON_FW_DIR="C:\Program Files\SIL\FieldWorks 9" FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue825_fw_dir_override_live.py -m requires_live_project -q

- run_mode (tests/live_status.json): "live"
- Fixture: target_sandbox (tempdir copy; no in-place Target)
- Result: 1 passed (3 consecutive runs; the very first run errored once in fixture setup, not reproducible)
- Checks: FLExGlobals.FWCodeDir == FLEXICON_FW_DIR; sandbox opens write-enabled with a live LCM cache; LexEntry.GetAll() queries.
- Invalid override (`FLEXICON_FW_DIR=C:\nonexistent`, `import flexicon`) raises: "FLEXICON_FW_DIR is set to ... not an existing directory ..."
- Offline: tests/operations/test_issue825_fw_dir_override_offline.py, 6 passed.
- Note: the override test does not write data; it verifies init/open under the override.
