# Tasks: Phonological rule readers (issue #572)

**Input**: [spec.md](spec.md) (C1-C12 frozen), [plan.md](plan.md),
[research.md](research.md), [data-model.md](data-model.md),
[contracts/public-api.md](contracts/public-api.md), [quickstart.md](quickstart.md)

**User stories.** The spec is written as contract items, not stories. The
stories below group those items by what a caller can do once each phase lands:

- **US1 (P1)**: A context describes itself. C5, C6, C7, C10 on
  `PhonologicalContext` / `ContextCollection`. SC-004.
- **US2 (P1)**: A rule describes itself. C1, C2, C3, C4, C8, C9, C11 on
  `PhonologicalRule` / `PhonologicalRuleOperations`. SC-001, SC-003, SC-005,
  SC-007, SC-008. Depends on US1, because its environment readers return the
  context wrapper US1 repairs.
- **US3 (P2)**: The dead names are gone and stay gone. The C7 sweep, the pattern
  audit docstrings, and the Principle III ratchet. SC-002.

**Two deviations from plan.md, both for file ownership.**

1. The plan's two live files (`..._readers_live.py` read path,
   `..._construct_live.py` write path) would each be shared by US1 and US2. So
   US1 gets its own `test_issue572_context_readers_live.py`, holding both its
   read-only `morphboundary` tests and its Target-built iteration-context test.
   US2 keeps the plan's two files. (quickstart.md §3 names
   `test_issue572_construct_live.py`. plan.md's
   `test_issue572_phonrule_construct_live.py` is the name used here.)
2. There is no Foundational phase. Nothing blocks all three stories. US1's two
   context files are the only shared dependency, and US2 already waits for
   US1.

**Two findings the plan did not record.**

- `tests/test_context_wrappers.py` holds 13 `PhBoundaryContext` mocks and a mock
  `boundary_type` (lines 73, 88, 171-437). The ratchet scans `tests/`, so US1
  owns updating it.
- No test or JSON file pins the method list of `PhonologicalRuleOperations`.
  `GetStratum` appears only in two live tests, and neither
  `test_issue339_public_import_surface.py` nor `test_operations_baseline.py`
  lists methods. research.md R-2 expected a "regenerated surface baseline".
  T027 checks this and records what it finds, and does not invent an edit.

**Required invocations** (CLAUDE.md, Principle II). They are quoted here once
and used by every verify task:

```
python -m pytest -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest <live test file> -m requires_live_project -q
```

Never bare `pytest` and never `pytest --ignore=tests/contract`.

---

## Phase 1: Setup

Files: `specs/572-phonological-rule-readers/evidence/capture_sc003.py`,
`specs/572-phonological-rule-readers/evidence/sc003-before.json`

**Wave 1: independent (different files):**

- [x] **T001** [P] Prepare the worktree. Run `git config core.hooksPath .githooks` and `gh repo set-default MattGyverLee/flexicon`. Confirm the git-ignored Target and Sena 3 `.fwbackup` fixtures are present in this worktree, and copy them from the main checkout if not (the `target_sandbox` / `sena3_sandbox` fixtures need them). Nothing to commit · (worktree config)
- [x] **T002** [P] Capture the SC-003 before-state. **This must run before any code edit.** Write a read-only script that opens `morphboundary` with `writeEnabled=False` and serialises `input_contexts`, `output_specs` and `metathesis_parts` for all four rules. Record each rule's GUID, `Disabled` and the class of each context. Run it and write the result to `sc003-before.json` · `specs/572-phonological-rule-readers/evidence/capture_sc003.py`, `specs/572-phonological-rule-readers/evidence/sc003-before.json`

---

## Phase 3: US1 (P1): A context describes itself

**Goal**: `PhonologicalContext` reports its real name, description, boundary,
iteration bounds and sequence members. It never returns a .NET type name, and
no check reads an uncast proxy.

**Independent Test**: wrap every context in `morphboundary`'s
`PhonologicalDataOA.ContextsOS`. Each returns real text or `""`. Both
`PhSimpleContextBdry` report `is_boundary_context`, and the `PhSequenceContext`
lists its members. An iteration context built on Target reports
`min_count` / `max_count` / `member`.

