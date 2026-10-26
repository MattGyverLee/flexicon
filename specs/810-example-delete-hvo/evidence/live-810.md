# Issue #810 -- live evidence

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue810_example_delete_hvo_live.py -m requires_live_project -q
```

## run_mode

**FAIL: unverified** -- FieldWorks LCM / pythonnet not available in cloud agent environment.

## Expected live proof (Target sandbox)

- Pre: sense has >=2 examples; victim HVO present in ExamplesOS via GetAll.
- Action: `Delete(project.Object(victim.Hvo))` (bare view).
- Post (read back): example count -1; victim HVO absent; keep HVO still present.

## Result

Gate module committed; live run deferred to Windows FieldWorks host.
