# T2 sweep: nonexistent LCM members named in #326

Scope: `flexicon/`, `tests/`, `examples/`, `docs/` under `C:/Github/flexicon-326`.
Date: 2026-09-22. Read-only audit.

## Summary

| Token | Invented (phonology wrappers) | Real (leave it) |
| --- | --- | --- |
| `SegmentRA` | `phonological_context.py` + context docs | `BeginSegmentRA` / `EndSegmentRA` on `IConstChartWordGroup` |
| `NaturalClassRA` | `phonological_context.py` only (no docs/tests) | none |
| `*PartOfMetathesisOS` | wrapper + docs | none (real `IPhMetathesisRule` uses `StrucDescOS` + switch/index ints) |
| `*PartOfReduplicationOS` | wrapper + docs | none |
| `PhReduplicationRule` / `IPhReduplicationRule` / `IPhReduplicationRuleFactory` | wrappers, casting, collections, tests, docs | none in LCM snapshot |
| `reduplication_rules` | **docs example only** (`ARCHITECTURE_COLLECTIONS.md:393`). Live API is `RuleCollection.redup_rules()` |

Wrapper reads of invented members are **silent**: `hasattr` + `try/except` return `None` / `[]` / `False`. The only **would-raise** library path is `PhonologicalRuleOperations.Duplicate` when `ClassName` has no factory (includes `PhReduplicationRule`). Copied doc examples that access invented members on live LCM objects would `AttributeError`.

Suspected real phoneme/NC link: `IPhSimpleContextSeg` / `IPhSimpleContextNC`.`FeatureStructureRA` (used in `PhonologicalRuleOperations.py`, not in the context wrapper).

---

## Classification table

Columns: **class** = `code-path (silent None/[ ])` | `code-path (would raise)` | `docstring/doc` | `test fixture/mock` | `real member (leave it)`.

### SegmentRA (non-ConstChart)

| File:line | Token | Class | Notes |
| --- | --- | --- | --- |
| `flexicon/code/System/phonological_context.py:330` | `SegmentRA` | code-path (silent None/[ ]) | `segment` property; `hasattr` then getattr; outer `except` -> `None`. Does not read `FeatureStructureRA`. |
| `flexicon/code/System/phonological_context.py:331` | `SegmentRA` | code-path (silent None/[ ]) | Same; only reached if `hasattr` is true. Still swallowed. |
| `flexicon/code/System/phonological_context.py:411` | `SegmentRA` | docstring/doc | Example inside `as_simple_context_seg`. Copied vs live `IPhSimpleContextSeg` would raise. |
| `flexicon/code/System/phonological_context.py:540` | `SegmentRA` | docstring/doc | Example inside `concrete`. Same. |
| `docs/USAGE_CONTEXTS.md:42` | `SegmentRA` | docstring/doc | "Before" example: `IPhSimpleContextSeg(context).SegmentRA`. Copied vs live LCM would raise. |
| `docs/USAGE_CONTEXTS.md:259` | `SegmentRA` | docstring/doc | Advanced: `concrete.SegmentRA` after `as_simple_context_seg()`. Copied vs live LCM would raise. |

### SegmentRA (ConstChartWordGroup — real)

