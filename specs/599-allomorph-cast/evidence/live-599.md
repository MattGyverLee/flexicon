# Live evidence: issue 599 (AllomorphOperations.GetForm on affix allomorphs)

Finding: on current main the shared resolver `__GetAllomorphObject` already
dispatches on ClassName (MoStemAllomorph -> IMoStemAllomorph,
MoAffixAllomorph -> IMoAffixAllomorph) and unwraps GetAll() wrappers first
(#449, merged 2026-09-24 22:40). The #599 log evidence is from 2026-09-24
13:41, before that merge; the reported TypeError was a wrapper being passed to
a pythonnet cast. No source change needed; regression locks added.

Command (PowerShell: `$env:FLEXLIBS_REQUIRE_LIVE = "1"`):

    python -m pytest tests/operations/test_issue599_allomorph_getform_affix_live.py -m requires_live_project -q

run_mode (tests/live_status.json): "live"

Fixture: target_sandbox (tempdir copy of Target .fwbackup).

Pre-state: sandbox entry TEST_599_entry created; Allomorphs.Create(...,
morphType="suffix") and (..., morphType="stem").
Read back from LCM (sandbox.Object(hvo).ClassName): affix -> "MoAffixAllomorph",
stem -> "MoStemAllomorph".
Post-state: GetForm returned "TEST_599_suf" for the affix as raw object, HVO
and GetAll() wrapper; "TEST_599_stem" for the stem as object and HVO.

Result: 1 passed in 1.93s -- PASS
Offline: `python -m pytest -m "not requires_live_project" -q` -> 2795 passed, 1111 deselected
