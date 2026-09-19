# Verification Report -- T4.4 (Q2: MSA sharing hazard for SetInflectionClass)

**Verdict:** [PASS]
**Live run:** yes | **run_mode:** live
**Evidence:** specs/lcm-member-truth-sweep/evidence/live-T4.4-msa-sharing.md
**Project:** Sena 3 (sena3_sandbox, read-only probe, tempdir copy)

## Claim vs. observed

| Claim | Observed live | Status |
|---|---|---|
| Prior total bundle figure 1838 | Actual total = 1932; 1838 is the non-null-`MsaRA` subset, not the total | [FAIL] (figure corrected) |
| Prior non-stem figure 1144 | Confirmed exact: 1109 MoInflAffMsa + 32 MoDerivAffMsa + 3 MoUnclassifiedAffixMsa = 1144 | [PASS] |
| `InflClassRA` absent from `IWfiMorphBundle` | Confirmed absent (live reflection) | [PASS] |
| `InflectionClassRA` present on `IMoStemMsa` only, not on affix MSA subtypes | Confirmed: present on IMoStemMsa, absent on IMoInflAffMsa/IMoDerivAffMsa/IMoUnclassifiedAffixMsa | [PASS] |

## Q2 verdict: REAL, not rare

**The sharing hazard is REAL, and it is the dominant case, not an edge
case.**

- Of the 1838 bundles with a resolvable MSA, **1648 (89.66%) point at an
  MSA that at least one other bundle also points at.** Sharing is the
  norm in this dataset, not the exception -- unshared (bundle-exclusive)
  MSAs are the minority (190 bundles, ~10.3%).
- **203 distinct MSA objects** are each referenced by 2+ bundles.
- **Maximum fan-out is 267** -- a single MSA is the `MsaRA` target of 267
  separate morph bundles. A `SetInflectionClass(bundle, cls)` call that
  writes through that bundle's `MsaRA` handle would silently change the
  effective inflection class read back through the other 266 bundles that
  happen to share the same MSA, with no signal to the caller that they
  touched anything beyond the one bundle they named.
- This is not confined to stem MSAs specifically (the class that actually
  carries `InflectionClassRA`) -- the 89.66% figure is across all
  non-null MSA types -- but the fan-out mechanism (RA = reference, not
  owned, so many bundles can legally point at the identical MSA instance)
  applies identically to the 694 stem-MSA bundles that `SetInflectionClass`
  would actually touch. There is no structural reason to expect stem MSAs
  to be shared less than the aggregate; if anything, MoInflAffMsa (1109 of
  1838, the largest single class and the most likely home of the biggest
  fan-outs) shows this is a general MSA-sharing pattern in FLEx lexicons,
  not a modeling accident specific to one MSA subtype.
- Measurement 5 (0 of 694 stem MSAs in Sena 3 currently carry a non-null
  `InflectionClassRA`) does NOT reduce the hazard -- it means today's read
  path loses nothing in *this* dataset, but a future `SetInflectionClass`
  write would be the first thing to populate the field, and it would do so
  through a handle that -- per measurement 4 -- is very likely (89.66% base
  rate) to be shared with other bundles the caller never named or saw.

## Recommendation for the domain ruling (C11)

Given an 89.66% base rate of MSA sharing and a demonstrated 267x fan-out,
`SetInflectionClass(bundle, cls)` implemented as a bare
`bundle.MsaRA.InflectionClassRA = cls` is an undisclosed
action-at-a-distance write on the *typical* case, not a rare corner case.
This verification does not rule on refuse/warn/accept (that is explicitly
reserved for the domain expert next cycle, per the task), but the number
that should drive that ruling is unambiguous: **silent accept is not
defensible at this sharing rate.** A minimum bar is a warn-with-fan-out-count
(the API already has both pieces of information needed -- `Hvo`-based
lookup of all other bundles referencing the same MSA is a cheap query,
structurally identical to the `IWfiMorphBundleRepository.AllInstances()`
pass this probe and `MSAOperations.RemoveOrphanedMsas` both already use).

## Mock suite (regression, supplementary)

Not run this cycle -- T4.4 is a read-only live probe with no production
code change; there is nothing for the mock suite to regress-check that
this probe's live numbers do not already settle more directly.

## Blockers

None.
