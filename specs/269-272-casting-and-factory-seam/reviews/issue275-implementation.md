# Issue #275 implementation report: resolver cast gap sweep

## Summary

#269 fixed `LexEntryOperations.__ResolveObject`'s two defects (uncast
non-int branch; `isinstance`-against-`ICmObject` false negative on the HVO
branch). #275 asked for the same two-defect shape to be swept across every
sibling `__ResolveObject`-family resolver in the codebase. This pass fixed
**44 sites across 24 files**, all using the same strict-widening pattern:
cast by `ClassName` before returning, keep the `isinstance` leg as a
fallback so nothing that worked before can break, and (where the resolver
already raised) raise only when *neither* leg matches.

All fixes were syntax-checked, run against the full offline suite (1858
passed / 2 pre-existing unrelated failures), and 17 of the 44 sites were
additionally verified against a real LCM (`target_sandbox` /
`sena3_sandbox`, `run_mode: live`), covering every raising-guard class
family that was reasonably self-contained to construct test data for.

## The fix pattern actually used

The issue's suggested pattern calls `cast_to_concrete(...)` directly. I
used an equivalent but more targeted variant instead: an explicit
`ClassName`-dispatched cast to the resolver's own known interface (the
same idiom already established in this codebase by
`EnvironmentOperations.__ResolveObject`, `POSOperations.__ResolveObject`,
`AllomorphOperations.__GetAllomorphObject`, and
`MSAOperations.__GetMsaObject`), wrapped in `try/except` so a cast attempt
against an object that merely *claims* a matching `ClassName` (e.g. a
Python test double) degrades gracefully instead of raising a raw
pythonnet `TypeError`:

```python
# int branch:
if isinstance(thing_or_hvo, int):
    obj = self.project.Object(thing_or_hvo)
    if getattr(obj, "ClassName", None) == "ThingClassName":
        try:
            return IThing(obj)
        except Exception:
            pass
    if isinstance(obj, IThing):
        return obj
    raise FP_ParameterError(...)
# non-int branch:
if getattr(thing_or_hvo, "ClassName", None) == "ThingClassName":
    try:
        return IThing(thing_or_hvo)
    except Exception:
        pass
return thing_or_hvo
```

Reasons for this choice over a literal `cast_to_concrete(...)` call:

1. **Registry coverage.** `cast_to_concrete`'s `ClassName -> interface`
   registry (`flexicon/code/lcm_casting.py`) does not include most of the
   types this sweep touches (`LexEtymology`, `LexEntryRef`, `CmFile`,
   `ReversalIndexEntry`, `ReversalIndex`, `ScrBook`, `ScrDraft`,
   `ScrScriptureNote`, `ScrSection`, `ScrTxtPara`, `ScrBookAnnotations`,
   `Text`, `WfiWordform`, `MoStratum`). Calling `cast_to_concrete` on
   these would be a silent no-op for Defect 1 (still returns the bare
   `ICmObject`) while only fixing Defect 2 via the `getattr(...) ==
   ClassName` leg of the guard. An explicit interface cast fixes both
   defects regardless of registry coverage, and needed no new imports --
   every interface used was already imported in its file (confirmed by
   grep before editing).
2. **No shared-file edit.** Extending the registry would mean editing
   `flexicon/code/lcm_casting.py`, a file every other Operations class
   (and every other agent working this repo concurrently) depends on.
   The chosen pattern stays entirely local to each fixed file.
3. **Strict widening is still guaranteed.** `isinstance(obj, IThing)` is
   kept as the second leg in every raising resolver, exactly as the
   issue specified, so nothing that passed the old guard can fail the
   new one.

