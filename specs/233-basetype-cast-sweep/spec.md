# SPEC — 233-basetype-cast-sweep

**Repo:** flexicon, branch `main`
**Origin:** Follow-up work uncovered by the Cycle-1 sweep run while fixing issue #232
(`specs/232-getpos-object/reviews/cycle1-sweep.md`).
**Status:** Draft — not yet dispatched to a crew cycle.
**Do-not-list for this feature:** no code changes under `flexicon/code/`, no GitHub
issues opened, no git commits. This document is planning only.

## 1. Problem statement

Issue #232 (`LexSenseOperations.py:1184`, `getattr(msa, "PartOfSpeechRA", None)`) was one
resolved exemplar of a **defect family**: code reads an LCM property off a *base*
interface (e.g. `IMoMorphSynAnalysis`, `IPhSegmentRule`, `IConstituentChartCellPart`)
when that property is declared only on one or more *concrete subtypes*. Because
pythonnet does not raise on a missing-attribute read the way a statically typed
caller would, the read degrades silently:

- `getattr(obj, "Prop", None)` returns `None` even though the object legitimately has
  the data — just not visible through the base interface.
- `hasattr(obj, "Prop")` returns `False`, so capability-gated code branches into the
  wrong path or rejects the object outright.
- A collection property (`...RS`, `...OC`, `...OS`) reads back `[]` instead of raising,
  masking writes that were silently skipped.

None of these fail loudly. The object works fine when routed through
`cast_to_concrete()` (or an equivalent typed resolver); it silently misbehaves when it
isn't. #232 fixed one instance in `LexSenseOperations.GetPartOfSpeechObject`. This spec
scopes the remaining instances the same sweep surfaced across the rest of
`flexicon/code/`.

## 2. CONFIRMED sites (16), carried over verbatim from the sweep report

Source: `specs/232-getpos-object/reviews/cycle1-sweep.md`, "CONFIRMED BUG (16)" table.
Grouped by file below; the sweep's file:line, variable, property, and rationale are
reproduced unmodified.

### `Lexicon/AllomorphOperations.py` (4 sites)

| file:line | variable | property read | why |
|---|---|---|---|
| `Lexicon/AllomorphOperations.py:472` | `source` | `PhoneEnvRC` | `__GetAllomorphObject` returns raw `IMoForm`/`ICmObject`, never casts; `PhoneEnvRC` is on `IMoStemAllomorph`/`IMoAffixAllomorph` only. |
| `Lexicon/AllomorphOperations.py:979` | `allomorph` | `PhoneEnvRC` | Same resolver; `GetPhoneEnv` raises `AttributeError` on a raw allomorph or HVO. |
| `Lexicon/AllomorphOperations.py:1025` | `allomorph` | `PhoneEnvRC` | `AddPhoneEnv` — same uncast resolver. |
| `Lexicon/AllomorphOperations.py:1067` | `allomorph` | `PhoneEnvRC` | `RemovePhoneEnv` — same (also line 1068). |

### `Lexicon/LexEntryOperations.py` (1 site)

| file:line | variable | property read | why |
|---|---|---|---|
| `Lexicon/LexEntryOperations.py:433` | `allomorph` | `PhoneEnvRC` | Loop var from `source_entry.AlternateFormsOS` is `IMoForm`; deep-Duplicate reads it uncast. |

### `Grammar/PhonologicalRuleOperations.py` (4 sites)

| file:line | variable | property read | why |
|---|---|---|---|
| `Grammar/PhonologicalRuleOperations.py:918` | `rule` | `RightHandSidesOS` | `__ResolveObject` unwraps wrappers to `_obj` (base `IPhSegmentRule`); `hasattr` is always False -> `WireRule` rejects every rule from `GetAll()`/HVO. |
| `Grammar/PhonologicalRuleOperations.py:925` | `rule` | `RightHandSidesOS` | Same variable, direct read. |
| `Grammar/PhonologicalRuleOperations.py:938` | `rule` | `RightHandSidesOS` | Same, inside transaction. |
| `Grammar/PhonologicalRuleOperations.py:942` | `rule` | `RightHandSidesOS` | Same; file has **zero** `cast_to_concrete` uses. |

