# Live evidence: issue 630 (affix MSA exception features)

Command (PowerShell equivalent: `$env:FLEXLIBS_REQUIRE_LIVE = "1"` first):

    FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue630_affix_msa_exception_features_live.py tests/operations/test_574_msa_exception_features.py -m requires_live_project -q

run_mode (tests/live_status.json): "live"
Fixture: sena3_sandbox (tempdir copy of the Sena 3 backup); entries/senses/MSAs and
TEST_630_ exception features created via ExceptionFeatureCreate (#631).

Every state below is read back by re-fetching the MSA with `project.Object(hvo)`,
casting to the concrete interface, and reading the LCM field (not the wrapper getter).

| Case | Field | Pre | After add | After 2nd add | After remove |
|---|---|---|---|---|---|
| MoInflAffMsa, side=from | FromProdRestrictRC | [] | [feat] | [feat] | [] |
| MoInflAffMsa, side=to | (none) | raises FP_ParameterError on Get/Add/Remove; FromProdRestrictRC stays [] |||
| MoDerivAffMsa add from | From / To | [] / [] | [f_from] / [] | [f_from] / [f_to] (after to-add) | |
| MoDerivAffMsa add to | From / To | | [f_from] / [f_to] | unchanged on re-add | remove to: [f_from] / []; remove from: [] / [] |
| MoDerivAffMsa side="both" | | raises FP_ParameterError |||
| MoStemMsa (regression) | ProdRestrictRC | [] | [feat] | [feat] (side="to" ignored) | [] |

Result: PASS -- 5 passed (live file), offline 574 file deselected by the marker filter
(39 tests pass in the offline run). Full offline run: 3710 passed.

## Cycle 3 re-run (review findings)

Command:

    FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue630_affix_msa_exception_features_live.py tests/operations/test_issue631_inflection_class_store_live.py -m requires_live_project -q

run_mode (tests/live_status.json): "live". Fixture: sena3_sandbox. All values re-queried from the LCM.

| Case | Pre | Post (read back) |
|---|---|---|
| MoInflAffMsa side="to": Get | FromProdRestrictRC=[feat] | Get returns [] + warning; Add/Remove raise; FromProdRestrictRC still [feat] |
| MoUnclassifiedAffixMsa Get | no field | returns [] + warning; Add raises |
| ExceptionFeatureCreate with MorphologicalDataOA.ProdRestrictOA set to None | ProdRestrictOA is None | ProdRestrictOA not None, PossibilitiesOS == [new feature], name read back |
| ChangeAffixVariant infl -> deriv | infl From=[feat] | new deriv From=[feat], To=[]; no "FromProdRestrictRC" lost warning |
| ChangeAffixVariant deriv -> infl | deriv From=[f_from], To=[f_to] | new infl From=[f_from]; lost-warning names ToProdRestrictRC only |
| ChangeAffixVariant infl -> unclassified | infl From=[feat] | new MoUnclassifiedAffixMsa; lost-warning names FromProdRestrictRC |

Result: PASS -- 15 passed (both live files, 630 + 631). Offline run: 3719 passed, 1174 deselected.