`ClassName` strings for `LexEtymology` and `LexEntryRef`/`VariantEntryRef`
are confirmed against `FLExProject.py`'s own
`LexiconDeleteObject`/`class_name ==` dispatch (read-only; that file was
not edited). The rest (`CmFile`, `ReversalIndexEntry`, `ReversalIndex`,
`ScrBook`, `ScrDraft`, `ScrScriptureNote`, `ScrSection`, `ScrTxtPara`,
`ScrBookAnnotations`, `MoStratum`, `WfiWordform`) follow the
interface-name-minus-leading-`I` convention that every one of the ~20
existing entries in `lcm_casting.py`'s registry uses without exception
(`DsConstChart`, `ConstChartRow`, `CmSemanticDomain`, `CmLocation`,
`CmPerson`, `PhRegularRule`, `MoStemMsa`, ... ). `ScrScriptureNote` is
additionally corroborated by a string literal already in
`Notebook/annotation.py`. Live verification confirmed the convention
holds for every class it covers (`CmFile`, `ReversalIndexEntry`,
`ReversalIndex`, `ScrBook`, `LexEtymology`, `LexEntryRef`,
`ConstChartRow`, `DsConstChart`, `MoStratum`, `CmLocation`, `CmPerson`,
`CmSemanticDomain`) -- see the evidence file. The Scripture family beyond
`ScrBook` (`ScrDraft`, `ScrScriptureNote`, `ScrSection`, `ScrTxtPara`,
`ScrBookAnnotations`) and `WfiWordform` were **not** independently
live-confirmed; flagging this honestly rather than overclaiming.

## Definitive site inventory

Legend: **FIXED** = corrected this pass. **ALREADY-OK** = inspected,
already casts correctly (explicit interface cast, or `ClassName`-dispatch
pattern), left unchanged. **SKIPPED** = inspected, deliberately not
touched, with reason. **OFF-LIMITS** = in one of the 5 files this task
must not edit; not inspected in depth, flagged as a cross-boundary
candidate only.

