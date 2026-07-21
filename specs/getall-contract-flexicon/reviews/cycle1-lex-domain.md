# Cycle 1 — lex-domain: repo interface + wrap strategy

> Written by main session on behalf of lex-domain (ran read-only, no Write tool).
> Content is the agent's verbatim findings.

## Q1 — MediaOperations.py:179 fix

**Verdict: `ICmFileRepository` is correct; the real bug is a `TypeError` (2-arg call to 1-arg `ObjectsIn`), not just a wrong repository.**

- `ObjectsIn(repository)` (FLExProject.py:2938) takes exactly one arg and does `iter(self.ObjectRepository(repository).AllInstances())`. Current call `self.project.ObjectsIn(ICmObjectRepository, ICmFile)` passes two positional args → `TypeError` at runtime. That's the actual severity of #37.
- LibLCM auto-generates `I{ClassName}Repository : IRepository<I{ClassName}>` for **every** concrete model class via NVelocity template `src/SIL.LCModel/LcmGenerate/repositoryInterface.vm.cs` (lines 10-27). `CmFile` is a real model class (`MasterLCModel.xml`), so `ICmFileRepository` exists as generated code even though it has no hand-written entry in `RepositoryInterfaceAdditions.cs` (that file only carries supplemental members; absence there ≠ non-existence).
- **Fix:** add `ICmFileRepository` to the SIL.LCModel import at MediaOperations.py:22-28; change line 179 to `return self.project.ObjectsIn(ICmFileRepository)`. `AllInstances()` yields `ICmFile` directly (via `IRepository<ICmFile>`); no cast needed. Matches the `ILexEntryRepository`/`ILexSenseRepository` pattern.
- **Semantic-difference flag:** `ICmFileRepository.AllInstances()` returns *every* `CmFile` DB instance regardless of owning collection — not just files reachable by walking `LangProject.MediaOC`/`PicturesOC`. CmFile can also be referenced from `LexPronunciation` media, external-link files, and orphaned records. For #37's audio-rename case this is *more correct* (catches files a folder walk misses) but NOT strictly equivalent to a MediaOC+PicturesOC walk — worth a one-line docstring caveat.

## Q2 — GetAll() wrap contract: (a) vs (b)

**Recommendation: (a) — decorate each raw-returning `GetAll()` individually with `@wrap_enumerable`; do NOT centralize into `OperationsMethod`/`BaseOperations`.**

Rationale: `OperationsMethod` (BaseOperations.py:243) wraps *every* Operations method — Create/Update/Delete/Find/scalar getters included. Baking `_needs_enumerable_wrap` into it would run the check against every return value library-wide, including intentional single objects, booleans, and non-collection iterators — large blast radius for a fix only `GetAll`-shaped methods need. `_needs_enumerable_wrap` IS safe for `AllomorphCollection`/`RuleCollection` (both inherit `SmartCollection`, which defines `__len__`/`__getitem__` in `Shared/smart_collection.py`, so the "already sequence-like" branch no-ops regardless) — the risk with (b) is NOT to the smart collections but to the broader surface (accidentally wrapping a generator-based non-GetAll helper, or a scalar method returning something with `__next__`). Option (a) keeps the wrap decision to a set a reviewer/lint rule can enumerate: `grep '@wrap_enumerable' | wc -l` vs `grep 'def GetAll'`.

**Docstrings:** normalization needed either way — `MediaOperations.GetAll` (line 171) already *claims* "Returns an EnumerableWrapper" despite currently raising TypeError before reaching it. After adding the decorator, audit all `GetAll`-style docstrings for the same "claims EnumerableWrapper, decorator missing/wrong" mismatch — a grep for `Returns an EnumerableWrapper` cross-checked against `@wrap_enumerable` presence catches the whole class.

## Summary
Q1 — `ICmFileRepository` correct (generated per-class by LibLCM); line 179 is a TypeError (2-arg→1-arg), plus a folder-walk-vs-repository semantic caveat for a docstring note. Q2 — option (a), per-method `@wrap_enumerable`; SmartCollection's `__len__`/`__getitem__` make it safe either way, but centralizing widens blast radius to non-GetAll methods for no added safety.
