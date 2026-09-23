# Issues #302 / #328 / #261 -- offline evidence

## Lex-lead ruling

See `specs/302-datanotebook-records/rulings.md`.

## Commands

```
python -m pytest tests/operations/test_issue302_328_datanotebook_offline.py -m "not requires_live_project" -q
python -m pytest tests/operations/test_352_datanotebook_live.py -m requires_live_project -q
```

## Result (cloud agent, offline only)

```
python3 -m pytest tests/operations/test_issue302_328_datanotebook_offline.py -m "not requires_live_project" -q
```

```
5 passed in 0.05s
```

**Live LCM:** deferred to existing #352 live suite when FieldWorks available.

## Pre/post behaviour

| Defect | Before (issue text) | After (pinned on main) |
|--------|---------------------|-------------------------|
| #302 RecordsOC | `repos.RecordsOC.Add` | `ResearchNotebookOA.RecordsOC` |
| #302/#261 resolver | `project.project.GetObject` | `project.Object` |
| #328 Title | `Title.set_String` | direct `Title = _MakeTsString` |
| #328 content | `record.Text` | `DescriptionOA` helpers |

**Pass/fail:** PASS offline ratchet when pytest green.
