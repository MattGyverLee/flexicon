# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Future breaking changes go under `[Unreleased]` until the next version cut.

---

## [Unreleased]

## [4.4.1] - 2026-08-18

> Two production fixes to public methods that were broken outright, plus a
> type-stub correction. No breaking changes.

### Fixed
- **Seven `Duplicate()` methods rejected keyword arguments their own
  docstrings documented.** `AllomorphOperations`, `EtymologyOperations`,
  `NaturalClassOperations`, `WfiGlossOperations` and
  `WfiMorphBundleOperations` raised `TypeError: got an unexpected keyword
  argument 'deep'`; `LexEntryOperations` and `TextOperations` did the same for
  `insert_after`. Five of them already described a `deep` parameter in their
  `Args:` block that the signature never had -- the docstring was the
  published spec and the signature was the defect. Found on the first live run
  of `test_duplicate_operations.py`.

  Harmonised **additively** rather than by imposing one uniform signature.
  `CLAUDE.md`'s canonical shape is `Duplicate(item_or_hvo, deep=True)` with no
  `insert_after`, but most classes have `insert_after`, some genuinely need it
  (ordered owning sequences) and others cannot use it (unordered owning
  collections) -- so no single shape fits. Every `Duplicate()` now accepts
  **both** keywords, and a parameter that is meaningless for its type is
  accepted and documented as ignored. **No existing default and no existing
  behaviour changed**, so this is not a breaking change.

  Where a class already had `insert_after`, `deep=False` is appended -- `False`
  because it honestly describes the existing shallow behaviour. Where a class
  already had `deep`, `insert_after` is added **keyword-only**
  (`deep=True, *, insert_after=True`); the bare `*` is load-bearing, preserving
  positional compatibility for existing `Duplicate(obj, False)` callers.

  Closes #246.

- **The `.pyi` stubs lied about nearly every `Duplicate()`.** The stubs emitted
  one of two fabricated templates -- `(self, obj: Any, deep: bool = True)` or
  the fully untyped `(self, *args: Any, **kwargs: Any)` -- almost universally,
  while the real implementations vary along three independent axes. A caller
  who trusted a stub got a `TypeError`, which is worse than having no stub at
  all. 40 stub lines were rewritten from the real signatures and 4 fabricated
  ones deleted, for classes that define no `Duplicate()` and inherit none
  (`BaseOperations`, `InflectionFeatureOperations`, `LexReferenceOperations`,
  `SegmentOperations`).

  Note for whoever next regenerates stubs: `Duplicate` is wrapped by
  `OperationsMethod.__get__` in `BaseOperations`, so `inspect.signature()`
  reports `(project, *args, **kwargs)` for every one of them. That wrapper is
  where the bogus template came from. **Generate from the AST, not from
  `inspect`.**

- **`ILexEtymology.Source` does not exist in the installed LCM, so every
  etymology source method was broken.** Live reflection confirms the field is
  absent entirely -- `CLAUDE.md` and `docs/API_ISSUES_CATEGORIZED.md`
  "Category 8" were both **wrong** to list it as an `IMultiString`, and are
  corrected here. The real field is `LanguageNotes` (an `IMultiString`); the
  separate `LanguageRS` (a reference sequence onto the Languages list) is a
  distinct concept, not a rename.

  `EtymologyOperations.Create(source=...)`, `GetSource()`, `SetSource()`,
  `GetSyncableProperties()` and `ApplySyncableProperties()` now read and write
  `LanguageNotes`. The public surface is unchanged: `source=`, `GetSource()`,
  `SetSource()` and the `"Source"` dictionary key all keep their names, so no
  caller has to change. `Duplicate()`'s `hasattr(duplicate, "Source")` guard
  could never fire and was therefore **silently dropping the field on every
  duplicate**; it is now an unconditional `LanguageNotes` copy.

  `GetLanguage()` / `SetLanguage()` reference the equally absent `LanguageRA`
  and are deliberately **not** fixed here -- a separate bug, already recorded
  as `xfail`.

- **Two live tests were asserting against the wrong writing system.**
  `test_phonemes.py::TestPhonemeSync` matched a feature value by calling
  `GetAbbreviation(v)` with no explicit writing system, which resolves to the
  *project's* default analysis WS. The `PHON:fPAConsonantal` catalog only ever
  writes `Abbreviation` into `en`, and Sena 3's default analysis WS is `pt`,
  so the lookup was always empty and `next()` raised a bare `StopIteration`.
  The tests now match on the catalog's stable value GUID, following the
  existing pattern in `test_phon_features.py`. This is why the failure looked
  environment-dependent: the same tests pass against Target, whose default
  analysis WS is `en`.

- **`test_pronunciation_form_roundtrip` indexed a set.**
  `GetAllVernacularWSs()` / `GetAllAnalysisWSs()` are documented to return a
  `set`, and the test subscripted the result with `[0]`. It now uses
  `GetDefaultVernacularWS()` / `GetDefaultAnalysisWS()`, which additionally
  match the writing system the preceding `Create()` actually wrote to.

---

## [4.4.0] - 2026-08-18

> **The write path is now transactional.** This release contains a public-API
> default change; read the first entry under **Changed** before upgrading.
> Completes `specs/write-path-transactions`.

### Added
- **`FLExProject.AbortSession()`.** Task A3. Wraps `IActionHandler.Rollback(0)`
  to discard every uncommitted change made since the session's write envelope
  was opened, then reopens that envelope so the abort is non-terminal,
  repeatable, and safe to call from inside an `except:` block. Reopening is
  required (decision D8): `Rollback` leaves the handler's state machine in
  `ReadyForBeginTask`, which ends the `undoable=False` session envelope, and
  `CloseProject()` unconditionally calls `EndNonUndoableTask()` -- so a
  terminal abort would leave every abort followed by a broken close.

  Guards: a read-only project raises `FP_ReadOnlyError`; nothing open
  (`CurrentDepth == 0`) returns `False` rather than surfacing a raw
  `InvalidOperationException`; and `undoable=True` with a block open raises
  `FP_TransactionError` rather than rolling back underneath the owning
  `UndoableUnitOfWorkHelper`.

  Note that under the new 4.4.0 default this method is a near-no-op by design
  -- see the `OpenProject` entry under **Changed**. It is useful chiefly to
  callers who opt into `undoable=False`.

- **`flexicon.CAPABILITIES`.** Task B4. A module-level `frozenset` of
  capability tokens declaring what this build implements, so consumers such as
  FlexToolsMCP can feature-detect rather than version-sniff. This release ships
  all four tokens of section 3 of the write contract: `ui-injection`,
  `refresh-from-disk`, `per-operation-uow`, and `transaction-rollback`.

  Per decision D7 a token means "this build implements the capability", not
  "it is active in your session" -- two of the four are mode-dependent and
  deliver nothing to a caller who opts out with `undoable=False`. See
  `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md` section 3.

