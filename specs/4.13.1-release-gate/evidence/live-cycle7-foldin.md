# Live verification -- cycle 7 fold-in (#830/#831/#832 + 684/740/752)

**Project:** Sena 3 (sena3_sandbox fixtures; tempdir copy) | **Date:** 2026-11-02
**Env:** FLEXLIBS_REQUIRE_LIVE=1, FLEXICON_FW_DIR="C:\Program Files\SIL\FieldWorks 9" (same as cycle 6)
**run_mode:** live (tests/live_status.json)

## Commands
1. python -m pytest -m "not requires_live_project" -q
   -> 4006 passed, 1301 deselected, 0 failed (matches cycle-6 baseline)
2. python -m pytest tests/operations/test_issue830_allomorph_inflection_class_live.py tests/operations/test_issue831_example_media_live.py tests/operations/test_issue832_dependent_clause_rows_live.py tests/operations/test_issue684_example_movemedia_hvo_live.py tests/operations/test_issue740_allomorph_rc_hvo_live.py tests/operations/test_issue752_dependent_clause_hvo_live.py -m requires_live_project -q -s
   -> 9 collected, 9 passed, 0 failed, 0 skipped (18.78s)

## [EVIDENCE] lines (re-queried by HVO)
[EVIDENCE] affix allomorph hvo=58052 class hvo=152222 RC before=[]
[EVIDENCE] after add RC=[152222]
[EVIDENCE] after second add RC=[152222]
[EVIDENCE] after remove RC=[]
.[EVIDENCE] stem allomorph hvo=42189 class hvo=152222
.[EVIDENCE] MoAffixProcess present in sena3_sandbox: False
.[EVIDENCE] example_hvo=10446 icmfile_before=1 audiovisual_before=None example_before={999000002: 'TEST_831_example'}
[EVIDENCE] example_hvo=10446 icmfile_after_add=1 audiovisual_after_add=None example_after_add={999000002: 'TEST_831_example'}
[EVIDENCE] example_hvo=10446 icmfile_final=1 audiovisual_final=None example_final={999000002: 'TEST_831_example'} get=[] count=0
.[EVIDENCE] marker_hvo=10455 host_row=10449 r1=10450 r2=10451 r3=10452 r4_normal=10453
[EVIDENCE] pre-state RS=[]
[EVIDENCE] after add r1(obj), r2(hvo): RS=[10450, 10451]
[EVIDENCE] after re-add r1: RS=[10450, 10451]
[EVIDENCE] after insert r3@0: RS=[10452, 10450, 10451]
[EVIDENCE] after remove idx 0: RS=[10450, 10451]
[EVIDENCE] after add Normal r4: RS=[10450, 10451, 10453] warnings=1
[EVIDENCE] marker passed as element rejected; RS=[10450, 10451, 10453]

MoAffixProcess presence line: "MoAffixProcess present in sena3_sandbox: False" (so the process path is not live-exercised; offline-only).

## Step 4: HEAD (4.13.0) vs docs/MIGRATION_GUIDE.md
- GetInflectionClasses: returns [] unless ClassName == MoStemAllomorph, and IMoStemAllomorph has no InflectionClassesRC (getattr default None -> []). So [] for every allomorph in effect. MATCHES guide.
- AddInflectionClass / RemoveInflectionClass: raise FP_ParameterError when ClassName != MoStemAllomorph (i.e. affix). MATCHES guide.
- Examples.AddMediaFile HEAD docstring Returns ICmFile; MoveMediaFile Returns bool. MATCHES.
- HEAD writers documented FP_ReadOnlyError and FP_NullParameterError. MATCHES.
- Nit (no mismatch): guide says stem Add/Remove "failed on the missing field"; HEAD code path past the ClassName guard was not executed to confirm, inferred from the field's absence (stem path is not covered by a HEAD run).
