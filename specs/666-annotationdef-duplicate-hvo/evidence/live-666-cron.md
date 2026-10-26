# Issue #666 live evidence (cron)

## Command (required on FieldWorks host)

```
FLEXLIBS_REQUIRE_LIVE=1
python -m pytest tests/operations/test_issue666_annotationdef_duplicate_hvo_live.py -m requires_live_project -q
```

## run_mode

**FAIL: unverified** — Cloud Agent VM has no `clr` / FieldWorks LCM; live suite not executed.

## Expected behaviour when run

After `Duplicate(project.Object(def_b.Hvo), insert_after=True)`, re-read
`AnnotationDefsOA.PossibilitiesOS` order from the LCM; duplicate HVO index
must equal source HVO index + 1.
