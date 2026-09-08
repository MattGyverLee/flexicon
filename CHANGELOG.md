# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Future breaking changes go under `[Unreleased]` until the next version cut.

---

## [Unreleased]

### Added
- **`MSAOperations.GetSyncableProperties`/`ApplySyncableProperties`.**
  Task T6 of `specs/feature-structure-sync-gap`, closes #251.
  `MSAOperations` previously had ZERO sync methods, so every MSA synced
  across projects with a correct `ClassName`/POS but a permanently null
  feature structure: `MoStemMsa.MsFeaturesOA`, `MoInflAffMsa.InflFeatsOA`,
  and `MoDerivAffMsa`'s two independent slots,
  `FromMsFeaturesOA`/`ToMsFeaturesOA`.

  Dispatch is entirely `ClassName`-driven, reusing the shared
  `BaseOperations._ResolveFeatureStrucOwner`/`_GetFeatureStruc`/
  `_ApplyFeatureStruc` helpers (T1-T5) rather than a second resolver
  table: an MSA reached via `entry.MorphoSyntaxAnalysesOC` is
  base-`IMoMorphSynAnalysis`-typed under pythonnet, so a `hasattr` gate on
  any of these four properties is 0/2088 True in live data and would be
  dead code (spec D5). `MoUnclassifiedAffixMsa` is discriminated BEFORE
  any resolver call and never raises, since
  `MSAOperations.CreateUnclassifiedAffix` manufactures these routinely
  and the resolver excludes this `ClassName` by design.

  An unresolvable feature/value GUID raises `FP_ParameterError` naming it
  rather than silently dropping the spec (same policy as
  `NaturalClassOperations`/#222).

- **`POSOperations.GetSyncableProperties`/`ApplySyncableProperties` now
  capture and apply `DefaultFeaturesOA`/`InherFeatValOA`.** Task T7 of
  `specs/feature-structure-sync-gap`, closes #252. `PartOfSpeech` has two
  independent feature-struct slots in the frozen C1 table
  (`DefaultFeaturesOA`, `InherFeatValOA`), neither of which was ever
  captured or applied, so a synced POS carried a correct
  `Name`/`Abbreviation`/`Description`/`CatalogSourceId` but a permanently
  null feature structure. Dispatch always passes an explicit `slot=`
  ("Default" / "InherFeatVal") through the shared
  `BaseOperations._ResolveFeatureStrucOwner`/`_GetFeatureStruc`/
  `_ApplyFeatureStruc` helpers (T1-T5), since `PartOfSpeech` -- unlike
  `MoStemMsa` -- is ambiguous and requires it.

  **Bug fix, not merely a coverage gap:** `POSOperations.__ResolveObject`
  also had an independent hole on the HVO entry path -- it returned a
  bare, uncast `ICmObject`, which silently dropped even the four
  PRE-EXISTING properties (`Name`/`Abbreviation`/`Description`/
  `CatalogSourceId`) whenever `GetSyncableProperties`/
  `ApplySyncableProperties` was called with an HVO instead of an
  already-typed object (as `GetAll()` yields). `__ResolveObject` now
  casts to `IPartOfSpeech` when `ClassName == "PartOfSpeech"` and returns
  any other input unchanged (never raises) -- live-measured before and
  after the fix in `specs/feature-structure-sync-gap/evidence/live-T7.md`.
  GUID-string support remains out of scope (folded into T12).

  **Disclosed behaviour change:** `POSOperations.CompareTo` is not
  modified by T7, but its observable output changes as a side effect --
  two POS with identical feature specs but independently-created
  feature structs now report a difference on the `DefaultFeaturesGuid`/
  `InherFeatValGuid` keys, where previously neither key existed to
  compare. Pinned by `TestPOSSyncCompareToStructGuidPinning`
  (`tests/operations/test_issue252_pos_feature_sync.py`). A candidate
  follow-up -- comparing serialized spec content rather than struct
  identity -- is noted but not filed as an issue.

- **`AllomorphOperations.GetSyncableProperties`/`ApplySyncableProperties`
  now capture and apply `MsEnvFeaturesOA`.** Task T8 of
  `specs/feature-structure-sync-gap` (`spec.md:655`) -- an UNFILED P0;
  filing a GitHub issue is an outstanding user decision, so this entry
  references the task, not an issue number. `MoAffixAllomorph` has the
  single C1 table row (`MsEnvFeaturesOA`, no slot ambiguity); a
  `MoStemAllomorph` has no such property at all and is never routed to
  the resolver. Dispatch is a positive `ClassName == "MoAffixAllomorph"`
  check with no `else` and no explicit `MoStemAllomorph` guard, mirroring
  `MSAOperations`' out-of-table fallback.

  **Bug fix, not merely a coverage gap (same shape as #251/#252):**
  `GetSyncableProperties` previously used `item` raw instead of routing
  through `__GetAllomorphObject`, so an HVO entry path returned every
  `hasattr` gate False and silently produced `{"Form": {}, "MorphTypeRA":
  None}` with no raise. Independently, `__GetAllomorphObject` (the shared
  resolver behind 11 call sites) returned a bare, uncast `ICmObject` on
  the HVO path. Both fixed together: `__GetAllomorphObject` now casts to
  `IMoStemAllomorph`/`IMoAffixAllomorph` by `ClassName` and never raises
  on a miss (unlike `Duplicate`, whose own raise on an unrecognized
  `ClassName` is local to that method and untouched) -- live-measured
  before and after the fix, plus a mutation-testing pass, in
  `specs/feature-structure-sync-gap/evidence/live-T8.md`.

- **`cast_to_concrete` is now a public, top-level export** (#271):
  `from flexicon import cast_to_concrete`. It was already the correct remedy
  for the whole `'ICmObject' object has no attribute 'X'` failure class and
  already shipped in the wheel, but it was documented as internal-only, so
  consumers reached into the private `flexicon.code.lcm_casting` path,
  re-implemented it with hardcoded `ILexEntry(...)` casts, or guessed at
  public names that do not exist (`from flexicon import CastingOperations`
  fails; there has never been a `CastingOperations` module -- two stale
  audit documents that named one have been corrected). Also re-exported as
  `flexicon.code.cast_to_concrete`; the long-standing
  `flexicon.code.lcm_casting.cast_to_concrete` path is unchanged, and all
  three are the same function object. Available under the deprecated
  `flexlibs2` alias too, via the existing namespace shim.

  The export is behaviour-neutral -- no code changed, only its
  reachability and documentation. `import flexicon` still works with no
  FieldWorks installed: `lcm_casting` imports only `logging` at module
  scope and defers every `SIL.LCModel` import into a lazy
  `_ensure_interfaces()` call made on first cast.

  The documented contract is that the function is **total**: an
  unrecognised `ClassName`, a missing `ClassName`, and a cast that fails
  inside the CLR all return the *original object, unchanged*. That is what
  makes it preferable to the `ILexEntry(x)` workaround users otherwise
  land on, which throws when `x` is legitimately an `ILexSense` -- and
  `ComponentLexemesRS` / `TargetsRS` legally mix the two. Guard
  derived-member access with `hasattr` / `getattr(..., None)` accordingly.
  Because flexicon's Operations classes cast internally, this is the
  documented *escape hatch* for direct-LCM work and legitimately
  polymorphic collections, not the primary remedy.
  `validate_merge_compatibility` and `clone_properties` remain internal;
  exporting `LCMObjectWrapper` is deliberately left for a separate call.

### Changed
- **BREAKING (behavioural): name-field writers across four Operations
  classes now persist the caller's original, unstripped name, and their
  three sibling comparison methods now strip whitespace on BOTH sides of
  the comparison, not just the search argument** (Q-242A,
  `specs/name-field-whitespace-identity`). Persist sites:
  `TextOperations.Create`/`SetName`, `AnthropologyOperations.Create`/
  `CreateSubitem`, `DiscourseOperations.CreateChart`/`SetChartName`,
  `CheckOperations.CreateCheckType`/`SetName`. Comparison sites:
  `TextOperations.Exists`, `AnthropologyOperations.Find`,
  `CheckOperations.FindCheckType`.

  Previously these six writer sites validated a `.strip()`ed copy of the
  caller's name but persisted that same stripped copy, silently
  discarding leading/trailing whitespace; meanwhile the three sibling
  dedup comparisons stripped only the search argument, never the stored
  name, because the stored name was ALWAYS pre-stripped by the same
  writer bug -- the writer's own strip was load-bearing for dedup
  coherence, not incidental to it (spec.md C1). Fixing persist alone
  would have broken that coherence: a name persisted with trailing
  whitespace would become invisible to its own family's dedup check,
  letting `Create()` mint unbounded duplicate-looking records instead of
  raising (spec.md C2). Both halves land together for this reason.

  **A caller who relied on the old stripping now silently persists
  different data**, and **a caller who relied on whitespace defeating
  the uniqueness guard (e.g. deliberately padding a name to bypass a
  duplicate check) now gets `FP_ParameterError: ... already exists`
  instead of a second record.** Whitespace-insensitive dedup was a
  deliberate ruling, not an oversight: the uniqueness guard at all three
  families is a flexicon invention with no FLEx/LCM equivalent (FLEx's
  own Texts & Words organizer enforces zero title uniqueness), and a
  guard defeated by one invisible character is a false-confidence
  footgun -- worse than no guard at all (spec.md C3, independently
  re-derived and accepted by `/lex-domain` under owner override).

  `DiscourseOperations` has no dedup check at all and never did (spec.md
  C3's per-family carve-out); only its persist half changed.
  `AnthropologyOperations.CreateSubitem` also has no dedup check, unlike
  `Create` (spec.md C5 observation) -- this was not added.
  `AnthropologyOperations.Exists` was deliberately left untouched (it
  still strips and reassigns its own local copy; only `Find`, which it
  calls, gained symmetric comparison).

  **Known remaining gap, disclosed and not fixed here (Q-242D):** at
  three of the eight persist sites -- `AnthropologyOperations.Create`,
  `AnthropologyOperations.CreateSubitem`, and `TextOperations.SetName` --
  a whitespace-only name (e.g. `"   "`) is not rejected. It now persists
  as literal whitespace instead of silently becoming `""` as before;
  this removes a payload-loss bug but does not add the whitespace-only
  rejection the other five sites already have. Adding that rejection at
  these three sites is `Q-242C`'s decision (validator harmonisation
  across differing exception types), deliberately not fragmented into
  this fix.

  **Verification gap, disclosed rather than smoothed over:**
  `DiscourseOperations.CreateChart`'s persist fix is correct by code
  inspection but is `FAIL: unverified` through its own public API --
  live verification is blocked by two pre-existing, unrelated defects in
  the chart-creation path (`Q-DISC1`). `SetChartName` and all seven other
  sites are fully live-verified (20/20 tests passing,
  `run_mode: live`, `target_sandbox`/`target_sandbox_path` fixtures only;
  see `specs/name-field-whitespace-identity/evidence/`). This entry does
  not claim 8/8 sites live-verified.

- **BREAKING (behavioural): `CheckOperations.CreateCheckType`,
  `.FindCheckType`, and `.SetName` now raise instead of silently
  persisting or matching an empty name** (Q-242B,
  `specs/name-field-whitespace-identity`). All three previously ran
  `name = name.strip() if isinstance(name, str) else ""` ahead of a
  None-only `_ValidateParam` check, so a non-`str` payload OR an
  ordinary whitespace-only string (e.g. `"   "`) silently coerced to
  `""` and was persisted or matched with **no exception at all** --
  total loss of the caller's intended name, not merely lost padding.
  This is classified separately from, and more severe than, the Q-242A
  entry above: Q-242A restores whitespace that used to be silently
  trimmed; Q-242B closes a path that used to silently destroy the
  caller's entire payload.

  All three now call the already-shipped
  `BaseOperations._ValidateStringNotEmpty` (no reassignment of `name`,
  so the caller's original bytes still reach persist), which raises
  `TypeError` for a non-`str` payload and `FP_ParameterError` for a
  whitespace-only string. The pre-existing leading
  `_ValidateParam(name, "name")` call is unchanged at all three sites,
  so `None` still raises `FP_NullParameterError` exactly as before.

  **`FindCheckType`'s docstring previously contradicted itself** --
  its `Raises` section promised `FP_NullParameterError` for an empty
  name, a promise the pre-fix code never kept, while its `Notes` section
  simultaneously claimed the method never raises. Both are now true and
  mutually consistent: see the updated docstring.

  **Callers who were passing a non-`str` or whitespace-only name to any
  of these three methods, and relying on it silently succeeding with an
  empty/blank name, now get an exception instead.** No caller should
  have depended on this -- it is the Tier-1 silent-data-loss bug this
  campaign exists to close -- but it is recorded as breaking per this
  file's own convention for exception-behaviour changes (see the
  `SaveChanges()` entry above). Blast radius of `FindCheckType`'s break
  is external callers only: the sole internal call site
  (`CheckOperations.py`, inside `CreateCheckType`) already validates
  `name` immediately beforehand.

  Live-verified: 20/20 tests passing, `run_mode: live`, all nine
  predictions matched exactly (`specs/name-field-whitespace-identity/
  evidence/live-t4b-check-q242b-fix.md`). Reaching `CreateCheckType`
  through the public API at all required a test-instance-only monkeypatch
  of the unrelated, pre-existing `_GetCheckList()` stub bug (recorded,
  not fixed, in `spec.md` section 3 of the same feature).

- **BREAKING (behavioural): `WfiMorphBundleOperations.GetMorphType` now
  returns `IMoMorphType` instead of `IMoForm`** (#254). The bundle's
  `MorphRA` field holds its linked allomorph (`IMoForm` -- concretely
  `MoStemAllomorph`/`MoAffixAllomorph`), not its morph type; the real type
  lives one hop further, at `MorphRA.MorphTypeRA`. `GetMorphType` returned
  `bundle.MorphRA` raw, so every caller was actually receiving an
  allomorph under a method name promising a type. It now returns
  `bundle.MorphRA.MorphTypeRA`: `None` (silently) if the linked allomorph
  has no morph type set, `None` with a logged warning naming the bundle's
  `Hvo` if the bundle has no linked allomorph at all (`MorphRA is None`).
  Live-verified against Sena 3 (`sena3_sandbox`): of 1932 sampled bundles,
  93 (~4.8%) had `MorphRA is None`; the naive
  `morph_type.Name.get_String(ws)` read used in the old docstring example
  returns empty for every sample, so the corrected getter's docstring now
  uses `Name.BestAnalysisAlternative.Text` instead. Callers who chained
  `.MorphTypeRA` off the old (mistyped) return value themselves must drop
  that extra hop; callers who want the allomorph itself should call the
  new `GetMorph` instead.

  **`SetMorphType` is retired** and now raises `FP_ParameterError`
  unconditionally, including for the `None` form, before checking
  write-enabled state (identical message on read-only and write-enabled
  projects). Live-verified: every non-`None` call already raised
  `TypeError: SIL.LCModel.DomainImpl.MoMorphType value cannot be converted
  to SIL.LCModel.IMoForm` at the .NET boundary before any write reached
  the LCM -- no caller has ever successfully changed a bundle's morph type
  through this method, so there is no corrupt data in the wild to
  migrate. The `None` form (which nulled `MorphRA`, i.e. cleared the
  *allomorph*, not the type) is retired too: keeping it would preserve a
  method that clears an allomorph under a name saying "type", the exact
  bug class this fix eliminates. The shipped docstring `Example` block
  itself instructed callers to pull a possibility-list `IMoMorphType` and
  assign it via this method -- following it corrupted or crashed on the
  bundle reference; that example is deleted, not merely corrected. To
  retype the lexicon allomorph, use
  `project.Allomorphs.SetMorphType(allomorph, morph_type)`. To change or
  clear which allomorph a bundle links, use the new
  `SetMorph(bundle, allomorph_or_None)`.

  **New: `GetMorph`/`SetMorph`** on `WfiMorphBundleOperations` expose
  `bundle.MorphRA` (`IMoForm | None`) honestly named -- `GetMorph` is
  today's old (buggy) `GetMorphType` behaviour, with `None` returned
  silently (no warning), and `SetMorph` accepts `None` to clear. `SetMorph`
  raises `FP_ParameterError` naming the received `ClassName` if a
  non-`None` argument resolves to something that is not an `IMoForm`
  (e.g. an `IMoMorphType`), so a caller who passes a morph type gets an
  actionable error instead of a raw pythonnet `TypeError`.

- **BREAKING (behavioural): `FLExProject.SaveChanges()` now raises
  `FP_TransactionError` instead of letting the call reach liblcm when
  `CurrentDepth > 0`** (#243, spec.md C20/C21). Previously, calling
  `SaveChanges()` while a unit of work was open -- in EITHER mode --
  reached `usm.Save()` unguarded, which raised liblcm's
  `InvalidOperationException: "Commit at wrong place."` and, under
  `undoable=False`, that failure's own path collapsed the session-long
  task envelope as a side effect, discarding the whole pending change set
  with nothing written to disk (measured 0/25 survivors -- spec.md
  P-5/P-7/P-10 case C). `SaveChanges()` now reads `CurrentDepth` first and
  refuses before `usm.Save()` is ever attempted, so the refusal itself
  discards nothing. **Callers catching the old liblcm exception type must
  now catch `FP_TransactionError` instead.** What to do per mode:
  - `undoable=False`: do not call `SaveChanges()` while
    `HasOpenSessionTask()` is true. The pending changes are intact in
    memory; `CloseProject()` ends the session envelope and writes them to
    disk.
  - `undoable=True`: call `SaveChanges()` AFTER the
    `UndoableOperation()`/`Transaction()` block has exited (`CurrentDepth`
    back to 0), never from inside one -- the block commits automatically
    on a normal exit.

  If the `CurrentDepth` read itself fails (closed/never-opened project),
  the guard fails OPEN -- it logs a `WARNING` and proceeds to `usm.Save()`
  unguarded, exactly as before the guard existed.

  See also the `[4.4.0]` entry below (`OpenProject(..., undoable=...)` now
  defaults to `True`) -- this guard and that default flip are the two
  halves of the #243 story: the flip is what let callers reach
  `undoable=False`'s single-envelope mode at all, and this guard is what
  now stops that mode's `SaveChanges()` from destroying it.

- **BREAKING (behavioural): `ParagraphOperations.Create`,
  `ParagraphOperations.SetText`, `ParagraphOperations.InsertAt`, and
  `SegmentOperations.AppendSentence` no longer strip leading/trailing
  whitespace from the persisted `content`/`text` value** (#242). All four
  previously validated emptiness against a `.strip()`ed copy but then
  persisted that same stripped copy via `TsStringUtils.MakeString`,
  silently discarding whitespace that was genuinely part of the caller's
  string. The `.strip()` is now a throwaway used only for the emptiness
  check; the caller's original, unstripped value is what reaches
  `MakeString` and is written to `IStTxtPara.Contents` /
  `ISegment.BaselineText`.

  This is a correctness fix, not a cleanup, because trailing whitespace is
  structural in FLEx paragraph/segment data: `AppendSentence` itself
  builds multi-sentence paragraphs by inserting `". "` -- period plus a
  trailing space -- as its own sentence terminator, then steps its next
  insertion point by `current_length + 2` to land past that space. The
  same file was, until this fix, stripping equivalent trailing whitespace
  out of the *next* call's input -- refusing from a caller the same shape
  of data it manufactures internally. Preserving the caller's whitespace
  brings the four writers into line with the structure FLEx itself uses.

  **A caller who relied on the old stripping now silently persists
  different data.** Code that built text by padding a separator into the
  string itself -- e.g. `f"{sentence} "` or `" ".join(parts) + " "` --
  expecting the library to absorb the trailing space, now gets that space
  written verbatim. Call `.strip()` at the call site to restore the old
  behaviour; the library no longer does it for you.

  Whitespace-only input (e.g. `"   "`) still raises `FP_ParameterError` at
  all four sites -- the emptiness contract is unchanged; only what gets
  persisted for non-empty, whitespace-bearing input changes.

  The non-`str` coercion branch is no longer stripped either:
  `SegmentOperations.AppendSentence`'s `str(text).strip()` is now
  `str(text)`, matching the three `ParagraphOperations` sites, which never
  stripped their non-`str` branch. `str` and non-`str` payloads now behave
  identically at all four methods.

  This same fix is also what makes a pre-existing join-boundary defect in
  `AppendSentence`'s terminator branch reachable through this API for the
  first time -- see **Fixed**, below.

### Fixed
- **`BaseOperations._apply_props_loop` now resolves a case- or
  separator-divergent writing-system tag instead of silently dropping the
  alt** (issue #250, Defect 4). Every `ApplySyncableProperties`-style sync
  write builds a `{ws.Id: ws.Handle}` map keyed on the **exact-case**
  `ws.Id`; a caller (or a source project) that spells a tag `en-us`,
  `EN-US` or `en_US` where the target's real `ws.Id` is `en-US` used to
  miss that `dict.get` and lose the text via a silent `continue` with no
  diagnostic. The resolution step now tries an exact match first
  (byte-for-byte unchanged for every write that already succeeds), then
  falls back to a normalized (hyphen-lowercase, `_`/`-` folded) lookup
  built lazily from the same dict, at most once per apply call. This is a
  **bug fix, not a breaking change**: no currently-succeeding write
  changes behaviour. **New failure mode:** if two or more distinctly
  cased/separated spellings in the target's writing-system set normalize
  to the same form but resolve to *different* handles, the fallback now
  raises `FP_ParameterError` naming both ambiguous spellings and their
  handles, rather than guessing which one the caller meant (spellings
  that normalize together but share one handle do not raise).

  **Coverage boundary -- read before assuming this closes #250's Defect 4
  everywhere.** The fix reaches `BaseOperations._apply_props_loop` ONLY.
  It does **NOT** reach two other apply paths that build their own
  `{ws.Id: ws.Handle}` map and run their own exact-case resolution loop
  instead of delegating: `Grammar/PhonemeOperations.__ApplyBasicIPASymbol`
  and `Lexicon/ExampleOperations.ApplySyncableProperties`'s `TranslationsOC`
  loop. Concretely: a phoneme's `Name`/`Description` alts (which delegate
  to `_apply_props_loop` via `super()`) will now save under a divergent
  spelling, while that **same phoneme's** `BasicIPASymbol` alt will still
  be silently dropped under the identical divergent spelling. Closing
  those two sites is tracked as follow-up work, not done here (Defects 1-3
  of #250 also remain open and out of scope for this fix).
- **`FLExProject.CloseProject()` no longer skips `usm.Save()` if its own
  `EndNonUndoableTask()` mirror call raises** (#243). Under
  `writeEnabled=True, undoable=False`, `CloseProject()` called
  `EndNonUndoableTask()` unconditionally, immediately before `usm.Save()`;
  a raise there (e.g. because a prior mid-session `SaveChanges()` call had
  already collapsed the session's non-undoable task envelope) skipped
  `usm.Save()` entirely, discarding the whole in-memory session with
  nothing written to disk. `CloseProject()` now guards that call two ways:
  it checks the new `HasOpenSessionTask()` first and skips
  `EndNonUndoableTask()` outright when no envelope is open, and it
  additionally wraps the call in try/except (logging a warning on any
  other raise), so `usm.Save()` always still runs either way. End-then-
  `Save()` order is unchanged. Live-verified against a `target_sandbox_path`
  tempdir copy (`run_mode: live`; the real Target was never opened and no
  restore script was run): the forced-double-`End` scenario that
  previously lost all 25 created objects (0/25 survived reopen) now
  persists 25/25.

  **This fix, combined with the `SaveChanges()` guard above, now closes
  the incident #243 was filed about.** The incident is a two-step chain:

  1. A mid-session `SaveChanges()` call under `undoable=False` used to
     reach `usm.Save()` while the session-long envelope was still open
     (`CurrentDepth == 1`), raising `Commit at wrong place.` and
     collapsing the envelope as a side effect, discarding the whole
     pending change set before `CloseProject()` was ever entered. This
     step is now **refused outright** by `SaveChanges()`'s own depth
     guard (see `### Changed` above) -- `usm.Save()` is never attempted,
     so nothing is discarded at this step any more.
  2. With the envelope never collapsed, `CloseProject()`'s own
     `EndNonUndoableTask()` mirror call finds a genuinely open envelope to
     end, so this fix's guard (above) reaches `usm.Save()` at a legal
     depth with an intact, never-touched change set.

  The full sequence -- 25 objects created, mid-session `SaveChanges()`
  attempted and refused, `CloseProject()` called -- now re-measures
  **25/25 survivors in memory** (re-read from the still-open project
  before close) **and 25/25 survivors after a genuine close-and-reopen**
  (spec.md T8b, `evidence/live-t8b-savechanges-guard.md`).

  **Two things this fix does NOT claim, so a future reader cannot
  overclaim them:**
  - It says nothing about `Target.fwdata` being replaced by a
    crash-recovery copy, as originally reported. flexicon has no code
    path that renames, rotates or replaces `.fwdata`; that observation
    remains attributed to a FieldWorks-side mechanism, out of this
    project's scope (spec.md C10).
  - Every measurement above is **single-client**, against a local,
    file-backed `target_sandbox_path` copy. No shared-project /
    multi-client recovery behaviour was measured, and none is claimed.

  **Also (#243 T7, landing in parallel this cycle -- verify against the
  landed diff before the next release cut):** `CloseProject()`'s Phase-1
  envelope-missing branch (`HasOpenSessionTask()` reads `False` while
  `writeEnabled and not undoable` -- reachable only via a stray or forced
  early `End`, spec.md P-3) now logs at **ERROR** instead of `debug`,
  naming the anomaly explicitly and stating that `usm.Save()` is
  proceeding anyway. This restores **loudness**, not **data** (spec.md
  C14) -- it asserts **nothing** about whether data was lost, because the
  only live route into this branch post-T8b is the one where the save
  succeeds (spec.md C23).

  **New public surface: `FLExProject.CurrentDepth`** (raw `int`
  passthrough of the live LCM action handler's task depth) **and
  `FLExProject.HasOpenSessionTask()`** (whether the session-long
  `undoable=False` task envelope is currently open; unconditionally
  `False` under `undoable=True`). Both raise `FP_ProjectError` on a closed
  or never-opened project rather than silently returning `0`/`False`.

- **`SegmentOperations.AppendSentence`'s sentence-terminator branch no
  longer inserts a period before existing trailing whitespace** (#242).
  This is a **pre-existing defect that the #242 whitespace fix above made
  reachable through this API for the first time -- it was not introduced
  by that fix.** The terminator branch reads the raw last character of
  the paragraph's *existing* `Contents`, whatever wrote it: `Create`/
  `SetText`/`InsertAt`, an import, a sync, or a direct LCM write could
  always have left a trailing space there, independently of #242. Before:
  appending to `'foo '` produced `'foo . bar'` (a space inserted before
  the period); appending to the already-terminated `'foo.  '` (two
  trailing spaces) produced the double-terminator `'foo.  . bar'`. After:
  `'foo '` produces `'foo. bar'`, and `'foo.  '` produces `'foo.  bar'`.
  The branch now anchors "already terminated?" and its insertion point on
  the last *non-whitespace* character, and reuses any existing trailing
  whitespace as the sentence separator instead of inserting a new one
  next to it. Zero characters are ever removed by this change --
  `rstrip()` is used only to compute an index; its stripped output is
  never written. The change is inert whenever the paragraph has no
  trailing whitespace, i.e. for every paragraph shape reachable through
  the public API before #242 landed (`Create`/`SetText`/`InsertAt`
  previously stripped all trailing whitespace unconditionally). Live-
  verified against `target_sandbox`: 9/9 predicted rows matched measured
  output, including the four-row inertness proof on shapes reachable
  before #242
  (`specs/242-paragraph-whitespace/evidence/live-t5-joinfix.md`).

## [4.5.2] - 2026-08-19

> Follow-up to 4.5.1: a residual falsy-gate gap for empty-but-present
> feature structures. No breaking changes.

### Fixed
- **`NaturalClassOperations.ApplySyncableProperties` silently dropped a
  present-but-empty `FeaturesOA` on 3 of 41 `PhNCFeatures`.** Found by
  code review (not a live run) after 4.5.1 shipped. `GetSyncableProperties`
  correctly omits the `"Features"` key when a feature-based class's
  `FeatureSpecsOC` is genuinely empty (auto-generated placeholder classes
  for phonological rules with no constraints), but always emits
  `"FeaturesGuid"` whenever `FeaturesOA` is non-null. `ApplySyncableProperties`
  gated the whole feature-rewiring branch on `if features:` alone -- and
  both `[]` and `None` are falsy in Python, so a present-but-empty source
  `FeaturesOA` was treated identically to "no `FeaturesOA` at all":
  `__ApplyFeatures` was never called, and the target's `FeaturesOA`
  stayed null even though `GetSyncableProperties` only ever emits
  `FeaturesGuid` when the source's `FeaturesOA` is definitively non-null.
  A rule referencing one of these 3 classes would silently match nothing,
  same as the original 4.5.0 bug, on a narrower slice of data (3/41
  instead of 41/41).

  The gate is now `if features or features_guid:`, so presence of
  *either* key -- not truthiness of `features` -- decides whether the
  branch runs; `__ApplyFeatures` receives `features or []` so `specs`
  is never `None`. `__ApplyFeatures` itself needed no change: it already
  creates/attaches the `IFsFeatStruc` (GUID-preserving via
  `_CreateWithGuid`) before touching `FeatureSpecsOC`, so an empty specs
  list correctly produces a non-null, zero-spec target struct. The
  type-mismatch guard (source carries feature data, target isn't
  feature-based) now sits inside the widened gate and fires correctly for
  the `FeaturesGuid`-only shape too; a legitimate `PhNCSegments` sync
  (neither key present) still never enters the branch at all.

  New behavioural tests (`TestNaturalClassSyncEmptyFeatureStructPreservation`
  in `tests/operations/test_natural_class_feature_sync.py`) exercise the
  real `ApplySyncableProperties`/`__ApplyFeatures` code -- not just the
  gate expression -- against fakes with `BaseOperations._TransactionCM`/
  `_CreateWithGuid` reduced to trivial stand-ins (no live LCM transaction
  machinery needed). Confirmed 3 of the 4 new tests fail red against the
  reverted 4.5.1 source and pass green against this fix; the 4th is a
  non-regression check that correctly passes under both.

## [4.5.1] - 2026-08-19

> Follow-up to 4.5.0: the fix in that release was dead code against live
> data. No breaking changes.

### Fixed
- **4.5.0's `NaturalClassOperations.GetSyncableProperties`/
  `ApplySyncableProperties` fix never actually fired against a real
  project.** Both gated on `hasattr(nc, "FeaturesOA")` /
  `hasattr(nc, "SegmentsRC")`, mirroring `PhonemeOperations`. That works
  for phonemes because `IPhPhoneme` declares `FeaturesOA` directly, but
  `NaturalClassOperations.GetAll()` (and `Find()`/`Object()`) yield
  objects wrapped by pythonnet under the BASE `IPhNaturalClass`
  interface -- `FeaturesOA` and `SegmentsRC` are declared on the
  concrete subtypes `IPhNCFeatures`/`IPhNCSegments`, and pythonnet's
  attribute visibility follows the static wrapper interface, not the
  runtime CLR type. Both `hasattr` checks were therefore always `False`,
  even for a genuine, populated `PhNCFeatures`/`PhNCSegments` object --
  the entire 4.5.0 capture block was dead code. Verified live against
  `Ngoreme FLEx` (read-only): 0/41 `PhNCFeatures` and 0/7 `PhNCSegments`
  passed either gate, so **neither** `Features`/`FeaturesGuid` **nor**
  `PhonemeGuids` was ever emitted for any class reached via `GetAll()` --
  a strictly worse regression than the original bug, since the
  previously-working `PhonemeGuids` path silently broke too.

  `GetSyncableProperties` and `ApplySyncableProperties` now discriminate
  on the reliable `.ClassName` string (declared on the base interface, so
  always visible) and explicitly cast to `IPhNCFeatures`/`IPhNCSegments`
  before touching a subtype-only member. Re-verified live against
  `Ngoreme FLEx`: 41/41 `PhNCFeatures` now emit `FeaturesGuid` (38/41
  emit `Features`; the other 3 legitimately have an empty
  `FeatureSpecsOC` -- auto-generated placeholder classes for rules with
  no constraints), and 7/7 `PhNCSegments` emit `PhonemeGuids`.

  New behavioural tests (`tests/operations/test_natural_class_feature_sync.py`,
  `TestNaturalClassSyncPythonnetBaseInterfaceView`) exercise the real code
  against a fake object that reproduces pythonnet's base-interface view
  (no `FeaturesOA`/`SegmentsRC` attribute, `.ClassName` set) so the same
  class of bug cannot regress silently again; confirmed these fail
  against the 4.5.0 code and pass against this fix.

## [4.5.0] - 2026-08-19

> Additive fix: closes a silent cross-project data-loss bug for
> feature-based natural classes. No breaking changes.

### Fixed
- **`NaturalClassOperations.GetSyncableProperties` dropped every
  feature-based natural class's `FeaturesOA` constraint bundle.** For an
  `IPhNCFeatures` item -- whose entire reason for existing is its owned
  `FeaturesOA` (an `IFsFeatStruc` of `IFsClosedValue` specs) -- only
  `Name`/`Abbreviation`/`Description`/`PhonemeGuids` were ever captured.
  `ApplySyncableProperties` had no `Features` handling at all (it purely
  delegated to `BaseOperations`). The result: every feature-based natural
  class synced across to a target project with the correct Name and GUID
  but a `null` `FeaturesOA`, so any phonological rule referencing the
  class silently matched nothing -- no error, no warning. Measured on two
  real project pairs: 0/34 and 0/11 `PhNCFeatures` retained their feature
  structure after sync (source had 41/41 and 15/15 respectively).

  Same bug class as `PhonemeOperations` issue #222 (which already closed
  the identical hole for phoneme `FeaturesOA`), never swept to
  `NaturalClassOperations` when #222 landed. `GetSyncableProperties` now
  additionally emits `FeaturesGuid` and `Features` (a list of
  `{"FeatureGuid", "ValueGuid"}` specs) for `IPhNCFeatures` items, and
  `ApplySyncableProperties` rewires those specs against the target
  project's feature system by GUID, creating the owned `IFsFeatStruc`
  (GUID-preserving via `_CreateWithGuid`) when needed. The segment-based
  `IPhNCSegments` / `PhonemeGuids` path is unchanged.

  Unlike the phoneme path (which skips an unresolved feature/value GUID),
  `ApplySyncableProperties` here **raises** `FP_ParameterError` naming the
  missing GUID and the natural class when the target's feature system has
  no matching feature or value. Silence is the exact defect being fixed;
  the fix must not reintroduce it by a different route.

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

