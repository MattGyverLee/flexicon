# Quickstart: validating issue #572 — phonological rule readers

A runnable guide to proving the feature works end to end. Four scenarios, each
with its exact command and expected outcome. Not a test suite — the test bodies
belong to `tasks.md`; this is the order to run things in and what "working"
looks like.

## Prerequisites

- FieldWorks 9 with a live SIL.LCModel. Present on this machine at
  `C:\Program Files\SIL\FieldWorks 9\`.
- Python 3.14.5 with the project installed (`pythonnet >= 3.0.3, < 3.2`).
- **Data availability, measured across all five installed projects**
  (`evidence/live-instance-probe.json`) — this determines which scenario covers
  which reader:

  | Project | `PhonologicalDataOA` | Rules | `ContextsOS` | Usable for |
  |---|---|---|---|---|
  | `morphboundary` | yes | **4** | **7** | reads (§2) |
  | Target | yes | 0 | 0 | writes (§3) |
  | Sena 3 | yes | 0 | 0 | — |
  | Resembli, Mbugwe Lizzie | yes | 0 | 0 | — |

  `morphboundary` holds `PhSimpleContextSeg`, `PhSimpleContextBdry` (2) and
  `PhSequenceContext` instances. **No project anywhere holds an
  `IPhIterationContext` or an `IPhPhonRuleFeat`** — those two readers can only
  be proven by constructing the data (§3). This is the reason §2 and §3 are
  separate files rather than one.

- Worktree `C:\Github\flexicon-572`, branch `fix/572-phonological-rule-readers`.

---

## 1. The two required invocations

Per Constitution Principle II, both are required for every claim of completion.
Never bare `pytest` and never `pytest --ignore=tests/contract`: neither applies
an `-m` filter, so both would execute all 322 `requires_live_project` tests in
place.

```powershell
cd C:\Github\flexicon-572

# Offline gate
python -m pytest -m "not requires_live_project" -q

# Live gate (FLEXLIBS_REQUIRE_LIVE=1 makes every silent degradation fatal)
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue572_phonrule_readers_live.py -m requires_live_project -q
```

**Expected (offline)**: at least `2575 passed, 1081 deselected` — the baseline
recorded before any change. Any delta is reported with its arithmetic
(Principle IV): state what changed and why, never round to "green".

**Expected (live)**: `run_mode: "live"` in `tests/live_status.json`. A `"mock"`
value proves nothing; check it explicitly:

```powershell
Get-Content tests\live_status.json | Select-String run_mode
```

---

## 2. Read path — `morphboundary` (read-only)

```powershell
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue572_phonrule_readers_live.py -m requires_live_project -q -s
```

Project opened **read-only**. Nothing is written, so this scenario is safe to
re-run indefinitely.

### 2a. The environment, per rule

For each of `morphboundary`'s four rules, assert the left and right context come
back as `PhonologicalContext` wrappers and describe themselves:

| Rule | Expected left | Expected right |
|---|---|---|
| `t deletion` | `None` | `PhSimpleContextSeg` |
| `a insertion` | `PhSimpleContextBdry` | `PhSequenceContext` |
| `n insertion` (×2) | `PhSimpleContextSeg` / `PhSequenceContext` | `PhSimpleContextSeg` / `PhSequenceContext` |

**Working means**: `has_environments` is `True` for all four; the `None` on
`t deletion` is returned, not raised; the `PhSimpleContextBdry` on
`a insertion` reports `is_boundary_context is True` and a non-empty
`boundary_name`; the `PhSequenceContext` reports a non-empty `members` whose
members each have a non-empty `context_name`.

### 2b. The C7 repairs, observable on real objects

These are the checks that fail loudly if the fix regresses:

```python
ctx = ruleOps.GetRightContext(ruleOps.GetAll()[0])   # t deletion
assert ctx is not None
assert ctx.context_name != "SIL.LCModel.DomainImpl.MultiUnicodeAccessor"
assert not ctx.context_name.startswith("SIL.LCModel")   # no .NET type names, ever
assert "SIL.LCModel" not in ctx.context_name
```

- `context_name` returns the context's own text.
- `is_boundary_context` is `True` for the `PhSimpleContextBdry` on
  `a insertion`, and `ContextCollection.boundary_contexts()` returns a
  **non-empty** collection for that rule's contexts.
- `filter(name_contains=...)` matches. Before the fix it could never match
  anything, so a passing match is the proof.

### 2c. The narrowing trap (C10)

```python
rule = ruleOps.GetAll()[0]
raw = project.PhonologicalData.PhonRulesOS[0]
# The point of the test is that these DIFFER before the fix:
assert hasattr(raw, "RightHandSidesOS") is False        # the pythonnet proxy
assert rule.has_environments is True                    # the wrapper, cast
```

**Working means**: the wrapper reports what the raw proxy cannot see. This is
the assertion that makes C10 mechanical rather than remembered.

### 2d. `Disabled` and `DescribeRule`

```python
assert ruleOps.IsDisabled(ruleOps.GetAll()[1]) is True   # a insertion is off
text = ruleOps.DescribeRule(ruleOps.GetAll()[0])
assert text and "SIL.LCModel" not in text
```

**Working means**: `DescribeRule` returns a non-empty string containing no .NET
type name and no `object at 0x...` repr, for **all four** rules. It must not
raise for any of them.

### 2e. SC-003 — no regression in the existing members

Capture `input_contexts`, `output_specs`, and `metathesis_parts` for all four
rules **before** and **after** the change and assert the two runs are identical.
Same objects, same order, same values. A reader added next to an existing one
that shifts is a regression, not an addition.

---

## 3. Write path — Target (construct, read back, restore)

The iteration-context and rule-feature readers have no pre-existing data
anywhere on this machine (measured, §Prerequisites), so this scenario builds
it.

```powershell
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue572_construct_live.py -m requires_live_project -q
```

Uses the `target_project` fixture (`tests/flex_plugin.py:1375`) — write-enabled
on the real Target, **not** a sandbox. Object names prefixed `TEST_`, and
**restored in a `finally:`**. If the restore cannot be guaranteed, use
`target_sandbox` (`:1284`) instead, which is a tempdir copy and cannot leak.

### Working sequence

1. Create an `IPhIterationContext` with `Minimum=1`, `Maximum=-1` (unbounded),
   `MemberRA` pointing at a context in the pool. Register it in
   `PhonologicalDataOA.ContextsOS`.
2. Re-query it **through the new reader** — not by asserting on the value just
   passed in:

   ```python
   # after the write, re-read from the LCM:
   found = [c for c in project.PhonologicalData.ContextsOS
            if c.ClassName == "PhIterationContext"]
   assert found, "the iteration context did not survive the write"
   wrapped = PhonologicalContext(found[0])
   assert wrapped.is_iteration_context
   assert wrapped.min_count == 1
   assert wrapped.max_count is None       # -1 becomes None; C5
   assert wrapped.member is not None
   ```

3. Create a `CmPossibility` in `PhonologicalDataOA.PhonRuleFeatsOA.PossibilitiesOS`
   with `ItemRA` set to an `IMoInflClass`, and a `PhRegularRule` referencing it
   via `ReqRuleFeatsRC`.
4. Read back: `GetRequiredRuleFeatures(rule)` returns a non-empty collection;
   `.names` is non-empty; `[f.item for f in coll]` yields the `IMoInflClass`.
5. Also construct a **bounded** iteration context (`Maximum=3`) and assert
   `max_count == 3` — so the `None` case is proven by contrast, not alone.
6. `finally:` delete both, and assert the pool is back to its pre-test length.

### Evidence

Write `specs/572-phonological-rule-readers/evidence/live-T2-construct.md` with
the exact command, `run_mode`, the **pre-state and post-state re-queried from
the LCM**, and the pass/fail line. Asserting on the value just passed in proves
nothing.

---

## 4. The offline gate, and the docs

```powershell
python -m pytest -m "not requires_live_project" -q
Get-Content tests\live_status.json | Select-String run_mode
```

**Also run, all four offline:**

```powershell
# 1. The PhBoundaryContext ratchet (Principle III control) -- must pass at zero
python -m pytest tests/test_issue572_boundary_context_ratchet.py -q

