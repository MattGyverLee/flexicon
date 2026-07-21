# SPEC — getall-contract-flexicon

**Repo:** flexicon (MattGyverLee/flexicon), branch `main`
**Tracking issue:** FlexToolsMCP#37 (issue lives on the MattGyverLee/FlexToolsMCP
tracker; the fix lands in the flexicon repo — cross-repo reference).
**Status:** Cycle 2 — implementation
**Origin:** Spun out of the MCP-side `getall-contract` investigation.

## Reframe (result of Cycle 1)

The original hypothesis was a **systemic** GetAll() wrap defect ("Defect 2") across
flexicon. **That disease does not exist.** The Cycle-1 code audit (Explore) audited
79 real methods (51 bare `GetAll` + 28 `GetAll*` variants) and found:

- **0** raw-shape GetAll methods missing `@wrap_enumerable`.
- **0** additional two-arg `ObjectsIn(` arity bugs beyond MediaOperations.

Every raw/generator/`ObjectsIn`-returning method already carries `@wrap_enumerable`;
every unwrapped method returns a materialized `list`/`dict`/`set`. The MCP-index
"prose-vs-type contradiction" (Defect A) is manufactured by the **MCP extractor**
(`flexicon_analyzer.py` reads the `Yields: <Element>` docstring line as
`returns.type`), NOT by flexicon docstrings — those correctly say
"EnumerableWrapper". **Therefore the MCP-side Level-2 extractor override is a genuine
MCP fix and STAYS** (do not drop it; tracked separately on the MCP repo).

## In scope for this flexicon feature

Three concrete, unrelated defects to fix in the flexicon repo:

### D1 — MediaOperations.GetAll TypeError (issue #37)
`flexicon/code/Shared/MediaOperations.py:179`
```python
return self.project.ObjectsIn(ICmObjectRepository, ICmFile)   # 2-arg -> TypeError
```
`FLExProject.ObjectsIn(repository)` takes exactly ONE arg. The current 2-arg call
raises `TypeError` at runtime before the (already-correct) `@wrap_enumerable`
docstring contract can apply.

**Fix:**
- Import `ICmFileRepository` from `SIL.LCModel` (line 22-28 block). LibLCM
  auto-generates `I<Class>Repository : IRepository<I<Class>>` for every concrete
  model class; `CmFile` qualifies, so `ICmFileRepository` exists even without a
  hand-written entry in `RepositoryInterfaceAdditions.cs`.
- Change line 179 to `return self.project.ObjectsIn(ICmFileRepository)`.
  `AllInstances()` yields `ICmFile` directly — no cast.
- `ICmObjectRepository` is used ONLY at line 27 (import) and line 179 in this file
  — replace it with `ICmFileRepository` in the import (remove the now-unused
  `ICmObjectRepository`). Verify no other use before removing.
- Keep the existing `@wrap_enumerable` / `@OperationsMethod` decorators (correct).
- **Docstring caveat (add one line):** repository enumeration returns *every*
  `CmFile` DB instance (including pronunciation media, external-link files, and
  orphans), which is BROADER than a `LangProject.MediaOC`/`PicturesOC` folder walk.
  For the audio-rename use case this is *more correct* (catches files a folder walk
  misses) but is NOT strictly equivalent to a folder walk — note this.

### D2 — AgentOperations.GetAll missing @OperationsMethod (B1)
`flexicon/code/Lists/AgentOperations.py:84`
The only GetAll lacking both decorators. It legitimately overrides
`PossibilityItemOperations.GetAll` because `AnalyzingAgentsOC` is a plain
`LcmOwningCollection` with no `PossibilitiesOS`. Body returns `list(agents_oc)` — a
materialized list.

**Fix:**
- Add `@OperationsMethod` (inner decorator) so the class-level call form
  `AgentOperations.GetAll(project)` works like every sibling.
- **Do NOT add `@wrap_enumerable`** — return is a plain `list`, wrap is moot and
  would misrepresent the shape. Preserve the `AnalyzingAgentsOC` override rationale
  in the docstring.

### D3 — TranslationTypeOperations.GetSegmentsWithType silent None (B2)
`flexicon/code/Lists/TranslationTypeOperations.py:320`
Docstring promises `Yields: ISegment`, but the inner block is `pass` (no
yield/return) so the method always returns `None`. The author's own note says
segments don't carry typed translations "in the same way texts do" — so the
*correct* semantic behavior is genuinely undefined without further design.

**Fix (fail-loud, conservative):**
- Replace the silent `pass` no-op so the method no longer lies about its contract.
  Preferred: raise `NotImplementedError` with a message that points callers to the
  working `GetTextsWithType()`; update the docstring to state it is not implemented
  (drop/adjust the `Yields:` promise).
- **Flag:** if the programmer determines a genuine segment-level implementation is
  feasible and in-scope, implement it instead; otherwise note that a real
  implementation needs its own spec. Do not leave a silent `None`.

## Out of scope
- Any systemic wrap sweep (nothing to wrap — see reframe).
- The MCP-side Level-2 extractor fix (separate MCP repo feature; stays).
- Designing a real `GetSegmentsWithType` implementation (own spec if needed).

## Success criteria
- `MediaOperations.GetAll()` returns an EnumerableWrapper over `ICmFile` without
  TypeError; regression test covers the arity fix.
- `AgentOperations.GetAll(project)` callable in class-level form; test covers it.
- `GetSegmentsWithType` no longer returns silent `None` (raises or implements).
- Full flexicon test suite green; no new lint/import errors (no orphan
  `ICmObjectRepository` import).
- Committed on flexicon with `closes MattGyverLee/FlexToolsMCP#37`, CHANGELOG
  `[Unreleased]` + history.md updated.

## Reframe v2 (author pivot)

The line ~24 claim above ("the MCP-side Level-2 extractor override is a
genuine MCP fix and STAYS ... tracked separately on the MCP repo") is now
**superseded**. The author's north star is a single, explicit **behavioral
collection contract**: every `GetAll` returns something loopable/`len()`-able/
indexable/re-iterable, and the concrete return type (`EnumerableWrapper`,
`list`, or a `SmartCollection` subtype) is an implementation detail. Given
that, patching around a wrong docstring at the MCP extractor layer treats the
symptom, not the cause — the flexicon docstrings themselves should say
`Returns: <ContainerType>[<Element>]`, never `Yields: <Element>`, for any
method that doesn't have a genuine unwrapped-generator return (the Cycle-1
audit found none).

**Decision:** the MCP-side Level-2 extractor override described in the
original reframe is to be **dropped** — fix at the flexicon source instead.
Docstring standardization (Cycle 3, T7) is the canonical Defect-A fix. The
MCP repo should be told to remove/retire its override once this lands,
rather than carrying a permanent compensating shim for a documentation
defect that no longer exists upstream.

See `specs/getall-contract-flexicon/reviews/cycle3-lex-programmer.md` for the
full before/after docstring tally and verification detail.
