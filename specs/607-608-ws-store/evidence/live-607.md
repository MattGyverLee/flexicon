# Live evidence: #607 (WritingSystems.Delete) and #608 (change-log producer)

Date: 2026-10-02. Project: tempdir copy of the Target .fwbackup (target_sandbox /
target_sandbox_undoable). FieldWorks 9.3.9 LCM. flexicon.version = 4.11.0.

## Command

    FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue607_608_ws_store_live.py -m requires_live_project -q

run_mode (tests/live_status.json): "live"

## Result line

    6 passed in 3.46s

Red-before-green: with the two source files stashed (fix reverted) the same file
fails 4 of 6 (`'???' == 'flexicon'` x2, `ldml still in the live store` x2).
Regression runs: tests/operations/test_issue250_defects123_ws_activation_live.py +
tests/operations/test_target_live_smoke.py: 8 passed (live).
Offline: `python -m pytest -m "not requires_live_project" -q` -> 2823 passed.

## Pre/post state read back from disk and the LCM (undoable=True sandbox, tag qaa-x-testdel)

PRE (fresh sandbox)
- WritingSystemStore: en.ldml, etu.ldml, idchangelog.xml
- ExistsInStore("qaa-x-testdel"): False

AFTER Ensure("qaa-x-testdel") + store save
- WritingSystemStore: en.ldml, etu.ldml, idchangelog.xml, qaa-x-testdel.ldml
- ExistsInStore: True; CurVernWss: "etu qaa-x-testdel"
- idchangelog.xml entries (kind, Producer, ProducerVersion, Id):
  - Add, FieldWorks, "Version 9.3.9 (apparent build date: 20-May-2026)", en
  - Add, FieldWorks, "Version 9.3.9 (apparent build date: 20-May-2026)", etu
  - Add, flexicon, 4.11.0, qaa-x-testdel          <- #608 (was "???" / "unknown")

AFTER Delete("qaa-x-testdel")
- WritingSystemStore: en.ldml, etu.ldml, idchangelog.xml, trash/ (trash/qaa-x-testdel.ldml)
- ExistsInStore: False; CurVernWss: "etu"
- idchangelog.xml gains: Delete, flexicon, 4.11.0, qaa-x-testdel   <- #607
  (the earlier Add is retained; the log is append-only, as in FieldWorks)

Also asserted by the tests: Exists() False; tag absent from CurVernWss,
CurAnalysisWss and LangProject.VernacularWritingSystems; default vernacular
Delete still raises FP_ParameterError with the store untouched; the Add entry
is attributed to flexicon even when written by CloseProject's own save (file
read after CloseProject); a read-only OpenProject of a Target copy still works.

PASS
