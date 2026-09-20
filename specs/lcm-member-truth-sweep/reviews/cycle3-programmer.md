# Cycle 3 -- Programmer report: #283, `Grammar/EnvironmentOperations.py`

**Tasks:** T3.1-T3.6 (checkpoint 3, spec.md bindings C7/C8/C9).
**Commit:** NOT made -- per briefing, the lead commits after review.

---

## T3.1 (C7) -- rename the two readers

`flexicon/code/Grammar/EnvironmentOperations.py`:

- `GetLeftContextPattern` (was `:494,495`): replaced the
  `if hasattr(env, "LeftContextOA") and env.LeftContextOA: return
  env.LeftContextOA` / `return None` pair with a single
  `return getattr(env, "LeftContextRA", None)`, per the briefing's stated
  preference for the plain-getattr shape. Docstring `Notes` updated to
  name `LeftContextRA` and point at spec.md C7.
- `GetRightContextPattern` (was `:550,551`): identical treatment with
  `RightContextRA`.

## T3.2 (C7) -- Duplicate: unconditional reference assignment

Deleted the entire `if deep:` block (was `:630-655`) -- the
`from ..lcm_casting import clone_properties` import, both
`ServiceLocator.ObjectRepository.NewObject(src_context.ClassID)` calls,
the `clone_properties(...)` calls, and both bare `except Exception: pass`
swallows -- and replaced it with, outside any conditional:

```python
if source.LeftContextRA is not None:
    duplicate.LeftContextRA = source.LeftContextRA
if source.RightContextRA is not None:
    duplicate.RightContextRA = source.RightContextRA
```

`deep` is read nowhere else in the method body now.

## T3.3 (C7) -- docstrings + CHANGELOG

All six cited sites in `EnvironmentOperations.py` corrected:

- `:479`/`:535` region (`GetLeftContextPattern`/`GetRightContextPattern`
  Notes) -- now name `LeftContextRA`/`RightContextRA` with a spec.md C7
  pointer.
- `:564-565` (`Duplicate` Args, `deep`) -- rewritten to state `deep` is
  INERT for this method, pinned only for `.pyi` compatibility, with the
  Reference-Atomic rationale and a spec.md C7 pointer.
- `:583-585` (`Duplicate` Example, "Shallow copy") -- the misleading
  "Shallow copy (no context objects)" comment is replaced with a comment
  stating `deep` is inert for context objects and both calls produce
  identical context references.
- `:591` (`Duplicate` Notes) -- rewritten to describe unconditional
  reference-copy semantics, replacing the old "deep=True copies owned
  context objects" line.
- `:674-675` region (`__ResolveObject` narrative) -- rewritten to past
  tense: the missing-cast defect this method fixes is unrelated to the
  OA/RA name defect; the paragraph now says the getters *historically*
  also returned `None` on a correctly-cast object because the property
  names they read never existed, and states the real names and a
  spec.md C7 pointer, while keeping the still-true missing-cast
  narrative (Name/StringRepresentation/GetSyncableProperties) intact.
- `:746` region (`GetSyncableProperties` Notes) -- "Does not include
  owned objects (LeftContextOA, RightContextOA)" -> "Does not include
  context references (LeftContextRA, RightContextRA -- see spec.md C7)".

`CHANGELOG.md`: added a `### Fixed` entry under `[Unreleased]`, following
the house style of the existing #317 entry immediately above it (prose
description of the defect, then the fix, then the `deep`-is-inert /
no-real-caller note). Referenced as "#283" in prose only -- no close/fix/
resolve keyword immediately precedes it anywhere in the entry.

