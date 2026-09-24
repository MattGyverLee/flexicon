# 449 -- GetAll() wrappers crash when passed back to Operations resolvers

Worktree: C:/Github/flexicon-449, branch fix/449-wrapper-resolver-unwrap (off origin/main 88e2e2b).
Issue: MattGyverLee/flexicon #449 (P0). Leave the issue for the PR to reference; do not
use close/fix keywords in prose.

## Phase 1 -- Sweep + failing tests
- [x] T1 Sweep: every resolver / I<Interface>(x) cast site reachable by an object from a
      wrapper-returning GetAll() (Allomorph, MorphosyntaxAnalysis, AffixTemplate,
      CompoundRule, PhonologicalRule, AdhocProhibition, Annotation, PhonologicalContext;
      also PythonicWrapper). Output: reviews/cycle1-sweep.md (file:line table).
- [x] T2 Offline regression test: wrapper passed to each resolver unwraps before cast
      (tests/operations/test_449_wrapper_resolver_unwrap.py).

**Checkpoint:** sweep table + red offline test.

## Phase 2 -- Fix
- [x] T3 Shared helper on BaseOperations (e.g. `_UnwrapLcm(obj)`: LCMObjectWrapper ->
      .lcm_object, PythonicWrapper -> unwrap(); raw/int/str pass through).
- [x] T4 Apply helper in every site from T1 (AllomorphOperations.__GetAllomorphObject,
      MSAOperations.__GetMsaObject, POSOperations.__ResolveObject, MorphRuleOperations,
      PhonologicalRuleOperations, siblings).
- [x] T5 Docstrings: GetAll() docstrings of wrapper-returning ops state that I<Iface>(item)
      casts need `.lcm_object`; update docs/API_ISSUES_CATEGORIZED.md.

## Phase 3 -- Verify
- [x] T6 Live test tests/operations/test_449_getall_roundtrip_live.py (read-only on
      Sena 3 sandbox): for every wrapper-returning Ops, Ops.GetX(item) works for every
      item of GetAll(); stem+affix allomorphs, each MSA subtype present.
- [x] T7 Offline suite + live run; evidence/live-T6.md with run_mode=live.
- [ ] T8 QC + domain review; PR.

**Checkpoint:** all gates green -> PR.
