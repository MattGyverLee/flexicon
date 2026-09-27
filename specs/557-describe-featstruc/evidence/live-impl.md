# Live verification evidence -- issue #557 (DescribeFeatStruc)

## Change

`InflectionFeatureOperations.DescribeFeatStruc(fs_or_spec, slot=None)`: a
read-only, display-only renderer. No write path is touched.

## Commands run

```
python -m pytest -m "not requires_live_project" -q
```
Result: **2554 passed**, 1052 deselected, 0 failed (includes the 20 new
offline tests in `tests/operations/test_describe_featstruc.py`).

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_describe_featstruc_live.py -m requires_live_project -q -s
```
Result: **2 passed in 4.85s**. `tests/live_status.json`: `"run_mode": "live"`.

## What the live test checked

Project: `sena3_sandbox` (a fresh tempdir copy of
`Sena 3 2026-06-09 1645.fwbackup`). Nothing was written.

For every `IMoMorphSynAnalysis` in the project, every non-empty feature
structure on `MsFeaturesOA` / `InflFeatsOA` / `FromMsFeaturesOA` /
`ToMsFeaturesOA` was rendered by an independent oracle. The oracle walks
`IFsFeatStruc.FeatureSpecsOC` directly and reads each `Abbreviation` from
the LCM, never through the GUID spec. `DescribeFeatStruc` was then called
three ways, and each result had to equal the oracle:

1. on the `MSA.GetFeatures(msa, slot=...)` GUID spec (the #544 getter output);
2. on the owning MSA, with `slot=` for `MoDerivAffMsa`;
3. on the `IFsFeatStruc` itself.

The test also checked that no GUID from the spec appears in the rendered
text.

- **Structures checked:** 719, including nested `IFsComplexValue` levels
  and a `MoDerivAffMsa.ToMsFeaturesOA`.
- **Sample values read from the LCM** (pre-state = post-state, since this
  is read-only):

```
hvo=4977 ToMsFeaturesOA: [NounAgr: [genro: 7/8]]
hvo=90   MsFeaturesOA:   [NounAgr: [genro: 3/4]]
hvo=211  MsFeaturesOA:   [NounAgr: [genro: 5/6]]
hvo=241  MsFeaturesOA:   [NounAgr: [genro: 1/2]]
hvo=742  MsFeaturesOA:   [NounAgr: [genro: 12/8]]
hvo=645  MsFeaturesOA:   [NounAgr: [genro: 9/10]]
```

- **Null case:** A stem MSA with a null `MsFeaturesOA` returned `None` from
  `GetStemFeatures` and `""` from `DescribeFeatStruc`. `DescribeFeatStruc(None)`
  also returned `""`.

## Verdict

PASS (live).
