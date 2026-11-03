# Issue #884 live verification evidence

## Command

```text
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue884_variant_ref_rs_sync_live.py -m requires_live_project -q
```

## Environment

- Cloud agent VM (no FieldWorks / pythonnet `clr` stack)

## Result

- **FAIL: unverified** — live LCM session not available in this environment.
- Offline ratchet passed (see PR verification section).

## WHAT WAS NOT EXERCISED

- Round-trip `ApplySyncableProperties` on real `VariantEntryTypesRS` / `ComponentLexemesRS` in Target/Sena 3.
