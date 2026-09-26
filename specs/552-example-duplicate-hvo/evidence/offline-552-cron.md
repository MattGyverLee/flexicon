# Issue #552 -- offline evidence (cron)

## /lex-lead ruling

`specs/552-example-duplicate-hvo/rulings.md`

## Command

```
python3 -m pytest tests/operations/test_issue552_example_duplicate_hvo_offline.py -m "not requires_live_project" -q
```

## Result

See pytest output captured at commit time (2 passed).

## Live

**FAIL: unverified** -- cloud agent has no `clr` / FieldWorks; live gate module present at `tests/operations/test_issue552_example_duplicate_hvo_live.py`.
