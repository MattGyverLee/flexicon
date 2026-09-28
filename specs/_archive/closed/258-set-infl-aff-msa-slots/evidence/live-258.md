# Issue #258 -- live verification

**Status:** FAIL: unverified on this agent (Linux cloud pod; no FieldWorks / libmono LCM runtime).

**Planned command (Windows / FLEx host):**

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue258_set_infl_aff_msa_slots_live.py -m requires_live_project -q
```

**Expected evidence when run:** `tests/live_status.json` with `"run_mode": "live"`; pre-state
`SlotsRC` HVO set `{slot_a}` after `CreateInflAff`; post-replace `{slot_b}`; post-append
`{slot_a, slot_b}` read back via fresh `project.Object(msa_hvo)`.
