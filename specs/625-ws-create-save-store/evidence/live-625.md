# Live evidence: #625 WritingSystems.Create/Ensure save the store

Command:
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue625_ws_create_save_store_live.py -m requires_live_project -q
```
run_mode (tests/live_status.json): live
Project: target_sandbox (tempdir copy of Target .fwbackup).

Pre-state (read from disk): `WritingSystemStore/qaa-x-t625a.ldml` and
`qaa-x-t625b.ldml` absent; no idchangelog.xml entries for either tag.

Action, project NOT closed, no explicit store flush:
- `Ensure("qaa-x-t625a", "TEST_t625a")` -> created True
- `Create("qaa-x-t625b", "TEST_t625b", is_vernacular=False)`

Post-state (read from disk / re-queried from LCM):
- both `.ldml` files exist in WritingSystemStore
- idchangelog.xml has exactly one `<Add>` per tag; for t625a
  Producer="flexicon", ProducerVersion=flexicon.version
- `Exists("qaa-x-t625a")` True; `qaa-x-t625b` in `lp.CurAnalysisWss`
- second `Ensure` on the already-active tag: created False, change-log entries
  unchanged (no-op)

Regression: tests/operations/test_issue607_608_ws_store_live.py also re-run (Delete
now goes through the shared save helper).

PASS: 3 passed (625 live); see regression line in PR.
