# Live evidence -- #327 CompoundRule surfaces (HANDOFF item 3b)

**Date:** 2026-09-23
**Supersedes:** the "FAIL: unverified" live line in `rulings.md` / `offline-327.md`

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue327_compound_rule_live.py -m requires_live_project -q
```

`tests/live_status.json` -> `"run_mode": "live"`

## What was checked (wrapper vs raw LCM, re-queried by GUID)

| Case | Project | Assertion |
|---|---|---|
| 4 x `MoExoCompound` | `sena3_sandbox` | `to_msa` is the same object as `ToMsaOA` (at least one populated); `head_last` / `overriding_msa` are None; `left_context` / `right_context` / `contexts` absent |
| `MoEndoCompound` (TEST_ rule created; no sanctioned project has one) | `target_sandbox` | after raw `HeadLast = True` and `OverridingMsaOA = <new IMoStemMsa>`, `head_last is True`, `overriding_msa` is the same object as `OverridingMsaOA`, `to_msa` is None, phantom context props absent |

## Result

`[PASS] 2 passed in 3.80s`

## New finding (not in #389's scope)

Live instances across every local project with compound rules (Sena 3,
Tlachichilco Tepehua, Yi Sichuan, blx-flex, Vanaw, ...) show **no
`LeftHeadDep` / `RightHeadDep`** on either type. The real members are:

- `IMoEndoCompound`: `HeadLast`, `LeftMsaOA`, `RightMsaOA`, `LinkerOA`, `OverridingMsaOA`
- `IMoExoCompound`: `LeftMsaOA`, `RightMsaOA`, `LinkerOA`, `ToMsaOA`

So `CompoundRule.left_head_dep`, `right_head_dep` and `head_dependency` are
always None, `CompoundRuleCollection.filter(head_dependency=...)` always
returns nothing, and `docs/USAGE_COMPOUND_RULES.md` documents the phantoms.
The wrapper also exposes none of `LeftMsaOA` / `RightMsaOA` / `LinkerOA`.
This needs an API redesign, so it is left for a separate issue.
