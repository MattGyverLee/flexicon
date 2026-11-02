# Cycle 6 - #832 DependentClausesRS element type (programmer)

Files edited (nothing staged/committed):
- flexicon/code/Discourse/ConstChartClauseMarkerOperations.py (no .pyi exists)
- flexicon/code/FLExProject.py (docstring example only, ~3707)
- tests/operations/test_issue230_dependent_clauses_rs.py (fake collection -> rows)
- tests/operations/test_issue752_dependent_clause_hvo_{live,offline}.py (rows)
- NEW tests/operations/test_issue832_dependent_clause_rows_{offline,live}.py

Renamed parameters (positional order unchanged):
- AddDependentClause(marker_or_hvo, row_or_hvo)
- InsertDependentClause(marker_or_hvo, index, row_or_hvo)
- RemoveDependentClause unchanged (index-based).

Behaviour:
- row_or_hvo: int goes through project.Object(hvo); ClassName must be
  "ConstChartRow" (cast to IConstChartRow) else FP_ParameterError naming
  IConstChartRow (a marker passed the old way gets this error).
- Add idempotent by HVO, check outside _TransactionCM; Insert keeps range check.
- Normal row: logger.warning("[WARN] ...") naming Dependent/Speech/Song and
  Start/EndDependentClauseGroup; never blocks. Not logged for Dependent rows.
- GetDependentClauses returns IConstChartRow (cast, fallback to raw).
- Docstrings say plainly: writes only DependentClausesRS; FLEx also sets
  ClauseType and group flags; Normal + both flags False is a state FLEx
  essentially never produces; set row fields via raw LCM until the 4.14.0 helper.

New imports: only `import logging` + module `logger`. I first imported
ClauseTypes from SIL.LCModel, but that broke
test_issue357 (stubbed SIL.LCModel) and tests/contract
test_no_new_type_dependencies (new type dependency). I removed it: the Normal check
compares str(row.ClauseType) == "Normal". Contract baseline untouched.

Live (FLEXLIBS_REQUIRE_LIVE=1, target_sandbox): 2 passed.
tests/live_status.json run_mode = "live".
[EVIDENCE] marker=10455 host_row=10449 r1=10450 r2=10451 r3=10452 r4(Normal)=10453
- pre RS=[]
- add r1(obj), r2(hvo): RS=[10450, 10451] (all ClassName ConstChartRow)
- re-add r1: unchanged
- insert r3@0: [10452, 10450, 10451]
- remove idx 0: [10450, 10451]
- add Normal r4: [10450, 10451, 10453], 1 warning
- marker as element: FP_ParameterError, RS unchanged

Offline: 3971 passed, 35 failed, 1301 deselected. Failures are all in files
I do not own and were not touched: test_issue581_offline.py (34),
test_issue471_lexicon_media_move_offline.py (1). tests/contract passes.

Not touched: demos/demo_discourse_operations.py:271 still calls
AddDependentClause(marker1, marker2) (outside my file list; now raises
FP_ParameterError) - needs updating by someone else.