### `Discourse/ConstChartClauseMarkerOperations.py` (3 sites)

| file:line | variable | property read | why |
|---|---|---|---|
| `Discourse/ConstChartClauseMarkerOperations.py:290` | `marker` | `WordGroupRA` | Uncast resolver; prop is on `IConstChartMovedTextMarker` only — `GetWordGroup` always returns `None`. |
| `Discourse/ConstChartClauseMarkerOperations.py:327` | `marker` | `DependentClausesRS` | Prop on `IConstChartClauseMarker` only -> always returns `[]`. |
| `Discourse/ConstChartClauseMarkerOperations.py:380` | `marker` | `DependentClausesRS` | Same, write path silently skipped. |

### `Discourse/ConstChartWordGroupOperations.py` (2 sites)

| file:line | variable | property read | why |
|---|---|---|---|
| `Discourse/ConstChartWordGroupOperations.py:294` | `group` | `BeginSegmentRA` | Prop on `IConstChartWordGroup`/`ITextTag` only; base is `IConstituentChartCellPart`. |
| `Discourse/ConstChartWordGroupOperations.py:366` | `group` | `EndSegmentRA` | Same. |

### `Grammar/InflectionFeatureOperations.py` (1 site)

| file:line | variable | property read | why |
|---|---|---|---|
| `Grammar/InflectionFeatureOperations.py:1211` | `feature` | `ValuesOC` | `__ResolveFeature` (line 1611) never casts; `ValuesOC` is `IFsClosedFeature`-only -> always `[]`. |

### `Notebook/annotation.py` (1 site)

| file:line | variable | property read | why |
|---|---|---|---|
| `Notebook/annotation.py:438` | `self._obj` | `BeginObjectRA` | `ICmBaseAnnotation`-only, and unreachable anyway (line 436 `hasattr(_obj,"Owner")` is always True) — dead fallback. |

**Totals check:** 4 + 1 + 4 + 3 + 2 + 1 + 1 = 16, matching the sweep's count across 6
files (`AllomorphOperations.py`, `LexEntryOperations.py`,
`PhonologicalRuleOperations.py`, `ConstChartClauseMarkerOperations.py`,
`ConstChartWordGroupOperations.py`, `InflectionFeatureOperations.py`,
`annotation.py` — 7 files; the sweep's "6 files" framing groups the two
`ConstChart*Operations.py` files under one "Discourse" heading).

## 3. BLOCKER — interface-cache gaps in `lcm_casting.py`

**This is prerequisite work. Do not schedule the Discourse or InflectionFeature fixes
before it.**

`cast_to_concrete()`'s `_interface_cache` (populated in `_load_interfaces()`,
`flexicon/code/lcm_casting.py`) has **no entries for**:

- `ConstChart*` concrete types (`IConstChartClauseMarker`, `IConstChartWordGroup`,
  `IConstChartMovedTextMarker`, and siblings) — only the *chart container* type
  `IDsConstChart` is cached (`lcm_casting.py:199`, `:274-275`); the individual
  chart-cell-part subtypes that own `WordGroupRA`, `DependentClausesRS`,
  `BeginSegmentRA`, `EndSegmentRA` are absent.
- `IFsClosedFeature` — no `FsFeat*`/`FsClosedFeature` key exists anywhere in the
  cache-population block.

Because the Discourse (`ConstChartClauseMarkerOperations.py`,
`ConstChartWordGroupOperations.py`) and InflectionFeature
(`InflectionFeatureOperations.py:1211`) fixes need `cast_to_concrete()` to resolve
those ClassNames, **the fix for those 6 sites requires adding cache entries to
`lcm_casting.py` first** (new conditional import block + `_interface_cache[...] = `
assignment, following the existing pattern at lines 191-209 and 262-273) — not merely
editing the call sites in the Discourse/InflectionFeature operations files.

