# Live evidence -- US2 rule readers (T017, issue #572)

**Worktree:** `C:/Github/flexicon-572`, branch `fix/572-phonological-rule-readers`.
**Date:** 2026-09-28
**Nature:** `morphboundary` opened read-only throughout the read path. The
only writes are `TEST_572_US2_*` objects on the real Target, removed in a
`finally:` with pool counts asserted back to pre-state.

## Exact commands

```powershell
cd C:\Github\flexicon-572
python -m pytest tests/operations/test_issue572_phonrule_offline.py -q
# 11 passed in 0.69s

$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue572_phonrule_readers_live.py -m requires_live_project -q
# 10 passed in 3.02s

$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue572_phonrule_construct_live.py -m requires_live_project -q
# 4 passed in 2.42s
```

## LIVE GATE

`tests/live_status.json`, read immediately after the live runs:

```json
"run_mode": "live",
```

FieldWorks 9 `SIL.LCModel` loaded; these were live runs, not a mock fallback.

## Pass/fail lines

- `tests/operations/test_issue572_phonrule_offline.py`: **11 passed**
  (GSP `Disabled` key, `DescribeRule(None)`, seven `None`-raises,
  two read-only `SetDisabled`).
- `tests/operations/test_issue572_phonrule_readers_live.py`: **10 passed**
  (environments incl. quickstart §2a table, C10 control, `IsDisabled` vs
  `sc003-before.json`, POS/feature collections, `rhs_index=99`
  `IndexError`, SC-003 serialisation, SC-005, SC-001 print).
- `tests/operations/test_issue572_phonrule_construct_live.py`: **4 passed**
  (features/POSes/disabled round-trip, metathesis silence, no-RHS
  totality, unbounded-iteration rendering).

## SC-003 comparison result

`test_sc003_serialisation_matches_before_capture` re-serialises
`input_contexts`, `output_specs` and `metathesis_parts` for all four
`morphboundary` rules with the same code as `evidence/capture_sc003.py`
and compares against `evidence/sc003-before.json`: **identical**.
Existing members did not shift.

## Constructed rule: pre-state and post-state (re-queried from the LCM)

Pre-state (Target): **0 rules, 0 pooled contexts, 0 rule-feature
possibilities, 0 POS-owned inflection classes**, no `TEST_` rows. Target
holds 18 POSes.

Post-state, re-fetched by GUID via `target_project.Object(guid_str)`
after the write (never asserted off the objects just built):

| Check | Re-queried value |
|---|---|
| `GetRequiredRuleFeatures(...).names` | `['TEST_572_US2_req_feat']` |
| `GetExcludedRuleFeatures(...).names` | `['TEST_572_US2_excl_feat']` |
| required `.items` identity | `IMoInflClass` HVO match |
| excluded `.items` identity | plain-possibility HVO match |
| `item_name` (both features) | non-empty (`TEST_572_US2_infl_class`, `TEST_572_US2_plain_poss`) |
| `GetInputPOSes` | `list`, contains the wired POS HVO |
| `IsDisabled` after `SetDisabled(rule, True)` | `True` (fresh lookup) |
| `GetSyncableProperties(rule)["Disabled"]` | `True` (`is True`) |
| `DescribeRule` (metathesis) | non-empty, `recwarn` empty |
| `DescribeRule` (no RHS) | non-empty |
| `DescribeRule` (unbounded iteration right context) | contains `*`, no `-1` |

Restore: every `TEST_` object removed in `finally:` (rule from
`PhonRulesOS`, feats/poss from `PossibilitiesOS`, infl class from its
POS `InflectionClassesOC`, iteration member/contexts from `ContextsOS`);
counts back to **0/0/0/0/0** (asserted in-test; a separate post-run
probe confirmed no `TEST_` rows on Target).

## Findings outside this feature's scope (not fixed here)

1. **`InflectionFeatureOperations.InflectionClassCreate` is broken on this
   LCM build (pre-existing).** It adds the new `IMoInflClass` to
   `ProdRestrictOA.PossibilitiesOS`, whose `Add(ICmPossibility)` rejects
   it (`TypeError`, reproduced on the pristine `target_sandbox` copy, so
   it is not Target corruption). FieldWorks' own `HCLoaderTests.cs:322`
   shows the real owner: `pos.InflectionClassesOC.Add(inflClass)`. The
   T010 test therefore builds its `TEST_` class under the POS. The
   `InflectionClassGetAll` / `Create` / `Delete` ProdRestrictOA premise
   needs its own issue.
2. **No `IMoInflClass` exists on any of the five installed projects**
   (Target, Sena 3, `morphboundary`, Resembli, Mbugwe Lizzie: 0 each),
   extending the C12 data gap to rule-feature ItemRA targets.
3. **`ItemRA` narrowing (C10, one level deeper).** `ItemRA` is typed
   `ICmObject`, so the proxy exposes no `Name` -- `item_name` on an
   uncast target reads `""` even for a plain `CmPossibility` (measured).
   `RuleFeature.item_name` therefore resolves through `cast_to_concrete`
   first; `item`/`items` stay uncast per the contract (HVO identity
   holds on any proxy).
