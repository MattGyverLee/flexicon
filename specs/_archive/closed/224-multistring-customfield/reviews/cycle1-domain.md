# Cycle 1 — Domain Review (issue #224)

**Agent:** lex-domain
**Scope:** Correct `ITsMultiString` accessor + "best analysis, else vernacular" fallback semantics for `FLExProject.GetCustomFieldValue`.

## 1. Correct "best analysis, else vernacular" accessor for an ITsMultiString

`get_MultiStringProp` (called at `FLExProject.py:3350`) returns the bare `ITsMultiString`
(`SIL.LCModel.Core.KernelInterfaces`), whose only surface is `get_String(wsHandle)`,
`StringCount`, `GetStringFromIndex(i, out ws)`. `BestAnalysisVernacularAlternative` lives on
`IMultiAccessorBase`, which this narrow interface does not implement in the pythonnet-visible
surface — the same "same concept, narrower interface at this call site" trap as Category 8/9.
There is no shortcut property; the fallback must be built manually:

```python
WSHandle = self.project.DefaultAnalWs
tss = mua.get_String(WSHandle)
if not tss or not tss.Text or tss.Text == "***":
    WSHandle = self.project.DefaultVernWs
    tss = mua.get_String(WSHandle)
if not tss or not tss.Text or tss.Text == "***":
    # exhaustive fallback: walk all analysis WSs, then vernacular WSs,
    # in priority order, returning first non-empty alternative
    for ws in self.GetAllAnalysisWSs() | self.GetAllVernacularWSs():
        candidate = mua.get_String(self.WSHandle(ws))
        if candidate and candidate.Text and candidate.Text != "***":
            tss = candidate
            break
return ITsString(tss)
```

`self.project.DefaultAnalWs` / `DefaultVernWs` are already used elsewhere in this file
(`__WSHandleAnalysis`/`__WSHandleVernacular`, `FLExProject.py:3074-3078`) and are the right
primitives — no new WS-lookup machinery needed.

## 2. No existing helper is directly reusable as-is

`WritingSystemOperations.GetBestString` (`WritingSystemOperations.py:894-906`) and
`string_utils.best_text`/`best_vernacular_text` (`string_utils.py:183-225`) all key off
`.BestAnalysisVernacularAlternative` and are isinstance-guarded/duck-typed against
`IMultiUnicode`/`IMultiString` — they would raise the identical `AttributeError` if handed this
`ITsMultiString`, since it implements neither. They cannot be called unmodified. Also both
existing helpers *normalize and return `.Text`* (a plain str), which would break the ITsString
contract (see #3). Recommend adding a new sibling helper (e.g.
`best_multistring_alternative(mua, default_anal_ws, default_vern_ws, fallback_anal_wss,
fallback_vern_wss)` in `string_utils.py`) that does the manual `get_String` walk above and
returns the `ITsString`/None, rather than retrofitting `GetBestString`/`best_text` which are
contractually str-returning and used elsewhere for that purpose.

## 3. Contract preservation

The docstring at `FLExProject.py:3333-3337` ("best analysis or vernacular string is returned")
is preserved by the manual fallback above. Return type must stay `ITsString`, matching both
sibling branches: `CellarStringTypes` (line 3347, explicit `ITsString(...)` wrap) and the
explicit-WS `MultiString` branch (line 3353). The fix should return `ITsString(tss)`, not
`.Text`, so callers (`CustomFieldOperations.GetValue`, `CustomFieldOperations.py:639`) see the
same type regardless of which branch fired.

## Files referenced
- `flexicon/code/FLExProject.py:3327-3355` (bug + `__WSHandle*` helpers at 3058-3078)
- `flexicon/code/System/CustomFieldOperations.py:589-639`
- `flexicon/code/System/WritingSystemOperations.py:894-906`
- `flexicon/code/Shared/string_utils.py:183-225`
- `docs/API_ISSUES_CATEGORIZED.md:445-505` (Category 8 precedent)