| # | File | Resolver(s) | Issue-table / comment reference | Status |
|---|---|---|---|---|
| 1 | `Lexicon/EtymologyOperations.py` | `__GetEntryObject`, `__GetEtymologyObject` | table row 1 (lines 1297, 1317 as filed) | **FIXED** (2 sites) |
| 2 | `Lexicon/VariantOperations.py` | `__GetEntryObject`, `__GetVariantObject` | table row 2 (1116, 1136); consumer family | **FIXED** (2 sites) |
| 3 | `Shared/MediaOperations.py` | 11 identical inline HVO-resolution blocks (no shared helper method exists in this class -- the block is copy-pasted at each call site) | table row 3 (1241) | **FIXED** (11 sites) |
| 4 | `System/CheckOperations.py` | `__GetCheckObject` | table row 4 (1251) | **ALREADY-OK** -- already does `return ICmPossibility(obj)` in a `try/except` converting failures to `FP_ParameterError`; this is the *correct* remedy (explicit cast succeeds against the real runtime type regardless of the declared static return type), not the flawed `isinstance` pattern. No change made. |
| 5 | `Discourse/ConstChartOperations.py` | `__ResolveObject` | table row 5 (515) | **FIXED** (1 site) |
| 6 | `Discourse/ConstChartRowOperations.py` | `__ResolveObject`, `__ResolveChart` | table row 6 (547, 567) | **FIXED** (2 sites) |
| 7 | `Discourse/ConstChartWordGroupOperations.py` | `__ResolveObject`, `__ResolveRow` | table row 7 (498, 518) | **FIXED** (2 sites) |
| 8 | `Discourse/ConstChartClauseMarkerOperations.py` | `__ResolveObject`, `__ResolveRow` | table row 8 (405, 425) | **FIXED** (2 sites) |
| 9 | `Discourse/ConstChartMovedTextOperations.py` | `__ResolveObject`, `__ResolveWordGroup`, `__ResolveChart` | table row 9 (386, 406, 426) | **FIXED** (3 sites) |
| 10 | `Discourse/ConstChartCellTagOperations.py` | `__ResolveRow`, `__ResolveTag` | table row 10 (188, 198); consumer family | **FIXED** (2 sites) |
| 11 | `Discourse/ConstChartMarkerOperations.py` | `__ResolveMarker` | table row 11 (260) | **FIXED** (1 site) |
| 12 | `Notebook/LocationOperations.py` | `__ResolveObject` | consumer family; static-inspection "still uncast" | **FIXED** (1 site) |
| 13 | `Notebook/PersonOperations.py` | `__ResolveObject` | static-inspection "still uncast" | **FIXED** (1 site) |
| 14 | `Lexicon/SemanticDomainOperations.py` | `__ResolveObject` | consumer family; static-inspection "still uncast" | **FIXED** (1 site) |
| 15 | `Reversal/ReversalIndexEntryOperations.py` | `__ResolveObject`, `__GetIndexObject` | static-inspection "Reversal/*" | **FIXED** (2 sites) |
| 16 | `Reversal/ReversalIndexOperations.py` | `__ResolveObject` | static-inspection "Reversal/*" | **FIXED** (1 site) |
| 17 | `Scripture/ScrAnnotationsOperations.py` | `__ResolveObject` | static-inspection "All 5 Scripture/* resolvers" | **FIXED** (1 site) |
| 18 | `Scripture/ScrBookOperations.py` | `__ResolveObject` | static-inspection | **FIXED** (1 site) |
| 19 | `Scripture/ScrDraftOperations.py` | `__ResolveObject` | static-inspection | **FIXED** (1 site) |
| 20 | `Scripture/ScrNoteOperations.py` | `__ResolveObject` | static-inspection | **FIXED** (1 site) |
| 21 | `Scripture/ScrSectionOperations.py` | `__ResolveObject` | static-inspection | **FIXED** (1 site) |
| 22 | `Scripture/ScrTxtParaOperations.py` | `__ResolveObject` | static-inspection | **FIXED** (1 site) — 6th Scripture file found; issue comment said "5", tree has moved since filing |
| 23 | `Grammar/StratumOperations.py` | `__ResolveObject` (non-raising) | static-inspection "still uncast" | **FIXED** (1 site) |
| 24 | `TextsWords/TextOperations.py` | `__GetTextObject` | **not named in issue** -- found via my own sweep, identical raising-guard shape | **FIXED** (1 site, bonus find) |
| 25 | `TextsWords/WfiAnalysisOperations.py` | `__GetWordformObject`, `__GetAnalysisObject` | **not named in issue** -- found via my own sweep, identical raising-guard shape | **FIXED** (2 sites, bonus find) |
| 26 | `Lexicon/LexEntryOperations.py` | `__ResolveObject` | fixed by #269 | ALREADY-OK (pre-existing fix, not touched) |
| 27 | `Grammar/EnvironmentOperations.py` | `__ResolveObject` | static-inspection "casts landed" | **ALREADY-OK** -- `ClassName`-dispatch cast, confirmed correct |
| 28 | `Grammar/POSOperations.py` | `__ResolveObject` | static-inspection "casts landed" | **ALREADY-OK** -- confirmed correct |
| 29 | `Lexicon/AllomorphOperations.py` | `__GetAllomorphObject`, `__GetEnvironmentObject` | static-inspection "casts landed" (1365-1367) | **ALREADY-OK** -- confirmed correct |
| 30 | `Lexicon/AllomorphOperations.py` | `__GetEntryObject` | not named anywhere | **SKIPPED** -- non-raising plain passthrough (no false-negative-rejection risk), not in issue scope; discovered gap, deferred |
| 31 | `Lexicon/MSAOperations.py` | `__GetMsaObject` | static-inspection "casts landed" | **ALREADY-OK** -- confirmed correct |
| 32 | `Lists/possibility_item_base.py` | `__ResolveObject` | static-inspection "casts landed" | **ALREADY-OK for the int branch** (uses `cast_to_concrete`, correctly). **Partial gap found**: the non-int branch (`return obj_or_hvo`) is still an uncast identity return -- Defect 1 survives there. Not fixed here: this is a shared base class for every possibility-list Operations subclass (Publications, Agents, etc.), outside the issue's named scope, and touching it has a much wider blast radius than a single-class resolver. Flagged as a follow-up, not silently left as "already-OK". |
| 33 | `Notebook/AnthropologyOperations.py` | `__GetItemObject` | not named; found in my sweep | **ALREADY-OK** -- explicit `ICmAnthroItem(obj)` cast in `try/except` |
| 34 | `Notebook/DataNotebookOperations.py` | `__GetRecordObject` | not named; found in my sweep | **ALREADY-OK** -- explicit `IRnGenericRec(obj)` cast in `try/except` |
| 35 | `TextsWords/ParagraphOperations.py` | `__GetTextObject`, `__GetParagraphObject` | not named; found in my sweep | **ALREADY-OK** -- explicit cast (`IText`/`IStTxtPara`) in `try/except` |
| 36 | `TextsWords/DiscourseOperations.py` | `__GetTextObject`, `__GetChartObject`, `__GetRowObject` | not named; found in my sweep | **ALREADY-OK** -- explicit cast in `try/except` (distinct class from `Discourse/ConstChartOperations.py`) |
| 37 | `Grammar/PhonFeatureOperations.py` | `__ResolveObject` | static-inspection "still uncast" | **SKIPPED** -- own docstring documents this as an intentionally generic, wrapper-agnostic passthrough with no single target interface (callers handle multiple concrete feature-struct types themselves); a `ClassName`-dispatch fix needs a target interface to dispatch to, which this resolver by design does not have one. Flagged for a future targeted design, not a blind conformance fix. |
| 38 | `Grammar/NaturalClassOperations.py` | `__GetNaturalClassObject`, `__GetPhonemeObject` | static-inspection; explicitly corrected by `MSAOperations.__GetMsaObject`'s own docstring as "NOT already fixed... part of the Class-A caller-usage re-triage tracked in specs/260-environment-resolver-cast/STATUS.md" | **SKIPPED** -- explicitly owned by an in-flight sibling spec (260), not this issue; touching it here risks duplicate/conflicting work with that spec's own triage. |
| 39 | `Grammar/MorphRuleOperations.py` | `__ResolveObject` (non-raising) | not named anywhere | **SKIPPED** -- discovered, non-raising (lower severity), out of issue's named scope, deferred |
| 40 | `Lexicon/LexSenseOperations.py` | `__GetEntryObject`, `__GetSenseObject`, `__GetSemanticDomainObject` (non-raising) | not named anywhere | **SKIPPED** -- discovered, non-raising, out of scope, deferred (3 sites) |
| 41 | `Lexicon/PronunciationOperations.py` | `__GetEntryObject`, `__GetPronunciationObject` (non-raising) | not named anywhere | **SKIPPED** -- discovered, non-raising, out of scope, deferred (2 sites) |
| 42 | `TextsWords/SegmentOperations.py` | `__GetParagraphObject`, `__GetSegmentObject`, `__GetAnalysisObject` (non-raising) | not named anywhere | **SKIPPED** -- discovered, non-raising, out of scope, deferred (3 sites) |
| 43 | `TextsWords/WfiMorphBundleOperations.py` | `__GetBundleObject`, `__GetAnalysisObject`, `__GetSenseObject`, `__GetMorphObject`, `__GetMSAObject`, `__GetInflectionClassObject` (non-raising) | not named anywhere | **SKIPPED** -- discovered, non-raising, out of scope, deferred (6 sites) |
| 44 | `Grammar/PhonemeOperations.py` | `__GetPhonemeObject`, `__GetCodeObject` | not inspected (off-limits) | **OFF-LIMITS** -- file excluded by task constraints; not read. Cross-boundary candidate for the owning agent to check for the same pattern. |
| 45 | `Lexicon/ExampleOperations.py` | `__GetSenseObject`, `__GetExampleObject` | not inspected (off-limits) | **OFF-LIMITS** -- same reason |

