# Cycle 1 programmer report: issue 631

## Changes (flexicon/code/Grammar/InflectionFeatureOperations.py)
- Header/class docstring updated; `import logging` + `logger` added (top of file); imports of ICmPossibility, ICmPossibilityFactory, ICmPossibilityListFactory, normalize_text.
- `InflectionClassGetAll()` (~l.153): iterates `self.project.POS.GetAll(recursive=True)` and `POS.GetInflectionClasses(pos, recursive=True)`; no ProdRestrictOA.
- `InflectionClassCreate(self, name, pos=None, parent=None)` (~l.190): name-only raises FP_ParameterError ("part of speech"); parent -> `parent.SubclassesOC.Add`, pos -> `pos.InflectionClassesOC.Add`; IMoInflClassFactory; name in DefaultAnalWs; sibling-scoped duplicate check; writeEnabled checked. Reuses existing `__ResolvePOS`.
- `InflectionClassDelete` (~l.285): removes from `ic.Owner`'s `SubclassesOC` (owner ClassName MoInflClass) or `InflectionClassesOC`.
- New, before the PRIVATE HELPER section (~l.1940):
  - `ExceptionFeatureGetAll()` (generator, ICmPossibility; empty if list None)
  - `ExceptionFeatureFind(name, wsHandle=None)` -> item or None (case-insensitive)
  - `ExceptionFeatureCreate(name, abbreviation=None)` (creates ProdRestrictOA via ICmPossibilityListFactory if None; abbreviation defaults to name; duplicate -> FP_ParameterError)
- No FLExProject passthroughs: siblings are reached through `project.InflectionFeatures`, which already exposes the new methods.
- docs/API_ISSUES_CATEGORIZED.md: new "Issue #631" entry (before Conclusion).

Breaking: `InflectionClassCreate(name)` alone now raises.

## Tests
- Offline: tests/operations/test_issue631_inflection_class_store.py (12 tests). Full `python -m pytest -m "not requires_live_project" -q`: 3691 passed.
- Live: tests/operations/test_issue631_inflection_class_store_live.py (4 tests, sena3_sandbox): 4 passed, live_status.json run_mode "live".
- Finding: the Sena 3 fixture has 0 inflection classes anywhere (so no "7 on Nome"). The live test seeds its own under Nome; the GetAll-with-exception-features check still exercises the old crash path.

## Evidence
specs/issues-630-631-exception-features/evidence/live-631.md

## Notes
- Labels bug + P2 applied to #630 and #631; core.hooksPath set; branch fix/630-631-exception-features.
- Working tree also has unrelated speckit companion modifications (not committed).
