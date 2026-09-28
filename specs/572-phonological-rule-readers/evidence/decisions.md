# Decisions taken by a human (issue #572)

## D-1. `inspect_rule_final.py`: delete it, or fix `:43`

**Status: decided, 2026-09-28: delete.** The maintainer chose option 1 after
implement. The file is deleted, the `context7.json` exclude entry is removed,
and the Category 8 entry says the site was deleted rather than deferred.

**The defect.** Line 43 is the `except:` fallback of the name print:

```python
        except:
            print(f"Name: {rule.Name}")
```

`rule.Name` is an `IMultiUnicode`, so this prints
`SIL.LCModel.DomainImpl.MultiUnicodeAccessor`. It is the seventh site of the
`str(IMultiString)` shape the pattern audit found. The other six were repaired.
The primary path above it (`rule.Name.get(ws_handle)`) is also wrong in shape:
it is not the house `best_analysis_text` read.

**What the file is.** A git-tracked scratch script at the repo root. It dates
from `076f6a2` ("WIP: Phonological rule duplication ...") and was only carried
through `c792af8` (v2.4.0 release) and `ec54432` (the `flexlibs2` -> `flexicon`
rename). No test, module or script imports or runs it.

**What references it** (`rg -n inspect_rule_final`, 2026-09-28):

| Path | Line | Kind of reference |
|---|---|---|
| `context7.json` | 42 | Listed in the Context7 index's exclude list. Not a caller |
| `docs/API_ISSUES_CATEGORIZED.md` | 721, 727 | The #572 Category 8 entry, naming it as the unrepaired site and pointing here |
| `specs/572-phonological-rule-readers/plan.md` | 243, 258 | Pattern audit table and the note deferring it |
| `specs/572-phonological-rule-readers/research.md` | 226 | R-7 |
| `specs/572-phonological-rule-readers/tasks.md` | 221 | T025 |

No code references it.

**The options.**

1. **Delete it** (recommended). It is dead WIP. Deleting it also means removing
   the `context7.json:42` exclude entry, and rewording the two
   `docs/API_ISSUES_CATEGORIZED.md` lines to say the site was deleted.
2. **Fix `:43`.** Replace both name reads (and the matching `Description` reads
   below) with `best_analysis_text(...)`. It keeps a script nobody runs.

The maintainer chose option 1. It lands in the #572 PR.
