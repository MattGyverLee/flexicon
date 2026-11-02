# Cycle 2 QC (lex-qc) -- 4.13.1 release gate

Transcribed by the main session from the lex-qc hand-back (patch-based review;
no shell; did not read programmer-tests/data/lib reports in full; did not open
live-full-sweep-cycle2.md or live_status.json). Score 76/100. Recommendation:
APPROVE library and test edits with fixes; hold release until P2s triaged.

Gates: no `flexlibs2` in added lines; no new public API; pattern audit N/A.

## (a) Library -- sound
- Internal casting: possibility_item_base.py:144, NoteOperations.py:415.
- _EnsureWriteEnabled / FP_* untouched. MorphRule Delete resolves member first,
  then opens bracket (no empty undo entry). #640 clr.GetClrType(...).IsInstanceOfType
  correct. #670 sound, signature kept, raises FP_ParameterError if no re-segmentation.
  WfiAnalysisOperations.Exists catches only FP_ParameterError from Object(int).

## (b) Tests
- P2: #686, #740 (remove_inflection_class), #684, #752 fail on purpose, unmarked.
  Offline gate stays green (requires_live_project) but the live gate is permanently
  red. Want xfail(strict=True, reason="#NNN") or equivalent.
- P2: #724 still skips on Target -> `FAIL: unverified` under CLAUDE.md. Switch to
  sena3_sandbox as done for #720/#722.
- P3: test_issue686...py:16 patch only adds unused tmp_path (stale/incomplete?).
- P3: #658 acceptable, but dropped position assertion means insert_after is
  silently ignored for notes: document the limitation or file an issue.
- P3: #640 is still a source-text ratchet; no behavioural offline test.
- P3: #774 unused sense_c. #782 has no offline test for Exists -> False on stale HVO.
- P3: SegmentOperations.__GetSegmentFactory may now be dead code.
- OK: #668, #692, #804, #814, #664; #802 now behavioural.

## (d) Open gaps (pre-existing API defects, code untouched)
- #752 P1 (label right). #684 should be P1 not P2 (5 methods no-op/raise).
- #686, #740 AddInflectionClass, LexReferenceOperations.GetAll: evidence is a
  prose error string with no reflection dump; capture it. All always raise ->
  suggest P1/P1/P1 unless reflection says otherwise.
