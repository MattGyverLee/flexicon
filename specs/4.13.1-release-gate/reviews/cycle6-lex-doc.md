# Cycle 6 - lex-doc

Edited (all CRLF preserved; grep found 0 LF-only lines): CHANGELOG.md, RELEASE_NOTES_v4.13.1.md,
docs/API_ISSUES_CATEGORIZED.md (3 Category 8 rows, heading extended), docs/MIGRATION_GUIDE.md
(#830, #831, #832 appended), docs/FUNCTION_REFERENCE.md (Examples.GetMediaFiles/GetMediaCount
marked deprecated). Nothing staged or committed.

CHANGELOG: callout now lists four breaking changes; #830/#832 under Fixed; #831 under new
Deprecated heading.

Verification wording, before -> after:
- CHANGELOG Known gaps "Issue 740 has offline evidence only ... Other fixes carry offline and
  live evidence under specs/" -> a Verification section: offline 4006 passed/0 failed; live
  127 passed/0 failed/0 skipped of 127, run_mode live, FLEXLIBS_REQUIRE_LIVE=1, sandbox
  fixtures, 99 files changed since v4.13.0 (not every live test); MoAffixProcess offline only
  (Sena 3 sandbox has none); #831 verified inert only (no audio-WS fixture). Known gaps: FLEx UI
  label for affix inflection classes unverified; #836 open.
- RELEASE_NOTES: same content, shorter. Line 3 "Released 2026-11-01" -> "Release candidate
  (not yet tagged)". "One breaking change" -> "Four breaking changes" with a bullet each.
- The #740 offline-only gap was dropped: the sweep shows 740 live passing (2p).
- Version date in the CHANGELOG heading left as 2026-11-01 (your call).

Grep (docs/**/*.md, README.rst, examples/, demos/, .pyi): no stale callers. Only
docs/FUNCTION_REFERENCE.md:375-379 (fixed). demos/demo_discourse_operations.py:274 already
passes a row (integration fix). docs/FLEXTOOLSMCP_WRITE_CONTRACT.md:289 cites
ExampleOperations.AddMediaFile as a write surface; not in my allowed list, left as is.
No Allomorphs.*InflectionClass or marker-style callers elsewhere.

Not reconciled: cycle-1 QC overclaim findings were already fixed in earlier cycles. The
sweep's #829 count line is not tagged EVIDENCE, so I did not cite it. MIGRATION_GUIDE
#831 example uses wsHandle=audio_ws_handle as an illustrative placeholder (no audio WS
fixture exists to verify the route).
