# Live evidence: #625 WritingSystems.Create/Ensure save the store

Commands:
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue625_ws_create_save_store_live.py -m requires_live_project -q
python -m pytest tests/operations/test_issue607_608_ws_store_live.py -m requires_live_project -q
```
run_mode (tests/live_status.json): live (after each run)
Projects: target_sandbox / target_sandbox_undoable (tempdir copies of Target).

## Create / Ensure (project NOT closed, no explicit flush)
Pre-state (disk): `qaa-x-t625a`, `-b`, `-c`, `-d`, `-e`, `-f` `.ldml` absent; no
idchangelog.xml entries for them.
Post-state (disk + LCM re-query):
- `Ensure("qaa-x-t625a")` -> created True; `.ldml` exists; exactly one `<Add>`
  with Producer="flexicon", ProducerVersion=flexicon.version; Exists True
- `Create("qaa-x-t625b", is_vernacular=False)` -> `.ldml` exists, one `<Add>`,
  tag in `lp.CurAnalysisWss`
- second `Ensure` on the active tag -> created False, change log unchanged

## Nested / host unit of work (QC item 1)
Mid-UoW store save proven safe; no skip logic needed.
- `project.Transaction` outer block, legacy mode (CurrentDepth >= 1):
  `.ldml` on disk inside the block, one `<Add>` after.
- `project.UndoableOperation` outer block on target_sandbox_undoable:
  `.ldml` and `<Add>` on disk, CurrentDepth back to 0, a further Ensure works.
- `FromOpenProject` attached view over the host: `.ldml` + one `<Add>` on disk,
  host CurrentDepth still 1, tag in host `lp.CurVernWss`.

## Delete regression (shared helper), test_issue607_608_ws_store_live.py
Post-state: `.ldml` removed from the store and present in `trash/`;
idchangelog entries for the tag are `[Add, Delete]` with Producer="flexicon";
ExistsInStore False; tag gone from CurVernWss/CurAnalysisWss.

## Results
- test_issue625_ws_create_save_store_live.py: 6 passed
- test_issue607_608_ws_store_live.py: 6 passed
- Offline: 3635 passed, 1148 deselected

PASS
