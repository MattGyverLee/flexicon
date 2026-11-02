# Live evidence: issue #826 (syncable scalar/text fields)

Command (PowerShell equivalent: `$env:FLEXLIBS_REQUIRE_LIVE="1"`):

    FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue826_syncable_scalar_fields_live.py -m requires_live_project -q

run_mode (tests/live_status.json): live
Result: 5 passed (fixture: target_sandbox, tempdir copy of Target .fwbackup).

Pre/post values (read back from the LCM via get_String / ITsString after
ApplySyncableProperties on a second, freshly created object; source keyed
under fake WS "zz-src" and mapped with ws_map={"zz-src": <analysis ws id>}):

| Class | Field | Target pre | Target post (read back) |
|-------|-------|-----------|-------------------------|
| LexSense | AnthroNote | empty | TEST_AnthroNote |
| LexSense | UsageNote | empty | TEST_UsageNote |
| LexEntry | SummaryDefinition | empty | TEST_SummaryDefinition |
| LexEntry | Restrictions | empty | TEST_Restrictions |
| Etymology | Note | empty | TEST_Note |
| Etymology | PrecComment | empty | TEST_PrecComment |
| Pronunciation | CVPattern | unset | CVC |
| Pronunciation | Tone | unset | HL |
| Text | Source (GetSource/SetSource + sync) | "" | TEST_src |

PASS
