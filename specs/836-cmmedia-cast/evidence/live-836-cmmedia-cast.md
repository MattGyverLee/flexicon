# Live verification -- issue #836 (CmMedia cast)

**Date:** 2026-11-02  
**Command:** `FLEXLIBS_REQUIRE_LIVE=1 python3 -m pytest tests/operations/test_issue836_cmmedia_cast_live.py -m requires_live_project -q`  
**Environment:** Cursor cloud agent (Linux, no FieldWorks / mono .NET runtime)

## Result

**FAIL: unverified** -- live LCM unavailable (`RuntimeError: Failed to create a default .NET runtime` on collection).

## Offline gate (machine evidence)

**Command:** `python3 -m pytest tests/operations/test_issue836_cmmedia_cast_offline.py tests/contract/test_lcm_contract.py -m "not requires_liblcm" -q`  
**Result:** 21 passed, 5 skipped

## Expected live read-back (when run on FieldWorks)

1. Create pronunciation media via `AddMediaFile` (returns `ICmMedia`).
2. `bare = project.Object(media_hvo)` -- `MediaFileRA` not on bare view.
3. `concrete = cast_to_concrete(bare)` -- `hasattr(concrete, "MediaFileRA")` True; label matches.