| File:line | Token | Class | Notes |
| --- | --- | --- | --- |
| `flexicon/code/Discourse/ConstChartWordGroupOperations.py:142` | `BeginSegmentRA` | real member (leave it) | Create assign |
| `flexicon/code/Discourse/ConstChartWordGroupOperations.py:143` | `EndSegmentRA` | real member (leave it) | Create assign |
| `flexicon/code/Discourse/ConstChartWordGroupOperations.py:304` | `BeginSegmentRA` | real member (leave it) | Get |
| `flexicon/code/Discourse/ConstChartWordGroupOperations.py:343` | `BeginSegmentRA` | real member (leave it) | Set |
| `flexicon/code/Discourse/ConstChartWordGroupOperations.py:377` | `EndSegmentRA` | real member (leave it) | Get |
| `flexicon/code/Discourse/ConstChartWordGroupOperations.py:416` | `EndSegmentRA` | real member (leave it) | Set |
| `tests/operations/test_collection_cast_pattern.py:631` | `BeginSegmentRA` | real member (leave it) | Mock dict on `ConstChartWordGroup` |
| `tests/test_plans/discourse_operations_tests.md:518` | `BeginSegmentRA`,`EndSegmentRA` | real member (leave it) | Plan |
| `tests/test_plans/discourse_operations_tests.md:546` | `BeginSegmentRA` | real member (leave it) | |
| `tests/test_plans/discourse_operations_tests.md:573` | `BeginSegmentRA` | real member (leave it) | |
| `tests/test_plans/discourse_operations_tests.md:574` | `EndSegmentRA` | real member (leave it) | |
| `tests/test_plans/discourse_operations_tests.md:602` | `BeginSegmentRA` | real member (leave it) | |
| `tests/test_plans/discourse_operations_tests.md:648` | `BeginSegmentRA` | real member (leave it) | |
| `tests/contract/snapshots/liblcm_baseline.json:7927` | `BeginSegmentRA` | real member (leave it) | `IConstChartWordGroup` |
| `tests/contract/snapshots/liblcm_baseline.json:7936` | `EndSegmentRA` | real member (leave it) | |
| `tests/contract/snapshots/liblcm_baseline.json:7991` | `get_BeginSegmentRA` | real member (leave it) | |
| `tests/contract/snapshots/liblcm_baseline.json:8000` | `get_EndSegmentRA` | real member (leave it) | |
| `tests/contract/snapshots/liblcm_baseline.json:8024` | `set_BeginSegmentRA` | real member (leave it) | |
| `tests/contract/snapshots/liblcm_baseline.json:8027` | `set_EndSegmentRA` | real member (leave it) | |
| `tests/contract/snapshots/liblcm_baseline.json:8051` | `BeginSegmentRA` | real member (leave it) | type map |
| `tests/contract/snapshots/liblcm_baseline.json:8056` | `EndSegmentRA` | real member (leave it) | type map |

No `BeginSegmentRA`/`EndSegmentRA` hits in `docs/`.

### NaturalClassRA

| File:line | Token | Class | Notes |
| --- | --- | --- | --- |
| `flexicon/code/System/phonological_context.py:359` | `NaturalClassRA` | code-path (silent None/[ ]) | `natural_class`; `hasattr` + `except` -> `None`. Real link: `FeatureStructureRA`. |
| `flexicon/code/System/phonological_context.py:360` | `NaturalClassRA` | code-path (silent None/[ ]) | Same. |

No hits in `tests/`, `examples/`, or `docs/`.

### *PartOfMetathesisOS

| File:line | Token | Class | Notes |
| --- | --- | --- | --- |
| `flexicon/code/Grammar/phonological_rule.py:30` | `LeftPartOfMetathesisOS`, `RightPartOfMetathesisOS` | docstring/doc | Module docstring: invented members on `PhMetathesisRule`. |
| `flexicon/code/Grammar/phonological_rule.py:295` | `LeftPartOfMetathesisOS` | code-path (silent None/[ ]) | `has_metathesis_parts`; `hasattr` False on live `IPhMetathesisRule` => `False`. |
| `flexicon/code/Grammar/phonological_rule.py:296` | `RightPartOfMetathesisOS` | code-path (silent None/[ ]) | Same. |
| `flexicon/code/Grammar/phonological_rule.py:326` | `LeftPartOfMetathesisOS` | code-path (silent None/[ ]) | `metathesis_parts`; gated by `has_metathesis_parts` (always False live) + `hasattr` + `except` => `[]`. |
| `flexicon/code/Grammar/phonological_rule.py:329` | `RightPartOfMetathesisOS` | code-path (silent None/[ ]) | Same. |
| `flexicon/code/Grammar/phonological_rule.py:330` | `RightPartOfMetathesisOS` | code-path (silent None/[ ]) | `hasattr` check. |
| `flexicon/code/lcm_casting.py:1353` | `LeftPartOfMetathesisOS` | docstring/doc | Example claims `'LeftPartOfMetathesisOS' in unique_props` is True. |
| `docs/USAGE_PHONOLOGICAL_RULES.md:43` | `LeftPartOfMetathesisOS` | docstring/doc | "Before" example on cast concrete. Copied vs live would raise. |
| `docs/ARCHITECTURE_WRAPPERS.md:58` | `LeftPartOfMetathesisOS` | docstring/doc | Example print on concrete. |
| `docs/ARCHITECTURE_WRAPPERS.md:87` | `LeftPartOfMetathesisOS` | docstring/doc | Example print on wrapper. |
| `docs/ARCHITECTURE_WRAPPERS.md:278` | `LeftPartOfMetathesisOS` | docstring/doc | Pattern snippet `get_property(...)`. |
| `docs/ARCHITECTURE_WRAPPERS.md:310` | `LeftPartOfMetathesisOS` | docstring/doc | Comment in pattern. |
| `docs/ARCHITECTURE_WRAPPERS.md:311` | `RightPartOfMetathesisOS` | docstring/doc | |
| `docs/ARCHITECTURE_WRAPPERS.md:413` | `LeftPartOfMetathesisOS` | docstring/doc | "Good pattern" example. |
| `docs/ARCHITECTURE_COLLECTIONS.md:54` | `LeftPartOfMetathesisOS` | docstring/doc | "Before" type-check example. Copied vs live would raise. |