**Verification note (spot-checked against source while drafting this spec):** the
sweep report's note also lists `IPhSegRuleRHS` as missing from the cache. A direct
read of `lcm_casting.py:127-138, 232-238` shows `PhSegRuleRHS` (along with
`PhRegularRule`, `PhMetathesisRule`, `PhSimpleContextSeg`, `PhSimpleContextNC`) **is
already populated conditionally**, gated on a successful `from SIL.LCModel import
IPhSegRuleRHS` at load time. This narrows — it does not remove — the blocker: the
phonological-rule concrete types are already cache-resident, so the top-priority
`PhonologicalRuleOperations.py:918` fix (Section 4) is a call-site cast problem, not a
cache-population problem. The cache-addition work in this section is scoped strictly
to `ConstChart*` and `IFsClosedFeature`. Checkpoint C1 (Section 5) should verify this
against a live `IPhSegmentRule` instance before assuming no cache work is needed there
— per the verification caveat in Section 6, absence/presence claims about LCM
interfaces are not final until checked live.

## 4. Severity ranking

| Rank | Site | Rationale |
|---|---|---|
| **1** | `Grammar/PhonologicalRuleOperations.py:918` (`hasattr(rule, "RightHandSidesOS")`) | Used as a **capability gate**, not a data read: `WireRule` checks `hasattr` on an *uncast* `rule` before doing anything else. Because the base `IPhSegmentRule` never exposes `RightHandSidesOS`, the check is always `False` — `WireRule` rejects **every** rule obtained via `GetAll()` or by HVO, regardless of its actual concrete type or whether it has right-hand sides. This is broader-blast-radius than #232 (which returned a wrong-but-plausible `None` for one MSA subtype path): here an entire public operation is inert for its primary call pattern. Independently confirmed against source by the orchestrator (direct read of the `hasattr` gate and the surrounding `__ResolveObject` unwrap). The file has **zero** uses of `cast_to_concrete` anywhere — this is not one missed call site among many correct ones, it is a file that never adopted the casting pattern. |
| 2 | `Lexicon/AllomorphOperations.py:472,979,1025,1067(-1068)` (`PhoneEnvRC`) | 4 sites, one shared uncast resolver (`__GetAllomorphObject`). Fixing the resolver once fixes all 4 call sites — high leverage, no cache work needed (`MoStemAllomorph`/`MoAffixAllomorph` are already cached, `lcm_casting.py:218-219`). |
| 3 | `Lexicon/LexEntryOperations.py:433` (`PhoneEnvRC`) | Same property/root cause as rank 2, different resolver (loop var from `AlternateFormsOS` inside deep-`Duplicate`). Silent skip during entry duplication is a data-fidelity bug (a duplicated allomorph silently loses its phonological environment) but is scoped to one code path, not four. |
| 4 | `Discourse/ConstChartClauseMarkerOperations.py:290,327,380` + `ConstChartWordGroupOperations.py:294,366` (5 sites) | Real defects (silent `None`/`[]`, silent write-skip) but blocked on the Section 3 cache-addition prerequisite, which raises the cost-to-fix above the AllomorphOperations/LexEntryOperations sites. Discourse chart features are also a narrower-used part of the FLEx UI than allomorphs or phonological rules. |
| 5 | `Grammar/InflectionFeatureOperations.py:1211` (`ValuesOC`) | Single site, but also blocked on the Section 3 cache addition (`IFsClosedFeature`). Lower rank than the Discourse cluster only because it is one site instead of five, not because it's less real. |
| 6 | `Notebook/annotation.py:438` (`BeginObjectRA`) | Confirmed but the sweep itself flags this branch as **dead code** — line 436's `hasattr(_obj, "Owner")` is always `True`, so the buggy fallback at 438 is unreachable in current control flow. Lowest severity: no live user-facing impact today, but should still be corrected or removed so it doesn't become live-and-wrong after an unrelated refactor of line 436. |

## 5. Proposed work breakdown (checkpoints, one crew spurt each)

