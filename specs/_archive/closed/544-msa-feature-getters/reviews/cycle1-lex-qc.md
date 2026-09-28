# QC Report -- issue #544 (MSA feature-structure getters)
Date: 2026-09-26 | Quality Score: 90/100 | Status: PASS

(Saved by the coordinator; the QC agent had no write tool this session.)

## Pattern-Audit Gate
N/A -- feature addition, not a bugfix-shaped commit. Gate status: PASS

## Live-LCM Evidence Gate
- Touches LCM read path (new getters build on `_GetFeatureStruc` / `_ResolveFeatureStrucOwner`): yes
- Evidence artifact: specs/_archive/closed/544-msa-feature-getters/evidence/live-impl.md -- present
- run_mode: live (cross-checked against tests/live_status.json, `by_class.MSAOperations.read.status == "pass"`)
- Pre/post field values: OK -- real GUIDs read back before/after `MakeFeatStruc(getter_output, owner=<second, independent MSA>)`
- Cleanup: OK -- sena3_sandbox only (tempdir copy), Target never opened, `.fwbackup` fixture git-ignored
- Gate status: PASS

## User constraint: live writes in Sena 3 only
Confirmed. tests/operations/test_msa_feature_getters_live.py header (lines 9-10) states writes go through `sena3_sandbox` only; all 5 live test methods take `sena3_sandbox` (lines 53, 155, 221, 312, 349). No `target_sandbox` / `target_project` reference. No P0.

## (1) Output shape matches `_MakeFeatStruc` input, not raw C4
`__C4ToFeatStrucSpec` (MSAOperations.py:679-721) strips `TypeGuid` / nested `Guid` and returns `{featGuid: valGuid | {...}}`, recursing for `IFsComplexValue` levels (717-718). `BaseOperations.__ResolveFeatStrucOperand` (BaseOperations.py:2953-2995) resolves GUID-string operands at any depth. Live evidence shows a real round-trip onto a second MSA. `TypeGuid` loss is pre-existing (`_MakeFeatStruc` never writes `TypeRA`). PASS.

## (2) Owner resolution and casting
`__ReadMsaFeatureStrucSpec` (MSAOperations.py:754-770) routes exclusively through `_ResolveFeatureStrucOwner`. `__ResolveMsaForFeatures` (723-752) and `__GetMsaObject` (1682+) cast via ClassName dispatch, no hasattr probing of subtype members. `GetFeatures` (973-989) dispatches on `msa.ClassName`. PASS.

## (3) None vs {} semantics, exception types
- Sense with no MSA -> None; wrong MSA class -> None (764-765); null owning prop -> None (712-713); present-but-empty -> `{}` (715). Consistent with `POSOperations.GetDefaultFeatures` / `GetInflAffMsaSlots`.
- `GetFeatures` raises `FP_ParameterError` for `MoDerivAffMsa` with missing/invalid slot (979-984).
- All five getters call `_ValidateParam` first -> `FP_NullParameterError` (lines 804, 841, 879, 917, 967). PASS.

## (4) Docs / style / duplication
Docstrings follow house style (description, Args, Returns, Raises, `project.MSA.*` example). `.pyi` updated (MSAOperations.pyi:44-52). docs/API_ISSUES_CATEGORIZED.md gained Category 14 (1071+), noting `POSOperations.GetDefaultFeatures` is intentionally untouched. No `flexlibs2`, no emoji. Converter centralized in one private helper behind a single choke point. PASS.

## (5) Tests / live evidence
Naming follows convention (`TestC4ToFeatStrucSpec`, `TestExplicitGetters`, `TestGetFeaturesDispatch`; `test_[what]_[expected]`). Live evidence cites exact commands, run_mode "live", and genuine LCM read-back GUIDs. PASS.

## (6) Commit hygiene
Coordinator verified with `git log origin/main..HEAD`: 0d5c181, 3c68402, 3a525dc all use "for #544" (no close/fix/resolve before the number) and carry the Co-Authored-By footer. PASS.

## Issues found
- ~~P2 -- commit messages not independently verified~~ -- resolved by coordinator check above.
- P3 -- `DescribeFeatStruc` display helper and `keys="guid"|"abbr"` option deliberately scoped out (documented, justified against API rule 5); candidate follow-up, not a defect.

No P0 or P1.

## Final Assessment
Overall Score: 90/100
Recommendation: APPROVE
