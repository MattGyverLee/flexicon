# Programmer report - issue #220 (test-only)

Created `tests/operations/test_yield_cast_pattern.py` (model: `test_owner_cast_pattern.py`).
Tests-only; no production code touched (per 92762fa, already merged).

## Static tests (no LCM required)
- `TestYieldCastStatic::test_casts_before_yield` (parametrized, 3 sites): source-inspects
  `InflectionClassGetAll`, `SemanticDomainOperations.GetSubdomains`,
  `LocationOperations.GetSublocations`, asserting `IMoInflClass(ic)` / `ICmSemanticDomain(` /
  `ICmLocation(` appear the expected number of times (fast path + recursive walk).
- `test_inflection_class_no_bare_yield`, `test_semantic_domain_no_bare_collection_pass_through`,
  `test_location_no_bare_collection_pass_through`: forbid the pre-fix bare
  `yield ic` / `return list(...SubPossibilitiesOS)` / `for child in collection:` shapes.
- `TestProjectSettingsAccessorsStatic` (5 tests): confirm `GetProjectGuid`,
  `GetProjectDescription`, `GetExternalLink`, `GetAnalysisWritingSystem`,
  `GetVernacularWritingSystem` exist and delegate to the expected LCM source.

## Live tests (writable_project fixture, `@pytest.mark.requires_live_project`)
- `TestYieldCastLive` (3 tests): pattern-level guard — asserts `type(item) is not
  ICmPossibility` and `type(item) is <ConcreteType>` for every item from the three
  enumerators, plus concrete-only member access without re-cast (`OcmCodes` on
  ICmSemanticDomain, `Elevation` on ICmLocation).
- `TestProjectSettingsAccessorsLive` (5 tests): smoke-check new accessors return
  sane values / match their delegate methods. All read-only, no `-restore` concern.

## Registry discovery
No generic "possibility-list enumerator" registry exists in `_op_aliases.py` /
`FLExProject.py` (those only alias operation-namespace accessors, e.g.
`project.SemanticDomains`). Followed `test_owner_cast_pattern.py`'s convention: a
curated `_SITES` table built by grepping all `PossibilitiesOS`/`SubPossibilitiesOS`
loops repo-wide, scoped to the three methods 92762fa actually fixed.

## Result
`python -m pytest tests/operations/test_yield_cast_pattern.py -q` — **17 passed, 2
skipped**. This environment unexpectedly has a live FieldWorks project available
(via `tests/conftest.py`'s LCM bootstrap), so most live tests ran for real rather
than skipping; 2 skipped only for lack of fixture data (no inflection classes / no
location with sublocations in the sample project).
