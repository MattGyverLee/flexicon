# Live LCM verification — B2 batch 10/11 (Grammar)

Covers the 59 Grammar mutation sites bracketed per decision **D5**
(per-site `with self._TransactionCM(...)`, all 295).

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_grammar_brackets_live.py -m requires_live_project -q
```

Result: **16 passed**, 67 warnings, 12.07s.

## run_mode

`tests/live_status.json` -> `"run_mode": "live"` (run_timestamp
`2026-08-15T21:50:46Z`). Not `"mock"` — the writes reached a real LCM cache.

The library under test is the working tree: `pyflexicon` is installed
editable against `D:\Github\_Projects\_LEX\flexicon`, so `flexicon` resolves
to this checkout from any cwd. Verified before the run:

```
flexicon.__file__            -> D:\Github\_Projects\_LEX\flexicon\flexicon\__init__.py
transaction.py _transaction_depth      hits: 0
transaction.py UndoableUnitOfWorkHelper hits: 10
```

(Previously the MCP/site-packages copy still carried `_transaction_depth`
and zero `UndoableUnitOfWorkHelper` — i.e. pre-B1 code. See the caveat at
the bottom.)

## Fixture

`target_sandbox` — write-enabled on a fresh tempdir copy of the Target
`.fwbackup`. Nothing can leak into the real Target. All created objects use
the `TEST_` prefix and are deleted in a `finally:`.

`TestGrammarFixtureReachesLiveLCM::test_sandbox_opens_write_enabled` asserts
`writeEnabled is True` and that a real underlying LCM cache is present, so a
mock fixture would fail the run rather than pass it silently.

## Pre-state / post-state, read back from the LCM

Every assertion **re-queries through the Operations getter** after the write.
Asserting on the value passed in would prove nothing.

| Operation | Pre-state | Write | Post-state (re-read) |
|---|---|---|---|
| `POSOperations.SetName` | `TEST_pos_name` | `SetName(-, "TEST_renamed")` | `GetName` -> `TEST_renamed` |
| `POSOperations.SetAbbreviation` | `TEST_pa` | `SetAbbreviation(-, "TEST_ab")` | `GetAbbreviation` -> `TEST_ab` |
| `POSOperations.Delete` | count `N+1` | `Delete(created)` | `GetAll()` -> `N` |
| `PhonemeOperations.SetRepresentation` | `TEST_p` | `SetRepresentation(-, "TEST_pp")` | `GetRepresentation` -> `TEST_pp` |
| `PhonemeOperations.SetDescription` | `""` | `SetDescription(-, "voiceless bilabial stop")` | `GetDescription` -> `voiceless bilabial stop` |
| `PhonemeOperations.Delete` | count `N+1` | `Delete(created)` | `GetAll()` -> `N` |
| `NaturalClassOperations.SetName` | `TEST_nc` | `SetName(-, "TEST_nc_renamed")` | `GetName` -> `TEST_nc_renamed` |
| `NaturalClassOperations.AddPhoneme` | `GetPhonemes` len `0` | `AddPhoneme(nc, p)` | `GetPhonemes` len `1` |
| `NaturalClassOperations.RemovePhoneme` | `GetPhonemes` len `1` | `RemovePhoneme(nc, p)` | `GetPhonemes` len `0` |
| `StratumOperations.Delete` | count `N+1` | `Delete(created)` | `GetAll()` -> `N` |
| `EnvironmentOperations.SetName` | `TEST_env` | `SetName(-, "TEST_env_renamed")` | `GetName` -> `TEST_env_renamed` |
| `EnvironmentOperations.Delete` | count `N+1` | `Delete(created)` | `GetAll()` -> `N` |
| `PhonologicalRuleOperations.SetName` | `TEST_rule` | `SetName(-, "TEST_rule_renamed")` | `GetName` -> `TEST_rule_renamed` |
| `PhonologicalRuleOperations.SetDescription` | `""` | `SetDescription(-, "intervocalic voicing")` | `GetDescription` -> `intervocalic voicing` |
| `PhonologicalRuleOperations.Delete` | count `N+1` | `Delete(created)` | `GetAll()` -> `N` |

## Validation-stays-outside-the-bracket

The property D5's per-site shape exists to preserve. A dispatch-layer bracket
would pull these validators inside the UoW, so every rejected input would
open a named undo task, raise, and (under B1's `UndoableUnitOfWorkHelper`)
fire a real `Rollback(0)`.

| Guard | Input | Expected | Observed |
|---|---|---|---|
| `POSOperations.SetName` empty-name | `"   "` | `FP_ParameterError`, name unchanged | raised; `GetName` still `TEST_pos_guard` |
| `PhonemeOperations.SetRepresentation` empty | `"  "` | `FP_ParameterError`, representation unchanged | raised; `GetRepresentation` still `TEST_p_guard` |

## live_status.json per-class outcome

All `pass`, `last_verified: 2026-08-16`:

- `POSOperations` — modify, delete
- `PhonemeOperations` — modify, delete
- `NaturalClassOperations` — modify
- `StratumOperations` — delete
- `EnvironmentOperations` — modify, delete
- `PhonologicalRuleOperations` — modify, delete

## Offline gate (no regressions)

Same invocation before and after the batch, compared by stashing the batch:

```
python -m pytest tests/ -m "not requires_live_project" -q
```

| | failed | passed | deselected |
|---|---|---|---|
| pre-batch | 35 | 1201 | 325 |
| post-batch | 35 | 1201 | 325 |

Byte-identical — zero regressions. The 35 are pre-existing and unrelated
(#240 rename path: tests still referencing `flexlibs2\...` paths; sync
engine).

Grammar-domain selection (`-k "grammar or phon or pos or inflection or
stratum or natural or morphrule or environment or gramcat"`): 8 failed /
150 passed both before and after — identical, same #240 rename-path cause.

Ratchet guard + B1t action-handler-double suite: **34 passed**.

## Ratchet

Scanner total **143 -> 84**; `grep -c "Grammar/"` on the scanner output
= **0**. Baseline diff is 547 deletions and 1 changed `total` — removals
only, no new entries.

## Caveat: what this run does NOT cover

`undoable=True` is not yet the default (task **DEF**, gated on Checkpoint 2
and flagged `needs_human`). This run executed under `undoable=False`, where
`OpenProject` emits the one-shot A2d warning and the atomicity unit is the
session, not the operation. So this verifies that **every bracketed site
still performs its mutation correctly and that validators sit outside the
bracket** — it does not exercise `Rollback(0)` on those brackets. The
end-to-end persistence proof under `undoable=True` is task **B2t**, which
remains a `needs_human` gate.

Prior to this session the FlexTools MCP loaded `flexicon` from a copied
site-packages install carrying pre-B1 code, so any verification routed
through `flextools_run_module` would have proved nothing about this branch.
Fixed by installing editable; pytest-based verification (this run and the
batch 1-9 runs) was never affected, because running from the repo root puts
the checkout first on `sys.path`.

**PASS** — live verification of B2 batch 10/11 (Grammar) complete.
