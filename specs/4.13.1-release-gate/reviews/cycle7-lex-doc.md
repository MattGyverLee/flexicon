# cycle7 lex-doc

Note: `git show HEAD:` was unavailable (no shell); old-code facts verified from the `-` lines of reviews/cycle6-diff.patch.

- docs/MIGRATION_GUIDE.md ~975: Get row: "`[]` (was: the stem's list)" -> affix "the classes (was: always `[]`)", stem "`[]` (unchanged)"
- MIGRATION_GUIDE ~979: added 4.13.0 behaviour: Get `[]` for all; Add/Remove raised FP_ParameterError on affix, failed on missing field on stem
- MIGRATION_GUIDE "Who Is Affected" (#830): rewritten to match (stem Get unchanged; stem Add/Remove now raise)
- MIGRATION_GUIDE #831 table: added paragraph: old FP_ReadOnlyError/FP_NullParameterError -> FP_ParameterError first; old returns ICmFile / bool gone
- MIGRATION_GUIDE #831 What Changed + Before/After: hedged audio route; `audio_ws_handle` marked illustrative/placeholder
- CHANGELOG.md ~21-31 banner: "stem allomorphs return [] / raise" -> "still return [] (Add / Remove raise FP_ParameterError)"
- CHANGELOG.md ~41-48 (#831 Deprecated): "is a file name" -> "appears to be ... (observed in surveyed projects; not yet exercised by flexicon tests)"; "Replacement" -> "Possible replacement (untested)"
- CHANGELOG.md ~96-101 (#830 Fixed): removed false "previously returned that allomorph's list"; now "still returns [] (as it did for every allomorph in 4.13.0)"
- RELEASE_NOTES_v4.13.1.md ~49-51: hedged audio route (dropped "which SetExample can write")
- docs/API_ISSUES_CATEGORIZED.md:519: hedged cause and fix ("Possibly ... (untested)")
- docs/FUNCTION_REFERENCE.md:376: hedged, dropped the SetExample claim
- Item 4: RELEASE_NOTES #830 bullet did not repeat the stem-Get error; no change. CHANGELOG banner and Fixed bullet did; corrected.
- CHANGELOG heading date and FLEXTOOLSMCP_WRITE_CONTRACT.md untouched.

CRLF check: all 5 edited files, regex `[^\r]\n` (multiline) found 0 LF-only line endings; `\r\n` count confirmed the check works (MIGRATION_GUIDE 1087).