### *PartOfReduplicationOS

| File:line | Token | Class | Notes |
| --- | --- | --- | --- |
| `flexicon/code/Grammar/phonological_rule.py:31` | `LeftPartOfReduplicationOS`, `RightPartOfReduplicationOS` | docstring/doc | Invented type + members. |
| `flexicon/code/Grammar/phonological_rule.py:358` | `LeftPartOfReduplicationOS` | code-path (silent None/[ ]) | `has_redup_parts`; needs `class_type == "PhReduplicationRule"` (never on live) and `hasattr`. => `False`. |
| `flexicon/code/Grammar/phonological_rule.py:359` | `RightPartOfReduplicationOS` | code-path (silent None/[ ]) | Same. |
| `flexicon/code/Grammar/phonological_rule.py:389` | `LeftPartOfReduplicationOS` | code-path (silent None/[ ]) | `redup_parts`; gated; `[]`. |
| `flexicon/code/Grammar/phonological_rule.py:390` | `LeftPartOfReduplicationOS` | code-path (silent None/[ ]) | `hasattr`. |
| `flexicon/code/Grammar/phonological_rule.py:394` | `RightPartOfReduplicationOS` | code-path (silent None/[ ]) | |
| `flexicon/code/Grammar/phonological_rule.py:395` | `RightPartOfReduplicationOS` | code-path (silent None/[ ]) | |
| `docs/ARCHITECTURE_WRAPPERS.md:283` | `LeftPartOfReduplicationOS` | docstring/doc | Pattern `get_property`. |
| `docs/ARCHITECTURE_WRAPPERS.md:314` | `LeftPartOfReduplicationOS` | docstring/doc | |
| `docs/ARCHITECTURE_WRAPPERS.md:315` | `RightPartOfReduplicationOS` | docstring/doc | |
| `docs/ARCHITECTURE_WRAPPERS.md:416` | `LeftPartOfReduplicationOS` | docstring/doc | "Good pattern". |

### PhReduplicationRule / IPhReduplicationRule / factory / reduplication_rules

#### flexicon/ code

