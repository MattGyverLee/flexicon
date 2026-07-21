# tasks — getall-contract-flexicon

Repo: flexicon (main). Issue: FlexToolsMCP#37 (cross-repo).

## Cycle 2 — implement + review

- [x] T1 (D1/#37) Fix `MediaOperations.GetAll` — import `ICmFileRepository`, drop
      unused `ICmObjectRepository`, change line 179 to
      `ObjectsIn(ICmFileRepository)`, add folder-walk-vs-repository docstring caveat.
      (Already implemented in working tree — see cycle2-lex-programmer.md.)
- [x] T2 (D2/B1) Add `@OperationsMethod` to `AgentOperations.GetAll`
      (`Lists/AgentOperations.py:84`); no `@wrap_enumerable`.
      (Already implemented in working tree — see cycle2-lex-programmer.md.)
- [x] T3 (D3/B2) Make `TranslationTypeOperations.GetSegmentsWithType`
      (`Lists/TranslationTypeOperations.py:320`) fail-loud (NotImplementedError +
      docstring fix) or implement; never silent `None`. Flag if own spec needed.
      (Already implemented in working tree — see cycle2-lex-programmer.md.)
- [x] T4 (verify) Regression test for #37 (GetAll no-TypeError / correct arity) +
      class-level-call test for `AgentOperations.GetAll(project)` + behavior test
      for `GetSegmentsWithType` (raises rather than returns None). Full suite green.
      VERIFIED: 3 fixes correct + regression-clean delta 0 (clean-main HEAD ff1c008
      vs working tree — identical 172-node fail/error set, 0 new failures, 0 fixed).
      See cycle4-lex-verification.md + cycle5-lex-verification-baseline.md.
- [x] T5 (QC) Style/complexity/decorator-order/import-hygiene review of T1-T3.
      QC 91/100 APPROVE. See cycle4-lex-qc.md.

**Checkpoint:** implementation reviewed and green.

## Cycle 3 — GetAll consistency scope (author pivot; new)

- [x] T7 (Defect A, the real fix) Standardize the ~51 bare `GetAll` docstrings
      (plus the `GetAll*` variants that share the same misleading wording) to
      `Returns:\n    <ContainerType>[<Element>]: <description>`, dropping
      `Yields:` wording on every method that doesn't have a genuine unwrapped
      generator return (audit found none). See cycle3-lex-programmer.md for the
      full before/after tally against the 16/2/33 audit taxonomy.
- [x] T8 (contract guarantee doc) Add `docs/getall-contract.md` (the canonical
      loop/len/index/re-iterate guarantee across `EnumerableWrapper`/`list`/
      `SmartCollection`), a one-line pointer in `README.rst`, and a
      cross-referencing "Behavioral collection contract" paragraph in the
      `wrap_enumerable` docstring in `BaseOperations.py`.
- [x] T9 (straggler re-verify) Re-ran the raw-shape-without-`@wrap_enumerable`
      sweep across all real `GetAll*` methods: confirmed 0 stragglers (matches
      Cycle-1 audit). No runtime changes required.
- [x] T10 (.pyi stubs — assessed, deferred) `.pyi` stubs use blanket
      `(*args: Any, **kwargs: Any) -> Iterator[Any]` for nearly every method
      across ~30 files, not just `GetAll` — the return-type annotations are
      already generic/inaccurate independent of this feature, and the
      parameter signatures don't match the real methods either. Reconciling
      `GetAll` return annotations to `EnumerableWrapper[T]`/`list[T]`/
      `SmartCollection[T]` properly requires (a) modeling those generics in
      the stub layer, plus (b) fixing the pre-existing `*args/**kwargs`
      signature drift, which is a distinct, larger pre-existing defect.
      Recommend a dedicated follow-up cycle rather than folding it in here.

**Checkpoint:** T7-T9 implemented and self-verified (py_compile green, import
smoke pending live review); T10 explicitly deferred with rationale above.

## Cycle 4 — commit (after gates green)

- [ ] T6 (archivist) Commit on flexicon `closes MattGyverLee/FlexToolsMCP#37`
      (cross-repo ref), update CHANGELOG `[Unreleased]` + history.md. Combined
      commit covers T1-T3 (already-implemented D1-D3 fixes) and T7-T9
      (docstring standardization + contract guarantee doc) together.
