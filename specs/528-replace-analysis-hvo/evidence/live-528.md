# Issue #528 live evidence

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest \
  tests/operations/test_issue528_replace_analysis_hvo_live.py \
  -m requires_live_project -q
```

## run_mode

**FAIL: unverified** -- cloud agent environment has no `clr` / FieldWorks; live gate not executed here.

## Expected behaviour (when run on a FieldWorks host)

1. Create segment with one wordform token in `AnalysesRS`.
2. Call `ReplaceAnalysis(seg, project.Object(old_hvo), new_wf)`.
3. Read back via `GetAnalyses`: new token HVO present, old HVO absent.
