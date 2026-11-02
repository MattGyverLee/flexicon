# Cycle 5 lex-programmer report

Files changed:
- flexicon/code/Lexicon/PronunciationOperations.py (AddMediaFile: MediaFilesOS guard moved above CopyToProject, outside _TransactionCM; RemoveMediaFile: raises FP_ParameterError("Pronunciation does not support media files"), docstring Raises updated)
- tests/operations/test_issue829_lexreference_getall_live.py (try/except skip removed; Create called directly)
- tests/operations/test_issue686_pronunciation_movemedia_hvo_live.py, tests/operations/test_issue828_pronunciation_media_live.py (ASCII [EVIDENCE-*] prints of read-back media Hvo, MediaFileRA.Hvo, owner pronunciation Hvo; no assertion changes)
- tests/operations/test_issue828_pronunciation_media_offline.py (NEW, 2 tests: rejected AddMediaFile never calls CopyToProject; RemoveMediaFile raises FP_ParameterError without MediaFilesOS)
- CHANGELOG.md ([4.13.1] #828 entry sentence appended)

Guard reachability (read-only, Sena 3): __GetPronunciationObject returns an ILexPronunciation exposing MediaFilesOS for (i) a GetAll object and (ii) a bare HVO int (cast_to_concrete gives ILexPronunciation, hasattr True). The hasattr guard is NOT reachable for a real pronunciation; only for a non-pronunciation object or a stub.

Offline: 3966 passed, 0 failed (3964 + 2 new), 1296 deselected.
Live (FLEXLIBS_REQUIRE_LIVE=1, 686/828/829/644 live files): 13 passed, 0 failed.
tests/live_status.json run_mode: "live".

Evidence prints (sandbox HVOs) are in the -s output, e.g. 686 move: media_hvo=10449, MediaFileRA.Hvo=10448, owner_pron_hvo=10446. 828 add: media 10448, file 10447, owner 10445.
Nothing committed.
