# Cycle 1 programmer report: issue 630

## Changes
flexicon/code/Lexicon/MSAOperations.py
- l.971-1040: comment block + `_EXCEPTION_FEATURE_SIDES`, `_EXCEPTION_FEATURE_TYPES_MSG`, and new
  `__ExceptionFeatureRC(msa, side)` replacing `__ProdRestrictRC`/`_PROD_RESTRICT_MSA_CLASSES`.
  Dispatches on ClassName and casts to IMoStemMsa / IMoInflAffMsa / IMoDerivAffMsa:
  Stem -> ProdRestrictRC (side ignored, but validated); Infl -> FromProdRestrictRC (side="to" raises);
  Deriv -> From/ToProdRestrictRC; other -> FP_ParameterError naming the three types and their fields.
- l.1042: `__RCHasItems` static helper.
- l.1071 `GetExceptionFeatures(self, msa_or_hvo, side="from")`
- l.1138 `AddExceptionFeature(self, msa_or_hvo, feature_or_hvo, side="from")`
- l.1200 `RemoveExceptionFeature(self, msa_or_hvo, feature_or_hvo, side="from")`
  Docstrings list fields per type and side semantics; point to InflectionFeatures.ExceptionFeature*.
  Choice: GetExceptionFeatures on MoUnclassifiedAffixMsa now RAISES FP_ParameterError (was []), consistent with
  Add/Remove; documented in the docstring (behavior change).
- l.1763 / l.1785: ChangeAffixVariant (clone path, ~1643 docstring) claimed From/ToProdRestrictRC loss warnings
  but never checked them; added the checks (warn only when the collection is non-empty). Docstring unchanged.
- InflectionClassGetAll: the "in practice inflection classes" claim was already removed in #631; nothing to change.
docs/API_ISSUES_CATEGORIZED.md: Category 8 exception-feature field table + "Issue #630" entry.

## Tests
- tests/operations/test_574_msa_exception_features.py: fake MSAs now per-type (as in LCM); new
  TestPerTypeMappingAndSide (side validation, mapping, error message). 39 pass.
- tests/operations/test_issue630_affix_msa_exception_features_live.py (new, sena3_sandbox, requires_live_project):
  5 pass (infl from add/idempotent/remove, infl side=to raises, deriv from/to independent, invalid side, stem regression).
- `python -m pytest -m "not requires_live_project" -q`: 3710 passed.
- Live command: 5 passed; tests/live_status.json run_mode "live".

## Evidence
specs/issues-630-631-exception-features/evidence/live-630.md