Files: `flexicon/code/System/phonological_context.py`,
`flexicon/code/System/context_collection.py`, `tests/test_context_wrappers.py`,
`tests/operations/test_issue572_context_readers_live.py`,
`specs/572-phonological-rule-readers/evidence/live-US1-contexts.md`

### Tests (write first; they fail before Wave 1 of Implementation)

**Wave 1: independent (different files):**

- [x] **T003** [P] [US1] Live test for the context readers, modelled on `tests/operations/test_target_live_smoke.py`, marked `requires_live_project`. **Read-only on `morphboundary`:** for every pooled and rule-referenced context, `context_name` does not contain `"SIL.LCModel"` (SC-004), and neither does `description`. Each `PhSimpleContextBdry` has `is_boundary_context is True`, a non-`None` `boundary_marker`, a non-empty `boundary_name` and a non-`None` `as_boundary_context()`. `ContextCollection.boundary_contexts()` is non-empty over the pool. `filter(name_contains=<a real name>)` matches at least one. The `PhSequenceContext` has `is_sequence_context` and non-empty `members`, each with a non-empty `context_name`. **C10 control:** wrap raw `ContextsOS[i]` elements directly and assert the concrete-only readers still report content. **Write path on `target_project`:** Target's pool is empty, so create a `TEST_` member context first (a `PhSimpleContextBdry` on an existing `IPhBdryMarker` is the cheapest). Then create two `TEST_` `PhIterationContext`s, `Minimum=1, Maximum=-1` and `Minimum=0, Maximum=3`, both with `MemberRA` on that member. Re-query them from `ContextsOS` after the write, not from the objects just built. Assert `max_count is None` for the first and `== 3` for the second, `min_count` 1 and 0, and `member.context_name` non-empty. In a `finally:`, remove every `TEST_` context and assert `ContextsOS` is back to its pre-test count · `tests/operations/test_issue572_context_readers_live.py`
- [x] **T004** [P] [US1] Update the offline mock suite to the real class names. `"PhBoundaryContext"` becomes `"PhSimpleContextBdry"` at every site (lines 73, 171-437), and the mock `boundary_type` (line 88) becomes `boundary_marker` / `boundary_name`. Add mock cases for `boundary_contexts()` selecting `PhSimpleContextBdry`, and for an iteration mock whose `Maximum == -1` yields `max_count is None` · `tests/test_context_wrappers.py`

### Implementation

**⟶ Wait for the Tests wave to finish, then:**

**Wave 1: independent (different files):**

