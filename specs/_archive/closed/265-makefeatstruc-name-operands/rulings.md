# Issue #265 -- lex-lead ruling

**Date:** 2026-09-24  
**Branch:** fix/265-makefeatstruc-names from origin/main

## RULING (binding)

`MakeFeatStruc` / `BaseOperations._MakeFeatStruc` **accept plain feature and
value name strings** as operands wherever C3 already accepts objects, HVOs, or
GUID strings. This is additive; existing callers are unchanged.

### Policy (the four undecided choices from #265)

1. **Which lookup** -- reuse the same name-matching convention as
   `InflectionFeatureOperations.Find` (morphological / MS owners) and
   `PhonFeatureOperations.Find` (phoneme / natural-class owners): scan
   `FeaturesOC` in the appropriate feature system, NFD-normalized casefold
   match on analysis writing system `Name`.
2. **Scope** -- **owner-driven, never project-wide.** Derive domain from
   `owner.ClassName`: `PhPhoneme` and `PhNCFeatures` -> phonological feature
   system; every other C1 row -> morphological (`MsFeatureSystemOA`). Do not
   search both systems for one operand.
3. **Ambiguity** -- if more than one feature (or value on a given feature)
   matches the normalized name, raise `FP_ParameterError` naming the ambiguity.
   Never return the first of several matches silently.
4. **Case / writing system** -- analysis WS only (`DefaultAnalWs`), via
   `normalize_match_key(..., casefold=True)` (same as `Find`).

### Operand routing

- **`str` that parses as a well-formed GUID** (Python `uuid.UUID`) -> existing
  `project.Object(guid)` path (unchanged).
- **Any other non-empty `str`** -> name resolution in the owner domain:
  - Feature position (dict keys, tuple first elements, nested keys): resolve as
    a feature name.
  - Scalar value position (closed value): resolve as a value name on the
    **already-resolved** feature for that pair.
- **Nested dict values** recurse with the same domain; keys at each level are
  feature names.

### Out of scope

- Sync wire format (C4) stays GUID-only.
- Resolving value names without a enclosing feature (impossible for closed
  values).
- Cross-system or abbreviation-only matching.

## Verification plan

- Offline: mock/resolver unit tests for GUID vs name routing and ambiguity raises.
- Live: extend `tests/operations/test_makefeatstruc_c3_live.py` or add a
  targeted live test with `TEST_`-prefixed features on `target_sandbox` when
  FieldWorks is available.
