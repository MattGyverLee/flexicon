# STATUS -- 4.13.1-release-gate

**Updated:** 2026-11-02 (cycle 6 dispatched by lex-lead)
**Status:** `in_progress` -- RELEASE ON HOLD (user decision). No v4.13.1 tag
exists; none may be created or pushed by the crew.

## Where things stand

- #828 and #829 are APPROVED at cycle 6 and committed to main (commit made by
  the main session from lex-lead's message; check `git log` for the hash).
  Evidence: `evidence/live-cycle5-828-829.md` (offline 3966, live 13/13,
  run_mode live). Cycle-4 QC 90/100, no P0/P1; cycle-5 folded in its P2/P3.
- Same commit: `docs/MIGRATION_GUIDE.md` gained the #828 breaking-change entry
  and a #829 note (Quality Gate 5), and the CHANGELOG [4.13.1] intro and
  RELEASE_NOTES_v4.13.1.md no longer claim "no breaking changes".
- Filed #836 (P2): `cast_to_concrete` returns bare ICmObject for CmMedia
  (ICmMedia missing from lcm_casting). Not a release blocker.
- PR #835 (flexicon-4c, OPEN, unmerged at cycle 6): skips the #825 live test
  when FLEXICON_FW_DIR is unset. The authoritative sweep exports the variable
  regardless, so the test runs either way.

## The five P1 gaps the release waits on

| Issue | Kind | State |
|-------|------|-------|
| #828 Pronunciation media uses ICmFile instead of ICmMedia | internal fix | DONE, committed cycle 6 |
| #829 LexReferences.GetAll always raises | internal fix | DONE, committed cycle 6 |
| #830 Allomorph inflection-class methods target stem allomorphs | REDESIGN | user chose A; implementing cycle 6 |
| #831 Example media methods (no MediaFilesOS) | REDESIGN | user chose A; implementing cycle 6 |
| #832 Dependent clauses take markers, collection holds IConstChartRow | REDESIGN | user chose A; implementing cycle 6 |

## User decisions (final, 2026-11-02) -- binding

Each is a Principle VII cause-2 change ("the surface was wrong") and carries a
`BREAKING CHANGE:` footer plus a MIGRATION_GUIDE entry.

- **#830 -> A.** Retarget `Allomorphs.Get/Add/RemoveInflectionClass` to
  `IMoAffixForm.InflectionClassesRC` (MoAffixAllomorph; MoAffixProcess via the
  same IMoAffixForm cast). Stem allomorphs: Get returns [], Add/Remove raise
  FP_ParameterError naming `MSA.SetInflectionClass`. B lost: MSA class is
  atomic and per-sense, so redirecting silently edits data the caller did not
  name. C lost: the affix field is real (113 populated allomorphs across 15
  projects) and worth exposing.
- **#831 -> A.** Example media writers (Add/Remove/MoveMediaFile) raise
  FP_ParameterError BEFORE copying anything, naming the audio-writing-system
  route; GetMediaFiles/GetMediaCount return [] / 0; all five emit
  DeprecationWarning; removal at 5.0. B (faithful audio-WS rebuild) becomes
  ADDITIVE new methods in 4.14.0 -- it needs a return-shape design and an
  audio WS fixture (Target/Sena 3 have none).
- **#832 -> A.** Add/Insert/Remove/GetDependentClauses take IConstChartRow or
  its HVO (parameter renamed, positional calls unaffected). Docstring states
  plainly that writing DependentClausesRS alone leaves rows Normal/False/False,
  a state FLEx essentially never produces (1 case in hundreds); a
  logger [WARN] fires when an added row's ClauseType is Normal (design rule 6).
  The FLEx-faithful helper (sets ClauseType + group flags) is 4.14.0. Lead's
  review of the reflection: does NOT warrant revisiting A -- the methods never
  worked, the incomplete state is not corruption (FLEx has tolerated it in
  real data), and the caveat + warning make it honest.

## Cycle 6 (in flight)

1. Three parallel lex-programmers (disjoint files): #830, #831, #832, each
   with offline + live tests on sandbox fixtures; the failing #684/#740/#752
   tests are rewritten to assert the new behaviour.
2. Sequential: lex-programmer integration (contract snapshot regen, full
   offline run, `reviews/cycle6-diff.patch`), then lex-verification
   authoritative sweep with FLEXLIBS_REQUIRE_LIVE=1 and FLEXICON_FW_DIR
   exported (`evidence/live-full-sweep-cycle6.md`).
3. Parallel: lex-qc on the patch; lex-doc (CHANGELOG, RELEASE_NOTES,
   API_ISSUES, MIGRATION_GUIDE x3, and the owed overall verification-wording
   rewrite against the cycle-6 sweep).

## Owed before any tag (named, not ambient)

- Rewrite the overall 4.13.1 verification wording (cycle-6 lex-doc task).
- Final full live sweep with FLEXICON_FW_DIR exported (cycle-6 sweep).
- The release itself (tag) is the USER's call; the crew never tags.

## Next pickup

Cycle 7: lex-lead synthesises cycle-6 reports (reviews/cycle6-*.md,
evidence/live-full-sweep-cycle6.md), approves or loops fixes, drafts the
#830/#831/#832 commit message (three BREAKING CHANGE causes), then hands back
to the user for the release decision.