- **C1 — Interface-cache additions + unit tests.** Add `ConstChart*` concrete-type
  imports/cache entries and `IFsClosedFeature` to `lcm_casting.py` following the
  existing conditional-import pattern (see Section 3). Add unit tests asserting
  `cast_to_concrete()` resolves each new ClassName to the expected interface. Also use
  this checkpoint to confirm live whether `IPhSegRuleRHS`'s existing cache entry
  actually resolves for the concrete rule types hit by `WireRule` (per the Section 3
  verification note) before C2 assumes it's a pure call-site fix.
- **C2 — `PhonologicalRuleOperations.py` `WireRule` (top-priority item).** Cast `rule`
  via `cast_to_concrete()` (or the module's existing phonological-rule wrapper
  pattern, per `Grammar/phonological_rule.py`) before the `hasattr`/`RightHandSidesOS`
  gate and reads at lines 918, 925, 938, 942. Add a regression test that calls
  `WireRule` on a rule obtained through `GetAll()` (not a hand-constructed concrete
  object), since that is exactly the call pattern the current code rejects.
- **C3 — `AllomorphOperations.py` `PhoneEnvRC` (x4) + `LexEntryOperations.py:433`.**
  Fix `__GetAllomorphObject` to cast before returning (fixes all 4 AllomorphOperations
  sites at once); fix the `Duplicate` loop in `LexEntryOperations.py` to cast the
  `AlternateFormsOS` loop variable. Add regression tests for `GetPhoneEnv`,
  `AddPhoneEnv`, `RemovePhoneEnv`, and a deep-`Duplicate` round-trip that asserts the
  cloned allomorph's `PhoneEnvRC` matches the source.
- **C4 — Discourse `ConstChart*` (x5).** Depends on C1. Fix
  `ConstChartClauseMarkerOperations.py:290,327,380` and
  `ConstChartWordGroupOperations.py:294,366` to cast before reading
  `WordGroupRA`/`DependentClausesRS`/`BeginSegmentRA`/`EndSegmentRA`. Add regression
  tests per method.
- **C5 — `InflectionFeatureOperations.py` + `annotation.py`.** Depends on C1 for the
  `InflectionFeatureOperations.py:1211` half. Fix `__ResolveFeature` to cast before
  `ValuesOC` reads. For `annotation.py:438`, resolve per Section 4 rank 6: either cast
  before the read (if the branch should stay reachable) or remove the dead fallback
  entirely and document why — this is a judgment call for the checkpoint owner, not a
  mechanical fix; flag it for `/lex-lead` or the user rather than picking silently.
- **C6 — Resolve the 19 NEEDS RUNTIME sites against a live project.** Not a code-fix
  checkpoint by default — a verification checkpoint. For each NEEDS RUNTIME group in
  the sweep report (`EnvironmentOperations.py:476,532,616,628`;
  `OverlayOperations.py:173,205,420`; `ConstChartMovedTextOperations.py:203`;
  `ConstChartClauseMarkerOperations.py:128,210,251,442`;
  `NoteOperations.py:126,197,345,374,422,602,643`), run the relevant getter/setter
  against a live FLEx project and record whether the property genuinely exists on the
  base interface (LIKELY SAFE / no fix needed), is absent entirely from the object
  model (permanently-`None` by design, docstring fix only, no cast possible), or is a
  genuine cast bug (moves to CONFIRMED, gets its own follow-up checkpoint). Do not
  promote or fix any of these 19 sites based on snapshot/index evidence alone (see
  Section 6).

## 6. VERIFICATION CAVEAT

`tests/contract/snapshots/liblcm_baseline.json` and the FlexToolsMCP casting index
have **proven coverage gaps**. The clearest documented counter-example: the snapshot
omits `ILexEtymology.Source`, which `CLAUDE.md` records as a real property from the
resolved issues #36/#39/#40 (`Source` is `ITsString` on `ILexSense` but
`IMultiString` on `ILexEtymology`/`ICmBaseAnnotation` — the same interfaces this
snapshot is supposed to describe).

