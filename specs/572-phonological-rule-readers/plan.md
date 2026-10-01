# Implementation Plan: Phonological rule readers — environment, rule features, POSes, disabled, iteration/sequence contexts

**Branch**: `fix/572-phonological-rule-readers` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/572-phonological-rule-readers/spec.md`
(REVIEWED; C1–C12 frozen by the interview of 2026-09-27)

**Note**: `setup-plan.ps1` reported `BRANCH=572-phonological-rule-readers`; the
actual branch is `fix/572-phonological-rule-readers` (the script derives the
label from the feature directory).

---

## Summary

Twelve frozen contract items, of which **seven are new readers** and **three
are fixes to members that are currently dead** (they promise behaviour they
cannot deliver, and one returns a .NET type name instead of text).

The new readers, all on `PhonologicalRuleOperations` (published) with a
wrapper property as the primitive (internal):

| Reader | Returns | Spec |
|---|---|---|
| `GetLeftContext(rule, rhs_index=0)` | `PhonologicalContext` or `None` | C1, C2 |
| `GetRightContext(rule, rhs_index=0)` | `PhonologicalContext` or `None` | C1, C2 |
| `GetInputPOSes(rule, rhs_index=0)` | `list[IPartOfSpeech]` | C3 |
| `GetRequiredRuleFeatures(rule, rhs_index=0)` | `RuleFeatureCollection` | C3, C4 |
| `GetExcludedRuleFeatures(rule, rhs_index=0)` | `RuleFeatureCollection` | C3, C4 |
| `IsDisabled(rule)` / `SetDisabled(rule, disabled)` | `bool` / `None` | C8 |
| `DescribeRule(rule)` | `str` | C11 |

The dead members, all on the internal `PhonologicalContext` /
`ContextCollection`:

| Member | Current behaviour | Becomes |
|---|---|---|
| `context_name` | `"SIL.LCModel.DomainImpl.MultiUnicodeAccessor"` | the context's own name, or `""` |
| `description` | `""` always (reads a member that does not exist) | `DescriptionOA`'s text, or `""` |
| `is_boundary_context` | always `False` (tests a class that does not exist) | tests `PhSimpleContextBdry` |
| `boundary_type` | always `-1` | **retired** → `boundary_marker` / `boundary_name` |
| `ContextCollection.boundary_contexts()` | always empty | filters on `PhSimpleContextBdry` |
| `ContextCollection.filter(name_contains=)` | never matches | filters on real names |

Plus new context members `is_iteration_context` / `min_count` / `max_count` /
`member` (C5) and `is_sequence_context` / `members` (C6), and one control
change: `Disabled` joins `GetSyncableProperties` (C9).

**Technical approach.** No new LCM access pattern. Every property this feature
reads was reflected off a live FieldWorks 9 runtime and recorded in
`evidence/live-surface-probe.json`; the wrapper base already performs the
`cast_to_concrete` that makes the concrete-only members reachable
(`Shared/wrapper_base.py:149`). The work is *exposing* verified members and
*repairing* four string/discriminator bugs, not discovering a surface.

**The one design constraint that shapes everything** (C10): pythonnet narrows
an object to the interface its owning collection yields, so `hasattr` against a
raw `PhonRulesOS` element is unsound — `RightHandSidesOS` reads as absent until
the object is cast. Measured, not assumed: `evidence/live-instance-probe.json`.

## Technical Context

**Language/Version**: Python 3.14.5 (`requires-python = ">=3.8,<3.15"`,
`pyproject.toml:12`); pythonnet `>=3.0.3, <3.2` (`pyproject.toml:39`; 3.1.0 is
the first release supporting 3.14)

**Primary Dependencies**: pythonnet → `SIL.LCModel` (FieldWorks 9);
`flexicon.code.Shared.string_utils` for all multilingual-string text
(`best_analysis_text` / `best_vernacular_text` / `best_text`,
`string_utils.py:160, 183, 205`); `flexicon.code.lcm_casting.cast_to_concrete`

**Storage**: FLEx projects via the LCM (`.fwdata` / `.fwbackup`). This feature
is **read-only against existing data**; the only writes are in tests that
construct iteration contexts and rule features, because no installed project
contains any (C12).

**Testing**: pytest. Two required invocations (Principle II) — the offline gate
`python -m pytest -m "not requires_live_project" -q` and the live gate
`$env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest <file> -m requires_live_project -q`.
Live tests carry `@pytest.mark.requires_live_project` and use the
`target_project` / `target_sandbox` / `sena3_sandbox` fixtures
(`tests/flex_plugin.py:1375`, `:1284`).

**Target Platform**: Windows + FieldWorks 9, both required. No
cross-platform story: the library is a pythonnet bridge.

**Project Type**: library (published API surface; no CLI, no service)

**Performance Goals**: none new. These are property reads off already-cached
LCM objects; the only cost is `cast_to_concrete`, which is memoised in the
wrapper base. Not a hot path.

**Constraints**:
- Writes only to Target, Sena 3, or a tempdir sandbox. Reads are unrestricted
  (Principle II).
- No new writer for any member touched (C1; `WireRule` remains the only
  composer, #142).
- `PhonologicalRuleOperations` is published; every method added is additive
  growth under Principle VII and needs only a regenerated surface baseline.
- `PhonologicalContext`, `ContextCollection` and the new `RuleFeatureCollection`
  are internal (`flexicon/code/**`, absent from `__all__`) and change freely.

**Scale/Scope**: 3 files edited, 2 created (`RuleFeatureCollection`, the
ratchet test), 4 new tests, 1 doc updated, ~26 sweep sites in
`flexicon/code/` + `docs/`, 8 contract items to satisfy.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Verdict | Basis |
|---|---|---|
| **I. Verify the LCM surface** | **PASS** | spec §2 tabulates 19 properties with declared type and r/w, each from `tests/contract/snapshots/liblcm_baseline.json` or a live pythonnet reflection (`run_mode: "live"`), corroborated by FieldWorks source at `HCLoader.cs:2341-2343`, `RuleFormulaVcBase.cs:520-554`, `RegRuleFormulaControl.cs:731-742`, `HCLoader.cs:2610-2623`, `HCLoaderTests.cs:405-411, 1084-1086`. Two names the issue asserted are recorded as **non-existent** (spec §2.2) and no design item depends on them. |
| **II. Live verification mandatory** | **PASS, with a hard planning constraint** | Both invocations are quoted in Technical Context. The constraint: no installed project holds an `IPhIterationContext` or `IPhPhonRuleFeat` (measured across 5 projects, `evidence/live-instance-probe.json`), so C5 and C4 **cannot** be verified against pre-existing data and require write-path tests on Target. Carried into [research.md](research.md) R-6 and the SC-008 success criterion. |
| **III. Controls, not prohibitions** | **ACTION REQUIRED before implementation** | C7 is a sweep across 26 sites (> ~20), and the Constitution's Development
Workflow requires a scanner with a two-way guard. C10 ("never `hasattr` a raw collection element") is an instruction an agent must *remember* unless encoded. Both become controls: `tests/test_issue572_boundary_context_ratchet.py` and a live wrapper test. Detailed in [research.md](research.md) R-4, including why this sweep needs **no frozen baseline** (target is zero). |
| **IV. Report the measurement** | **PASS** | Offline baseline recorded before any change: `2575 passed, 1081 deselected, 16 warnings in 18.97s` (`evidence/live-T1-surface.md`). SC-006 requires the arithmetic for any delta. |
| **V. Honest API surface** | **PASS — this feature *is* the fix** | Six members currently promise behaviour they do not deliver; C7 repairs them and retires `boundary_type`, whose name implied a discriminator the LCM does not have. The issue's own two errors (spec §2.2) are recorded rather than implemented. |
| **VI. Hide complexity, not behavior** | **PASS** | C5 returns `None` for unbounded rather than the `-1` LCM sentinel, and `best_analysis_text` is used for text rather than `str()`. The quirk that a disabled rule syncs as enabled (C9) is surfaced in behaviour, not smoothed away. |
| **VII. Expand freely** | **PASS — additive only** | All 12 new `Operations` members are growth (unrestricted). The only removals (`boundary_type`, `as_boundary_context`) are **internal**, so under 2.1.0's definition of "published" they need no cause and no `BREAKING CHANGE:` footer. Quality Gate 5 is satisfied by regenerating the surface baseline only. |

**Gates passed. One action item (Principle III) and one hard constraint
(Principle II / C12) are carried into the task list; neither is a violation, and
neither is waived.**

### Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified.

**Empty — no violations, therefore no exemptions requested.** Per Governance,
agents do not grant themselves exemptions; had any principle blocked a task,
this section would carry the blocked item rather than a justification for it.

## Project Structure

### Documentation (this feature)

```text
specs/572-phonological-rule-readers/
├── spec.md                          # REVIEWED; C1-C12 frozen
├── plan.md                          # this file
├── research.md                      # Phase 0 output
├── data-model.md                    # Phase 1 output
├── quickstart.md                    # Phase 1 output
├── contracts/
│   └── public-api.md                # Phase 1 output
├── evidence/
│   ├── live-T1-surface.md           # mandatory evidence (run_mode: live)
│   ├── live-surface-probe.json      # LCM reflection, every type the issue names
│   └── live-instance-probe.json     # real values from 5 installed projects
├── reviews/                         # (empty; gate 3 audit lives in plan.md)
└── tasks.md                         # Phase 2 — NOT created by /speckit-plan
```

### Source Code (repository root)

```text
flexicon/code/
├── Grammar/
│   ├── phonological_rule.py             # EDIT  PhonologicalRule: +7 members
│   ├── PhonologicalRuleOperations.py    # EDIT  +7 readers, GSP +Disabled
│   ├── PhonologicalRuleOperations.pyi   # EDIT  stub parity for new methods
│   └── MorphRuleOperations.py           # READ  IsDisabled precedent (:813-880)
├── System/
│   ├── phonological_context.py          # EDIT  6 dead members repaired, +6 new
│   ├── context_collection.py            # EDIT  boundary_contexts, filter
│   └── rule_feature.py                  # NEW   RuleFeature + RuleFeatureCollection
├── Shared/
│   ├── wrapper_base.py                  # READ  cast_to_concrete at :149
│   └── string_utils.py                  # READ  best_analysis_text at :160
└── __init__.py                          # READ  __all__ at :505 (not edited — additive)

docs/
└── USAGE_CONTEXTS.md                    # EDIT  8 PhBoundaryContext + 5 boundary_type

tests/
├── operations/
│   ├── test_target_live_smoke.py        # READ  canonical live template
│   ├── test_issue572_phonrule_readers_live.py   # NEW  read-path, morphboundary
│   └── test_issue572_phonrule_construct_live.py # NEW  write-path, Target
└── test_issue572_boundary_context_ratchet.py    # NEW  Principle III control
```

**Structure Decision**: single project, no new package. The feature touches the
existing Grammar and System domains only. `RuleFeatureCollection` lives beside
`PhonologicalContext` in `System/` because it is a `SmartCollection` over a
context-adjacent owned type and is consumed by a `Grammar/` reader; putting it
in `System/` keeps the import direction the same as the existing
`ContextCollection` dependency it parallels. `RuleFeature` is **not** exported
in `flexicon/__init__.py` (spec §5, C-Q4a) — it is internal, reached through
the reader.

## Post-Design Constitution Re-check

*Re-evaluated after Phase 1 design (research.md, data-model.md, contracts/,
quickstart.md).*

| Principle | Verdict | Change from pre-design, and why |
|---|---|---|
| **I** | **PASS** | Unchanged. Phase 1 introduced no new LCM member. `data-model.md` is a wrapper/collection model over an already-verified surface. |
| **II** | **PASS** | Unchanged, and now concrete: [quickstart.md](quickstart.md) §3 sequences the live write-path test on Target with capture-and-restore, and §2 sequences the read-path test against `morphboundary`. Both carry the `FLEXLIBS_REQUIRE_LIVE=1` invocation. |
| **III** | **PASS — controls specified** | Changed from ACTION REQUIRED to PASS. [research.md](research.md) R-4 fixes the ratchet's exact shape: a four-pass scanner modelled on `tests/test_flexlibs2_alias_ratchet.py` (AST, string literals, prose, comments+docstrings) with the target at **zero occurrences**, so `assert not offenders` *is* the frozen baseline, and the two-way guard is an allowlist-honesty backward test. R-5 adds the live wrapper test that makes C10 mechanical. |
| **IV** | **PASS** | Unchanged. [quickstart.md](quickstart.md) §4 requires the offline-gate arithmetic against the recorded baseline. |
| **V** | **PASS** | Unchanged, and Phase 1 strengthened it: [contracts/public-api.md](contracts/public-api.md) states the `None`/metathesis silence as a *contract*, not an accident, and every retired name is listed with its replacement. |
| **VI** | **PASS** | Unchanged. |
| **VII** | **PASS** | Unchanged. Re-confirmed against the actual surface: adding 7 methods to a published class and creating one internal class touches `flexicon/__init__.py`'s `__all__` **zero** times, so the change is pure additive growth and the surface baseline is regenerated rather than justified. |

**Post-design verdict: all seven principles PASS. No `BREAKING CHANGE:` footer is
required (Quality Gate 5 — purely additive). The surface baseline is
regenerated in the same commit.**

### Quality Gate obligations carried into tasks

| Gate | Obligation | Where planned |
|---|---|---|
| 1 | Both invocations run, full counts quoted, delta explained | quickstart §2, §3, §4 |
| 2 | Every LCM claim carries a citation | spec §2.1 table; cited per reader in contracts/public-api.md |
| 3 | Shaped bugs carry a **pattern audit** or a by-construction impossibility statement | plan.md §"Pattern audit" below; research.md R-7 |
| 4 | Docs and docstrings match merged code, one voice | `docs/USAGE_CONTEXTS.md` in the same commit as the code |
| 5 | Purely additive → regenerate surface baseline, no footer | tasks |

## Pattern audit (Quality Gate 3)

Required because `context_name`'s bug is a **named shape** — "ITsString /
IMultiString confusion" — and recurrence is possible by construction, so the
"impossible by construction" exemption does not apply.

**Instance.** `phonological_context.py:136` — `str(self._concrete.Name)` on an
`IMultiString`, returning the literal `"SIL.LCModel.DomainImpl.MultiUnicodeAccessor"`
for every context. Live-measured against all 7 contexts in `morphboundary`.

**Siblings found** (audit run over the whole tree; all paths in
`flexicon-572`):

| Site | Expression | Verdict |
|---|---|---|
| `flexicon/code/System/phonological_context.py:136` | `str(self._concrete.Name)` | **the instance** — returns a type name |
| `flexicon/code/System/phonological_context.py:155` | `str(self._concrete.Description)` | dead read; member absent from `IPhPhonContext` |
| `flexicon/code/System/phonological_context.py:323` | docstring `print(f"Segment: {seg.Name}")` | garbage in a **copied example** — `seg` is an `IPhPhoneme` |
| `flexicon/code/System/phonological_context.py:358` | docstring `print(f"Natural Class: {nc.Name}")` | garbage in a copied example — `nc` is an `IPhNaturalClass` |
| `flexicon/code/Grammar/affix_template.py:163` | docstring `print(f"Stratum: {wrapped.stratum.Name}")` | garbage in a copied example — `IMoStratum.Name` is `IMultiString` |
| `flexicon/code/Grammar/affix_slot.py:183` | docstring `print(f"Slot for POS: {slot.owner_pos.Name}")` | garbage in a copied example — `IPartOfSpeech.Name` is `IMultiString` |
| `inspect_rule_final.py:43` | `print(f"Name: {rule.Name}")` | garbage — **and the file is git-tracked** (see note) |

**Downstream consequence the audit surfaced.** `context_collection.py:151`
filters on `ctx.context_name`, and `context_collection.py:340` filters on
`by_type("PhBoundaryContext")`. The first can never match anything; the second
selects on a class that does not exist. Both are **shipped, documented**
convenience methods on an internal class, so no published name breaks — but the
docstrings in `context_collection.py` (lines 24, 39, 51, 324, 338) teach
callers to use them, and line 51 asserts a fictional distribution
(`#   PhBoundaryContext: 3 (37%)`).

**Scope ruling.** The six in-tree sites plus the doc prose are in scope: they
are 6 lines plus one doc file, they are the same defect, and leaving them means
C7's fix ships while a caller who copies the neighbouring example still gets a
type name — which Quality Gate 4 exists to prevent. The stray tracked script
`inspect_rule_final.py` is **not** edited in this feature; it is a scratch file
at the repo root with no test importing it, and deleting a tracked file is a
call for `tasks.md` to surface rather than for this plan to assume.
