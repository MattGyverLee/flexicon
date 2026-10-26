# Issue #732 live evidence

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue732_example_donotpublish_hvo_live.py -m requires_live_project -q
```

## run_mode

`mock` — FieldWorks LCM (`clr`) not available in this cloud agent environment.

## Result

**FAIL: unverified** — live write-path test could not execute; offline ratchet passed.

## Offline gate

```
python -m pytest tests/operations/test_issue732_example_donotpublish_hvo_offline.py -m "not requires_live_project" -q
```

PASS (3/3).
