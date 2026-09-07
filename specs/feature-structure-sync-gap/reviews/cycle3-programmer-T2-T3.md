# Cycle 3 -- Programmer report: T2 + T3

## (a) Where the C1 table lives, and why

`FEATURE_STRUC_OWNER_TABLE` lives in `flexicon/code/Shared/lcm_constants.py`
(one dict, 8 keys, each a tuple of `(slot, owning_property, props_key)`
rows) -- NOT as a `BaseOperations.py` literal. Two reasons: (1)
`BaseOperations.py` already imports from `lcm_constants.py`
(`OWNING_SEQUENCE_SUFFIX`), so this is one more import, not a new
dependency direction; (2) every future consumer (T4's `_ApplyFeatureStruc`,
T5's generalized `MakeFeatStruc`, T6-T9's per-domain
Get/ApplySyncableProperties) can import the table directly from `Shared/`
the same way `InflectionFeatureOperations.py` already imports
`Shared.string_utils`/`Shared.catalog`, without needing `BaseOperations`
itself. `BaseOperations.py` imports it as
`FEATURE_STRUC_OWNER_TABLE` alongside the existing import.

## (b) Diff summary

- `Shared/lcm_constants.py`: +82 lines, the frozen C1 table plus its
  rationale/exclusion comment block. Pure data, no `SIL.LCModel` import.
- `BaseOperations.py`: +361 lines, three new methods inserted between
  `_GetTypedOwner` and `_RejectLegacyKwargs`:
  - `_ResolveFeatureStrucOwner(owner, slot=None)` -- unwraps
    wrapper-style owners, raises `FP_ParameterError` naming the ClassName
    for an unrecognized/excluded row, raises naming valid slots for an
    ambiguous owner with no/wrong `slot=`, ignores `slot=` on a
    single-row owner, then casts via `getattr(SIL.LCModel, "I"+ClassName)`
    directly (uncaught -- a wrong cast raises `TypeError` loudly, per C1
    step 5) and returns `(concrete_owner, prop_name)`.
  - `_GetFeatureStruc(struct, _top_level=True)` -- recursive C4
    serializer; `None` in -> `None` out; discriminates
    `FsClosedValue`/`FsComplexValue` by `.ClassName`, casts explicitly,
    recurses into `ValueOA` with `_top_level=False` so only nested levels
    carry `"Guid"`. Documents C4a in its own docstring verbatim (legacy
    NC/Phoneme flat-list capture is unmigrated; this method always emits
    C4).
  - `_ResolveFsByGuid(guid, kind=None)` -- `project.Object(guid)` /
    except -> `None`, mirroring the NC/Phoneme private twins but as a new
    shared, additive method.
- `tests/operations/test_feature_struc_resolver.py`: new file, 13 offline
  + 16 live tests.
- `specs/feature-structure-sync-gap/evidence/live-t2-t3.md`: new evidence
  file.

No other `flexicon/code/` file touched.

## (c) Zero-delta proof

`git status` shows only the two files above changed under `flexicon/code/`.
Offline suite: 1277 pre-existing + 13 new = 1290 passed. Live: existing
`TestFeatureStructOwnerCastT1`, all of
`test_natural_class_feature_sync.py` (including the `__ResolveByGuid`
source-text pin at ~:145), and the cycle-1 probe file all pass unchanged
(9 passed, live). `NaturalClassOperations.py`/`PhonemeOperations.py`'s
private `__ApplyFeatures`/`__ResolveByGuid` are untouched byte-for-byte.

## (d) Nested-struct construction recipe (for T4/T5 reuse)

Ownership-first at every level, RAW factories, no `MakeFeatStruc`:
`top = fs_factory.Create(); owner.MsFeaturesOA = top` (re-fetch);
`cv = cv_factory.Create(); top.FeatureSpecsOC.Add(cv)` (re-cast
`IFsComplexValue`); `cv.FeatureRA = complex_feat_defn`;
`nested = fs_factory.Create(); cv.ValueOA = nested` (re-cast
`IFsFeatStruc`); `nested.TypeRA = some_type`; `clv = clv_factory.Create();
nested.FeatureSpecsOC.Add(clv)` (re-cast `IFsClosedValue`);
`clv.FeatureRA/.ValueRA = ...`. Real `IFsClosedFeature`/`IFsSymFeatVal`/
`IFsComplexFeature`/`IFsFeatStrucType` objects came from
`InflectionFeatureOperations.Create(type="closed"/"complex")`,
`.CreateValue(...)`, `.TypeCreate(...)` -- no need to hand-roll those too.

## (e) Sena 3 natural nesting

**717/719 (99.7%)** of Sena 3's populated MSA feature structures are
naturally nested (measured live via `_GetFeatureStruc` itself). Corroborates
cycle-1's Ngoreme finding (799/820) on a second project.

## (f) Offline + live results

Offline: 1290 passed. Live (`FLEXLIBS_REQUIRE_LIVE=1`,
`tests/live_status.json` -> `"run_mode": "live"`): 16/16 new tests passed
against `target_sandbox`; 9/9 pre-existing regression tests passed
unchanged. Full commands and re-queried pre/post GUIDs in
`specs/feature-structure-sync-gap/evidence/live-t2-t3.md`.