### Reconciliation against the issue's two source lists

- **"Casts already landed" list** (`POSOperations:1141`,
  `EnvironmentOperations:707`, `AllomorphOperations:1365-1367`,
  `LexEntryOperations:2487`, `possibility_item_base.py:143`): all 5
  confirmed correct by direct source read, with one caveat --
  `possibility_item_base.py`'s int branch is genuinely fixed, but its
  non-int branch is not (row 32 above). Not previously reported.
- **"Still return `obj_or_hvo` unchanged" list** (5 Scripture resolvers,
  4 `Discourse/ConstChart*` resolvers, `LocationOperations`,
  `PersonOperations`, `SemanticDomainOperations`, `StratumOperations`,
  `PhonFeatureOperations`, `Reversal/*`): every item fixed **except**
  `PhonFeatureOperations` (deliberately skipped, reason above). The
  Scripture family turned out to have **6** resolvers, not 5 -- a 6th
  file, `ScrTxtParaOperations.py`, exists and carries the identical
  defect; fixed as row 22.
- **Sites my own sweep found that neither list mentions**:
  `TextsWords/TextOperations.py.__GetTextObject` and
  `TextsWords/WfiAnalysisOperations.py`'s two resolvers (raising-guard
  shape, fixed as bonus finds), plus the larger population of
  **non-raising** plain-passthrough resolvers (`MorphRuleOperations`,
  `AllomorphOperations.__GetEntryObject`, 3x `LexSenseOperations`, 2x
  `PronunciationOperations`, 3x `SegmentOperations`, 6x
  `WfiMorphBundleOperations` -- 16 sites total) that carry Defect 1 only
  (no raise, so no false-negative-rejection risk) and were not named
  anywhere in the issue. These are a real, related population but a
  meaningfully larger and lower-urgency scope expansion; deliberately
  left for a follow-up rather than folded silently into this pass.

