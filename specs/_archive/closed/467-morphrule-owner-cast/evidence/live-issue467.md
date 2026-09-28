# Issue #467 live verification

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue467_morphrule_owner_cast_live.py -m requires_live_project -q
```

## run_mode

`mock` (session refused live: `No module named 'clr'` on cloud agent)

## Result

**FAIL: unverified** -- write-path change; live LCM read-back not performed in this environment.

## Expected live behaviour (when run on FieldWorks host)

1. Create affix template on Target sandbox POS; read back via `IPartOfSpeech.AffixTemplatesOS`.
2. `Delete(template)`; re-query shows template HVO absent.
3. `Duplicate(source)`; re-query shows count +1 and new HVO present.
