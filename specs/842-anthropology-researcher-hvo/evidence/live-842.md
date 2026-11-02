# Live evidence: issue #842 (Anthropology ResearchersRC HVO)

Command:

    FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue842_anthropology_researcher_hvo_live.py -m requires_live_project -q

run_mode (tests/live_status.json): **mock** (cloud agent -- no FieldWorks / `clr`)

Result: **FAIL: unverified** -- live gate not executed in this environment.

## WHAT WAS NOT EXERCISED

- Create anthropology item, link researcher, re-fetch person via `Object(hvo)`, `RemoveResearcher`, re-query `GetResearchers` on Target sandbox.
