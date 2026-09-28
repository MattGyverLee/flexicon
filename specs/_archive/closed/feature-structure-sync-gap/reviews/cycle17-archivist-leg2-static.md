# Cycle-17 Checkpoint 5 gate -- LEG 2 static spec (task B)

## Step 1: the 7-row hasattr table (AST-confirmed, grep cross-checked)

| Line | Enclosing fn | arg0 | arg1 |
|---|---|---|---|
| 358 | Delete | `owner` | `"LexemeFormOA"` |
| 368 | Delete | `owner` | `"AlternateFormsOS"` |
| 460 | Duplicate | `parent` | `"LexemeFormOA"` |
| 466 | Duplicate | `parent` | `"AlternateFormsOS"` |
| 570 | GetSyncableProperties | `allomorph` | `"Form"` |
| 579 | GetSyncableProperties | `allomorph` | `"IsAbstract"` |
| 584 | GetSyncableProperties | `allomorph` | `"MorphTypeRA"` |

**G2b: HELD.** Total is 7, not 3: 4 owner/parent probes (Delete x2, Duplicate x2) + 3 subtype gates (all in GetSyncableProperties, all first-arg `allomorph`). No race: `evidence/live-cycle17-gate-predictions.md` was already committed by task A with the identical 7-row breakdown.

## Step 2: what the shipped AST test pins

`test_get_syncable_properties_hasattr_calls_are_allowlisted` (:171) asserts every `hasattr` name found in `GetSyncableProperties`'s body is `in {"Form","IsAbstract","MorphTypeRA"}` -- this DOES pin "only these three, only here" for that one function. `test_zero_hasattr_in_apply_and_feature_helpers_and_resolver` (:187) asserts zero hasattr in `ApplySyncableProperties`, `__CaptureFeatureStrucProp`, `__ApplyFeatureStrucProp`, `__GetAllomorphObject` only.

STATUS.md Ruling 3's prose ("allowlists slot= literals... merely checks hasattr's second argument is a string literal") is **imprecise as literally stated** -- that description matches a *different* assertion (`test_no_non_none_slot_literal_anywhere_in_feature_struct_calls`, :267) and the `_hasattr_second_args` helper's internal literal-arg precondition, not the allowlist test's actual gate. But Ruling 3's bottom line -- "does NOT pin these three are the only gates" -- is **CONFIRMED**, for a narrower reason: coverage is enumerated by function name (5 named functions), not by identity of the resolved object. GetForm, SetForm, SetFormAudio, GetFormAudio, GetMorphType, SetMorphType, GetPhoneEnv, AddPhoneEnv, RemovePhoneEnv all call `__GetAllomorphObject` (13 call sites total, matching the docstring's "11 other call sites" outside GetSyncableProperties/ApplySyncableProperties) and are covered by NEITHER test. A hasattr probe added to any of these 9 escapes silently.

## Step 3: new test specification (LEG 2)

Scope by **first-argument identity**, module-wide, not by total count (7, not 3) or line number:
1. `ast.walk` the WHOLE module (not per-method `inspect.getsource`).
2. Collect every `Call` where `func` is `Name("hasattr")` and `args[0]` is a bare `Name` whose `.id == "allomorph"`.
3. Assert `len(results) == 3`.
4. Assert the `{(enclosing_fn, arg1_literal)}` set equals exactly `{("GetSyncableProperties","Form"), ("GetSyncableProperties","IsAbstract"), ("GetSyncableProperties","MorphTypeRA")}`.

Discriminating-function boundary (justified, not assumed): every function assigning via `self.__GetAllomorphObject(...)` and then touching the result -- Delete(347)->`allomorph`, Duplicate(424)->`source`, GetSyncableProperties(564)->`allomorph`, ApplySyncableProperties(654)->`allomorph`, GetForm/SetForm/SetFormAudio/GetFormAudio/GetMorphType/SetMorphType/GetPhoneEnv/AddPhoneEnv/RemovePhoneEnv, plus `__CaptureFeatureStrucProp`(680)/`__ApplyFeatureStrucProp`(716) which receive `allomorph` as a parameter. Checked directly: none of the 9 uncovered public methods, nor the two helpers, contain any hasattr today (confirmed by the 7-row table -- all 7 are accounted for in Delete/Duplicate/GetSyncableProperties). The module-wide scan by literal name `allomorph` is a single test that supersedes needing to enumerate all 15 functions by name, because Delete/Duplicate's probes target `owner`/`parent`, not `allomorph` -- so they are naturally excluded, remaining free to change. Residual limitation to disclose in the test's docstring: this scoping is defeated if a future edit renames the resolved-object local variable away from `allomorph` in the same statement that adds the new hasattr call -- not a "silent" one-line addition, so acceptable per the stated threat model.

**Killing mutation:** in a disposable worktree, add a fourth line inside `GetSyncableProperties` (or, to prove the module-wide claim, inside `GetForm` instead): `if hasattr(allomorph, "MsEnvFeaturesOA"): pass`. The new test must go RED; today's two shipped tests would NOT catch the `GetForm` placement (neither enumerates that function), which is exactly the gap this test closes.

## Step 4: LEG 2 live-probe recommendation

Use the `ILexEntry` created by the test's own setup (`_make_entry(sandbox, tag)` returns `sandbox.LexEntry.Create(...)`; `entry.Hvo` is free -- no extra object creation). `entry.ClassName == "LexEntry"`, neither allomorph subtype, so `__GetAllomorphObject(entry.Hvo)` takes the `getattr(obj,"ClassName",None)` miss branch and returns `obj` unchanged. Feed that returned object into `GetSyncableProperties`: `hasattr(entry,"Form")`/`"IsAbstract"`/`"MorphTypeRA"` are all False (safe, no raise), and the risk line at :594 (`allomorph.ClassName == "MoAffixAllomorph"`, unguarded direct access, not `getattr`) is SAFE here because `ILexEntry` is still an `ICmObject` and always exposes `.ClassName` -- it evaluates to `"LexEntry" != "MoAffixAllomorph"` and falls through cleanly. Risk would only materialize for a non-ICmObject input (not applicable to any live Target candidate); flag this so group 2 doesn't need to re-derive it, but no live raise is expected on this path.
