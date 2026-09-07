# Verification Report -- feature-structure-sync-gap / cycle1 (issues #251, #252, #256)

**Verdict:** [PASS] (reconnaissance-only cycle; no fix code exists yet to verify against a claim -- this report certifies the GROUND TRUTH the fix must be designed against, gathered live)
**Live run:** yes | **run_mode:** live
**Evidence:** specs/feature-structure-sync-gap/evidence/live-cycle1-probe.md
**Project:** Ngoreme FLEx (read-only) + Target (via target_sandbox only; the real Target was never opened)

## Scope note

This cycle is explicitly READ-ONLY / SANDBOX-ONLY reconnaissance, per the
dispatch: establish ground truth for the #251/#252/#256 cluster BEFORE any
code is written. There is no implementation to verify a claim against
yet, so the table below maps each of the 9 checklist items to its live
observed value rather than a claim-vs-observed diff. No write touched the
real Target project; test_issue251_252_256_feature_struct_probe.py uses
a custom read-only ngoreme_readonly fixture (writeEnabled=False) for
items 1/3/4/5/6, and target_sandbox (tempdir copy) for items 1(b)/7/8b/9.

## Checklist item vs. observed (live)

| # | Question | Observed live |
|---|---|---|
| 1 | hasattr(msa, prop) under base-interface view | **False for 100%** of 1951+134+3 live MSAs in Ngoreme FLEx; reproduces the known pythonnet static-wrapper-type trap |
| 1 | hasattr under factory-fresh concrete view | True (MSAOperations.CreateStem etc. already cast) |
| 2 | Correct cast route (IMoStemMsa(obj).MsFeaturesOA) | Works |
| 2 | Wrong cast (IMoInflAffMsa on a MoStemMsa) | Raises TypeError immediately at cast time -- loud, not silent |
| 3 | POS.DefaultFeaturesOA / InherFeatValOA existence+type | Both exist, both IFsFeatStruc-typed, hasattr True for 26/26 (POSOperations.GetAll() already casts to IPartOfSpeech) -- #252 is a pure coverage gap, not a hasattr trap |
| 4 | Adjacent candidates (IMoDerivStepMsa, IMoUnclassifiedAffixMsa, IMoAffixAllomorph, ILexEntryInflType) | 3 of 4 carry an IFsFeatStruc-typed property; IMoUnclassifiedAffixMsa has none at all -- widens true fix scope |
| 5 | Nested shape (real Bantu noun-agreement) | Confirmed live: IFsFeatStruc(TypeRA=NULL) > IFsComplexValue('noun agreement') > IFsFeatStruc(TypeRA=FsFeatStrucType:8465) > 2x IFsClosedValue. Only the OUTER TypeRA is null, contradicting the brief's assumption that both levels are typeless |
| 6 | Counts (Ngoreme FLEx) | 1951/134/3 MSAs (stem count corrects reporter's cited 1949 by +2); 782/38/0 with non-null feature structs; 799 nested vs 21 flat (nesting is the MAJORITY shape) |
| 7 | Reproduce #256 (MakeFeatStruc on MSA owner) | FP_ParameterError every time, INCLUDING for a concrete-typed MSA -- root cause is a hard-coded property name (owner.FeaturesOA), not a hasattr/casting bug |
| 8 | Create(Guid) on Fs*Factory types | Naive reflection said No (misleading -- GetMethods() doesn't flatten interface inheritance); corrected reflection + a real functional round-trip via _CreateWithGuid say **Yes**, all three factories preserve GUIDs |
| 9 | Ownership-first rule | Confirmed: free-floating IFsFeatStruc.FeatureSpecsOC getter itself throws NullReferenceException; attach-then-populate succeeds |

## Mock suite (regression, supplementary)

Not run this cycle -- no code was changed, so there is nothing for the
mock suite to regress-check yet. Will run
`python -m pytest -m "not requires_live_project" -q` once a fix lands.

## Key findings for the fix design (not covered by a mock-only pass)

1. **#251 (MSAOperations)**: any naive `GetSyncableProperties` gating on
   `hasattr(msa, "MsFeaturesOA"/"InflFeatsOA"/...)` will be **100% dead
   code** against live data, exactly repeating the f424f96 & 3abf6b5
   NaturalClassOperations mistake. Discriminate by `.ClassName` and cast
   explicitly (`IMoStemMsa(msa)` etc.), never by hasattr on a
   subtype-only member.
2. **#252 (POSOperations)**: NOT a hasattr trap -- `GetAll()` already
   casts to concrete `IPartOfSpeech`. Purely a missing-capture bug; add
   `DefaultFeaturesOA`/`InherFeatValOA` to the existing capture loop.
3. **#256 (InflectionFeatureOperations.MakeFeatStruc)**: NOT a hasattr/
   casting bug either -- `owner.FeaturesOA` is a wrong hard-coded property
   name for every MSA type (they use `MsFeaturesOA`/`InflFeatsOA`/
   `FromMsFeaturesOA`/`ToMsFeaturesOA` instead). Needs an owner-type ->
   property-name dispatch table, plus a nesting parameter (specs can
   contain sub-specs producing `IFsComplexValue` children), plus a
   second explicit cast (`IFsFeatStruc(complex_value.ValueOA)`) at every
   nesting level when reading back.
4. GUID-preserving struct creation IS possible for all three Fs*
   factories via the existing `_CreateWithGuid` helper -- no new
   factory-detection logic is needed for that part of the sync contract.
5. The ownership-first rule generalizes: every level of a nested
   structure (including a complex value's `ValueOA`) must be attached to
   its LCM owner before its own `FeatureSpecsOC` is populated or even
   read.

## Blockers

none

## Recommendation

Proceed to design/implementation for #251/#252/#256 using the findings
above. Re-verify live (Target write-path via target_sandbox or
target_project, per CLAUDE.md) once the fix is written -- this cycle's
evidence establishes ground truth only, it does not verify a fix.
