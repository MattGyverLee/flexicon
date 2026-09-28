# Final validation: issue #572 (T027)

Date: 2026-09-28. Worktree `C:\Github\flexicon-572`, branch
`fix/572-phonological-rule-readers`.

## Offline gate (SC-006)

```
python -m pytest -m "not requires_live_project" -q
2593 passed, 1100 deselected, 16 warnings in 12.93s
```

**Result: PASS.** Zero failures. Baseline (`live-T1-surface.md:51`):
`2575 passed, 1081 deselected`.

| Delta | Count | Source |
|---|---|---|
| passed | +18 | `test_issue572_phonrule_offline.py` 11, `test_issue572_boundary_context_ratchet.py` 5, `test_context_wrappers.py` 2 (26 now, 24 on `main`) |
| deselected | +19 | live tests in `test_issue572_context_readers_live.py` 5, `test_issue572_phonrule_readers_live.py` 10, `test_issue572_phonrule_construct_live.py` 4 |

2575 + 18 = 2593 and 1081 + 19 = 1100. The surface probe
(`test_issue572_phonrule_surface_live.py`, 2 tests) already existed when the
baseline was taken, so it is in the 1081.

The 16 warnings are pre-existing (`GramCatOperations` deprecation alias and a
`PytestReturnNotNoneWarning` in `test_lcm_direct.py`). None is from this
feature.

**One failure found and fixed during this run.** The first offline run failed
`test_issue572_boundary_context_ratchet.py::TestRetiredBoundaryNameIsGone::test_no_retired_name_in_docs_prose`.
T024 had added the Category 8 entry to `docs/API_ISSUES_CATEGORIZED.md`, and
that task requires naming the retired class. The ratchet allowlist was written
before T024 and did not include it. Fix: `docs/API_ISSUES_CATEGORIZED.md`
became a third allowlist entry with its reason, and the Category 8 text now
says "three-entry allowlist". The backward guard
(`test_every_allowlisted_path_still_earns_its_hole`) covers the new entry.

## Live gate (SC-007)

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue572_context_readers_live.py tests/operations/test_issue572_phonrule_readers_live.py tests/operations/test_issue572_phonrule_construct_live.py -m requires_live_project -q
19 passed in 8.96s
```

`tests/live_status.json`: `"run_mode": "live"`, `"run_timestamp":
"2026-09-28T19:29:36Z"`, `uncategorized_live_tests: []`.

**Result: PASS.** Pre-state and post-state values read back from the LCM
are in `live-US1-contexts.md` and `live-US2-rules.md`. This run re-executed
those tests; each one re-queries after its write and restores in `finally:`.

## Ratchet and SC-002 greps (T022)

```
python -m pytest tests/test_issue572_boundary_context_ratchet.py -q
5 passed in 1.13s

rg -n "PhBoundaryContext|IPhBoundaryContext" flexicon docs tests
docs\API_ISSUES_CATEGORIZED.md:688   (Category 8 correction heading, allowlisted)
docs\API_ISSUES_CATEGORIZED.md:697   (Category 8 correction table, allowlisted)
tests\operations\test_issue572_phonrule_surface_live.py:61   (probe, allowlisted)
tests\operations\test_issue572_phonrule_surface_live.py:78   (probe, allowlisted)
```

The `CHANGELOG.md:3313` history entry is also allowlisted and sits outside
the `rg` scope. Every hit is an allowlisted file.

```
rg -n "FeatureStructureRA" flexicon/code/System/rule_feature.py docs
```

`rule_feature.py:24` and `:83` both say `IPhPhonRuleFeat` has *no*
`FeatureStructureRA`. The `docs/` hits either describe contexts
(`IPhSimpleContextSeg`, `IPhSimpleContextNC`, `IPhBdryMarker`) or are the
Category 8 entry saying the field does not exist on rule features. No hit
ties `FeatureStructureRA` to `IPhPhonRuleFeat` as a real field.

## Surface checks (T026)

- `python scripts/check_decorators.py flexicon/code/Grammar/PhonologicalRuleOperations.py`
  -> `[OK] No duplicate decorators found`. A grep confirms all eight new
  methods (`GetLeftContext`, `GetRightContext`, `GetInputPOSes`,
  `GetRequiredRuleFeatures`, `GetExcludedRuleFeatures`, `IsDisabled`,
  `SetDisabled`, `DescribeRule`) sit directly under `@OperationsMethod`.
- `python -m pytest tests/test_issue339_public_import_surface.py tests/test_operations_baseline.py tests/test_syncable_properties_member_ratchet.py -q`
  -> `403 passed, 4 warnings`.
- `flexicon/__init__.py`: no commit on this branch touches it, and `__all__`
  is unchanged. `git diff main` shows one comment-path line, which comes from
  `main` moving ahead.
- **No baseline file pins `PhonologicalRuleOperations`' method list.** A
  search of `tests/**/*.json|*.txt` for `GetStratum` / `DescribeRule` finds
  only `tests/live_status.json`, which is run output. Nothing was
  regenerated (R-2).

## Success criteria

| SC | Result | Evidence |
|---|---|---|
| SC-001 rule prints all seven parts via `flexicon` only | PASS | `test_print_every_rule_with_all_seven_parts` (live), `live-US2-rules.md` |
| SC-002 retired names gone, ratcheted | PASS | ratchet 5 passed, greps above |
| SC-003 existing wrapper output unchanged | PASS | `test_sc003_serialisation_matches_before_capture` against `sc003-before.json` |
| SC-004 `context_name` never a type name | PASS | `test_context_name_and_description_have_no_type_names` (live), `live-US1-contexts.md` |
| SC-005 `DescribeRule` total, no leaks | PASS | `test_describe_rule_nonempty_without_leaks`, `TestDescribeRuleTotality` (live) |
| SC-006 offline gate | PASS | 2593 passed, arithmetic above |
| SC-007 live gate | PASS | 19 passed, `run_mode: live` |
| SC-008 live tests for iteration and rule-feature readers | PASS | `test_iteration_bounds_and_member`, `test_features_poses_and_disabled` |

## Human decision

`inspect_rule_final.py` was deleted on the maintainer's decision, together
with its `context7.json` exclude entry. See `decisions.md` D-1.
