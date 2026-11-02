# STATUS -- 4.13.1-release-gate

**Updated:** 2026-11-02 (cycle 7 synthesis by lex-lead; fold-in dispatched)
**Status:** `in_progress` -- RELEASE ON HOLD (user decision). No v4.13.1 tag
exists; none may be created or pushed by the crew.

## Where things stand

- origin/main HEAD 7668f58f: #828 and #829 committed and closed (cycle 6).
- #830, #831, #832 (user option A each) are implemented, UNCOMMITTED in the
  working tree. Cycle-6 gates:
  - Authoritative live sweep: `evidence/live-full-sweep-cycle6.md` --
    run_mode live, FLEXLIBS_REQUIRE_LIVE=1, FLEXICON_FW_DIR exported,
    99 files, 127 passed / 0 failed / 0 skipped / 0 errors (cycle 4 was
    118 / 4 failed). One of the 127 (MoAffixProcess round trip) is
    presence-report only: Sena 3 has no MoAffixProcess.
  - Offline: 4006 passed / 0 failed / 1301 deselected.
  - QC `reviews/cycle6-lex-qc.md`: 88/100, no P0/P1, 3 P2, 6 P3.
  - Contract snapshot: +1 entry (IMoAffixForm), attributable to #830.
  - Docs `reviews/cycle6-lex-doc.md`: CHANGELOG, RELEASE_NOTES (now
    "Release candidate (not yet tagged)"), API_ISSUES, MIGRATION_GUIDE x3,
    FUNCTION_REFERENCE.
- QC P2-2's remark that MIGRATION_GUIDE / API_ISSUES are "not in this patch"
  is stale: QC read `cycle6-diff.patch`, cut before lex-doc ran. Both are
  modified in the tree. What the guide still lacks is detail (below).

## Cycle 7 (in flight) -- small fold-in, then commit

Folded in (lex-lead decision):
- P2-1: hedge `_EXAMPLE_MEDIA_WITHDRAWN` (audio-WS route "observed in
  surveyed data, not exercised in a sandbox"); keep the substring
  `SetExample(example, text, wsHandle)` the offline test asserts. Same hedge
  in the five docs that state the route as fact.
- P2-2: MIGRATION_GUIDE detail -- #830 table row is wrong (old stem Get was
  always [] too, the field never existed; affix Get used to return []);
  #831 old exceptions (FP_ReadOnlyError / FP_NullParameterError) and old
  returns (ICmFile, bool). The commit footer covers all four QC omissions.
- P2-3: soften the MoAffixProcess wording (live test docstring + library
  docstrings) to "offline-tested only". Live test kept (count stays 127).
- P3-1: move `import logging` to the top of
  ConstChartClauseMarkerOperations.py.

Deferred (user to approve filing one P3 issue): P3-2 narrowing `except
Exception` around IConstChartRow casts (behaviour change -- pythonnet cast
failures do not reliably surface as TypeError), P3-3 `_FakeClauseMarker`
alias, P3-4 private `_TransactionCM` + `except Exception: pass` in the 832
live test, P3-5 weak `Object(hvo) is not None` in the 684 live test, P3-6
740 live RC checks not re-fetched via `Object(hvo)`. Also deferred to
4.14.0: an audio-WS sandbox fixture for the #831 route.

Cycle-7 artifacts: `reviews/cycle7-lex-programmer.md`,
`reviews/cycle7-lex-doc.md`, `reviews/cycle7-lex-verification.md`,
`evidence/live-cycle7-foldin.md` (offline full + live 830/831/832/684/740/752).

Commit message draft: `reviews/cycle7-commit-message.txt` (one placeholder,
`<CYCLE7_LINE>`, filled at cycle 8). Cycle 8: lex-lead go/no-go, fills the
line, main session commits + pushes (explicit paths), then `needs_human`
handoff for the tag decision.

## Open issues after the commit

#833 (Checks._GetCheckList stub, P2), #834 (Note.Duplicate insert_after
no-op, P2), #836 (cast_to_concrete / ICmMedia, P2) -- non-blocking.
Also open and unlabelled: #776 (a bug with no priority label), #826.

## Decisions owed by the USER before any tag

1. Release date for CHANGELOG `## [4.13.1] - 2026-11-01` (stale) and
   RELEASE_NOTES line 3.
2. Tag v4.13.1 now or hold. Any `v*` tag triggers the PyPI publish workflow.
3. `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md:289` lists Examples.AddMediaFile ->
   Media.CopyToProject as one of "three real" wrapper-calls-wrapper pairs;
   after #831 that pair no longer exists (two remain). Fast-path doc fix --
   recommend yes.
4. File the deferred-P3 follow-up issue (QC P3-2..P3-6).
5. Confirm #833/#834/#836 ride to a later release (4.13.2 / 4.14.0).
6. Priority label for #776 (unlabelled bug).

## Next pickup

Cycle 8: lex-lead reads the four cycle-7 artifacts, approves or loops,
fills `<CYCLE7_LINE>`, main session commits + pushes, then `needs_human`.
