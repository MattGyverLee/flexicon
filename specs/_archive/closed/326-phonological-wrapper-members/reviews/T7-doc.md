# T7 Documentation Review — Issue #326: Phonological Wrapper Members

Docs-only updates synced with T5 programmer changes; live LCM behavior verified in T5 evidence.

## Files Changed

- `docs/ARCHITECTURE_WRAPPERS.md` — Updated metathesis examples (StrucDescOS + switch indices); removed reduplication examples and properties
- `docs/ARCHITECTURE_COLLECTIONS.md` — Removed `reduplication_rules()` method; updated type counts from 12 to 10 rules (2 concrete types only)
- `docs/USAGE_PHONOLOGICAL_RULES.md` — Updated overview (2 rule types, not 3); removed redup filtering and property examples
- `docs/USAGE_CONTEXTS.md` — Changed `SegmentRA` → `FeatureStructureRA` (IPhPhoneme); `NaturalClassRA` → `FeatureStructureRA` (IPhNaturalClass)
- `docs/API_ISSUES_CATEGORIZED.md` — Added Category 8 rows for segment/natural_class link correction and metathesis part model repair
- `examples/README.md` — Updated print example: 12→10 rules, 3→2 concrete types
- `CHANGELOG.md` — Added [Unreleased] BREAKING (behavioural) entries for metathesis/context fixes and deprecated-v5.0.0 for redup symbols

## Corrections Applied

| Issue | Doc Site | Was | Now | Reason |
|-------|----------|-----|-----|--------|
| Metathesis parts | ARCH_WRAPPERS, USAGE_RULES | `LeftPartOfMetathesisOS` | `StrucDescOS` + index slicing | Real LCM field |
| Context links | USAGE_CONTEXTS | `SegmentRA` | `FeatureStructureRA` (IPhPhoneme) | Real LCM field |
| Context links | USAGE_CONTEXTS | `NaturalClassRA` | `FeatureStructureRA` (IPhNaturalClass) | Real LCM field |
| Redup surface | ARCH_COLLECTIONS, USAGE_RULES | `reduplication_rules()` method + examples | removed | Nonexistent LCM type |
| Type counts | All collections sections | 12 total, 3 types | 10 total, 2 types | PhReduplicationRule unobserved |
| Deprecation | CHANGELOG | n/a | 4 redup symbols deprecated v5.0.0 | T4 ruling: remove at v5.0.0 |