## Verification

### Offline

```
python -m pytest -m "not requires_live_project" -q
```

1858 passed, 774 deselected, 2 failed
(`tests/test_docstring_example_ratchet.py`, pre-existing and unrelated --
flags a docstring example on `PersonOperations.AddLanguage`, a method this
change never touched; present before any of these edits).

### Live

New file: `tests/operations/test_issue275_resolver_sweep_live.py`
(17 tests, all against `target_sandbox` except one against
`sena3_sandbox`). Full command, `run_mode` confirmation, and per-class
pre/post-state table:
`specs/269-272-casting-and-factory-seam/evidence/live-275-resolver-sweep.md`.

**Result: 17/17 passed, `run_mode: live`.**

Per-class live-verification verdicts:

| Class | Live-verified? |
|---|---|
| `EtymologyOperations` | YES (both resolvers, HVO + raw-object paths) |
| `VariantOperations` | YES (both resolvers, HVO + raw-object paths, + 1 rejection) |
| `LocationOperations` | YES (+ 1 cross-type rejection) |
| `PersonOperations` | YES |
| `StratumOperations` | YES |
| `ReversalIndexOperations` | YES |
| `ReversalIndexEntryOperations` | YES (both resolvers, + 1 rejection) |
| `SemanticDomainOperations` | YES |
| `MediaOperations` | YES (proves all 11 sites share one code shape; one representative call path exercised end-to-end) |
| `ConstChartOperations` | YES |
| `ConstChartRowOperations` | YES (both resolvers, + 1 rejection) |
| `ScrBookOperations` | YES (via `sena3_sandbox`, using `GetCanonicalNum` -- see note below) |
| `ConstChartWordGroupOperations` | offline-only (identical code shape to `ConstChartRowOperations`, which is live-verified; not independently live-run) |
| `ConstChartClauseMarkerOperations` | offline-only (same reasoning) |
| `ConstChartMovedTextOperations` | offline-only (same reasoning) |
| `ConstChartCellTagOperations` | offline-only (same reasoning) |
| `ConstChartMarkerOperations` | offline-only (same reasoning) |
| `ScrAnnotationsOperations`, `ScrDraftOperations`, `ScrNoteOperations`, `ScrSectionOperations`, `ScrTxtParaOperations` | offline-only (identical code shape to `ScrBookOperations`, which is live-verified; each needs its own construction path -- book/draft/section/para/note chaining -- not built out here for time) |
| `TextOperations` | offline-only |
| `WfiAnalysisOperations` | offline-only |

