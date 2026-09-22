# T5 Programmer Review — Issue #326: Phonological Wrapper Members

Cycle 2 rulings applied by lex-programmer in worktree `C:/Github/flexicon-326`,
branch `fix/326-phonological-wrapper-members`.

## Pattern Audit

| file:line | token | class | disposition | reason |
|---|---|---|---|---|
| `flexicon/code/System/phonological_context.py:338-340` | `SegmentRA` | code-path | fixed | `segment` now reads `FeatureStructureRA` and casts to `IPhPhoneme` |
| `flexicon/code/System/phonological_context.py:375-377` | `NaturalClassRA` | code-path | fixed | `natural_class` now reads `FeatureStructureRA` and casts to `IPhNaturalClass` |
| `flexicon/code/System/phonological_context.py:430-432` | `SegmentRA` | docstring | fixed | `as_simple_context_seg` example now shows `FeatureStructureRA` + `IPhPhoneme` |
| `flexicon/code/System/phonological_context.py:563-565` | `SegmentRA` | docstring | fixed | `concrete` property example now shows `FeatureStructureRA` + `IPhPhoneme` |
| `flexicon/code/Discourse/ConstChartWordGroupOperations.py:142-143,304,343,377,416` | `BeginSegmentRA`/`EndSegmentRA` | real member | left-as-real | T3/T5 ruling: ConstChart Begin/End segment links are real |
| `tests/operations/test_collection_cast_pattern.py:631` | `BeginSegmentRA` | real member | left-as-real | real LCM member on `IConstChartWordGroup` |
| `tests/test_plans/discourse_operations_tests.md:518,546,573-574,602,648` | `BeginSegmentRA`/`EndSegmentRA` | real member | left-as-real | real LCM member |
| `tests/contract/snapshots/liblcm_baseline.json:7927,7936,7991,8000,8024,8027,8051,8056` | `BeginSegmentRA`/`EndSegmentRA` | real member | left-as-real | contract baseline, real |
| `flexicon/code/System/phonological_context.py:338-340` | `NaturalClassRA` | code-path | fixed | same as `SegmentRA` above; `natural_class` now uses `FeatureStructureRA` |
| `flexicon/code/Grammar/phonological_rule.py:28-30` | `LeftPartOfMetathesisOS`, `RightPartOfMetathesisOS` | docstring | fixed | module docstring now describes `StrucDescOS` + switch indices |
| `flexicon/code/Grammar/phonological_rule.py:295-330` (old) | `LeftPartOfMetathesisOS`, `RightPartOfMetathesisOS` | code-path | fixed | reimplemented `has_metathesis_parts`/`metathesis_parts` against `StrucDescOS` + switch indices |
| `flexicon/code/lcm_casting.py:1353` (old) | `LeftPartOfMetathesisOS` | docstring | fixed | `get_concrete_type_properties` example now uses `StrucDescOS` |
| `docs/USAGE_PHONOLOGICAL_RULES.md:43` | `LeftPartOfMetathesisOS` | doc | doc-deferred-to-T7 | docs/ owned by T7 |
| `docs/ARCHITECTURE_WRAPPERS.md:58,87,278,310-311,413` | `LeftPartOfMetathesisOS`, `RightPartOfMetathesisOS` | doc | doc-deferred-to-T7 | docs/ owned by T7 |
| `docs/ARCHITECTURE_COLLECTIONS.md:54` | `LeftPartOfMetathesisOS` | doc | doc-deferred-to-T7 | docs/ owned by T7 |
| `flexicon/code/Grammar/phonological_rule.py:31,83-89,236,343-357,381-395,460-482` (old) | `LeftPartOfReduplicationOS`, `RightPartOfReduplicationOS`, `PhReduplicationRule`, `IPhReduplicationRule` | code-path + docstring | deprecated / removed | public symbols deprecated with `DeprecationWarning` naming v5.0.0 and return empty values; internal code paths no longer touch nonexistent LCM members |
| `docs/ARCHITECTURE_WRAPPERS.md:283,314-315,416` | `LeftPartOfReduplicationOS`, `RightPartOfReduplicationOS` | doc | doc-deferred-to-T7 | docs/ owned by T7 |
| `flexicon/code/lcm_casting.py:63` | `PhReduplicationRule` | docstring | fixed | Supported Types list corrected to `PhRegularRule, PhMetathesisRule` |
| `flexicon/code/lcm_casting.py:127-128` | `IPhReduplicationRule`, `PhReduplicationRule` | comment | fixed | comment now states no such type exists |
| `flexicon/code/lcm_casting.py:141` (old) | `IPhReduplicationRule` | code-path | removed | hardcoded `= None` slot removed |
| `flexicon/code/lcm_casting.py:282` (old) | `IPhReduplicationRule` | comment | fixed | stale precedent reference removed |
| `flexicon/code/lcm_casting.py:327-328` (old) | `IPhReduplicationRule`, `PhReduplicationRule` | code-path | removed | `_interface_cache["PhReduplicationRule"]` registration removed |
| `flexicon/code/lcm_casting.py:1058-1059` | `PhReduplicationRule` | comment | fixed | `_get_factory_for_class` comment lists only real types |
| `flexicon/code/lcm_casting.py:1089-1091` | `PhReduplicationRule`, `IPhReduplicationRule` | docstring | fixed | `cast_phonological_rule` docstring corrected |
| `flexicon/code/Shared/smart_collection.py:52,163` | `PhReduplicationRule` | docstring | doc-deferred-to-T7 | docs/ owned by T7 |
| `flexicon/code/Grammar/rule_collection.py:22-284` (old sites) | `PhReduplicationRule`, `redup_rules` | code-path + docstring | deprecated / fixed | `redup_rules()` deprecated with v5.0.0 warning; docstrings no longer claim a third concrete type |
| `flexicon/code/Grammar/phonological_rule.py:21-496` (old sites) | `PhReduplicationRule`, `IPhReduplicationRule`, `has_redup_parts`, `redup_parts`, `as_reduplication_rule` | code-path + docstring | deprecated / fixed | public redup surface deprecated-then-remove; class/module docstrings corrected |
| `flexicon/code/Grammar/PhonologicalRuleOperations.py:119` | `PhReduplicationRule` | docstring | fixed | `GetAll` example type breakdown corrected |
| `flexicon/code/Grammar/PhonologicalRuleOperations.py:1360-1375` | `PhReduplicationRule`, `IPhReduplicationRuleFactory` | comment | fixed | Duplicate comment now mentions only `PhRegularRule`/`PhMetathesisRule` |
| `flexicon/code/Grammar/PhonologicalRuleOperations.py:1378` | `PhReduplicationRule` | message | fixed | Duplicate error message now lists `PhRegularRule, PhMetathesisRule` only |
| `tests/test_wrappers.py:257,260` (old) | `PhReduplicationRule` | test fixture/mock | fixed | `test_class_type_with_different_types` now uses `MoStemMsa` instead of invented type |
| `tests/test_phonological_rules_wrappers.py:11,73,77,88,247,248,253,254,258,261` (old) | `PhReduplicationRule`, `redup_rules()` | test fixture/mock | fixed | mock class and tests updated; redup filter test replaced by deprecation test; added `PhonologicalRule` deprecation and metathesis-parts tests |
| `tests/test_collections.py:83,88,89,364,461,679,681` (old) | `PhReduplicationRule` | test fixture/mock | fixed | `mock_wrapped_rule_reduplication` removed; mixed fixture reduced to 10 items; by-type test asserts empty collection for `PhReduplicationRule` |
| `examples/README.md:131` | `PhReduplicationRule` | doc example | left-for-cleanup | outside edited-module docstrings; not covered by this task's scope |
| `docs/...` (all `PhReduplicationRule`/`IPhReduplicationRule`/`reduplication_rules` sites) | — | doc | doc-deferred-to-T7 | docs/ owned by T7 except docstrings in edited modules |