| File:line | Token | Class | Notes |
| --- | --- | --- | --- |
| `flexicon/code/lcm_casting.py:63` | `PhReduplicationRule` | docstring/doc | Module "Supported Types" list. |
| `flexicon/code/lcm_casting.py:127` | `IPhReduplicationRule`, `PhReduplicationRule` | docstring/doc | Comment: **no such LCM type**; slot kept for back-compat. |
| `flexicon/code/lcm_casting.py:141` | `IPhReduplicationRule` | code-path (silent None/[ ]) | Hardcoded `= None` (never imported). |
| `flexicon/code/lcm_casting.py:282` | `IPhReduplicationRule` | docstring/doc | Comment citing this as precedent for absent types. |
| `flexicon/code/lcm_casting.py:327` | `IPhReduplicationRule` | code-path (silent None/[ ]) | `if ... is not None` never true. |
| `flexicon/code/lcm_casting.py:328` | `PhReduplicationRule` | code-path (silent None/[ ]) | Cache key never registered. `cast_to_concrete` falls through. |
| `flexicon/code/lcm_casting.py:1064` | `PhReduplicationRule` | docstring/doc | Comment: factory map omits reduplication; callers get `None`. |
| `flexicon/code/lcm_casting.py:1095` | `PhReduplicationRule`, `IPhReduplicationRule` | docstring/doc | `cast_phonological_rule` docstring still lists invented mapping. |
| `flexicon/code/Shared/smart_collection.py:52` | `PhReduplicationRule` | docstring/doc | Example `__str__` output. |
| `flexicon/code/Shared/smart_collection.py:163` | `PhReduplicationRule` | docstring/doc | `__str__` docstring example. |
| `flexicon/code/Grammar/rule_collection.py:22` | `PhReduplicationRule` | docstring/doc | Module lists three concrete types. |
| `flexicon/code/Grammar/rule_collection.py:37` | `redup_rules()` | docstring/doc | Real method name (not `reduplication_rules`). |
| `flexicon/code/Grammar/rule_collection.py:50` | `PhReduplicationRule` | docstring/doc | Example type breakdown. |
| `flexicon/code/Grammar/rule_collection.py:262` | `redup_rules` | code-path (silent None/[ ]) | Method exists. Live `GetAll()` never yields this ClassName => empty collection. |
| `flexicon/code/Grammar/rule_collection.py:264` | `PhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/rule_collection.py:266` | `PhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/rule_collection.py:269` | `PhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/rule_collection.py:273` | `redup_rules` | docstring/doc | Example. |
| `flexicon/code/Grammar/rule_collection.py:277` | `redup_rules` | docstring/doc | |
| `flexicon/code/Grammar/rule_collection.py:280` | `PhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/rule_collection.py:284` | `PhReduplicationRule` | code-path (silent None/[ ]) | `return self.by_type("PhReduplicationRule")` => `[]` on live data. |
| `flexicon/code/Grammar/phonological_rule.py:21` | `PhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/phonological_rule.py:83` | `PhReduplicationRule` | docstring/doc | Class docstring. |
| `flexicon/code/Grammar/phonological_rule.py:89` | `IPhReduplicationRule` | docstring/doc | `_concrete` type list. |
| `flexicon/code/Grammar/phonological_rule.py:236` | `PhReduplicationRule` | docstring/doc | `has_output_specs` notes. |
| `flexicon/code/Grammar/phonological_rule.py:343` | `PhReduplicationRule` | docstring/doc | `has_redup_parts` returns. |
| `flexicon/code/Grammar/phonological_rule.py:352` | `PhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/phonological_rule.py:357` | `PhReduplicationRule` | code-path (silent None/[ ]) | `class_type ==` never true on live. |
| `flexicon/code/Grammar/phonological_rule.py:381` | `PhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/phonological_rule.py:460` | `as_reduplication_rule` | code-path (silent None/[ ]) | Returns `_concrete` only if ClassName matches; else `None`. |
| `flexicon/code/Grammar/phonological_rule.py:462` | `IPhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/phonological_rule.py:465` | `PhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/phonological_rule.py:468` | `IPhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/phonological_rule.py:469` | `PhReduplicationRule` | docstring/doc | |
| `flexicon/code/Grammar/phonological_rule.py:475` | `IPhReduplicationRule` | docstring/doc | Example. |
| `flexicon/code/Grammar/phonological_rule.py:482` | `PhReduplicationRule` | code-path (silent None/[ ]) | Guard for `as_reduplication_rule`. |
| `flexicon/code/Grammar/phonological_rule.py:496` | `IPhReduplicationRule` | docstring/doc | `concrete` property. |
| `flexicon/code/Grammar/PhonologicalRuleOperations.py:119` | `PhReduplicationRule` | docstring/doc | `GetAll` example breakdown. |
| `flexicon/code/Grammar/PhonologicalRuleOperations.py:1361` | `PhReduplicationRule` | docstring/doc | Duplicate comment lists invented third subtype. |
| `flexicon/code/Grammar/PhonologicalRuleOperations.py:1367` | `IPhReduplicationRuleFactory` | docstring/doc | Comment: avoid importing factory at module load. |
| `flexicon/code/Grammar/PhonologicalRuleOperations.py:1384` | `PhReduplicationRule` | code-path (would raise) | `Duplicate`: `_get_factory_for_class` is `None` for this ClassName => `FP_ParameterError`. Same raise for any unknown class; message still names the invented type as "known". |

#### tests/