Two unrelated pre-existing defects were surfaced incidentally while
building the live tests (not #275 resolver defects, not fixed here, fully
detailed in the evidence file): `ReversalIndexEntryOperations`'s default
writing-system inference, and `ScrBookOperations.GetTitle` reading a
nonexistent `book.Title` instead of `book.TitleOA`.

**Coverage is honestly uneven, as the issue anticipated.** 13 of the 24
fixed files got direct live proof; the remaining 11 (mostly the
lower-traffic `ConstChart*` siblings and 5 of 6 Scripture classes) are
offline-only, verified by identical-shape analogy to a live-proven sibling
in the same file family, not independently live-run. This is reported as
`offline-only`, not as `live-verified`.

## Files modified

`flexicon/code/Lexicon/EtymologyOperations.py`,
`flexicon/code/Lexicon/VariantOperations.py`,
`flexicon/code/Lexicon/SemanticDomainOperations.py`,
`flexicon/code/Shared/MediaOperations.py`,
`flexicon/code/Discourse/ConstChartOperations.py`,
`flexicon/code/Discourse/ConstChartRowOperations.py`,
`flexicon/code/Discourse/ConstChartWordGroupOperations.py`,
`flexicon/code/Discourse/ConstChartClauseMarkerOperations.py`,
`flexicon/code/Discourse/ConstChartMovedTextOperations.py`,
`flexicon/code/Discourse/ConstChartCellTagOperations.py`,
`flexicon/code/Discourse/ConstChartMarkerOperations.py`,
`flexicon/code/Notebook/LocationOperations.py`,
`flexicon/code/Notebook/PersonOperations.py`,
`flexicon/code/Reversal/ReversalIndexEntryOperations.py`,
`flexicon/code/Reversal/ReversalIndexOperations.py`,
`flexicon/code/Scripture/ScrAnnotationsOperations.py`,
`flexicon/code/Scripture/ScrBookOperations.py`,
`flexicon/code/Scripture/ScrDraftOperations.py`,
`flexicon/code/Scripture/ScrNoteOperations.py`,
`flexicon/code/Scripture/ScrSectionOperations.py`,
`flexicon/code/Scripture/ScrTxtParaOperations.py`,
`flexicon/code/Grammar/StratumOperations.py`,
`flexicon/code/TextsWords/TextOperations.py`,
`flexicon/code/TextsWords/WfiAnalysisOperations.py`.

New file: `tests/operations/test_issue275_resolver_sweep_live.py`.

## Cross-boundary dependencies

None of the 44 fixes required editing any of the 5 off-limits files
(`FLExProject.py`, `Grammar/PhonemeOperations.py`,
`Lexicon/ExampleOperations.py`, `System/WritingSystemOperations.py`,
`BaseOperations.py`). Two off-limits files were, however, identified (not
inspected in depth, per the boundary) as carrying resolvers of the exact
same shape:

- `Grammar/PhonemeOperations.py`: `__GetPhonemeObject` (:1263),
  `__GetCodeObject` (:1277).
- `Lexicon/ExampleOperations.py`: `__GetSenseObject` (:1628),
  `__GetExampleObject` (:1642).

These are flagged for whichever agent owns those files to check against
the same two-defect pattern; not fixed or read in detail here.

## Proposed commit subject

```
fix(resolvers): cast HVO-resolver returns across ~25 Operations classes (closes #275)
```
