# Live verification -- T4.4 (Q2 probe: MSA sharing across morph bundles)

**Project:** Sena 3 | **Fixture:** sena3_sandbox (tempdir copy of the
.fwbackup -- the real Sena 3 was never opened; no write of any kind was
issued, so no restore script was invoked)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q -k TestPart7MsaSharingQ2 -s
```
**run_mode:** live (confirmed via
`python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"`
-> `live`)
**Date:** 2026-09-18

## Claim under test

Q2 (spec.md:265): does writing `msa.InflectionClassRA` through a
`IWfiMorphBundle` handle risk mutating OTHER bundles, because an
`IMoStemMsa` can be a shared (RA = reference, not owned) target of many
`IWfiMorphBundle`s? This gates ruling C11 / whether `SetInflectionClass`
should refuse, warn, or silently accept a write on a shared MSA.

## Test added

`TestPart7MsaSharingQ2::test_7a_msa_sharing_census_sena3` in
`tests/operations/test_lcm_member_truth_sweep.py` (the campaign's existing
live file). Pure read-only probe: no `_TransactionCM`, no seeded `TEST_`
object, no write of any kind, so no `finally:` restore is needed.

## Measurements (read live from the LCM, Sena 3 sandbox)

### 1. Total `IWfiMorphBundle` count

Enumerated exhaustively via `project.ObjectsIn(IWfiMorphBundleRepository)`
(`.AllInstances()` under the hood) -- the same production pattern already
used by `MSAOperations.RemoveOrphanedMsas` (`MSAOperations.py:748`).

**Total = 1932.**

**This CORRECTS the campaign's prior figure of 1838.** 1838 is not the
total bundle count -- it is, as measurement 2 below shows, exactly the
count of bundles with a *non-null* `MsaRA`. The prior figure conflated
"bundles with a resolvable MSA" with "all bundles." The true total
(including the 94 bundles whose `MsaRA` is null) is 1932.

### 2. Bundles with a null `MsaRA`

- Null `MsaRA`: **94**
- Non-null `MsaRA`: **1838** (= 1932 - 94; matches the campaign's prior
  figure, but as the non-null subset, not the total)

### 3. Breakdown of non-null MSAs by concrete `ClassName` (post
`cast_to_concrete`)

| ClassName | Count |
|---|---|
| MoStemMsa | 694 |
| MoInflAffMsa | 1109 |
| MoDerivAffMsa | 32 |
| MoUnclassifiedAffixMsa | 3 |
| **Non-stem total** | **1144** |

**Confirms the campaign's prior figure of 1144 non-stem exactly**
(1109 + 32 + 3 = 1144; 694 + 1144 = 1838 non-null bundles, consistent
with measurement 2).

### 4. THE Q2 NUMBER -- MSA sharing across bundles

Of the 1838 bundles with a non-null `MsaRA`:

- **Bundles whose MSA is shared with >= 1 other bundle: 1648**
- **Percentage of non-null-`MsaRA` bundles that share: 89.66%**
- **Distinct MSAs referenced by MORE THAN ONE bundle: 203**
  (out of 393 distinct MSA objects referenced in total)
- **MAXIMUM fan-out (bundles pointing at a single MSA): 267**

### 5. Stem-MSA bundles with a non-null `InflectionClassRA` today

- IMoStemMsa-typed bundles with non-null `InflectionClassRA`: **0**
- IMoStemMsa-typed bundles with null `InflectionClassRA`: **694**
- Stem-MSA bundle total: **694**

Every single stem MSA referenced by a morph bundle in Sena 3 has a null
`InflectionClassRA` today. The current read path is not dropping any real
inflection-class data on the floor in this dataset -- there is none set to
drop. (This does not mean the field is never populated in other projects;
it means Sena 3's own stem MSAs carry no inflection-class value to lose.)

### 6. Sanity reflection (live `clr.GetClrType`)

- `IWfiMorphBundle` has `InflClassRA`: **False** (confirmed absent --
  issue #259 premise holds)
- `IMoStemMsa` has `InflectionClassRA`: **True** (confirmed present)
- `IMoInflAffMsa` has `InflectionClassRA`: **False**
- `IMoDerivAffMsa` has `InflectionClassRA`: **False**
- `IMoUnclassifiedAffixMsa` has `InflectionClassRA`: **False**

All six sanity assertions passed live; none of the affix MSA subtypes
carry `InflectionClassRA`.

## Action

Read-only probe. `project.ObjectsIn(IWfiMorphBundleRepository)` was
enumerated once; for each bundle, `MsaRA` was read, `cast_to_concrete()`
was applied, `ClassName`/`Hvo`/`InflectionClassRA` were read where
applicable, and `clr.GetClrType` was used for the CLR-surface sanity
checks. No property was ever set; no factory `.Create()` was called; no
`_TransactionCM` was opened.

## Cleanup

None required -- no write of any kind was issued. `sena3_sandbox` is a
tempdir copy discarded by pytest fixture teardown after the test; the real
Sena 3 project was never opened, and `scripts/restore_sena3.py` was not
invoked (nothing to restore).

## Result

[PASS] -- live run against the Sena 3 sandbox, `run_mode: live`. All six
requested measurements produced. The campaign's prior total-bundle figure
(1838) is corrected to 1932 (1838 was actually the non-null-`MsaRA`
subset); the prior non-stem figure (1144) is confirmed exact.
