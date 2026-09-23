# Issue #281 -- lcm_casting logger (offline evidence)

## Lex-lead ruling

See `specs/281-lcm-casting-logger/rulings.md`.

## Commands

```
python3 -m pytest tests/test_issue281_lcm_casting_logger.py -m "not requires_live_project" -q
```

## Result (cloud agent)

```
python3 -m pytest tests/test_issue281_lcm_casting_logger.py -m "not requires_live_project" -q
3 passed
```

**Pass/fail:** PASS (offline). Live LCM not required.

## Pre/post behaviour

| Check | Before | After |
|-------|--------|-------|
| `import logging` in docstring | yes (dead code) | removed |
| `logger = logging.getLogger(__name__)` | absent | present |
| Unregistered `ClassName` in `cast_to_concrete` | silent no-op | `logger.debug` |

**Live LCM:** not required.
