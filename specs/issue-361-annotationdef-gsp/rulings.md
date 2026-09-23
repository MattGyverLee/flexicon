# Issue #361 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/361-annotationdef-gsp from origin/main

## RULING (binding)

`ICmAnnotationDefn` (liblcm baseline 2026-09-08) has **no** `AnnotationType`,
`InstanceOf`, or `AllowsMultiple` members. Sync was guarded with `hasattr` on
phantom names, so keys were permanently empty.

**Correct behaviour (GetSyncableProperties only -- issue scope):**

1. **Drop `AnnotationType`** from the sync payload. There is no declared LCM
   field on `ICmAnnotationDefn`; do not emit a fabricated value.
2. **`InstanceOf`** -- emit `int(anno_def.InstanceOfSignature)` (baseline
   `Int32`). Also emit **`AllowsInstanceOf`** as `bool(anno_def.AllowsInstanceOf)`.
3. **`AllowsMultiple`** -- read **`Multi`** (`Boolean` on baseline); keep the
   sync key name `AllowsMultiple` for existing consumers.

**Out of scope:** `GetAnnotationType`, `GetInstanceOf`, `GetMultiple` /
`SetMultiple`, and `Duplicate` copy blocks (separate issues / #352 family).

## Verification plan

- Offline: source ratchet test on `GetSyncableProperties` body.
- Live: extend `tests/operations/test_352_annodef_live.py` when
  `FLEXLIBS_REQUIRE_LIVE=1` (blocked on Linux cloud agent if no LCM).
