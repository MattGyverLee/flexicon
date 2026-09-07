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

Entries to add: `PhNCFeatures`, `PhNCSegments`, `PhPhoneme`, `PartOfSpeech`,
`PosFeatures`, `FsComplexFeature`, `MoStemMsa`, `MoInflAffMsa`,
`MoDerivAffMsa`, `MoAffixAllomorph`, `FsFeatStruc`, `FsComplexValue`,
`FsClosedValue`.

**Mandatory guard on this task:** adding entries *changes* `cast_to_concrete`
behaviour for every existing caller that passes one of those ClassNames (today
they get the object back unchanged; afterwards they get a concrete cast). The
implementer must enumerate all `cast_to_concrete` / `_GetTypedOwner` call sites,
state the delta for each in the task note, and run the full offline suite plus
the NC/Phoneme live tests before any other task in this feature is started.
`PhNCSegments` is included even though the `SegmentsRC` fixes are out of scope --
the entry is inert here and unblocks spec 233.

### D4 -- Frozen surfaces

See section 4 (contract items C1-C8). Headline rulings:

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

## 4. Frozen contract (C1-C8)

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

Keys/values accept a name, an `IFsFeatDefn`/`IFsSymFeatVal`, an HVO, or a GUID
string -- i.e. whatever the existing `__ResolveFeature`/`__Unwrap` pair already
accepts. `owner=None` continues to raise (the issue #28 ruling stands,
unchanged).

### C4 -- Sync wire format for a captured structure (FROZEN)

The user-facing surface (C3) is name-tolerant. **The sync wire format is
GUID-only** -- names are localised and renameable, and every other sync key in
this repo that crosses projects is a GUID. These are two different surfaces and
must not be conflated.

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

- [ ] **T1** `lcm_casting._interface_cache` -- add the 13 entries (D3), enumerate
      and state the delta for every `cast_to_concrete`/`_GetTypedOwner` caller,
      full offline suite + NC/Phoneme live tests green before proceeding.
- [ ] **T2** `BaseOperations`: `_ResolveFeatureStrucOwner` + the C1 table (one copy).
- [ ] **T3** `BaseOperations`: `_GetFeatureStruc` (recursive serialize, C4) and
      `_ResolveFsByGuid`.
- [ ] **T4** `BaseOperations`: `_ApplyFeatureStruc` (recursive apply, C5/C6/C7);
      re-point NC (`on_unresolved="raise"`) and Phoneme (`"skip"`) at it.
      **Behaviour-preserving -- zero delta.**
- [ ] **T5** `MakeFeatStruc` generalization (C3) -- one implementation; Infl and
      Phon become call-throughs; recursive dict + flat-list alias; `slot=`.
      Closes **#256**.
- [ ] **T6** `MSAOperations`: new `GetSyncableProperties`/`ApplySyncableProperties`,
      `ClassName`-discriminated + cast, all four properties. Closes **#251**.
- [ ] **T7** `POSOperations`: capture + apply `DefaultFeaturesOA` and
      `InherFeatValOA` (coverage-gap fix, no hasattr gate -- D5). Closes **#252**.
- [ ] **T8** `AllomorphOperations`: capture + apply `MsEnvFeaturesOA` (unfiled P0).
- [ ] **T9** `PhonemeOperations`: `:1351` HVO-path cast (C2) **and** `:1431`
      presence gate (C6) **and** struct-GUID preservation -- these three land
      together or none is testable. Then the `on_unresolved` default flips to
      `"raise"` in its **own commit** with a `CHANGELOG.md` `### Changed`
      BREAKING (behavioural) entry. Closes **#253**.
- [ ] **T10** `NaturalClassOperations`: replace the feature-struct `hasattr` gates
      at `:911`, `:913`, `:956`, `:1021` with `ClassName` + cast. (`SegmentsRC`
      gates at `:655`/`:711`/`:766` are OUT -- append to spec 233.)
- [ ] **T11** `InflectionFeatureOperations.py:493` -- complete the #133 fix using
      the C1 resolver (needs T1 + T2).
- [ ] **T12** `CopyFeatStruc` (C8).
- [ ] **T13** Latent truthiness gates: `PhonemeOperations.py:1428`,
      `PhonFeatureOperations.py:760`.
- [ ] **T14** Live verification on Target / `target_sandbox`: nested round-trip
      (write nested -> re-read from the LCM -> compare), empty-but-present struct
      round-trip, per-level `TypeGuid` preservation, per-level GUID preservation,
      `slot=` disambiguation errors, unknown-`ClassName` raise. Evidence ->
      `specs/feature-structure-sync-gap/evidence/live-<task>.md`, `run_mode: live`
      required.
- [ ] **T15** Docs: `docs/API_ISSUES_CATEGORIZED.md` Category 8 entry for the
      varying feature-struct property name; `FeatureStructureRA` on
      `IPhSimpleContextNC`/`IPhSimpleContextSeg` documented as a false-positive
      class; `CHANGELOG.md` entries.
- [ ] **T16** Docs: **`CLAUDE.md` staleness fix** -- see section 7.
- [ ] **T17** Append the three NC `SegmentsRC` rows to
      `specs/233-basetype-cast-sweep/spec.md` section 2 (docs-only).

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

**`CLAUDE.md` is stale on the package directory name (T16).** The project
instructions say `flexlibs2/code/` and `flexlibs2/sync/`; the actual package is
**`flexicon/code/` and `flexicon/sync/`** (`flexlibs2/` does not exist).
Affected: the "Project Structure" tree, the file-header example, the
`Shared.string_utils` / `flexlibs2.APIHelpFile` references, and every path under
"Key Files to Know". This has already cost real work --
`specs/254-getmorphtype-allomorph`'s handoff carries a deferred repo-wide
`flexlibs2` -> `flexicon` import-alias sweep, and
`tests/operations/test_wfi_morph_bundle.py:43,73,104,188` still import the old
name. Fix `CLAUDE.md` in this feature (docs-only, zero risk); the code/test
alias sweep stays deferred as its own PR.

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