- **`guid=` on three more `Create()` methods.** `Agents.Create()`,
  `ReversalIndexes.Create()`, and `ReversalEntries.Create()` now accept an
  optional trailing `guid=` argument and route through the existing
  `BaseOperations._CreateWithGuid()` helper already used by eight other
  `Create()` methods. This lets a sync/migration tool preserve a source
  project's identity for agents, reversal indexes, and reversal entries
  instead of minting new GUIDs on every run.

  The parameter is trailing and defaults to `None`, so existing positional
  call sites are unaffected, and `guid=None` behaves exactly as before.
  Semantics match the established helper: a malformed GUID string raises
  `FP_ParameterError` before anything is written, and a GUID already in use
  logs a warning and falls back to a newly minted identity rather than
  raising -- the requested GUID is **not** preserved in that case, so callers
  that care must read `.Guid` back. Supplying a `guid` does not weaken any
  existing business rule: `ReversalIndexes.Create()` still raises
  `FP_ParameterError` when the writing system already has an index, and
  `ReversalEntries.Create()` performs no GUID-based deduplication.
  `Agents.Duplicate()` is unchanged and still always mints a new GUID.

### Changed
- **BREAKING (behavioural): `OpenProject(..., undoable=...)` now defaults to
  `True`.** Task DEF of `specs/write-path-transactions`, gated on decision D3.
  Previously every write-enabled session ran inside a single session-long
  `BeginNonUndoableTask()` envelope in which nothing rolled back: an exception
  raised mid-operation left every mutation applied before the failure sitting
  in the cache, to be written to disk by the next
  `SaveChanges()`/`CloseProject()` (#236). Under the new default each write
  runs inside its own named, nesting-aware LCM unit of work, so an exception
  escaping an operation reverts that operation, and the operation appears in
  FLEx's Ctrl+Z menu under its own label.

  No signature or call-site change is required. What changes underneath a
  caller who passes only `writeEnabled=True`:

  - Failed operations no longer leave partial writes behind.
  - Writes appear individually on the FLEx undo stack rather than not at all.
  - `AbortSession()` becomes a near-no-op: it returns `False` between
    operations and raises `FP_TransactionError` inside one (decision D8),
    because per-operation rollback covers the same ground. Callers relying on
    it to discard a whole partial batch must now pass `undoable=False`
    explicitly, or restructure around per-operation rollback.
  - `CustomFieldOperations.CreateField()` still always raises
    `FP_TransactionError`, but now for the other of its two reasons. Its
    `CurrentDepth > 0` guard no longer fires (the old session envelope held
    that depth at 1 all session; between operations it is now 0), so calls
    fall through to the unimplemented-no-UoW-path raise instead. Callers
    matching on the message text will see a different one; the behaviour
    (no custom field is created) is unchanged.
  - Nested blocks **join** the enclosing unit of work rather than opening an
    independent one. Catching an exception from an inner block while still
    inside the outer block therefore commits the inner block's partial
    writes -- see `docs/EXCEPTION_HANDLING.md`.

  To keep the previous behaviour, pass `undoable=False` explicitly. That path
  is retained, still warns once per `OpenProject()` call, and must not be used
  when the project may be open in FLEx or another process (D3).

  If your own code writes through the LCM **directly** rather than through a
  wrapper method (`agent.SetEvaluation(...)`, `sense.Source = ...`), it now
  needs its own `with project.UndoableOperation("..."):` block. Those writes
  used to be covered for free by the session envelope; under the new default
  nothing is open between operations and an unbracketed raw write raises
  `InvalidOperationException: Not in the right state to register a change.`

### Fixed
- **CRITICAL: every write under `undoable=True` was silently discarded.**
  Decision D9. `UndoableUnitOfWorkHelper.RollBack` is declared
  `{private get; set;}`, so pythonnet synthesizes no property for it and
  surfaces only `set_RollBack`. The assignment form `helper.RollBack = False`
  therefore does **not** raise -- pythonnet accepts it as a plain Python
  attribute on the wrapper object while the real .NET field keeps its
  constructor default of `True`. `Dispose()` consequently rolled back *every*
  unit of work, successful ones included, so under `undoable=True` no write
  ever reached the project. Both call sites now use `set_RollBack(...)`.

  This was invisible offline, because the test doubles had encoded the same
  bug: 30 tests passed against code that destroyed all data live. Both doubles
  now raise on the assignment form, and a source-level guard keeps the
  assignment form from reappearing.

- **`_NestingAwareTransaction` rewritten on `UndoableUnitOfWorkHelper`**
  (#233, #234). The hand-rolled `_transaction_depth` counter is deleted
  outright; every `__enter__` now asks liblcm's own
  `ActionHandlerAccessor.CurrentDepth`, following
  `UndoableUnitOfWorkHelper.DoUsingNewOrCurrentUOW`'s join-or-open idiom
  verbatim. The `undoable=True` phase constructs `UndoableUnitOfWorkHelper`
  directly and is genuinely rollback-capable; the `undoable=False` phase is
  unchanged. All 174 `with self._TransactionCM(...)` call sites keep working
  unedited.

  `_FLExUndoableOperation` is rewritten on the same idiom, since it shared the
  one-argument `BeginUndoTask` call that was #233 -- that method needs both
  undo *and* redo text, not a single label. `FLExProject._GetUndoRedoAPI`, the
  discovery layer that produced the bad call, is deleted.

- **`FLExProject.Undo()` / `Redo()` no longer reference a non-existent
  attribute** (#235). Both now read `LcmCache.ActionHandlerAccessor` -- the old
  `self.project.UndoStack` did not exist at all -- and both gate on
  `CanUndo()` / `CanRedo()`, since calling into an empty stack throws rather
  than returning a status. The dead `if undo_stack is None` / `else` branches
  are removed.

  **Scope caveat, now stated in both docstrings:** liblcm's undo stack lives in
  RAM and is never serialized into `.fwdata`, so undo/redo is in-process only.
  A reopened project always starts with `CanUndo()` returning `False`.

- **Writes now persist across `CloseProject()` under `undoable=True`** (#237),
  covered by a live-project test on the Target (task B2t).

- **47 mutation sites that were running outside any unit of work are now
  bracketed.** Found by the DEF default flip, which turned a latent gap into a
  visible failure. They were missed by the original 295-site sweep because its
  scanner recognised a mutation only as a call from a hardcoded name list or an
  assignment to a property ending `RA`/`OA`/`OS`/`RS`. Three classes fell
  outside both:

  - **43 unsuffixed scalar property writes** across 22 files — `Senses.SetSource`,
    `SetScientificName`, `SetImportResidue`, `LexEntry.SetHomographNumber`,
    `SetDoNotUseForParsing`, `SetExcludeAsHeadword`, `WritingSystems.SetFontName`
    / `SetFontSize` / `SetRightToLeft`, `Wordforms.SetSpellingStatus`,
    `Segments.SetBaselineText` / `ReparseParagraph` / `SetIsLabel`,
    `Texts.SetIsTranslated`, and others. ITsString, Unicode, bool, int and
    GenDate properties carry no ownership suffix, so none of them ever counted.
  - **3 `ISilDataAccess` scalar setters** — `FLExProject.LexiconSetFieldInteger`,
    `LexiconSetListFieldSingle`, `LexiconClearListFieldSingle`
    (`SetInt` / `SetObjProp`).
  - **1 LCM domain mutator** — `WfiAnalyses.SetApprovalStatus`, which reaches
    `ICmAgent.SetEvaluation`.

  Under `undoable=False` these were invisible (the session envelope covered
  them); under the new default each raised
  `InvalidOperationException: Not in the right state to register a change.`
  The mutation scanner now recognises all three shapes, so the guard measures
  the codebase rather than its own name list.

- **`BaseOperations.ApplySyncableProperties` now runs inside a unit of work.**
  Its writes live in a module-level helper, so no per-method sweep reached
  them. The whole property loop is bracketed as one unit, so a sync that fails
  partway cannot leave the target item half-updated.

- **`project.Senses.GetPartOfSpeechObject()` no longer returns `None` for every
  sense.** The method read `getattr(msa, "PartOfSpeechRA", None)` off the base
  `IMoMorphSynAnalysis` interface, where that property is not declared, so it
  silently returned `None` even for ordinary stem and inflectional senses with
  a perfectly valid part of speech. It now delegates to `get_pos_from_msa()`,
  which casts to the concrete MSA subtype first: `MoStemMsa`, `MoInflAffMsa`,
  `MoDerivAffMsa`, and `MoUnclassifiedAffixMsa` all now return their POS
  correctly. For `MoDerivAffMsa`, the value returned is the output category
  (`ToPartOfSpeechRA`), matching what `SetPartOfSpeech()` already writes for
  that subtype (#87 precedent), so get/set round-trips as expected. A sense
  with no MSA still returns `None` silently (unchanged contract); a sense
  whose MSA has an unrecognized `ClassName` now returns `None` and logs a
  warning naming the sense `Hvo` and the `ClassName`, so that gap is
  discoverable rather than indistinguishable from "no POS set" (#232).
  `GetPartOfSpeech()` (the string getter, which uses `InterlinearAbbr`) was
  not affected and is unchanged -- `InterlinearAbbr` is declared on the base
  interface.

- **The offline test suite is green again: 117 failures and 17 errors down to
  zero.** All of it was fallout from the `flexlibs2` -> `flexicon` rename plus
  two mismarked test modules; no production behaviour was at fault except where
  noted below.

  - **Source-inspection tests were silently vacuous.** Roughly thirty tests
    across nine files `read_text()` a source file and assert on its contents,
    but still named `flexlibs2/code/...`. Where the path was a single file they
    died with `FileNotFoundError`; where it was an `rglob` root they passed by
    iterating zero files, which is worse. All are repointed at `flexicon/code`.
    Two of them then reported genuine false positives on first real execution
    and were repaired, not deleted: the factory/`GetService` guard now exempts
    a shared helper handed an already-resolved `factory`, and the LCM
    collection-method regex no longer matches the all-caps `POS` facade
    attribute merely because it ends in the letters "OS".
  - **Two modules opened live FLEx projects without the
    `requires_live_project` marker**, so they ran under the offline selector
    and crashed `FLExInitialize` with a Windows access violation --
    `flexicon/sync/tests/test_duplicate_operations.py` (86 of the failures, on
    Sena 3) and `flexicon/tests/test_CustomFields.py`. Both are now marked.
    `test_duplicate_operations.py`'s `tearDownModule()` also called
    `FLExCleanup()` without importing it, which would have raised `NameError`
    on its first successful live run.
  - **Mock-fidelity bugs in the sync test doubles.** A bare `Mock()`
    auto-vivifies any attribute, which defeats the `hasattr()` checks in
    `sync/validation.py` and `sync/diff.py` that exist precisely to detect
    "this LCM object does not have this attribute" -- so the code went on to
    `len()` and iterate Mocks it had never been given values for. The doubles
    now stub the attributes each code path touches and use `spec=` where the
    real operations class has a narrower surface.

- **Ten `Duplicate()` and related crashes fixed, all of the same shape.** Marking
  `flexicon/sync/tests/test_duplicate_operations.py` as a live test made it
  execute for the first time in a long while, and it went from 69 failed / 27
  passed / 16 errors to **112 passed, 0 failed, 0 errors** against a restored
  Sena 3. Almost every failure was `CLAUDE.md`'s "Category 8" trap -- a property
  declared on a *concrete* LCM type being read off a *base* interface -- or a
  field that has since moved or vanished:

  - `AllomorphOperations.Duplicate()` read `PhoneEnvRC` off base `IMoForm`; now
    casts to the concrete `IMoStemAllomorph` / `IMoAffixAllomorph` first.
  - `ParagraphOperations.__GetParagraphObject()` cast to `IStTxtPara` on its HVO
    branch but returned the raw `IStPara` unchanged on its already-an-object
    branch. The two branches now agree, which alone fixed most of the
    paragraph and text failures.
  - `NaturalClassOperations.Duplicate()` read `SegmentsRC` off base
    `IPhNaturalClass`; now casts to `IPhNCSegments`.
  - `WfiGlossOperations.Duplicate()` did not cast its owner to `IWfiAnalysis`,
    though `Delete()` in the same class already did.
  - `PhonemeOperations.Duplicate()` (`BasicIPASymbol`) and
    `LexSenseOperations.__copy_sense_content()` (`ILexExampleSentence.Reference`)
    called `.CopyAlternatives()` on fields that are single-writing-system
    `ITsString`, not `IMultiString`. Both now reference-share the immutable
    `ITsString`, matching the pattern this codebase already uses for
    `Source` / `ScientificName` / `ImportResidue` (#31, #93). **`Senses.Duplicate(deep=True)`
    was raising `AttributeError` for any sense carrying an example sentence.**
  - `WfiAnalysisOperations.Duplicate()` and `WordformOperations`' deep-copy loops
    referenced `IWfiMorphBundle.Gloss`, which does not exist.
    `WfiMorphBundleOperations.Duplicate()` already carried this fix; these were
    the missed sibling sites.
  - `NoteOperations`: `Source` is now `SourceRA` (a reference, not text);
    `Create()` raised `NullReferenceException` for any owner without
    `AnnotationsOC` and now falls back to the language project's collection;
    and `Delete()` double-deleted, because removing an object from an owning
    collection already deletes it.
  - `LexEntryOperations.Duplicate()` passed `create_blank_sense=(not deep)`,
    so a *shallow* duplicate acquired a spurious blank sense -- contradicting
    the method's own documented example.
  - `lcm_casting.py` gains `LangProject` in its ClassName-to-interface registry.

- **`ILexEtymology.Source` does not exist in the installed LCM.** Confirmed by
  live reflection. `EtymologyOperations.Duplicate()` now guards the copy with
  `hasattr` rather than guessing at a replacement field. Note that `GetSource()`,
  `SetSource()` and `Create()` on the same class are broken by the same missing
  field and are **not** fixed here -- and that `CLAUDE.md` and
  `docs/API_ISSUES_CATEGORIZED.md` Category 8 are stale on this point, both
  still listing `Source` as an `IMultiString` on `ILexEtymology`.

- **`SelectiveImport._exists_in_target()` no longer propagates unexpected
  lookup failures.** It caught only `(AttributeError, KeyError)` while every
  other `except` in the same file catches broad `Exception` and logs. A
  `project.Object(guid)` lookup goes through pythonnet into the live LCM and
  can raise other types (malformed GUID, backend errors); this is a boolean
  existence check, so any failure now means "not found" and is logged, rather
  than aborting the caller's candidate scan.

### Known limitations

Stated rather than papered over:

- **A single whole-suite live run has never completed, in either mode.** It
  hangs at the same point on the unmodified pre-4.4.0 tree, so it is
  pre-existing and not caused by this work -- but "the entire live suite is
  green in one process" is not a claim this release makes. Running the suite
  one file at a time completes cleanly and is the supported way to execute it.
- **The broad live suite still runs `undoable=False` by design** (decision
  D12), so continuous coverage of the new default rests on the DEF-COV suite
  plus the module-scoped fixtures that pin no mode.
- **`SaveChanges()` cannot succeed under `undoable=False`,** and the failed
  save also rolls back the session's uncommitted work. Pinned by
  `TestSaveChangesIsUnusableInThisMode`, which asserts the current broken
  behaviour and must be inverted when it is fixed.
- **`ReversalIndexOperations.Create()` stores an int writing-system handle as a
  stringified int,** breaking the entry path's own writing-system resolution.
  Pre-existing, surfaced incidentally by the `guid=` work, and sidestepped in
  the tests with an explicit `wsHandle=`.
- **`Duplicate()` signatures are inconsistent across the codebase,** and the
  `.pyi` stubs are wrong about nearly all of them. The stub generator emits
  `(obj, deep: bool = True)` or a fully untyped `(*args, **kwargs)`, while the
  real implementations vary in whether they take `insert_after`, whether they
  take `deep`, and what those default to. A caller trusting a stub can get a
  `TypeError`. Catalogued in `reports/audit/duplicate-signature-audit.md`; no
  signature was changed, because harmonising them is a breaking API change that
  deserves its own deliberate release.
- **Only `LexSenseOperations` was live-verified against every branch of its
  duplicate path.** The other operations classes in the sweep above were
  verified by the `test_duplicate_operations.py` suite, which does not exercise
  every field of every type.
- **`TextOperations` calls `IText.Source.CopyAlternatives()`,** but the field
  table says the real `Source` lives on `IStText`, not `IText`. Possibly a
  silent no-op rather than a crash. Flagged, not touched.
- **`flexicon/tests/test_CustomFields.py` needs a `__flexlibs_testing`
  project** that is not part of either checked-in fixture project. It is now
  correctly gated behind `requires_live_project`, and skips rather than
  crashing where that project is absent.

---

## [4.3.1] - 2026-08-13

### Fixed
- **`project.Agents.GetVersion()` / `SetVersion()` no longer treat
  `ICmAgent.Version` as multilingual.** `Version` is a monolingual `Unicode`
  property in the LCM model (unlike `ICmAgent.Name`, which is `MultiUnicode`),
  so pythonnet surfaces it as a plain Python `str`. Both accessors routed it
  through `get_String()` / `set_String()` / `TsStringUtils.MakeString()`,
  raising `AttributeError: 'str' object has no attribute 'get_String'` on
  every call and leaving parser-agent versions unreadable and unwritable.
  `GetVersion` now returns `agent.Version or ""` and `SetVersion` assigns
  `agent.Version` directly.

### Changed
- The `wsHandle` parameter on `Agents.GetVersion()` / `Agents.SetVersion()` is
  now accepted but **ignored**, and documented as such. It is retained for
  signature compatibility only -- a monolingual property has no
  per-writing-system alternative to select. No caller changes are required.

---

## [4.3.0] - 2026-07-22

### Added
- **`SegmentOperations` `AnalysesRS` write API**: new `SetAnalysis`,
  `ReplaceAnalysis`, `InsertAnalysis`, `AppendAnalysis`, and `RemoveAnalysis`
  methods on `ISegment.AnalysesRS`, bringing segment-level analysis-list
  mutation in line with the existing `SetFreeTranslation` support (#215).
- **`project.MSA.RemoveOrphaned(entry=None, progress=None)`**: project-wide
  `WfiMorphBundle`-aware MSA orphan cleanup. Returns a structured
  `RemoveOrphanedResult` describing what was removed, scoped to a single
  entry when `entry` is supplied (#206).

### Fixed
- **`LCMObjectWrapper` exposes `lcm_object` / `AsICmObject()`** so wrapper
  objects returned by the API can be cast back to LCM interfaces from user
  scripts; fixes a runtime crash that occurred when user code attempted to
  cast a wrapper directly (#199).
- **`.pyi` stub `GetAll`/`GetAll*` return annotations** across ~40 Operations
  stub files no longer collapse to a blanket `Iterator[Any]`. Each method is
  now annotated with the concrete behavioral-collection shape it actually
  returns per `docs/getall-contract.md`: `EnumerableWrapper[T]`, `list[T]`
  (spelled `List[Any]` for stub compatibility), or a `SmartCollection[T]`
  subtype (`RuleCollection`, `CompoundRuleCollection`,
  `AffixTemplateCollection`, `AllomorphCollection`). `BaseOperations.pyi` now
  declares `EnumerableWrapper` as a proper `Generic[T]` stub class with typed
  `__iter__`/`__len__`/`__getitem__`/`Count`, instead of leaving it
  unshadowed-but-untyped. `BaseOperations.GetAll`'s own declared return type
  changed from `Iterator[Any]` to `Any` -- none of the three real shapes is
  an `Iterator` (no `__next__`), so `Iterator[Any]` at the base would make
  every subclass override an LSP violation under a strict checker.
- **Stale/orphaned `.pyi` paths.** `AllomorphOperations.pyi`,
  `FilterOperations.pyi`, and `MediaOperations.pyi` were shadow-stubbed at
  their pre-refactor locations (`Grammar/`, `TextsWords/`) which no longer
  match the real modules (`Lexicon/`, `Shared/`); a type checker resolving
  those modules got no stub coverage at all. Relocated to match the real
  module paths.
- **Fabricated `GetAll`/`GetAll*` overrides removed or corrected** for
  classes whose stub asserted a per-class `GetAll` override that does not
  exist in the runtime implementation (`InflectionFeatureOperations`,
  `ProjectSettingsOperations`, `PossibilityListOperations`,
  `CheckOperations`, `CustomFieldOperations`, `DiscourseOperations`) --
  these either inherit `GetAll` from a base class or only define a
  `GetAll*`-named sibling method. Also dropped `LexEntryOperations.pyi`'s
  fabricated `GetAllomorphs` stub method, which does not exist in
  `LexEntryOperations.py`.
- **Missing `GetAll*` sibling methods added to stubs** (previously absent
  entirely, so any call site fell through the class's blanket
  `__getattr__ -> Any`): `GetAllCompoundRules`, `GetAllAffixTemplates`,
  `GetAllAffixTemplatesForPOS`, `GetAllAdhocCoProhibitions`,
  `GetAllByMorphType`, `GetAllSenses` (both `LexEntryOperations` and
  `LexSenseOperations`), `GetAllTypes` (`LexReferenceOperations` and
  `VariantOperations`), `GetAllLists`, `GetAllRecordTypes`,
  `GetAllStatuses`, `GetAllCheckTypes`, `GetAllFields`, `GetAllCharts`,
  `GetAllForms`, `GetAllWithStatus`, `GetAllUnapproved`, `GetAllByType`.
  Each now has the real method's parameter signature (positional args and
  defaults) instead of a blanket `*args: Any, **kwargs: Any`, resolving the
  pre-existing signature drift noted as a prerequisite in the original T10
  assessment.
- **`MediaOperations.GetAll`** now enumerates `ICmFileRepository` directly
  instead of the incorrect `ICmObjectRepository` cast, and its docstring now
  states the caveat that repository enumeration returns every `ICmFile` in
  the database (pronunciation media, external-link files, orphans included),
  which is broader than walking `LangProject.MediaOC`/`PicturesOC` folders.
- **`AgentOperations.GetAll`** now carries the `@OperationsMethod` decorator
  it was missing, matching every other `GetAll` in the codebase.
- **`TranslationTypeOperations.GetSegmentsWithType`** now raises
  `NotImplementedError` instead of silently returning `None`. `ISegment`
  translations have no typed link to a translation-type possibility the way
  text-level translations do, so the method could never do what its name
  promised; it now fails loudly and points callers at `GetTextsWithType()`.

### Deferred (documented, not fixed in this pass)
- Three whole Operations packages (`Discourse/`, `Reversal/`, `Scripture/`)
  have **no `.pyi` stubs at all** -- a pre-existing gap outside this issue's
  scope (adding a new stub tree, not reconciling an existing one).
- The non-`GetAll` methods on every stub (`Find`, `Create`, `Delete`, etc.)
  still use the blanket `*args: Any, **kwargs: Any -> Any`/`__getattr__`
  pattern; only `GetAll`/`GetAll*` methods were reconciled in this pass, per
  the issue's stated scope.

### Changed
- **Build:** the package version is now a single source of truth. `pyproject.toml`
  declares `dynamic = ["version"]` and reads it from the `flexicon.version`
  attribute via `[tool.setuptools.dynamic]`, so the distribution version and the
  runtime `flexicon.version` can no longer diverge (the root cause of the 4.2.0
  stale-version issue). Requires `setuptools>=77` (already pinned in
  `[build-system]`).

### Docs
- **`GetAll`/`GetAll*` collection-return contract**: standardized ~51
  docstrings across ~50 `flexicon/code/**/*Operations.py` files to a
  consistent `Returns:\n    <ContainerType>[<Element>]: ...` form, dropping
  `Yields:` generator-style wording (the `@wrap_enumerable` decorator always
  converts generator bodies to a re-iterable `EnumerableWrapper` before the
  caller sees them, so `Yields:` misdescribed the actual contract).
  `BaseOperations.wrap_enumerable`'s docstring gains a "Behavioral
  collection contract" paragraph explaining the three concrete return
  shapes (`EnumerableWrapper[T]`, `list[T]`, `SmartCollection[T]`
  subtypes) and the loop/`len()`/index/re-iterate guarantee they all
  satisfy. New `docs/getall-contract.md` documents the full guarantee;
  `README.rst` links to it.

---

## [4.2.1]

### Fixed
- **Runtime version string:** bumped the `flexicon.version` attribute in
  `flexicon/__init__.py`, which was left at `4.1.2` during the 4.2.0 cut so
  the published 4.2.0 wheel reported a stale runtime version. Now matches the
  distribution version.

---

## [4.2.0]

### Added
- **`MsaFactoryOperations.CreateStem` / `CreateUnclassifiedAffix`** now
  accept `pos=None` for a category-less stem or unclassified-affix MSA
  (a valid, blank-category-cell FLEx state), mirroring the existing
  `CreateDerivAff` `to_pos=None` precedent. Unblocks cross-project
  transfer of category-less MSAs (9c04ab8).

### Fixed
- **`MsaFactoryOperations.CreateInflAff`** accepts `pos=None` for a
  category-less inflectional affix, matching `CreateStem` /
  `CreateUnclassifiedAffix` (6f316b3).
- **Morph-type classification** unified into a single shared module
  (`Shared/morph_type_utils.py`); `LexEntryOperations`,
  `AllomorphOperations`, and `LexSenseOperations` no longer each carry
  independently drifting stem/affix GUID sets. Fixes a silent logical
  inversion in `LexSenseOperations.__EntryHasAffixMorphType`'s GUID set.
  `MorphRuleOperations.Duplicate` now defaults `deep=True`, matching the
  LexEntry/Text family (#203, #213, #214).
- **`wrap_enumerable`** now catches bare Python iterators/generators (not
  just raw C# `IEnumerable`), so `GetAll()`/`GetAnalyses()`-style methods
  across ~20 Operations classes reliably return a subscriptable,
  `len()`-able collection instead of raising `TypeError` on `entries[0]`
  or `len(entries)` (#201).
- **`MediaOperations.Create`** now owns a new `CmFile` in the appropriate
  `CmFolder` before setting `InternalPath`, fixing a
  `NullReferenceException` that made the add-a-picture/media surface
  (`AddPicture`, `CopyToProject`, `Create`, `AddMediaFile`) unusable.
  `CopyToProject`'s `LinkedFilesRootDir` guard now reads from `ILangProject`
  instead of the `LcmCache` (#226).
- **`GetCustomFieldValue`** on a bare `ITsMultiString` (no
  `BestAnalysisVernacularAlternative` accessor) now resolves the best
  alternative by writing-system priority instead of failing (#224).
  Transaction entry no longer logs a misleading "NoneType is not
  callable" warning when the LCM `Mark` API is unavailable; it logs at
  debug level and proceeds without rollback capability (#221).
- **`BaseOperations._ValidateParam`** guards against stale/deleted LCM
  objects (`IsValidObject is False`), raising `FP_ParameterError` naming
  the parameter instead of an opaque `NullReferenceException` deep
  inside LCM (#205).
- **`SegmentOperations.GetAnalyses`** / `WfiGlossOperations` — polymorphic
  `IAnalysis` tokens (`IWfiWordform` / `IWfiAnalysis` / `IWfiGloss` /
  `IPunctuationForm`) are now resolved by `ClassName` rather than
  `isinstance`, which is unreliable against base-typed LCM refs. Adds
  `SegmentOperations.GetGloss`, `WfiAnalysisOperations.GetCategoryAbbrev`,
  and `GetMorphemeBundles` polymorphic helpers (#212).

### Changed
- **`FLExProject`** singular/plural accessor aliases (e.g.
  `InflectionFeature`/`InflectionFeatures`) are now generated from a
  single table (`_op_aliases.py`, 58 aliases) instead of ~10 hand-written
  properties, closing the gap where a guessed accessor name raised
  `AttributeError`. All previously hand-written aliases are preserved;
  each now emits a `DeprecationWarning` naming the canonical accessor
  (#200).

---

## [4.1.2]

### Fixed
- **Grammar sync:** hardened `Phoneme` synchronization and corrected
  `GetSyncableProperties` in `Phoneme`/`Environment` to distinguish mono
  `ITsString` fields from multi-string fields, preventing type-mismatch errors
  during sync (#222).

### Added
- Syncable-properties support for `PhonFeatures`.

### Changed
- Documentation build pipeline updates: Sphinx configuration, `make.bat`, a
  gh-pages publish workflow on the self-hosted FieldWorks runner, and
  Context7-scoped docs.

---

## [4.1.0]

### Changed
- **Renamed the library from `flexlibs2` to `flexicon`** (distribution name on
  PyPI: `pyflexicon`). flexicon is now maintained as an independent successor
  to cdfarrow/flexlibs rather than a fork; it no longer tracks the upstream
  codebase. Original LGPL-2.1 attribution (Craig Farrow) is retained in
  `LICENSE.txt` / `NOTICE`.
- Packaging consolidated to a single `pyproject.toml` (removed `setup.cfg`);
  corrected the license metadata from `GPL-2.0-or-later` to the actual
  `LGPL-2.1-or-later`.

### Added
- `flexlibs2` compatibility alias: `import flexlibs2` (and deep submodule
  imports such as `flexlibs2.code.lcm_casting`) transparently resolve to the
  identical `flexicon` objects via a meta-path finder, so existing FlexTools /
  FlexTrans scripts keep working. Emits a `DeprecationWarning`.

### Deprecated
- The `flexlibs2` import alias is deprecated and will be **removed in v5.0.0**.
  Update imports to `flexicon`.

---

## [4.0.1] - 2026-06-30

### Fixed

- **`LexEntryOperations.GetComplexFormsNotSubentries`** — none-guard the
  `sense.OwnerOfClass(LexEntryTags.kClassId)` cast. When `OwnerOfClass`
  returns `None` (orphaned sense or test-double context), the unconditional
  `ILexEntry()` cast raised `TypeError`; now returns an empty result,
  mirroring the safer cast pattern already used elsewhere in that file.
  (66b8eb3)

- **`sync/tests/test_base_operations.py`** — corrected a stale import from
  the nonexistent `flexlibs2.flexlibs` module (v1 leftover). The bad import
  raised `ModuleNotFoundError` at collection time and aborted the entire
  pytest session. Corrected to import from the package root `flexlibs2`.
  (742b9b4)

- **`SemanticDomainOperations.GetSubdomains`** — yield `ICmSemanticDomain`
  (typed cast) instead of the base `ICmPossibility` object, for both the
  fast path and the recursive walk.

- **`LocationOperations.GetSublocations`** — yield `ICmLocation` (typed
  cast) for both fast path and recursive walk.

- **`InflectionFeatureOperations.InflectionClassGetAll`** — yield
  `IMoInflClass` (typed cast) instead of the raw base-interface object.
  These three close the Category 5 cast-on-yield gaps. (92762fa)

- **`ProjectSettingsOperations`** — added LCM-backed accessors:
  `GetProjectGuid`, `GetProjectDescription`, `GetExternalLink`,
  `GetAnalysisWritingSystem`, `GetVernacularWritingSystem`. Both WS getters
  return `None` safely when `project.lp` is unavailable. (92762fa, fd156ee)

- **`ReversalIndexEntryOperations.__GetEntryWS`** — raises
  `FP_ParameterError` (naming `entry.Hvo`) when `entry.ReversalIndex` is
  `None`, replacing the `NullReferenceException` that previously surfaced
  during reversal cleanup of orphaned or cascade-deleted entries
  (Category 7). (fd156ee)

### Tests

- **Grammar live tests** (phon-feature, natural-class, phon-rule) refactored
  as self-restoring round-trips. Removed top-of-test pre-clean calls that
  masked incremental failures; each test now follows create -> assert ->
  delete -> assert-gone so a failed test leaves evidence rather than being
  silently swept. 18 tests verified to pass twice back-to-back without a
  DB restore in between. (ddbfe3c)

### Docs

- **`docs/API_ISSUES_CATEGORIZED.md`**: Category 5 marked RESOLVED;
  Category 4 / ProjectSettings table updated to reflect new accessors;
  Category 7 reversal NullReferenceException entry updated with the
  `__GetEntryWS` null-guard fix; additional latent-gap notes added to
  Category 3. (a1d4bb3, 57ed7a0)

---

## [4.0.0] - 2026-06-23

### Changed (Breaking)

- **`flat=` parameter renamed to `recursive=` (inverted semantics) on every hierarchical-list `GetAll()` accessor.** Collection queries default to `recursive=True` (returns every descendant). Passing `flat=` raises `TypeError`. Affected modules:
  - `POSOperations.GetAll`, `LexSenseOperations.GetAll`, `SemanticDomainOperations.GetAll`,
    `AnthropologyOperations.GetAll`, `LocationOperations.GetAll`,
    `PublicationOperations.GetAll`, `PossibilityListOperations.GetAll`,
    plus the inline `GetSubcategories` / `GetSubdomains` / `GetSubitems` helpers.
  - `FLExProject.GetAllSemanticDomains` now also raises `TypeError` on `flat=` (the one-release deprecation shim has been removed).
- **`include_subcategories=` parameter renamed to `recursive=`** on `LexEntryOperations.GetAvailableMorphTypes`. Same semantics, more consistent naming.
- **Counting queries default to `recursive=False`** (FLEx UI parity). `POSOperations.GetEntryCount` was briefly flipped to `recursive=True` in d423e83 and reverted by #101 to match every count column in FLEx's UI (Categories tool, Lexicon Browse, Tools > Statistics — all direct-tag only). `SemanticDomainOperations.GetSenseCount` now accepts the same `recursive=` parameter (default `False`), so caller code looks identical across all `Get*Count` methods. Pass `recursive=True` when you actually want the descendant roll-up.

### Fixed

#### LCM Owner Typing — Pattern A Sweep (2026-05-30)

- **14 raw `Owner` return sites converted to typed casts** across 10 files in
  the Lexicon and TextsWords modules. Untyped `Owner` references silently
  produced wrong parent relationships in `Duplicate` operations and returned
  objects that callers could not navigate without manual casting. All 14 sites
  now cast to the correct interface (e.g. `ILexEntry(obj.Owner)`,
  `ILexSense(obj.Owner)`). (closes #166, closes #168, closes #159)
  - Affected: ExampleOperations, VariantOperations, PronunciationOperations,
    LexReferenceOperations, LexSenseOperations, WfiAnalysisOperations,
    WfiGlossOperations, WfiMorphBundleOperations, SegmentOperations,
    ParagraphOperations

#### API Documentation — Category 8 Correction (2026-05-30)

- **`docs/API_ISSUES_CATEGORIZED.md` Category 8 corrected.** The `Source` field
  row previously listed `ICmBaseAnnotation` as the owner; the field actually
  lives on `IStText`. The stale `ICmBaseAnnotation.Source` is unused dead
  interface; any code relying on it would silently return nothing. Row updated
  to reflect the correct `IStText.Source` owner. (closes #173)
- **`ISegment.BaselineText` entry added** to Category 8. Documents that this is
  an `ITsString` single-WS read-only computed property (backed by
  `IStTxtPara.Contents`) and that writing must go through the
  `Contents`/`ContentsSideEffects`/`AnalysisAdjuster` chain, not direct segment
  assignment.

#### SegmentOperations BaselineText — Partial Fix (2026-05-30, refs #172)

- **`SetBaselineText` write idiom corrected.** Was attempting direct segment
  mutation; now uses `para.Contents.GetBldr().ReplaceTsString(begin, end,
  new_run)` + `para.Contents = bldr.GetString()`, which fires
  `ContentsSideEffects` and lets `AnalysisAdjuster.AdjustAnalysis` maintain
  segment consistency.
- **`GetSyncableProperties` BaselineText read corrected.** Was calling
  `GetMultiStringDict` on an `ITsString` (type mismatch). Now reads the WS
  handle via `bt.get_Properties(0).GetIntPropValues(1, 0)[0]`, verified against
  a live Sena 3 project.
- **Defensive `None` guard** added in `SetBaselineText`; raises
  `FP_ParameterError` on null paragraph.
- **`DeprecationWarning` silenced** in three `SplitSegment`/`MergeSegments`
  internal callers that were passing a deprecated `ws` argument to
  `GetBaselineText`.
- 7 new regression tests (`TestGetSyncablePropertiesBaselineText`) added to
  `tests/test_segment_baseline_text.py`.
- Note: 5 entangled methods (Create, Duplicate, SplitSegment, MergeSegments,
  RebuildSegments) still manually mutate `SegmentsOS`; these require
  architectural rework tracked at #174. **#172 remains open.**

---

## [3.0.0] - 2026-04-07

### Breaking Changes

#### Reversal API Removed (GROUP 6)
- **`project.Reversal` API entirely removed** — 1,343 LOC deleted.
  Migrate to `project.ReversalIndexes` and `project.ReversalEntries`.
  See [docs/REVERSAL_API_MIGRATION.md](docs/REVERSAL_API_MIGRATION.md) for the full per-method table and code examples.
  - `project.Reversal.GetAllIndexes()` → `project.ReversalIndexes.GetAll()`
  - `project.Reversal.GetAll(index)` → `project.ReversalEntries.GetAll(index)`
  - `project.Reversal.GetForm(entry)` → `project.ReversalEntries.GetForm(entry)`
  - `project.Reversal.SetForm(entry, text)` → `project.ReversalEntries.SetForm(entry, text)`
  - `project.Reversal.Create(index, form, ws)` → `project.ReversalEntries.Create(index, form, ws)`

#### Lists Consolidation (GROUP 8)
- **`AgentOperations`, `PublicationOperations`, `TranslationTypeOperations`, and `OverlayOperations`
  now inherit from `PossibilityItemOperations`** instead of duplicating CRUD methods.
  Most caller code is unchanged; see [docs/RELEASE_v3_0_0.md](docs/RELEASE_v3_0_0.md) for full details.
  Known follow-up issues: `AgentOperations` (#54) and `OverlayOperations` (#149) have partial
  parent-class fit problems; some inherited methods may not function correctly.

### Changed
- Net -3,686 LOC since v2.4.0 (6,583 deletions, 2,897 additions) from deprecated-code removal.

---

## [2.4.0] - 2026-03-22

### Added

#### Transaction & Undo/Redo Framework (MAJOR)
- **Safe Transaction Rollback** - Phase 1 implementation for safe undo/redo operations
  - Automatic transaction state tracking
  - Rollback recovery for failed operations
  - Integration with FieldWorks LCM transactions
  - Comprehensive testing guide in docs/TESTING_UNDO_REDO.md

#### Security Enhancements
- **Write-Enable Guards** - 7 untagged mutating methods now protected
  - Prevents accidental modifications in read-only mode
  - `_EnsureWriteEnabled()` guards on all mutation points
  - Protects data integrity across all Operations classes

#### Pre-commit Hooks & Quality Control
- Custom decorator validator prevents duplicate decorators
- Black code formatting enforcement
- Flake8 linting (unused imports, complexity)
- Detect-secrets for credential detection
- Setup documentation in docs/PRE_COMMIT_SETUP.md
- Decorator checking script in scripts/check_decorators.py

### Fixed

#### Decorator Bugs
- **Duplicate `@OperationsMethod` decorators** - Fixed `'OperationsMethod' object is not callable'` errors
  - BaseOperations.py: Removed duplicates from 9 reordering/sync methods
  - POSOperations.py: Removed duplicates from 17 methods (including GetAll)
  - LexEntryOperations.py: Removed duplicates from 5 methods
  - All 64 operation files verified clean

### Documentation

#### New Guides
- **TESTING_UNDO_REDO.md** - Comprehensive undo/redo testing strategy and examples
- **TRANSACTION_GUIDE.md** - Transaction management and error recovery patterns
- **CONTRACT_TESTING.md** - LibLCM contract testing for API compatibility

### Tested Against

- LibLCM Contract Test Suite - Validates API compatibility across versions
- Unit tests for undo/redo implementation
- Pre-commit hooks prevent regression

### Breaking Changes

None. Fully backward compatible with v2.3.x APIs.

---

## [2.3.0] - 2026-02-28

### Added

#### Extended Wrapper Classes
- **Allomorph**: Wrapper for allomorph variants and forms
  - Form and gloss access with normalization
  - Environment context tracking
  - Variant relationship management

- **CompoundRule**: Wrapper for compound rule definitions
  - Rule component access
  - Directional compound rules
  - Integration with morpheme inventories

- **AdhocProhibition**: Wrapper for morphosyntactic prohibitions
  - Prohibited morpheme combinations
  - Context-aware blocking rules
  - Exception handling

- **Annotation**: Wrapper for project annotations and notes
  - Annotation type identification
  - Content and metadata access
  - Author and timestamp tracking

- **AffixTemplate**: Wrapper for morpheme slot templates
  - Slot configuration and ordering
  - Prefix and suffix slot management
  - Obligatory/optional slot constraints

#### Smart Collections (Extended)
- **AllomorphCollection**: Type-aware collection for allomorphs
- **CompoundRuleCollection**: Unified collection for compound rules
- **ProhibitionCollection**: Collection for morphosyntactic prohibitions
- **AnnotationCollection**: Collection for project annotations
- **AffixTemplateCollection**: Collection for affix templates

#### Type Hints and IDE Support
- Python type hints on all wrapper class properties (18+ properties)
- Improved IDE autocomplete and type checking
- Better static analysis support

#### Documentation
- **USAGE_ALLOMORPHS.md**: Allomorph operations guide
- **USAGE_COMPOUND_RULES.md**: Compound rule operations guide
- **USAGE_PROHIBITIONS.md**: Morphosyntactic prohibition guide
- **USAGE_ANNOTATIONS.md**: Annotation operations guide
- **USAGE_AFFIX_TEMPLATES.md**: Affix template operations guide

### Improved

- **Code Quality**: Type hints across all wrapper classes
- **Documentation**: Usage guides for all new domains
- **Test Coverage**: Extended test suite for new wrappers
- **API Consistency**: All collections follow unified interface

### Backward Compatibility

- **100% Maintained**: All v2.0 and v2.1 APIs unchanged
- **Additive Only**: New wrappers don't modify existing functionality
- **Mixed Usage**: Old and new approaches coexist seamlessly

### Deprecation Notices

None. All previous APIs remain fully functional.

---

## [2.2.0] - 2025-02-28

### Added

#### Wrapper Classes
- **PhonologicalRule**: Unified wrapper for PhRegularRule, PhMetathesisRule, and PhReduplicationRule
  - Transparent casting to concrete types
  - Capability-based API (`has_output_specs`, `has_metathesis_parts`, `has_reduplication_parts`)
  - Convenience properties for common operations
  - Full backward compatibility with base interface

- **MorphosyntaxAnalysis**: Unified wrapper for MoStemMsa, MoDerivAffMsa, MoInflAffMsa, and MoUnclassifiedAffMsa
  - Type identification properties (`is_stem_msa`, `is_deriv_aff`, `is_infl_aff`)
  - Automatic casting based on actual type
  - Convenience properties for POS access
  - Proper string representation showing actual type

- **PhonologicalContext**: Unified wrapper for PhSimpleContextSeg, PhSimpleContextNC, PhComplexContext, and PhBoundaryContext
  - Context type detection (`is_simple_context`, `is_complex_context`, `is_boundary_context`)
  - Segment-based vs natural class detection
  - Convenience properties for accessing context-specific data
  - Clear display of context type

#### Smart Collections
- **RuleCollection**: Collection class for phonological rules
  - Type-aware display showing breakdown of rule types
  - Convenience filter methods (`regular_rules`, `metathesis_rules`, `reduplication_rules`)
  - Custom filtering with `filter_where()` across all rule types
  - Support for method chaining

- **MSACollection**: Collection class for morphosyntactic analyses
  - Type-aware display showing MSA type breakdown
  - Convenience filters (`stem_msas`, `deriv_aff_msas`, `infl_aff_msas`, `unclassified_aff_msas`)
  - POS-based filtering (`filter_by_pos()`)
  - Advanced filtering with `filter_by_has_pos()`, `filter_where()`

- **ContextCollection**: Collection class for phonological contexts
  - Type-aware display with context type breakdown
  - Convenience filters for all context types
  - Custom filtering capabilities
  - Full iteration and indexing support

#### Base Infrastructure
- **LCMObjectWrapper**: Base class for all wrapper implementations
  - Automatic delegation to concrete interfaces
  - Consistent property access across types
  - Exception handling for missing properties
  - `__getattr__` delegation pattern for seamless access

- **SmartCollection**: Base class for all collection types
  - Type-aware string representation
  - By-type filtering with `by_type()`
  - Generic filtering framework
  - Standard collection operations (append, extend, clear)

### Improved

- **Type Transparency**: Users no longer need to manually check `ClassName` and cast to concrete types
- **IDE Support**: Wrapper classes provide better autocomplete and type hints
- **Error Messages**: Type mismatches produce clear, actionable error messages
- **Filtering**: Unified filtering across type hierarchies without manual type checking
- **Documentation**: Comprehensive examples in docstrings and test suite
- **Code Maintainability**: Internal casting hidden from public API, reducing complexity

### Fixed

- **AttributeError Prevention**: Capability checks prevent accessing unavailable properties
- **Type Safety**: Automatic casting ensures correct interface access
- **Method Chaining**: Collections support fluent filtering patterns

### Documentation

- **MIGRATION.md**: Complete migration guide showing old vs new API
  - Side-by-side examples for all three domains
  - Backward compatibility notes
  - Gradual vs immediate migration strategies
  - Feature comparison table

- **Wrapper Classes Documentation**: Comprehensive docstrings
  - Usage examples in all wrapper classes
  - Capability-based API documented
  - Type detection methods explained

- **Smart Collections Guide**: Collection usage patterns
  - Filtering examples
  - Type-aware display explanation
  - Convenience method documentation

### Backward Compatibility

- **Zero Breaking Changes**: All existing v2.1 code runs unchanged
- **Additive Design**: New wrappers are purely additive, don't modify existing API
- **Mixed Usage**: Old and new approaches can coexist in same codebase
- **Gradual Migration**: Users can migrate at their own pace
- **Base Interface Access**: Direct access to base ILcmObjects still available

### Tests

**Core Wrapper Tests** (41 tests)
- LCM Object wrapper initialization and delegation
- Concrete property access across types
- Exception handling and edge cases
- Attribute error prevention

**Collection Tests** (70 tests)
- SmartCollection initialization and operations
- Indexing, slicing, iteration
- Type-aware string representation
- By-type filtering and custom filtering

**Domain-Specific Tests** (68 tests)
- **Phonological Rules**: RuleCollection and PhonologicalRule wrapper
  - Regular rule properties
  - Metathesis rule properties
  - Reduplication rule properties
  - Convenience filters and chaining

- **MSAs**: MSACollection and MorphosyntaxAnalysis wrapper
  - Stem MSA properties and filters
  - Derivational affixal MSA properties
  - Inflectional affixal MSA properties
  - POS-based filtering and detection

- **Contexts**: ContextCollection and PhonologicalContext wrapper
  - Simple context (segment-based) properties
  - Simple context (natural class) properties
  - Complex context properties
  - Boundary context properties
  - Type convenience filters

**Total: 179 tests passing, 0 failures, 0 regressions**

### Performance

- No performance degradation compared to v2.1
- Wrapper overhead minimal (delegation pattern)
- Collection operations O(n) as expected
- Lazy evaluation in filter chains

### Known Limitations

- Wrappers currently available for three domains:
  - Grammar: Phonological Rules
  - Lexicon: Morphosyntactic Analyses
  - Grammar: Phonological Contexts
- Other domains will receive wrapper support in v2.3+
- Direct operations still available for all domains

### Deprecation Notices

None. All v2.1 API remains fully functional.

---

## [2.1.0] - Previous Release

See git history for previous changelog entries.

---

## How to Upgrade

### From Earlier Versions to v2.3.0

No action required. Simply upgrade the package:

```bash
pip install flexlibs2==2.3.0
```

Existing code will continue to work unchanged. All v2.0, v2.1, and v2.2 APIs remain fully functional.

### Using Wrapper Classes

To use the latest wrappers for additional domains:

```python
from flexlibs2.wrappers import Allomorph, CompoundRule, AffixTemplate
from flexlibs2.collections import AllomorphCollection, CompoundRuleCollection

# Work with allomorphs transparently
allomorphs = project.Allomorph.GetAll()
for allomorph in allomorphs:
    print(f"{allomorph.form}: {allomorph.gloss}")
```

Existing code continues to work without modification.

---

## Future Roadmap

### v2.4.0 (Planned)

- Performance optimizations for large collections
- Advanced query builder pattern
- Integration with FLEx import/export
- Extended wrapper support for remaining domains

### v3.0.0 (Future)

- Complete wrapper coverage for all domains
- Potential breaking changes for major improvements
- Enhanced type safety with static typing

---

## Contributing

See CONTRIBUTING.md for guidelines on contributing to FlexLibs2.

---

## Version Support

- **v2.3.x**: Current stable release, actively maintained
- **v2.2.x**: Previous stable, maintenance only
- **v2.1.x**: Legacy, security fixes only
- **v2.0.x**: End of life
- **v1.x**: End of life

