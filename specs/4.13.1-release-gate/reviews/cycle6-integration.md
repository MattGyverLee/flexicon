# Cycle 6 integration

**Contract** (`extract_lcm_contract.py -o ...expected_contract.json`): exactly one entry added,
`files/code/Lexicon/AllomorphOperations.py/imports/SIL.LCModel: IMoAffixForm`. Nothing removed or moved.
IConstChartRow and ClauseTypes did NOT appear (#832 dropped the ClauseTypes import; row cast uses ClassName strings). All attributable to #830.

**Surface baseline**: none records parameter names. Checked tests/docstring_example_baseline.json (counts of bad examples),
test_operations_baseline.py (method presence), liblcm_baseline.json (LCM-side), issue339 import surface, pyi return ratchet.
No update needed for the #832 rename; all pass.

**Unowned files fixed**
- test_issue581_offline.py: stub gained IMoAffixForm; `_make_affix_allomorph` gained InflectionClassesRC. Infl-class tests moved to affix
  allomorphs (Get/Add/Remove, hvo, idempotent no-ops); non-stem tests replaced by stem checks (Get == [], Add/Remove raise
  FP_ParameterError naming SetInflectionClass, no transaction). 34 pass.
- test_issue471_..._offline.py: example-media removed from the Remove/Add ratchet params (with comment); new class asserts
  Example.MoveMediaFile code has no MediaFilesOS, warns DeprecationWarning, raises FP_ParameterError. Pronunciation/picture cases unchanged.
- demos/demo_discourse_operations.py: AddDependentClause now passes a row (`dependent_row=row2`), skipped if none. No other
  callers in demos/ or examples/.

**Offline gate**: 4006 passed, 0 failed, 1301 deselected.

**Breaking changes for cycle-7 footer**
- #830: Allomorphs.Get/Add/RemoveInflectionClass now operate on MoAffixAllomorph/MoAffixProcess (IMoAffixForm). Stem allomorphs: Get returns []
  (was their list); Add/Remove raise FP_ParameterError naming project.MSA.SetInflectionClass (affix previously raised). Other classes raise FP_ParameterError.
- #831: Examples Add/Remove/Move MediaFile always raise FP_ParameterError (+DeprecationWarning, no write-enabled check); GetMediaFiles -> [],
  GetMediaCount -> 0, both with DeprecationWarning.
- #832: AddDependentClause(marker_or_hvo, row_or_hvo), InsertDependentClause(marker_or_hvo, index, row_or_hvo): second argument renamed
  (was a marker; keyword callers break) and must be a ConstChartRow, else FP_ParameterError. GetDependentClauses returns IConstChartRow.
  Normal-type rows log a warning.

**Patch**: specs/4.13.1-release-gate/reviews/cycle6-diff.patch, 106777 bytes, 22 files.
