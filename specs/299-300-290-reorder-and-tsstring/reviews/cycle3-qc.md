# QC Report

**Date:** 2026-09-10
**Quality Score:** 90/100
**Status:** ISSUES (Pattern-Audit Gate blocks approval; code quality itself is clean)

## Pattern-Audit Gate
- Sweep present in PR body/commit message: **FAIL** — no commit exists yet and no "Pattern audit" heading appears anywhere in `specs/299-300-290-reorder-and-tsstring/`. `cycle2-programmer-299.md` documents a *caller-site* regression grep (good, but not a sibling-shape sweep), and #290's fix explicitly flags but does not sweep the sibling `DiscourseOperations.py:888/892/950` hasattr branches or the `ConstChartClauseMarker`/`ConstChartMovedText` "bonus bugs" it found.
- Spot-check on a listed `[HIGH]` sibling: N/A — no sibling list exists to check.
- **Gate status: BLOCK.** All three issues match recognizable repeat-bug shapes named in CLAUDE.md itself: #290 is a textbook Category 8 recurrence (same-name field, different LCM type — the exact class of #36/#39/#40); #299/#300 are wrong-sequence/attribute-name assumptions on `_GetSequence`, a documented repeat pattern (`EnvironmentOperations` vs `InflectionFeatureOperations` precedent cited in `cycle1-domain.md`). None qualifies for the one-off exemption. Before commit, run `sweep-pattern` for (i) other bare-ITsString-treated-as-IMultiString sites (the `DiscourseOperations.py` branches already surfaced are a ready-made starting sibling list) and (ii) other `_GetSequence` overrides with unverified property names, and paste the result under a "Pattern audit" heading in the commit message body.

## Live-LCM Evidence Gate
- Change touches an LCM write path: yes (all three fixes).
- Evidence artifact: `specs/299-300-290-reorder-and-tsstring/evidence/live-cycle2.md` + `live-cycle2-raw.json`. Present.
- run_mode: **live** (confirmed via `tests/live_status.json` cross-check quoted in the evidence file).
- Pre/post field values present: **OK** — every claim shows HVO-ordered re-reads after each write (e.g. MorphBundlesOS `[10444,10445,10446]` → post-MoveDown `[10445,10444,10446]`), plus negative-path evidence (`TextOperations.Sort`/`MoveUp` raising `NotImplementedError` live) and the #290 Label/Notes round-trip re-read after Create/Set/clear.
- Cleanup confirmed: **OK** — `target_sandbox` (tempdir copy, discarded at teardown); real Target never opened.
- **Gate status: PASS.** This is exemplary evidence, including honest reporting of two unrelated pre-existing `DataNotebookOperations` defects discovered and routed around rather than silently fixed or hidden.

## Code Quality: 24/25
Clean, well-documented fixes. `TextOperations`'s deletion is the right call: `project.lp.Texts` is `TextsOC` (no indexer/`.MoveTo()`), the inherited `BaseOperations._GetSequence` `NotImplementedError` is honest, and it mirrors the existing no-override `LexEntryOperations` precedent — confirmed both by the domain ruling (`cycle1-domain.md`) and live negative-path evidence. Minor: `#290`'s now-inert `ws=` parameter on `GetLabel`/`GetNotes` was flagged rather than fixed — correct discipline (out-of-scope escalation, not scope creep).

## Standards Compliance: 24/25
`_MakeTsString`/`_ReadTsString` usage matches the documented `ILexSense.Source` idiom exactly. Docstrings updated accurately (e.g. `SegmentOperations._GetSequence` corrected from "segment analyses" to segments, with an explicit note that `AnalysesRS` has its own #215 API). No `flexlibs2` references introduced.

## Error Handling: 23/25
Unchanged/appropriate — `FP_ParameterError`/`NotImplementedError` paths preserved. `ConstChartRowOperations` correctly lets a wrong-type parent fail loudly rather than adding defensive normalization (per CLAUDE.md rule #5).

## Best Practices: 24/25
Test quality is strong and has real teeth: mocks deliberately omit the old (wrong) attribute so a regression raises `AttributeError` rather than silently passing (verified in `test_299_getsequence_ownership_fix.py`, `test_300_getsequence_property_rename.py`, `test_290_const_chart_row_tsstring.py`). (a) TextOperations deletion confirmed correct. (b) The #290 mock scaffold's unmarked `TsStringUtils.MakeString` use is consistent with house practice — grep-confirmed identical unmarked usage in `tests/test_lcm_api_real.py`; it only needs the loaded `SIL.LCModel` assembly, not an open project, so `requires_live_project` (which gates tests that open a `.fwdata` project) does not apply.

## Final Assessment
**Overall Score:** 90/100 (code) — but **BLOCKED** by the Pattern-Audit Gate.
**Recommendation:** FIX ISSUES — return to `/lex-programmer` to run `sweep-pattern` against the Category 8 (bare-ITsString-as-IMultiString) and `_GetSequence`-wrong-target shapes, and add a "Pattern audit" section to the eventual commit message(s) before landing.

---
**Reviewed By:** QC Agent

Key files reviewed (all absolute paths):
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\TextsWords\TextOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\TextsWords\ParagraphOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\TextsWords\SegmentOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\TextsWords\WfiMorphBundleOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\Notebook\DataNotebookOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\flexicon\code\Discourse\ConstChartRowOperations.py`
- `D:\Github\_Projects\_LEX\flexicon\tests\operations\test_299_getsequence_ownership_fix.py`
- `D:\Github\_Projects\_LEX\flexicon\tests\operations\test_300_getsequence_property_rename.py`
- `D:\Github\_Projects\_LEX\flexicon\tests\operations\test_290_const_chart_row_tsstring.py`
- `D:\Github\_Projects\_LEX\flexicon\tests\operations\test_cycle2_live_299_300_290.py`
- `D:\Github\_Projects\_LEX\flexicon\specs\299-300-290-reorder-and-tsstring\evidence\live-cycle2.md`
- `D:\Github\_Projects\_LEX\flexicon\specs\299-300-290-reorder-and-tsstring\reviews\cycle2-verification.md`
- `D:\Github\_Projects\_LEX\flexicon\specs\299-300-290-reorder-and-tsstring\evidence\live-290-reflection.md`

**Summary:** Code quality and Live-LCM evidence are both strong (live PASS with re-queried pre/post values); the Pattern-Audit Gate BLOCKs because no "Pattern audit" section/sibling sweep exists for three fixes that each match a named recurring bug shape in CLAUDE.md.
