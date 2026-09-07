# Cycle 1 - Domain review: FLEx/LCM semantics of guid-preserving Create()

Note: produced by lex-domain, whose toolset had no write capability; the main
session persisted it verbatim to this path.

Summary: all three factories (CmAgent, ReversalIndex, ReversalIndexEntry)
publicly expose `Create(Guid)` and it is safe to use via the existing
`Add()`-to-owning-collection pattern, because none of the three overrides
`SetDefaultValuesAfterInit` (the one generic gap `Create(Guid)` has for
owner-required classes). CmAgent needs a well-known-GUID skip-list (3
bootstrap agents), ReversalIndex GUID identity is purely additive to the
existing WS-uniqueness guard, and ReversalIndexEntry needs a caller-side fix
for subentry placement and target-side sense resolution.

Verdicts: VIABLE / VIABLE / VIABLE-WITH-CAVEAT.

## Item 1 - CmAgent (`AgentOperations.py:115`) -- VIABLE

1. [OK] Confirmed: `MasterLCModel.xml:672` (`class num="23" id="CmAgent" ...
   base="CmObject"`) has no `generateBasicCreateMethod="false"` and no
   `owner=` attribute (defaults to `kOwnerRequired`, cf. classes that do
   override it, e.g. `owner="optional"`/`"none"` elsewhere in the file).
   `factory.vm.cs:61` (`public I$className Create(Guid guid)`) is generated
   unconditionally for such classes; `ILcmFactory<T>.Create(Guid guid)`
   (`InterfaceDeclarations.cs:646`) is the public contract `ICmAgentFactory`
   inherits.
2. `BootstrapNewLanguageProject.cs:143-162` creates exactly 3 fixed-GUID
   agents in *every* project: `kguidAgentDefUser` (Human=true),
   `kguidAgentXAmpleParser`, `kguidAgentComputer`. Since the target already
   has the same GUIDs, transplanting the source's DefUser agent does not
   "shadow" anything -- `Create(Guid)` throws `InvalidOperationException`
   immediately (loud failure, per the established duplicate-GUID rule), which
   is safe, not silent corruption. For any other (custom, human-created)
   agent, `Human` (bool) and `Version` (free string) are not identity -- GUID
   is the sole identity anchor, so preserving it for non-default agents is
   exactly right.
3. CmAgent is owner-required with no override of `SetDefaultValuesAfterInit`
   (checked `FactoryAdditions.cs` and `OverridesCellar.cs` -- none found).
   `factory.vm.cs:82` skips `InitializeNewOwnerlessCmObjectWithPresetGuid()`
   for owner-required classes on the `Create(Guid)` path, and
   `LcmOwningCollection.BasicValidityCheck` (`Vectors.cs:596-603`) only calls
   `InitializeNewCmObject`/`SetDefaultValuesAfterInit` if `Hvo` is still
   `kHvoUninitializedObject` -- which it is not after `Create(Guid)` (the
   constructor assigns a real hvo). So `SetDefaultValuesAfterInit` never runs
   on this path -- but since CmAgent has no override, there is no observable
   bad state.
4. **VIABLE** -- works via `AnalyzingAgentsOC.Add()`; callers should just skip
   the 3 bootstrap well-known GUIDs (fails loud if attempted anyway).

## Item 2 - ReversalIndex (`ReversalIndexOperations.py:111`) -- VIABLE

1. [OK] `MasterLCModel.xml:3861`, no `generateBasicCreateMethod="false"`, no
   `owner=` (required). Same generated `Create(Guid)`.
2. `ReversalIndexOperations.py:157-159` already enforces one-index-per-WS via
   `FindByWritingSystem()`, independent of GUID. A supplied GUID neither
   bypasses nor conflicts with that check -- it is purely additive identity on
   top of the WS key, useful for a merge tool to re-link
   `ReversalIndexEntry.ReversalIndex` owner-refs and downstream sense
   cross-references by identity instead of re-deriving from the WS string.
3. Same owner-required default; no `SetDefaultValuesAfterInit` override found
   (`OverridesLing_Lex.cs` ~6281 region). Same harmless-gap conclusion.
4. **VIABLE** -- GUID identity layers cleanly on top of the existing
   WS-uniqueness guard.

## Item 3 - ReversalIndexEntry (`ReversalIndexEntryOperations.py:131`) -- VIABLE-WITH-CAVEAT

1. [OK] `MasterLCModel.xml:3868`, no `generateBasicCreateMethod="false"`,
   owner required. Same generated `Create(Guid)`.
2. Two owning slots exist in the model: `ReversalIndex.EntriesOC` (top-level,
   xml:3864) and `ReversalIndexEntry.SubentriesOS` (nested, xml:3870). The
   current `Create()` (`ReversalIndexEntryOperations.py:190`) *always* does
   `index.EntriesOC.Add(new_entry)` -- there is no path to create directly
   into a parent's `SubentriesOS`. A round-tripped source subentry would land
   as a top-level entry, losing hierarchy placement -- a domain gap
   independent of GUID.

   Separately, `Senses` (xml:3877, `SensesRS`) is a *reference*, not owning;
   references are direct in-cache object pointers and cannot span two
   projects' `LcmCache` instances, so the `sense` argument passed to
   `Create()` must already be a target-project `ILexSense` resolved by the
   caller -- the entry's own GUID identity does not resolve or preserve that
   link by itself.
3. Same owner-required default; no `SetDefaultValuesAfterInit` override found.
   Same harmless-gap conclusion.
4. **VIABLE-WITH-CAVEAT** -- `Create(Guid)` itself is safe, but callers must
   separately re-parent subentries (the API has no subentry-creation path) and
   must pre-resolve the `sense` argument to a target-project object.

Reviewed By: lex-domain, cycle 1