Consequence for this feature: **no property may be classified as ABSENT from an LCM
interface on snapshot/index evidence alone.** The sweep report already applied this
discipline correctly — every CONFIRMED site above is backed by a *positive* index hit
(the property is shown defined on a named concrete subtype), which the snapshot's
gaps cannot manufacture; every site whose classification would have required trusting
an *absence* in the index was demoted to NEEDS RUNTIME instead. This spec inherits
that discipline:

- C6 (Section 5) must settle every NEEDS RUNTIME absence claim against a live FLEx
  project via `dir()`/reflection on the real object, not by re-reading the snapshot.
- Any new site discovered during C1-C5 implementation that looks like a candidate
  CONFIRMED bug but whose evidence is "the snapshot doesn't list this property" must
  be treated as NEEDS RUNTIME, not CONFIRMED, until checked live.
- The C1 unit tests for new cache entries should where possible run against a live
  interface (or a faithful pythonnet stub) rather than asserting only that a Python
  dict key exists — a passing dict-key test does not prove the underlying LCM
  interface actually carries the property.

## 7. Out of scope

- **The 20 TECH DEBT hand-rolled `ClassName` dispatch sites** listed in the sweep
  report (`FLExProject.py:3616,4325`; `lcm_casting.py:609,845,849`;
  `Shared/wrapper_base.py:46,151`; `Lexicon/LexEntryOperations.py:423-427`;
  `Lexicon/AllomorphOperations.py:428-443`; `Lexicon/LexSenseOperations.py:342,1357-1382`;
  `Lexicon/LexReferenceOperations.py:116,676-680,1216,1278`;
  `Lexicon/SemanticDomainOperations.py:704`; `Lists/PublicationOperations.py:879`;
  `Lists/PossibilityListOperations.py:1170,1520-1522`;
  `Notebook/LocationOperations.py:944`; `Notebook/AnthropologyOperations.py:1735`;
  `System/CheckOperations.py:1378`; `System/AnnotationDefOperations.py:1110`;
  `Grammar/InflectionFeatureOperations.py:1468`). These are **not bugs** — each
  correctly picks a factory or owner branch by `ClassName` — they just re-implement
  `cast_to_concrete()`'s ClassName-to-interface table independently and will drift
  from it over time. Deferred to a separate consolidation feature, not this one.
- **The Unicode-vs-MultiUnicode defect family** parked at
  `specs/agent-version-hotfix/reviews/unicode-vs-multiunicode-sweep.md`. This is a
  **different defect family** (a scalar `Unicode`/`String` property mistaken for a
  multilingual `MultiUnicode`/`MultiString` property — wrong method called on a
  correctly-typed object, not a base-vs-concrete-interface cast gap). That sweep is
  explicitly marked **UNVERIFIED**, with its own reliability caveat about the same
  snapshot coverage gaps described in Section 6. It is not part of this feature and
  should not be merged into this checkpoint plan.
- The 9 LIKELY SAFE sites from the sweep report (already routed through a cast or
  verified safe on the base interface) — no action needed; listed here only so the
  full sweep total (16 + 19 + 9 + 20 = 64, on top of the 1 excluded #232 exemplar) is
  accounted for and nothing was silently dropped.

## Success criteria

- All 16 CONFIRMED sites (Section 2) fixed, each cast through `cast_to_concrete()` or
  an equivalent typed resolver, with a regression test per fixed method/call pattern.
- C1's cache additions land and are covered by unit tests before C4/C5 begin (BLOCKER
  in Section 3 respected — no call-site edit lands ahead of its cache prerequisite).
- The 19 NEEDS RUNTIME sites are each resolved to a final classification (LIKELY SAFE,
  permanently-absent/no-fix-possible, or CONFIRMED-and-fixed) against a live project,
  not against snapshot evidence.
- No new site is classified as ABSENT-therefore-safe on snapshot/index evidence alone
  (Section 6 discipline maintained throughout).
- CHANGELOG `[Unreleased]` entries added for each checkpoint's user-visible fix
  (handled by `/lex-doc` per checkpoint, not bundled here).
- TECH DEBT and Unicode-vs-MultiUnicode items explicitly left untouched, each with a
  one-line pointer to its own tracking location (this spec's Section 7) so they are
  not lost, only deferred.