Notes:
- Old line numbers refer to the pre-edit state captured in `T2-sweep.md`. Edited files were re-grepped after changes to confirm the invented members no longer appear in code paths.
- `reduplication_rules` (the misspelled collection method name in `docs/ARCHITECTURE_COLLECTIONS.md:393`) is doc-deferred to T7; the live collection method remains `redup_rules()`.

## Files Changed

- `flexicon/code/System/phonological_context.py`
  - `segment` reads `FeatureStructureRA` and casts to `IPhPhoneme`
  - `natural_class` reads `FeatureStructureRA` and casts to `IPhNaturalClass`
  - docstring examples at `as_simple_context_seg` and `concrete` updated
- `flexicon/code/Grammar/phonological_rule.py`
  - module + class docstrings corrected to two concrete rule types
  - `has_metathesis_parts`/`metathesis_parts` reimplemented against `StrucDescOS` + switch indices; returns `ContextCollection` pairs
  - `has_redup_parts`, `redup_parts`, `as_reduplication_rule` deprecated with `DeprecationWarning` naming v5.0.0
- `flexicon/code/Grammar/rule_collection.py`
  - `redup_rules()` deprecated with v5.0.0 warning; returns empty collection
  - docstrings no longer advertise `PhReduplicationRule`
- `flexicon/code/lcm_casting.py`
  - removed `IPhReduplicationRule = None` slot and `_interface_cache["PhReduplicationRule"]` registration
  - corrected module, comment, and `cast_phonological_rule` docstrings
