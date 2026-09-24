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
