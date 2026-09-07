# Verification Report -- issue #254 investigation probe (Cycle 1)

**Verdict:** [PASS] (as an investigation probe -- ground truth established, no fix yet designed/verified)
**Live run:** yes | **run_mode:** live
**Evidence:** specs/254-getmorphtype-allomorph/evidence/live-cycle1-probe.md
**Project:** Sena 3 (via `sena3_sandbox` -- disposable tempdir copy, no restore needed)

## Claim vs. observed

| Claim / Question | Observed live | Status |
|---|---|---|
| Q1: `bundle.MorphRA` is an `IMoForm` subtype | 1932 sampled bundles: `MoStemAllomorph` (697), `MoAffixAllomorph` (1142). Zero `MoMorphType`/`ICmPossibility` ClassNames observed. | [PASS] |
| Q2: `IMoForm(bundle.MorphRA).MorphTypeRA.Name` yields real type strings | Distribution: prefix (819), suffix (323), root (468), stem (222), enclitic (7). Concrete prefix/suffix/stem examples captured with real strings. Note: `Name.get_String(anal_ws)` returned empty for all samples -- must use `Name.BestAnalysisAlternative.Text`. | [PASS] |
| Q3: `ICmPossibility(bundle.MorphRA).Name` raises `TypeError` | Confirmed verbatim: `TypeError: object does not implement ICmPossibility` | [PASS] |
| Q4: `bundle.MorphRA` can be `None` on real data | 93 of 1932 sampled bundles (~4.8%) had `MorphRA is None` | [PASS] |
| Q5: `SetMorphType(bundle, IMoMorphType)` -- crash or silent corruption? | `TypeError: SIL.LCModel.DomainImpl.MoMorphType value cannot be converted to SIL.LCModel.IMoForm`, raised before any mutation reaches the LCM. **CRASH, not corruption.** | [PASS] |

## Mock suite (regression, supplementary)

Not run this cycle -- this was an investigation probe against a live
project only, per dispatch instructions. No code under
`flexicon/code/` was modified; only a new test file was added
(`tests/operations/test_issue254_morphra_probe.py`). No regression risk
introduced.

## Key finding for the eventual fix design

- `WfiMorphBundleOperations.GetMorphType()` currently returns
  `bundle.MorphRA` directly and calls it "the morpheme type" -- but
  live data shows this is the **allomorph** (`IMoForm`), not the morph
  **type** (`IMoMorphType`). The real type object is one hop further:
  `IMoForm(bundle.MorphRA).MorphTypeRA`, which can itself be `None`
  even when `MorphRA` is set.
- `SetMorphType(bundle, morph_type_or_hvo)` as currently implemented
  (`WfiMorphBundleOperations.py:877`, `bundle.MorphRA = morph_type`)
  is unusable with an actual `IMoMorphType` argument -- it always raises
  `TypeError` before writing. It is not a silent-corruption risk; it is
  a hard, immediate crash on every real invocation matching its own
  documented example.
- Any fix must account for `MorphRA` being `None` (~5% of real bundles)
  and for `MorphTypeRA` being `None` even when `MorphRA` is set (some
  samples had type_name resolve after retry, but a null‑MorphTypeRA
  path was reachable during earlier debugging and must be guarded).

## Blockers

none

## Recommendation

Proceed to fix design. The programmer should decide whether
`SetMorphType` should (a) accept an `IMoForm` allomorph object directly
(matching what `MorphRA` actually stores), or (b) accept an
`IMoMorphType` and internally resolve/require an allomorph to attach it
to (raising a clear `FP_ParameterError` rather than a raw `TypeError`
if no compatible allomorph exists). This probe supplies the ground
truth needed to make that call; it is not itself the fix and does not
close issue #254.