- `flexicon/code/Grammar/PhonologicalRuleOperations.py`
  - `Duplicate` error message now lists only `PhRegularRule, PhMetathesisRule`
  - surrounding comment updated
- `tests/test_phonological_rules_wrappers.py`
  - removed `PhReduplicationRule` from mock class
  - added deprecation tests for `PhonologicalRule.has_redup_parts`, `redup_parts`, `as_reduplication_rule`, and `RuleCollection.redup_rules()`
  - added offline `metathesis_parts` slice tests and `PhonologicalContext.segment`/`natural_class` tests
- `tests/test_collections.py`
  - removed `mock_wrapped_rule_reduplication` fixture
  - adjusted counts and assertions to 7 regular + 3 metathesis rules
  - `by_type("PhReduplicationRule")` now asserts empty collection
- `tests/test_wrappers.py`
  - `test_class_type_with_different_types` uses `MoStemMsa` instead of `PhReduplicationRule`
- `tests/operations/test_phonological_wrappers_live.py`
  - new live read-back test modeled on `test_target_live_smoke.py`
  - verifies `PhSimpleContextSeg.segment`, `PhSimpleContextNC.natural_class`, and `PhonologicalRule.metathesis_parts` against real FLEx projects
- `tests/operations/test_issue326_phonological_reflection_live.py`
  - **deleted** (temporary T1 reflection file)

## Tests

Offline:
```powershell
cd C:/Github/flexicon-326
python -m pytest -m "not requires_live_project" -q
```
Result: `2043 passed, 896 deselected, 5 failed`

The 5 failures are pre-existing and unrelated to #326:
- `tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies` — `ICmDomainQ`, `ICmDomainQFactory` new LCM types not in baseline
- `tests/contract/test_lcm_contract.py::TestLiveRegressionCheck::test_no_regressions_from_baseline` — `IRnResearchNbkRepository` missing vs baseline
- `tests/operations/test_issue266_phoneme_ws_resolution.py::TestApplyBasicIPASymbolSharedIndexCache::test_fresh_index_cache_per_apply_call`
- `tests/operations/test_issue267_translations_ws_resolution.py::TestTranslationsOCSharedIndexCache::test_fresh_index_cache_per_apply_call`
- `tests/write_path_transactions/test_unbracketed_mutations.py::TestUnbracketedMutationRatchet::test_no_new_unbracketed_mutations`

Live:
```powershell
cd C:/Github/flexicon-326
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_phonological_wrappers_live.py -m requires_live_project -q
```
Result: `3 passed in 24.14s`

`tests/live_status.json` shows:
```json
"run_mode": "live"
```
with `PhonologicalRuleOperations.read` and `FLExProject.read` statuses `pass`.

Live evidence written:
- `specs/326-phonological-wrapper-members/evidence/live-programmer-context-links.json`
- `specs/326-phonological-wrapper-members/evidence/live-programmer-metathesis.json`

Context-links evidence: `seg_class_name: "PhPhoneme"`, `nc_class_name: "PhNCSegments"`.
Metathesis-parts evidence: `left_switch: [0,1]`, `right_switch: [1,2]`, `left_count: 1`, `right_count: 1`.

## Open Questions

- **T6 (QC):** The offline suite still carries 5 pre-existing failures (see above). Confirm none of them are newly introduced by this change. Also confirm the `pytest.warns` regexes for v5.0.0 are strict enough.
- **T7 (docs):** `docs/` still contains `PhReduplicationRule`, `LeftPartOfMetathesisOS`, `RightPartOfMetathesisOS`, `LeftPartOfReduplicationOS`, `RightPartOfReduplicationOS`, `IPhReduplicationRule`, `IPhReduplicationRuleFactory`, and `reduplication_rules` references per `T2-sweep.md`. These need a docs-only cleanup pass.
- **T7 (docs):** `examples/README.md:131` still shows a `PhReduplicationRule` type-breakdown example. Decide whether to update or leave.
- **T8 (verification):** Sena 3 `.fwbackup` fixture is missing from this worktree; live verification used the Target sandbox to prove the LCM session and then scanned installed FLEx projects read-only. Confirm this satisfies the live-read gate, or request the Sena 3 fixture be restored/copied for a follow-up read-only pass.
