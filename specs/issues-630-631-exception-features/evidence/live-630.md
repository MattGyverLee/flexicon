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