Grep confirms zero remaining live `LeftContextOA`/`RightContextOA`
references in `EnvironmentOperations.py` -- the three hits that remain
are inside docstring/comment prose explicitly describing the historical
bug (lines documenting "the historical `LeftContextOA` name never
existed").

## T3.4 (Q4) -- deep=False caller check

Re-ran (independently, after reading the file) the grep across
`flexicon/`, `examples/`, `tests/`:

```
grep -rn "deep=False" flexicon/ examples/ tests/
```

**Confirmed: zero real callers of `EnvironmentOperations.Duplicate` (or
`project.Environments.Duplicate`) pass `deep=False`.** The only hit
against this method is the docstring example at
`EnvironmentOperations.py:585` itself (now rewritten under T3.3). Every
other `deep=False` hit in the grep output belongs to a different
Operations class's own `Duplicate`/`__copy_sense_content` method
(`MorphRuleOperations`, `NaturalClassOperations`, `PhonemeOperations`,
`PhonologicalRuleOperations`, `POSOperations`, `AllomorphOperations`,
`EtymologyOperations`, `ExampleOperations`, `LexEntryOperations`,
`LexSenseOperations`, `PronunciationOperations`, `VariantOperations`,
`AgentOperations`, `possibility_item_base`, `PersonOperations`,
`FilterOperations`, `MediaOperations`, `CustomFieldOperations`,
`ProjectSettingsOperations`, `WritingSystemOperations`,
`DiscourseOperations`, `ParagraphOperations`, `TextOperations`,
`WfiAnalysisOperations`, `WfiGlossOperations`, `WfiMorphBundleOperations`,
`WordformOperations`), plus `sync/tests/test_duplicate_operations.py` and
`tests/operations/test_lexentry_duplicate.py`, none of which call
`Environments.Duplicate`. No STOP condition was triggered; T3.2 landed
as planned. This matches the answer the briefing anticipated. Documented
in the CHANGELOG entry per T3.3.

## T3.5 (C8) -- invert the bug-asserting anchors

**(a) `tests/operations/test_260_environment_resolver_gate.py:311-317`
(class `TestP7DiscoveredWrongPropertyName`).** Read the whole test and
class first, as instructed. Handled the subtlety exactly as briefed:

- Kept the class and its narrative docstring (extended, not replaced,
  with an "INVERTED under spec.md C8/C7 (#283)" paragraph explaining the
  discovery-to-fix arc).
- Kept the existing no-context method
  (`test_left_and_right_context_are_reference_atomic_not_owning_atomic`)
  and its `assert result is None` UNCHANGED in truth value -- only the
  surrounding comment and failure message were reworded to say this is
  the genuine "no context was ever assigned" case, not the old wrong-
  property-name case, with a pointer to spec.md C8.
- Also updated the module header's original "P7 CORRECTION" narrative
  paragraph (the block ending "...locks the DISCOVERY... not a fix"),
  changing tense to past and appending a note that the fix landed under
  #283/spec.md C7-C8.
- **Added** a new test,
  `test_left_context_returns_seeded_context_by_reference`, that seeds a
  real `IPhSimpleContextSeg` via `IPhSimpleContextSegFactory`, adds it to
  `phon_data.ContextsOS` first (unowned-assignment guard, per the
  `test_2d` precedent), sets `FeatureStructureRA` to a phoneme, assigns
  it to `env.LeftContextRA`, all inside `envs._TransactionCM(...)`, then
  re-reads the environment fresh **by HVO** and asserts
  `GetLeftContextPattern(reread)` is non-`None` and `.Hvo`-equal to the
  seeded context. Cleanup removes the seeded context from `ContextsOS`
  and deletes the environment in a `finally:`.

  **Fixture choice deviation, explicitly reasoned and reported rather
  than silently substituted:** the new seeded test uses `sena3_sandbox`,
  not `target_sandbox` (which every other test in this file uses).
  Building a legal `IPhSimpleContextSeg` requires an existing
  `IPhPhoneme` to assign to `FeatureStructureRA`; CLAUDE.md's Live LCM
  Verification table describes Target as "mostly blank scratch" with no
  guarantee of a seeded phoneme inventory, whereas Sena 3 is the
  populated project and is the fixture `test_2d` already used
  successfully for this exact seeding pattern. I did not attempt to
  verify Target's phoneme inventory live (offline-only per the
  briefing), so I did not gamble the new test on an unconfirmed
  assumption. Flagging this for lex-verification/lex-domain review in
  case a Target-only policy is stricter than I've inferred.

**(b) `test_lcm_member_truth_sweep.py::test_2d_seed_and_observe_
duplicate_reference_semantics` (originally `:250-388`).** Converted the
print-only observation to hard assertions:
- `dup_left_hvo is not None`, `dup_right_hvo is not None`.
- `dup_left_hvo == src_left_hvo`, `dup_right_hvo == src_right_hvo`
  (HVO identity, both re-read from the LCM after `Duplicate`, matching
  the pre-existing re-read-by-HVO discipline already in the test).
- Deleted the `if dup_left_hvo is None and dup_right_hvo is None:
  print("[2d] OBSERVATION: Duplicate did not populate...")` branch
  documenting pre-fix behaviour.
- The docstring gained an "INVERTED under spec.md C7/C8 (#283)"
  paragraph explaining the change from observation to assertion.
