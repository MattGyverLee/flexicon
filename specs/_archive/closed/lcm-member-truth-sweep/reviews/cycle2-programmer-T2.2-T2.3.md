# Cycle 2 -- Programmer report: T2.2 (#302) and T2.3 (#261)

**Precondition check:** `evidence/live-T2.1-notebook-owner.md` VERDICT: PASS
(2026-09-18) -- confirmed before editing. Both tasks implemented in
`flexicon/code/Notebook/DataNotebookOperations.py`.

## T2.2 -- #302, ownership form (rulings C1, C3)

| Site (baseline 598f41e) | Before | After (final line) |
|---|---|---|
| `Create` `:306` lookup + `:313` add | `repos = ...GetService(IRnResearchNbkRepository)`; `repos.RecordsOC.Add(record)` | lookup deleted; `self.project.lp.ResearchNotebookOA.RecordsOC.Add(record)` at `:319` |
| `Delete` `:376` lookup + `:393` remove | `repos = ...GetService(...)`; `repos.RecordsOC.Remove(record)` | lookup deleted; `self.project.lp.ResearchNotebookOA.RecordsOC.Remove(record)` at `:399` |
| `Duplicate` `:2529` lookup + `:2530` add | `repos = ...GetService(...)`; `repos.RecordsOC.Add(duplicate)` | lookup deleted; `self.project.lp.ResearchNotebookOA.RecordsOC.Add(duplicate)` at `:2538` |

Comments/docstrings updated at the corresponding sites (`Create`'s
"Get the research notebook repository" comment, `Delete`'s
"repos.RecordsOC.Remove(record)..." narration, `Duplicate`'s
"Parent is the top-level repository" comment, and the `insert_after`
Args-doc line) to describe the ownership path and cite ruling C1.

**`:232`/`:238` (GetAll enumerable getter) -- CONFIRMED UNTOUCHED.** Still
`repos = self.project.project.ServiceLocator.GetService(IRnResearchNbkRepository)`
followed by `repos.AllInstances()` (now at final line 238), per ruling C3.
The `IRnResearchNbkRepository` import survives (still needed for this one
live use).

## T2.3 -- #261, resolver + mask (ruling C6)

`__GetRecordObject` (final lines 186-203):

Before:
```python
obj = self.project.project.GetObject(hvo)   # LcmCache has no GetObject
...
except (TypeError, System.InvalidCastException, AttributeError,
        KeyError, System.Collections.Generic.KeyNotFoundException) as e:
    raise FP_ParameterError(f"Invalid notebook record object or HVO: {record_or_hvo} - {e}")
```

After:
```python
obj = self.project.Object(hvo)              # :194 -- house path (FLExProject.Object)
...
except (TypeError, System.InvalidCastException,
        KeyError, System.Collections.Generic.KeyNotFoundException) as e:   # AttributeError removed
    raise FP_ParameterError(f"Invalid notebook record object or HVO: {record_or_hvo} - {e}") from e   # :202
```

`AttributeError` was dropped from the catch tuple rather than merely
chained: it was the exact shape of the original bug (accessing a
nonexistent `GetObject` attribute on `LcmCache`), and catching it
unconditionally would keep laundering any *future* genuine
`AttributeError` (e.g. a real coding mistake reachable through this path)
into the same misleading "Invalid notebook record object or HVO" message.
`TypeError`/`InvalidCastException`/`KeyError`/`KeyNotFoundException`
remain because they are genuine "bad HVO" outcomes reachable from
`FLExProject.Object()` and the `IRnGenericRec(obj)` cast, matching the
precedent shape at `DiscourseOperations.py:139-146`. The re-raise now
chains the cause (`from e`) per ruling C6's minimum bar.

This resolver feeds 38 public methods' int-HVO path, all now on the
correct house call.

**`LexSenseOperations.py:1376,1481,1488` -- CONFIRMED UNTOUCHED**
(`ServiceLocator.GetObject`, not part of this sweep).

## Contradictions with spec ground truth

None found. `IRnResearchNbkRepository`'s surface matched the spec's
description exactly (no `RecordsOC`); `FLExProject.Object` at
`FLExProject.py:3946` and the `EnvironmentOperations.py:714` precedent
matched as described.

## Checks run

- `grep -n "flexlibs2"` on the edited file: no hits.
- `python -c "import ast; ast.parse(...)"`: parses cleanly.
- `python -c "from flexicon.code.Notebook.DataNotebookOperations import DataNotebookOperations"`:
  imports cleanly (offline/mock, not a live verification -- T2.8 owns that).
- No test files edited; no `git add`/commit/push performed.
