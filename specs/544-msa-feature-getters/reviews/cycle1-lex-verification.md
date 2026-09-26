# Verification Report -- issue #544 (MSAOperations feature-structure getters)

**Verdict:** PASS
**Live run:** yes | **run_mode:** live
**Evidence:** specs/544-msa-feature-getters/evidence/live-verification.md
**Project:** Sena 3 only (sandbox copies); Target never opened

## Claim vs. observed

| Claim | Observed live | Status |
|-------|---------------|--------|
| GetStemFeatures round-trips through MakeFeatStruc onto a 2nd MSA | pre/post GUID dicts equal, re-queried from LCM | PASS |
| GetInflAffFeatures reads InflFeatsOA correctly | matches expected GUID dict | PASS |
| GetDerivFromFeatures / GetDerivToFeatures independent slots round-trip onto 2nd MSA | both slots equal after re-query | PASS |
| GetFeatures dispatches by ClassName | infl/stem/deriv all resolved correctly | PASS |
| GetFeatures(deriv_msa, slot=None) raises FP_ParameterError | raised with correct message | PASS |
| None vs {} semantics (no MSA / null prop / wrong class vs empty struct) | unclassified affix -> None, null MsFeaturesOA -> None, explicit empty MakeFeatStruc({}) -> {} | PASS |
| Getter output matches a raw IFsFeatStruc walk on real pre-existing data | 3 real Sena 3 MSAs, raw walk == GetFeatures output | PASS |
| No library write leaked outside sandbox | tempdir copies used throughout; cleanup confirmed each run; real .fwbackup untouched; Target never opened | PASS |

## Commands run (this verification, independent of programmer's own report)

```
cd C:\Github\flexicon-544
python -m pytest -m "not requires_live_project" -q
-> 4 failed (pre-existing, in test_morphrule_duplicate_deep.py, unrelated
   Operations class), 2515 passed, 1041 deselected

$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_msa_feature_getters_live.py -m requires_live_project -q
-> 5 passed

python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"
-> live
```

Plus an independent ad-hoc script (own FLEx init + own tempdir Sena 3
sandbox copy, not the pytest fixture) exercising the same public API a
second, separate way -- see evidence file for full pre/post GUID values.

## Mock suite (regression, supplementary)

Command: `python -m pytest -m "not requires_live_project" -q`
Result: 2515 passed, 4 failed
Pre-existing failures (not caused by this change): all 4 in
`tests/operations/test_morphrule_duplicate_deep.py` -- a different
Operations class, untouched by this branch's diff (`MSAOperations.py`,
`MSAOperations.pyi`, `docs/API_ISSUES_CATEGORIZED.md`,
`tests/operations/test_msa_feature_getters.py`,
`tests/operations/test_msa_feature_getters_live.py`).

## Blockers

none

## Recommendation

APPROVE
