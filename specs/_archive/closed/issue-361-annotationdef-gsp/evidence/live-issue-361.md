# Live verification -- issue #361 AnnotationDef GetSyncableProperties

## Command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_352_annodef_live.py -m requires_live_project -q
```

## run_mode

**FAIL: unverified** -- Cloud Agent Linux pod has no FieldWorks LCM runtime.

Offline gate:

```
python -m pytest tests/operations/test_issue361_annotationdef_gsp_offline.py tests/operations/test_352_annodef_live.py -m "not requires_live_project" -q
```

## Pre-state (issue #361)

`GetSyncableProperties` guarded `AnnotationType`, `InstanceOf`, and
`AllowsMultiple` with `hasattr`; all three guards false on `ICmAnnotationDefn`,
so sync keys were empty.

## Post-state (expected after fix)

Payload includes `InstanceOf`, `AllowsInstanceOf`, `UserCanCreate`,
`AllowsMultiple` (from `Multi`); no `AnnotationType` key.

## Result

**FAIL: unverified** (live LCM read-back not performed in this environment).
