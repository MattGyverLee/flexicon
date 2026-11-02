# Cycle 6 QC (lex-qc) -- #830 / #831 / #832

Transcribed by the main session from the lex-qc hand-back (no write tool; no tests run;
results taken from cycle6-integration.md and evidence/live-full-sweep-cycle6.md).
Score 88/100 (quality 22, standards 22, error handling 22, best practices 22).
APPROVE with fixes. P0=0, P1=0, P2=3, P3=6.

## Gates
- Pattern audit: N/A (redesign, not a bugfix commit).
- Live-LCM: PASS. run_mode live; sandboxes; 127 passed, 0 skipped. Quoted read-backs:
  #830 RC [] -> [152222] -> [152222] -> []; #832 RS sequences; #831 ICmFile count,
  AudioVisual directory and multistring unchanged.
- grep of patch: no xfail, no pytest.skip, no Xinaliq; only sena3_sandbox / target_sandbox.

## User decisions: all faithful, no drift
- #830: local IMoAffixForm cast, shared resolver untouched; stem Get []; stem Add/Remove
  raise FP_ParameterError naming project.MSA.SetInflectionClass; MoAffixProcess handled.
- #831: five methods warn; writers raise with no copy, no LCM access, no transaction
  (offline test asserts project.method_calls == []); readers return []/0.
- #832: row or HVO; ClassName check raises FP_ParameterError (including for a clause
  marker); parameter renamed to row_or_hvo, positional order kept; [WARN] on Normal rows.
- Principle V OK in all three (no UI-label claim; no LinkedFiles claim, test asserts it;
  #832 states the Normal/False/False caveat plainly).
- Tests: #684/#740/#752 assert new behaviour; #581 stub gained IMoAffixForm, not weakened;
  #471 example case replaced by an AST test, pronunciation + sense-picture cases kept.
- Contract snapshot diff = one IMoAffixForm import, attributable to #830.

## P2
1. ExampleOperations.py ~line 48 (_EXAMPLE_MEDIA_WITHDRAWN): the message recommends
   SetExample(..., audio wsHandle) as the route, stated as fact from one project (Xinaliq,
   read-only); Target and Sena 3 have no audio writing system, so the route is not live-tested.
   Hedge it ("observed in...") or add a sandbox test that creates an audio WS and calls SetExample.
2. Breaking-change list in cycle6-integration.md (lines 22-29) omits: #830 affix Get now returns the
   real list (was always []); #831 Add/Remove/MoveMediaFile used to raise FP_ReadOnlyError or
   FP_NullParameterError and now raise FP_ParameterError first; #831 old return values (ICmFile, bool)
   gone; #832 GetDependentClauses elements now cast to IConstChartRow. MIGRATION_GUIDE and
   API_ISSUES_CATEGORIZED are not in this patch -- cycle 7 must add them.
3. test_issue830_allomorph_inflection_class_live.py ~1770-1776: the MoAffixProcess test returns
   early when no data exists, so it passes vacuously (not a skip; evidence discloses it).
   Docstrings claim MoAffixProcess handled but only offline mock covers it: soften to
   "untested live" or drop the test.

## P3
1. ConstChartClauseMarkerOperations.py:31 `import logging` mid-file; move to top.
2. ConstChartClauseMarkerOperations.py (GetDependentClauses, __ResolveDependentRow): bare
   `except Exception` around IConstChartRow(...) casts; catch TypeError or similar.
3. test_issue230_dependent_clauses_rs.py ~63,76: `_FakeClauseMarker = _FakeRow` alias is misleading.
4. test_issue832_dependent_clause_rows_live.py: calls private _TransactionCM; finally-cleanup
   is `except Exception: pass` (harmless in sandbox).
5. test_issue684_example_movemedia_hvo_live.py ~34: `assert Object(hvo) is not None` is weak;
   compare ICmFile count as #831 does.
6. test_issue740_allomorph_rc_hvo_live.py ~84-90: RC checks go through ops.GetInflectionClasses
   on the same object, not project.Object(hvo); re-fetch by HVO.
