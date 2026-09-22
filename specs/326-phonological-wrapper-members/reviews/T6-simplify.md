# T6 Simplify — Issue #326 (post-T5 cleanup)

Worktree: `C:/Github/flexicon-326`. Behaviour-preserving only; no commit.

## Scope

Remove dead guards and orphaned scaffolding after T5. Keep all four public reduplication
symbols (`redup_rules`, `has_redup_parts`, `redup_parts`, `as_reduplication_rule`) with
`DeprecationWarning` through v5.0.0. No `docs/` edits.

## Files touched

| File | Change |
| --- | --- |
| `flexicon/code/Grammar/phonological_rule.py` | Dropped unused `cast_to_concrete` import (T5 leftover). Removed redundant `hasattr(RightHandSidesOS)` in `output_specs` (already gated by `has_output_specs`). Removed redundant `hasattr(StrucDescOS)` in `_metathesis_ranges` (outer `try`/`except` preserves behaviour). |
| `flexicon/code/System/phonological_context.py` | Dropped unused `cast_to_concrete` import. Replaced `hasattr`/`FeatureStructureRA` branches with `getattr(..., None)` for `segment` and `natural_class` (same semantics for missing or null FSRA; SegmentRA/NaturalClassRA guards were already gone after T5). |
| `flexicon/code/Shared/smart_collection.py` | Module and `__str__` docstring examples: removed invented `PhReduplicationRule` line; counts now 10 total (7 regular / 3 metathesis). |
| `flexicon/code/lcm_casting.py` | Removed redundant 4-line reduplication comment above `_get_factory_for_class` factory map (slot removal and module comment already document issue #326). |
| `tests/test_phonological_rules_wrappers.py` | `TestPhonologicalRuleDeprecation._make_wrapper` patches `wrapper_base.cast_to_concrete` instead of the removed phonological_rule import (test fix only). |

## Deleted vs kept

**Deleted / simplified**

- Unused `cast_to_concrete` imports in `phonological_rule.py` and `phonological_context.py`.
- Redundant defensive `hasattr` in metathesis/output-spec paths listed above.
- `PhReduplicationRule` from `SmartCollection` **source** docstring examples (not public API).
- Verbose factory-map reduplication comment in `lcm_casting.py`.

**Kept (intentional)**

- `has_redup_parts`, `redup_parts`, `as_reduplication_rule`, `RuleCollection.redup_rules()` with
  `_REDUP_DEPRECATION_MSG` / inline warnings and v5.0.0 messaging.
- `hasattr` on real LCM fields where still needed (e.g. `has_output_specs` + `RightHandSidesOS`,
  `input_contexts` + `StrucDescOS`, Name/Description on contexts).
- Issue #326 comments in `lcm_casting.py` (`_ensure_interfaces`, `cast_phonological_rule`).

**Not present after T5 (no further action)**

- `SegmentRA`, `NaturalClassRA`, `LeftPartOfMetathesisOS`, `RightPartOfMetathesisOS`,
  `LeftPartOfReduplicationOS`, `RightPartOfReduplicationOS` in code paths.

## Pytest (offline)

```powershell
cd C:/Github/flexicon-326
python -m pytest -m "not requires_live_project" -q
```

**Result:** `2043 passed, 896 deselected, 5 failed`

Same five pre-existing failures as T5 (no new failures vs T5):

1. `tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies`
2. `tests/contract/test_lcm_contract.py::TestLiveRegressionCheck::test_no_regressions_from_baseline`
3. `tests/operations/test_issue266_phoneme_ws_resolution.py::TestApplyBasicIPASymbolSharedIndexCache::test_fresh_index_cache_per_apply_call`
4. `tests/operations/test_issue267_translations_ws_resolution.py::TestTranslationsOCSharedIndexCache::test_fresh_index_cache_per_apply_call`
5. `tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_no_new_unbracketed_mutations`

## Live LCM

Not run (T6 is simplify-only; no write-path or LCM semantic change).
