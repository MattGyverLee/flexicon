# Issue #886 live verification evidence

## Command

```text
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue886_variant_lexemeform_sync_live.py -m requires_live_project -q
```

## Environment

- Cloud agent VM (no FieldWorks / pythonnet `clr` stack)

## Result

- **FAIL: unverified** — live LCM session not available in this environment.
- Offline ratchet passed (see PR verification section).

## WHAT WAS NOT EXERCISED

- Round-trip `ApplySyncableProperties` for `LexemeForm` on real variant refs in Target/Sena 3.
