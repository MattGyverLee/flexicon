# 449 status
- 2026-09-24: worktree created (C:/Github/flexicon-449, branch fix/449-wrapper-resolver-unwrap
  off origin/main 88e2e2b, upstream unset). Spec scaffold written. Next: cycle 1 (T1+T2).
- 2026-09-24: cycle 1 T2-T6 complete (lex-programmer). Added
  `BaseOperations._UnwrapLcm`; applied at every T1 sweep site (Allomorph,
  MSA, MorphRule, PhonologicalRule resolvers; base reorder methods;
  WfiMorphBundle Get*Object; LexSense.SetGrammaticalInfo). Updated GetAll
  docstrings + docs/API_ISSUES_CATEGORIZED.md Category 13. Offline test
  (23/23 pass, fails 21/23 on unmodified code) +
  live test (6/6 pass, requires_live_project, sena3_sandbox, run_mode=live).
  Evidence: specs/449-wrapper-resolver-unwrap/evidence/live-T6.md. Two
  MorphRule bare-owner bugs (template Delete, __DuplicateAffixTemplate)
  confirmed out of scope, documented for a follow-up issue. Next: T7/T8
  (QC + domain review, PR).
- 2026-09-24 cycle 1 done: _UnwrapLcm helper + ~18 sites (b8e4b92, bb95a1a, af45c41, not pushed).
  Offline new file 23/23 (21 red on main). Full offline suite WAS run: 148F/2109P/48E vs main
  baseline 168F/2089P/48E; the delta is 20, but 21 tests fail on main, so the numbers are off by one
  and the failing node IDs need diffing. Live read-only 6/6 run_mode=live.
  Gaps for cycle 2: no live read-back for write paths that were silent no-ops (SetStratum,
  SetDisabled, MoveUp/Down/Before/After/Swap, SetGrammaticalInfo, WfiMorphBundle SetMorph/SetMSA,
  ChangeAffixVariant, MorphRule Delete/Duplicate); PhonologicalRules = 0 in Sena 3.
  Out of scope: MorphRule template Delete / __DuplicateAffixTemplate take a bare owner from
  _GetObject(Owner.Hvo); needs its own issue (user to approve filing).
- 2026-09-24 cycle 2 done: live write-path tests (60489a8) 10 pass + 1 xfail (affix-template owner bug);
  independent live re-run 16 pass / 1 xfail, run_mode=live. The off-by-one is now explained: the stale ratchet
  tests/operations/test_issue251_msa_feature_sync.py::test_get_msa_object_hasattr_calls_are_allowlisted
  looks for the removed hasattr(_obj) unwrap. QC 94/100 APPROVE. Domain: the wrapper round-trip contract must also go
  into docs/ARCHITECTURE_WRAPPERS.md (+ new-wrapper checklist) and docs/API_DESIGN_PHILOSOPHY.md.
  Waiting on the user: file the affix-template owner bug (domain says P2, cycle 1 proposed P1), and file the
  wrapper __eq__/__hash__-by-Hvo follow-up?
- 2026-09-24 cycle 3 done (lex-programmer): the off-by-one flagged by cycle 2 verification was the stale
  ratchet test_get_msa_object_hasattr_calls_are_allowlisted (asserted "at least one hasattr()" for the
  removed hasattr(_obj) unwrap); it is now updated to assert zero-or-allowlisted hasattr() calls plus a
  positive check that __GetMsaObject routes through self._UnwrapLcm. Added the round-trip contract section
  to docs/ARCHITECTURE_WRAPPERS.md, a new-wrapper checklist item there and in
  docs/API_DESIGN_PHILOSOPHY.md's "Creating a new wrapper" list, and a Rule 1 cross-reference; Category 13
  in docs/API_ISSUES_CATEGORIZED.md left unchanged (already consistent). Offline:
  48 passed (test_issue251_msa_feature_sync.py + test_449_wrapper_resolver_unwrap.py, not
  requires_live_project).
- 2026-09-24 cycle 3 done, lead verdict APPROVED: ratchet updated (f1b9f5c), contract docs (4ece234), offline
  failing-ID diff against main@88e2e2b empty both ways (195 identical pre-existing), alias ratchet green, no
  production change since the cycle 2 live run (run_mode=live). Waiting on the user: approve push + PR; file the
  affix-template owner bug (recommended P2) and the wrapper __eq__/__hash__ follow-up?
