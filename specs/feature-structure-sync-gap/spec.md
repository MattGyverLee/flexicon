# SPEC -- feature-structure-sync-gap

**Repo:** flexicon, branch `main`
**Issues:** #251 (MSA has no sync methods), #252 (POS never captures
`DefaultFeaturesOA`/`InherFeatValOA`), #256 (`MakeFeatStruc` cannot attach to an
MSA and cannot express nesting), **#253 (Phoneme apply silently skips
unresolvable GUIDs) -- FOLDED IN, see D1**.
**Status:** **CONTRACT FROZEN** at Checkpoint 1 (2026-09-07). Cycle-1
reconnaissance complete; no code under `flexicon/code/` has been modified yet.
**Cycle-1 inputs (read these before implementing):**
- `specs/feature-structure-sync-gap/evidence/live-cycle1-probe.md` (live, `run_mode: live`, 8/8)
- `specs/feature-structure-sync-gap/reviews/cycle1-verification.md`
- `specs/feature-structure-sync-gap/reviews/cycle1-sweep.md`
- `specs/feature-structure-sync-gap/reviews/cycle1-domain.md`
- `tests/operations/test_issue251_252_256_feature_struct_probe.py` (the probe harness)

---

## 0. One-paragraph problem statement

FLEx feature structures (`IFsFeatStruc`) are owned by many LCM types under
*differently named* atomic-owning properties -- `MsFeaturesOA`, `InflFeatsOA`,
`FromMsFeaturesOA`, `ToMsFeaturesOA`, `DefaultFeaturesOA`, `InherFeatValOA`,
`MsEnvFeaturesOA`, `FeaturesOA`. Every implementation in this repo hard-codes
`FeaturesOA` and/or gates on `hasattr(owner, "FeaturesOA")`. On the two owners
that genuinely have `FeaturesOA` (`IPhNCFeatures`, `IPhPhoneme`) that works by
coincidence; on every other owner the documented contract is **unreachable by
construction** and the failure is silent. Compounding this, the live probe shows
`hasattr` returns **False for 100%** of base-interface-viewed MSAs, so a fix
written as a `hasattr` capability gate is dead code -- the exact mistake f424f99
and 3abf6b5 had to fix twice in `NaturalClassOperations`. The fix is one shared,
`ClassName`-driven **owner-property resolver** plus a matching **recursive
serialize/apply pair** on `BaseOperations`.

---

## 1. Ground truth (live-measured, do not re-litigate)

From `evidence/live-cycle1-probe.md` (Ngoreme FLEx read-only + `target_sandbox`):

| Fact | Value |
|---|---|
| `hasattr(msa, <feat prop>)` via base-interface view | **0 True / 2088 False** (MoStemMsa 1951, MoInflAffMsa 134, MoDerivAffMsa 3) |
| Same CLR object via factory/cast return | `hasattr` **True** -- divergence is the accessor path, not object freshness |
| `hasattr(pos, DefaultFeaturesOA/InherFeatValOA)` | **26/26 True** -- `POSOperations.GetAll()` already casts |
| Wrong cast (`IMoInflAffMsa` on a `MoStemMsa`) | raises `TypeError` at cast time -- **loud**, safe to rely on |
| Structures with content | 782 stem / 38 inflAffix / 0 derivAffix |
| Nesting frequency | **799 nested vs 21 flat** of 820 -- nesting is the MAJORITY shape |
| Nested shape observed | `IFsFeatStruc(TypeRA=NULL)` > `IFsComplexValue("noun agreement")` > `IFsFeatStruc(TypeRA=FsFeatStrucType:8465)` > 2x `IFsClosedValue`. **Only the OUTER TypeRA is null.** |
| `Create(Guid)` on `IFsFeatStrucFactory` / `IFsComplexValueFactory` / `IFsClosedValueFactory` | **Yes** -- all three round-trip GUIDs via the existing `BaseOperations._CreateWithGuid` |
| Ownership-first rule | Confirmed -- a free-floating `IFsFeatStruc.FeatureSpecsOC` **getter** itself throws `NullReferenceException`. Attach, then populate, at *every* level. |

Corrections to the filed issues: the stem-MSA population is **1951**, not the
1949 cited by the reporter.

---

## 2. Decision D5 (recorded first because it changes how #251/#252 are written)

### #252 is a PURE COVERAGE GAP, not a hasattr trap. #251 is the opposite.

The probe measured the distinction directly:

- **#252 / POS:** `POSOperations.GetAll()` already returns concrete
  `IPartOfSpeech`, so `hasattr` is True 26/26. The *only* defect is that
  `GetSyncableProperties` (`POSOperations.py:1124`) never emits the two
  properties, and `ApplySyncableProperties` (`:1178`) is a bare `super()`
  delegate. **Fix = add capture + apply. No cast is required for the
  `GetAll()`/object path** (a cast is still required on the HVO/GUID path and is
  mandated by C2).
- **#251 / MSA:** `MSAOperations` has **zero** sync methods, and its objects
  arrive base-typed off `entry.MorphoSyntaxAnalysesOC`. `hasattr` is 0/2088.
  **Fix = new sync methods that discriminate on `.ClassName` and cast
  explicitly.**

**Therefore:** a fix written on the #251 assumption ("add a hasattr gate") is
100% dead code for MSA *and* pointless for POS; a fix written on the #252
assumption ("just add the property to the capture loop") is **wrong for MSA** --
it will read `None` forever. The two issues share a resolver but not a
diagnosis. Any implementation that treats them as one copy-paste is rejected at
QC.

**Frozen rule for the whole family:** never gate on `hasattr` for a
subtype-declared member. Discriminate on `.ClassName`, then cast. A `ClassName`
absent from the frozen table in C1 raises `FP_ParameterError` naming it -- never
guess, never silently return `None`.

---

## 3. Decisions required of the lead

### D1 -- #253 is IN, and the behaviour change ships IN THIS FEATURE (two commits)