# 2. The GSP member ratchet, to confirm the "Disabled" key did not disturb it
python -m pytest tests/test_syncable_properties_member_ratchet.py -q

# 3. The published-surface ratchets, to confirm the baseline edit
python -m pytest tests/test_issue339_public_import_surface.py tests/test_operations_baseline.py -q

# 4. Proof the retired name is gone from docs and code
rg -c "PhBoundaryContext" flexicon\docs 2>&1   # expect no match
```

**Working means**: the new methods appear in the surface baseline (regenerated
in the same commit, per Quality Gate 5); `PhBoundaryContext` has **zero**
occurrences in `flexicon/code/` and `docs/`; and `docs/USAGE_CONTEXTS.md` no
longer documents `boundary_type` or teaches `boundary_contexts()` as a filter on
a class that does not exist.

Report the offline counts in full, including failures, against the recorded
baseline of `2575 passed, 1081 deselected`.

---

## 5. Definition of done

| # | Check | Command | Expected |
|---|---|---|---|
| 1 | Offline gate | §1 | ≥ `2575 passed`, delta explained |
| 2 | Live gate, read path | §2 | `run_mode: "live"`, all pass |
| 3 | Live gate, write path | §3 | `run_mode: "live"`, re-queried post-state recorded |
| 4 | SC-004 `context_name` | §2b | real text, never a .NET type name |
| 5 | SC-005 `DescribeRule` | §2d | non-empty, no type names, never raises |
| 6 | SC-003 no regression | §2e | identical before/after |
| 7 | SC-001 the issue's goal | — | a script prints each rule with contexts and features, no `IPh*` import, no `ClassName`, no cast |
| 8 | SC-002 sweep to zero | §4.1 | zero occurrences |
| 9 | C9 sync key | §4.2 | ratchet undisturbed, key present |
| 10 | Surface baseline | §4.3 | regenerated, additive only |
| 11 | Docs match code | §4.4 | `USAGE_CONTEXTS.md` updated in the same commit |

**The SC-001 acceptance test** is the one that matters most, because it is the
issue's own evidence: the FlexToolsMCP `phonological-rules` recipe
(MCPlayground `flex-parse-fixup/lib/phon_rules.py`, 44 lines) uses no flexicon
today — 13 casts across 10 `IPh*` types plus `ClassName` dispatch. If a script
can print every rule with its input contexts, output, environment, required and
excluded features, input POSes and disabled state using flexicon alone, the
issue is closed. If it still needs a cast to say what a context contains, it is
not.
