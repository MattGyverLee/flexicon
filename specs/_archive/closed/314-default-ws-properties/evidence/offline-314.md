# Issue #314 -- offline evidence

## Commands

```
python3 -m pytest -m "not requires_live_project" tests/test_issue314_default_ws_properties.py -q
```

## Result

PASS (3/3) on cloud agent (no FieldWorks / no libmono).

## Live verification

**FAIL: unverified** -- this environment has no .NET/FieldWorks runtime.
Live parity is covered by new assertions in
`tests/test_flexproject_discoverability.py::test_default_ws_properties_match_handle_helpers`
when `FLEXLIBS_REQUIRE_LIVE=1` and a candidate project is available.
