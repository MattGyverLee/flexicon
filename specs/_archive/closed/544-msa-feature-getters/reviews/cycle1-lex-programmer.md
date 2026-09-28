# Cycle 1 -- MSA feature-structure getters (issue #544)

## Files changed

- `flexicon/code/Lexicon/MSAOperations.py` -- 5 new public getters +
  3 private helpers (`__C4ToFeatStrucSpec`, `__ResolveMsaForFeatures`,
  `__ReadMsaFeatureStrucSpec`), inserted after `GetInflAffMsaSlots`.
- `flexicon/code/Lexicon/MSAOperations.pyi` -- stub entries for the 5
  new methods.
- `docs/API_ISSUES_CATEGORIZED.md` -- new "Category 14" section.
- `tests/operations/test_msa_feature_getters.py` -- 22 offline unit
  tests (converter shape, dispatch, None/{} semantics, deriv slot
  error, plus a cycle-2 regression test locking that the converter
  never attribute-accesses a raw LCM object).
- `tests/operations/test_msa_feature_getters_live.py` -- 5 live tests,
  `requires_live_project`, all writes via `sena3_sandbox`. Cycle 2
  fixed a missing `IFsFeatStruc(...)` cast in this file's own
  re-read assertion (test bug, not a library bug -- see evidence file).
- `specs/_archive/closed/544-msa-feature-getters/evidence/live-impl.md` -- evidence
  file, rewritten in cycle 2 with a real live PASS and pre/post GUIDs
  read back from the LCM.

## API added (all `@OperationsMethod` on `MSAOperations`)

```
GetStemFeatures(sense_or_msa) -> dict | None
GetInflAffFeatures(sense_or_msa) -> dict | None
GetDerivFromFeatures(sense_or_msa) -> dict | None
GetDerivToFeatures(sense_or_msa) -> dict | None
GetFeatures(sense_or_msa, slot=None) -> dict | None
```

Each returns `{featureGuid: valueGuid | {...}}`, never the raw C4
sync wire format. `None`: sense with no MSA, null owning property, or
(explicit getters only) wrong MSA class. `{}`: present-but-empty
struct. `GetFeatures` dispatches on `msa.ClassName`; raises
`FP_ParameterError` for `MoDerivAffMsa` with no/invalid `slot`; returns
`None` for `MoUnclassifiedAffixMsa` and any out-of-table `ClassName`.
`FP_NullParameterError` on a null `sense_or_msa` (all five methods, via
`_ValidateParam`).

## Round-trip shape decision

`_MakeFeatStruc`'s `__ResolveFeatStrucOperand` resolves a GUID *string*
via `project.Object(guid)` for either a feature or value operand
(confirmed by reading `BaseOperations.py:2953-2995`), so a dict of
GUID-string keys/values recursively nested is a valid, unambiguous
`MakeFeatStruc` input. `__C4ToFeatStrucSpec` performs exactly that
conversion from `_GetFeatureStruc`'s C4 dict, dropping `TypeGuid` at
every level (confirmed `_MakeFeatStruc`/`__PopulateFeatStrucLevel` never
sets `TypeRA` -- only the C4/C5 sync-apply surface,
`_ApplyFeatureStruc`, does -- so `TypeGuid` carries no round-trip value
and its loss is a pre-existing `MakeFeatStruc` limitation, not a new
one). The optional `keys="guid"|"abbr"` call-site flag was **not**
added: GUID keys are the only unconditionally-correct round-trip shape
(names can rename/collide), so a flag here would be exactly the
"behaviour that should be unconditional" anti-pattern API rule 5 warns
against. `DescribeFeatStruc` (optional display helper) was also
skipped to stay in scope; flagged for a follow-up if wanted.

## Offline results

```
python -m pytest tests/operations/test_msa_feature_getters.py -q -m "not requires_live_project"
-> 22 passed
python -m pytest -m "not requires_live_project" -q
-> 2515 passed, 4 pre-existing failures in
   tests/operations/test_morphrule_duplicate_deep.py (confirmed present
   on unmodified origin/main via git stash before this change)
```

## Live results

**PASS (cycle 2, superseding cycle 1's "FAIL: unverified").** Cycle 1's
blocker report was wrong: the fixture is git-ignored and just hadn't
been copied into this worktree yet ("No module named SIL" before
flexicon's own FLEx init is a normal transient, not a missing-install
signal). With `tests/fixtures/Sena 3 2026-06-09 1645.fwbackup` in
place:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_msa_feature_getters_live.py -m requires_live_project -q
-> 5 passed
```

`tests/live_status.json` confirms `"run_mode": "live"` and
`by_class.MSAOperations.read.status == "pass"`.

The first live run caught a real `AttributeError` in
`TestStemFeaturesRoundTripLive` (missing `IFsFeatStruc(...)` cast on a
nested `ValueOA` re-read). Investigated per Category 8 and confirmed
this is a **test-assertion bug, not a library bug**:
`BaseOperations._GetFeatureStruc` already performs that exact cast
internally (`BaseOperations.py:2201-2204`), and the new
`__C4ToFeatStrucSpec` converter never touches a raw LCM object at all
(it only walks the already-serialized C4 dict). Fixed the test's own
cast and added an offline regression test,
`TestC4ToFeatStrucSpec.test_converter_never_touches_a_raw_lcm_object`,
pinning that the converter cannot regress into this bug shape. No
library code (`BaseOperations.py`, `MSAOperations.py`) changed as a
result. Full transcript, real pre/post GUIDs read back from the LCM,
and the PASS line are in
`specs/_archive/closed/544-msa-feature-getters/evidence/live-impl.md`.

All live writes went through `sena3_sandbox` only; `Target` was never
opened. The `.fwbackup` fixture is git-ignored and was not committed.

## Commits (branch `fix/544-msa-feature-getters`, not pushed)

- `0d5c181` -- feat(lexicon): add MSA feature-structure getters, for #544
- `3c68402` -- test(lexicon): add live round-trip coverage for MSA
  feature getters, for #544
- (cycle 2) -- fix the live test's missing `IFsFeatStruc(...)` cast,
  add the converter regression test, rewrite the evidence file with
  the real live PASS
