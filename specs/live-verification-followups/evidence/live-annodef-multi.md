# Live evidence -- AnnotationDefOperations phantom members (HANDOFF item 2)

**Date:** 2026-09-23
**Project:** `target_sandbox` (tempdir copy of the Target `.fwbackup`)
**Change:** `flexicon/code/System/AnnotationDefOperations.py`
(`GetMultiple`, `SetMultiple`, `GetCopyCutPasteAllowed`, `GetInstanceOf`,
`Duplicate`, `_DuplicateSubDefInto`)

## Reflection (live, `ICmAnnotationDefn` plus inherited interfaces)

| Name probed by old code | Present? | Real field |
|---|---|---|
| `AllowsMultiple` | no | `Multi` |
| `CopyCutPasteAllowed` | no | `CopyCutPastable` |
| `InstanceOf` | no | `InstanceOfSignature` |
| `AnnotationType` | no | none (left as-is, see Category 8) |

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_annodef_phantom_members_live.py tests/operations/test_352_annodef_live.py -m requires_live_project -q
```

`tests/live_status.json` -> `"run_mode": "live"`

## Pre / post state (read back via `ICmAnnotationDefn(project.Object(guid))`)

| Step | LCM `Multi` | `GetMultiple()` |
|---|---|---|
| fresh `Create(...)` | `False` | `False` (old code: `True`) |
| `SetMultiple(d, True)` | `True` (old code: stayed `False`) | `True` |
| `SetMultiple(d, False)` | `False` | `False` |

`Duplicate` after flipping `Multi`, `CopyCutPastable` and `UserCanCreate`
away from their defaults: the re-read duplicate carries all three flipped
values, and the same `InstanceOfSignature` / `AllowsInstanceOf` as the source.

`GetCopyCutPasteAllowed` tracks raw `CopyCutPastable = True` and `False`.

## Result

- Old code (fix stashed): `4 failed in 3.17s` -- the new tests catch the bug
- New code: `[PASS] 7 passed in 3.78s`
