# Offline verification -- issue #294 POS default features

## Command

```
python3 -m pytest tests/operations/test_issue294_pos_default_features.py tests/operations/test_issue252_pos_feature_sync.py -m "not requires_live_project" -q
```

## Result

Cloud agent (2026-09-23):

```
python3 -m pytest tests/operations/test_issue294_pos_default_features.py -m "not requires_live_project" -q
# 5 passed
```

## Live

**FAIL: unverified** -- no FieldWorks LCM on Linux cloud pod.
