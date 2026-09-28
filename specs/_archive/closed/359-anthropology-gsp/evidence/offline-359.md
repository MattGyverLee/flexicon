# Offline verification -- issue #359 anthropology GSP

## Command

```
python -m pytest tests/operations/test_anthropology_get_syncable_properties.py tests/operations/test_issue359_anthropology_gsp_offline.py tests/test_syncable_properties_member_ratchet.py -m "not requires_live_project" -q
```

## Result

**PASS** (2026-09-23, cloud agent worktree `fix/359-anthropology-gsp`):

```
python3 -m pytest tests/operations/test_anthropology_get_syncable_properties.py tests/operations/test_issue359_anthropology_gsp_offline.py tests/test_syncable_properties_member_ratchet.py -m "not requires_live_project" -q
# 77 passed
```
