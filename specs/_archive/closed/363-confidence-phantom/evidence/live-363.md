# Issue #363 -- live evidence

**Required command (Windows / FieldWorks host):**

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue363_confidence_live.py -m requires_live_project -q
```

**Cloud agent status:** FAIL: unverified -- no .NET / FieldWorks on this pod.

**Pre-state:** `GetAnalysesWithConfidence` scanned `IWfiAnalysisRepository` with
`hasattr(..., "ConfidenceRA")` (always false); `GetGlossesWithConfidence` same on
`IWfiGlossRepository`.

**Expected post-state (live):** Matching notebook records returned with
`record.ConfidenceRA.Hvo == level.Hvo`; `GetGlossesWithConfidence` raises
`FP_ParameterError`.

**Pass/fail:** FAIL: unverified on cloud agent