- The `finally:` cleanup block (original lines ~358-388) was left
  **byte-for-byte unchanged**, as instructed. (Note for the record, not
  a defect: because post-fix `Duplicate` now assigns by reference, the
  duplicate's `LeftContextRA`/`RightContextRA` are the *same objects* as
  `left_ctx`/`right_ctx`; the existing cleanup's `if dup_left in
  phon_data.ContextsOS: ... Remove(dup_left)` followed by `if left_ctx in
  phon_data.ContextsOS: ... Remove(left_ctx)` still behaves correctly
  under reference semantics -- the second removal is a harmless no-op
  once the first has already removed the same object -- so no cleanup
  edit was needed or made.)

**(c) `test_2a_iphenvironment_full_surface` (`:205`).** Confirmed per the
briefing: this asserts LCM ground truth (the interface never had the OA
names; it always had the RA names), which remains true independent of
the production fix, so it needed NO inversion. Added only the one-line
pointer comment above the method, citing spec.md C8(c), as instructed.
Reporting this here rather than silently leaving it: **no assertion logic
was touched in this test.**

## T3.6 (C9) -- hands-off confirmation

`git status --porcelain` after all edits:

```
 M CHANGELOG.md
 M flexicon/code/Grammar/EnvironmentOperations.py
 M tests/operations/test_260_environment_resolver_gate.py
 M tests/operations/test_lcm_member_truth_sweep.py
?? .claude/ralph-loop.local.md
```

`.claude/ralph-loop.local.md` is a pre-existing untracked file from before
this task started (present in the session's initial git status snapshot)
and was not created or touched by this work.

Confirmed NOT touched, by the same `git status --porcelain` output above
(absent from the modified-files list) and by direct inspection:
- `flexicon/code/Grammar/compound_rule.py` -- untouched. Its
  `LeftContextOA`/`RightContextOA` reads at `:30,220-221,244-245` are a
  separate, cleared-scope question (C9); `IMoEndoCompound`/
  `IMoExoCompound` carry neither the OA nor the RA form, so a blind
  rename would be wrong in both directions.
- `flexicon/code/Grammar/PhonologicalRuleOperations.py` -- untouched.
  Its `...OA` references at `:639-1145` are on `IPhSegRuleRHS`, where
  those names are correct.
- `tests/operations/test_phon_rules.py` -- untouched.

## Offline regression run

Command (per the standing gate, `-m "not requires_live_project"`, never
bare `pytest`):

```
python -m pytest tests/ -m "not requires_live_project" -q
```

**Result: 1689 passed, 655 deselected, 0 failed** (12 pre-existing,
unrelated warnings: `pytest.mark.integration`/`pytest.mark.live_phase`
registration notices and two `TestDataBuilder`/`TestResultReporter`
collection-class warnings, none touching files this task modified).

**Delta explanation vs. the task briefing's stated baseline ("1876
passed / 0 failed" at `994f2ee`):** that count does not reproduce in
this environment. To isolate whether my edits caused a regression, I
stashed all four modified files (`git stash push -u`) and reran the
identical command against the untouched `994f2ee` tree in this same
environment:

```
994f2ee (stashed, clean):  1689 passed, 654 deselected
with T3 changes (popped):  1689 passed, 655 deselected
```

**Passed count is unchanged (1689 -> 1689); deselected count increases
by exactly 1 (654 -> 655)**, which is the one new test added in T3.5(a)
(`test_left_context_returns_seeded_context_by_reference`) -- it lives in
a module carrying `pytestmark = pytest.mark.requires_live_project`, so
it is correctly excluded from the offline run, not silently dropped.
**Zero regressions; the "1876" figure in tasks.md/spec.md does not match
this checkout/environment's true offline count of 1689 and should be
corrected or re-derived by whoever owns that number** -- I did not
attempt to reconcile it further since the briefing scoped me to compare
deltas, not audit the stated baseline, and doing so live is out of scope
for an "OFFLINE CHECK ONLY" instruction. Confirmed with
`--collect-only` on the two edited test files: 26 tests collected, no
collection errors (T3 gate 5, "no tests collected is a ZERO").

## Verification NOT performed (by design)

Per the briefing's "OFFLINE CHECK ONLY -- do not attempt live runs" and
T3.7 being explicitly out of scope for this handoff (owned by
verification), **no live run was executed against `target_sandbox` or
`sena3_sandbox`.** This includes the new seeded tests added under T3.5.
This is FAIL: unverified for the live-path claim until lex-verification
runs T3.7's live command and produces
`specs/lcm-member-truth-sweep/evidence/live-T3-environment.md`; do not
report this fix as live-verified before that evidence exists.

## Files touched

- `flexicon/code/Grammar/EnvironmentOperations.py`
- `CHANGELOG.md`
- `tests/operations/test_260_environment_resolver_gate.py`
- `tests/operations/test_lcm_member_truth_sweep.py`

No commit was made; the lead commits after review, per the briefing.
