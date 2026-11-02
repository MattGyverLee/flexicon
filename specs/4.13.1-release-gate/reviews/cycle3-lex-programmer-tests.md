# Cycle 3 programmer (tests) report

1. #724: switched to sena3_sandbox; no anthro codes in sandbox -> creates TEST_724_code via
   project.Anthropology.Create. Skip replaced by asserts; AnthroCodesRC HVOs re-queried after
   each write. PASS live.
2. #774: unused sense_c removed (call kept, no binding). PASS live.
3. #686: tmp_path IS an unused fixture param (wav is created via Media.Create, no file written).
   Left untouched (instruction: leave unless used; it is unused, so a one-word removal is available).
4. #640: 3 behavioural tests added (accepts IMultiUnicode stub, accepts IMultiString stub,
   rejects other types / plain str) by patching clr.GetClrType; source ratchet kept.
5. #782: new file, 3 tests (stale HVO -> False; empty analyses -> False; non-FP_ParameterError
   from Object() is not swallowed).

Offline: `python -m pytest -m "not requires_live_project" -q` -> 3962 passed, 1285 deselected, 0 failed.
Live: `$env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest tests/operations/test_issue724_lexsense_anthrocode_hvo_live.py tests/operations/test_issue774_baseops_move_hvo_live.py -m requires_live_project -q`
-> 2 passed, no skips. tests/live_status.json run_mode: "live".
Evidence: specs/4.13.1-release-gate/evidence/live-724.md (AnthroCodesRC pre [] / mid [26614] / post []).

Files changed: tests/operations/test_issue724_lexsense_anthrocode_hvo_live.py,
test_issue774_baseops_move_hvo_live.py, test_issue640_getbeststring_offline.py,
test_issue782_wfianalysis_exists_offline.py (new). Nothing under flexicon/ touched; no commit.