Both specialists converged independently, and Explore's Deliverable 4 satisfies
the flip condition stated in cycle 1 ("fold #253 in *iff* one shared helper is
structurally realistic"). It is: `NaturalClassOperations.__ApplyFeatures`
(`:1282-1397`) and `PhonemeOperations.__ApplyFeatures` (`:1454-1521`) are
line-for-line the same algorithm differing on **four parameters** -- owning
property name, unresolved-GUID policy, struct-GUID preservation, diagnostic
label -- and `__ResolveByGuid` is duplicated verbatim. One of those four
parameters (property name) *is* the #251/#252/#256 fix, so the parameterisation
is not speculative generality.

Reconciling lex-domain F ("RAISE family-wide, retrofit PhonemeOperations") with
Explore ("do not unify the policy silently"): these are not in conflict. The
ruling is **do it loudly, in two separately reviewable steps**:

- **T4 (refactor, behaviour-preserving):** extract the helper; NC passes
  `on_unresolved="raise"`, Phoneme passes `on_unresolved="skip"`. Zero
  behavioural delta. Verifiable by the existing NC/Phoneme live tests passing
  unchanged.
- **T9 (policy flip = the actual #253 fix):** Phoneme's default becomes
  `"raise"`. Its own commit, its own live evidence file, its own
  `CHANGELOG.md` `[Unreleased] ### Changed` entry marked **BREAKING
  (behavioural)**, next minor, no deprecation window.

Rationale for shipping the flip now rather than deferring: `"Phoneme"` is a live
sync object type (`flexicon/sync/engine.py:446`), so the skip is active silent
data loss today; and leaving `on_unresolved="skip"` wired up after building the
parameter would mean shipping a knob whose sole purpose is preserving a bug.
Precedent for the semver handling is #254 (breaking behavioural, `### Changed`,
next minor, no deprecation window).

`on_unresolved="skip"` **remains a supported parameter value** -- it is just no
longer any caller's default. It stays because a bulk importer may legitimately
want lenient mode; that must be an explicit, visible opt-in.

### D2 -- Scope ruling on the newly-found P0s

Governing principle: **in scope iff the shared resolver / shared
serialize-apply pair fixes it as a direct consequence.** Different defect family
=> out, and filed separately (issue filing requires the user's approval; the lead
cannot authorise it).

**IN (implement under this feature):**

| Item | Site | Why in |
|---|---|---|
| #251 MSA x4 properties | `Lexicon/MSAOperations.py` (no sync methods exist) | the feature |
| #252 POS x2 properties | `Grammar/POSOperations.py:1124`, `:1178` | the feature |
| #256 resolver + nesting | `Grammar/InflectionFeatureOperations.py:1031` | the feature |
| #256 byte-identical twin | `Grammar/PhonFeatureOperations.py:614` | same resolver; fixing one and not the other leaves the family half-applied (the 3abf6b5 failure mode) |
| #253 apply policy | `Grammar/PhonemeOperations.py:1454-1521` | D1 |
| **`IMoAffixAllomorph.MsEnvFeaturesOA` (P0, UNFILED)** | `Lexicon/AllomorphOperations.py:487` (`Get`), no `Apply` override | one more row of the same resolver table, and `"Allomorph"` is a live sync type (`engine.py:441`) -- data loss **ships today**. Fixing the table and skipping a row it already covers would be indefensible. A traceability issue may be filed by the user; implementation does **not** wait on it. |
| **`PhonemeOperations.py:1431` truthiness gate (P0, UNFILED)** | `if features:` | identical shape to what 3abf6b5 fixed in NC. We are rewriting this exact method body for #253/T4; fixing the gate is part of that rewrite, not an addition. Correct gate: `if "Features" in props or "FeaturesGuid" in props:` passing `features or []` + the guid (mirror `NaturalClassOperations.py:1257`). |
| **`PhonemeOperations.py:1351` HVO-path omission (P0, UNFILED)** | `hasattr(phoneme,"FeaturesOA") and phoneme.FeaturesOA` | must land **with** the :1431 fix or neither is testable: today the HVO path omits *both* `Features` and `FeaturesGuid`, so the apply gate never sees them. One-line `IPhPhoneme(...)` cast inside `__GetPhonemeObject`, which also repairs `:1167`, `:1237`, `:366`. |
| Phoneme struct-GUID not preserved (P1) | `PhonemeOperations.py:1471` bare `factory.Create()` | Explore axis 3 -- the shared helper always takes the guid, so this is fixed by construction |
| `lcm_casting._interface_cache` gaps (P1) | `lcm_casting.py:213-295` | D3 |
| `InflectionFeatureOperations.py:493` (#133 incomplete) | `hasattr(parent,"FeaturesOA")` after `_GetTypedOwner` | literally the resolver + the cache fix; the #133 fix silently does nothing today for exactly the owners its own comment names |
| NC `hasattr` gates on **feature-struct** members (P1) | `NaturalClassOperations.py:911`, `:913`, `:956`, `:1021` | same resolver; `:956`/`:1021` currently raise a spurious "not feature-based" error / are inert for their primary call pattern |
| Nested read (`IFsComplexValue.ValueOA`) in capture (P0, upgraded) | `PhonemeOperations.py:1358-1364` and `NaturalClassOperations.py:1144` both `continue` on non-`IFsClosedValue` | **prerequisite, not expansion.** Nesting is 799/820 live. Adding capture for MSA/POS/Allomorph without nested traversal would ship a capture path that drops the majority of real data, and would make writes asymmetric with reads. |
| Latent truthiness gates in the same files (P2) | `PhonemeOperations.py:1428`, `PhonFeatureOperations.py:760` | one line each, in files already open; leaving them is how 3abf6b5 became a second pass after f424f99 |
| NC in-call duplicate-spec double-insert (P2); Phoneme dead `fill_gaps` param (P2) | -- | both collapse for free in the shared helper |
| Doc: Category 8 entry for the varying feature-struct property name; `FeatureStructureRA` documented as a false-positive class | `docs/API_ISSUES_CATEGORIZED.md` | zero code risk; Category 8 has **no** feature-structure entry today |

**OUT -- file as new issues (user approval required to file):**

| Item | Site | Where it goes |
|---|---|---|
| `IWfiAnalysis.MsFeaturesOA` never captured (P1) | `TextsWords/WfiAnalysisOperations.py:335` | new issue. The resolver row is added here (C1) so the fix is a one-liner, but no `WfiAnalysisOperations` change lands in this feature. **Cross-reference** the unfiled `InflClassRA` draft at `specs/254-getmorphtype-allomorph/reviews/cycle3-archivist-inflclass-issue-draft.md`, which also touches this file -- consider one combined issue. |
| `IFsFeatStruc.FeatureDisjunctionsOC` never traversed (P1) | all four readers walk `FeatureSpecsOC` only | new issue. Disjunctive feature structures are a genuinely new capability, not a resolver defect. |
| `ICmBaseAnnotation.FeaturesOA`, `IScrScriptureNote.FeaturesOA` (P2) | `Notebook/NoteOperations.py:420`; `Scripture/ScrNoteOperations.py`, `ScrAnnotationsOperations.py` (no `GetSyncableProperties` at all) | new issue |
| `EtymologyOperations.py:548` no-clear-on-null (P2) | -- | new issue; unrelated family (undocumented RA-clearing policy) |
| `BaseOperations._apply_props_loop` dict-dispatch hazard (P1) | `BaseOperations.py:346-353` | new issue. Changing base dispatch touches all 15 `ApplySyncableProperties` implementations. **In this feature it is a binding constraint, not a change** -- see C6. |

**OUT -- append to an existing spec, do not double-file:**

- `NaturalClassOperations.py:655`, `:711`, `:766` (`hasattr(nc,"SegmentsRC")`,
  P1) -- **segment**-based classes, not feature structures; same defect family
  as the base-type cast sweep. Explore's do-not-double-file list named
  `AllomorphOperations` `PhoneEnvRC` x4, `LexEntryOperations.py:433` and
  `PhonologicalRuleOperations` `RightHandSidesOS` x4 as already scoped in
  `specs/233-basetype-cast-sweep/spec.md` section 2, but **NC `SegmentsRC` is
  not there.** Append those three rows to that spec (planning doc; a docs-only
  edit, permitted -- 233 is explicitly no-code).
- Everything already in `specs/233-basetype-cast-sweep/spec.md` section 2 stays
  there. Do not re-file, do not fix here.
- `EtymologyOperations.py:478`/`:491` (`LanguageRA`, `LanguageNotesRA`) --
  deliberately unfixed per `docs/API_ISSUES_CATEGORIZED.md:466-473` (the members
  do not exist at all). Leave alone.

### D3 -- `lcm_casting._interface_cache` IS fixed in this feature, and it is Task 1

`_GetTypedOwner` (`BaseOperations.py:1564-1602`) delegates to `cast_to_concrete`,
which returns the object **unchanged** for any `ClassName` absent from
`_interface_cache` (`lcm_casting.py:213-295`). That cache contains **no**
feature-structure owner class. It is the root enabler: it is why the #133 fix at
`InflectionFeatureOperations.py:493` silently does nothing, and several fixes
below depend on it. Fixing it is one place and unblocks multiple rows, so it is
sequenced **first**.

**Cycle-3 correction (E1):** the original 13-name list below included
`PosFeatures`, but the live assembly scan run as part of T1 proves
**`IPosFeatures` does not exist in this LCM version**
(`missing_types: ["IPosFeatures"]`). "Add the 13 entries" was therefore
unachievable as written. The corrected scope is **12 registrable
`_interface_cache` names** -- 8 net-new, plus 4 (`MoStemMsa`, `MoInflAffMsa`,
`MoDerivAffMsa`, `MoAffixAllomorph`) that were already cached **before T1
ran** -- **plus `PosFeatures` hardcoded to resolve to `None`**, following the
existing `IPhReduplicationRule` precedent for a name with no backing LCM
interface. Landed in commit `1790fcc0`; T1 is marked `[x]` DONE in section 5.

**C1's frozen table (section 4) is UNAMENDED by this correction** -- it never
listed `PosFeatures` as a resolver row; only the interface-cache entries list
below was wrong.

Entries to add (corrected, 12 registrable names): `PhNCFeatures`,
`PhNCSegments`, `PhPhoneme`, `PartOfSpeech`, `FsComplexFeature`, `MoStemMsa`,
`MoInflAffMsa`, `MoDerivAffMsa`, `MoAffixAllomorph`, `FsFeatStruc`,
`FsComplexValue`, `FsClosedValue` -- plus `PosFeatures` hardcoded to `None`
(not a real cache entry; see correction above).

**Cycle-3 finding (E2), second T1 result:** the live assembly scan also
confirms that **only `PhNCFeatures` and `PhPhoneme` have a property literally
named `FeaturesOA`** -- `PartOfSpeech` has
`DefaultFeaturesOA`/`InherFeatValOA`, and `FsComplexFeature` has `DefaultOA`,
never `FeaturesOA`. This **CONFIRMS C1; no amendment**. Side effect now
unlocked by T1: with the cache entries in place,
`InflectionFeatureOperations.FeatureStructureDelete` now **genuinely clears
`FeaturesOA`** on a `PhNCFeatures`/`PhPhoneme` owner where it previously
silently no-op'd -- and **no test locks this clear-path today**. See D3a and
T11 (section 5) for the regression-test obligation this creates.

**Mandatory guard on this task:** adding entries *changes* `cast_to_concrete`
behaviour for every existing caller that passes one of those ClassNames (today
they get the object back unchanged; afterwards they get a concrete cast). The
implementer must enumerate all `cast_to_concrete` / `_GetTypedOwner` call sites,
state the delta for each in the task note, and run the full offline suite plus
the NC/Phoneme live tests before any other task in this feature is started.
`PhNCSegments` is included even though the `SegmentsRC` fixes are out of scope --
the entry is inert here and unblocks spec 233.

### D3a -- Scope statement: T6 unchanged, T11 changes twice (E3)

`T6` (`MSAOperations`, #251) is **UNCHANGED** by E1 and E2 -- the MSA rows in
C1 never involved `PosFeatures` or a bare `FeaturesOA` assumption.

`T11` (`InflectionFeatureOperations.py:493`, #133 completion) **changes
twice**:
(a) drop `PosFeatures` from its owner list and from the descriptive comment at
`InflectionFeatureOperations.py:486` that invented it;
(b) T11 now also owns a **regression test** for the E2
`FeatureStructureDelete` clear-path on `PhNCFeatures`/`PhPhoneme` owners.

T11's bullet in section 5 is updated accordingly.

### D4 -- Frozen surfaces

See section 4 (contract items C1-C8, plus C4a/C4b added cycle 3). Headline rulings:

- **Nested spec surface: RECURSIVE DICT. The `("feat", [(f,v)...])` tuple
  overload is REJECTED** -- it is a silent `isinstance` branch (element 2 is
  sometimes a value, sometimes a list) capped at exactly one extra level, and
  live data shows nesting is the majority shape with no structural depth bound.
- **The flat list-of-tuples is a HARD back-compat requirement, not a courtesy
  alias:** 5 live internal call sites (`NaturalClassOperations.py:463`, `:867`,
  `:1034`; `PhonemeOperations.py:1924`; the `PhonFeatureOperations.py:106`
  docstring) plus shipped tests (`test_phonemes.py:672`,
  `test_phon_features.py:412`/`:450`/`:501`) all pass it. It must keep working
  byte-for-byte.
- **Owner resolution is by `ClassName` + explicit `slot=` for ambiguous
  owners.** lex-domain's table listed only `IMoDerivAffMsa` as ambiguous;
  **`IPartOfSpeech` is equally ambiguous** (`DefaultFeaturesOA` *and*
  `InherFeatValOA`) and is corrected into the frozen table below.
- **`IFsComplexValue.ValueOA` is treated as CONFIRMED**, overriding the sweep's
  UNCONFIRMED marking. The sweep could not confirm it because
  `tests/contract/snapshots/liblcm_baseline.json` (255 types, generated
  2026-08-13) has no `IFsComplexValue` entry; the live probe observed the
  property directly. Live evidence outranks a stale snapshot. The snapshot gap
  is recorded as a P2 tooling follow-up in section 7.

---

## 4. Frozen contract (C1-C8, C4a-C4b)

### C1 -- Owner-property resolver table (FROZEN)

Single source of truth. Lives beside the shared helper (`BaseOperations`, or a
module-level constant in `Shared/` if the implementer prefers -- but exactly ONE
copy).

| `ClassName` | `slot=` | LCM owning property | props key | in scope this feature |
|---|---|---|---|---|
| `MoStemMsa` | -- | `MsFeaturesOA` | `MsFeatures` / `MsFeaturesGuid` | yes (#251) |
| `MoInflAffMsa` | -- | `InflFeatsOA` | `InflFeats` / `InflFeatsGuid` | yes (#251) |
| `MoDerivAffMsa` | `"From"` | `FromMsFeaturesOA` | `FromMsFeatures` / `FromMsFeaturesGuid` | yes (#251) |
| `MoDerivAffMsa` | `"To"` | `ToMsFeaturesOA` | `ToMsFeatures` / `ToMsFeaturesGuid` | yes (#251) |
| `PartOfSpeech` | `"Default"` | `DefaultFeaturesOA` | `DefaultFeatures` / `DefaultFeaturesGuid` | yes (#252) |
| `PartOfSpeech` | `"InherFeatVal"` | `InherFeatValOA` | `InherFeatVal` / `InherFeatValGuid` | yes (#252) |
| `MoAffixAllomorph` | -- | `MsEnvFeaturesOA` | `MsEnvFeatures` / `MsEnvFeaturesGuid` | yes (unfiled P0, D2) |
| `PhNCFeatures` | -- | `FeaturesOA` | `Features` / `FeaturesGuid` | yes (reference template) |
| `PhPhoneme` | -- | `FeaturesOA` | `Features` / `FeaturesGuid` | yes (#253 + P0 gates) |
| `WfiAnalysis` | -- | `MsFeaturesOA` | `MsFeatures` / `MsFeaturesGuid` | **resolver row only** -- no `WfiAnalysisOperations` change (D2 OUT) |

**Explicitly EXCLUDED from the table** (unconfirmed against live data, zero
references in `flexicon/code/`, absent from both snapshots): `MoDerivStepMsa`,
`LexEntryInflType`, `MoStemName`, and `MoUnclassifiedAffixMsa` (the probe
confirmed this last one carries **no** feature-struct property at all).
Resolving any of these raises.

**Resolver behaviour (frozen):**
1. Unwrap, read `.ClassName`.
2. `ClassName` not in table -> `FP_ParameterError` naming the ClassName and
   listing the supported ones.
3. `ClassName` has >1 row and `slot` is `None` -> `FP_ParameterError` naming the
   valid `slot` values. **Never guess.**
4. `ClassName` has 1 row and `slot` is given -> `slot` is ignored (documented),
   not an error.
5. Return `(concrete_cast_owner, prop_name)`. The cast is via `IMoStemMsa(obj)`
   etc.; a wrong cast raises `TypeError` loudly (probe item 2), which is
   acceptable and must not be swallowed.

**props-key naming rule (frozen):** the LCM property name minus its `OA`
suffix, plus a `<Name>Guid` sibling. This is *already* what the two shipped
implementations do (`FeaturesOA` -> `"Features"`/`"FeaturesGuid"`), so NC's and
Phoneme's wire format is unchanged, and multi-slot owners are unambiguous
without inventing a qualifier syntax.

### C2 -- Object resolution must cast on the HVO/GUID path

`FLExProject.Object(hvo)` (`FLExProject.py:3212-3226`) returns a bare
`ICmObject`. Every `__Get<X>Object` resolver in this feature's blast radius must
cast before returning. Applies to
`PhonemeOperations.__GetPhonemeObject` (`:1263-1275`),
`NaturalClassOperations.__GetNaturalClassObject` (`:106-118`), and the new
MSA/POS/Allomorph paths. Without this, capture silently omits the feature-struct
keys on the HVO path (the `PhonemeOperations.py:1351` P0).

### C3 -- User-facing `MakeFeatStruc` surface (FROZEN)

```python
def MakeFeatStruc(self, specs, owner=None, slot=None):
    """
    specs -- either:
      (a) RECURSIVE DICT (canonical):
            {"noun agreement": {"class": "1", "number": "sg"},
             "polarity": "positive"}
          A dict value   -> IFsComplexValue whose ValueOA is a nested
                            IFsFeatStruc built by recursing.
          A scalar value -> IFsClosedValue.
          No depth limit.
      (b) FLAT LIST OF (feature, value) TUPLES (legacy, SUPPORTED
          INDEFINITELY -- 5 internal call sites + shipped tests).
          Exactly equivalent to a one-level dict.

    slot -- disambiguates owners with >1 owning property (MoDerivAffMsa:
            "From"/"To"; PartOfSpeech: "Default"/"InherFeatVal").
            Ignored for single-property owners. See C1.
    """
```

Keys/values accept an `IFsFeatDefn`/`IFsSymFeatVal` object (or a wrapper around
one), an HVO int, or a GUID string -- i.e. whatever the existing
`__ResolveFeature`/`__Unwrap` pair already accepts. `owner=None` continues to
raise (the issue #28 ruling stands, unchanged).

**Errata (cycle 5, 2026-09-07):** the previous revision of this section listed
"a name" as an accepted operand. That was never backed by an implementation in
either pre-T5 twin -- both twins' non-int branch was a pure passthrough with no
name lookup, independently confirmed at the true parent commit by both the T5
implementer and the verification gate. This is a **specification defect, not a
T5 regression**: T5 did not remove name support because none existed to
remove. GUID-string support, conversely, **was added by T5**. Name-operand
support is recorded in section 7 as a candidate follow-up, not implemented
here.

### C4 -- Sync wire format for a captured structure (FROZEN)

The user-facing surface (C3) accepts objects, HVOs, and GUID strings (see the
cycle-5 errata under C3 -- it does not accept a bare name). **The sync wire
format is GUID-only** -- names are localised and renameable, and every other
sync key in this repo that crosses projects is a GUID. These are two different
surfaces and must not be conflated.

```
props["<Name>"] = {
    "TypeGuid": "<guid>" | None,           # IFsFeatStruc.TypeRA / IFsComplexValue.TypeRA
    "Guid": "<guid>",                      # NESTED levels only; omitted at top level
    "specs": {
        "<featureDefnGuid>": "<valueGuid>",            # -> IFsClosedValue
        "<complexFeatureGuid>": { "TypeGuid": ..., "Guid": ..., "specs": {...} },
                                                       # -> IFsComplexValue.ValueOA
    },
}
props["<Name>Guid"] = "<guid of the top-level struct>"
```

- The top-level struct GUID stays in the existing sibling `<Name>Guid` key for
  back-compat with the shipped NC/Phoneme format; nested levels carry their own
  `"Guid"` inline. Every level is created through `_CreateWithGuid` (probe item
  8: all three `Fs*` factories preserve GUIDs).
- `"TypeGuid"` is copied **per level, when present**. The live shape has a null
  outer `TypeRA` and a non-null inner one, so this is emphatically not a
  whole-struct property. `TypeRA` does **not** drive `LongName` -- which is why
  the reporter's 0-mismatch `LongName` validation could never have caught a
  dropped `TypeRA` -- but dropping a populated `TypeRA` is a silent fidelity bug
  and is prohibited.
- An **empty but present** structure serialises as
  `{"TypeGuid": None, "specs": {}}` (plus its `<Name>Guid`), and must round-trip
  to a present-but-empty struct on the target -- not to `None`. This is the
  `PhonemeOperations.py:1431` bug class; see C6.

### C4a -- `_ApplyFeatureStruc` must accept both wire shapes (FROZEN, cycle 3, E4)

C4 defines `props["<Name>"]` as a recursive dict, and C6 codifies
`props.get("<Name>") or {}`. But the **shipped format is a flat LIST** of
`{"FeatureGuid", "ValueGuid"}` dicts (`NaturalClassOperations.py:1162`,
`PhonemeOperations.py:1373`), locked byte-for-byte by three test files:
`test_natural_classes.py:826/865/897/925/959`, `test_phonemes.py:678/715/725`,
`test_natural_class_feature_sync.py:88/446`. C4 addressed back-compat only for
the `<Name>Guid` sibling key -- it never addressed the `<Name>` key itself;
that gap is closed here.

`_ApplyFeatureStruc` **MUST accept BOTH** the C4 recursive dict and the legacy
flat list, normalising legacy -> C4 internally. This mirrors C3's frozen
flat-list concession for `MakeFeatStruc`.

### C4b -- Capture stays on the legacy wire format for NC/Phoneme; migration is T9b (FROZEN, cycle 3, E4)

`_GetFeatureStruc` always **emits** C4 (recursive dict). But NC's and
Phoneme's **capture** sides are **not** re-pointed at it in T3 or T4 -- they
keep emitting the legacy flat list byte-for-byte, so T4 stays
behaviour-preserving. Migrating capture to C4 is a **new task T9b** (section
5, sequenced after T9): its own commit, its own live evidence, its own
`CHANGELOG.md` entry. **Two concurrent wire formats is the accepted interim
state.**

T9b's priority depends on an **open measurement** -- whether NC/Phoneme
feature structs ever nest in live data. The code comments at
`NaturalClassOperations.py:1145-1148` and `PhonemeOperations.py:1358-1362`
assert they do not, but **nobody has measured it**.

### C5 -- Shared helpers on `BaseOperations` (FROZEN shape)

```python
_ResolveFeatureStrucOwner(owner, slot=None)        # -> (concrete_owner, prop_name); C1
_GetFeatureStruc(struct)                           # -> C4 dict | None; recursive
_ApplyFeatureStruc(owner, prop_name, spec_dict,
                   struct_guid=None,
                   on_unresolved="raise",          # "raise" | "skip"
                   label=None)                     # -> IFsFeatStruc
_ResolveFsByGuid(guid, kind)                       # de-duplicates the verbatim copies
```

Invariants carried over from `NaturalClassOperations.__ApplyFeatures` and
required at **every nesting level**:

- **Ownership-first:** attach the struct / `ValueOA` to its owner *before*
  populating or even reading its `FeatureSpecsOC` (the getter NPEs otherwise).
- Idempotency: the `existing_pairs` set of
  `(feat_guid.lower(), val_guid.lower())` is consulted before insert **and
  updated after** insert (fixes NC's in-call double-insert).
- Guards stay **outside** `_TransactionCM` so no empty named undo entry is
  created.
- Every read-back of a nested `ValueOA` needs its own explicit
  `IFsFeatStruc(...)` cast.
- `NaturalClassOperations` and `PhonemeOperations` become thin call-throughs.
  `PhonFeatureOperations.MakeFeatStruc` and
  `InflectionFeatureOperations.MakeFeatStruc` both become thin call-throughs to
  ONE generalized implementation -- **neither existing body becomes canonical**
  (they are byte-identical code with divergent correctness; Phon's works only
  because `IPhNCFeatures` happens to have `FeaturesOA`).
- Phoneme's dead `fill_gaps` parameter is removed at the call-through.

### C6 -- Apply-gate contract (FROZEN)

- Gate on **key presence, never truthiness**:
  `if "<Name>" in props or "<Name>Guid" in props:` then pass
  `props.get("<Name>") or {}` plus the guid. This is the 3abf6b5 ruling,
  extended to every row in C1.
- Feature-struct keys **must be popped out of `props` before `super()`** --
  `BaseOperations._apply_props_loop` (`:346-353`) dispatches on
  `isinstance(value, dict)` and would route a C4 dict to the multi-writing-system
  multistring path and drop it silently at `:352-353`.
  `NaturalClassOperations.py:1233` and `PhonemeOperations.py:1421` already do
  this; the new MSA/POS/Allomorph implementations must too. Enforced by an
  explicit test, not by convention. (Repairing `_apply_props_loop` itself is out
  of scope -- D2.)

### C7 -- Error contract (FROZEN): RAISE, family-wide

An unresolvable feature or value GUID raises `FP_ParameterError` naming the
unresolved GUID and instructing the caller to sync the feature system first.
Silently dropping a spec produces a class/MSA whose *names* match but that
matches nothing at rule-application time -- discoverable only when a rule
mysteriously fails to fire. This is the documented
`NaturalClassOperations.ApplySyncableProperties` ruling (`:1294-1299`, issue
#222 lineage), which already explicitly overrode Phoneme's skip as the bug-class
being fixed rather than a model to extend. `on_unresolved="skip"` survives as an
explicit opt-in only (D1).

### C8 -- `CopyFeatStruc` (FROZEN)

```python
def CopyFeatStruc(self, src_fs, target_owner, slot=None, overwrite=False):
```

Lives in `InflectionFeatureOperations`, delegating to the same C1 resolver and
the same C5 recursion. `overwrite=False` (default) raises `FP_ParameterError`
when the target's resolved property is already non-null -- silently overwriting
an existing struct is itself a data-loss defect. `overwrite=True` replaces it.
**No merge mode:** there is no unambiguous domain rule for a conflicting
`(feature, value)` at either nesting level, and that judgment belongs to the
linguist, not to a silently-invented policy.

---

## 5. Task list for Checkpoint 2 (implementation)

Sequenced; T1 is a hard prerequisite.

**Re-cut checkpoints (cycle 3):** **Checkpoint 2a = T1-T3** (additive helpers,
zero runtime delta) -- T1 is now `[x]` DONE (commit `1790fcc0`; see D3
correction above). **Checkpoint 2b = T4-T5** (re-pointing NC/Phoneme onto the
shared helper + `MakeFeatStruc` generalization).

**Checkpoint 2b is NOT closed by T4's gate (cycle-4 lead ruling).** Checkpoint 2b
is **T4 AND T5**. Cycle 4's PASS was T4's *task* gate. Anything downstream that
keys off "the Checkpoint 2b gate" -- specifically
`specs/250-writingsystem-activation/spec.md` section 6.3, whose condition 3
requires that `BaseOperations.py` hold no uncommitted FS work -- is **still
gated**, because T5 puts the single generalized `MakeFeatStruc` into that same
file. The #250 Defect 4 window opens **after T5's gate**, not after T4's.

- [x] **T1** DONE (commit `1790fcc0`) -- `lcm_casting._interface_cache`: added
      the **12 registrable entries** (corrected from 13, D3/E1 --
      `IPosFeatures` does not exist), plus `PosFeatures` hardcoded to `None`
      (`IPhReduplicationRule` precedent); enumerated and stated the delta for
      every `cast_to_concrete`/`_GetTypedOwner` caller; full offline suite +
      NC/Phoneme live tests green. Also surfaced the E2 finding (only
      `PhNCFeatures`/`PhPhoneme` literally have `FeaturesOA`) and unlocked the
      `FeatureStructureDelete` clear-path side effect -- see D3/D3a.
- [x] **T2** DONE (commit `cfc86af`) -- `BaseOperations._ResolveFeatureStrucOwner`
      + the C1 table in exactly ONE copy
      (`Shared/lcm_constants.py::FEATURE_STRUC_OWNER_TABLE`). Verification gate
      PASS (`reviews/cycle3-verification-T2-T3.md`).
- [x] **T3** DONE (commit `cfc86af`) -- `BaseOperations`: `_GetFeatureStruc` (recursive serialize, C4) and
      `_ResolveFsByGuid`.
      **Corollary (E5):** NC's and Phoneme's private `__ResolveByGuid` must
      survive T3 **untouched** -- de-duplication into `_ResolveFsByGuid`
      happens in T4, not here.
- [x] **T4** DONE (commits `4aca74a` production / `61e0f87` live tests / `e17cd7d`
      evidence) -- `BaseOperations`: `_ApplyFeatureStruc` (recursive apply, C5/C6/C7);
      re-point NC (`on_unresolved="raise"`) and Phoneme (`"skip"`) at it.
      **Behaviour-preserving -- zero delta.**
      **Hazard (E5, cycle 3):** `tests/operations/test_natural_class_feature_sync.py:77-160`
      holds five `inspect.getsource` shape assertions against
      `_NaturalClassOperations__ApplyFeatures`, including
      `src.index("feat_obj = self.__ResolveByGuid")` at ~:145, which raises
      `ValueError` if that literal disappears. A thin call-through breaks all
      five. **Ruling: "behaviour-preserving" means RUNTIME behaviour only**;
      these source-text assertions must be **migrated 1:1** to introspect
      `BaseOperations._ApplyFeatureStruc`, enumerated assertion-by-assertion in
      the T4 report. Deleting or weakening any one of the five is a QC
      rejection.
      **Outcome:** all 6 assertions (spec's "five") migrated 1:1, zero deleted,
      zero weakened -- independently re-enumerated at `a26d39c` by the gate.
      Also landed: `_ApplyFeatureStrucSpecMap` (C4 dict recursion), the three
      `_CastFs*` testability seams (`SIL.LCModel` is a CLR namespace and
      REJECTS `monkeypatch.setattr` -- record for every future fake-object test
      of LCM-casting code in `BaseOperations`), NC/Phoneme `__ResolveByGuid`
      de-duplicated onto `_ResolveFsByGuid`, Phoneme's dead `fill_gaps` dropped.
      Gate PASS (`reviews/cycle4-verification-T4.md`): zero runtime delta
      measured on both sides, plus TWO mutation tests (legacy raise-branch and
      nested recursion) that each produced real failures and were restored
      `git hash-object`-identical.
- [ ] **T18** = **`flexicon#264`** (FILED, user-approved -- **DEFERRED, does NOT
      gate T5**) **Guard the SLDR double-init in `tests/conftest.py:135`.**
      Tracked at https://github.com/MattGyverLee/flexicon/issues/264. Note for
      that issue: the marker asymmetry is **11 unmarked modules**, not one --
      all of `flexicon/sync/tests/` except `test_duplicate_operations.py`, plus
      `flexicon/tests/test_FLExInit.py` and `test_FLExProject.py`; only 2
      modules in those trees set `pytestmark`. That line calls
      `Sldr.Initialize(True)` **unguarded**, while the production path it is
      bootstrapping (`flexicon/code/FLExInit.py:66-71`) wraps the identical call
      in `try/except` + warning. The asymmetry is unambiguous and pre-existing
      (identical at `a26d39c`, orthogonal to T4).
      **Cycle-5 correction (2026-09-07), supersedes the "11" figure above:** of
      the 13 modules in `flexicon/sync/tests/` and `flexicon/tests/`, 11 are
      unmarked, but only **three actually call `FLExInitialize`** --
      `test_base_operations.py`, `test_FLExInit.py`, and `test_FLExProject.py`.
      The other 8 unmarked modules call no init and are genuinely offline-safe.
      Blanket-marking those 11 would wrongly delete real offline coverage.
      `#264`'s suggested-fix item 2 must therefore target the **three**
      init-calling modules, not the eleven unmarked ones.
      **Do NOT land it while a second crew is active.** `tests/conftest.py` is a
      SHARED harness that neither crew owns, the other crew is measuring deltas
      against it, and their protocol
      (`specs/name-field-whitespace-identity/CONCURRENCY.md`) instructs them to
      **STOP and report** if a fourth failure appears. Perturbing their baseline
      to tidy ours is not a trade we get to make unilaterally. Land it when
      only one crew is active, or escalate `needs_human` for a coordinated
      window.
      **What actually unblocks measurement is procedural and costs nothing --
      see section 5.1 below; adopt it in cycle 5 without waiting for T18.**
- [x] **T5** DONE (commit `6643b483`; gate PASS `reviews/cycle5-verification-T5.md`) --
      `MakeFeatStruc` generalization (C3) -- one implementation; Infl and
      Phon become call-throughs; recursive dict + flat-list alias; `slot=`.
      Closes **#256**.
- [x] **T6** DONE (commits `04b50407` production, `941a29eb` .pyi, `23227b64`
      tests, `f7ab3a69` CHANGELOG, `e356670e`/`e022a783` live evidence; gate PASS
      `reviews/cycle10-verification-T6-gate.md`) -- `MSAOperations`: new
      `GetSyncableProperties`/`ApplySyncableProperties`, `ClassName`-discriminated
      + cast, all four properties. Fixes **#251**.
      **The central question is answered YES:** the discrimination holds against
      genuine base-interface views -- three live tests fetch via
      `sandbox.Object(hvo)` (a bare `ICmObject` from `ServiceLocator.GetObject`)
      before `GetSyncableProperties` and all three round-trip. Entry paths are
      genuine re-fetches, never the factory handle held at write time. #251's
      trap is NOT repeated. **#251 is not CLOSED on GitHub yet** -- closure waits
      on T6b so the closing comment states accurate coverage, and closure needs
      its own user authorisation (the #250 posting delegation was specific to
      that comment and does not generalise).
- [ ] **T6b** **Coverage-honesty follow-up to T6. Runs BEFORE T7.** The cycle-10
      gate proved four T6 coverage claims are narrower than written. The code is
      correct; the tests are what need work. Sequenced before T7 for the same
      reason section 6.3 sequenced #250 Defect 4 before T6: T7/T8 will copy T6's
      test patterns, and shipping three more instances of decorative coverage
      then sweeping it later is the exact trade that argument rejected.
      1. `__GetMsaObject`'s C2 cast is **dead code by mutation** -- removing it
         left all 6 live tests green. **KEEP the cast** (see the ruling in
         STATUS.md) and add a DIRECT, mutation-resistant test that asserts the
         returned object is concrete on both the HVO(int) and GUID(str) paths --
         e.g. that a subtype-only member is reachable on the result. Verify the
         new test DIES when the cast is removed.
      2. `TestMSASyncApplyRaisesOnUnresolvedGuid` mocks the thing it tests
         (`_make_apply_spy` raises unconditionally on `raise_guid`, never reading
         `on_unresolved`). Either make it exercise the real `on_unresolved`, or
         rename it to what it actually covers (raise-propagation through the
         public surface). C7's real lock is the live test.
      3. `TestMSASyncApplyPresenceGate` cannot separate presence from truthiness
         because the fixture's Guid value is truthy. Add a **falsy-but-present**
         value so the two come apart.
      4. Extend the zero-`hasattr` AST test to inspect `__GetMsaObject`. Note
         `_ResolveFeatureStrucOwner` lives in `BaseOperations` -- either cover it
         there or state the boundary explicitly in the test's docstring.
      5. **R2 needs no new test.** Behavioural coverage is structurally
         impossible (the `if/elif` dispatch excludes `MoUnclassifiedAffixMsa`
         regardless). Record that in the test docstring; the two static AST tests
         are the real lock. Do NOT chase a test that cannot exist.
- [ ] **T7** `POSOperations`: capture + apply `DefaultFeaturesOA` and
      `InherFeatValOA` (coverage-gap fix, no hasattr gate -- D5). Closes **#252**.
- [ ] **T8** `AllomorphOperations`: capture + apply `MsEnvFeaturesOA` (unfiled P0).
- [ ] **T9** `PhonemeOperations`: `:1351` HVO-path cast (C2) **and** `:1431`
      presence gate (C6) **and** struct-GUID preservation -- these three land
      together or none is testable. Then the `on_unresolved` default flips to
      `"raise"` in its **own commit** with a `CHANGELOG.md` `### Changed`
      BREAKING (behavioural) entry. Closes **#253**.
- [ ] **T9b** (C4b, E4) Migrate NC's and Phoneme's **capture** sides
      (`NaturalClassOperations.py:1162`, `PhonemeOperations.py:1373`) from the
      legacy flat list to the C4 recursive-dict wire format emitted by
      `_GetFeatureStruc`. Own commit, own live evidence, own `CHANGELOG.md`
      entry. Priority gated on an **open measurement** -- whether NC/Phoneme
      feature structs ever nest in live data; the code comments at
      `NaturalClassOperations.py:1145-1148` and `PhonemeOperations.py:1358-1362`
      assert they do not, but nobody has measured it.
- [ ] **T10** `NaturalClassOperations`: replace the feature-struct `hasattr` gates
      at `:911`, `:913`, `:956`, `:1021` with `ClassName` + cast. (`SegmentsRC`
      gates at `:655`/`:711`/`:766` are OUT -- append to spec 233.)
- [ ] **T11** `InflectionFeatureOperations.py:493` -- complete the #133 fix using
      the C1 resolver (needs T1 + T2). **Cycle-3 changes (E3/D3a):** (a) drop
      `PosFeatures` from its owner list and from the descriptive comment at
      `InflectionFeatureOperations.py:486` that invented it; (b) add a
      regression test for the E2 `FeatureStructureDelete` clear-path on
      `PhNCFeatures`/`PhPhoneme` owners.
- [ ] **T12** `CopyFeatStruc` (C8).
- [ ] **T13** Latent truthiness gates: `PhonemeOperations.py:1428`,
      `PhonFeatureOperations.py:760`.
- [x] **T14a** DONE cycle 6, commit `b3ba083b` --
      `tests/operations/test_makefeatstruc_c3_live.py` (3 live tests,
      `target_sandbox`), evidence `evidence/live-T14a.md`, `run_mode: live`,
      3/3 passed. Test 3 landed as a **raise** test: the resolver raises
      `FP_ParameterError` on an ambiguous `ClassName` with no `slot=`, so the
      "silent guess" risk flagged at dispatch did not materialise. Falsifiability
      residue: only test 1 carries a mutation kill; the mutations for tests 2/3
      are folded into the Defect-4 gate (see STATUS.md, cycle-6 ruling 2).
      (split out cycle 5, 2026-09-07) Promote the C3 live coverage
      into the shipped suite: nested recursive-dict round-trip (write nested ->
      re-read from the LCM -> compare), `slot="From"/"To"` disambiguation
      exercised **through `MakeFeatStruc` itself**, and the ambiguous-owner-
      without-slot error path. Runs at **Checkpoint 2c (cycle 6)**. TEST-ONLY by
      design -- does **not** re-open `BaseOperations.py`. Its existence is owed
      to the gate's probes having died with their disposable worktree. Evidence
      -> `specs/feature-structure-sync-gap/evidence/live-t14a.md`, `run_mode:
      live` required.
- [ ] **T14b** (remainder of original T14; keeps T14's original late position)
      Live verification on Target / `target_sandbox`: empty-but-present struct
      round-trip, per-level `TypeGuid` preservation, per-level GUID
      preservation, unknown-`ClassName` raise. Evidence ->
      `specs/feature-structure-sync-gap/evidence/live-t14b.md`, `run_mode: live`
      required.
- [ ] **T15** Docs: `docs/API_ISSUES_CATEGORIZED.md` Category 8 entry for the
      varying feature-struct property name; `FeatureStructureRA` on
      `IPhSimpleContextNC`/`IPhSimpleContextSeg` documented as a false-positive
      class; `CHANGELOG.md` entries.
- [x] **T16** DONE (commit `9e0f9710`, by `flexicon-cd`) Docs: **`CLAUDE.md`
      staleness fix** -- see section 7.
- [x] **T17** DONE (commit `4fc2b6bd`, by `flexicon-cd`) Append the three NC
      `SegmentsRC` rows to `specs/233-basetype-cast-sweep/spec.md` section 2
      (docs-only). Left an OPEN QUESTION for spec 233's owner, which this
      campaign does NOT resolve: that spec's "All 16 CONFIRMED sites fixed"
      definition-of-done becomes 19, which collides numerically with a
      pre-existing "19 NEEDS RUNTIME" count in the same document. The
      sweep-total arithmetic was deliberately left on the original 16 so it
      still reconciles.

## 5.1 Measurement discipline (cycle-4 lead ruling -- BINDING from cycle 5 on)

**Measure a DELTA between your own two runs in the same shell. An absolute
offline pass count is not evidence and must not be quoted as a gate.**

This is not a preference; it is forced by measurement. Three agents measured the
same offline suite at effectively the same commit and got three different
answers:

| Who | Result |
|---|---|
| T4 implementer (disposable `git worktree`) | 1494 -> **1495 passed**, 0 failed, 627 deselected |
| Cycle-4 verification gate | **225 passed, 1273 errors** |
| The other crew, at committed HEAD (`specs/name-field-whitespace-identity/reviews/cycle2-baseline.md`) | **1292 passed, 3 failed, 498 deselected, 0 errors** |

**Two of the three were clean, so "the suite is broken" is the wrong
conclusion.** And the `deselected` counts (627 vs 498) prove the three runs did
not even *collect the same set* -- so no `conftest.py` guard could have made
those numbers agree. The dominant variable is an **unpinned invocation** (rootdir,
`-m` filter, worktree vs clone, stale `__pycache__`, whether FLEx/SLDR was
already initialised in that shell), with SLDR order-dependence sitting
underneath it. T18 addresses the second; only this rule addresses the first.

Binding rules, adopted from the other crew's protocol (which derived them
independently against the same repo -- convergent, not borrowed):

1. Record counts **immediately before** your first edit, in the shell you will
   use for the after-run. Change. Re-run. **Only the delta between your own two
   runs is yours.** Report both raw numbers *and* the delta.
2. Expected delta for a correct change: `passed` unchanged or up by the offline
   tests you added; `deselected` up by exactly the `requires_live_project` tests
   you added.
3. Quote the **exact command** with the run, every time. A count without its
   command is unfalsifiable.
4. A failure in a file you did not touch, on the known-foreign list, is named as
   foreign and passed over. A failure in a file you did not touch that is **not**
   on that list -- **STOP and report**.
5. `--collect-only` marker counts still bind: **no tests collected is a ZERO,
   never a pass.** Live runs are unaffected -- sandbox fixtures are per-test
   tempdir copies, so `run_mode: live` stays trustworthy.

### The comparator T5 (and every later task) is measured against -- FROZEN

**Ruled cycle 4, after `flexicon#264` was filed.** The bare full-suite offline
count is **retired as a gate**. It is not merely noisy -- it is invalid on its
own terms, and `#264`'s conftest guard would not repair it:

`python -m pytest -m "not requires_live_project"` collects **11 modules that
require a live FLEx and are not marked** -- all of `flexicon/sync/tests/`
except `test_duplicate_operations.py`, plus `flexicon/tests/test_FLExInit.py`
and `test_FLExProject.py`. Only **2** modules in those two trees carry
`pytestmark = pytest.mark.requires_live_project`. So the "offline" set drags in
live init, and whichever of those 11 reaches SLDR first decides whether
`tests/conftest.py:135` raises. Marker hygiene is `#264`'s suggested-fix item 2
-- a **separate** change from the guard. **Waiting for `#264` therefore buys T5
nothing.**

**Cycle-5 correction (2026-09-07):** see the T18 entry above -- only **three**
of these modules (`test_base_operations.py`, `test_FLExInit.py`,
`test_FLExProject.py`) actually call `FLExInitialize`; the other 8 are
offline-safe and must not be blanket-marked.

T5's acceptance is measured against these four, in this order of authority:

1. **PRIMARY -- live subset, both sides, same shell.** At T5's parent commit and
   at T5's HEAD, with `FLEXLIBS_REQUIRE_LIVE=1` and `run_mode: live` confirmed
   in `tests/live_status.json` on **every** run:
   `tests/operations/test_phon_features.py test_phonemes.py test_natural_classes.py test_natural_class_feature_sync.py test_feature_struc_resolver.py test_apply_feature_struc.py test_issue251_252_256_feature_struct_probe.py -m requires_live_project`.
   Expected: identical on both sides **except** the #256 probe assertions
   flipping FAIL -> PASS. Any other status change must be explained or the gate
   fails.
2. **SECONDARY -- a PINNED offline subset, delta only, never an absolute.**
   `python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider`.
   Pinned by explicit directory, explicitly **excluding** `flexicon/sync/tests`
   and `flexicon/tests` (the 11 mis-marked modules above). Run before the first
   edit and after, **in the same shell**. Report both raw numbers **and** the
   delta; only the delta is evidence.
3. **DETERMINISM CHECK, attached to the run rather than to `#264`.** Run the
   pinned subset twice in the same shell and once in a fresh shell. If the three
   counts disagree, the comparator is not yet valid: report **`FAIL:
   unfalsifiable`** with the three numbers -- never a bare count. This is cheap
   (offline, subset) and converts "the instrument might be broken" from an
   assumption into a per-cycle measured fact.
4. **FALSIFIABILITY -- the mutation test, which is what actually carries the
   claim.** A "zero delta" is only meaningful if something could have made it
   non-zero. Cycles 3 and 4 both established this: cycle 3 deleted a cast and 12
   of 16 live tests went red; cycle 4 ran two mutations and each produced real
   failures. **The offline count never was the falsifier** -- it only ever
   detected collateral breakage elsewhere, which (2) now covers for the
   directories we actually touch. T5's gate **must** therefore break the
   generalized `MakeFeatStruc`'s owner resolution, show the live subset go red,
   restore, and verify `git hash-object` identical to the committed blob.

**`#264` must NOT be fixed inside T5's commit** -- `tests/conftest.py` is a
shared harness the other crew is measuring deltas against. If a stable pinned
subset proves unobtainable without touching it, **STOP and hand off
`needs_human`**; do not widen the task.

### Known-foreign red set (expected; do NOT fix, do NOT re-diagnose)

- `tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`
- `tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::test_depth_restored_on_exception`
- `tests/test_flexlibs2_alias_ratchet.py::TestFlexlibs2AliasIsInboundOnly::test_no_executable_flexlibs2_imports_outside_alias_package`
  (rename fallout from `ec54432`; T16's territory at most, not T5's)
- **Live, ours:** `test_apply_raises_on_type_mismatch_segments_target`
  (`AttributeError: 'ICmObject' object has no attribute 'Name'`,
  `NaturalClassOperations.py:1270`) -- pre-existing C2/HVO-cast symptom, expected
  to fall out of **T10**.

---

## 6. Definition of done

1. `#251`, `#252`, `#253`, `#256` closable.
2. No `hasattr(<base-typed obj>, <subtype member>)` gate remains in any file
   touched by this feature.
3. Exactly ONE copy of the C1 table, ONE `MakeFeatStruc` implementation, ONE
   apply/serialize recursion pair.
4. Live evidence with `run_mode: live` and post-write values **re-read from the
   LCM** (asserting on the value passed in proves nothing).
5. Offline suite green; NC/Phoneme live tests green and unchanged across T4.
6. Nested (majority-shape) round-trip demonstrated live, not just flat.
7. The #253 behaviour flip is a separate commit with a CHANGELOG entry.

---

## 7. Recorded ancillary findings (not code changes to this feature's targets)

**`CLAUDE.md` is stale on the package directory name (T16).** DONE -- landed
as `9e0f9710` by the concurrent session `flexicon-cd`. The project
instructions said `flexlibs2/code/` and `flexlibs2/sync/`; the actual package
is **`flexicon/code/` and `flexicon/sync/`**.

**Errata (cycle 8, 2026-09-07), correcting this entry's own premise.** An
earlier revision of this paragraph asserted "(`flexlibs2/` does not exist)".
**That is false, and the error understated the finding.** `flexlibs2/` DOES
exist -- as the **inbound-only compatibility shim** created by `ec54432`
(#241) for external FlexTools / FlexTrans callers on disk, deprecated and
**removed at v5.0.0**. Verified present and tracked at cycle 8.

The correction matters because it changes the severity. `#240`'s ratchet
(`tests/test_flexlibs2_alias_ratchet.py`) forbids **any** internal reference
to the alias, so a stale `CLAUDE.md` was not merely out of date -- it was
actively instructing every agent to write exactly what that ratchet rejects,
and what would become a hard break at the v5.0.0 boundary. A footgun, not a
typo. Credit to `flexicon-cd`, which caught it while doing T16 and could not
correct this file itself (it is locked to this session).

Affected: the "Project Structure" tree, the file-header example, the
`Shared.string_utils` / `flexlibs2.APIHelpFile` references, and every path under
"Key Files to Know". This has already cost real work --
`specs/254-getmorphtype-allomorph`'s handoff carries a deferred repo-wide
`flexlibs2` -> `flexicon` import-alias sweep, and
`tests/operations/test_wfi_morph_bundle.py:43,73,104,188` still import the old
name. Fix `CLAUDE.md` in this feature (docs-only, zero risk); the code/test
alias sweep stays deferred as its own PR.

**FILED as flexicon#265 (user-approved, cycle 6, 2026-09-07): `MakeFeatStruc`
does not accept a plain feature/value NAME as an operand.** See the C3 errata
above -- this was
never implemented in either pre-T5 twin, so it is a pre-existing specification
gap, not a T5 regression. It needs its own freeze cycle rather than a quick
patch here, because a bare-name lookup requires four undecided policy choices:
which `Find`-style lookup to use, what scope to search (project-wide vs. a
single feature system), what ambiguity policy applies when the same name
occurs in more than one feature system, and what case/writing-system rule
governs the match. **Status (cycle 6, 2026-09-07): the user approved filing and
the issue is now OPEN as flexicon#265, recording those four undecided policy
choices as its content.** It is OUT of this feature's scope; nothing in
`feature-structure-sync-gap` waits on it. Supersedes the earlier "needs user
approval / not filed" wording.

**Tooling limitations found during the sweep (recorded so future sweeps do not
repeat them):**

- `api_usage_extract.json` / `api_usage_by_namespace.json` record **imports
  only** (`{file, namespace, class, line_start, import_type, statement}`). They
  contain no property-level usage and **cannot answer "is this property
  captured?"**. Use `tests/contract/snapshots/liblcm_baseline.json` for type
  shape, and grep for usage.
- `liblcm_baseline.json` (255 types, generated 2026-08-13) is **incomplete**: it
  omits `IFsComplexValue`, `IMoDerivStepMsa`, `ILexEntryInflType`, and
  `IMoStemName`. The live probe confirmed `IFsComplexValue.ValueOA`, which the
  snapshot could not. P2 follow-up: regenerate/extend the snapshot.

**Crew process finding.** `Explore` and `lex-domain` have no `Write` tool in
their agent definitions, so cycle-1 reports had to be persisted by the main
session on their behalf. Future dispatch plans must either grant those roles
write access to `specs/<feature>/reviews/` or route report-writing through an
agent that has it -- otherwise the path-relay discipline that keeps the
orchestrator's context small breaks down.