- [x] **T005** [P] [US1] Repair the dead members (C7). `context_name` becomes `best_analysis_text(Name)` or `""`. `description` becomes the text of `DescriptionOA`'s name via `best_analysis_text`, or `""`. `is_boundary_context` tests `"PhSimpleContextBdry"`. Retire `boundary_type` silently: no `DeprecationWarning` (Q3). Add `boundary_marker`, which returns `FeatureStructureRA` as `IPhBdryMarker` or `None`, and `boundary_name`, which returns the marker's name text or `""`. Repair `as_boundary_context()` to return `self._concrete` when `is_boundary_context` is true. Fix the docstring examples at `:323` (`seg.Name`) and `:358` (`nc.Name`) to use `best_analysis_text`. Remove every `PhBoundaryContext` mention from the module and class docstrings. Every read goes through `self._concrete` (C10) · `flexicon/code/System/phonological_context.py`
- [x] **T006** [P] [US1] `boundary_contexts()` filters `by_type("PhSimpleContextBdry")`. Fix the docstrings at lines 24, 39, 51 and 324-338, including the fictional `PhBoundaryContext: 3 (37%)` distribution. Leave `filter(name_contains=)` unedited: T005 repairs it through `context_name` (data-model §6) · `flexicon/code/System/context_collection.py`

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T007** [US1] Add the new context members (C5, C6). `is_iteration_context` tests `class_type == "PhIterationContext"`. `min_count` returns `Minimum`, or `-1` when the context is not an iteration context. `max_count` returns `Maximum`, or `None` when `Maximum == -1`, and the docstring states that `None` means unbounded and cites `RuleFormulaVcBase.cs:554`. `member` returns `MemberRA` wrapped as `PhonologicalContext`, or `None`. `is_sequence_context` tests `class_type == "PhSequenceContext"`. `members` returns a `ContextCollection` of wrapped `MembersRS`, and its docstring states that the members are references into `PhonologicalDataOA.ContextsOS` and that removing the slot leaks them (#134). Import `ContextCollection` lazily inside `members` if a module-level import would be circular · `flexicon/code/System/phonological_context.py`

**⟶ Wait for T007 to finish, then:**

- [x] **T008** [US1] Verify. Run `python -m pytest tests/test_context_wrappers.py -q`, then the live invocation on `tests/operations/test_issue572_context_readers_live.py` with `FLEXLIBS_REQUIRE_LIVE=1`. Confirm `tests/live_status.json` shows `"run_mode": "live"`. Write the evidence file with the exact commands, `run_mode`, the iteration contexts' pre-state (pool count, and no `TEST_` rows) and post-state re-queried from the LCM, the restore count, and the pass/fail lines · `specs/572-phonological-rule-readers/evidence/live-US1-contexts.md`

**Checkpoint**: every context in a live project describes itself through
`PhonologicalContext` alone, and the iteration reader is proven on constructed
data (SC-004, SC-008 iteration half).

---

## Phase 4: US2 (P1): A rule describes itself

**Goal**: with `flexicon` only, a script prints every rule with its input,
output, environment, required and excluded rule features, input POSes and
disabled state (SC-001). `DescribeRule` renders any rule without raising
(SC-005). A disabled rule syncs as disabled (C9).

**Independent Test**: on `morphboundary`, `GetLeftContext` /
`GetRightContext` / `IsDisabled` / `DescribeRule` return the values in
quickstart.md §2a and §2d, and the SC-003 capture is unchanged. On Target, a
constructed rule with rule features and POSes reads back through
`GetRequiredRuleFeatures` / `GetExcludedRuleFeatures` / `GetInputPOSes`.

Files: `flexicon/code/System/rule_feature.py` (NEW),
`flexicon/code/Grammar/phonological_rule.py`,
`flexicon/code/Grammar/PhonologicalRuleOperations.py`,
`flexicon/code/Grammar/PhonologicalRuleOperations.pyi`,
`tests/operations/test_issue572_phonrule_readers_live.py`,
`tests/operations/test_issue572_phonrule_construct_live.py`,
`tests/operations/test_issue572_phonrule_offline.py`,
`specs/572-phonological-rule-readers/evidence/live-US2-rules.md`

### Tests (write first; they fail before Wave 1 of Implementation)

**Wave 1: independent (different files):**

- [ ] **T009** [P] [US2] Live read-path test, read-only on `morphboundary`. For each of the four rules, `has_environments is True`, and left/right contexts match the quickstart §2a table (for `t deletion`, the left is `None` and it is returned, not raised). **C10 control:** raw `PhonRulesOS[0]` fails `hasattr(raw, "RightHandSidesOS")`, but the wrapper's `has_environments` is `True`. `IsDisabled` matches the `Disabled` recorded in `sc003-before.json`. `GetInputPOSes` returns a `list`. `GetRequiredRuleFeatures` / `GetExcludedRuleFeatures` return an empty `RuleFeatureCollection`, not `None`. `rhs_index=99` raises `IndexError`. **SC-003:** `input_contexts`, `output_specs` and `metathesis_parts` serialise identically to `sc003-before.json`. **SC-005:** `DescribeRule` is non-empty for all four rules and contains neither `"SIL.LCModel"` nor `" object at 0x"`. **SC-001:** one test prints every rule with all seven parts, and the module imports nothing from `SIL.*`, makes no `ClassName` test and calls no `cast_to_concrete` · `tests/operations/test_issue572_phonrule_readers_live.py`
- [ ] **T010** [P] [US2] Live write-path test on `target_project` (use `target_sandbox` if Target is locked), with every object prefixed `TEST_`. Build a `TEST_` `PhRegularRule` (via the class's `Create` / `WireRule`). Build two `TEST_` `IPhPhonRuleFeat`s in `PhonologicalDataOA.PhonRuleFeatsOA.PossibilitiesOS`, with `ItemRA` on an `IMoInflClass` (create a `TEST_` one under a POS if Target has none) and on an `ICmPossibility` respectively. Put one in `ReqRuleFeatsRC` and one in `ExclRuleFeatsRC`, and add a POS to `InputPOSesRC`. Then **re-fetch the rule by GUID** and assert: `.names` from `GetRequiredRuleFeatures` / `GetExcludedRuleFeatures`, each `.items` target's identity, `item_name` non-empty, and `GetInputPOSes` containing the POS (SC-008 rule-feature half). `SetDisabled(rule, True)` is re-read as `True` through a fresh lookup, and `GetSyncableProperties(rule)["Disabled"] is True`. Build a `TEST_` `PhMetathesisRule`. Assert `has_environments is False`, `GetLeftContext` returns `None` with **no** warning recorded (`recwarn` empty, Q2), and `DescribeRule` is non-empty. Build a regular rule with its RHS removed: `DescribeRule` is non-empty. Build a regular rule whose right context is an unbounded iteration context: `DescribeRule` contains `*` and not `-1`. In a `finally:`, delete every `TEST_` object and assert that the rule, pool, possibility and inflection-class counts equal the pre-state · `tests/operations/test_issue572_phonrule_construct_live.py`
- [ ] **T011** [P] [US2] Offline tests. `GetSyncableProperties` on a mock rule includes a `"Disabled"` bool key beside `Name` / `Description` / `Direction` / `StratumGuid`. `DescribeRule(None)` returns a non-empty `str`. The seven other new readers raise `FP_NullParameterError` for `None`. `SetDisabled` raises `FP_ReadOnlyError` when `project.writeEnabled` is false · `tests/operations/test_issue572_phonrule_offline.py`

### Implementation

**⟶ Wait for the Tests wave to finish, then:**

**Wave 1: single task:**

- [ ] **T012** [US2] New module with the standard file header. `RuleFeature(LCMObjectWrapper)` provides `name` (`best_analysis_text` of its own `Name`), `item` (`ItemRA`, uncast, or `None`) and `item_name` (`best_analysis_text` of the target's `Name`, with no assumption about its type, or `""`). `RuleFeatureCollection(SmartCollection)` provides the properties `names` and `items`. Do not model `FeatureStructureRA` (spec §2.2.1). Do not export it from `flexicon/__init__.py` (C-Q4a) · `flexicon/code/System/rule_feature.py`

**⟶ Wait for Wave 1 to finish, then:**

- [ ] **T013** [US2] Extend the wrapper (the primitive, Q4). `has_environments` is `True` only for a concrete `IPhRegularRule` with at least one RHS. Add `left_context(rhs_index=0)` / `right_context(rhs_index=0)`, which return `PhonologicalContext` or `None`, and return `None` silently for a metathesis rule (C2). `input_poses(rhs_index=0)` returns `list(InputPOSesRC)`. `required_rule_features` / `excluded_rule_features(rhs_index=0)` always return a `RuleFeatureCollection`. `is_disabled` and `set_disabled(disabled)` follow the house wrapper-setter write check. An out-of-range `rhs_index` on a rule that has RHSs raises `IndexError`. Every read goes through `self._concrete` (C10). Do not change `__str__` or any existing member (SC-003) · `flexicon/code/Grammar/phonological_rule.py`

**⟶ Wait for T013 to finish, then:**

**Wave 3: independent (different files):**

- [ ] **T014** [P] [US2] Add the published readers, each `@OperationsMethod`, each resolving through `__ResolveObject` and delegating to T013. They are `GetLeftContext`, `GetRightContext`, `GetInputPOSes`, `GetRequiredRuleFeatures` and `GetExcludedRuleFeatures` (all `rhs_index=0`), plus `IsDisabled` and `SetDisabled`, mirroring `MorphRuleOperations.py:813-880` in signature and contract but with no `hasattr` guard (R-8). `SetDisabled` checks `writeEnabled` first and runs inside the class's transaction bracket. Docstrings state the documented silences (contract §1) and show `FLExProject` usage. Add `props["Disabled"] = rule.Disabled` to `GetSyncableProperties`, with no base change (C9). Correct the `IPhPhonRule` docstring mentions to `IPhSegmentRule` (C8) · `flexicon/code/Grammar/PhonologicalRuleOperations.py`
- [ ] **T015** [P] [US2] Stub parity for all eight new methods, `DescribeRule` included, with the signatures exactly as in contracts/public-api.md §1 · `flexicon/code/Grammar/PhonologicalRuleOperations.pyi`

**⟶ Wait for Wave 3 to finish, then:**

- [ ] **T016** [US2] `DescribeRule(rule_or_hvo)` (C11, lowest priority, last). It is read-only and **total**, mirroring `InflectionFeatureOperations.DescribeFeatStruc` (`:1015`): it accepts a wrapper, a rule, an HVO or `None`. It renders `input -> output / left _ right`. An absent context renders as `-`. A sequence renders its members in order. An iteration context renders `(member){min,max}`, with `*` for `max_count is None`. A metathesis rule renders from `metathesis_parts`. Wrap each piece so that an unexpected shape degrades to a placeholder and never raises, never shows a .NET type name, and never shows a Python repr · `flexicon/code/Grammar/PhonologicalRuleOperations.py`

**⟶ Wait for T016 to finish, then:**

- [ ] **T017** [US2] Verify. Run `python -m pytest tests/operations/test_issue572_phonrule_offline.py -q`, then the live invocation on `tests/operations/test_issue572_phonrule_readers_live.py` and on `tests/operations/test_issue572_phonrule_construct_live.py` with `FLEXLIBS_REQUIRE_LIVE=1`. Confirm `"run_mode": "live"`. Write the evidence file with the commands, `run_mode`, the SC-003 comparison result, and the constructed rule's pre-state and post-state re-queried by GUID (features, POSes, `Disabled`, `GetSyncableProperties`). Include the restore counts and the pass/fail lines · `specs/572-phonological-rule-readers/evidence/live-US2-rules.md`

**Checkpoint**: the issue's acceptance shape works. Every rule prints fully
through `flexicon` with no `IPh*` import, `ClassName` test or cast. Every write
in the live tests is re-queried from the LCM.

---

## Phase 5: US3 (P2): The dead names are gone and stay gone

**Goal**: zero `PhBoundaryContext` / `IPhBoundaryContext` in `flexicon/code/`,
`docs/` and `tests/` outside the allowlist, enforced by a ratchet. The copied
docstring examples no longer print a type name.

**Independent Test**: `python -m pytest tests/test_issue572_boundary_context_ratchet.py -q`
passes at zero offenders, and its backward guard passes.

Files: `tests/test_issue572_boundary_context_ratchet.py`,
`docs/USAGE_CONTEXTS.md`, `flexicon/code/Grammar/affix_template.py`,
`flexicon/code/Grammar/affix_slot.py`

### Tests (write first; it fails until Wave 1 below and US1 are done)

- [ ] **T018** [US3] Ratchet, modelled on `tests/test_flexlibs2_alias_ratchet.py` (research R-4). It makes four passes (AST, string literal, prose `.md` / `.rst`, and comment+docstring via `tokenize` and `ast.get_docstring`) for the substring `PhBoundaryContext`, and asserts **zero** offenders with no count baseline. Reuse `_SKIP_DIR_NAMES` verbatim (it already skips `specs/`). The allowlist has exactly two entries, each with a reason: `CHANGELOG.md` (the 4.x history entry at `:3313`) and `tests/operations/test_issue572_phonrule_surface_live.py` (the probe that records the class does not exist). Add the backward guard `test_every_allowlisted_path_still_earns_its_hole`, which fails on an entry whose file is gone or no longer mentions the string · `tests/test_issue572_boundary_context_ratchet.py`

### Implementation

**Wave 1: independent (different files):**

- [ ] **T019** [P] [US3] Rewrite the 8 `PhBoundaryContext` and 5 `boundary_type` mentions. Use `PhSimpleContextBdry`, `boundary_marker` / `boundary_name`, and the new `is_iteration_context` / `min_count` / `max_count` / `member` / `is_sequence_context` / `members`. Correct the `context_name` examples to show real text. Quality Gate 4: this lands in the same commit as T005-T007 · `docs/USAGE_CONTEXTS.md`
- [ ] **T020** [P] [US3] Docstring example at `:163`: `wrapped.stratum.Name` becomes `best_analysis_text(wrapped.stratum.Name)` (pattern audit) · `flexicon/code/Grammar/affix_template.py`
- [ ] **T021** [P] [US3] Docstring example at `:183`: `slot.owner_pos.Name` becomes `best_analysis_text(slot.owner_pos.Name)` (pattern audit) · `flexicon/code/Grammar/affix_slot.py`

**⟶ Wait for Wave 1 and Phase 3 to finish, then:**

- [ ] **T022** [US3] Verify. Run `python -m pytest tests/test_issue572_boundary_context_ratchet.py -q` and `rg -n "PhBoundaryContext|IPhBoundaryContext" flexicon docs tests`, and expect only the two allowlisted hits. For the other SC-002 string, run `rg -n "FeatureStructureRA" flexicon/code/System/rule_feature.py docs`, and confirm no hit ties `FeatureStructureRA` to `IPhPhonRuleFeat`. Record the outputs in the Phase 6 evidence (T027) · (no file owned)

**Checkpoint**: SC-002 holds, and the ratchet stops it regressing.

---

## Phase 6: Polish and cross-cutting

Files: `CHANGELOG.md`, `docs/API_ISSUES_CATEGORIZED.md`,
`specs/572-phonological-rule-readers/evidence/decisions.md`,
`specs/572-phonological-rule-readers/evidence/live-final.md`

**Wave 1: independent (different files):**

- [ ] **T023** [P] Add an `Unreleased` entry covering the eight `PhonologicalRuleOperations` readers, the `Disabled` sync key, the context repairs, and the internal `boundary_type` retirement. Do not add a new `PhBoundaryContext` mention. Follow the close-keyword rule in `.githooks/README.md` · `CHANGELOG.md`
- [ ] **T024** [P] Category 8: record that `IPhPhonRuleFeat` has no `FeatureStructureRA` (only `ItemRA`), that `PhBoundaryContext` is really `PhSimpleContextBdry`, and that `IPhPhonContext.Name` is an `IMultiString` (the `context_name` bug) · `docs/API_ISSUES_CATEGORIZED.md`
- [ ] **T025** [P] `inspect_rule_final.py` decision (plan pattern audit, R-7). Run `rg -n inspect_rule_final` over the tree and record what references it. **Do not edit or delete it.** Record it as a `needs_human` item: delete the tracked scratch script, or fix `:43`. A human decides · `specs/572-phonological-rule-readers/evidence/decisions.md`

**⟶ Wait for Wave 1 and all story phases to finish, then:**

- [ ] **T026** Surface checks. Run `python scripts/check_decorators.py` (all eight new methods carry `@OperationsMethod`), then `python -m pytest tests/test_issue339_public_import_surface.py tests/test_operations_baseline.py tests/test_syncable_properties_member_ratchet.py -q`. Confirm `flexicon/__init__.py`'s `__all__` is unchanged. Confirm whether any baseline file pins the class's methods. If one does, regenerate it. If none does, say so in T027's evidence rather than claim a regeneration (R-2) · (no file owned)
- [ ] **T027** Validate against the Success Criteria (no `owns: validation` hook exists, so this phase owns the suite run). Run the offline gate `python -m pytest -m "not requires_live_project" -q`, and report the full counts and the arithmetic against `2575 passed, 1081 deselected` (SC-006): which new offline tests account for the delta, and any failure verbatim. Then run the live gate on all three new live files in one `FLEXLIBS_REQUIRE_LIVE=1` invocation, and confirm `"run_mode": "live"` (SC-007). Tick SC-001 to SC-008 against their evidence files, and include T022's and T026's outputs. An unverified item is reported as `FAIL: unverified`, never as clean · `specs/572-phonological-rule-readers/evidence/live-final.md`

---

## Dependencies & Execution Order

**Phases**: Setup (T002 before any code edit) → US1 → US2 → Polish. US3
depends on US1 only (the ratchet passes once `phonological_context.py`,
`context_collection.py` and `test_context_wrappers.py` are clean). It can run
beside US2, and must finish before Polish.

**Waves within each phase:**

- **Setup**: T001 ∥ T002.
- **US1**: tests T003 ∥ T004 → T005 ∥ T006 → T007 (same file as T005) → T008.
- **US2**: tests T009 ∥ T010 ∥ T011 → T012 → T013 → T014 ∥ T015 → T016 (same
  file as T014) → T017.
- **US3**: T018 → T019 ∥ T020 ∥ T021 → T022 (also waits for US1).
- **Polish**: T023 ∥ T024 ∥ T025 → T026 → T027.

**File ownership**: every path above appears under exactly one phase. The two
shared-looking files are split: `phonological_context.py` belongs to US1 only,
and `PhonologicalRuleOperations.py` belongs to US2 only, with `DescribeRule` as
US2's last wave rather than its own story.

**Commit note**: T019 (`docs/USAGE_CONTEXTS.md`) must land in the same commit
as T005-T007 (Quality Gate 4).
