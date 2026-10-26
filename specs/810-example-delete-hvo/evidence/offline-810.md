# Issue #810 -- offline evidence

## Command

```
python -m pytest tests/operations/test_issue810_example_delete_hvo_offline.py -m "not requires_live_project" -q
```

## run_mode

N/A (offline ratchet; no FLEx session)

## Result

PASS (2/2) -- cloud agent 2026-10-26

## Notes

Source ratchet asserts Delete resolves ExamplesOS membership by HVO and does not call `ExamplesOS.Remove(example)` with the caller handle.