| File:line | Token | Class | Notes |
| --- | --- | --- | --- |
| `tests/test_wrappers.py:257` | `PhReduplicationRule` | test fixture/mock | `ClassName` on Mock; only tests `class_type` passthrough. |
| `tests/test_wrappers.py:260` | `PhReduplicationRule` | test fixture/mock | Assert. |
| `tests/test_phonological_rules_wrappers.py:11` | `redup_rules()` | docstring/doc | Module test list. |
| `tests/test_phonological_rules_wrappers.py:73` | `PhReduplicationRule` | test fixture/mock | `MockPhonologicalRule.has_redup_parts`. |
| `tests/test_phonological_rules_wrappers.py:77` | `PhReduplicationRule` | test fixture/mock | `redup_parts`. |
| `tests/test_phonological_rules_wrappers.py:88` | `PhReduplicationRule` | test fixture/mock | `as_reduplication_rule`. |
| `tests/test_phonological_rules_wrappers.py:247` | `redup_rules` | test fixture/mock | Test method. |
| `tests/test_phonological_rules_wrappers.py:248` | `redup_rules` | test fixture/mock | |
| `tests/test_phonological_rules_wrappers.py:253` | `PhReduplicationRule` | test fixture/mock | |
| `tests/test_phonological_rules_wrappers.py:254` | `PhReduplicationRule` | test fixture/mock | |
| `tests/test_phonological_rules_wrappers.py:258` | `redup_rules` | test fixture/mock | Filters mocks; does not prove LCM type. |
| `tests/test_phonological_rules_wrappers.py:261` | `PhReduplicationRule` | test fixture/mock | |
| `tests/test_collections.py:83` | `PhReduplicationRule` | test fixture/mock | Fixture docstring. |
| `tests/test_collections.py:88` | `PhReduplicationRule` | test fixture/mock | `class_type`. |
| `tests/test_collections.py:89` | `PhReduplicationRule` | test fixture/mock | `ClassName`. |
| `tests/test_collections.py:364` | `PhReduplicationRule` | test fixture/mock | `__str__` on mixed mock collection. |
| `tests/test_collections.py:461` | `PhReduplicationRule` | test fixture/mock | `by_type`. |
| `tests/test_collections.py:679` | `PhReduplicationRule` | test fixture/mock | |
| `tests/test_collections.py:681` | `PhReduplicationRule` | test fixture/mock | |

`tests/contract/snapshots/liblcm_baseline.json`: **no** `PhReduplicationRule` / `IPhReduplicationRule`.

#### examples/

| File:line | Token | Class | Notes |
| --- | --- | --- | --- |
| `examples/README.md:131` | `PhReduplicationRule` | docstring/doc | Sample `print(rules)` output. |

#### docs/ (known sites + rest of docs/)

