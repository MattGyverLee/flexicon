# Cycle 4 QC (lex-qc) -- #828 / #829

Transcribed by the main session from the lex-qc hand-back (no write tool; read
cycle4-diff.patch and live-full-sweep-cycle4.md, grep of sources; did not open
the individual cycle-4 reports). Score 90/100. APPROVE. P0=0, P1=0.

## Gates
- Live evidence PASS: run_mode live, FLEXLIBS_REQUIRE_LIVE=1, 118 passed / 0 skipped;
  4 failures = known gaps #684, #740, #752 plus #825 (needs FLEXICON_FW_DIR; other
  session's test, out of scope).
- Read-back acceptable: #686/#828 tests re-fetch via Object(hvo) + cast_to_concrete,
  then re-read MediaFilesOS, MediaFileRA.Hvo, Label.get_String; not asserting on inputs.
- Sandbox fixtures + TEST_ prefix everywhere; no xfail/skip in test_issue686; no flexlibs2.
- No close/fix/resolve keyword before an issue number in CHANGELOG/notes/docs diff.
- Pattern audit section not verifiable (no commit message yet); include one at commit time.

## Code
- MoveMediaFile: single Add, no Remove (offline ratchet asserts). __FindOwnedMedia
  compares by HVO. All writes inside _TransactionCM. Docstrings match ICmMedia behaviour.
- expected_contract.json regeneration plausible: adds ICmMediaFactory (replacing
  ICmFileFactory in two files) plus pre-existing drift (IMultiString/IMultiUnicode moved,
  ws_text.py added, extra imports in InflectionFeatureOperations).

## P2
- tests/operations/test_issue829_lexreference_getall_live.py:66-68: `except Exception:
  pytest.skip(...)` around ops.Create can hide a regression; remove the skip.
- PronunciationOperations.py ~851: RemoveMediaFile silently returns when there is no
  MediaFilesOS, while AddMediaFile raises FP_ParameterError; make consistent.

## P3
- PronunciationOperations.py ~762: AddMediaFile runs Media.CopyToProject before the
  MediaFilesOS capability check, so a rejected call leaves an orphan ICmFile; move the
  check above the copy.
- test_issue686_..._offline.py ratchets match source text (weak; live tests cover behaviour).
- #686/#828 live tests do not print HVOs, so evidence cannot quote them.
- test_issue825 needs FLEXICON_FW_DIR exported (out of scope; flexicon-4c notified).