| File:line | Token | Class | Notes |
| --- | --- | --- | --- |
| `docs/ARCHITECTURE_WRAPPERS.md:151` | `PhReduplicationRule` | docstring/doc | |
| `docs/ARCHITECTURE_WRAPPERS.md:241` | `PhReduplicationRule` | docstring/doc | Pattern `REDUPLICATION = ...` |
| `docs/ARCHITECTURE_COLLECTIONS.md:23` | `PhReduplicationRule` | docstring/doc | |
| `docs/ARCHITECTURE_COLLECTIONS.md:81` | `PhReduplicationRule` | docstring/doc | |
| `docs/ARCHITECTURE_COLLECTIONS.md:212` | `PhReduplicationRule` | docstring/doc | |
| `docs/ARCHITECTURE_COLLECTIONS.md:274` | `PhReduplicationRule` | docstring/doc | |
| `docs/ARCHITECTURE_COLLECTIONS.md:349` | `PhReduplicationRule` | docstring/doc | |
| `docs/ARCHITECTURE_COLLECTIONS.md:393` | `reduplication_rules` | docstring/doc | **Only** identifier hit for this token. Pattern method; **not** implemented on `RuleCollection` (live name: `redup_rules`). |
| `docs/ARCHITECTURE_COLLECTIONS.md:398` | `PhReduplicationRule` | docstring/doc | |
| `docs/ARCHITECTURE_COLLECTIONS.md:400` | `PhReduplicationRule` | docstring/doc | `by_type(...)` in pattern. |
| `docs/ARCHITECTURE_COLLECTIONS.md:512` | `PhReduplicationRule` | docstring/doc | |
| `docs/USAGE_PHONOLOGICAL_RULES.md:10` | `PhReduplicationRule` | docstring/doc | Overview: third concrete type. |
| `docs/USAGE_PHONOLOGICAL_RULES.md:69` | `PhReduplicationRule` | docstring/doc | Sample breakdown. |
| `docs/USAGE_PHONOLOGICAL_RULES.md:194` | `IPhReduplicationRule` | docstring/doc | `as_reduplication_rule` example. |
| `docs/USAGE_PHONOLOGICAL_RULES.md:274` | `PhReduplicationRule` | docstring/doc | `class_type` values. |
| `docs/USAGE_PHONOLOGICAL_RULES.md:282` | `PhReduplicationRule` | docstring/doc | `has_redup_parts` branch. |
| `docs/API_SURFACE.md:179` | `IPhReduplicationRuleFactory` | docstring/doc | Factory inventory; not in LCM. |
| `docs/API_SURFACE.md:283` | `IPhReduplicationRule` | docstring/doc | Interface table, usage count 1. |
| `docs/API_DESIGN_PHILOSOPHY.md:193` | `PhReduplicationRule` | docstring/doc | Example `__str__`. |
| `docs/FUNCTION_REFERENCE.md:1254` | `IPhReduplicationRule` | docstring/doc | Duplicate/clone description. |
| `docs/getall-contract.md:23` | `PhReduplicationRule` | docstring/doc | Mixed-type GetAll example. |
| `docs/internal/MERGE_OPERATIONS_AUDIT.md:291` | `PhReduplicationRule` | docstring/doc | Sample `survivor_class` list. |
| `docs/audit/LCM_CAPABILITIES_AUDIT_REFERENCES.md:390` | `IPhReduplicationRule` | docstring/doc | |
| `docs/audit/LCM_CAPABILITIES_AUDIT_REFERENCES.md:503` | `PhReduplicationRule` | docstring/doc | |
| `docs/audit/LCM_CAPABILITIES_AUDIT.md:148` | `IPhReduplicationRuleFactory` | docstring/doc | |
| `docs/audit/LCM_AUDIT_QUICK_REFERENCE.txt:77` | `IPhReduplicationRuleFactory` | docstring/doc | |
| `docs/audit/LCM_AUDIT_SUMMARY.md:81` | `IPhReduplicationRuleFactory` | docstring/doc | Long factory sample list. |

`docs/USAGE_CONTEXTS.md`: no `PhReduplicationRule` / `NaturalClassRA` / `*PartOf*` (only invented `SegmentRA` as above).

---

## Known sites vs this sweep

| Site | Confirmed | Dominant class |
| --- | --- | --- |
| `phonological_context.py:330,359` | yes | silent None |
| `phonological_context.py:411,540` | yes | docstring (copied example would raise) |
| `phonological_rule.py:21-31` | yes | docstring |
| `phonological_rule.py:83-89,236` | yes | docstring |
| `phonological_rule.py:295-395` | yes | silent False/`[]` |
| `phonological_rule.py:462-496` | yes | docstring + silent None on `as_reduplication_rule` |
| `lcm_casting.py:63,127-141,282,327,1064,1095,1353` | yes | mix: comments/docs; `141`/`327-328` silent None; `1353` invented member in docstring |
| `rule_collection.py:22,50,264-284` | yes | docs + `redup_rules()` silent `[]` |
| `smart_collection.py:52,163` | yes | docstring |
| `PhonologicalRuleOperations.py:119` | yes | docstring |
| `PhonologicalRuleOperations.py:1361-1384` | yes | comment + **would raise** on Duplicate for this ClassName |
| tests listed | yes | test fixture/mock |
| docs listed | yes | docstring/doc |
| `reduplication_rules` | **one hit**: `docs/ARCHITECTURE_COLLECTIONS.md:393` | docstring; not a code identifier |

## Out of search roots (not tabulated)

Specs/history/reports also mention these tokens (`specs/lcm-member-truth-sweep/*`, `CHANGELOG.md`, `history.md`, `reports/audit/api_usage_*.json`). Not in `flexicon/`/`tests/`/`examples/`/`docs/`.
